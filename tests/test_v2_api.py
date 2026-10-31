"""
Testes da API e do painel.

- Token: fora do código, guardado só como SHA-256, comparado em tempo constante, nunca em log;
  os tokens que estiveram no v1 são recusados como token de produção.
- Hospedagem: GET /healthz, corpo limitado a 1 MB, CORS só para a origem configurada,
  SQLite em WAL, porta ocupada = erro.
- Simulador v2: três canteiros, leituras horárias pelo contrato existente, idempotência.
- Painel: θlim lido da configuração; "tempo sem estresse hídrico" e "racionamento uniforme".
"""

from __future__ import annotations

import contextlib
import http.client
import io
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

from src.api_server import STATIC_DIR, iniciar_servidor
from src.database import inicializar_banco, ler_simulacao
from src.seguranca import HASHES_COMPROMETIDOS, TokenInvalido, hash_token, token_de_producao
from src.v2.parametros import PARAMETROS_PADRAO

TOKEN_TESTE = "token-de-teste-com-mais-de-24-caracteres"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@contextlib.contextmanager
def servidor(db_path, **kwargs):
    srv = iniciar_servidor(host="127.0.0.1", port=0, db_path=db_path, **kwargs)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}", srv
    finally:
        srv.shutdown()
        srv.server_close()


def post(url, payload, token=None, extra=None):
    cab = {"Content-Type": "application/json", **(extra or {})}
    if token:
        cab["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=cab, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


LEITURA = {"dispositivo": "sim-001", "leituras": [{"seq": 7, "canteiro": "C1", "tipo": "umidade_solo",
                                                  "profundidade_cm": 10, "valor_bruto": 2400,
                                                  "registrado_em": "2026-10-24T10:00:00-03:00"}]}


class TestTokens(unittest.TestCase):
    def test_token_de_producao_e_validado(self):
        with self.assertRaises(TokenInvalido):
            token_de_producao({})
        with self.assertRaises(TokenInvalido):
            token_de_producao({"DEVICE_TOKEN": "curto"})
        self.assertEqual(token_de_producao({"DEVICE_TOKEN": TOKEN_TESTE}), TOKEN_TESTE)

    def test_token_do_teste_de_contrato_nunca_vale_em_producao(self):
        # O token comprometido não é repetido aqui: é lido do teste de contrato (que não pode mudar).
        import re
        with open(os.path.join(RAIZ, "tests", "test_end_to_end.py"), encoding="utf-8") as f:
            token_contrato = re.search(r'"Bearer ([^"]+)"', f.read()).group(1)
        self.assertIn(hash_token(token_contrato), HASHES_COMPROMETIDOS)
        with self.assertRaises(TokenInvalido):
            token_de_producao({"DEVICE_TOKEN": token_contrato})

    def test_banco_guarda_so_o_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "b.db")
            inicializar_banco(db, token_dispositivo=TOKEN_TESTE)
            conn = sqlite3.connect(db)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            hashes = dict(conn.execute("SELECT codigo, token_sha256 FROM dispositivo"))
            conn.close()
            with open(db, "rb") as f:
                conteudo = f.read()
            self.assertEqual(hashes["sim-001"], hash_token(TOKEN_TESTE))
            self.assertIsNone(hashes["esp32-001"])
            self.assertNotIn(TOKEN_TESTE.encode(), conteudo)

    def test_rotacao_e_rejeicoes(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "b.db")
            with servidor(db, token_dispositivo=TOKEN_TESTE) as (url, _):
                self.assertEqual(post(url + "/api/v1/leituras", LEITURA, TOKEN_TESTE)[0], 200)
                self.assertEqual(post(url + "/api/v1/leituras", LEITURA, TOKEN_TESTE + "x")[0], 401)
                self.assertEqual(post(url + "/api/v1/leituras", LEITURA)[0], 401)
                esp = {**LEITURA, "dispositivo": "esp32-001"}
                self.assertEqual(post(url + "/api/v1/leituras", esp, TOKEN_TESTE)[0], 401)

    def test_log_nunca_tem_o_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "b.db")
            saida = io.StringIO()
            with contextlib.redirect_stderr(saida):
                with servidor(db, token_dispositivo=TOKEN_TESTE, registrar_acessos=True) as (url, _):
                    post(url + "/api/v1/leituras", LEITURA, TOKEN_TESTE)
                    post(url + "/api/v1/leituras", LEITURA, "errado-" + TOKEN_TESTE)
            self.assertIn("POST /api/v1/leituras", saida.getvalue())
            self.assertNotIn(TOKEN_TESTE, saida.getvalue())


class TestHospedagem(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "b.db")

    def tearDown(self):
        self.tmp.cleanup()

    def test_healthz_e_wal(self):
        with servidor(self.db) as (url, _):
            with urllib.request.urlopen(url + "/healthz") as r:
                corpo = json.loads(r.read())
        self.assertEqual(corpo["status"], "ok")
        self.assertEqual(corpo["banco"]["journal_mode"], "wal")

    def test_corpo_maior_que_1_mb(self):
        with servidor(self.db) as (url, srv):
            conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=10)
            conn.putrequest("POST", "/api/v1/leituras")
            conn.putheader("Content-Type", "application/json")
            conn.putheader("Content-Length", str(1024 * 1024 + 1))
            conn.endheaders()
            resp = conn.getresponse()
            self.assertEqual(resp.status, 413)
            conn.close()
            conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=10)
            conn.putrequest("POST", "/api/v1/leituras")
            conn.endheaders()
            self.assertEqual(conn.getresponse().status, 411)
            conn.close()

    def test_cors_so_para_a_origem_configurada(self):
        def origem_permitida(url, origem):
            req = urllib.request.Request(url + "/healthz", headers={"Origin": origem})
            with urllib.request.urlopen(req) as r:
                return r.headers.get("Access-Control-Allow-Origin")

        with servidor(self.db, cors_origem="https://painel.exemplo.org") as (url, _):
            self.assertEqual(origem_permitida(url, "https://painel.exemplo.org"), "https://painel.exemplo.org")
            self.assertIsNone(origem_permitida(url, "https://outro.exemplo.org"))
        with servidor(self.db) as (url, _):
            self.assertIsNone(origem_permitida(url, "https://painel.exemplo.org"))

    def test_porta_ocupada_e_erro(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        try:
            with self.assertRaises(OSError):
                iniciar_servidor(host="127.0.0.1", port=sock.getsockname()[1], db_path=self.db)
        finally:
            sock.close()

    def test_so_arquivos_publicados(self):
        with servidor(self.db) as (url, _):
            for caminho in ("/resultados/figuras/qualquer.png", "/api/v1/tabelas/tab_varredura_reservatorio",
                            "/resultados/figuras/..%2F..%2Fmain.py"):
                with self.subTest(caminho=caminho):
                    with self.assertRaises(urllib.error.HTTPError) as ctx:
                        urllib.request.urlopen(url + caminho)
                    self.assertEqual(ctx.exception.code, 404)

    def test_serve_exige_token_valido(self):
        ambiente = {k: v for k, v in os.environ.items() if k != "DEVICE_TOKEN"}
        ambiente.update({"PORT": "0", "DB_PATH": self.db})
        sem = subprocess.run([sys.executable, "main.py", "serve"], cwd=RAIZ, env=ambiente, capture_output=True,
                             text=True, timeout=60)
        self.assertEqual(sem.returncode, 2)
        self.assertIn("DEVICE_TOKEN", sem.stderr)


class TestSimuladorV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from src.v2.simulador import gerar_lotes, popular_banco

        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = os.path.join(cls.tmp.name, "painel.db")
        cls.resumo = popular_banco(cls.db, TOKEN_TESTE, "seco", "Restrito")
        cls.lotes = gerar_lotes("seco", "Restrito")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_tres_canteiros_horarios(self):
        conn = sqlite3.connect(self.db)
        por_canteiro = dict(conn.execute(
            "SELECT c.codigo, COUNT(*) FROM leitura l JOIN canteiro c ON c.id = l.canteiro_id "
            "WHERE l.tipo = 'umidade_solo' AND l.profundidade_cm = 10 GROUP BY c.codigo"))
        conn.close()
        self.assertEqual(por_canteiro, {"C1": 1680, "C2": 1680, "C3": 1680})
        self.assertEqual(self.resumo["leituras"]["aceitos"], len(self.lotes["leituras"]))

    def test_idempotencia_no_reenvio(self):
        self.assertEqual(self.resumo["reenvio"]["aceitos"], 0)
        self.assertGreater(self.resumo["reenvio"]["ignorados"], 0)

    def test_valores_iguais_aos_do_modelo(self):
        from src.v2.simulador import rodar_canteiros

        rodadas, _ = rodar_canteiros("seco", "Restrito")
        sim = ler_simulacao(self.db)
        conn = sqlite3.connect(self.db)
        for codigo, e in sim["canteiros"].items():
            theta = [v for (v,) in conn.execute(
                "SELECT l.valor_calibrado FROM leitura l JOIN canteiro c ON c.id = l.canteiro_id WHERE c.codigo = ? "
                "AND l.tipo = 'umidade_solo' AND l.profundidade_cm = 10 ORDER BY l.registrado_em", (codigo,))]
            n_eventos = conn.execute(
                "SELECT COUNT(*) FROM evento_irrigacao ev JOIN canteiro c ON c.id = ev.canteiro_id WHERE c.codigo = ?",
                (codigo,)).fetchone()[0]
            with self.subTest(canteiro=codigo, estrategia=e):
                modelo = rodadas[e].serie["theta1"]
                self.assertEqual(len(theta), len(modelo))
                self.assertLess(max(abs(a - b) for a, b in zip(theta, modelo)), 1e-6)
                self.assertEqual(n_eventos, rodadas[e].metricas.acionamentos)
                self.assertEqual(sim["metricas"][e]["acionamentos"], rodadas[e].metricas.acionamentos)
        conn.close()
        self.assertAlmostEqual(sim["parametros"]["theta_lim"], PARAMETROS_PADRAO.theta_lim, places=12)


class TestPainel(unittest.TestCase):
    def test_termos_e_limiar_da_configuracao(self):
        with open(os.path.join(STATIC_DIR, "index.html"), encoding="utf-8") as f:
            html = f.read()
        self.assertIn("Tempo sem estresse hídrico", html)
        self.assertIn("racionamento uniforme", html)
        self.assertNotIn("conforto", html.lower())
        for literal in ("0,238", "0.238", "0,231", "0.231"):
            self.assertNotIn(literal, html)
        self.assertIn("p.theta_lim", html)


if __name__ == "__main__":
    unittest.main()
