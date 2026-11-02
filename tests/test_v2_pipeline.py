"""
Testes do pipeline do v2, da formatação pt-BR, normal climatológica,
extração dos arquivos de 2024/2025 e completude.
"""

from __future__ import annotations

from datetime import date
import os
import tempfile
import unittest
import zipfile

from src.v2.conferencia import (
    agrupar_pendencias,
    conferir_ambiente,
    conferir_checksums,
    conferir_numeros,
    impressao_digital_do_codigo,
    pendencias,
)
from src.v2.dados_externos import (
    FormatoNaoReconhecido,
    PESOS_JANELA_MEDIA,
    completude_janela,
    extrair_a204_do_zip,
    ler_media_chuva,
)
from src.v2.formatacao import inteiro, num
from src.v2.inmet import ler_arquivo_inmet


class TestFormatacao(unittest.TestCase):
    def test_numeros_pt_br(self):
        self.assertEqual(num(1234.56, 1), "1.234,6")
        self.assertEqual(num(8.4), "8,4")
        self.assertEqual(num(1000, 0), "1.000")
        self.assertEqual(num(-0.04), "0,0")
        self.assertEqual(num(-8.232, 2), "-8,23")
        self.assertEqual(inteiro(1680), "1.680")
        self.assertEqual(num(None), "—")


class TestMediaChuva(unittest.TestCase):
    """Média 1991–2021 da estação 82768 (Corrêa, Carvalho e Mendes, 2023, Tabela 6)."""

    def test_janelas_ponderadas_pelos_dias(self):
        m = ler_media_chuva()
        self.assertEqual(m.arquivo, "data/referencias/correa_2023_balsas_82768.csv")
        self.assertAlmostEqual(m.janela(PESOS_JANELA_MEDIA["chuvoso"]), 221.8 * 17 / 31 + 187.9 + 180.4 * 25 / 31, places=9)
        self.assertAlmostEqual(m.janela(PESOS_JANELA_MEDIA["seco"]), 2.5 + 1.3 + 18.6 * 8 / 30, places=9)

    def test_arquivo_fora_do_formato_e_erro(self):
        casos = {
            "colunas": "mes,chuva_mm\n1,10\n",
            "mes_repetido": "mes,precipitacao_media_mm\n1,10\n1,20\n",
            "mes_invalido": "mes,precipitacao_media_mm\n13,10\n",
            "negativo": "mes,precipitacao_media_mm\n1,-1\n",
            "nao_numerico": "mes,precipitacao_media_mm\n1,abc\n",
        }
        with tempfile.TemporaryDirectory() as tmp:
            for nome, conteudo in casos.items():
                caminho = os.path.join(tmp, f"{nome}.csv")
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write("# comentário\n" + conteudo)
                with self.subTest(caso=nome), self.assertRaises(FormatoNaoReconhecido):
                    ler_media_chuva(caminho)

    def test_mes_ausente_na_janela_e_erro(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = os.path.join(tmp, "incompleta.csv")
            with open(caminho, "w", encoding="utf-8") as f:
                f.write("mes,precipitacao_media_mm\n1,10\n2,20\n")
            with self.assertRaises(FormatoNaoReconhecido):
                ler_media_chuva(caminho).janela(PESOS_JANELA_MEDIA["chuvoso"])


class TestAnosVizinhos(unittest.TestCase):
    def test_extrai_so_o_arquivo_da_a204(self):
        with tempfile.TemporaryDirectory() as tmp:
            zip_ano = os.path.join(tmp, "2024.zip")
            with zipfile.ZipFile(zip_ano, "w") as z:
                z.writestr("2024/INMET_NE_MA_A204_BALSAS_01-01-2024_A_31-12-2024.CSV", "conteudo da A204")
                z.writestr("2024/INMET_NE_MA_A203_SAO LUIS_01-01-2024_A_31-12-2024.CSV", "outra estação")
            destino = os.path.join(tmp, "raw")
            os.makedirs(destino)
            caminho = extrair_a204_do_zip(zip_ano, destino)
            self.assertEqual(os.listdir(destino), ["INMET_NE_MA_A204_BALSAS_01-01-2024_A_31-12-2024.CSV"])
            with open(caminho, encoding="utf-8") as f:
                self.assertEqual(f.read(), "conteudo da A204")

    def test_zip_sem_a204_e_erro(self):
        with tempfile.TemporaryDirectory() as tmp:
            zip_ano = os.path.join(tmp, "2025.zip")
            with zipfile.ZipFile(zip_ano, "w") as z:
                z.writestr("INMET_NE_MA_A203_SAO LUIS_01-01-2025_A_31-12-2025.CSV", "x")
            with self.assertRaises(FormatoNaoReconhecido):
                extrair_a204_do_zip(zip_ano, tmp)

    def test_completude_no_arquivo_de_2023(self):
        estacao, registros = ler_arquivo_inmet()
        seco = completude_janela(estacao, registros, 2023, "seco", date(2023, 7, 1), date(2023, 9, 8))
        self.assertEqual((seco.dias, seco.dias_completos, seco.dias_sem_registro), (70, 70, 0))
        lacuna = completude_janela(estacao, registros, 2023, "out-dez", date(2023, 10, 1), date(2023, 12, 30))
        self.assertEqual(lacuna.dias_sem_registro, 34)
        self.assertEqual(lacuna.maior_lacuna_sem_registro_dias, 17)


class TestImpressaoDigital(unittest.TestCase):
    def test_muda_quando_um_arquivo_muda(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "src"))
            for nome, texto in (("main.py", "a"), ("requirements.txt", "b"), (os.path.join("src", "m.py"), "c")):
                with open(os.path.join(tmp, nome), "w", encoding="utf-8") as f:
                    f.write(texto)
            antes = impressao_digital_do_codigo(tmp)
            self.assertEqual(antes, impressao_digital_do_codigo(tmp))
            with open(os.path.join(tmp, "src", "m.py"), "w", encoding="utf-8") as f:
                f.write("c2")
            self.assertNotEqual(antes, impressao_digital_do_codigo(tmp))


class TestPipelineV2(unittest.TestCase):
    """Roda o pipeline numa pasta temporária (sem as séries da varredura, para ganhar tempo)."""

    @classmethod
    def setUpClass(cls):
        from src.v2.pipeline import executar_pipeline

        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = os.path.join(cls.tmp.name, "v2")
        cls.res = executar_pipeline(cls.dir, gravar_varredura=False)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_arquivos_esperados(self):
        for nome in ("tab_clima_ciclos", "tab_parametros", "tab_cenarios", "tab_desempenho_chuvoso",
                     "tab_desempenho_seco", "tab_capacidade_minima", "tab_comparacao_v1_v2", "tab_sensibilidade_z1"):
            for ext in ("csv", "md"):
                self.assertTrue(os.path.exists(os.path.join(self.dir, "tabelas", f"{nome}.{ext}")), f"{nome}.{ext}")
        for fig in ("figura1_sensibilidade_e1", "figura2_seco_restrito"):
            for ext in (".png", ".pdf", "_dados.csv"):
                self.assertTrue(os.path.exists(os.path.join(self.dir, "figuras", fig + ext)), fig + ext)
        for doc in ("NUMEROS_ARTIGO.md", "RELATORIO.md", "AMBIENTE.md", "CHECKSUMS.txt", "resultados.json"):
            self.assertTrue(os.path.exists(os.path.join(self.dir, doc)), doc)
        self.assertFalse(os.path.exists(self.dir + ".tmp"))

    def test_todo_csv_grava_os_parametros(self):
        for raiz, _d, arquivos in os.walk(self.dir):
            for a in arquivos:
                if a.endswith(".csv"):
                    with open(os.path.join(raiz, a), encoding="utf-8") as f:
                        cabeca = [f.readline() for _ in range(4)]
                    with self.subTest(arquivo=a):
                        self.assertTrue(cabeca[0].startswith("# conteudo:"))
                        self.assertTrue(any(l.startswith("# parametros:") and "theta1_inicial=" in l for l in cabeca))

    def test_numeros_do_artigo_conferem_com_os_csvs(self):
        n, erros = conferir_numeros(self.dir)
        self.assertGreater(n, 400)
        self.assertEqual(erros, [])

    def test_conferencia_detecta_numero_alterado(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            copia = os.path.join(tmp, "v2")
            shutil.copytree(self.dir, copia)
            caminho = os.path.join(copia, "NUMEROS_ARTIGO.md")
            with open(caminho, encoding="utf-8") as f:
                texto = f.read()
            alvo = next(l for l in texto.splitlines() if "| Chuva no ciclo chuvoso |" in l)
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(texto.replace(alvo, alvo.replace("299,2 mm", "299,3 mm")))
            _n, erros = conferir_numeros(copia)
        self.assertEqual(len(erros), 1)
        self.assertIn("299,3 mm", erros[0])

    def test_checksums(self):
        n, erros, nao_conferidos = conferir_checksums(self.dir)
        self.assertGreater(n, 50)
        self.assertEqual(erros, [])
        self.assertEqual(nao_conferidos, 0)

    def test_checksums_sem_a_pasta_da_varredura(self):
        """Num clone limpo a varredura (fora do git) não existe: fica sem conferir, sem erro."""
        import hashlib
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            copia = os.path.join(tmp, "v2")
            shutil.copytree(self.dir, copia)
            varredura = os.path.join(copia, "series", "varredura")
            os.makedirs(varredura)
            for nome in ("a.csv", "b.csv"):
                with open(os.path.join(varredura, nome), "w", encoding="utf-8") as f:
                    f.write(nome)
            with open(os.path.join(copia, "CHECKSUMS.txt"), "a", encoding="utf-8") as f:
                for nome in ("a.csv", "b.csv"):
                    f.write(f"{hashlib.sha256(nome.encode()).hexdigest()}  series/varredura/{nome}\n")
            self.assertEqual(conferir_checksums(copia)[1:], ([], 0))
            os.remove(os.path.join(varredura, "b.csv"))
            _n, erros, nao_conferidos = conferir_checksums(copia)
            self.assertEqual((len(erros), nao_conferidos), (1, 0))
            self.assertIn("series/varredura/b.csv", erros[0])
            shutil.rmtree(varredura)
            self.assertEqual(conferir_checksums(copia)[1:], ([], 2))

    def test_ambiente_identifica_o_codigo_atual(self):
        ok, gravada, atual = conferir_ambiente(self.dir)
        self.assertTrue(ok, (gravada, atual))

    def test_pendencias_todas_classificadas(self):
        grupos = agrupar_pendencias(pendencias(dir_resultados=self.dir))
        self.assertNotIn("Outros", grupos)
        self.assertTrue(os.path.exists(os.path.join(self.dir, "PENDENCIAS.md")))

    def test_series_horarias_tem_as_colunas_documentadas(self):
        caminho = os.path.join(self.dir, "series", "principal", "seco_restrito_E3.csv")
        with open(caminho, encoding="utf-8") as f:
            cabecalho = next(l for l in f if not l.startswith("#")).strip().split(",")
        for coluna in ("p_mm", "et0_mm", "kc", "etc_mm", "ks", "eta_mm", "i_mm", "theta1", "theta2", "dr_mm",
                       "d1_mm", "d2_mm", "v_l"):
            self.assertIn(coluna, cabecalho)
        self.assertEqual(cabecalho[0], "hora_local_inicio")

    def test_nenhum_conforto_no_v2(self):
        for nome in ("RELATORIO.md", "NUMEROS_ARTIGO.md"):
            with open(os.path.join(self.dir, nome), encoding="utf-8") as f:
                texto = f.read().lower()
            linhas = [l for l in texto.splitlines() if "conforto" in l and "v1" not in l]
            with self.subTest(arquivo=nome):
                self.assertEqual(linhas, [], "\"conforto\" só pode aparecer referido ao v1")


if __name__ == "__main__":
    unittest.main()
