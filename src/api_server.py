"""
Servidor HTTP da interface de ingestão, consulta, exportação CSV e painel web.
Implementa o contrato de `docs/CONTRATO_E_MODELO_DADOS.md` com a biblioteca padrão do Python.

Proteções para hospedagem: corpo de requisição limitado a 1 MB; CORS só
para a origem configurada; token do dispositivo conferido pelo SHA-256 em tempo constante e
nunca registrado em log (o log traz só método, caminho e status); erros internos sem detalhes
para o cliente. O servidor não roda simulação: só serve o que o `pipeline` gravou.
"""

from __future__ import annotations

import csv
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import sys
import traceback
from typing import Optional
from urllib.parse import parse_qs, urlparse

from src.database import (
    DEFAULT_DB_PATH,
    consultar_eventos_canteiro,
    consultar_series_canteiro,
    exportar_csv_dados,
    ingerir_lote_eventos_irrigacao,
    ingerir_lote_leituras,
    inicializar_banco,
    ler_simulacao,
    listar_canteiros,
    verificar_banco,
)


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DIR_RESULTADOS_PADRAO = os.path.join(ROOT_DIR, "resultados", "v2")
DEFAULT_REPORT_JSON = os.path.join(DIR_RESULTADOS_PADRAO, "resultados.json")
LIMITE_CORPO_BYTES = 1024 * 1024
TABELAS_PUBLICADAS = ("tab_desempenho_chuvoso", "tab_desempenho_seco", "tab_capacidade_minima",
                      "tab_clima_ciclos", "tab_cenarios")
FIGURAS_PUBLICADAS = ("figura1_sensibilidade_e1.png", "figura2_seco_restrito.png")


class RequisicaoInvalida(ValueError):
    def __init__(self, status: int, mensagem: str):
        super().__init__(mensagem)
        self.status = status


def _ler_tabela_csv(caminho: str) -> dict:
    with open(caminho, encoding="utf-8", newline="") as f:
        linhas = [l for l in f if not l.startswith("#")]
    leitor = csv.DictReader(linhas)
    return {"campos": leitor.fieldnames, "linhas": list(leitor)}


def criar_handler_api(
    db_path: str = DEFAULT_DB_PATH,
    report_json_path: str = DEFAULT_REPORT_JSON,
    cors_origem: Optional[str] = None,
    dir_resultados: Optional[str] = None,
    registrar_acessos: bool = False,
):
    """Cria a classe de handler HTTP parametrizada com o banco, a origem do CORS e os resultados."""
    dir_res = dir_resultados or os.path.dirname(os.path.abspath(report_json_path))

    class IrrigacaoAPIHandler(BaseHTTPRequestHandler):
        server_version = "PICFAPEMA"
        sys_version = ""

        def log_message(self, format: str, *args) -> None:
            # Só método, caminho e status; cabeçalhos (e o token) nunca entram no log.
            if registrar_acessos or os.environ.get("IRRIGACAO_VERBOSE_LOG") == "1":
                sys.stderr.write("%s - %s\n" % (self.log_date_time_string(), format % args))

        def _cabecalhos_comuns(self) -> None:
            self.send_header("X-Content-Type-Options", "nosniff")
            origem = self.headers.get("Origin")
            if cors_origem and origem == cors_origem:
                self.send_header("Access-Control-Allow-Origin", cors_origem)
                self.send_header("Vary", "Origin")

        def _enviar_bytes(self, status: int, corpo: bytes, content_type: str, extras: Optional[dict] = None) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(corpo)))
            for k, v in (extras or {}).items():
                self.send_header(k, v)
            self._cabecalhos_comuns()
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(corpo)

        def _enviar_json(self, status_code: int, payload: object) -> None:
            corpo = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._enviar_bytes(status_code, corpo, "application/json; charset=utf-8")

        def _enviar_texto(self, status_code: int, conteudo: str, content_type: str,
                          filename: Optional[str] = None) -> None:
            extras = {"Content-Disposition": f'attachment; filename="{filename}"'} if filename else None
            self._enviar_bytes(status_code, conteudo.encode("utf-8"), content_type, extras)

        def _erro_interno(self) -> None:
            traceback.print_exc(file=sys.stderr)
            self._enviar_json(500, {"erro": "Erro interno do servidor."})

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self._cabecalhos_comuns()
            if cors_origem and self.headers.get("Origin") == cors_origem:
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
                self.send_header("Access-Control-Max-Age", "600")
            self.end_headers()

        def do_HEAD(self) -> None:
            self.do_GET()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            rota = parsed.path
            qs = parse_qs(parsed.query)
            try:
                if rota in ("/", "/index.html"):
                    with open(os.path.join(STATIC_DIR, "index.html"), "rb") as f:
                        self._enviar_bytes(200, f.read(), "text/html; charset=utf-8",
                                           {"Cache-Control": "no-cache"})
                    return

                if rota == "/healthz":
                    self._enviar_json(200, {"status": "ok", "banco": verificar_banco(db_path)})
                    return

                if rota == "/api/v1/canteiros":
                    self._enviar_json(200, listar_canteiros(db_path))
                    return

                m_series = re.match(r"^/api/v1/canteiros/([^/]+)/series$", rota)
                if m_series:
                    self._enviar_json(200, consultar_series_canteiro(
                        db_path, m_series.group(1), de=qs.get("de", [None])[0], ate=qs.get("ate", [None])[0],
                        tipo=qs.get("tipo", [None])[0]))
                    return

                m_eventos = re.match(r"^/api/v1/canteiros/([^/]+)/eventos$", rota)
                if m_eventos:
                    self._enviar_json(200, consultar_eventos_canteiro(
                        db_path, m_eventos.group(1), de=qs.get("de", [None])[0], ate=qs.get("ate", [None])[0]))
                    return

                if rota == "/api/v1/export.csv":
                    canteiro = qs.get("canteiro", [None])[0]
                    csv_str = exportar_csv_dados(db_path, canteiro_identificador=canteiro,
                                                 de=qs.get("de", [None])[0], ate=qs.get("ate", [None])[0])
                    nome = re.sub(r"[^A-Za-z0-9_-]", "", canteiro or "todos") or "todos"
                    self._enviar_texto(200, csv_str, "text/csv; charset=utf-8", filename=f"irrigacao_{nome}.csv")
                    return

                if rota == "/api/v1/simulacao":
                    sim = ler_simulacao(db_path)
                    if sim is None:
                        self._enviar_json(404, {"erro": "Banco sem simulação carregada. Rode python3 main.py pipeline."})
                    else:
                        self._enviar_json(200, sim)
                    return

                if rota in ("/api/v1/resultados", "/api/v1/comparativo"):
                    if not os.path.exists(report_json_path):
                        self._enviar_json(404, {"erro": "Resultados do v2 não encontrados. Rode python3 main.py pipeline."})
                        return
                    with open(report_json_path, encoding="utf-8") as f:
                        self._enviar_json(200, json.load(f))
                    return

                m_tab = re.match(r"^/api/v1/tabelas/([a-z0-9_]+)$", rota)
                if m_tab:
                    nome = m_tab.group(1)
                    caminho = os.path.join(dir_res, "tabelas", f"{nome}.csv")
                    if nome not in TABELAS_PUBLICADAS or not os.path.exists(caminho):
                        self._enviar_json(404, {"erro": f"Tabela não publicada: {nome}"})
                        return
                    self._enviar_json(200, _ler_tabela_csv(caminho))
                    return

                m_fig = re.match(r"^/resultados/figuras/([a-z0-9_]+\.png)$", rota)
                if m_fig:
                    nome = m_fig.group(1)
                    caminho = os.path.join(dir_res, "figuras", nome)
                    if nome not in FIGURAS_PUBLICADAS or not os.path.exists(caminho):
                        self._enviar_json(404, {"erro": f"Figura não publicada: {nome}"})
                        return
                    with open(caminho, "rb") as f:
                        self._enviar_bytes(200, f.read(), "image/png", {"Cache-Control": "no-cache"})
                    return

                self._enviar_json(404, {"erro": f"Rota não encontrada: {rota}"})
            except ValueError as e:
                self._enviar_json(400, {"erro": str(e)})
            except Exception:
                self._erro_interno()

        def _ler_corpo(self) -> dict:
            tamanho_txt = self.headers.get("Content-Length")
            if tamanho_txt is None:
                raise RequisicaoInvalida(411, "Cabeçalho Content-Length obrigatório.")
            try:
                tamanho = int(tamanho_txt)
            except ValueError:
                raise RequisicaoInvalida(400, "Content-Length inválido.")
            if tamanho < 0:
                raise RequisicaoInvalida(400, "Content-Length inválido.")
            if tamanho > LIMITE_CORPO_BYTES:
                raise RequisicaoInvalida(413, f"Corpo maior que o limite de {LIMITE_CORPO_BYTES} bytes.")
            corpo = self.rfile.read(tamanho) if tamanho else b"{}"
            try:
                return json.loads(corpo.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise RequisicaoInvalida(400, f"JSON inválido: {exc}")

        def do_POST(self) -> None:
            rota = urlparse(self.path).path
            try:
                payload = self._ler_corpo()
                if not isinstance(payload, dict):
                    raise RequisicaoInvalida(400, "O corpo deve ser um objeto JSON.")
                auth_header = self.headers.get("Authorization")
                if rota == "/api/v1/leituras":
                    self._enviar_json(200, ingerir_lote_leituras(db_path, payload, auth_header))
                    return
                if rota == "/api/v1/eventos-irrigacao":
                    self._enviar_json(200, ingerir_lote_eventos_irrigacao(db_path, payload, auth_header))
                    return
                self._enviar_json(404, {"erro": f"Endpoint POST não encontrado: {rota}"})
            except RequisicaoInvalida as e:
                self.close_connection = True
                self._enviar_json(e.status, {"erro": str(e)})
            except PermissionError as e:
                self._enviar_json(401, {"erro": str(e)})
            except (ValueError, KeyError, TypeError) as e:
                self._enviar_json(400, {"erro": f"Requisição inválida: {e}"})
            except Exception:
                self._erro_interno()

    return IrrigacaoAPIHandler


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    """SO_REUSEADDR só libera portas em TIME_WAIT: uma porta já em uso continua dando erro."""
    allow_reuse_address = True
    daemon_threads = True


def iniciar_servidor(
    host: str = "127.0.0.1",
    port: int = 8000,
    db_path: str = DEFAULT_DB_PATH,
    report_json_path: str = DEFAULT_REPORT_JSON,
    token_dispositivo: Optional[str] = None,
    cors_origem: Optional[str] = None,
    dir_resultados: Optional[str] = None,
    registrar_acessos: bool = False,
) -> ThreadingHTTPServer:
    """
    Inicializa o banco e devolve um ThreadingHTTPServer pronto para servir. Porta ocupada
    levanta OSError: não há troca automática de porta.
    """
    inicializar_banco(db_path, token_dispositivo=token_dispositivo)
    handler_cls = criar_handler_api(db_path=db_path, report_json_path=report_json_path, cors_origem=cors_origem,
                                    dir_resultados=dir_resultados, registrar_acessos=registrar_acessos)
    return ReusableThreadingHTTPServer((host, port), handler_cls)
