"""
Diagnósticos para a seção de limitações (docs/MODELO.md, seção 9). Nada aqui entra no
balanço: são grandezas que mostram o efeito de escolhas que o modelo não aplica.
"""

from __future__ import annotations

from dataclasses import dataclass
import statistics
from typing import Dict, List

from src.v2.clima import CicloClima, HoraClima
from src.v2.parametros import ParametrosModelo


ALTURA_ALFACE_M = 0.3      # FAO-56, Tabela 12 (altura máxima da cultura)
P_REFERENCIA = 0.30        # p da Tabela 22 para ETc ≈ 5 mm/d


def kc_mid_ajustado(kc_mid_tabela: float, u2_ms: float, urmin_pct: float, altura_m: float = ALTURA_ALFACE_M) -> float:
    """FAO-56, eq. 62: Kc,mid = Kc,mid(Tab) + [0,04·(u₂ − 2) − 0,004·(URmin − 45)]·(h/3)^0,3."""
    return kc_mid_tabela + (0.04 * (u2_ms - 2.0) - 0.004 * (urmin_pct - 45.0)) * (altura_m / 3.0) ** 0.3


def p_ajustado(etc_mm_dia: float, p_tabela: float = P_REFERENCIA) -> float:
    """FAO-56, Tabela 22 (nota): p = p_tab + 0,04·(5 − ETc), limitado a 0,1–0,8."""
    return min(0.8, max(0.1, p_tabela + 0.04 * (5.0 - etc_mm_dia)))


@dataclass
class DiagnosticoCiclo:
    ciclo: str
    dias_fase_media: List[int]
    u2_medio_fase_media_ms: float
    urmin_media_fase_media_pct: float
    kc_mid_ajustado: float
    kc_mid_diferenca: float
    etc_diaria_min_mm: float
    etc_diaria_max_mm: float
    p_ajustado_min: float
    p_ajustado_max: float
    et0_negativa_horas: int
    et0_negativa_soma_mm: float
    et0_pm_mm: float
    et0_pm_ra_pelo_meio_mm: float
    rs_rso_bruta_max_ciclo: float
    rs_rso_bruta_p99_ciclo: float


def percentil(valores: List[float], q: int) -> float:
    """Percentil pela interpolação linear (método 'inclusive' do statistics; igual ao padrão do numpy)."""
    return statistics.quantiles(valores, n=100, method="inclusive")[q - 1]


def diagnosticar_ciclo(ciclo: CicloClima, ciclo_ra_pelo_meio: CicloClima, par: ParametrosModelo) -> DiagnosticoCiclo:
    l_ini, l_dev, l_mid, _ = par.fases_dias
    dias_mid = list(range(l_ini + l_dev + 1, l_ini + l_dev + l_mid + 1))
    dias_obj = [ciclo.dias[d - 1] for d in dias_mid]
    u2 = statistics.fmean(d.u2_medio_ms for d in dias_obj)
    urmin = statistics.fmean(d.urmin_pct for d in dias_obj)
    kc_aj = kc_mid_ajustado(par.kc_mid, u2, urmin)
    etc_dia = [par.kc(i + 1) * d.et0_pm_mm for i, d in enumerate(ciclo.dias)]
    p_dia = [p_ajustado(e, par.p) for e in etc_dia]
    negativas = [h.et0_bruta_mm for h in ciclo.horas if h.et0_bruta_mm < 0]
    razoes = razoes_rs_rso_brutas(ciclo.horas)
    return DiagnosticoCiclo(
        ciclo=ciclo.nome,
        dias_fase_media=dias_mid,
        u2_medio_fase_media_ms=u2,
        urmin_media_fase_media_pct=urmin,
        kc_mid_ajustado=kc_aj,
        kc_mid_diferenca=kc_aj - par.kc_mid,
        etc_diaria_min_mm=min(etc_dia),
        etc_diaria_max_mm=max(etc_dia),
        p_ajustado_min=min(p_dia),
        p_ajustado_max=max(p_dia),
        et0_negativa_horas=len(negativas),
        et0_negativa_soma_mm=sum(negativas),
        et0_pm_mm=sum(h.et0_mm for h in ciclo.horas),
        et0_pm_ra_pelo_meio_mm=sum(h.et0_mm for h in ciclo_ra_pelo_meio.horas),
        rs_rso_bruta_max_ciclo=max(razoes),
        rs_rso_bruta_p99_ciclo=percentil(razoes, 99),
    )


LIMIAR_RA_RS_RSO_MJ = 1.5   # só horas com Sol alto, longe do nascer e do pôr do sol


def razoes_rs_rso_brutas(horas: List[HoraClima]) -> List[float]:
    return [h.termos.rs_rso_bruta for h in horas if h.termos is not None and h.ra_mj > LIMIAR_RA_RS_RSO_MJ]


def rs_rso_no_ano(serie: List[HoraClima]) -> Dict[str, float]:
    razoes = razoes_rs_rso_brutas(serie)
    return {"n_horas": len(razoes), "maximo": max(razoes), "p99": percentil(razoes, 99),
            "acima_de_1": sum(1 for r in razoes if r > 1.0)}
