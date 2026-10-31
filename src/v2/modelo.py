"""
Modelo v2: balanço hídrico horário em duas camadas com Ks do FAO-56 (docs/MODELO.md, seções 4 e 5).

Ordem do passo horário (obrigatória):
  1. decisão no início da hora h, com o estado no fim da hora h−1 → lâmina pedida;
  2. reservatório: I = mín(pedida; V/A); V ← V − I·A (pulso no início da hora);
  3. Ks pela depleção depois da irrigação (FAO-56, eq. 84);
  4. ETc = Kc·ET0; ETa = Ks·ETc, limitada para θ₁ nunca ficar abaixo de θpmp;
  5. camada 1: S₁ = θ₁·z₁ + I + P − ETa₁; D₁ = máx(0; S₁ − θcc·z₁);
  6. camada 2: S₂ = θ₂·z₂ + D₁ − ETa₂; D₂ = máx(0; S₂ − θcc·z₂);
  7. percolação profunda = D₂;
  8. sem escoamento superficial e com drenagem instantânea dentro da hora;
  9. reservatório cheio às 00:00 locais do dia 1 e reposto às 00:00 dos dias 1 + N, 1 + 2N, …
Com f_ext2 = 0 (padrão), ETa₁ = ETa e ETa₂ = 0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from src.v2.clima import CicloClima
from src.v2.parametros import Cenario, ParametrosModelo


ESTRATEGIAS = ("E1", "E2", "E3")
SEQUEIRO = "Sequeiro"
NOMES_ESTRATEGIAS = {
    "E1": "limiar fixo",
    "E2": "reposição por balanço hídrico",
    "E3": "racionamento uniforme",
    SEQUEIRO: "sequeiro (sem irrigação)",
}

EPS_LAMINA_MM = 1e-9      # lâmina abaixo disso é tratada como zero (resíduo de ponto flutuante)
EPS_GATILHO_MM = 1e-9     # folga numérica na comparação Dr ≥ RAW
LIMIAR_VAZIO_L = 0.5      # reservatório "vazio" no fim de uma hora

COLUNAS_SERIE = (
    "p_mm", "et0_mm", "kc", "etc_mm", "ks", "eta_mm", "i_mm",
    "theta1", "theta2", "dr_mm", "d1_mm", "d2_mm", "v_l",
)


@dataclass(frozen=True)
class Forcante:
    """Entrada horária do modelo: chuva e ET0 por hora, dia do ciclo e hora local."""
    rotulos: Sequence[str]         # início da hora em hora local, 'AAAA-MM-DD HH:MM'
    dia: Sequence[int]             # dia do ciclo, 1..n
    hora_local: Sequence[int]      # 0..23
    p_mm: Sequence[float]
    et0_mm: Sequence[float]

    def __len__(self) -> int:
        return len(self.p_mm)

    def com(self, p_mm: Optional[Sequence[float]] = None, et0_mm: Optional[Sequence[float]] = None) -> "Forcante":
        return Forcante(
            self.rotulos, self.dia, self.hora_local,
            list(self.p_mm if p_mm is None else p_mm),
            list(self.et0_mm if et0_mm is None else et0_mm),
        )


def forcante_do_ciclo(ciclo: CicloClima) -> Forcante:
    return Forcante(
        rotulos=[h.inicio_local.strftime("%Y-%m-%d %H:%M") for h in ciclo.horas],
        dia=[k // 24 + 1 for k in range(len(ciclo.horas))],
        hora_local=[h.hora_local for h in ciclo.horas],
        p_mm=[h.p_mm for h in ciclo.horas],
        et0_mm=[h.et0_mm for h in ciclo.horas],
    )


def coeficiente_estresse(dr_mm: float, taw_mm: float, raw_mm: float) -> float:
    """FAO-56, eq. 84: Ks = 1 se Dr ≤ RAW; senão (TAW − Dr)/(TAW − RAW), limitado a [0, 1]."""
    if dr_mm <= raw_mm:
        return 1.0
    return max(0.0, min(1.0, (taw_mm - dr_mm) / (taw_mm - raw_mm)))


def proximo_dia_de_reposicao(dia: int, intervalo: int) -> int:
    """Próximo dia de reposição depois de `dia`, no calendário 1, 1 + N, 1 + 2N, …"""
    return 1 + intervalo * ((dia - 1) // intervalo + 1)


@dataclass
class Metricas:
    estrategia: str
    cenario: str
    ciclo: str
    lamina_e1_mm: Optional[float]
    horas: int
    horas_sem_estresse: int
    tse_pct: float
    tse_diaria_pct: float
    eta_mm: float
    etc_mm: float
    eta_etc_pct: float
    dr_max_mm: float
    theta1_min: float
    chuva_mm: float
    aplicada_mm: float
    acionamentos: int
    lamina_media_mm: Optional[float]
    percolacao_mm: float
    percolacao_sequeiro_mm: Optional[float]
    percolacao_incremental_mm: Optional[float]
    eficiencia_incremental_pct: Optional[float]
    dias_reservatorio_vazio: Optional[int]
    primeiro_dia_vazio: Optional[int]
    erro_balanco_mm: float


@dataclass
class Rodada:
    estrategia: str
    cenario: Optional[Cenario]
    ciclo: str
    parametros: ParametrosModelo
    forcante: Forcante
    serie: Dict[str, List[float]]
    metricas: Metricas
    detalhe: Dict[str, object] = field(default_factory=dict)


def simular(
    estrategia: str,
    forcante: Forcante,
    parametros: ParametrosModelo,
    cenario: Optional[Cenario] = None,
    nome_ciclo: str = "",
    percolacao_sequeiro_mm: Optional[float] = None,
) -> Rodada:
    """
    Simula um ciclo hora a hora para E1, E2, E3 ou o sequeiro.

    Todas as estratégias decidem no início de cada hora h usando apenas informação disponível
    até o fim da hora h−1. Nenhuma conhece a chuva nem a ET0 da hora h. Para isolar o efeito
    da **regra de decisão**, todas recebem informação perfeita do estado do solo: E1 lê a
    umidade real da camada 1 (sensor sem erro, lido de hora em hora) e E2/E3 conhecem a
    depleção real, calculada pelo mesmo balanço do FAO-56. Erros de sensor e de estimativa
    ficam para a fase de campo.

    - E1, limiar fixo: se θ₁ ≤ θlim (equivale a Dr ≥ RAW), pede a lâmina fixa L.
    - E2, reposição por balanço hídrico: se Dr ≥ RAW, pede Dr (repõe até θcc).
    - E3, racionamento uniforme: às 00:00 locais calcula a cota do dia, B = (V/A)/n, com n o
      número de dias até a próxima reposição, contando o dia atual; durante o dia, se
      Dr ≥ RAW, pede mín(Dr; B − já aplicado no dia). Conhece o calendário de reposição.
    - Sequeiro: I = 0 (contrafactual da percolação incremental).
    """
    if estrategia not in ESTRATEGIAS and estrategia != SEQUEIRO:
        raise ValueError(f"Estratégia desconhecida: {estrategia}")
    if estrategia != SEQUEIRO and cenario is None:
        raise ValueError(f"A estratégia {estrategia} precisa de um cenário de reservatório.")

    par = parametros
    z1, z2, area = par.z1_mm, par.z2_mm, par.area_m2
    taw, raw, theta_lim = par.taw_mm, par.raw_mm, par.theta_lim
    s1_cc, s1_pmp = par.theta_cc * z1, par.theta_pmp * z1
    s2_cc, s2_pmp = par.theta_cc * z2, par.theta_pmp * z2
    lamina_e1 = par.lamina_e1_mm

    s1 = par.theta1_0 * z1
    s2 = par.theta2_0 * z2
    s_inicial = s1 + s2
    v = cenario.capacidade_l if cenario is not None else None
    cota_dia = aplicado_dia = 0.0

    serie: Dict[str, List[float]] = {c: [] for c in COLUNAS_SERIE}
    for k in range(len(forcante)):
        dia, hora = forcante.dia[k], forcante.hora_local[k]
        p, et0 = forcante.p_mm[k], forcante.et0_mm[k]

        if hora == 0:
            aplicado_dia = 0.0
            if cenario is not None:
                if (dia - 1) % cenario.intervalo_dias == 0:
                    v = cenario.capacidade_l
                n = proximo_dia_de_reposicao(dia, cenario.intervalo_dias) - dia
                cota_dia = (v / area) / n

        # 1. Decisão com o estado no fim da hora anterior.
        dr_anterior = s1_cc - s1
        pedido = 0.0
        if estrategia == "E1":
            if s1 / z1 <= theta_lim + EPS_GATILHO_MM / z1:
                pedido = lamina_e1
        elif estrategia == "E2":
            if dr_anterior >= raw - EPS_GATILHO_MM:
                pedido = dr_anterior
        elif estrategia == "E3":
            if dr_anterior >= raw - EPS_GATILHO_MM:
                pedido = min(dr_anterior, max(0.0, cota_dia - aplicado_dia))
        if pedido < EPS_LAMINA_MM:
            pedido = 0.0

        # 2. Reservatório.
        irrigacao = 0.0
        if pedido > 0.0 and v is not None:
            irrigacao = min(pedido, v / area)
            if irrigacao < EPS_LAMINA_MM:
                irrigacao = 0.0
            v = max(0.0, v - irrigacao * area)
            if v < EPS_LAMINA_MM:
                v = 0.0
        aplicado_dia += irrigacao

        # 3. Ks pela depleção depois da irrigação.
        s1 += irrigacao
        ks = coeficiente_estresse(s1_cc - s1, taw, raw)

        # 4. ETc e ETa (ETa₁ limitada para θ₁ não passar de θpmp).
        kc = par.kc(dia)
        etc = kc * et0
        eta = ks * etc
        eta1 = min((1.0 - par.f_ext2) * eta, max(0.0, s1 + p - s1_pmp))
        eta2_pedida = par.f_ext2 * eta

        # 5. Camada 1.
        s1 = s1 + p - eta1
        d1 = max(0.0, s1 - s1_cc)
        s1 -= d1

        # 6–7. Camada 2 e percolação profunda.
        s2 = s2 + d1
        eta2 = min(eta2_pedida, max(0.0, s2 - s2_pmp))
        s2 -= eta2
        d2 = max(0.0, s2 - s2_cc)
        s2 -= d2

        serie["p_mm"].append(p)
        serie["et0_mm"].append(et0)
        serie["kc"].append(kc)
        serie["etc_mm"].append(etc)
        serie["ks"].append(ks)
        serie["eta_mm"].append(eta1 + eta2)
        serie["i_mm"].append(irrigacao)
        serie["theta1"].append(s1 / z1)
        serie["theta2"].append(s2 / z2)
        serie["dr_mm"].append(s1_cc - s1)
        serie["d1_mm"].append(d1)
        serie["d2_mm"].append(d2)
        serie["v_l"].append(v if v is not None else float("nan"))

    metricas = calcular_metricas(
        estrategia, cenario, nome_ciclo, par, forcante, serie, s_inicial, s1 + s2, percolacao_sequeiro_mm
    )
    return Rodada(estrategia, cenario, nome_ciclo, par, forcante, serie, metricas)


def calcular_metricas(
    estrategia: str,
    cenario: Optional[Cenario],
    nome_ciclo: str,
    par: ParametrosModelo,
    forcante: Forcante,
    serie: Dict[str, List[float]],
    s_inicial: float,
    s_final: float,
    percolacao_sequeiro_mm: Optional[float],
) -> Metricas:
    n = len(serie["dr_mm"])
    raw = par.raw_mm
    sem_estresse = [dr <= raw + EPS_GATILHO_MM for dr in serie["dr_mm"]]
    dia_ok: Dict[int, bool] = {}
    for ok, d in zip(sem_estresse, forcante.dia):
        dia_ok[d] = dia_ok.get(d, True) and ok
    dias = sorted(dia_ok)
    dias_sem_estresse = sum(dia_ok.values())
    chuva, aplicada = sum(serie["p_mm"]), sum(serie["i_mm"])
    eta, etc = sum(serie["eta_mm"]), sum(serie["etc_mm"])
    percolacao = sum(serie["d2_mm"])
    acionamentos = sum(1 for i in serie["i_mm"] if i > 0.0)

    perc_incr = efic = None
    if percolacao_sequeiro_mm is not None:
        perc_incr = percolacao - percolacao_sequeiro_mm
        if aplicada > 0.0:
            efic = (aplicada - perc_incr) / aplicada * 100.0

    dias_vazio = primeiro_vazio = None
    if cenario is not None:
        vazios = sorted({d for d, vol in zip(forcante.dia, serie["v_l"]) if vol < LIMIAR_VAZIO_L})
        dias_vazio = len(vazios)
        primeiro_vazio = vazios[0] if vazios else None

    return Metricas(
        estrategia=estrategia,
        cenario=cenario.nome if cenario is not None else SEQUEIRO,
        ciclo=nome_ciclo,
        lamina_e1_mm=par.lamina_e1_mm if estrategia == "E1" else None,
        horas=n,
        horas_sem_estresse=sum(sem_estresse),
        tse_pct=100.0 * sum(sem_estresse) / n,
        tse_diaria_pct=100.0 * dias_sem_estresse / len(dias),
        eta_mm=eta,
        etc_mm=etc,
        eta_etc_pct=100.0 * eta / etc if etc > 0 else 100.0,
        dr_max_mm=max(serie["dr_mm"]),
        theta1_min=min(serie["theta1"]),
        chuva_mm=chuva,
        aplicada_mm=aplicada,
        acionamentos=acionamentos,
        lamina_media_mm=aplicada / acionamentos if acionamentos else None,
        percolacao_mm=percolacao,
        percolacao_sequeiro_mm=percolacao_sequeiro_mm,
        percolacao_incremental_mm=perc_incr,
        eficiencia_incremental_pct=efic,
        dias_reservatorio_vazio=dias_vazio,
        primeiro_dia_vazio=primeiro_vazio,
        erro_balanco_mm=(s_final - s_inicial) - (chuva + aplicada - eta - percolacao),
    )
