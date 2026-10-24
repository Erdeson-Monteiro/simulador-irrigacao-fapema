"""
Servidor HTTP da Interface de Ingestão, Consulta, Exportação CSV e Painel Web (Etapas 5 e 7).
Implementa integralmente o contrato da Seção 8 utilizando a biblioteca padrão do Python 3.
"""

from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs

from src.database import (
    DEFAULT_DB_PATH,
    inicializar_banco,
    ingerir_lote_leituras,
    ingerir_lote_eventos_irrigacao,
    listar_canteiros,
    consultar_series_canteiro,
    consultar_eventos_canteiro,
    exportar_csv_dados,
)
from src.experiments import DEFAULT_REPORT_JSON, executar_estudo_completo


STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def criar_handler_api(db_path: str = DEFAULT_DB_PATH, report_json_path: str = DEFAULT_REPORT_JSON):
    """Cria a classe de handler HTTP parametrizada com o caminho do banco SQLite."""

    class IrrigacaoAPIHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:
            # Log enxuto para não poluir testes automatizados
            if os.environ.get("IRRIGACAO_VERBOSE_LOG") == "1":
                super().log_message(format, *args)

        def _enviar_json(self, status_code: int, payload: object) -> None:
            corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(corpo)

        def _enviar_texto(
            self, status_code: int, conteudo: str, content_type: str, filename: Optional[str] = None
        ) -> None:
            corpo = conteudo.encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(corpo)))
            if filename:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(corpo)

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            rota = parsed.path
            qs = parse_qs(parsed.query)

            try:
                # 1. Painel Único (Seção 9)
                if rota in ("/", "/index.html"):
                    caminho_html = os.path.join(STATIC_DIR, "index.html")
                    if not os.path.exists(caminho_html):
                        self._enviar_json(404, {"erro": "Painel index.html não encontrado."})
                        return
                    with open(caminho_html, "r", encoding="utf-8") as f:
                        self._enviar_texto(200, f.read(), "text/html; charset=utf-8")
                    return

                # 2. GET /api/v1/canteiros
                if rota == "/api/v1/canteiros":
                    self._enviar_json(200, listar_canteiros(db_path))
                    return

                # 3. GET /api/v1/canteiros/{id}/series?de=&ate=&tipo=
                m_series = re.match(r"^/api/v1/canteiros/([^/]+)/series$", rota)
                if m_series:
                    canteiro_id = m_series.group(1)
                    de = qs.get("de", [None])[0]
                    ate = qs.get("ate", [None])[0]
                    tipo = qs.get("tipo", [None])[0]
                    dados = consultar_series_canteiro(db_path, canteiro_id, de=de, ate=ate, tipo=tipo)
                    self._enviar_json(200, dados)
                    return

                # 4. GET /api/v1/canteiros/{id}/eventos?de=&ate=
                m_eventos = re.match(r"^/api/v1/canteiros/([^/]+)/eventos$", rota)
                if m_eventos:
                    canteiro_id = m_eventos.group(1)
                    de = qs.get("de", [None])[0]
                    ate = qs.get("ate", [None])[0]
                    dados = consultar_eventos_canteiro(db_path, canteiro_id, de=de, ate=ate)
                    self._enviar_json(200, dados)
                    return

                # 5. GET /api/v1/export.csv?canteiro=&de=&ate=
                if rota == "/api/v1/export.csv":
                    canteiro = qs.get("canteiro", [None])[0]
                    de = qs.get("de", [None])[0]
                    ate = qs.get("ate", [None])[0]
                    csv_str = exportar_csv_dados(db_path, canteiro_identificador=canteiro, de=de, ate=ate)
                    nome_arq = f"irrigacao_{canteiro or 'todos'}.csv"
                    self._enviar_texto(200, csv_str, "text/csv; charset=utf-8", filename=nome_arq)
                    return

                # 6. GET /api/v1/comparativo (Métricas da Seção 5 e Validação da Seção 6)
                if rota == "/api/v1/comparativo":
                    if not os.path.exists(report_json_path):
                        executar_estudo_completo(caminho_json_saida=report_json_path)
                    with open(report_json_path, "r", encoding="utf-8") as f:
                        self._enviar_json(200, json.load(f))
                    return

                self._enviar_json(404, {"erro": f"Rota não encontrada: {rota}"})

            except ValueError as e:
                self._enviar_json(400, {"erro": str(e)})
            except Exception as e:
                self._enviar_json(500, {"erro": f"Erro interno: {e}"})

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            rota = parsed.path

            try:
                tamanho = int(self.headers.get("Content-Length", "0"))
                corpo_raw = self.rfile.read(tamanho).decode("utf-8") if tamanho > 0 else "{}"
                payload = json.loads(corpo_raw)
                auth_header = self.headers.get("Authorization")

                if rota == "/api/v1/leituras":
                    res = ingerir_lote_leituras(db_path, payload, auth_header)
                    self._enviar_json(200, res)
                    return

                if rota == "/api/v1/eventos-irrigacao":
                    res = ingerir_lote_eventos_irrigacao(db_path, payload, auth_header)
                    self._enviar_json(200, res)
                    return

                self._enviar_json(404, {"erro": f"Endpoint POST não encontrado: {rota}"})

            except PermissionError as e:
                self._enviar_json(401, {"erro": str(e)})
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                self._enviar_json(400, {"erro": f"Requisição inválida: {e}"})
            except Exception as e:
                self._enviar_json(500, {"erro": f"Erro interno: {e}"})

    return IrrigacaoAPIHandler


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def iniciar_servidor(
    host: str = "127.0.0.1",
    port: int = 8000,
    db_path: str = DEFAULT_DB_PATH,
    report_json_path: str = DEFAULT_REPORT_JSON,
) -> ThreadingHTTPServer:
    """Inicializa o banco e retorna uma instância de ThreadingHTTPServer pronta para servir."""
    inicializar_banco(db_path)
    handler_cls = criar_handler_api(db_path=db_path, report_json_path=report_json_path)
    server = ReusableThreadingHTTPServer((host, port), handler_cls)
    return server


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", "8000"))
    srv = iniciar_servidor(host="0.0.0.0", port=porta)
    print(f"Servidor da Plataforma de Irrigação PIC/FAPEMA ativo em http://localhost:{porta}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
        srv.server_close()
