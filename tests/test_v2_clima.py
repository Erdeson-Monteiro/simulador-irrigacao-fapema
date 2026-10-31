"""
Testes da série horária do INMET em hora local e da ET0 horária por
Penman-Monteith (FAO-56).

- Exemplo 19 do FAO-56 ("Determination of ETo with hourly data").
- Convenção de horário: o registro HH00 UTC marca o fim do intervalo (centroide da radiação).
- Regras de falta: radiação vazia de dia é erro; à noite vale 0; negativa vale 0.
- Valores de conferência de uma implementação independente: somas com tolerância de
  0,5%, contagens exatas.
"""

from __future__ import annotations

import dataclasses
from datetime import date, datetime, timezone
import math
import os
import statistics
import tempfile
import unittest

from src.v2 import fao56
from src.v2.clima import (
    CICLOS_2023,
    DadoClimaticoAusente,
    centroide_radiacao,
    extrair_ciclo,
    montar_serie_horaria,
)
from src.v2.inmet import ArquivoINMETInvalido, conferir_sha256, ler_arquivo_inmet, ARQUIVO_A204_2023


TOL_INTERMEDIARIO = 0.002
TOL_ET0 = 0.005
TOL_SOMA = 0.005  # 0,5%


class TestExemplo19FAO56(unittest.TestCase):
    """FAO-56, Exemplo 19: φ = 16°13′N, z = 8 m, 1º de outubro (J = 274), Lz = 15°, Lm = 16,25°."""

    LAT = math.radians(16 + 13 / 60)

    def calcular(self, t_h, t_c, ur, u2, rs, rs_rso_noite=None):
        geo = fao56.geometria_horaria(274, t_h, self.LAT, 15.0, 16.25)
        pm = fao56.et0_penman_monteith_horaria(t_c, ur, u2, rs, geo.ra_mj, 8.0, rs_rso_noite=rs_rso_noite)
        return geo, pm

    def test_latitude_e_geometria(self):
        self.assertAlmostEqual(self.LAT, 0.2830, delta=0.0001)
        geo, _ = self.calcular(14.5, 38, 52, 3.3, 2.450)
        self.assertAlmostEqual(geo.dr, 1.0001, delta=0.0001)
        self.assertAlmostEqual(geo.delta, -0.0753, delta=0.0001)
        self.assertAlmostEqual(geo.sc_h, 0.1889, delta=0.0001)

    def test_hora_noturna_02_03h(self):
        geo, pm = self.calcular(2.5, 28, 90, 1.9, 0.0, rs_rso_noite=0.8)
        esperado = {
            "gamma": (pm.gamma, 0.0673), "omega": (geo.omega, -2.46), "delta": (pm.delta_curva, 0.220),
            "e0": (pm.e0, 3.780), "ea": (pm.ea, 3.402), "ra": (geo.ra_mj, 0.0), "rso": (pm.rso, 0.0),
            "rs_rso": (pm.rs_rso, 0.8), "rnl": (pm.rnl, 0.100), "rn": (pm.rn, -0.100), "g": (pm.g, -0.050),
        }
        for nome, (obtido, ref) in esperado.items():
            with self.subTest(grandeza=nome):
                self.assertAlmostEqual(obtido, ref, delta=TOL_INTERMEDIARIO)
        self.assertAlmostEqual(pm.et0_mm_h, 0.00, delta=TOL_ET0)

    def test_hora_diurna_14_15h(self):
        geo, pm = self.calcular(14.5, 38, 52, 3.3, 2.450)
        esperado = {
            "gamma": (pm.gamma, 0.0673), "omega": (geo.omega, 0.682), "delta": (pm.delta_curva, 0.358),
            "e0": (pm.e0, 6.625), "ea": (pm.ea, 3.445), "ra": (geo.ra_mj, 3.543), "rso": (pm.rso, 2.658),
            "rs_rso": (pm.rs_rso, 0.922), "rnl": (pm.rnl, 0.137), "rn": (pm.rn, 1.749), "g": (pm.g, 0.175),
        }
        for nome, (obtido, ref) in esperado.items():
            with self.subTest(grandeza=nome):
                self.assertAlmostEqual(obtido, ref, delta=TOL_INTERMEDIARIO)
        self.assertAlmostEqual(pm.et0_mm_h, 0.63, delta=TOL_ET0)

    def test_noite_exige_razao_do_fim_da_tarde(self):
        with self.assertRaises(ValueError):
            self.calcular(2.5, 28, 90, 1.9, 0.0, rs_rso_noite=None)


class BaseSerie2023(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.estacao, cls.registros = ler_arquivo_inmet()
        cls.serie = montar_serie_horaria(cls.estacao, cls.registros)
        cls.ciclos = {
            nome: extrair_ciclo(cls.serie, cls.estacao, nome, ini, fim)
            for nome, (ini, fim) in CICLOS_2023.items()
        }

    def serie_com_registro_alterado(self, fim_utc: datetime, **novos_valores):
        registros = []
        for r in self.registros:
            if r.fim_utc == fim_utc:
                r = dataclasses.replace(r, valores={**r.valores, **novos_valores})
            registros.append(r)
        return montar_serie_horaria(self.estacao, registros)


class TestArquivoEConvencoes(BaseSerie2023):
    def test_metadados_do_arquivo(self):
        self.assertEqual(self.estacao.codigo, "A204")
        self.assertAlmostEqual(self.estacao.latitude, -7.45555555, places=8)
        self.assertAlmostEqual(self.estacao.longitude, -46.02749999, places=8)
        self.assertAlmostEqual(self.estacao.altitude, 271.03, places=2)
        self.assertEqual(
            self.estacao.sha256, "7aa68f3a9a2c09ef19a822490fb5fe957c1e0b37bed7ca6b084e3e38d450b233"
        )

    def test_sha256_fora_do_registro_e_recusado(self):
        with tempfile.TemporaryDirectory() as tmp:
            registro = os.path.join(tmp, "SHA256SUMS")
            with open(registro, "w", encoding="utf-8") as f:
                f.write("0" * 64 + "  " + os.path.relpath(ARQUIVO_A204_2023, tmp) + "\n")
            with self.assertRaises(ArquivoINMETInvalido):
                conferir_sha256(ARQUIVO_A204_2023, registro)

    def test_dia_local_vai_de_0400_utc_a_0300_utc(self):
        for nome, ciclo in self.ciclos.items():
            with self.subTest(ciclo=nome):
                self.assertEqual(len(ciclo.horas), 1680)
                self.assertEqual(ciclo.horas[0].fim_utc, datetime(
                    ciclo.inicio.year, ciclo.inicio.month, ciclo.inicio.day, 4, tzinfo=timezone.utc))
                self.assertEqual(ciclo.horas[0].hora_local, 0)
                self.assertEqual(ciclo.horas[-1].fim_utc.hour, 3)
                self.assertEqual(ciclo.horas[-1].hora_local, 23)
                self.assertTrue(all(d.horas == 24 for d in ciclo.dias))

    def test_convencao_registro_marca_o_fim_do_intervalo(self):
        """Centroide da radiação no meio do intervalo (HH − 0,5) cai no meio-dia solar; no início daria 1 h depois."""
        for meses in ((7, 8), (1, 2, 3)):
            with self.subTest(meses=meses):
                centroide_fim, meio_dia = centroide_radiacao(self.serie, self.estacao, meses, -0.5)
                centroide_inicio, _ = centroide_radiacao(self.serie, self.estacao, meses, +0.5)
                self.assertLess(abs(centroide_fim - meio_dia), 0.1)
                self.assertGreater(abs(centroide_inicio - meio_dia), 0.9)
        c_jul_ago, noon_jul_ago = centroide_radiacao(self.serie, self.estacao, (7, 8), -0.5)
        self.assertAlmostEqual(c_jul_ago, 15.16, delta=0.005)
        self.assertAlmostEqual(noon_jul_ago, 15.14, delta=0.005)
        c_jan_mar, noon_jan_mar = centroide_radiacao(self.serie, self.estacao, (1, 2, 3), -0.5)
        self.assertAlmostEqual(c_jan_mar, 15.22, delta=0.005)
        self.assertAlmostEqual(noon_jan_mar, 15.25, delta=0.005)


class TestRegrasDeFalta(BaseSerie2023):
    INICIO, FIM = CICLOS_2023["seco"]

    def test_radiacao_vazia_de_dia_e_erro(self):
        meio_dia = datetime(2023, 7, 20, 15, tzinfo=timezone.utc)
        serie = self.serie_com_registro_alterado(meio_dia, rs_kj_m2=None)
        with self.assertRaises(DadoClimaticoAusente):
            extrair_ciclo(serie, self.estacao, "seco", self.INICIO, self.FIM)

    def test_radiacao_vazia_a_noite_vale_zero(self):
        noite = datetime(2023, 7, 20, 3, tzinfo=timezone.utc)
        h = next(h for h in self.serie if h.fim_utc == noite)
        self.assertTrue(h.rs_vazia)
        self.assertEqual(h.ra_mj, 0.0)
        self.assertEqual(h.rs_mj, 0.0)
        self.assertEqual(h.falhas, [])

    def test_radiacao_negativa_vale_zero(self):
        meio_dia = datetime(2023, 7, 20, 15, tzinfo=timezone.utc)
        serie = self.serie_com_registro_alterado(meio_dia, rs_kj_m2=-12.0)
        h = next(h for h in serie if h.fim_utc == meio_dia)
        self.assertEqual(h.rs_mj, 0.0)
        extrair_ciclo(serie, self.estacao, "seco", self.INICIO, self.FIM)

    def test_outra_variavel_vazia_no_ciclo_e_erro(self):
        hora = datetime(2023, 8, 2, 10, tzinfo=timezone.utc)
        for chave in ("p_mm", "t_c", "ur_pct", "u10_ms", "tmax_c", "tmin_c", "urmin_pct"):
            with self.subTest(variavel=chave):
                serie = self.serie_com_registro_alterado(hora, **{chave: None})
                with self.assertRaises(DadoClimaticoAusente):
                    extrair_ciclo(serie, self.estacao, "seco", self.INICIO, self.FIM)

    def test_falta_fora_do_ciclo_nao_impede_o_ciclo(self):
        fora = datetime(2023, 5, 10, 15, tzinfo=timezone.utc)
        serie = self.serie_com_registro_alterado(fora, rs_kj_m2=None, t_c=None)
        extrair_ciclo(serie, self.estacao, "seco", self.INICIO, self.FIM)


class TestConferenciaIndependenteClima(BaseSerie2023):
    """Valores de conferência calculados por uma implementação independente do v2."""

    REFERENCIA = {
        "chuvoso": dict(chuva=299.2, et0_pm=279.0, neg_h=694, neg_mm=-8.23, et0_hs=357.4, vies=28.1,
                        dias_chuva=41, maior_dia=(77.8, date(2023, 3, 17)), maior_hora=40.0,
                        t_media=25.63, u2=0.71, rs_vazia=5),
        "seco": dict(chuva=42.2, et0_pm=358.5, neg_h=706, neg_mm=-14.16, et0_hs=409.4, vies=14.2,
                     dias_chuva=4, maior_dia=(26.2, date(2023, 8, 31)), maior_hora=16.2,
                     t_media=27.36, u2=1.04, rs_vazia=31),
    }

    def assertSoma(self, obtido, referencia):
        self.assertLessEqual(abs(obtido - referencia), TOL_SOMA * abs(referencia), f"{obtido} × {referencia}")

    def test_constantes_do_local(self):
        p = fao56.pressao_atmosferica(self.estacao.altitude)
        self.assertAlmostEqual(p, 98.14, delta=0.005)
        self.assertAlmostEqual(fao56.constante_psicrometrica(p), 0.06526, delta=0.000005)
        self.assertAlmostEqual(fao56.fator_vento_2m(10.0), 0.7480, delta=0.00005)

    def test_valores_de_cada_ciclo(self):
        for nome, ref in self.REFERENCIA.items():
            c = self.ciclos[nome]
            with self.subTest(ciclo=nome):
                pm = sum(h.et0_mm for h in c.horas)
                hs = sum(d.et0_hs_mm for d in c.dias)
                negativas = [h.et0_bruta_mm for h in c.horas if h.et0_bruta_mm < 0]
                self.assertEqual(len(c.horas), 1680)
                self.assertSoma(sum(h.p_mm for h in c.horas), ref["chuva"])
                self.assertSoma(pm, ref["et0_pm"])
                self.assertEqual(len(negativas), ref["neg_h"])
                self.assertSoma(sum(negativas), ref["neg_mm"])
                self.assertSoma(hs, ref["et0_hs"])
                self.assertAlmostEqual((hs - pm) / pm * 100, ref["vies"], delta=0.05)
                self.assertEqual(sum(d.p_mm > 0 for d in c.dias), ref["dias_chuva"])
                maior = max(c.dias, key=lambda d: d.p_mm)
                self.assertAlmostEqual(maior.p_mm, ref["maior_dia"][0], places=6)
                self.assertEqual(maior.data, ref["maior_dia"][1])
                self.assertAlmostEqual(max(h.p_mm for h in c.horas), ref["maior_hora"], places=6)
                self.assertAlmostEqual(statistics.fmean(h.t_c for h in c.horas), ref["t_media"], delta=0.005)
                self.assertAlmostEqual(statistics.fmean(h.u2_ms for h in c.horas), ref["u2"], delta=0.005)
                vazias = [h for h in c.horas if h.rs_vazia and h.ra_mj > 0]
                self.assertEqual(len(vazias), ref["rs_vazia"])
                self.assertTrue(all(h.fim_utc.hour == 22 for h in vazias))
                self.assertLessEqual(max(h.ra_mj for h in vazias), 0.094)

    def test_rs_rso_bruta_no_ano(self):
        razoes = [h.termos.rs_rso_bruta for h in self.serie if h.termos is not None and h.ra_mj > 1.5]
        self.assertAlmostEqual(max(razoes), 1.109, delta=0.0005)
        self.assertAlmostEqual(statistics.quantiles(razoes, n=100, method="inclusive")[98], 1.021, delta=0.0005)


if __name__ == "__main__":
    unittest.main()
