"""
Rodadas do v1 para a comparação v1 × v2. Usa o código do v1 sem alteração
(`src/water_balance.py` e `src/climate.py`), com os números da linha de base (tag `v1-parecer`).
"""

from __future__ import annotations

from dataclasses import dataclass
import inspect
import tempfile
from typing import Dict, Sequence, Tuple

from src.climate import DEFAULT_RAW_INMET_CSV, carregar_e_tratar_serie_climatica
from src.water_balance import SCENARIOS_PADRAO, SoilParams, simular_estrategia


CICLO_V1 = {"chuvoso": "Estacao_Chuvosa", "seco": "Estacao_Seca"}


LIMIAR_DEFICIT_V1_MM = inspect.signature(simular_estrategia).parameters["limiar_deficit_mm"].default


@dataclass
class ResultadosV1:
    metricas: Dict[Tuple[str, str, str], dict]                # (ciclo, cenário, estratégia)
    sensibilidade_e1: Dict[Tuple[str, str, float], dict]     # (ciclo, cenário, L)
    soil: SoilParams
    limiar_deficit_mm: float


def rodar_v1(laminas_e1: Sequence[float] = (5.0, 10.0, 15.0, 20.0, 25.0, 30.0)) -> ResultadosV1:
    """Métricas do v1 por (ciclo, cenário, estratégia), sequeiro e sensibilidade de E1."""
    with tempfile.TemporaryDirectory() as tmp:
        dados = carregar_e_tratar_serie_climatica(DEFAULT_RAW_INMET_CSV, diretorio_processed=tmp)
    soil = SoilParams()
    metricas: Dict[Tuple[str, str, str], dict] = {}
    sens: Dict[Tuple[str, str, float], dict] = {}
    for ciclo, periodo in CICLO_V1.items():
        serie = dados["series"][periodo]
        comum = dict(serie_climatica=serie, latitude_deg=dados["latitude_deg"], soil=soil, periodo_nome=periodo)
        seq = simular_estrategia(estrategia_codigo="SEQUEIRO", cenario=SCENARIOS_PADRAO["Abundante"], **comum)
        perc_seq = seq["metricas"].percolacao_acumulada_mm
        metricas[(ciclo, "Sequeiro", "Sequeiro")] = vars(seq["metricas"])
        for cenario, cfg in SCENARIOS_PADRAO.items():
            for estrategia in ("E1", "E2", "E3"):
                r = simular_estrategia(estrategia_codigo=estrategia, cenario=cfg,
                                       d2_chuva_referencia_mm=perc_seq, **comum)
                metricas[(ciclo, cenario, estrategia)] = vars(r["metricas"])
            for L in laminas_e1:
                r = simular_estrategia(estrategia_codigo="E1", cenario=cfg, lamina_fixa_mm=L,
                                       d2_chuva_referencia_mm=perc_seq, **comum)
                sens[(ciclo, cenario, L)] = vars(r["metricas"])
    return ResultadosV1(metricas, sens, soil, LIMIAR_DEFICIT_V1_MM)
