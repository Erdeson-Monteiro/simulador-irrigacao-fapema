"""
Equações do FAO-56 (ALLEN, R. G. et al. Crop evapotranspiration: guidelines for computing
crop water requirements. Rome: FAO, 1998. FAO Irrigation and Drainage Paper 56).

Só equações, sem leitura de arquivo. Unidades: temperatura em °C; radiação em MJ m⁻² h⁻¹
(horária) ou MJ m⁻² d⁻¹ (diária); pressão em kPa; vento em m s⁻¹; ET0 em mm h⁻¹ ou mm d⁻¹.
Ângulos em radianos. Longitudes Lz e Lm em graus a oeste de Greenwich, como no FAO-56.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Optional


GSC_MJ_M2_MIN = 0.0820          # constante solar (eqs. 21 e 28)
SIGMA_HORARIA = 2.043e-10       # Stefan-Boltzmann por hora, MJ m⁻² h⁻¹ K⁻⁴ (cap. 4, eq. 53)
ALBEDO_REFERENCIA = 0.23        # grama de referência (eq. 38)
FATOR_MJ_PARA_MM = 0.408        # 1/λ, mm por MJ m⁻² (eqs. 20 e 52)
RS_RSO_MINIMO = 0.3             # céu totalmente encoberto (cap. 4)
RS_RSO_MAXIMO = 1.0             # limite superior de Rs/Rso (eq. 39)


def pressao_atmosferica(z_m: float) -> float:
    """Eq. 7: P = 101,3·[(293 − 0,0065·z)/293]^5,26 (kPa)."""
    return 101.3 * ((293.0 - 0.0065 * z_m) / 293.0) ** 5.26


def constante_psicrometrica(p_kpa: float) -> float:
    """Eq. 8: γ = 0,665×10⁻³·P (kPa °C⁻¹)."""
    return 0.665e-3 * p_kpa


def pressao_saturacao(t_c: float) -> float:
    """Eq. 11: e°(T) = 0,6108·exp[17,27·T/(T + 237,3)] (kPa)."""
    return 0.6108 * math.exp(17.27 * t_c / (t_c + 237.3))


def declividade_pressao_saturacao(t_c: float) -> float:
    """Eq. 13: Δ = 4098·e°(T)/(T + 237,3)² (kPa °C⁻¹)."""
    return 4098.0 * pressao_saturacao(t_c) / (t_c + 237.3) ** 2


def fator_vento_2m(z_m: float) -> float:
    """Eq. 47: u₂ = u_z·4,87/ln(67,8·z − 5,42); devolve o fator u₂/u_z."""
    return 4.87 / math.log(67.8 * z_m - 5.42)


def distancia_relativa_terra_sol(j: int) -> float:
    """Eq. 23: dr = 1 + 0,033·cos(2πJ/365)."""
    return 1.0 + 0.033 * math.cos(2.0 * math.pi * j / 365.0)


def declinacao_solar(j: int) -> float:
    """Eq. 24: δ = 0,409·sen(2πJ/365 − 1,39) (rad)."""
    return 0.409 * math.sin(2.0 * math.pi * j / 365.0 - 1.39)


def angulo_por_do_sol(lat_rad: float, delta: float) -> float:
    """Eq. 25: ωs = arccos[−tan(φ)·tan(δ)] (rad)."""
    return math.acos(max(-1.0, min(1.0, -math.tan(lat_rad) * math.tan(delta))))


def correcao_sazonal(j: int) -> float:
    """Eqs. 32–33: Sc = 0,1645·sen(2b) − 0,1255·cos(b) − 0,025·sen(b), b = 2π(J − 81)/364 (h)."""
    b = 2.0 * math.pi * (j - 81) / 364.0
    return 0.1645 * math.sin(2.0 * b) - 0.1255 * math.cos(b) - 0.025 * math.sin(b)


def angulo_horario(t_h: float, lz_graus: float, lm_graus: float, sc_h: float) -> float:
    """Eq. 31: ω = π/12·[(t + 0,06667·(Lz − Lm) + Sc) − 12] (rad), t no meio do período."""
    return math.pi / 12.0 * ((t_h + 0.06667 * (lz_graus - lm_graus) + sc_h) - 12.0)


def ra_diaria(j: int, lat_rad: float) -> float:
    """Eq. 21: Ra diária (MJ m⁻² d⁻¹)."""
    dr = distancia_relativa_terra_sol(j)
    delta = declinacao_solar(j)
    ws = angulo_por_do_sol(lat_rad, delta)
    return (24.0 * 60.0 / math.pi) * GSC_MJ_M2_MIN * dr * (
        ws * math.sin(lat_rad) * math.sin(delta)
        + math.cos(lat_rad) * math.cos(delta) * math.sin(ws)
    )


@dataclass(frozen=True)
class GeometriaHoraria:
    dr: float
    delta: float
    omega_s: float
    sc_h: float
    omega: float
    omega1: float
    omega2: float
    ra_mj: float


def geometria_horaria(
    j: int,
    t_meio_h: float,
    lat_rad: float,
    lz_graus: float,
    lm_graus: float,
    duracao_h: float = 1.0,
    zerar_pelo_meio: bool = False,
) -> GeometriaHoraria:
    """
    Ra de um período curto (eq. 28), com ω₁ = ω − π·t₁/24 e ω₂ = ω + π·t₁/24 (eqs. 29–30)
    limitados a [−ωs, ωs] (docs/MODELO.md, seção 2.2). Assim Ra = 0 quando o período inteiro está
    com o Sol abaixo do horizonte, e a hora do nascer ou do pôr do sol recebe só a parte
    iluminada. O texto do FAO-56 zera Ra pelo meio do período (ω < −ωs ou ω > ωs); essa
    leitura (`zerar_pelo_meio=True`) só é usada como diagnóstico e difere da adotada apenas
    nas horas de transição (docs/MODELO.md).
    """
    dr = distancia_relativa_terra_sol(j)
    delta = declinacao_solar(j)
    ws = angulo_por_do_sol(lat_rad, delta)
    sc = correcao_sazonal(j)
    w = angulo_horario(t_meio_h, lz_graus, lm_graus, sc)
    w1 = max(-ws, min(ws, w - math.pi * duracao_h / 24.0))
    w2 = max(-ws, min(ws, w + math.pi * duracao_h / 24.0))
    ra = (12.0 * 60.0 / math.pi) * GSC_MJ_M2_MIN * dr * (
        (w2 - w1) * math.sin(lat_rad) * math.sin(delta)
        + math.cos(lat_rad) * math.cos(delta) * (math.sin(w2) - math.sin(w1))
    )
    if zerar_pelo_meio and (w < -ws or w > ws):
        ra = 0.0
    return GeometriaHoraria(dr=dr, delta=delta, omega_s=ws, sc_h=sc, omega=w, omega1=w1, omega2=w2, ra_mj=max(0.0, ra))


def radiacao_ceu_claro(ra_mj: float, z_m: float) -> float:
    """Eq. 37: Rso = (0,75 + 2×10⁻⁵·z)·Ra."""
    return (0.75 + 2e-5 * z_m) * ra_mj


@dataclass(frozen=True)
class TermosPenmanMonteith:
    p_kpa: float
    gamma: float
    delta_curva: float
    e0: float
    ea: float
    rso: float
    rs_rso_bruta: Optional[float]
    rs_rso: float
    rns: float
    rnl: float
    rn: float
    g: float
    et0_mm_h: float


def et0_penman_monteith_horaria(
    t_c: float,
    ur_pct: float,
    u2_ms: float,
    rs_mj: float,
    ra_mj: float,
    z_m: float,
    rs_rso_noite: Optional[float] = None,
) -> TermosPenmanMonteith:
    """
    ET0 horária pelo Penman-Monteith do FAO-56 (eq. 53), com ea = e°(T)·UR/100 (eq. 54),
    Rns = (1 − 0,23)·Rs (eq. 38), Rnl pela eq. 39 com σ horária e G = 0,1·Rn de dia e
    0,5·Rn à noite (eqs. 45–46).

    Rs/Rso: com Ra > 0, a razão medida, limitada a [0,3; 1,0]; com Ra = 0, `rs_rso_noite`
    (a razão do período 2–3 h antes do pôr do sol anterior), que é obrigatória.
    Devolve a ET0 sem truncar; valores negativos são tratados por quem chama.
    """
    p_kpa = pressao_atmosferica(z_m)
    gamma = constante_psicrometrica(p_kpa)
    e0 = pressao_saturacao(t_c)
    delta_curva = declividade_pressao_saturacao(t_c)
    ea = e0 * ur_pct / 100.0
    rso = radiacao_ceu_claro(ra_mj, z_m)

    dia = ra_mj > 0.0
    if dia:
        rs_rso_bruta = rs_mj / rso
        rs_rso = min(RS_RSO_MAXIMO, max(RS_RSO_MINIMO, rs_rso_bruta))
    else:
        if rs_rso_noite is None:
            raise ValueError("Hora noturna (Ra = 0) sem a razão Rs/Rso do fim da tarde anterior.")
        rs_rso_bruta = None
        rs_rso = rs_rso_noite

    rns = (1.0 - ALBEDO_REFERENCIA) * rs_mj
    rnl = (
        SIGMA_HORARIA
        * (t_c + 273.16) ** 4
        * (0.34 - 0.14 * math.sqrt(ea))
        * (1.35 * rs_rso - 0.35)
    )
    rn = rns - rnl
    g = (0.1 if dia else 0.5) * rn

    et0 = (
        FATOR_MJ_PARA_MM * delta_curva * (rn - g)
        + gamma * (37.0 / (t_c + 273.0)) * u2_ms * (e0 - ea)
    ) / (delta_curva + gamma * (1.0 + 0.34 * u2_ms))

    return TermosPenmanMonteith(
        p_kpa=p_kpa,
        gamma=gamma,
        delta_curva=delta_curva,
        e0=e0,
        ea=ea,
        rso=rso,
        rs_rso_bruta=rs_rso_bruta,
        rs_rso=rs_rso,
        rns=rns,
        rnl=rnl,
        rn=rn,
        g=g,
        et0_mm_h=et0,
    )


def et0_hargreaves_samani(tmed_c: float, tmax_c: float, tmin_c: float, ra_mj_dia: float) -> float:
    """
    Hargreaves e Samani (1985), na forma da eq. 52 do FAO-56:
    ET0 = 0,0023·(Tmed + 17,8)·(Tmax − Tmin)^0,5·0,408·Ra (mm d⁻¹).
    """
    return 0.0023 * (tmed_c + 17.8) * math.sqrt(max(0.0, tmax_c - tmin_c)) * FATOR_MJ_PARA_MM * ra_mj_dia
