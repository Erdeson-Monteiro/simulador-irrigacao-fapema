"""
Modelo de Balanço Hídrico de Duas Camadas, Evapotranspiração (Hargreaves-Samani),
Estratégias de Acionamento (E1, E2, E3 e Contrafactual SEQUEIRO) com Limite Físico
de Reservatório Universal e Validação Física Independente (Seções 3, 4, 5 e 6).

Nota: O modelo físico das equações de balanço nas duas camadas e de evapotranspiração
permanece inalterado. A latitude não possui valor fixo no código e deve ser fornecida
a partir do bloco de metadados do arquivo bruto do INMET.
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import List, Dict, Any, Optional


# Constante solar extraterrestre (MJ m^-2 min^-1)
GSC_MJ_M2_MIN = 0.0820
FATOR_CONVERSAO_MJ_PARA_MM = 0.408


@dataclass
class SoilParams:
    """Parâmetros hídricos do solo em duas camadas (Seção 3.2)."""
    theta_sat: float = 0.45   # Umidade na saturação (cm3/cm3)
    theta_cc: float = 0.28    # Umidade na capacidade de campo (cm3/cm3)
    theta_pmp: float = 0.14   # Umidade no ponto de murcha permanente (cm3/cm3)
    p: float = 0.35           # Fração de depleção tolerada antes do estresse
    z1: float = 200.0         # Espessura da camada 1 - zona radicular (mm)
    z2: float = 200.0         # Espessura da camada 2 - abaixo da raiz (mm)

    @property
    def agua_disponivel_mm(self) -> float:
        """AD = (θ_cc - θ_pmp) * z1 (28,0 mm para valores de partida)."""
        return (self.theta_cc - self.theta_pmp) * self.z1

    @property
    def theta_lim(self) -> float:
        """θ_lim = θ_cc - p * (θ_cc - θ_pmp) (0,231 cm3/cm3 para valores de partida)."""
        return self.theta_cc - self.p * (self.theta_cc - self.theta_pmp)


@dataclass
class ClimateDay:
    """Registro climático diário (Seções 3.4 e 3.5)."""
    data: str                 # YYYY-MM-DD
    dia_do_ano: int           # J (1 a 365/366)
    t_max: float              # °C
    t_min: float              # °C
    t_med: float              # °C
    precipitacao_mm: float    # P (mm)
    kc: float = 1.0           # Coeficiente de cultura
    interpolado: bool = False # Indica se houve interpolação de falha curta


@dataclass
class ScenarioConfig:
    """Configuração de cenário de escassez hídrica (Seção 4)."""
    nome: str                           # 'Abundante', 'Moderado', 'Restrito'
    capacidade_reservatorio_l: float    # 1000.0, 500.0, 500.0
    intervalo_reabastecimento_dias: int # 3, 7, 14
    area_canteiro_m2: float = 10.0      # Área padrão do canteiro (m²)


SCENARIOS_PADRAO: Dict[str, ScenarioConfig] = {
    "Abundante": ScenarioConfig("Abundante", 1000.0, 3, 10.0),
    "Moderado": ScenarioConfig("Moderado", 500.0, 7, 10.0),
    "Restrito": ScenarioConfig("Restrito", 500.0, 14, 10.0),
}


@dataclass
class DailyStepResult:
    """Estado diário completo após passo de simulação."""
    dia_idx: int
    data: str
    theta1_inicial: float
    theta2_inicial: float
    theta1_final: float
    theta2_final: float
    p_mm: float
    i_desejada_mm: float
    i_mm: float
    i_nao_atendida_mm: float
    volume_irrigado_l: float
    volume_nao_atendido_l: float
    et0_mm: float
    etc_potencial_mm: float
    etc_real_mm: float
    d1_mm: float
    d2_mm: float
    deficit_acumulado_mm: float
    deficit_solo_mm: float
    volume_reservatorio_inicial_l: float
    volume_reservatorio_final_l: float
    reabastecido: bool
    acionou_irrigacao: bool
    reservatorio_vazio: bool


@dataclass
class SimulationMetrics:
    """Métricas consolidadas de saída com limite físico de reservatório e percolação incremental."""
    estrategia: str
    cenario: str
    periodo: str
    dias_simulados: int
    lamina_desejada_mm: float
    lamina_total_mm: float
    volume_total_l: float
    lamina_nao_atendida_mm: float
    volume_nao_atendido_l: float
    percolacao_acumulada_mm: float             # D2_total (mm)
    percolacao_acumulada_l: float              # D2_total (L)
    d2_chuva_mm: float                         # Percolação no contrafactual I(t)=0 (mm)
    d2_chuva_l: float                          # Percolação no contrafactual I(t)=0 (L)
    d2_incremental_mm: float                   # D2_total - D2_chuva (mm)
    d2_incremental_l: float                    # D2_total - D2_chuva (L)
    interacao_nao_aditiva: bool                # True se D2_incremental < 0
    eficiencia_incremental_pct: float          # (lamina_aplicada - D2_incremental) / lamina_aplicada (%)
    eficiencia_bruta_sem_separacao_pct: float  # (lamina_aplicada - D2_total) / lamina_aplicada (%)
    conforto_hidrico_pct: float
    numero_acionamentos: int
    deficit_maximo_mm: float
    dias_reservatorio_vazio: int
    primeiro_dia_reservatorio_vazio: Optional[int]
    erro_conservacao_massa_pct: float


def calcular_ra_mm_dia(dia_do_ano: int, latitude_deg: float) -> float:
    """
    Calcula a radiação extraterrestre (Ra) em equivalente de evaporação (mm/dia)
    conforme Seção 3.4:
      Ra[MJ m^-2 dia^-1] = (24*60/pi) * Gsc * dr * (ws*sin(phi)*sin(delta) + cos(phi)*cos(delta)*sin(ws))
      Ra[mm/dia] = Ra[MJ m^-2 dia^-1] * 0.408
    `latitude_deg` deve ser extraída do bloco de metadados do arquivo INMET.
    """
    if latitude_deg is None:
        raise ValueError("A latitude (latitude_deg) é obrigatória e deve vir dos metadados do INMET.")
    phi = math.radians(latitude_deg)
    j = dia_do_ano
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * j / 365.0)
    delta = 0.409 * math.sin(2.0 * math.pi * j / 365.0 - 1.39)
    tan_prod = -math.tan(phi) * math.tan(delta)
    tan_prod = max(-1.0, min(1.0, tan_prod))
    ws = math.acos(tan_prod)

    ra_mj = (
        (24.0 * 60.0 / math.pi)
        * GSC_MJ_M2_MIN
        * dr
        * (ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws))
    )
    return ra_mj * FATOR_CONVERSAO_MJ_PARA_MM


def calcular_et0_hargreaves_samani(
    dia_do_ano: int,
    t_max: float,
    t_min: float,
    t_med: float,
    latitude_deg: float,
) -> float:
    """
    Calcula a evapotranspiração de referência (ET0, mm/dia) pelo método de Hargreaves-Samani:
      ET0 = 0.0023 * Ra * (T_max - T_min)^0.5 * (T_med + 17.8)
    """
    ra_mm = calcular_ra_mm_dia(dia_do_ano, latitude_deg)
    delta_t = max(0.0, t_max - t_min)
    et0 = 0.0023 * ra_mm * math.sqrt(delta_t) * (t_med + 17.8)
    return max(0.0, et0)


def passo_balanco_solo(
    theta1_t: float,
    theta2_t: float,
    p_t: float,
    i_t: float,
    etc_potencial_t: float,
    soil: SoilParams,
) -> Dict[str, float]:
    """
    Executa um passo diário das equações de balanço hídrico nas duas camadas (Seção 3.3),
    respeitando as restrições invariantes (theta_pmp <= theta <= theta_sat) e a conservação
    exata de massa. Modelo físico inalterado.
    """
    s1_t = theta1_t * soil.z1
    s2_t = theta2_t * soil.z2
    s1_min = soil.theta_pmp * soil.z1
    s1_cc = soil.theta_cc * soil.z1
    s2_cc = soil.theta_cc * soil.z2

    # Extração real limitada à água disponível acima do ponto de murcha permanente
    agua_extraivel_1 = max(0.0, s1_t + p_t + i_t - s1_min)
    etc_real_t = min(etc_potencial_t, agua_extraivel_1)

    # Camada 1 (zona radicular: 0 a 20 cm)
    armazenamento_prov_1 = s1_t + p_t + i_t - etc_real_t
    d1_t = max(0.0, armazenamento_prov_1 - s1_cc)
    theta1_next = (armazenamento_prov_1 - d1_t) / soil.z1

    # Camada 2 (abaixo da raiz: 20 a 40 cm)
    armazenamento_prov_2 = s2_t + d1_t
    d2_t = max(0.0, armazenamento_prov_2 - s2_cc)
    theta2_next = (armazenamento_prov_2 - d2_t) / soil.z2

    # Verificação estrita das restrições invariantes (Seção 3.3)
    eps = 1e-9
    if theta1_next < soil.theta_pmp - eps or theta1_next > soil.theta_sat + eps:
        raise ValueError(
            f"Violação de invariante na Camada 1: theta1={theta1_next:.6f} "
            f"fora de [{soil.theta_pmp}, {soil.theta_sat}]"
        )
    if theta2_next < soil.theta_pmp - eps or theta2_next > soil.theta_sat + eps:
        raise ValueError(
            f"Violação de invariante na Camada 2: theta2={theta2_next:.6f} "
            f"fora de [{soil.theta_pmp}, {soil.theta_sat}]"
        )

    return {
        "theta1_next": theta1_next,
        "theta2_next": theta2_next,
        "etc_real_mm": etc_real_t,
        "d1_mm": d1_t,
        "d2_mm": d2_t,
    }


def simular_estrategia(
    estrategia_codigo: str,
    serie_climatica: List[ClimateDay],
    latitude_deg: float,
    soil: Optional[SoilParams] = None,
    cenario: Optional[ScenarioConfig] = None,
    periodo_nome: str = "Ciclo Completo",
    theta1_inicial: Optional[float] = None,
    theta2_inicial: Optional[float] = None,
    lamina_fixa_mm: float = 10.0,
    limiar_deficit_mm: float = 10.0,
    d2_chuva_referencia_mm: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Executa a simulação diária para uma estratégia ('E1', 'E2', 'E3' ou 'SEQUEIRO' com I(t)=0)
    sobre uma série climática e um cenário de reservatório.

    Separa dois conceitos (Parte 2):
      1. LIMITE FÍSICO — vale para E1, E2 e E3, sem exceção:
           I_efetiva(t) = min(I_desejada(t), V(t) / area_canteiro)
           V(t+1) = V(t) - I_efetiva(t) * area_canteiro
         V é reposto à capacidade a cada intervalo de reabastecimento.
         Se V(t) = 0, nenhuma irrigação ocorre.
      2. RACIONAMENTO ESTRATÉGICO — exclusivo da E3:
           lamina_maxima(t) = V(t) / (dias_restantes * area_canteiro)
           I_desejada(t) = min(Deficit(t), lamina_maxima(t))
    """
    if latitude_deg is None:
        raise ValueError("latitude_deg é obrigatória para simular_estrategia.")
    soil = soil or SoilParams()
    cenario = cenario or SCENARIOS_PADRAO["Abundante"]

    contrafactual_historico: Optional[List[DailyStepResult]] = None
    if estrategia_codigo != "SEQUEIRO" and d2_chuva_referencia_mm is None:
        res_cf = simular_estrategia(
            estrategia_codigo="SEQUEIRO",
            serie_climatica=serie_climatica,
            latitude_deg=latitude_deg,
            soil=soil,
            cenario=cenario,
            periodo_nome=periodo_nome,
            theta1_inicial=theta1_inicial,
            theta2_inicial=theta2_inicial,
            lamina_fixa_mm=lamina_fixa_mm,
            limiar_deficit_mm=limiar_deficit_mm,
            d2_chuva_referencia_mm=0.0,
        )
        d2_chuva_referencia_mm = res_cf["metricas"].percolacao_acumulada_mm
        contrafactual_historico = res_cf["historico"]

    theta1 = theta1_inicial if theta1_inicial is not None else soil.theta_cc
    theta2 = theta2_inicial if theta2_inicial is not None else soil.theta_cc

    s_inicial_total = theta1 * soil.z1 + theta2 * soil.z2

    deficit_acumulado = 0.0
    volume_reservatorio = cenario.capacidade_reservatorio_l
    historico: List[DailyStepResult] = []

    for idx, dia in enumerate(serie_climatica):
        reabastecido = False
        if idx % cenario.intervalo_reabastecimento_dias == 0:
            volume_reservatorio = cenario.capacidade_reservatorio_l
            reabastecido = True

        vol_ini = volume_reservatorio
        dias_restantes = cenario.intervalo_reabastecimento_dias - (
            idx % cenario.intervalo_reabastecimento_dias
        )

        et0 = calcular_et0_hargreaves_samani(
            dia.dia_do_ano, dia.t_max, dia.t_min, dia.t_med, latitude_deg
        )
        etc_pot = dia.kc * et0
        p_t = dia.precipitacao_mm

        i_desejada_t = 0.0
        if estrategia_codigo == "SEQUEIRO":
            deficit_acumulado = max(0.0, deficit_acumulado + etc_pot - p_t)
            i_desejada_t = 0.0
        elif estrategia_codigo == "E1":
            # E1 — Limiar fixo: se θ1(t) < θ_lim -> I_desejada(t) = lamina_fixa
            deficit_acumulado = max(0.0, deficit_acumulado + etc_pot - p_t)
            if theta1 < soil.theta_lim:
                i_desejada_t = lamina_fixa_mm
        elif estrategia_codigo == "E2":
            # E2 — Balanço hídrico: se Deficit(t) >= limiar_deficit -> I_desejada(t) = Deficit(t), Deficit(t) = 0
            deficit_acumulado = max(0.0, deficit_acumulado + etc_pot - p_t)
            if deficit_acumulado >= limiar_deficit_mm:
                i_desejada_t = deficit_acumulado
                deficit_acumulado = 0.0
        elif estrategia_codigo == "E3":
            # E3 — Balanço com racionamento estratégico de reservatório
            deficit_acumulado = max(0.0, deficit_acumulado + etc_pot - p_t)
            if deficit_acumulado >= limiar_deficit_mm:
                lamina_maxima_t = volume_reservatorio / (
                    dias_restantes * cenario.area_canteiro_m2
                )
                i_desejada_t = min(deficit_acumulado, max(0.0, lamina_maxima_t))
        else:
            raise ValueError(f"Estratégia desconhecida: {estrategia_codigo}")

        # LIMITE FÍSICO DO RESERVATÓRIO — aplica-se a E1, E2 e E3 sem exceção
        if volume_reservatorio > 0.0:
            lamina_fisica_disp = volume_reservatorio / cenario.area_canteiro_m2
            i_efetiva_t = min(i_desejada_t, max(0.0, lamina_fisica_disp))
        else:
            i_efetiva_t = 0.0

        i_nao_atendida_t = max(0.0, i_desejada_t - i_efetiva_t)
        vol_nao_atendido_l = i_nao_atendida_t * cenario.area_canteiro_m2

        if estrategia_codigo in ("E1", "E3") and i_efetiva_t > 0.0:
            deficit_acumulado = max(0.0, deficit_acumulado - i_efetiva_t)

        vol_irrigado_l = i_efetiva_t * cenario.area_canteiro_m2
        volume_reservatorio = max(0.0, volume_reservatorio - vol_irrigado_l)
        reservatorio_vazio_dia = (
            estrategia_codigo != "SEQUEIRO"
            and cenario.capacidade_reservatorio_l > 0.0
            and volume_reservatorio <= 1e-6
        )

        res_solo = passo_balanco_solo(theta1, theta2, p_t, i_efetiva_t, etc_pot, soil)
        theta1_next = res_solo["theta1_next"]
        theta2_next = res_solo["theta2_next"]

        deficit_solo_mm = max(0.0, (soil.theta_cc - theta1_next) * soil.z1)

        historico.append(
            DailyStepResult(
                dia_idx=idx + 1,
                data=dia.data,
                theta1_inicial=theta1,
                theta2_inicial=theta2,
                theta1_final=theta1_next,
                theta2_final=theta2_next,
                p_mm=p_t,
                i_desejada_mm=i_desejada_t,
                i_mm=i_efetiva_t,
                i_nao_atendida_mm=i_nao_atendida_t,
                volume_irrigado_l=vol_irrigado_l,
                volume_nao_atendido_l=vol_nao_atendido_l,
                et0_mm=et0,
                etc_potencial_mm=etc_pot,
                etc_real_mm=res_solo["etc_real_mm"],
                d1_mm=res_solo["d1_mm"],
                d2_mm=res_solo["d2_mm"],
                deficit_acumulado_mm=deficit_acumulado,
                deficit_solo_mm=deficit_solo_mm,
                volume_reservatorio_inicial_l=vol_ini,
                volume_reservatorio_final_l=volume_reservatorio,
                reabastecido=reabastecido,
                acionou_irrigacao=(i_efetiva_t > 1e-9),
                reservatorio_vazio=reservatorio_vazio_dia,
            )
        )

        theta1 = theta1_next
        theta2 = theta2_next

    n_dias = len(historico)
    lamina_desejada_mm = sum(d.i_desejada_mm for d in historico)
    lamina_total_mm = sum(d.i_mm for d in historico)
    volume_total_l = sum(d.volume_irrigado_l for d in historico)
    lamina_nao_atendida_mm = sum(d.i_nao_atendida_mm for d in historico)
    volume_nao_atendido_l = sum(d.volume_nao_atendido_l for d in historico)
    d2_total_mm = sum(d.d2_mm for d in historico)
    d2_total_l = d2_total_mm * cenario.area_canteiro_m2

    if estrategia_codigo == "SEQUEIRO":
        d2_chuva_mm = d2_total_mm
    else:
        d2_chuva_mm = float(d2_chuva_referencia_mm or 0.0)

    d2_chuva_l = d2_chuva_mm * cenario.area_canteiro_m2
    d2_incremental_mm = d2_total_mm - d2_chuva_mm
    d2_incremental_l = d2_incremental_mm * cenario.area_canteiro_m2
    interacao_nao_aditiva = d2_incremental_mm < -1e-6

    if lamina_total_mm > 0:
        eficiencia_incremental_pct = ((lamina_total_mm - d2_incremental_mm) / lamina_total_mm) * 100.0
        eficiencia_bruta_pct = ((lamina_total_mm - d2_total_mm) / lamina_total_mm) * 100.0
    else:
        eficiencia_incremental_pct = 100.0
        eficiencia_bruta_pct = 100.0

    dias_conforto = sum(1 for d in historico if d.theta1_final >= soil.theta_lim - 1e-9)
    conforto_pct = (dias_conforto / n_dias * 100.0) if n_dias > 0 else 0.0
    acionamentos = sum(1 for d in historico if d.acionou_irrigacao)
    deficit_maximo_mm = max((d.deficit_solo_mm for d in historico), default=0.0)

    dias_vazio_indices = [d.dia_idx for d in historico if d.reservatorio_vazio]
    dias_reservatorio_vazio = len(dias_vazio_indices)
    primeiro_dia_vazio = dias_vazio_indices[0] if dias_vazio_indices else None

    # Conservação de massa computando os dois lados de forma independente:
    s_final_total = (
        historico[-1].theta1_final * soil.z1 + historico[-1].theta2_final * soil.z2
        if n_dias > 0
        else s_inicial_total
    )
    delta_s = s_final_total - s_inicial_total
    entradas = sum(d.p_mm + d.i_mm for d in historico)
    saidas = sum(d.etc_real_mm + d.d2_mm for d in historico)
    residuo = abs((entradas - saidas) - delta_s)
    escala_ref = max(1.0, entradas, s_inicial_total)
    erro_massa_pct = (residuo / escala_ref) * 100.0

    metricas = SimulationMetrics(
        estrategia=estrategia_codigo,
        cenario=cenario.nome,
        periodo=periodo_nome,
        dias_simulados=n_dias,
        lamina_desejada_mm=round(lamina_desejada_mm, 2),
        lamina_total_mm=round(lamina_total_mm, 2),
        volume_total_l=round(volume_total_l, 2),
        lamina_nao_atendida_mm=round(lamina_nao_atendida_mm, 2),
        volume_nao_atendido_l=round(volume_nao_atendido_l, 2),
        percolacao_acumulada_mm=round(d2_total_mm, 2),
        percolacao_acumulada_l=round(d2_total_l, 2),
        d2_chuva_mm=round(d2_chuva_mm, 2),
        d2_chuva_l=round(d2_chuva_l, 2),
        d2_incremental_mm=round(d2_incremental_mm, 2),
        d2_incremental_l=round(d2_incremental_l, 2),
        interacao_nao_aditiva=interacao_nao_aditiva,
        eficiencia_incremental_pct=round(eficiencia_incremental_pct, 2),
        eficiencia_bruta_sem_separacao_pct=round(eficiencia_bruta_pct, 2),
        conforto_hidrico_pct=round(conforto_pct, 2),
        numero_acionamentos=acionamentos,
        deficit_maximo_mm=round(deficit_maximo_mm, 2),
        dias_reservatorio_vazio=dias_reservatorio_vazio,
        primeiro_dia_reservatorio_vazio=primeiro_dia_vazio,
        erro_conservacao_massa_pct=round(erro_massa_pct, 6),
    )

    return {
        "metricas": metricas,
        "historico": historico,
        "contrafactual_historico": contrafactual_historico,
        "soil": soil,
        "cenario": cenario,
    }


def executar_testes_validacao_secao6(soil: Optional[SoilParams] = None) -> Dict[str, Any]:
    """
    Executa os três testes obrigatórios de validação do modelo físico (Seção 6)
    contra CONSTANTES LITERAIS CALCULADAS À MÃO (sem derivar valores esperados do próprio código).
    """
    soil = soil or SoilParams()
    registros_diarios_validacao: List[Dict[str, Any]] = []

    # =========================================================================
    # TESTE 1: CONSERVAÇÃO DE MASSA INDEPENDENTE (10 DIAS DETERMINÍSTICOS)
    # =========================================================================
    T1_DIAS = 10
    T1_THETA1_INI = 0.25
    T1_THETA2_INI = 0.26
    T1_ETC_DIARIA_MM = 4.0
    T1_VETOR_P_MM = [0.0, 15.0, 0.0, 0.0, 0.0, 0.0, 15.0, 0.0, 0.0, 0.0]
    T1_VETOR_I_MM = [12.0, 0.0, 0.0, 0.0, 0.0, 12.0, 0.0, 0.0, 0.0, 0.0]

    # Constantes literais fixas (calculadas à mão):
    T1_ESPERADO_S_INICIAL_MM = 102.0
    T1_ESPERADO_S_FINAL_MM = 100.0
    T1_ESPERADO_THETA1_FINAL = 0.22
    T1_ESPERADO_THETA2_FINAL = 0.28
    T1_ESPERADO_ENTRADAS_MM = 54.0
    T1_ESPERADO_D2_TOTAL_MM = 16.0
    T1_ESPERADO_SAIDAS_MM = 56.0
    T1_ESPERADO_BALANCO_MM = -2.0  # Lado A (Entradas - Saídas) == Lado B (ΔS) == -2,0 mm

    th1_t1 = T1_THETA1_INI
    th2_t1 = T1_THETA2_INI
    acum_etc_t1 = 0.0
    acum_d2_t1 = 0.0

    for d_idx in range(T1_DIAS):
        p_val = T1_VETOR_P_MM[d_idx]
        i_val = T1_VETOR_I_MM[d_idx]
        passo = passo_balanco_solo(
            theta1_t=th1_t1,
            theta2_t=th2_t1,
            p_t=p_val,
            i_t=i_val,
            etc_potencial_t=T1_ETC_DIARIA_MM,
            soil=soil,
        )
        registros_diarios_validacao.append({
            "teste": "Teste_1_Conservacao_Massa",
            "dia": d_idx + 1,
            "theta1_inicial": round(th1_t1, 6),
            "theta2_inicial": round(th2_t1, 6),
            "p_mm": p_val,
            "i_mm": i_val,
            "etc_potencial_mm": T1_ETC_DIARIA_MM,
            "etc_real_mm": round(passo["etc_real_mm"], 6),
            "d1_mm": round(passo["d1_mm"], 6),
            "d2_mm": round(passo["d2_mm"], 6),
            "theta1_final": round(passo["theta1_next"], 6),
            "theta2_final": round(passo["theta2_next"], 6),
        })
        th1_t1 = passo["theta1_next"]
        th2_t1 = passo["theta2_next"]
        acum_etc_t1 += passo["etc_real_mm"]
        acum_d2_t1 += passo["d2_mm"]

    lado_a_entradas_mm = sum(T1_VETOR_P_MM) + sum(T1_VETOR_I_MM)
    lado_a_saidas_mm = acum_etc_t1 + acum_d2_t1
    lado_a_saldo_fluxos_mm = lado_a_entradas_mm - lado_a_saidas_mm

    lado_b_s_inicial_mm = (T1_THETA1_INI * soil.z1) + (T1_THETA2_INI * soil.z2)
    lado_b_s_final_mm = (th1_t1 * soil.z1) + (th2_t1 * soil.z2)
    lado_b_delta_armazenamento_mm = lado_b_s_final_mm - lado_b_s_inicial_mm

    diferenca_lados_mm = abs(lado_a_saldo_fluxos_mm - lado_b_delta_armazenamento_mm)
    erro_relativo_pct = (diferenca_lados_mm / T1_ESPERADO_ENTRADAS_MM) * 100.0

    passou_teste1 = (
        erro_relativo_pct < 0.1
        and abs(lado_a_entradas_mm - T1_ESPERADO_ENTRADAS_MM) < 1e-6
        and abs(acum_d2_t1 - T1_ESPERADO_D2_TOTAL_MM) < 1e-6
        and abs(lado_a_saidas_mm - T1_ESPERADO_SAIDAS_MM) < 1e-6
        and abs(lado_a_saldo_fluxos_mm - T1_ESPERADO_BALANCO_MM) < 1e-6
        and abs(lado_b_s_inicial_mm - T1_ESPERADO_S_INICIAL_MM) < 1e-6
        and abs(lado_b_s_final_mm - T1_ESPERADO_S_FINAL_MM) < 1e-6
        and abs(lado_b_delta_armazenamento_mm - T1_ESPERADO_BALANCO_MM) < 1e-6
        and abs(th1_t1 - T1_ESPERADO_THETA1_FINAL) < 1e-6
        and abs(th2_t1 - T1_ESPERADO_THETA2_FINAL) < 1e-6
    )

    # =========================================================================
    # TESTE 2: SECAGEM MONOTÔNICA (60 DIAS SEM CHUVA E SEM IRRIGAÇÃO)
    # =========================================================================
    T2_DIAS = 60
    T2_THETA1_INI = 0.28
    T2_THETA2_INI = 0.28
    T2_ETC_DIARIA_MM = 4.0
    T2_ESPERADO_THETA1_DIA_7 = 0.14
    T2_ESPERADO_THETA1_FINAL = 0.14
    T2_ESPERADO_THETA2_FINAL = 0.28
    T2_ESPERADO_ETC_REAL_ACUMULADA_MM = 28.0

    th1_t2 = T2_THETA1_INI
    th2_t2 = T2_THETA2_INI
    curva_theta1 = [th1_t2]
    etc_real_acum_t2 = 0.0
    monotonica = True
    acima_ou_igual_pmp = True

    for d_idx in range(T2_DIAS):
        res = passo_balanco_solo(
            theta1_t=th1_t2,
            theta2_t=th2_t2,
            p_t=0.0,
            i_t=0.0,
            etc_potencial_t=T2_ETC_DIARIA_MM,
            soil=soil,
        )
        t1_novo = res["theta1_next"]
        if t1_novo > th1_t2 + 1e-12:
            monotonica = False
        if t1_novo < 0.14 - 1e-12:
            acima_ou_igual_pmp = False

        registros_diarios_validacao.append({
            "teste": "Teste_2_Secagem_Monotonica",
            "dia": d_idx + 1,
            "theta1_inicial": round(th1_t2, 6),
            "theta2_inicial": round(th2_t2, 6),
            "p_mm": 0.0,
            "i_mm": 0.0,
            "etc_potencial_mm": T2_ETC_DIARIA_MM,
            "etc_real_mm": round(res["etc_real_mm"], 6),
            "d1_mm": round(res["d1_mm"], 6),
            "d2_mm": round(res["d2_mm"], 6),
            "theta1_final": round(t1_novo, 6),
            "theta2_final": round(res["theta2_next"], 6),
        })
        th1_t2 = t1_novo
        th2_t2 = res["theta2_next"]
        etc_real_acum_t2 += res["etc_real_mm"]
        curva_theta1.append(th1_t2)

    estabilizou_no_pmp = (
        abs(curva_theta1[7] - T2_ESPERADO_THETA1_DIA_7) < 1e-9
        and abs(curva_theta1[-1] - T2_ESPERADO_THETA1_FINAL) < 1e-9
        and abs(etc_real_acum_t2 - T2_ESPERADO_ETC_REAL_ACUMULADA_MM) < 1e-9
    )
    passou_teste2 = monotonica and acima_ou_igual_pmp and estabilizou_no_pmp

    # =========================================================================
    # TESTE 3: SATURAÇÃO EXTREMA (1 DIA PARTINDO DA CAPACIDADE DE CAMPO)
    # =========================================================================
    T3_DIAS = 1
    T3_THETA1_INI = 0.28
    T3_THETA2_INI = 0.28
    T3_P_EXTREMA_MM = 250.0
    T3_ETC_MM = 0.0
    T3_ESPERADO_D1_MM = 250.0
    T3_ESPERADO_D2_MM = 250.0
    T3_ESPERADO_THETA1_FINAL = 0.28
    T3_ESPERADO_THETA2_FINAL = 0.28
    T3_LIMITE_THETA_SAT = 0.45

    res_sat = passo_balanco_solo(
        theta1_t=T3_THETA1_INI,
        theta2_t=T3_THETA2_INI,
        p_t=T3_P_EXTREMA_MM,
        i_t=0.0,
        etc_potencial_t=T3_ETC_MM,
        soil=soil,
    )
    registros_diarios_validacao.append({
        "teste": "Teste_3_Saturacao",
        "dia": 1,
        "theta1_inicial": T3_THETA1_INI,
        "theta2_inicial": T3_THETA2_INI,
        "p_mm": T3_P_EXTREMA_MM,
        "i_mm": 0.0,
        "etc_potencial_mm": T3_ETC_MM,
        "etc_real_mm": round(res_sat["etc_real_mm"], 6),
        "d1_mm": round(res_sat["d1_mm"], 6),
        "d2_mm": round(res_sat["d2_mm"], 6),
        "theta1_final": round(res_sat["theta1_next"], 6),
        "theta2_final": round(res_sat["theta2_next"], 6),
    })

    erro_d1_mm = abs(res_sat["d1_mm"] - T3_ESPERADO_D1_MM)
    erro_d2_mm = abs(res_sat["d2_mm"] - T3_ESPERADO_D2_MM)
    respeitou_theta_sat = (
        res_sat["theta1_next"] <= T3_LIMITE_THETA_SAT + 1e-12
        and res_sat["theta2_next"] <= T3_LIMITE_THETA_SAT + 1e-12
    )
    passou_teste3 = (
        erro_d1_mm < 1e-6
        and erro_d2_mm < 1e-6
        and abs(res_sat["theta1_next"] - T3_ESPERADO_THETA1_FINAL) < 1e-6
        and abs(res_sat["theta2_next"] - T3_ESPERADO_THETA2_FINAL) < 1e-6
        and respeitou_theta_sat
    )

    todos_aprovados = passou_teste1 and passou_teste2 and passou_teste3

    return {
        "aprovado": todos_aprovados,
        "registros_diarios": registros_diarios_validacao,
        "teste_1_conservacao_massa": {
            "aprovado": passou_teste1,
            "dias_simulados": T1_DIAS,
            "theta1_inicial": T1_THETA1_INI,
            "theta2_inicial": T1_THETA2_INI,
            "etc_diaria_mm": T1_ETC_DIARIA_MM,
            "s_inicial_mm_observado": round(lado_b_s_inicial_mm, 4),
            "s_inicial_mm_esperado_literal": T1_ESPERADO_S_INICIAL_MM,
            "s_final_mm_observado": round(lado_b_s_final_mm, 4),
            "s_final_mm_esperado_literal": T1_ESPERADO_S_FINAL_MM,
            "theta1_final_observado": round(th1_t1, 4),
            "theta1_final_esperado_literal": T1_ESPERADO_THETA1_FINAL,
            "theta2_final_observado": round(th2_t1, 4),
            "theta2_final_esperado_literal": T1_ESPERADO_THETA2_FINAL,
            "entradas_mm": round(lado_a_entradas_mm, 4),
            "entradas_mm_esperado_literal": T1_ESPERADO_ENTRADAS_MM,
            "saidas_mm": round(lado_a_saidas_mm, 4),
            "saidas_mm_esperado_literal": T1_ESPERADO_SAIDAS_MM,
            "d2_acumulado_mm_observado": round(acum_d2_t1, 4),
            "d2_acumulado_mm_esperado_literal": T1_ESPERADO_D2_TOTAL_MM,
            "lado_a_saldo_fluxos_mm": round(lado_a_saldo_fluxos_mm, 4),
            "delta_armazenamento_mm": round(lado_b_delta_armazenamento_mm, 4),
            "balanco_esperado_literal_mm": T1_ESPERADO_BALANCO_MM,
            "erro_absoluto_mm": round(diferenca_lados_mm, 8),
            "erro_relativo_pct": round(erro_relativo_pct, 8),
            "limite_maximo_pct": 0.1,
        },
        "teste_2_secagem_monotonica": {
            "aprovado": passou_teste2,
            "dias_simulados": T2_DIAS,
            "theta1_inicial": T2_THETA1_INI,
            "theta2_inicial": T2_THETA2_INI,
            "etc_diaria_mm": T2_ETC_DIARIA_MM,
            "monotonica": monotonica,
            "respeitou_limite_inferior_pmp": acima_ou_igual_pmp,
            "estabilizou_em_theta_pmp": estabilizou_no_pmp,
            "theta1_dia_7_observado": round(curva_theta1[7], 4),
            "theta1_dia_7_esperado_literal": T2_ESPERADO_THETA1_DIA_7,
            "theta1_final": round(curva_theta1[-1], 4),
            "theta1_final_esperado_literal": T2_ESPERADO_THETA1_FINAL,
            "theta2_final_observado": round(th2_t2, 4),
            "theta2_final_esperado_literal": T2_ESPERADO_THETA2_FINAL,
            "etc_real_acumulada_mm_observada": round(etc_real_acum_t2, 4),
            "etc_real_acumulada_mm_esperada_literal": T2_ESPERADO_ETC_REAL_ACUMULADA_MM,
            "theta_pmp": T2_ESPERADO_THETA1_FINAL,
        },
        "teste_3_saturacao": {
            "aprovado": passou_teste3,
            "dias_simulados": T3_DIAS,
            "theta1_inicial": T3_THETA1_INI,
            "theta2_inicial": T3_THETA2_INI,
            "etc_diaria_mm": T3_ETC_MM,
            "precipitacao_aplicada_mm": T3_P_EXTREMA_MM,
            "drenagem_d1_mm_observada": round(res_sat["d1_mm"], 4),
            "drenagem_d1_mm_esperada_literal": T3_ESPERADO_D1_MM,
            "drenagem_profunda_d2_mm": round(res_sat["d2_mm"], 4),
            "drenagem_esperada_mm": T3_ESPERADO_D2_MM,
            "theta1_final": round(res_sat["theta1_next"], 4),
            "theta1_final_esperado_literal": T3_ESPERADO_THETA1_FINAL,
            "theta2_final": round(res_sat["theta2_next"], 4),
            "theta2_final_esperado_literal": T3_ESPERADO_THETA2_FINAL,
            "theta_sat": T3_LIMITE_THETA_SAT,
            "respeitou_theta_sat": respeitou_theta_sat,
        },
    }
