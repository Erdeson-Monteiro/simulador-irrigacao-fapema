"""
Série horária em hora local, ET0 horária por Penman-Monteith (FAO-56) e ciclos de 70 dias.

Convenções (docs/MODELO.md, seção 2.1):
- O registro HH00 UTC cobre (HH−1, HH] UTC; o meio do intervalo é t = HH − 0,5 (UTC) e J é o
  dia do ano desse instante.
- Hora local = UTC − 3 (sem horário de verão). O dia local d reúne os registros de 0400 UTC
  de d a 0300 UTC de d+1.
- Regras de falta, sem imputação: radiação vazia com Ra < 0,1 MJ m⁻² h⁻¹ vale 0; radiação
  vazia com Ra ≥ 0,1 é erro; radiação negativa vale 0; qualquer outra variável vazia dentro
  de um ciclo é erro.
- Rs/Rso: medida e limitada a [0,3; 1,0] com Ra > 0; à noite (Ra = 0), a razão do período
  2–3 h antes do pôr do sol anterior (ωs − 0,79 ≤ ω ≤ ωs − 0,52), calculada como ΣRs/ΣRso
  desse período e limitada da mesma forma.
- Vento a 10 m (mastro de 10 m, NT 001/2011 do INMET; anemômetro assumido no topo).
- ET0 horária negativa (noite, condensação) vale 0 no balanço; a soma zerada fica como
  diagnóstico.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
import math
import statistics
from typing import Dict, List, Optional, Tuple

from src.v2 import fao56
from src.v2.inmet import ARQUIVO_A204_2023, EstacaoINMET, RegistroINMET, grade_horaria, ler_arquivo_inmet


FUSO_LOCAL = timezone(timedelta(hours=-3))
LZ_UTC_GRAUS = 0.0                 # hora em UTC: meridiano central Lz = 0
ALTURA_ANEMOMETRO_M = 10.0         # premissa declarada (mastro de 10 m)
LIMIAR_RA_NOITE_MJ = 0.1           # radiação vazia abaixo deste Ra vale 0
JANELA_POR_DO_SOL_RAD = (0.79, 0.52)

CICLOS_2023: Dict[str, Tuple[date, date]] = {
    "chuvoso": (date(2023, 1, 15), date(2023, 3, 25)),
    "seco": (date(2023, 7, 1), date(2023, 9, 8)),
}

VARIAVEIS_OBRIGATORIAS = ("p_mm", "t_c", "ur_pct", "u10_ms", "tmax_c", "tmin_c", "urmin_pct")


class DadoClimaticoAusente(ValueError):
    """Falta de dado dentro de um ciclo: o v2 para em vez de estimar."""


@dataclass
class HoraClima:
    fim_utc: datetime
    inicio_local: datetime
    dia_local: date
    hora_local: int
    j: int
    t_meio_utc_h: float
    p_mm: Optional[float]
    t_c: Optional[float]
    ur_pct: Optional[float]
    u10_ms: Optional[float]
    u2_ms: Optional[float]
    tmax_c: Optional[float]
    tmin_c: Optional[float]
    urmin_pct: Optional[float]
    rs_bruta_kj_m2: Optional[float]
    rs_mj: Optional[float]
    geometria: fao56.GeometriaHoraria
    rs_rso_noite: Optional[float] = None
    termos: Optional[fao56.TermosPenmanMonteith] = None
    et0_bruta_mm: Optional[float] = None
    et0_mm: Optional[float] = None
    falhas: List[str] = field(default_factory=list)

    @property
    def ra_mj(self) -> float:
        return self.geometria.ra_mj

    @property
    def rs_vazia(self) -> bool:
        return self.rs_bruta_kj_m2 is None


@dataclass
class DiaClima:
    data: date
    j: int
    horas: int
    p_mm: float
    p_max_horaria_mm: float
    et0_pm_mm: float
    et0_hs_mm: float
    tmax_c: float
    tmin_c: float
    tmed_c: float
    urmin_pct: float
    u2_medio_ms: float
    ra_dia_mj: float


@dataclass
class CicloClima:
    nome: str
    inicio: date
    fim: date
    estacao: EstacaoINMET
    horas: List[HoraClima]
    dias: List[DiaClima]

    @property
    def n_dias(self) -> int:
        return len(self.dias)


def montar_serie_horaria(
    estacao: EstacaoINMET,
    registros: List[RegistroINMET],
    ra_zerada_pelo_meio_da_hora: bool = False,
) -> List[HoraClima]:
    """
    Aplica as convenções de horário e as regras de radiação e calcula a ET0 de cada hora
    possível. `ra_zerada_pelo_meio_da_hora` troca a regra de Ra pela leitura literal do texto
    do FAO-56; serve só para o diagnóstico dessa escolha.
    """
    lat_rad = math.radians(estacao.latitude)
    lm_graus = -estacao.longitude  # longitude negativa = oeste
    fator_u2 = fao56.fator_vento_2m(ALTURA_ANEMOMETRO_M)
    serie: List[HoraClima] = []

    for reg in grade_horaria(registros):
        if reg is None:
            raise DadoClimaticoAusente("Hora sem registro no arquivo do INMET (grade horária com buraco).")
        meio = reg.fim_utc - timedelta(minutes=30)
        t_meio = meio.hour + meio.minute / 60.0
        j = meio.timetuple().tm_yday
        geo = fao56.geometria_horaria(
            j, t_meio, lat_rad, LZ_UTC_GRAUS, lm_graus, zerar_pelo_meio=ra_zerada_pelo_meio_da_hora
        )
        inicio_local = (reg.fim_utc - timedelta(hours=1)).astimezone(FUSO_LOCAL)
        v = reg.valores

        falhas: List[str] = []
        rs_kj = v["rs_kj_m2"]
        if rs_kj is None:
            if geo.ra_mj < LIMIAR_RA_NOITE_MJ:
                rs_mj: Optional[float] = 0.0
            else:
                rs_mj = None
                falhas.append(f"radiação vazia com Ra = {geo.ra_mj:.3f} MJ m⁻² h⁻¹ (≥ {LIMIAR_RA_NOITE_MJ})")
        else:
            rs_mj = max(0.0, rs_kj) / 1000.0
        for chave in VARIAVEIS_OBRIGATORIAS:
            if v[chave] is None:
                falhas.append(f"{chave} vazio")

        serie.append(HoraClima(
            fim_utc=reg.fim_utc,
            inicio_local=inicio_local,
            dia_local=inicio_local.date(),
            hora_local=inicio_local.hour,
            j=j,
            t_meio_utc_h=t_meio,
            p_mm=v["p_mm"],
            t_c=v["t_c"],
            ur_pct=v["ur_pct"],
            u10_ms=v["u10_ms"],
            u2_ms=(v["u10_ms"] * fator_u2 if v["u10_ms"] is not None else None),
            tmax_c=v["tmax_c"],
            tmin_c=v["tmin_c"],
            urmin_pct=v["urmin_pct"],
            rs_bruta_kj_m2=rs_kj,
            rs_mj=rs_mj,
            geometria=geo,
            falhas=falhas,
        ))

    _atribuir_rs_rso_noturna(serie, estacao.altitude)
    for h in serie:
        _calcular_et0(h, estacao.altitude)
    return serie


def _na_janela_por_do_sol(h: HoraClima) -> bool:
    g = h.geometria
    return h.ra_mj > 0.0 and g.omega_s - JANELA_POR_DO_SOL_RAD[0] <= g.omega <= g.omega_s - JANELA_POR_DO_SOL_RAD[1]


def _atribuir_rs_rso_noturna(serie: List[HoraClima], altitude: float) -> None:
    """Percorre a série em ordem e entrega a cada hora noturna a razão do fim da tarde anterior."""
    ultima_razao: Optional[float] = None
    soma_rs = soma_rso = 0.0
    janela_aberta = janela_incompleta = False
    for h in serie:
        if _na_janela_por_do_sol(h):
            if not janela_aberta:
                janela_aberta, janela_incompleta = True, False
                soma_rs = soma_rso = 0.0
            if h.rs_mj is None:
                janela_incompleta = True
            else:
                soma_rs += h.rs_mj
                soma_rso += fao56.radiacao_ceu_claro(h.ra_mj, altitude)
            continue
        if janela_aberta:
            janela_aberta = False
            if janela_incompleta or soma_rso <= 0.0:
                ultima_razao = None
            else:
                ultima_razao = min(fao56.RS_RSO_MAXIMO, max(fao56.RS_RSO_MINIMO, soma_rs / soma_rso))
        if h.ra_mj == 0.0:
            h.rs_rso_noite = ultima_razao
            if ultima_razao is None:
                h.falhas.append("noite sem Rs/Rso do fim da tarde anterior")


def _calcular_et0(h: HoraClima, altitude: float) -> None:
    if h.t_c is None or h.ur_pct is None or h.u2_ms is None or h.rs_mj is None:
        return
    if h.ra_mj == 0.0 and h.rs_rso_noite is None:
        return
    h.termos = fao56.et0_penman_monteith_horaria(
        h.t_c, h.ur_pct, h.u2_ms, h.rs_mj, h.ra_mj, altitude, rs_rso_noite=h.rs_rso_noite
    )
    h.et0_bruta_mm = h.termos.et0_mm_h
    h.et0_mm = max(0.0, h.termos.et0_mm_h)


def extrair_ciclo(
    serie: List[HoraClima],
    estacao: EstacaoINMET,
    nome: str,
    inicio: date,
    fim: date,
) -> CicloClima:
    """Recorta um ciclo em dias locais; qualquer falta dentro dele é erro explícito."""
    horas = [h for h in serie if inicio <= h.dia_local <= fim]
    n_dias = (fim - inicio).days + 1
    if len(horas) != 24 * n_dias:
        raise DadoClimaticoAusente(
            f"Ciclo {nome} ({inicio} a {fim}): {len(horas)} horas no arquivo, esperadas {24 * n_dias}."
        )
    falhas = [(h, f) for h in horas for f in h.falhas]
    if falhas:
        exemplos = "; ".join(
            f"{h.fim_utc:%Y-%m-%d %H%M} UTC: {f}" for h, f in falhas[:5]
        )
        raise DadoClimaticoAusente(
            f"Ciclo {nome}: {len(falhas)} falha(s) de dado sem regra de tratamento. Primeiras: {exemplos}"
        )
    sem_et0 = [h for h in horas if h.et0_mm is None]
    if sem_et0:
        raise DadoClimaticoAusente(f"Ciclo {nome}: {len(sem_et0)} hora(s) sem ET0 calculável.")

    lat_rad = math.radians(estacao.latitude)
    dias: List[DiaClima] = []
    for k in range(n_dias):
        d = inicio + timedelta(days=k)
        hs = horas[24 * k: 24 * (k + 1)]
        if any(h.dia_local != d for h in hs):
            raise DadoClimaticoAusente(f"Ciclo {nome}: horas fora de ordem no dia local {d}.")
        j = d.timetuple().tm_yday
        ra_dia = fao56.ra_diaria(j, lat_rad)
        tmax = max(h.tmax_c for h in hs)
        tmin = min(h.tmin_c for h in hs)
        tmed = statistics.fmean(h.t_c for h in hs)
        dias.append(DiaClima(
            data=d,
            j=j,
            horas=len(hs),
            p_mm=sum(h.p_mm for h in hs),
            p_max_horaria_mm=max(h.p_mm for h in hs),
            et0_pm_mm=sum(h.et0_mm for h in hs),
            et0_hs_mm=fao56.et0_hargreaves_samani(tmed, tmax, tmin, ra_dia),
            tmax_c=tmax,
            tmin_c=tmin,
            tmed_c=tmed,
            urmin_pct=min(h.urmin_pct for h in hs),
            u2_medio_ms=statistics.fmean(h.u2_ms for h in hs),
            ra_dia_mj=ra_dia,
        ))
    return CicloClima(nome=nome, inicio=inicio, fim=fim, estacao=estacao, horas=horas, dias=dias)


def carregar_ciclos(
    caminho: str = ARQUIVO_A204_2023,
    ciclos: Optional[Dict[str, Tuple[date, date]]] = None,
    verificar_sha256: bool = True,
) -> Dict[str, CicloClima]:
    estacao, registros = ler_arquivo_inmet(caminho, verificar_sha256=verificar_sha256)
    serie = montar_serie_horaria(estacao, registros)
    return {
        nome: extrair_ciclo(serie, estacao, nome, ini, fim)
        for nome, (ini, fim) in (ciclos or CICLOS_2023).items()
    }


def centroide_radiacao(
    serie: List[HoraClima],
    estacao: EstacaoINMET,
    meses: Tuple[int, ...],
    deslocamento_meio_h: float = -0.5,
) -> Tuple[float, float]:
    """
    Centroide horário (h UTC) da radiação média por hora do registro nos meses dados, com o
    meio de cada intervalo em HH + `deslocamento_meio_h` (−0,5 para registro = fim do
    intervalo; +0,5 se o registro marcasse o início), e o meio-dia solar médio em UTC, o t
    em que ω = 0 na eq. 31: t = 12 − Sc − 0,06667·(Lz − Lm). Radiação inválida é descartada.
    """
    lm_graus = -estacao.longitude
    por_hora: Dict[int, List[float]] = {hh: [] for hh in range(24)}
    dias: Dict[date, int] = {}
    for h in serie:
        if h.fim_utc.month not in meses:
            continue
        if h.rs_mj is not None:
            por_hora[h.fim_utc.hour].append(h.rs_mj)
        dias.setdefault(h.fim_utc.date(), h.fim_utc.timetuple().tm_yday)
    medias = {hh: statistics.fmean(v) for hh, v in por_hora.items() if v}
    centroide = sum(((hh + deslocamento_meio_h) % 24) * m for hh, m in medias.items()) / sum(medias.values())
    meio_dia = statistics.fmean(
        12.0 - fao56.correcao_sazonal(j) - 0.06667 * (LZ_UTC_GRAUS - lm_graus) for j in dias.values()
    )
    return centroide, meio_dia
