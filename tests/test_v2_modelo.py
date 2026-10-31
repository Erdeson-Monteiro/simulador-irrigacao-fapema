"""
Testes do modelo v2 de balanço hídrico horário.

- Não antecipação: mudar P e ET0 das horas ≥ k não muda as lâminas das horas ≤ k.
- Conservação de massa, Ks (eq. 84), curva de Kc (eq. 66), E3 = E2 sem limite de reservatório,
  camada 2 inerte com f_ext2 = 0, secagem, saturação.
- Regressão: o v1 reproduz os valores de controle da linha de base (tag `v1-parecer`).
"""

from __future__ import annotations

from dataclasses import asdict
import math
import tempfile
import unittest

from src.v2.clima import carregar_ciclos
from src.v2.modelo import (
    ESTRATEGIAS,
    SEQUEIRO,
    Forcante,
    coeficiente_estresse,
    forcante_do_ciclo,
    proximo_dia_de_reposicao,
    simular,
)
from src.v2.parametros import CENARIOS, PARAMETROS_PADRAO, Cenario, escalonar_fases


def forcante_sintetica(p_mm, et0_mm):
    """Forçante de teste (não é dado climático): horas consecutivas a partir do dia 1, 00:00."""
    n = len(p_mm)
    return Forcante(
        rotulos=[f"h{k}" for k in range(n)],
        dia=[k // 24 + 1 for k in range(n)],
        hora_local=[k % 24 for k in range(n)],
        p_mm=list(p_mm),
        et0_mm=list(et0_mm),
    )


class BaseCiclos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.forcantes = {nome: forcante_do_ciclo(c) for nome, c in carregar_ciclos().items()}

    def sequeiro(self, nome, par=PARAMETROS_PADRAO):
        return simular(SEQUEIRO, self.forcantes[nome], par, nome_ciclo=nome)

    def rodadas_principais(self, par=PARAMETROS_PADRAO):
        for nome, f in self.forcantes.items():
            seq = simular(SEQUEIRO, f, par, nome_ciclo=nome)
            yield seq
            for cen in CENARIOS.values():
                for e in ESTRATEGIAS:
                    yield simular(e, f, par, cen, nome, seq.metricas.percolacao_mm)


class TestParametrosEKc(unittest.TestCase):
    def test_derivados(self):
        p = PARAMETROS_PADRAO
        self.assertAlmostEqual(p.taw_mm, 28.0, places=10)
        self.assertAlmostEqual(p.raw_mm, 8.4, places=10)
        self.assertAlmostEqual(p.theta_lim, 0.238, places=10)
        self.assertAlmostEqual(p.theta1_0, p.theta_cc, places=12)
        self.assertAlmostEqual(p.theta2_0, p.theta_cc, places=12)

    def test_fases_escalonadas_da_tabela_11(self):
        self.assertEqual(escalonar_fases((20, 30, 15, 10), 70), (19, 28, 14, 9))
        self.assertEqual(PARAMETROS_PADRAO.fases_dias, (19, 28, 14, 9))

    def test_curva_de_kc(self):
        p = PARAMETROS_PADRAO
        self.assertAlmostEqual(p.kc(1), 0.70, places=12)
        self.assertAlmostEqual(p.kc(19), 0.70, places=12)
        self.assertAlmostEqual(p.kc(20), 0.7107, delta=0.00005)
        self.assertAlmostEqual(p.kc(47), 1.00, places=12)
        self.assertAlmostEqual(p.kc(48), 1.00, places=12)
        self.assertAlmostEqual(p.kc(61), 1.00, places=12)
        self.assertAlmostEqual(p.kc(62), 0.9944, delta=0.00005)
        self.assertAlmostEqual(p.kc(70), 0.950, places=12)
        self.assertAlmostEqual(sum(p.kc(i) for i in range(1, 71)), 60.000, places=9)

    def test_ks_eq_84(self):
        p = PARAMETROS_PADRAO
        self.assertEqual(coeficiente_estresse(0.0, p.taw_mm, p.raw_mm), 1.0)
        self.assertEqual(coeficiente_estresse(p.raw_mm, p.taw_mm, p.raw_mm), 1.0)
        self.assertAlmostEqual(coeficiente_estresse((p.raw_mm + p.taw_mm) / 2, p.taw_mm, p.raw_mm), 0.5, places=12)
        self.assertAlmostEqual(coeficiente_estresse(p.taw_mm, p.taw_mm, p.raw_mm), 0.0, places=12)

    def test_calendario_de_reposicao(self):
        self.assertEqual(proximo_dia_de_reposicao(1, 14), 15)
        self.assertEqual(proximo_dia_de_reposicao(14, 14), 15)
        self.assertEqual(proximo_dia_de_reposicao(15, 14), 29)
        self.assertEqual(proximo_dia_de_reposicao(70, 3), 73)


class TestNaoAntecipacao(BaseCiclos):
    """Prova de que nenhuma estratégia usa chuva ou ET0 da hora em que decide."""

    HORAS_K = (1, 23, 24, 25, 400, 777, 1000, 1300, 1679)

    def test_laminas_ate_k_nao_mudam(self):
        alguma_mudanca_depois = False
        for nome, f in self.forcantes.items():
            for cen in (CENARIOS["Abundante"], CENARIOS["Restrito"]):
                for e in ESTRATEGIAS:
                    base = simular(e, f, PARAMETROS_PADRAO, cen, nome).serie["i_mm"]
                    for k in self.HORAS_K:
                        p_alt = [p + (30.0 if h >= k else 0.0) for h, p in enumerate(f.p_mm)]
                        et0_alt = [x * 2.0 + 0.5 if h >= k else x for h, x in enumerate(f.et0_mm)]
                        alt = simular(e, f.com(p_mm=p_alt, et0_mm=et0_alt), PARAMETROS_PADRAO, cen, nome).serie["i_mm"]
                        with self.subTest(ciclo=nome, cenario=cen.nome, estrategia=e, k=k):
                            self.assertEqual(base[: k + 1], alt[: k + 1])
                        alguma_mudanca_depois |= base[k + 1:] != alt[k + 1:]
        self.assertTrue(alguma_mudanca_depois, "a alteração não teve efeito nenhum: teste vazio")


class TestPropriedadesFisicas(BaseCiclos):
    def test_conservacao_de_massa_em_todas_as_rodadas(self):
        for par in (PARAMETROS_PADRAO, PARAMETROS_PADRAO.com(z1_mm=300.0), PARAMETROS_PADRAO.com(lamina_e1_mm=30.0)):
            for r in self.rodadas_principais(par):
                with self.subTest(z1=par.z1_mm, L=par.lamina_e1_mm, ciclo=r.ciclo, cenario=r.metricas.cenario, estrategia=r.estrategia):
                    self.assertLess(abs(r.metricas.erro_balanco_mm), 1e-6)

    def test_e3_igual_a_e2_com_reservatorio_que_nunca_limita(self):
        for nome, f in self.forcantes.items():
            for n in (3, 7, 14):
                cen = Cenario("Ilimitado", 1e6, n)
                e2 = simular("E2", f, PARAMETROS_PADRAO, cen, nome)
                e3 = simular("E3", f, PARAMETROS_PADRAO, cen, nome)
                with self.subTest(ciclo=nome, intervalo=n):
                    self.assertEqual(e2.serie, e3.serie)
                    m2, m3 = asdict(e2.metricas), asdict(e3.metricas)
                    m2.pop("estrategia"), m3.pop("estrategia")
                    self.assertEqual(m2, m3)

    def test_camada_2_inerte_com_f_ext2_zero(self):
        for r in self.rodadas_principais():
            with self.subTest(ciclo=r.ciclo, cenario=r.metricas.cenario, estrategia=r.estrategia):
                for d1, d2 in zip(r.serie["d1_mm"], r.serie["d2_mm"]):
                    self.assertAlmostEqual(d1, d2, delta=1e-9)
                self.assertLess(max(abs(t - PARAMETROS_PADRAO.theta_cc) for t in r.serie["theta2"]), 1e-12)

    def test_theta_sat_e_z2_nao_mudam_nenhuma_metrica(self):
        referencia = [asdict(r.metricas) for r in self.rodadas_principais()]
        for mudanca in ({"theta_sat": 0.40}, {"theta_sat": 0.50}, {"z2_mm": 100.0}, {"z2_mm": 300.0}):
            variante = [asdict(r.metricas) for r in self.rodadas_principais(PARAMETROS_PADRAO.com(**mudanca))]
            for m_ref, m_var in zip(referencia, variante):
                for chave, v_ref in m_ref.items():
                    v_var = m_var[chave]
                    with self.subTest(mudanca=mudanca, ciclo=m_ref["ciclo"], cenario=m_ref["cenario"],
                                      estrategia=m_ref["estrategia"], metrica=chave):
                        if isinstance(v_ref, float):
                            self.assertAlmostEqual(v_ref, v_var, delta=1e-9)
                        else:
                            self.assertEqual(v_ref, v_var)

    def test_kc_constante_dentro_do_dia(self):
        r = self.sequeiro("seco")
        for d in range(70):
            self.assertEqual(len(set(r.serie["kc"][24 * d: 24 * (d + 1)])), 1)

    def test_secagem_monotonica_sem_passar_do_pmp(self):
        f = forcante_sintetica([0.0] * 24 * 60, [0.6] * 24 * 60)
        r = simular(SEQUEIRO, f, PARAMETROS_PADRAO)
        theta = [PARAMETROS_PADRAO.theta1_0] + r.serie["theta1"]
        self.assertTrue(all(b <= a for a, b in zip(theta, theta[1:])))
        self.assertGreaterEqual(min(theta), PARAMETROS_PADRAO.theta_pmp)
        self.assertLess(theta[-1], PARAMETROS_PADRAO.theta_pmp + 0.01)
        self.assertEqual(sum(r.serie["i_mm"]), 0.0)

    def test_saturacao_drena_tudo_na_mesma_hora(self):
        r = simular(SEQUEIRO, forcante_sintetica([250.0], [0.0]), PARAMETROS_PADRAO)
        self.assertAlmostEqual(r.serie["d1_mm"][0], 250.0, places=9)
        self.assertAlmostEqual(r.serie["d2_mm"][0], 250.0, places=9)
        self.assertAlmostEqual(r.serie["theta1"][0], PARAMETROS_PADRAO.theta_cc, places=12)
        self.assertAlmostEqual(r.serie["theta2"][0], PARAMETROS_PADRAO.theta_cc, places=12)

    def test_deteccao_em_no_maximo_uma_hora(self):
        """Com água sobrando, cada acionamento é precedido de no máximo uma hora com Dr > RAW."""
        raw = PARAMETROS_PADRAO.raw_mm
        for nome, f in self.forcantes.items():
            for e in ("E1", "E2"):
                r = simular(e, f, PARAMETROS_PADRAO, CENARIOS["Abundante"], nome)
                dr, irr = r.serie["dr_mm"], r.serie["i_mm"]
                with self.subTest(ciclo=nome, estrategia=e):
                    for h, i in enumerate(irr):
                        if i > 0:
                            self.assertGreater(h, 0)
                            self.assertGreaterEqual(dr[h - 1], raw - 1e-9)
                            self.assertFalse(h >= 2 and dr[h - 2] > raw + 1e-9 and irr[h - 1] == 0)
                        elif h > 0:
                            self.assertLess(dr[h - 1], raw - 1e-9)


class TestRegressaoV1(unittest.TestCase):
    """O v1 continua reproduzindo os valores de controle da linha de base (tag `v1-parecer`)."""

    CONTROLE = [
        ("Estacao_Chuvosa", "Abundante", "E1", 190.00, 72.86, 19),
        ("Estacao_Chuvosa", "Abundante", "E2", 196.92, 97.14, 16),
        ("Estacao_Seca", "Abundante", "E1", 350.00, 50.00, 35),
        ("Estacao_Seca", "Abundante", "E2", 363.61, 100.00, 31),
        ("Estacao_Chuvosa", "Restrito", "E3", 175.86, 74.29, 35),
        ("Estacao_Seca", "Restrito", "E3", 241.67, 25.71, 64),
    ]

    def test_valores_de_controle(self):
        from src.climate import DEFAULT_RAW_INMET_CSV, carregar_e_tratar_serie_climatica
        from src.water_balance import SCENARIOS_PADRAO, SoilParams, simular_estrategia

        with tempfile.TemporaryDirectory() as tmp:
            dados = carregar_e_tratar_serie_climatica(DEFAULT_RAW_INMET_CSV, diretorio_processed=tmp)
        for periodo, cenario, estrategia, aplicada, conforto, acion in self.CONTROLE:
            m = simular_estrategia(
                estrategia_codigo=estrategia, serie_climatica=dados["series"][periodo],
                latitude_deg=dados["latitude_deg"], soil=SoilParams(),
                cenario=SCENARIOS_PADRAO[cenario], periodo_nome=periodo,
            )["metricas"]
            with self.subTest(periodo=periodo, cenario=cenario, estrategia=estrategia):
                self.assertEqual(m.lamina_total_mm, aplicada)
                self.assertEqual(m.conforto_hidrico_pct, conforto)
                self.assertEqual(m.numero_acionamentos, acion)
        seq = simular_estrategia(
            estrategia_codigo="SEQUEIRO", serie_climatica=dados["series"]["Estacao_Chuvosa"],
            latitude_deg=dados["latitude_deg"], soil=SoilParams(),
            cenario=SCENARIOS_PADRAO["Abundante"], periodo_nome="Estacao_Chuvosa",
        )["metricas"]
        self.assertEqual(seq.percolacao_acumulada_mm, 84.39)


if __name__ == "__main__":
    unittest.main()
