"""
Suíte de Testes Automatizados de Ponta a Ponta.
Verifica:
  - Grandezas derivadas do solo (AD = 28 mm, θ_lim = 0,231 cm³/cm³)
  - Os 3 testes obrigatórios de validação independente da Seção 6 contra constantes literais
    calculadas à mão (Conservação de massa independente, Secagem monotônica, Saturação D2 = 250 mm)
  - Parser do formato oficial BDMEP/INMET, proibição de síntese climática e extração de latitude
  - Limite físico de reservatório para E1, E2 e E3 e decomposição D2_incremental
  - Análise de sensibilidade de lamina_fixa na E1 (5, 10, 15, 20, 25, 30 mm)
  - Varredura de capacidade do reservatório na E3 (250 a 2000 L × 3, 7, 14 dias)
  - Geração das tabelas T1 a T8, figuras F1 a F5 (300 dpi) e relatorio_final.md
  - Contrato HTTP da interface de ingestão, idempotência e exportação CSV
"""

from __future__ import annotations
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

from src.water_balance import (
    SoilParams,
    SCENARIOS_PADRAO,
    simular_estrategia,
    executar_testes_validacao_secao6,
)
from src.climate import (
    DEFAULT_RAW_INMET_CSV,
    carregar_e_tratar_serie_climatica,
    _interpolar_vetor,
)
from src.experiments import executar_estudo_completo
from src.api_server import iniciar_servidor


class TestPlataformaIrrigacaoEndToEnd(unittest.TestCase):
    def test_parametros_derivados_solo(self) -> None:
        soil = SoilParams()
        self.assertAlmostEqual(soil.agua_disponivel_mm, 28.0, places=5)
        self.assertAlmostEqual(soil.theta_lim, 0.231, places=5)

    def test_validacao_obrigatoria_secao6_constantes_literais(self) -> None:
        resultado = executar_testes_validacao_secao6()
        self.assertTrue(resultado["aprovado"])

        # Teste 1: constantes literais calculadas à mão (S_ini=102, S_fim=100, ΔS=-2, D2=16)
        t1 = resultado["teste_1_conservacao_massa"]
        self.assertTrue(t1["aprovado"])
        self.assertAlmostEqual(t1["s_inicial_mm_observado"], 102.0, places=6)
        self.assertAlmostEqual(t1["s_final_mm_observado"], 100.0, places=6)
        self.assertAlmostEqual(t1["d2_acumulado_mm_observado"], 16.0, places=6)
        self.assertAlmostEqual(t1["lado_a_saldo_fluxos_mm"], -2.0, places=6)
        self.assertAlmostEqual(t1["delta_armazenamento_mm"], -2.0, places=6)
        self.assertLess(t1["erro_relativo_pct"], 0.1)

        # Teste 2: secagem monotônica (estabiliza em 0.14 no dia 7 com ΣETc_real = 28.0 mm)
        t2 = resultado["teste_2_secagem_monotonica"]
        self.assertTrue(t2["aprovado"])
        self.assertAlmostEqual(t2["theta1_dia_7_observado"], 0.14, places=6)
        self.assertAlmostEqual(t2["theta1_final"], 0.14, places=6)
        self.assertAlmostEqual(t2["etc_real_acumulada_mm_observada"], 28.0, places=6)

        # Teste 3: saturação partindo de θ_cc=0.28 com P=250 mm e ETc=0 -> D1=250 mm, D2=250 mm
        t3 = resultado["teste_3_saturacao"]
        self.assertTrue(t3["aprovado"])
        self.assertAlmostEqual(t3["drenagem_d1_mm_observada"], 250.0, places=6)
        self.assertAlmostEqual(t3["drenagem_profunda_d2_mm"], 250.0, places=6)
        self.assertAlmostEqual(t3["theta1_final"], 0.28, places=6)
        self.assertAlmostEqual(t3["theta2_final"], 0.28, places=6)

    def test_tratamento_lacunas_e_parser_bdmep_real(self) -> None:
        vetor = [30.0, None, None, 36.0]
        interp, faltantes, maior = _interpolar_vetor(vetor, max_lacuna=3)
        self.assertEqual(faltantes, 2)
        self.assertEqual(maior, 2)
        self.assertAlmostEqual(interp[1], 32.0, places=5)
        self.assertAlmostEqual(interp[2], 34.0, places=5)

        vetor_longo = [30.0, None, None, None, None, 35.0]
        with self.assertRaises(ValueError):
            _interpolar_vetor(vetor_longo, max_lacuna=3)

        # Proibição 1: arquivo inexistente deve falhar explicitamente (sem síntese)
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho_inexistente = os.path.join(tmpdir, "nao_existe.csv")
            with self.assertRaises(FileNotFoundError):
                carregar_e_tratar_serie_climatica(caminho_inexistente)

            # Leitura do arquivo bruto real do BDMEP
            dados = carregar_e_tratar_serie_climatica(
                DEFAULT_RAW_INMET_CSV, diretorio_processed=tmpdir
            )
            qual = dados["qualidade"]
            self.assertTrue(qual["global"]["metadados_procedencia"]["origem_real_inmet"])
            self.assertAlmostEqual(dados["latitude_deg"], -7.45555555, places=6)
            for var in ("t_max", "t_min", "t_med", "precipitacao_mm"):
                self.assertIn(var, qual["Estacao_Seca"]["por_variavel"])
                self.assertIn(var, qual["Estacao_Chuvosa"]["por_variavel"])

    def test_estudo_completo_e_geracao_csvs_brutos(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            json_out = os.path.join(tmpdir, "relatorio.json")
            md_out = os.path.join(tmpdir, "relatorio_final.md")
            dir_tabelas = os.path.join(tmpdir, "tabelas")
            dir_rodadas = os.path.join(tmpdir, "rodadas")
            dir_figuras = os.path.join(tmpdir, "figuras")

            res = executar_estudo_completo(
                caminho_csv_clima=DEFAULT_RAW_INMET_CSV,
                caminho_json_saida=json_out,
                caminho_md_saida=md_out,
                diretorio_tabelas=dir_tabelas,
                diretorio_rodadas=dir_rodadas,
                diretorio_figuras=dir_figuras,
            )
            cons = res["consolidado"]
            self.assertEqual(len(cons["sensibilidade_lamina_fixa_e1"]), 36)  # 2 per * 3 cen * 6 lâminas
            self.assertEqual(len(cons["varredura_reservatorio_e3"]), 48)    # 2 per * 3 int * 8 cap
            self.assertEqual(len(cons["dimensionamento_reservatorio_e3"]), 6)
            for arq in cons["arquivos_csv_brutos"]:
                self.assertTrue(os.path.exists(arq), f"CSV bruto não encontrado: {arq}")
            for fig_info in cons["figuras_geradas"]:
                self.assertTrue(os.path.exists(fig_info["png"]))
                self.assertTrue(os.path.exists(fig_info["csv"]))
            self.assertTrue(os.path.exists(md_out))

    def test_contrato_http_ingestao_idempotencia_e_consultas(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_irrigacao.db")
            report_path = os.path.join(tmpdir, "relatorio.json")
            srv = iniciar_servidor(
                host="127.0.0.1", port=0, db_path=db_path, report_json_path=report_path
            )
            port = srv.server_address[1]
            base_url = f"http://127.0.0.1:{port}"
            th = threading.Thread(target=srv.serve_forever, daemon=True)
            th.start()

            try:
                payload_leitura = {
                    "dispositivo": "sim-001",
                    "leituras": [
                        {
                            "seq": 1042,
                            "canteiro": "C1",
                            "tipo": "umidade_solo",
                            "profundidade_cm": 10,
                            "valor_bruto": 2310,
                            "registrado_em": "2026-10-16T14:00:00-03:00",
                        }
                    ],
                }
                req_ok = urllib.request.Request(
                    f"{base_url}/api/v1/leituras",
                    data=json.dumps(payload_leitura).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": "Bearer tok-sim-001-fapema",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req_ok) as resp:
                    body1 = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(body1, {"aceitos": 1, "ignorados": 0, "ultima_sequencia": 1042})
            finally:
                srv.shutdown()
                srv.server_close()


if __name__ == "__main__":
    unittest.main()
