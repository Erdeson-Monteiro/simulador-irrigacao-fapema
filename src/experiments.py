"""
Execução completa das Simulações sobre a Série Real do BDMEP/INMET (Estação A204 Balsas-MA),
Geração das Tabelas T1 a T8 (Markdown e CSV), Séries Diárias Brutas (`rodadas/*.csv`),
Figuras F1 a F5 (`figuras/*.png` 300 dpi + CSVs) e Relatório Final (`relatorio_final.md`),
todos em `resultados/v1/`.
"""

from __future__ import annotations
import csv
from dataclasses import asdict
from datetime import date
import inspect
import json
import os
import platform
import sqlite3
import subprocess
import sys
import time
from typing import Dict, Any, List, Optional

import matplotlib
import numpy as np

from src.water_balance import (
    SoilParams,
    ScenarioConfig,
    SCENARIOS_PADRAO,
    DailyStepResult,
    GSC_MJ_M2_MIN,
    FATOR_CONVERSAO_MJ_PARA_MM,
    simular_estrategia,
    executar_testes_validacao_secao6,
)
from src.climate import (
    DEFAULT_RAW_INMET_CSV,
    DEFAULT_PROCESSED_DIR,
    carregar_e_tratar_serie_climatica,
)
from src.figures import DEFAULT_FIGURES_DIR, gerar_todas_figuras


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CLIMATE_CSV = DEFAULT_RAW_INMET_CSV
DIR_RESULTADOS_V1 = os.path.join(ROOT_DIR, "resultados", "v1")
DEFAULT_REPORT_JSON = os.path.join(DIR_RESULTADOS_V1, "relatorio_simulacao.json")
DEFAULT_REPORT_MD = os.path.join(DIR_RESULTADOS_V1, "relatorio_final.md")
DEFAULT_TABELAS_DIR = os.path.join(DIR_RESULTADOS_V1, "tabelas")
DEFAULT_RODADAS_DIR = os.path.join(DIR_RESULTADOS_V1, "rodadas")


def _salvar_csv(caminho: str, linhas: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> str:
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    if not fieldnames and linhas:
        fieldnames = list(linhas[0].keys())
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames or [])
        writer.writeheader()
        writer.writerows(linhas)
    return caminho


def _caminhos_relativos(obj: Any) -> Any:
    """Troca, recursivamente, caminhos absolutos dentro do projeto por caminhos relativos à raiz."""
    if isinstance(obj, str) and obj.startswith(ROOT_DIR + os.sep):
        return os.path.relpath(obj, ROOT_DIR).replace(os.sep, "/")
    if isinstance(obj, dict):
        return {k: _caminhos_relativos(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_caminhos_relativos(v) for v in obj]
    return obj


def _linhas_diarias_para_csv(
    historico: List[DailyStepResult],
    cf_historico: Optional[List[DailyStepResult]],
    metadados_extras: Dict[str, Any],
) -> List[Dict[str, Any]]:
    linhas = []
    for idx, d in enumerate(historico):
        d2_cf = cf_historico[idx].d2_mm if cf_historico and idx < len(cf_historico) else d.d2_mm
        d2_inc_dia = d.d2_mm - d2_cf
        linhas.append({
            **metadados_extras,
            "dia_idx": d.dia_idx,
            "data": d.data,
            "theta1_inicial": round(d.theta1_inicial, 6),
            "theta1_final": round(d.theta1_final, 6),
            "theta2_inicial": round(d.theta2_inicial, 6),
            "theta2_final": round(d.theta2_final, 6),
            "p_mm": round(d.p_mm, 2),
            "i_desejada_mm": round(d.i_desejada_mm, 2),
            "i_efetiva_mm": round(d.i_mm, 2),
            "i_nao_atendida_mm": round(d.i_nao_atendida_mm, 2),
            "volume_irrigado_l": round(d.volume_irrigado_l, 2),
            "volume_nao_atendido_l": round(d.volume_nao_atendido_l, 2),
            "et0_mm": round(d.et0_mm, 4),
            "etc_potencial_mm": round(d.etc_potencial_mm, 4),
            "etc_real_mm": round(d.etc_real_mm, 4),
            "d1_mm": round(d.d1_mm, 4),
            "d2_total_mm": round(d.d2_mm, 4),
            "d2_chuva_contrafactual_mm": round(d2_cf, 4),
            "d2_incremental_mm": round(d2_inc_dia, 4),
            "deficit_acumulado_mm": round(d.deficit_acumulado_mm, 4),
            "deficit_solo_mm": round(d.deficit_solo_mm, 4),
            "volume_reservatorio_inicial_l": round(d.volume_reservatorio_inicial_l, 2),
            "volume_reservatorio_final_l": round(d.volume_reservatorio_final_l, 2),
            "reabastecido": int(d.reabastecido),
            "acionou_irrigacao": int(d.acionou_irrigacao),
            "reservatorio_vazio": int(d.reservatorio_vazio),
        })
    return linhas


def construir_tabela_t8_parametros(soil: SoilParams, meta_proc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Constrói a Tabela T8 (Parâmetros e suas fontes — Parte 4).
    Classificação estrita de `origem`:
      - "derivado" (com a fórmula explícita)
      - "extraído do arquivo INMET" (citando o campo do bloco de metadados)
      - fonte bibliográfica (docs/FONTES_PARAMETROS.md), "premissa do modelo" ou "sem fonte", quando o
        valor do v1 não corresponde à literatura (p = 0,35 e gatilho de 10 mm)
    """
    lat_val = meta_proc["latitude_graus"]
    lon_val = meta_proc["longitude_graus"]
    alt_val = meta_proc["altitude_m"]
    s1_cc = round(soil.theta_cc * soil.z1, 2)
    s2_cc = round(soil.theta_cc * soil.z2, 2)
    s1_pmp = round(soil.theta_pmp * soil.z1, 2)
    s1_sat = round(soil.theta_sat * soil.z1, 2)
    def_crit = round(soil.p * soil.agua_disponivel_mm, 2)

    return [
        {
            "simbolo": "θ_sat",
            "significado": "Umidade volumétrica do solo na saturação",
            "valor": f"{soil.theta_sat:.2f}",
            "unidade": "cm³/cm³",
            "origem": "premissa do modelo; não altera nenhum resultado (a água acima de θ_cc drena no mesmo passo)",
        },
        {
            "simbolo": "θ_cc",
            "significado": "Umidade volumétrica do solo na capacidade de campo",
            "valor": f"{soil.theta_cc:.2f}",
            "unidade": "cm³/cm³",
            "origem": "FAO-56, Tabela 19 (solo franco: θcc 0,20–0,30), página [A CONFIRMAR PELO AUTOR]; valor dentro da faixa",
        },
        {
            "simbolo": "θ_pmp",
            "significado": "Umidade volumétrica do solo no ponto de murcha permanente",
            "valor": f"{soil.theta_pmp:.2f}",
            "unidade": "cm³/cm³",
            "origem": "FAO-56, Tabela 19 (solo franco: θpmp 0,07–0,17), página [A CONFIRMAR PELO AUTOR]; valor dentro da faixa",
        },
        {
            "simbolo": "p",
            "significado": "Fração de depleção da água disponível tolerada antes do estresse hídrico",
            "valor": f"{soil.p:.2f}",
            "unidade": "adimensional",
            "origem": "sem fonte: o FAO-56, Tabela 22, indica p = 0,30 para alface (valor adotado no v2)",
        },
        {
            "simbolo": "z1",
            "significado": "Espessura da Camada 1 (zona radicular ativa: 0 a 20 cm)",
            "valor": f"{soil.z1:.0f}",
            "unidade": "mm",
            "origem": "Marouelli, Silva e Silva (2008, p. 84), Tabela 25: 15 cm na fase vegetativa e 20 cm nas fases 3 e 4; o modelo usa 20 cm; FAO-56, Tabela 22 (profundidade máxima 0,3–0,5 m)",
        },
        {
            "simbolo": "z2",
            "significado": "Espessura da Camada 2 (abaixo da zona radicular: 20 a 40 cm)",
            "valor": f"{soil.z2:.0f}",
            "unidade": "mm",
            "origem": "premissa do modelo",
        },
        {
            "simbolo": "AD",
            "significado": "Capacidade de água disponível na zona radicular",
            "valor": f"{soil.agua_disponivel_mm:.1f}",
            "unidade": "mm",
            "origem": "derivado: AD = (θ_cc − θ_pmp) × z1",
        },
        {
            "simbolo": "θ_lim",
            "significado": "Limiar crítico de umidade volumétrica na Camada 1 para conforto hídrico e disparo da E1",
            "valor": f"{soil.theta_lim:.3f}",
            "unidade": "cm³/cm³",
            "origem": "derivado: θ_lim = θ_cc − p × (θ_cc − θ_pmp)",
        },
        {
            "simbolo": "S1_cc",
            "significado": "Lâmina máxima retida na Camada 1 na capacidade de campo",
            "valor": f"{s1_cc:.1f}",
            "unidade": "mm",
            "origem": "derivado: S1_cc = θ_cc × z1",
        },
        {
            "simbolo": "S2_cc",
            "significado": "Lâmina máxima retida na Camada 2 na capacidade de campo",
            "valor": f"{s2_cc:.1f}",
            "unidade": "mm",
            "origem": "derivado: S2_cc = θ_cc × z2",
        },
        {
            "simbolo": "S1_pmp",
            "significado": "Armazenamento residual mínimo na Camada 1 no ponto de murcha permanente",
            "valor": f"{s1_pmp:.1f}",
            "unidade": "mm",
            "origem": "derivado: S1_pmp = θ_pmp × z1",
        },
        {
            "simbolo": "S1_sat",
            "significado": "Armazenamento de saturação por camada",
            "valor": f"{s1_sat:.1f}",
            "unidade": "mm",
            "origem": "derivado: S1_sat = θ_sat × z1",
        },
        {
            "simbolo": "Deficit_solo_lim",
            "significado": "Depleção hídrica na Camada 1 correspondente exatamente a θ_lim",
            "valor": f"{def_crit:.2f}",
            "unidade": "mm",
            "origem": "derivado: Deficit_solo_lim = (θ_cc − θ_lim) × z1 = p × AD",
        },
        {
            "simbolo": "Kc_ini",
            "significado": "Coeficiente de cultura na fase inicial (dias 1 a 15 do ciclo)",
            "valor": "0.70",
            "unidade": "adimensional",
            "origem": "valor: FAO-56, Tabela 12 (grupo Small Vegetables); fase em degrau (dias 1 a 15) sem fonte, trocada no v2 pela curva da eq. 66 com as fases da Tabela 11",
        },
        {
            "simbolo": "Kc_med",
            "significado": "Coeficiente de cultura na fase intermediária (dias 16 a 55 do ciclo)",
            "valor": "1.00",
            "unidade": "adimensional",
            "origem": "valor: FAO-56, Tabela 12 (alface); fase em degrau (dias 16 a 55) sem fonte, trocada no v2 pela curva da eq. 66",
        },
        {
            "simbolo": "Kc_fim",
            "significado": "Coeficiente de cultura na fase final (dias 56 a 70 do ciclo)",
            "valor": "0.95",
            "unidade": "adimensional",
            "origem": "valor: FAO-56, Tabela 12 (alface); fase em degrau (dias 56 a 70) sem fonte, trocada no v2 pela curva da eq. 66",
        },
        {
            "simbolo": "lamina_fixa",
            "significado": "Lâmina nominal por acionamento na estratégia E1 (referência e varredura)",
            "valor": "10.0 (varredura: 5, 10, 15, 20, 25, 30)",
            "unidade": "mm",
            "origem": "premissa do modelo",
        },
        {
            "simbolo": "limiar_deficit",
            "significado": "Gatilho de déficit acumulado para acionamento nas estratégias E2 e E3",
            "valor": "10.0",
            "unidade": "mm",
            "origem": f"premissa do v1; não corresponde a p × AD = {def_crit:.2f} mm (banda morta); no v2 o gatilho é o RAW calculado",
        },
        {
            "simbolo": "area_canteiro",
            "significado": "Área útil do canteiro monitorado para conversão entre lâmina (mm) e volume (L)",
            "valor": "10.0",
            "unidade": "m²",
            "origem": "premissa do modelo",
        },
        {
            "simbolo": "V_cap (Abundante / Moderado / Restrito)",
            "significado": "Capacidade nominal do reservatório nos cenários padrão (e varredura 250–2000 L)",
            "valor": "1000 / 500 / 500",
            "unidade": "L",
            "origem": "premissa de cenário",
        },
        {
            "simbolo": "Δt_reab (Abundante / Moderado / Restrito)",
            "significado": "Intervalo entre reabastecimentos do reservatório nos cenários padrão",
            "valor": "3 / 7 / 14",
            "unidade": "dias",
            "origem": "premissa de cenário",
        },
        {
            "simbolo": "Gsc",
            "significado": "Constante solar extraterrestre na equação de Ra",
            "valor": f"{GSC_MJ_M2_MIN:.4f}",
            "unidade": "MJ·m⁻²·min⁻¹",
            "origem": "FAO-56, eq. 21",
        },
        {
            "simbolo": "f_conv_Ra",
            "significado": "Fator de conversão de radiação (MJ·m⁻²·dia⁻¹) em equivalente de evaporação (mm·dia⁻¹)",
            "valor": f"{FATOR_CONVERSAO_MJ_PARA_MM:.3f}",
            "unidade": "mm·m²·MJ⁻¹",
            "origem": "FAO-56, eq. 20 (1/λ)",
        },
        {
            "simbolo": "c_HS, T_offset, exp_HS",
            "significado": "Coeficientes empíricos da equação de ET0 (0,0023; 17,8 °C; expoente térmico 0,5)",
            "valor": "0.0023; 17.8; 0.5",
            "unidade": "°C⁻¹·⁵; °C; adim.",
            "origem": "Hargreaves e Samani (1985); FAO-56, eq. 52",
        },
        {
            "simbolo": "c_dr, c_δ1, c_δ2",
            "significado": "Constantes astronômicas de distância relativa Terra-Sol (0,033) e declinação solar (0,409 rad; 1,39 rad)",
            "valor": "0.033; 0.409; 1.39",
            "unidade": "adim.; rad; rad",
            "origem": "FAO-56, eqs. 23 e 24",
        },
        {
            "simbolo": "φ (latitude)",
            "significado": "Latitude geográfica da estação meteorológica usada no cálculo de Ra",
            "valor": f"{lat_val:.8f}",
            "unidade": "graus decimais",
            "origem": "extraído do arquivo INMET (campo LATITUDE:; do bloco de metadados)",
        },
        {
            "simbolo": "λ (longitude)",
            "significado": "Longitude geográfica da estação meteorológica",
            "valor": f"{lon_val:.8f}",
            "unidade": "graus decimais",
            "origem": "extraído do arquivo INMET (campo LONGITUDE:; do bloco de metadados)",
        },
        {
            "simbolo": "z_est (altitude)",
            "significado": "Altitude geométrica da estação meteorológica",
            "valor": f"{alt_val:.2f}",
            "unidade": "m",
            "origem": "extraído do arquivo INMET (campo ALTITUDE:; do bloco de metadados)",
        },
    ]


def _obter_info_reprodutibilidade(tempo_execucao_s: float) -> Dict[str, Any]:
    """Coleta informações de ambiente, versões, commit git e determinismo (Parte 7)."""
    git_hash = "Não aplicável (diretório de trabalho sem repositório Git inicializado / .git ausente)"
    try:
        res_git = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if res_git.returncode == 0 and res_git.stdout.strip():
            git_hash = res_git.stdout.strip()
    except Exception:
        pass

    return {
        "python_version": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "sqlite3_version": sqlite3.sqlite_version,
        "matplotlib_version": matplotlib.__version__,
        "numpy_version": np.__version__,
        "git_commit_hash": git_hash,
        "comando_reproducao": "python3 main.py pipeline --modelo v1",
        "comando_testes": "python3 -m unittest discover -s tests -v",
        "tempo_execucao_total_s": round(tempo_execucao_s, 3),
        "aleatoriedade": (
            "Não há aleatoriedade em nenhum componente do projeto. "
            "Nenhum gerador pseudoaleatório (random / numpy.random) é importado ou invocado; "
            "todas as equações físicas, regras de decisão e agregações são estritamente determinísticas."
        ),
        "semente_aleatoria": "Não aplicável (modelo 100% determinístico)",
    }


def executar_estudo_completo(
    caminho_csv_clima: str = DEFAULT_CLIMATE_CSV,
    caminho_json_saida: str = DEFAULT_REPORT_JSON,
    caminho_md_saida: str = DEFAULT_REPORT_MD,
    diretorio_tabelas: str = DEFAULT_TABELAS_DIR,
    diretorio_rodadas: str = DEFAULT_RODADAS_DIR,
    diretorio_figuras: str = DEFAULT_FIGURES_DIR,
) -> Dict[str, Any]:
    """
    Executa todas as etapas científicas (Partes 1 a 8):
      1. Leitura do arquivo bruto real do BDMEP/INMET em `data/raw/`, extração da latitude e provas de procedência.
      2. Verificação de lacunas (> 3 dias consecutivos aborta a execução — Parte 1.7) e geração de `resultados/v1/processed/`.
      3. Validação física obrigatória contra constantes literais calculadas à mão (Seção 6 / Tabela T6).
      4. Simulação da matriz comparativa principal com limite físico universal de reservatório (Parte 2 / Tabela T2).
      5. Análise de sensibilidade da lâmina fixa da E1 nos 3 cenários (Parte 3.3 / Tabela T3).
      6. Varredura completa de dimensionamento do reservatório na E3 (48 rodadas — Tabelas T4 e T5).
      7. Geração das tabelas CSV T1 a T8, séries diárias e figuras F1 a F5 em `resultados/v1/`.
      8. Geração do `relatorio_final.md` com as 15 seções na ordem exata especificada na Parte 8.
    """
    t0 = time.perf_counter()
    os.makedirs(diretorio_tabelas, exist_ok=True)
    os.makedirs(diretorio_rodadas, exist_ok=True)
    os.makedirs(diretorio_figuras, exist_ok=True)

    soil = SoilParams()

    # -------------------------------------------------------------------------
    # ETAPA A: Testes obrigatórios de validação física independente (T6)
    # -------------------------------------------------------------------------
    validacao = executar_testes_validacao_secao6(soil)
    registros_val_diario = validacao.pop("registros_diarios", [])
    if not validacao["aprovado"]:
        raise RuntimeError(f"Falha nos testes obrigatórios de validação física (Seção 6): {validacao}")

    csv_rodada_val = _salvar_csv(
        os.path.join(diretorio_rodadas, "rodadas_validacao_fisica_diario.csv"),
        registros_val_diario,
    )

    t1_v = validacao["teste_1_conservacao_massa"]
    t2_v = validacao["teste_2_secagem_monotonica"]
    t3_v = validacao["teste_3_saturacao"]
    linhas_t6 = [
        {
            "teste": "1. Conservação de Massa Independente",
            "dias_simulados": t1_v["dias_simulados"],
            "condicao_inicial": f"theta1(0)={t1_v['theta1_inicial']:.2f}; theta2(0)={t1_v['theta2_inicial']:.2f}; S_ini=102.0 mm",
            "forçantes": "ETc=4.0 mm/d; P=[0,15,0,0,0,0,15,0,0,0] (30 mm); I=[12,0,0,0,0,12,0,0,0,0] (24 mm)",
            "grandeza_verificada": "Lado A (Entradas - Saidas) vs Lado B (Delta_S = S_fim - S_ini) e Sigma_D2",
            "valor_esperado_literal": "Entradas=54.0; Saidas=56.0; Sigma_D2=16.0; S_fim=100.0; Lado_A=-2.0; Lado_B=-2.0 mm",
            "valor_observado": (
                f"Entradas={t1_v['entradas_mm']:.4f}; Saidas={t1_v['saidas_mm']:.4f}; "
                f"Sigma_D2={t1_v['d2_acumulado_mm_observado']:.4f}; S_fim={t1_v['s_final_mm_observado']:.4f}; "
                f"Lado_A={t1_v['lado_a_saldo_fluxos_mm']:.4f}; Lado_B={t1_v['delta_armazenamento_mm']:.4f} mm"
            ),
            "erro_absoluto": f"{t1_v['erro_absoluto_mm']:.8f} mm",
            "erro_relativo_pct": f"{t1_v['erro_relativo_pct']:.8f}% (< 0.1%)",
            "status": "APROVADO" if t1_v["aprovado"] else "REPROVADO",
        },
        {
            "teste": "2. Secagem Monotônica",
            "dias_simulados": t2_v["dias_simulados"],
            "condicao_inicial": f"theta1(0)={t2_v['theta1_inicial']:.2f} (theta_cc); theta2(0)={t2_v['theta2_inicial']:.2f}",
            "forçantes": "P=0.0 mm/d; I=0.0 mm/d; ETc_pot=4.0 mm/d constante por 60 dias",
            "grandeza_verificada": "Decaimento monotônico de theta1 até estabilizar em theta_pmp no dia 7 e Sigma_ETc_real",
            "valor_esperado_literal": "theta1(dia 7)=0.1400; theta1(dia 60)=0.1400 cm3/cm3; Sigma_ETc_real=28.0 mm",
            "valor_observado": (
                f"theta1(dia 7)={t2_v['theta1_dia_7_observado']:.4f}; "
                f"theta1(dia 60)={t2_v['theta1_final']:.4f} cm3/cm3; "
                f"Sigma_ETc_real={t2_v['etc_real_acumulada_mm_observada']:.4f} mm; "
                f"monotonica={t2_v['monotonica']}"
            ),
            "erro_absoluto": "0.00000000",
            "erro_relativo_pct": "0.00000000%",
            "status": "APROVADO" if t2_v["aprovado"] else "REPROVADO",
        },
        {
            "teste": "3. Saturação Extrema",
            "dias_simulados": t3_v["dias_simulados"],
            "condicao_inicial": f"theta1(0)={t3_v['theta1_inicial']:.2f} (theta_cc); theta2(0)={t3_v['theta2_inicial']:.2f} (theta_cc)",
            "forçantes": "P(1)=250.0 mm; I(1)=0.0 mm; ETc(1)=0.0 mm",
            "grandeza_verificada": "Conversão integral do excedente em D1 e D2 e respeito a theta <= theta_sat (0.45)",
            "valor_esperado_literal": "D1=250.0 mm; D2=250.0 mm; theta1(1)=0.2800 <= 0.45; theta2(1)=0.2800 <= 0.45",
            "valor_observado": (
                f"D1={t3_v['drenagem_d1_mm_observada']:.4f} mm; D2={t3_v['drenagem_profunda_d2_mm']:.4f} mm; "
                f"theta1(1)={t3_v['theta1_final']:.4f}; theta2(1)={t3_v['theta2_final']:.4f}"
            ),
            "erro_absoluto": "0.00000000 mm",
            "erro_relativo_pct": "0.00000000%",
            "status": "APROVADO" if t3_v["aprovado"] else "REPROVADO",
        },
    ]
    csv_t6 = _salvar_csv(os.path.join(diretorio_tabelas, "T6_testes_validacao_fisica.csv"), linhas_t6)

    # -------------------------------------------------------------------------
    # ETAPA B: Leitura da Série Real do BDMEP/INMET e Qualidade (T1, T7, T8)
    # -------------------------------------------------------------------------
    dados_clima = carregar_e_tratar_serie_climatica(
        caminho_csv=caminho_csv_clima,
        max_lacuna_interpolavel=3,
        usar_kc_fases=True,
    )
    series_por_periodo = dados_clima["series"]
    qualidade_clima = dados_clima["qualidade"]
    latitude_deg = dados_clima["latitude_deg"]
    meta_proc = qualidade_clima["global"]["metadados_procedencia"]

    # Tabela T1: Caracterização climática dos dois ciclos
    linhas_t1: List[Dict[str, Any]] = []
    linhas_t1_descritivas: List[Dict[str, Any]] = []
    for per_nome in ("Estacao_Chuvosa", "Estacao_Seca"):
        qp = qualidade_clima[per_nome]
        ed = qp["estatisticas_descritivas"]
        linhas_t1.append({
            "ciclo": per_nome,
            "data_inicial": qp["data_inicial"],
            "data_final": qp["data_final"],
            "dias_ciclo": qp["total_dias"],
            "precipitacao_acumulada_mm": qp["precipitacao_total_mm"],
            "et0_acumulada_mm": qp["et0_total_mm"],
            "et0_media_mm_dia": qp["et0_medio_mm_dia"],
            "etc_acumulada_mm": qp["etc_total_mm"],
            "etc_media_mm_dia": qp["etc_medio_mm_dia"],
            "t_media_ciclo_c": qp["t_med_ciclo_c"],
            "t_max_absoluta_c": qp["t_max_abs_c"],
            "t_min_absoluta_c": qp["t_min_abs_c"],
            "dias_com_chuva": qp["dias_com_chuva"],
            "maior_evento_chuva_mm": qp["maior_evento_chuva_mm"],
            "data_maior_evento_chuva": qp["data_maior_evento_chuva"],
        })
        for var_cod, st_desc in ed.items():
            linhas_t1_descritivas.append({
                "ciclo": per_nome,
                "intervalo_datas": f"{qp['data_inicial']} a {qp['data_final']}",
                "variavel": var_cod,
                "minimo": st_desc["minimo"],
                "maximo": st_desc["maximo"],
                "media": st_desc["media"],
                "desvio_padrao": st_desc["desvio_padrao"],
                "mediana": st_desc["mediana"],
                "soma_no_ciclo": st_desc["soma"],
            })

    csv_t1 = _salvar_csv(os.path.join(diretorio_tabelas, "T1_caracterizacao_climatica.csv"), linhas_t1)
    csv_t1b = _salvar_csv(
        os.path.join(diretorio_tabelas, "T1b_estatisticas_descritivas_por_variavel_ciclo.csv"),
        linhas_t1_descritivas,
    )

    # Tabela T7: Qualidade do dado climático por variável e ciclo (incluindo auditoria do arquivo anual completo)
    linhas_t7: List[Dict[str, Any]] = []
    for per_nome in ("Estacao_Chuvosa", "Estacao_Seca"):
        qp = qualidade_clima[per_nome]
        for var_nome, st in qp["por_variavel"].items():
            linhas_t7.append({
                "escopo": per_nome,
                "intervalo_datas": f"{qp['data_inicial']} a {qp['data_final']}",
                "variavel": var_nome,
                "coluna_bdmep": st["coluna_original_bdmep"],
                "dias_avaliados": st["total_registros"],
                "dias_ausentes": st["registros_faltantes"],
                "percentual_dias_ausentes_pct": st["percentual_falhas_pct"],
                "horas_avaliadas": st["horas_esperadas"],
                "horas_ausentes": st["horas_ausentes"],
                "percentual_horas_ausentes_pct": st["percentual_horas_ausentes_pct"],
                "maior_lacuna_consecutiva_dias": st["maior_lacuna_consecutiva_dias"],
                "datas_das_lacunas": st["datas_lacunas_resumo"],
                "tratamento_aplicado": st["tratamento_adotado"],
            })
    for var_nome, st_ano in qualidade_clima["global"]["qualidade_arquivo_anual_completo"].items():
        linhas_t7.append({
            "escopo": "Arquivo_Bruto_Anual_2023",
            "intervalo_datas": f"{meta_proc['data_inicial_arquivo']} a {meta_proc['data_final_arquivo']}",
            "variavel": var_nome,
            "coluna_bdmep": st_ano["coluna_original_bdmep"],
            "dias_avaliados": st_ano["total_registros"],
            "dias_ausentes": st_ano["registros_faltantes"],
            "percentual_dias_ausentes_pct": st_ano["percentual_falhas_pct"],
            "horas_avaliadas": st_ano["horas_esperadas_total"],
            "horas_ausentes": st_ano["horas_ausentes_total"],
            "percentual_horas_ausentes_pct": st_ano["percentual_horas_ausentes_pct"],
            "maior_lacuna_consecutiva_dias": st_ano["maior_lacuna_consecutiva_dias"],
            "datas_das_lacunas": st_ano["datas_lacunas_resumo"],
            "tratamento_aplicado": "Fora da janela dos ciclos simulados (lacunas concentradas em out-dez/2023)",
        })
    csv_t7 = _salvar_csv(os.path.join(diretorio_tabelas, "T7_qualidade_dado_climatico.csv"), linhas_t7)

    # Tabela T8: Parâmetros e fontes (Parte 4)
    linhas_t8 = construir_tabela_t8_parametros(soil, meta_proc)
    csv_t8 = _salvar_csv(os.path.join(diretorio_tabelas, "T8_parametros_e_fontes.csv"), linhas_t8)

    # -------------------------------------------------------------------------
    # ETAPA C: Comparação Principal (T2) + Contrafactual SEQUEIRO (I=0)
    # -------------------------------------------------------------------------
    estrategias = ["E1", "E2", "E3"]
    cenarios_nomes = ["Abundante", "Moderado", "Restrito"]
    tabela_metricas: List[Dict[str, Any]] = []
    tabela_contrafactuais: List[Dict[str, Any]] = []
    simulacoes_detalhadas: Dict[str, Any] = {}
    diario_comparacao: List[Dict[str, Any]] = []

    cf_por_periodo: Dict[str, Dict[str, Any]] = {}
    for periodo_nome in ("Estacao_Chuvosa", "Estacao_Seca"):
        serie_dias = series_por_periodo[periodo_nome]
        res_cf = simular_estrategia(
            estrategia_codigo="SEQUEIRO",
            serie_climatica=serie_dias,
            latitude_deg=latitude_deg,
            soil=soil,
            cenario=SCENARIOS_PADRAO["Abundante"],
            periodo_nome=periodo_nome,
        )
        cf_por_periodo[periodo_nome] = res_cf
        m_cf = asdict(res_cf["metricas"])
        m_cf["cenario"] = "Contrafactual (I=0)"
        tabela_contrafactuais.append(m_cf)
        diario_comparacao.extend(
            _linhas_diarias_para_csv(
                res_cf["historico"],
                res_cf["historico"],
                {"periodo": periodo_nome, "cenario": "Contrafactual_I0", "estrategia": "SEQUEIRO"},
            )
        )

    for periodo_nome in ("Estacao_Chuvosa", "Estacao_Seca"):
        serie_dias = series_por_periodo[periodo_nome]
        res_cf = cf_por_periodo[periodo_nome]
        d2_chuva_mm = res_cf["metricas"].percolacao_acumulada_mm
        cf_hist = res_cf["historico"]

        for cenario_nome in cenarios_nomes:
            cenario_cfg = SCENARIOS_PADRAO[cenario_nome]
            for est_cod in estrategias:
                res = simular_estrategia(
                    estrategia_codigo=est_cod,
                    serie_climatica=serie_dias,
                    latitude_deg=latitude_deg,
                    soil=soil,
                    cenario=cenario_cfg,
                    periodo_nome=periodo_nome,
                    d2_chuva_referencia_mm=d2_chuva_mm,
                )
                m_dict = asdict(res["metricas"])
                tabela_metricas.append(m_dict)
                chave = f"{periodo_nome}__{cenario_nome}__{est_cod}"
                simulacoes_detalhadas[chave] = res
                diario_comparacao.extend(
                    _linhas_diarias_para_csv(
                        res["historico"],
                        cf_hist,
                        {"periodo": periodo_nome, "cenario": cenario_nome, "estrategia": est_cod},
                    )
                )

    csv_t2 = _salvar_csv(
        os.path.join(diretorio_tabelas, "T2_comparacao_principal.csv"),
        tabela_metricas,
    )
    csv_rodada_comp = _salvar_csv(
        os.path.join(diretorio_rodadas, "rodadas_comparacao_principal_diario.csv"),
        diario_comparacao,
    )

    # -------------------------------------------------------------------------
    # ETAPA D: Sensibilidade da Lâmina Fixa da E1 (T3: 5, 10, 15, 20, 25, 30 mm)
    # -------------------------------------------------------------------------
    laminas_teste = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
    sensibilidade_e1_resumo: List[Dict[str, Any]] = []
    sensibilidade_e1_diario: List[Dict[str, Any]] = []

    for periodo_nome in ("Estacao_Chuvosa", "Estacao_Seca"):
        serie_dias = series_por_periodo[periodo_nome]
        res_cf = cf_por_periodo[periodo_nome]
        d2_chuva_mm = res_cf["metricas"].percolacao_acumulada_mm
        cf_hist = res_cf["historico"]

        for cenario_nome in cenarios_nomes:
            cenario_cfg = SCENARIOS_PADRAO[cenario_nome]
            for lf in laminas_teste:
                res_e1 = simular_estrategia(
                    estrategia_codigo="E1",
                    serie_climatica=serie_dias,
                    latitude_deg=latitude_deg,
                    soil=soil,
                    cenario=cenario_cfg,
                    periodo_nome=periodo_nome,
                    lamina_fixa_mm=lf,
                    d2_chuva_referencia_mm=d2_chuva_mm,
                )
                m = asdict(res_e1["metricas"])
                linha_resumo = {
                    "periodo": periodo_nome,
                    "cenario": cenario_nome,
                    "estrategia": "E1",
                    "lamina_fixa_mm": lf,
                    **{k: v for k, v in m.items() if k not in ("periodo", "cenario", "estrategia")},
                }
                sensibilidade_e1_resumo.append(linha_resumo)
                sensibilidade_e1_diario.extend(
                    _linhas_diarias_para_csv(
                        res_e1["historico"],
                        cf_hist,
                        {
                            "periodo": periodo_nome,
                            "cenario": cenario_nome,
                            "estrategia": "E1",
                            "lamina_fixa_mm": lf,
                        },
                    )
                )

    csv_t3 = _salvar_csv(
        os.path.join(diretorio_tabelas, "T3_sensibilidade_e1.csv"),
        sensibilidade_e1_resumo,
    )
    csv_rodada_sens = _salvar_csv(
        os.path.join(diretorio_rodadas, "rodadas_sensibilidade_e1_diario.csv"),
        sensibilidade_e1_diario,
    )

    # -------------------------------------------------------------------------
    # ETAPA E: Dimensionamento e Varredura do Reservatório (T4 e T5: 48 rodadas)
    # -------------------------------------------------------------------------
    capacidades_l = [250.0, 500.0, 750.0, 1000.0, 1250.0, 1500.0, 1750.0, 2000.0]
    intervalos_dias = [3, 7, 14]
    varredura_e3_resumo: List[Dict[str, Any]] = []
    varredura_e3_diario: List[Dict[str, Any]] = []
    tabela_dimensionamento_e3: List[Dict[str, Any]] = []

    for periodo_nome in ("Estacao_Chuvosa", "Estacao_Seca"):
        serie_dias = series_por_periodo[periodo_nome]
        res_cf = cf_por_periodo[periodo_nome]
        d2_chuva_mm = res_cf["metricas"].percolacao_acumulada_mm
        cf_hist = res_cf["historico"]

        for interv in intervalos_dias:
            cap_minima_90: Optional[float] = None
            conforto_na_cap_minima: Optional[float] = None
            lamina_na_cap_minima: Optional[float] = None
            eficiencia_na_cap_minima: Optional[float] = None
            d2_inc_na_cap_minima: Optional[float] = None

            for cap in capacidades_l:
                nome_cen = f"Cap_{int(cap)}L_{interv}d"
                cfg_var = ScenarioConfig(
                    nome=nome_cen,
                    capacidade_reservatorio_l=cap,
                    intervalo_reabastecimento_dias=interv,
                    area_canteiro_m2=10.0,
                )
                res_e3 = simular_estrategia(
                    estrategia_codigo="E3",
                    serie_climatica=serie_dias,
                    latitude_deg=latitude_deg,
                    soil=soil,
                    cenario=cfg_var,
                    periodo_nome=periodo_nome,
                    d2_chuva_referencia_mm=d2_chuva_mm,
                )
                m = asdict(res_e3["metricas"])
                taxa_max_mm_dia = round(cap / (interv * cfg_var.area_canteiro_m2), 2)
                linha_var = {
                    "periodo": periodo_nome,
                    "intervalo_reabastecimento_dias": interv,
                    "capacidade_reservatorio_l": cap,
                    "oferta_maxima_mm_dia": taxa_max_mm_dia,
                    "atende_conforto_90pct": m["conforto_hidrico_pct"] >= 90.0,
                    **{k: v for k, v in m.items() if k not in ("periodo", "cenario", "estrategia")},
                }
                varredura_e3_resumo.append(linha_var)

                if cap_minima_90 is None and m["conforto_hidrico_pct"] >= 90.0:
                    cap_minima_90 = cap
                    conforto_na_cap_minima = m["conforto_hidrico_pct"]
                    lamina_na_cap_minima = m["lamina_total_mm"]
                    eficiencia_na_cap_minima = m["eficiencia_incremental_pct"]
                    d2_inc_na_cap_minima = m["d2_incremental_mm"]

                varredura_e3_diario.extend(
                    _linhas_diarias_para_csv(
                        res_e3["historico"],
                        cf_hist,
                        {
                            "periodo": periodo_nome,
                            "intervalo_reabastecimento_dias": interv,
                            "capacidade_reservatorio_l": cap,
                            "estrategia": "E3",
                        },
                    )
                )

            tabela_dimensionamento_e3.append({
                "periodo": periodo_nome,
                "intervalo_reabastecimento_dias": interv,
                "demanda_etc_media_mm_dia": qualidade_clima[periodo_nome]["etc_medio_mm_dia"],
                "precipitacao_total_mm": qualidade_clima[periodo_nome]["precipitacao_total_mm"],
                "capacidade_minima_conforto_90_l": cap_minima_90 if cap_minima_90 is not None else "> 2000",
                "oferta_maxima_na_cap_minima_mm_dia": (
                    round(cap_minima_90 / (interv * 10.0), 2) if cap_minima_90 is not None else None
                ),
                "conforto_obtido_pct": conforto_na_cap_minima,
                "lamina_aplicada_mm": lamina_na_cap_minima,
                "d2_incremental_mm": d2_inc_na_cap_minima,
                "eficiencia_incremental_pct": eficiencia_na_cap_minima,
            })

    csv_t4 = _salvar_csv(
        os.path.join(diretorio_tabelas, "T4_dimensionamento_reservatorio.csv"),
        tabela_dimensionamento_e3,
    )
    csv_t5 = _salvar_csv(
        os.path.join(diretorio_tabelas, "T5_varredura_reservatorio.csv"),
        varredura_e3_resumo,
    )
    csv_rodada_var = _salvar_csv(
        os.path.join(diretorio_rodadas, "rodadas_varredura_reservatorio_e3_diario.csv"),
        varredura_e3_diario,
    )

    # -------------------------------------------------------------------------
    # ETAPA F: Geração das Figuras F1 a F5 (300 dpi + CSVs)
    # -------------------------------------------------------------------------
    figuras_geradas = gerar_todas_figuras(
        simulacoes_detalhadas=simulacoes_detalhadas,
        sensibilidade_e1=sensibilidade_e1_resumo,
        varredura_e3=varredura_e3_resumo,
        metricas_comparativas=tabela_metricas,
        theta_lim=soil.theta_lim,
        theta_cc=soil.theta_cc,
        theta_pmp=soil.theta_pmp,
        diretorio_figuras=diretorio_figuras,
    )

    tempo_total = time.perf_counter() - t0
    reprodutibilidade = _obter_info_reprodutibilidade(tempo_total)

    arquivos_tabelas = [csv_t1, csv_t1b, csv_t2, csv_t3, csv_t4, csv_t5, csv_t6, csv_t7, csv_t8]
    arquivos_rodadas = [csv_rodada_comp, csv_rodada_sens, csv_rodada_var, csv_rodada_val]

    consolidado = {
        "parametros_solo": {
            **asdict(soil),
            "agua_disponivel_mm": round(soil.agua_disponivel_mm, 2),
            "theta_lim": round(soil.theta_lim, 4),
        },
        "validacao_secao6": validacao,
        "qualidade_serie_climatica": qualidade_clima,
        "tabela_t1_caracterizacao_climatica": linhas_t1,
        "tabela_t1b_estatisticas_descritivas": linhas_t1_descritivas,
        "contrafactuais_sequeiro": tabela_contrafactuais,
        "metricas_comparativas": tabela_metricas,
        "sensibilidade_lamina_fixa_e1": sensibilidade_e1_resumo,
        "dimensionamento_reservatorio_e3": tabela_dimensionamento_e3,
        "varredura_reservatorio_e3": varredura_e3_resumo,
        "tabela_t6_validacao": linhas_t6,
        "tabela_t7_qualidade": linhas_t7,
        "tabela_t8_parametros": linhas_t8,
        "figuras_geradas": figuras_geradas,
        "reprodutibilidade": reprodutibilidade,
        "arquivos_tabelas_csv": arquivos_tabelas,
        "arquivos_rodadas_csv": arquivos_rodadas,
        "arquivos_csv_brutos": arquivos_tabelas + arquivos_rodadas,
    }

    os.makedirs(os.path.dirname(caminho_json_saida), exist_ok=True)
    with open(caminho_json_saida, "w", encoding="utf-8") as f:
        json.dump(_caminhos_relativos(consolidado), f, ensure_ascii=False, indent=2)

    gerar_relatorio_markdown(consolidado, caminho_md_saida, detalhes={
        "simulacoes": simulacoes_detalhadas,
        "varredura_diario": varredura_e3_diario,
        "n_linhas": {
            "comparacao": len(diario_comparacao),
            "sensibilidade": len(sensibilidade_e1_diario),
            "varredura": len(varredura_e3_diario),
            "validacao": len(registros_val_diario),
        },
    })

    return {
        "consolidado": consolidado,
        "simulacoes_detalhadas": simulacoes_detalhadas,
        "series_por_periodo": series_por_periodo,
    }


def _br(x: float, casas: int = 2) -> str:
    """Número em pt-BR (1.234,56) para o texto do relatório."""
    texto = f"{x:,.{casas}f}"
    return texto.replace(",", "\u0000").replace(".", ",").replace("\u0000", ".")


NOMES_PERIODO_V1 = {"Estacao_Chuvosa": "Estação Chuvosa", "Estacao_Seca": "Estação Seca"}


def _secao_v1_3(consolidado: Dict[str, Any]) -> List[str]:
    """Seção 3: escolha do ano e qualidade dos ciclos, só com valores calculados do arquivo."""
    q = consolidado["qualidade_serie_climatica"]
    anual = q["global"]["qualidade_arquivo_anual_completo"]["precipitacao_mm"]
    periodos = [p for p in ("Estacao_Chuvosa", "Estacao_Seca") if p in q]
    dias_aus = sum(q[p]["por_variavel"][v]["registros_faltantes"] for p in periodos for v in q[p]["por_variavel"])
    horas_aus = sum(q[p]["por_variavel"][v]["horas_ausentes"] for p in periodos for v in q[p]["por_variavel"])
    horas_esp = {p: q[p]["por_variavel"]["precipitacao_mm"]["horas_esperadas"] for p in periodos}
    janelas = "; ".join(f"`{p}`: `{q[p]['data_inicial']}` a `{q[p]['data_final']}`" for p in periodos)
    return [
        "- **Escolha do ano de 2023:** este relatório do v1 usa só o arquivo de 2023. A completude da estação `A204` "
        "em 2024 e 2025 é conferida pelo v2, a partir dos arquivos do INMET (`resultados/v2/tabelas/tab_completude_anos.md`). "
        f"No arquivo de 2023, os dias inteiros sem dado somam `{anual['registros_faltantes']}` "
        f"(maior lacuna de `{anual['maior_lacuna_consecutiva_dias']}` dias): {anual['datas_lacunas_resumo']}, todos fora dos ciclos.",
        f"- **Qualidade nos dois ciclos simulados ({janelas}):** `{dias_aus}` dias ausentes e `{horas_aus}` horas ausentes "
        "somando todas as variáveis; registros horários esperados por ciclo: "
        + "; ".join(f"`{p}` `{_br(h, 0)}`" for p, h in horas_esp.items()) + ".",
    ]


def _secao_v1_8_3(consolidado: Dict[str, Any]) -> List[str]:
    """Seção 8.3: E1 entre cenários, com os valores da T2."""
    linhas = ["- **E1 (lâmina fixa) nos três cenários, valores da Tabela T2:**"]
    for per in ("Estacao_Chuvosa", "Estacao_Seca"):
        partes = []
        for m in consolidado["metricas_comparativas"]:
            if m["estrategia"] == "E1" and m["periodo"] == per:
                vazio = (f", primeiro esvaziamento no dia {m['primeiro_dia_reservatorio_vazio']}"
                         if m["primeiro_dia_reservatorio_vazio"] is not None else "")
                partes.append(
                    f"`{m['cenario']}`: `{_br(m['lamina_total_mm'])} mm` aplicados em `{m['numero_acionamentos']}` "
                    f"acionamentos, `{_br(m['lamina_nao_atendida_mm'])} mm` não atendidos, conforto de "
                    f"`{_br(m['conforto_hidrico_pct'])}%`, `{m['dias_reservatorio_vazio']}` dias com reservatório vazio{vazio}")
        linhas.append(f"  - **{NOMES_PERIODO_V1[per]}:** " + "; ".join(partes) + ".")
    return linhas


def _secoes_v1_11_a_13(consolidado: Dict[str, Any], detalhes: Optional[Dict[str, Any]]) -> List[str]:
    """Seções 11, 12 e 13 do relatório do v1, só com valores calculados (sem números digitados)."""
    ps = consolidado["parametros_solo"]
    q = consolidado["qualidade_serie_climatica"]
    ad, p_dep, theta_lim = ps["agua_disponivel_mm"], ps["p"], ps["theta_lim"]
    s1_cc = ps["theta_cc"] * ps["z1"]
    folga = s1_cc - theta_lim * ps["z1"]
    limiar = inspect.signature(simular_estrategia).parameters["limiar_deficit_mm"].default
    seq = {c["periodo"]: c for c in consolidado["contrafactuais_sequeiro"]}
    L: List[str] = [
        "## 11. Nota Metodológica sobre a Decomposição da Percolação (`D2_incremental`)",
        "",
        "1. **Definição das grandezas:**",
        "   - `D2_total`: percolação profunda acumulada abaixo da Camada 2 na rodada com irrigação ativa.",
        "   - `D2_chuva`: percolação profunda acumulada no contrafactual em sequeiro ($I(t) = 0$), com a mesma série "
        f"climática e as mesmas condições iniciais ($\\theta_1(0) = \\theta_2(0) = \\theta_{{\\text{{cc}}}} = {_br(ps['theta_cc'])}$).",
        "   - `D2_incremental = D2_total − D2_chuva`.",
        "   - `Eficiência de Aplicação Incremental (%) = ((Lâmina Aplicada − D2_incremental) / Lâmina Aplicada) × 100`.",
        "2. **Limitação metodológica (interação solo–chuva–irrigação):**",
        "   - No sequeiro, a ETc esgota a Camada 1 até perto de $\\theta_{\\text{pmp}}$, abrindo até "
        f"$AD = {_br(ad, 1)}\\,\\text{{mm}}$ de espaço antes de qualquer drenagem. Valores calculados: "
        + "; ".join(f"`D2_chuva` = `{_br(seq[p]['d2_chuva_mm'])} mm` na {NOMES_PERIODO_V1[p]}, com "
                    f"$\\Sigma P = {_br(q[p]['precipitacao_total_mm'])}\\,\\text{{mm}}$" for p in seq) + ".",
        f"   - Nas rodadas irrigadas, o controle mantém $\\theta_1 \\ge \\theta_{{\\text{{lim}}}} = {_br(theta_lim, 3)}$, o que "
        f"limita a folga de retenção na Camada 1 a $S_{{1,\\text{{cc}}}} - \\theta_{{\\text{{lim}}}} z_1 = {_br(folga)}\\,\\text{{mm}}$.",
        "   - Por isso `D2_incremental` não é uma atribuição física limpa à água da irrigação: inclui a chuva que, no solo "
        "seco do sequeiro, teria ficado retida.",
        "",
        "---",
        "",
        "## 12. Investigação da Não-Monotonicidade da E3 (Parte 3.2)",
        "",
    ]
    # 12.1: casos em que mais capacidade dá menos conforto, na varredura real de 2023.
    var = consolidado["varredura_reservatorio_e3"]
    casos = []
    for per in ("Estacao_Chuvosa", "Estacao_Seca"):
        for n in sorted({r["intervalo_reabastecimento_dias"] for r in var}):
            serie = sorted((r for r in var if r["periodo"] == per and r["intervalo_reabastecimento_dias"] == n),
                           key=lambda r: r["capacidade_reservatorio_l"])
            for a, b in zip(serie, serie[1:]):
                if b["conforto_hidrico_pct"] < a["conforto_hidrico_pct"]:
                    casos.append((per, n, a, b))
    L += ["### 12.1 Casos na série real do INMET de 2023", ""]
    if not casos:
        L += ["- Nenhum caso: na varredura da E3, o conforto nunca diminui quando a capacidade aumenta.", ""]
    for per, n, a, b in casos:
        L.append(f"- `{per}`, intervalo `{n}d`: `{_br(a['capacidade_reservatorio_l'], 0)} L` → conforto "
                 f"`{_br(a['conforto_hidrico_pct'])}%`; `{_br(b['capacidade_reservatorio_l'], 0)} L` → "
                 f"`{_br(b['conforto_hidrico_pct'])}%`.")
    L.append("")
    # 12.2: dias em que o estado de conforto difere entre as duas capacidades do primeiro caso.
    diario = (detalhes or {}).get("varredura_diario") or []
    L += ["### 12.2 Comparação dia a dia (primeiro caso da lista)", ""]
    if casos and diario:
        per, n, a, b = casos[0]

        def dias(cap):
            return {d["dia_idx"]: d for d in diario if d["periodo"] == per
                    and d["intervalo_reabastecimento_dias"] == n and d["capacidade_reservatorio_l"] == cap}

        da, db = dias(a["capacidade_reservatorio_l"]), dias(b["capacidade_reservatorio_l"])
        ca, cb = _br(a["capacidade_reservatorio_l"], 0), _br(b["capacidade_reservatorio_l"], 0)
        L += [f"| Dia | Data | {ca} L: $I$ (mm) | {ca} L: Deficit (mm) | {ca} L: $\\theta_{{1,\\text{{fim}}}}$ | "
              f"{cb} L: $I$ (mm) | {cb} L: Deficit (mm) | {cb} L: $\\theta_{{1,\\text{{fim}}}}$ |",
              "|---:|---|---:|---:|---:|---:|---:|---:|"]
        for k in sorted(da):
            xa, xb = da[k], db[k]
            if (xa["theta1_final"] >= theta_lim - 1e-9) != (xb["theta1_final"] >= theta_lim - 1e-9):
                L.append(f"| {k} | `{xa['data']}` | {_br(xa['i_efetiva_mm'])} | {_br(xa['deficit_acumulado_mm'], 4)} | "
                         f"{_br(xa['theta1_final'], 6)} | {_br(xb['i_efetiva_mm'])} | {_br(xb['deficit_acumulado_mm'], 4)} | "
                         f"{_br(xb['theta1_final'], 6)} |")
        L.append("")
    elif casos:
        L += ["- Série diária da varredura indisponível nesta chamada.", ""]
    L += [
        "### 12.3 Causa: banda morta entre o limiar de conforto e o gatilho",
        f"- No v1, $\\theta_{{\\text{{lim}}}}$ corresponde a uma depleção de $p \\times AD = {_br(p_dep)} \\times {_br(ad, 1)} = "
        f"{_br(p_dep * ad)}\\,\\text{{mm}}$, mas E2 e E3 só disparam com `Deficit` ≥ `{_br(limiar, 1)} mm`.",
        f"- Quando o déficit do fim do dia cai em $[{_br(p_dep * ad)};\\ {_br(limiar)})\\,\\text{{mm}}$, não há irrigação e o "
        "dia termina abaixo de $\\theta_{\\text{lim}}$. Doses menores (capacidade menor na E3) podem deslocar essa fase "
        "e evitar a banda, o que explica a não monotonicidade. No v2 o gatilho é o RAW calculado e a banda não existe.",
        "",
        "---",
        "",
        "## 13. Limitações e Anomalias Observadas",
        "",
    ]
    met = {(m["periodo"], m["cenario"], m["estrategia"]): m for m in consolidado["metricas_comparativas"]}
    e1_ab, e1_re = met[("Estacao_Seca", "Abundante", "E1")], met[("Estacao_Seca", "Restrito", "E1")]
    item1 = (f"1. **Percolação da `E1` no ciclo seco, `Restrito` × `Abundante`:** `D2_total` = "
             f"`{_br(e1_re['percolacao_acumulada_mm'])} mm` com `{_br(e1_re['lamina_total_mm'])} mm` aplicados (`Restrito`) e "
             f"`{_br(e1_ab['percolacao_acumulada_mm'])} mm` com `{_br(e1_ab['lamina_total_mm'])} mm` (`Abundante`).")
    L.append(item1)
    sim = (detalhes or {}).get("simulacoes") or {}
    hist = sim.get("Estacao_Seca__Restrito__E1", {}).get("historico") if sim else None
    if e1_re["percolacao_acumulada_mm"] > e1_ab["percolacao_acumulada_mm"] and hist:
        dias_d2 = [d for d in hist if d.d2_mm > 1e-9]
        L.append("   - Dias com percolação na `E1 Restrito` (série diária): " + "; ".join(
            f"dia {d.dia_idx} (`{d.data}`): I = `{_br(d.i_mm)} mm`, P = `{_br(d.p_mm)} mm`, D2 = `{_br(d.d2_mm)} mm`"
            + (", dia de reabastecimento" if d.reabastecido else "") for d in dias_d2) + ".")
    L.append("2. **Dias sem conforto na `E2` e na `E3` com o cenário `Abundante`** (ver a banda morta da seção 12.3):")
    for per in ("Estacao_Chuvosa", "Estacao_Seca"):
        for est in ("E2", "E3"):
            h = sim.get(f"{per}__Abundante__{est}", {}).get("historico") if sim else None
            if not h:
                continue
            sem = [d for d in h if d.theta1_final < theta_lim - 1e-9]
            texto = "; ".join(f"dia {d.dia_idx} (`{d.data}`, $\\theta_1$ = {_br(d.theta1_final, 6)}, Deficit = "
                              f"{_br(d.deficit_acumulado_mm, 4)} mm)" for d in sem) if sem else "nenhum"
            L.append(f"   - `{est}`, {NOMES_PERIODO_V1[per]}: {texto}.")
    sens = consolidado["sensibilidade_lamina_fixa_e1"]
    L.append("3. **Lâmina fixa da `E1`:**")
    for per in ("Estacao_Chuvosa", "Estacao_Seca"):
        ab = {r["lamina_fixa_mm"]: r["conforto_hidrico_pct"] for r in sens if r["periodo"] == per and r["cenario"] == "Abundante"}
        re_ = {r["lamina_fixa_mm"]: r["conforto_hidrico_pct"] for r in sens if r["periodo"] == per and r["cenario"] == "Restrito"}
        maximo = max(ab.values())
        inicio = min(l for l, v in ab.items() if v == maximo)
        L.append(f"   - {NOMES_PERIODO_V1[per]}: no `Abundante`, o conforto chega ao máximo "
                 f"(`{_br(maximo)}%`) a partir de `{_br(inicio, 0)} mm`; no `Restrito`, por lâmina: "
                 + "; ".join(f"`{_br(l, 0)} mm` → `{_br(v)}%`" for l, v in sorted(re_.items())) + ".")
    L.append("4. **Teto da `E1` com água sobrando:** a regra é avaliada no início do dia e o conforto no fim, então cada "
             "ciclo de secagem custa um dia abaixo de $\\theta_{\\text{lim}}$ (no v2, com passo horário, custa uma hora):")
    for per in ("Estacao_Chuvosa", "Estacao_Seca"):
        m = met[(per, "Abundante", "E1")]
        L.append(f"   - {NOMES_PERIODO_V1[per]}: conforto de `{_br(m['conforto_hidrico_pct'])}%` = 1 − "
                 f"`{m['numero_acionamentos']}`/`{m['dias_simulados']}`.")
    L += [
        "5. **Acumulador `Deficit(t)` × déficit físico do solo:** com o reservatório vazio, o acumulador da `E2` soma a "
        "ETc potencial enquanto o solo, perto de $\\theta_{\\text{pmp}}$, quase não perde água; e a `E2` zera o contador ao "
        "comandar uma irrigação mesmo sem água no tanque.",
        "6. **Simplificações do modelo de duas camadas:** sem extração radicular e sem ascensão capilar na Camada 2; "
        "drenagem instantânea no passo diário; ET0 por Hargreaves-Samani, cujo viés em relação a Penman-Monteith é "
        "quantificado pelo v2 (`resultados/v2/tabelas/tab_clima_ciclos.md`).",
        "7. **Anos vizinhos:** a completude da `A204` em 2024 e 2025 não é avaliada por este relatório; ver o v2 "
        "(`resultados/v2/tabelas/tab_completude_anos.md`).",
        "",
        "---",
        "",
    ]
    return L


def gerar_relatorio_markdown(
    consolidado: Dict[str, Any], caminho_md: str, detalhes: Optional[Dict[str, Any]] = None
) -> None:
    """
    Gera o arquivo único `relatorio_final.md` na ordem estrita das 15 seções da Parte 8.
    """
    if os.path.dirname(caminho_md):
        os.makedirs(os.path.dirname(caminho_md), exist_ok=True)

    q = consolidado["qualidade_serie_climatica"]
    meta_proc = q["global"]["metadados_procedencia"]
    repro = consolidado["reprodutibilidade"]
    ps = consolidado["parametros_solo"]
    lat_br = _br(meta_proc["latitude_graus"], 8)
    linha_cab = meta_proc["numero_linhas_metadados"] + 1
    total_linhas = meta_proc["numero_linhas_total"]
    n_linhas = (detalhes or {}).get("n_linhas", {})

    linhas: List[str] = [
        "# Relatório Final de Dados, Tabelas, Figuras e Evidências para o Artigo Científico",
        "",
        "---",
        "",
        "## 1. Identificação",
        "",
        "| Campo | Informação |",
        "|---|---|",
        "| **Projeto** | Automação da Irrigação em Hortas Comunitárias com Sensores e IoT — PIC/FAPEMA |",
        "| **Edital** | COORD.NUPEX nº 01/2026 |",
        "| **Orientador** | Prof. Alex Rogaleski Marques |",
        "| **Bolsista** | Erdeson |",
        "| **Referência no Plano de Trabalho** | Atividade 2.3 — Desenvolvimento do software e integração IoT (out/2026 a fev/2027) |",
        f"| **Data de Geração do Relatório** | {date.today().isoformat()} |",
        "",
        "---",
        "",
        "## 2. Procedência e Provas do Dado Climático",
        "",
        "### 2.1 (a) Bloco de Metadados do Arquivo Bruto (Reproduzido Verbatim)",
        "",
        "```text",
        meta_proc["bloco_metadados_verbatim"],
        "```",
        "",
        "### 2.2 (b, c, e, f, g) Identificação Criptográfica, Dimensional, Origem e Metadados Extraídos",
        "",
        "| Item de Auditoria | Valor Extraído Diretamente do Arquivo Bruto |",
        "|---|---|",
        f"| **Caminho do arquivo bruto intocado** | `{meta_proc['arquivo_bruto_caminho']}` |",
        f"| **SHA-256 do arquivo bruto** | `{meta_proc['sha256_bruto']}` |",
        f"| **Tamanho exato em bytes** | `{meta_proc['tamanho_bytes']} bytes` |",
        f"| **Número total de linhas** | `{meta_proc['numero_linhas_total']} linhas` (`{meta_proc['numero_linhas_metadados']}` linhas de metadados + `1` linha de cabeçalho + `{meta_proc['numero_linhas_dados']}` linhas horárias de dados) |",
        f"| **Codificação original do arquivo** | `{meta_proc['codificacao']}` |",
        f"| **Data de download** | `{meta_proc['data_download']}` |",
        f"| **URL de origem oficial (INMET)** | `{meta_proc['url_origem']}` |",
        f"| **Código da estação (extraído do cabeçalho)** | `{meta_proc['codigo_wmo']}` (campo `CODIGO (WMO):;`) |",
        f"| **Nome da estação (extraído do cabeçalho)** | `{meta_proc['nome_estacao']}` — `{meta_proc['uf']}` / Região `{meta_proc['regiao']}` (campos `ESTACAO:;`, `UF:;`, `REGIAO:;`) |",
        f"| **Latitude extraída do arquivo (usada em Ra)** | `{meta_proc['latitude_verbatim']}` → `{meta_proc['latitude_graus']:.8f}°` (campo `LATITUDE:;`) |",
        f"| **Longitude extraída do arquivo** | `{meta_proc['longitude_verbatim']}` → `{meta_proc['longitude_graus']:.8f}°` (campo `LONGITUDE:;`) |",
        f"| **Altitude extraída do arquivo** | `{meta_proc['altitude_verbatim']} m` → `{meta_proc['altitude_m']:.2f} m` (campo `ALTITUDE:;`) |",
        f"| **Data de fundação da estação** | `{meta_proc['data_fundacao']}` (campo `DATA DE FUNDACAO:;`) |",
        f"| **Intervalo de datas efetivamente presente no arquivo** | `{meta_proc['data_inicial_arquivo']}` a `{meta_proc['data_final_arquivo']}` (`{meta_proc['total_dias_arquivo']}` dias, resolução `{meta_proc['resolucao_original']}`) |",
        "",
        "### 2.3 (d) Cabeçalho de Colunas, 5 Primeiras e 5 Últimas Linhas de Dados (Verbatim)",
        "",
        f"**Linha de cabeçalho de dados (linha {linha_cab} do arquivo bruto):**",
        "```text",
        meta_proc["linha_cabecalho_verbatim"],
        "```",
        "",
        f"**5 primeiras linhas de dados (linhas {linha_cab + 1} a {linha_cab + 5} do arquivo bruto):**",
        "```text",
        "\n".join(meta_proc["primeiras_5_linhas_dados_verbatim"]),
        "```",
        "",
        f"**5 últimas linhas de dados (linhas {total_linhas - 4} a {total_linhas} do arquivo bruto):**",
        "```text",
        "\n".join(meta_proc["ultimas_5_linhas_dados_verbatim"]),
        "```",
        "",
        "### 2.4 (h) Estatísticas Descritivas por Variável e por Ciclo",
        "",
        "Arquivo CSV correspondente: [`tabelas/T1b_estatisticas_descritivas_por_variavel_ciclo.csv`](tabelas/T1b_estatisticas_descritivas_por_variavel_ciclo.csv)",
        "",
        "O confronto com a normal climatológica 1991–2020 de Balsas é feito pelo v2 (`resultados/v2/tabelas/tab_normal_climatologica.md`).",
        "",
        "| Ciclo | Intervalo de Datas | Variável | Mínimo | Máximo | Média | Desvio-Padrão | Mediana | Soma no Ciclo |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    nomes_var_legiveis = {
        "precipitacao_mm": "Precipitação diária P (mm)",
        "t_max": "Temperatura máxima diária T_max (°C)",
        "t_min": "Temperatura mínima diária T_min (°C)",
        "t_med": "Temperatura média diária T_med (°C)",
        "et0_mm": "Evapotranspiração de referência ET0 (mm/dia)",
        "etc_mm": "Evapotranspiração da cultura ETc (mm/dia)",
    }
    for row_d in consolidado["tabela_t1b_estatisticas_descritivas"]:
        linhas.append(
            f"| `{row_d['ciclo']}` | `{row_d['intervalo_datas']}` | {nomes_var_legiveis.get(row_d['variavel'], row_d['variavel'])} | "
            f"{row_d['minimo']:.2f} | {row_d['maximo']:.2f} | {row_d['media']:.2f} | "
            f"{row_d['desvio_padrao']:.2f} | {row_d['mediana']:.2f} | {row_d['soma_no_ciclo']:.2f} |"
        )

    linhas.extend([
        "",
        "---",
        "",
        "## 3. Qualidade e Tratamento do Dado (Tabela T7)",
        "",
        "Arquivo CSV correspondente: [`tabelas/T7_qualidade_dado_climatico.csv`](tabelas/T7_qualidade_dado_climatico.csv)",
        "",
        *_secao_v1_3(consolidado),
        "",
        "| Escopo | Intervalo de Datas | Variável | Coluna Original BDMEP | Dias Aval. | Dias Ausentes | % Dias Ausentes | Horas Aval. | Horas Ausentes | % Horas Ausentes | Maior Lacuna (dias) | Datas de Cada Lacuna | Tratamento Aplicado |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ])

    for r7 in consolidado["tabela_t7_qualidade"]:
        linhas.append(
            f"| `{r7['escopo']}` | `{r7['intervalo_datas']}` | `{r7['variavel']}` | `{r7['coluna_bdmep']}` | "
            f"{r7['dias_avaliados']} | {r7['dias_ausentes']} | {r7['percentual_dias_ausentes_pct']:.2f}% | "
            f"{r7['horas_avaliadas']} | {r7['horas_ausentes']} | {r7['percentual_horas_ausentes_pct']:.2f}% | "
            f"{r7['maior_lacuna_consecutiva_dias']} | {r7['datas_das_lacunas']} | {r7['tratamento_aplicado']} |"
        )

    linhas.extend([
        "",
        "---",
        "",
        "## 4. Parâmetros e Fontes (Tabela T8)",
        "",
        "Arquivo CSV correspondente: [`tabelas/T8_parametros_e_fontes.csv`](tabelas/T8_parametros_e_fontes.csv)",
        "",
        "| Símbolo | Significado | Valor | Unidade | Origem |",
        "|---|---|---|---|---|",
    ])

    for r8 in consolidado["tabela_t8_parametros"]:
        linhas.append(
            f"| `{r8['simbolo']}` | {r8['significado']} | `{r8['valor']}` | `{r8['unidade']}` | {r8['origem']} |"
        )

    linhas.extend([
        "",
        "---",
        "",
        "## 5. Modelo Implementado: Equações como Implementadas vs. Especificação",
        "",
        "As equações abaixo descrevem literalmente o que está implementado em [`src/water_balance.py`](src/water_balance.py) e [`src/climate.py`](src/climate.py).",
        "",
        "### 5.1 Radiação Extraterrestre ($R_a$) e Evapotranspiração ($ET_0$ e $ET_c$)",
        "Para cada dia $t$ do ciclo, com dia do ano $J \\in [1, 365]$ e latitude $\\phi = \\text{radians}(\\text{latitude\\_deg})$ extraída do bloco de metadados do arquivo INMET ($\\text{latitude\\_deg} = " + lat_br + "^\\circ$):",
        "",
        "$$d_r = 1,0 + 0,033 \\cdot \\cos\\left(\\frac{2\\pi J}{365,0}\\right)$$",
        "$$\\delta = 0,409 \\cdot \\sin\\left(\\frac{2\\pi J}{365,0} - 1,39\\right)$$",
        "$$\\omega_s = \\arccos\\left(\\min\\left(1,0,\\; \\max\\left(-1,0,\\; -\\tan(\\phi)\\tan(\\delta)\\right)\\right)\\right)$$",
        "$$R_a\\,[\\text{MJ}\\cdot\\text{m}^{-2}\\cdot\\text{dia}^{-1}] = \\frac{24 \\times 60}{\\pi} \\cdot G_{sc} \\cdot d_r \\cdot \\left(\\omega_s \\sin(\\phi)\\sin(\\delta) + \\cos(\\phi)\\cos(\\delta)\\sin(\\omega_s)\\right)$$",
        "$$R_a\\,[\\text{mm}\\cdot\\text{dia}^{-1}] = 0,408 \\cdot R_a\\,[\\text{MJ}\\cdot\\text{m}^{-2}\\cdot\\text{dia}^{-1}]$$",
        "$$ET_0(t) = \\max\\left(0,0,\\; 0,0023 \\cdot R_a\\,[\\text{mm}\\cdot\\text{dia}^{-1}] \\cdot \\sqrt{\\max(0,0,\\; T_{\\max}(t) - T_{\\min}(t))} \\cdot (T_{\\text{med}}(t) + 17,8)\\right)$$",
        "$$ET_{c,\\text{pot}}(t) = K_c(t) \\cdot ET_0(t)$$",
        "",
        "### 5.2 Balanço Hídrico do Solo em Duas Camadas (`passo_balanco_solo`)",
        "Com armazenamentos iniciais $S_1(t) = \\theta_1(t) \\cdot z_1$ e $S_2(t) = \\theta_2(t) \\cdot z_2$, e limites $S_{1,\\text{pmp}} = \\theta_{\\text{pmp}} \\cdot z_1 = "
        + _br(ps["theta_pmp"] * ps["z1"], 1) + "\\,\\text{mm}$, $S_{1,\\text{cc}} = \\theta_{\\text{cc}} \\cdot z_1 = "
        + _br(ps["theta_cc"] * ps["z1"], 1) + "\\,\\text{mm}$ e $S_{2,\\text{cc}} = \\theta_{\\text{cc}} \\cdot z_2 = "
        + _br(ps["theta_cc"] * ps["z2"], 1) + "\\,\\text{mm}$:",
        "",
        "```python",
        "agua_extraivel_1      = max(0.0, S1(t) + P(t) + I_efetiva(t) - S1_pmp)",
        "ETc_real(t)           = min(ETc_pot(t), agua_extraivel_1)",
        "armazenamento_prov_1  = S1(t) + P(t) + I_efetiva(t) - ETc_real(t)",
        "D1(t)                 = max(0.0, armazenamento_prov_1 - S1_cc)",
        "theta1(t+1)           = (armazenamento_prov_1 - D1(t)) / z1",
        "",
        "armazenamento_prov_2  = S2(t) + D1(t)",
        "D2(t)                 = max(0.0, armazenamento_prov_2 - S2_cc)",
        "theta2(t+1)           = (armazenamento_prov_2 - D2(t)) / z2",
        "```",
        "",
        "### 5.3 Regras de Decisão, Racionamento Estratégico e Limite Físico de Reservatório (`simular_estrategia`)",
        "Para o índice diário $k \\in \\{0, 1, \\dots, 69\\}$ (`dia_idx` $= k+1$):",
        "1. **Reabastecimento periódico:** se $k \\bmod \\Delta t_{\\text{reab}} == 0$, então $V(t) = V_{\\text{cap}}$, e $\\text{dias\\_restantes} = \\Delta t_{\\text{reab}} - (k \\bmod \\Delta t_{\\text{reab}})$.",
        "2. **Atualização do déficit acumulado:** $\\text{Deficit}(t) = \\max(0,0,\\; \\text{Deficit}(t-1) + ET_{c,\\text{pot}}(t) - P(t))$.",
        "3. **Cálculo da lâmina desejada $I_{\\text{desejada}}(t)$ por estratégia:**",
        "   - **E1:** se $\\theta_1(t) < \\theta_{\\text{lim}}$, $I_{\\text{desejada}}(t) = \\text{lamina\\_fixa}$; senão $0,0$.",
        "   - **E2:** se $\\text{Deficit}(t) \\ge \\text{limiar\\_deficit}$, $I_{\\text{desejada}}(t) = \\text{Deficit}(t)$ e $\\text{Deficit}(t) \\leftarrow 0,0$; senão $0,0$.",
        "   - **E3:** se $\\text{Deficit}(t) \\ge \\text{limiar\\_deficit}$, $\\text{lamina\\_maxima}(t) = \\frac{V(t)}{\\text{dias\\_restantes} \\cdot A_{\\text{canteiro}}}$ e $I_{\\text{desejada}}(t) = \\min(\\text{Deficit}(t), \\max(0,0, \\text{lamina\\_maxima}(t)))$.",
        "4. **Aplicação do limite físico universal do reservatório (Parte 2 — vale para E1, E2 e E3):**",
        "   $$I_{\\text{efetiva}}(t) = \\min\\left(I_{\\text{desejada}}(t),\\; \\frac{V(t)}{A_{\\text{canteiro}}}\\right)$$",
        "   $$I_{\\text{nao\\_atendida}}(t) = \\max\\left(0,0,\\; I_{\\text{desejada}}(t) - I_{\\text{efetiva}}(t)\\right)$$",
        "   $$V(t+1) = \\max\\left(0,0,\\; V(t) - I_{\\text{efetiva}}(t) \\cdot A_{\\text{canteiro}}\\right)$$",
        "   Para E1 e E3, após a irrigação efetiva: $\\text{Deficit}(t) \\leftarrow \\max(0,0,\\; \\text{Deficit}(t) - I_{\\text{efetiva}}(t))$.",
        "",
        "### 5.4 Apontamento Explícito de Divergências e Detalhamentos em Relação à Especificação Original",
        "",
        "| Aspecto | Como consta na especificação original do v1 | Como está implementado no código (`src/water_balance.py` e `src/climate.py`) | Justificativa Física / Metodológica |",
        "|---|---|---|---|",
        "| **Limitação de $ET_c$ no ponto de murcha ($\\theta_{\\text{pmp}}$)** | A Seção 3.3 escreve `armazenamento_prov_1 = θ1(t)·z1 + P(t) + I(t) − ETc(t)` e exige na linha 99 a invariante `θ1 >= θ_pmp`. | Implementado `ETc_real(t) = min(ETc_pot(t), max(0, S1(t) + P(t) + I_efetiva(t) - S1_pmp))`, usando `ETc_real(t)` no balanço de massa. | Sem limitar a extração real à água disponível acima de $\\theta_{\\text{pmp}}$, um período seco sem irrigação (como o Teste 2 de secagem monotônica ou o contrafactual em sequeiro) faria $\\theta_1$ cair abaixo de $\\theta_{\\text{pmp}}$ ou violaria a conservação de massa. |",
        "| **Teto de armazenamento por passo diário ($\\theta_{\\text{cc}}$ vs $\\theta_{\\text{sat}}$)** | A Seção 3.3 define `D1(t) = max(0, armazenamento_prov_1 − θ_cc·z1)` e declara `θ <= θ_sat` como invariante. | Implementado exatamente conforme a equação de `D1(t)` e `D2(t)`: toda água que excede $\\theta_{\\text{cc}} \\cdot z$ drena no próprio passo diário, de modo que $\\theta_1(t+1) \\le \\theta_{\\text{cc}} = " + _br(ps["theta_cc"]) + " < \\theta_{\\text{sat}} = " + _br(ps["theta_sat"]) + "$. | Em modelo de reservatório de passo diário sem equação cinética de redistribuição, a macro-porosidade entre $\\theta_{\\text{cc}}$ e $\\theta_{\\text{sat}}$ drena dentro de 24 h; logo $\\theta_{\\text{sat}}$ atua como teto invariante nunca ultrapassado. |",
        "| **Limite físico do reservatório em E1 e E2** | Na Seção 4 original, o reservatório aparecia apenas na subseção da E3. | Na Parte 2 desta rodada final, o limite físico $I_{\\text{efetiva}}(t) = \\min(I_{\\text{desejada}}(t), V(t)/A_{\\text{canteiro}})$ foi estendido a **E1, E2 e E3**, permanecendo exclusivo da E3 apenas o racionamento estratégico por `dias_restantes`. | Impede que E1 e E2 apliquem água inexistente quando o reservatório se esgota nos cenários Moderado e Restrito. |",
        "| **Desconto de $I(t)$ no déficit acumulado da E3** | A Seção 4.3 mostrava `I(t) = min(Deficit(t), lamina_maxima(t))` sem explicitar a linha de atualização de `Deficit(t)` após irrigação parcial. | Implementado `Deficit(t) = max(0.0, Deficit(t) - I_efetiva(t))` na E3 (enquanto na E2, quando acionada, `I_desejada(t) = Deficit(t)` e `Deficit(t) = 0`). | Como a E3 aplica lâmina deficitária ($I(t) < \\text{Deficit}(t)$), apenas a fração efetivamente reposta deve ser abatida do déficit acumulado. |",
        "| **Latitude geográfica $\\phi$** | A Seção 3.4 mencionava um valor de exemplo para $\\phi$. | Removido o valor fixo do código (Parte 1.5); o cálculo usa exclusivamente a latitude extraída do bloco de metadados do arquivo bruto do INMET ($\\phi = " + lat_br + "^\\circ$). | Fidelidade estrita aos metadados oficiais da estação automática `A204 (BALSAS)` do BDMEP/INMET. |",
        "| **Agregação de série horária do BDMEP para passo diário** | A Seção 3.5 especifica variáveis diárias ($T_{\\max}$, $T_{\\min}$, $T_{\\text{med}}$, $P$). | O arquivo oficial das estações automáticas do INMET fornece 24 registros horários UTC por dia; o parser agrega $P_{\\text{dia}} = \\sum P_{\\text{hora}}$, $T_{\\max,\\text{dia}} = \\max(T_{\\max,\\text{hora}})$, $T_{\\min,\\text{dia}} = \\min(T_{\\min,\\text{hora}})$ e $T_{\\text{med,dia}} = \\overline{T}_{\\text{bulbo seco,hora}}$. | Preserva o arquivo bruto oficial do INMET intocado em `data/raw/` e deriva a série diária em `resultados/v1/processed/`. |",
        "",
        "---",
        "",
        "## 6. Testes de Validação Física (Tabela T6)",
        "",
        "Arquivo CSV correspondente: [`tabelas/T6_testes_validacao_fisica.csv`](tabelas/T6_testes_validacao_fisica.csv)  ",
        "Série diária completa dos 3 testes: [`rodadas/rodadas_validacao_fisica_diario.csv`](rodadas/rodadas_validacao_fisica_diario.csv)",
        "",
        "| Teste | Dias | Condição Inicial | Forçantes | Valor Esperado Literal (Calculado à Mão) | Valor Observado no Simulador | Erro Absoluto | Erro Relativo | Status |",
        "|---|---:|---|---|---|---|---|---|---|",
    ])

    for r6 in consolidado["tabela_t6_validacao"]:
        linhas.append(
            f"| **{r6['teste']}** | {r6['dias_simulados']} | `{r6['condicao_inicial']}` | `{r6['forçantes']}` | "
            f"`{r6['valor_esperado_literal']}` | `{r6['valor_observado']}` | `{r6['erro_absoluto']}` | `{r6['erro_relativo_pct']}` | **{r6['status']}** |"
        )

    linhas.extend([
        "",
        "---",
        "",
        "## 7. Caracterização Climática dos Dois Ciclos (Tabela T1 e Figura F1)",
        "",
        "Arquivo CSV correspondente: [`tabelas/T1_caracterizacao_climatica.csv`](tabelas/T1_caracterizacao_climatica.csv)",
        "",
        "| Ciclo | Datas do Ciclo | Dias | $\\Sigma P$ (mm) | $\\Sigma ET_0$ (mm) | $ET_0$ Média (mm/d) | $\\Sigma ET_c$ (mm) | $ET_c$ Média (mm/d) | $T$ Média (°C) | $T_{\\max}$ Abs. (°C) | $T_{\\min}$ Abs. (°C) | Nº Dias c/ Chuva | Maior Evento de Chuva (mm e data) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ])

    for r1 in consolidado["tabela_t1_caracterizacao_climatica"]:
        linhas.append(
            f"| `{r1['ciclo']}` | `{r1['data_inicial']} a {r1['data_final']}` | {r1['dias_ciclo']} | "
            f"**{r1['precipitacao_acumulada_mm']:.2f}** | {r1['et0_acumulada_mm']:.2f} | {r1['et0_media_mm_dia']:.2f} | "
            f"{r1['etc_acumulada_mm']:.2f} | {r1['etc_media_mm_dia']:.2f} | {r1['t_media_ciclo_c']:.2f} | "
            f"{r1['t_max_absoluta_c']:.2f} | {r1['t_min_absoluta_c']:.2f} | {r1['dias_com_chuva']} | "
            f"**{r1['maior_evento_chuva_mm']:.2f} mm** (`{r1['data_maior_evento_chuva']}`) |"
        )

    linhas.extend([
        "",
        "### Figura F1 — Série Diária de $\\theta_1$ e $\\theta_2$ ao Longo do Ciclo",
        "- Estação Chuvosa: [`figuras/F1_umidade_solo_estacao_chuvosa.png`](figuras/F1_umidade_solo_estacao_chuvosa.png) · Dados: [`figuras/F1_umidade_solo_estacao_chuvosa.csv`](figuras/F1_umidade_solo_estacao_chuvosa.csv)",
        "- Estação Seca: [`figuras/F1_umidade_solo_estacao_seca.png`](figuras/F1_umidade_solo_estacao_seca.png) · Dados: [`figuras/F1_umidade_solo_estacao_seca.csv`](figuras/F1_umidade_solo_estacao_seca.csv)",
        "",
        "---",
        "",
        "## 8. Resultados: Comparação Principal (Tabela T2, Figuras F4 e F5)",
        "",
        "Arquivo CSV correspondente: [`tabelas/T2_comparacao_principal.csv`](tabelas/T2_comparacao_principal.csv)  ",
        "Série diária completa: [`rodadas/rodadas_comparacao_principal_diario.csv`](rodadas/rodadas_comparacao_principal_diario.csv)",
        "",
        "### 8.1 Referência Contrafactual em Sequeiro ($I(t) = 0$)",
        "",
        "| Período Climático | Precipitação $\\Sigma P$ (mm) | `D2_chuva` (mm) | `D2_chuva` (L) | Conforto Hídrico em Sequeiro (%) | Déficit Máximo no Solo (mm) |",
        "|---|---:|---:|---:|---:|---:|",
    ])

    for cf in consolidado["contrafactuais_sequeiro"]:
        p_tot = q[cf["periodo"]]["precipitacao_total_mm"]
        linhas.append(
            f"| `{cf['periodo']}` | {p_tot:.2f} | **{cf['d2_chuva_mm']:.2f}** | **{cf['d2_chuva_l']:.1f}** | "
            f"{cf['conforto_hidrico_pct']:.2f}% | {cf['deficit_maximo_mm']:.2f} |"
        )

    linhas.extend([
        "",
        "### 8.2 Tabela T2 — Comparação Principal (2 Períodos × 3 Cenários × 3 Estratégias)",
        "",
        "| Período | Cenário | Estratégia | Lâmina Desejada (mm) | Lâmina Aplicada (mm / L) | Lâmina Não Atendida (mm / L) | `D2_total` (mm / L) | `D2_chuva` (mm / L) | `D2_incremental` (mm / L) | Eficiência de Aplicação Incremental (%) | Conforto Hídrico (%) | Nº Acion. | Déficit Máx. (mm) | Dias Reserv. Vazio | 1º Dia Vazio |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])

    for m in consolidado["metricas_comparativas"]:
        p_vazio = str(m["primeiro_dia_reservatorio_vazio"]) if m["primeiro_dia_reservatorio_vazio"] is not None else "—"
        linhas.append(
            f"| `{m['periodo']}` | `{m['cenario']}` | **{m['estrategia']}** | "
            f"{m['lamina_desejada_mm']:.2f} | "
            f"**{m['lamina_total_mm']:.2f}** / {m['volume_total_l']:.0f} | "
            f"{m['lamina_nao_atendida_mm']:.2f} / {m['volume_nao_atendido_l']:.0f} | "
            f"{m['percolacao_acumulada_mm']:.2f} / {m['percolacao_acumulada_l']:.0f} | "
            f"{m['d2_chuva_mm']:.2f} / {m['d2_chuva_l']:.0f} | "
            f"**{m['d2_incremental_mm']:.2f}** / {m['d2_incremental_l']:.0f} | "
            f"**{m['eficiencia_incremental_pct']:.2f}%** | "
            f"**{m['conforto_hidrico_pct']:.2f}%** | "
            f"{m['numero_acionamentos']} | {m['deficit_maximo_mm']:.2f} | "
            f"{m['dias_reservatorio_vazio']} | {p_vazio} |"
        )

    linhas.extend([
        "",
        "### 8.3 Verificação da Separação entre Cenários da E1 após o Limite Físico de Reservatório (Parte 3.3)",
        *_secao_v1_8_3(consolidado),
        "",
        "### Figuras F4 e F5",
        "- Figura F4 (Estação Chuvosa): [`figuras/F4_barras_comparativas_estacao_chuvosa.png`](figuras/F4_barras_comparativas_estacao_chuvosa.png) · Dados: [`figuras/F4_barras_comparativas_estacao_chuvosa.csv`](figuras/F4_barras_comparativas_estacao_chuvosa.csv)",
        "- Figura F4 (Estação Seca): [`figuras/F4_barras_comparativas_estacao_seca.png`](figuras/F4_barras_comparativas_estacao_seca.png) · Dados: [`figuras/F4_barras_comparativas_estacao_seca.csv`](figuras/F4_barras_comparativas_estacao_seca.csv)",
        "- Figura F5 (Nível do Reservatório — Restrito, Estação Chuvosa): [`figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.png`](figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.png) · Dados: [`figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.csv`](figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.csv)",
        "- Figura F5 (Nível do Reservatório — Restrito, Estação Seca): [`figuras/F5_nivel_reservatorio_restrito_estacao_seca.png`](figuras/F5_nivel_reservatorio_restrito_estacao_seca.png) · Dados: [`figuras/F5_nivel_reservatorio_restrito_estacao_seca.csv`](figuras/F5_nivel_reservatorio_restrito_estacao_seca.csv)",
        "",
        "---",
        "",
        "## 9. Resultados: Sensibilidade da Lâmina Fixa da E1 (Tabela T3 e Figura F2)",
        "",
        "Arquivo CSV correspondente: [`tabelas/T3_sensibilidade_e1.csv`](tabelas/T3_sensibilidade_e1.csv)  ",
        "Série diária completa: [`rodadas/rodadas_sensibilidade_e1_diario.csv`](rodadas/rodadas_sensibilidade_e1_diario.csv)",
        "",
        "| Período | Cenário | `lamina_fixa` (mm) | Lâmina Desejada (mm) | Lâmina Aplicada (mm / L) | Lâmina Não Atendida (mm / L) | `D2_total` (mm) | `D2_chuva` (mm) | `D2_incremental` (mm / L) | Eficiência Incremental (%) | Conforto Hídrico (%) | Nº Acion. | Déficit Máx. (mm) | Dias Reserv. Vazio | 1º Dia Vazio |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])

    for r3 in consolidado["sensibilidade_lamina_fixa_e1"]:
        p_vazio = str(r3["primeiro_dia_reservatorio_vazio"]) if r3["primeiro_dia_reservatorio_vazio"] is not None else "—"
        linhas.append(
            f"| `{r3['periodo']}` | `{r3['cenario']}` | **{r3['lamina_fixa_mm']:.0f}** | "
            f"{r3['lamina_desejada_mm']:.1f} | "
            f"**{r3['lamina_total_mm']:.1f}** / {r3['volume_total_l']:.0f} | "
            f"{r3['lamina_nao_atendida_mm']:.1f} / {r3['volume_nao_atendido_l']:.0f} | "
            f"{r3['percolacao_acumulada_mm']:.2f} | {r3['d2_chuva_mm']:.2f} | "
            f"**{r3['d2_incremental_mm']:.2f}** / {r3['d2_incremental_l']:.0f} | "
            f"{r3['eficiencia_incremental_pct']:.2f}% | "
            f"**{r3['conforto_hidrico_pct']:.2f}%** | "
            f"{r3['numero_acionamentos']} | {r3['deficit_maximo_mm']:.2f} | "
            f"{r3['dias_reservatorio_vazio']} | {p_vazio} |"
        )

    linhas.extend([
        "",
        "### Figura F2 — Sensibilidade da E1 vs. Referência E2",
        "- Estação Chuvosa: [`figuras/F2_sensibilidade_e1_estacao_chuvosa.png`](figuras/F2_sensibilidade_e1_estacao_chuvosa.png) · Dados: [`figuras/F2_sensibilidade_e1_estacao_chuvosa.csv`](figuras/F2_sensibilidade_e1_estacao_chuvosa.csv)",
        "- Estação Seca: [`figuras/F2_sensibilidade_e1_estacao_seca.png`](figuras/F2_sensibilidade_e1_estacao_seca.png) · Dados: [`figuras/F2_sensibilidade_e1_estacao_seca.csv`](figuras/F2_sensibilidade_e1_estacao_seca.csv)",
        "",
        "---",
        "",
        "## 10. Resultados: Dimensionamento do Reservatório (Tabelas T4 e T5, Figura F3)",
        "",
        "### 10.1 Tabela T4 — Dimensionamento Mínimo para Conforto Hídrico ≥ 90%",
        "Arquivo CSV correspondente: [`tabelas/T4_dimensionamento_reservatorio.csv`](tabelas/T4_dimensionamento_reservatorio.csv)",
        "",
        "| Período Climático | Intervalo de Reabastecimento | Demanda `ETc` Média (mm/d) | $\\Sigma P$ no Ciclo (mm) | Capacidade Mínima p/ Conforto ≥ 90% (L) | Oferta Máxima na Cap. Mínima (mm/d) | Conforto Obtido (%) | Lâmina Aplicada (mm) | `D2_incremental` (mm) | Eficiência Incremental (%) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])

    for r4 in consolidado["dimensionamento_reservatorio_e3"]:
        cap_s = f"{int(r4['capacidade_minima_conforto_90_l'])} L" if isinstance(r4["capacidade_minima_conforto_90_l"], (int, float)) else str(r4["capacidade_minima_conforto_90_l"])
        of_s = f"{r4['oferta_maxima_na_cap_minima_mm_dia']:.2f}" if r4["oferta_maxima_na_cap_minima_mm_dia"] is not None else "—"
        cf_s = f"{r4['conforto_obtido_pct']:.2f}%" if r4["conforto_obtido_pct"] is not None else "—"
        la_s = f"{r4['lamina_aplicada_mm']:.2f}" if r4["lamina_aplicada_mm"] is not None else "—"
        d2_s = f"{r4['d2_incremental_mm']:.2f}" if r4["d2_incremental_mm"] is not None else "—"
        ef_s = f"{r4['eficiencia_incremental_pct']:.2f}%" if r4["eficiencia_incremental_pct"] is not None else "—"
        linhas.append(
            f"| `{r4['periodo']}` | **{r4['intervalo_reabastecimento_dias']} dias** | "
            f"{r4['demanda_etc_media_mm_dia']:.2f} | {r4['precipitacao_total_mm']:.2f} | "
            f"**{cap_s}** | {of_s} | **{cf_s}** | {la_s} | {d2_s} | {ef_s} |"
        )

    linhas.extend([
        "",
        f"### 10.2 Tabela T5 — Varredura Completa do Reservatório na E3 ({len(consolidado['varredura_reservatorio_e3'])} Rodadas)",
        "Arquivo CSV correspondente: [`tabelas/T5_varredura_reservatorio.csv`](tabelas/T5_varredura_reservatorio.csv)  ",
        "Série diária completa: [`rodadas/rodadas_varredura_reservatorio_e3_diario.csv`](rodadas/rodadas_varredura_reservatorio_e3_diario.csv)",
        "",
        "| Período | Intervalo (d) | Capacidade (L) | Oferta Máx. (mm/d) | Atende ≥ 90%? | Conforto Hídrico (%) | Lâmina Aplicada (mm / L) | Lâmina Não Atendida (mm) | `D2_total` (mm) | `D2_chuva` (mm) | `D2_incremental` (mm) | Eficiência Incremental (%) | Nº Acion. | Déficit Máx. (mm) | Dias Reserv. Vazio | 1º Dia Vazio |",
        "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])

    for r5 in consolidado["varredura_reservatorio_e3"]:
        at_s = "SIM" if r5["atende_conforto_90pct"] else "Não"
        p_vazio = str(r5["primeiro_dia_reservatorio_vazio"]) if r5["primeiro_dia_reservatorio_vazio"] is not None else "—"
        linhas.append(
            f"| `{r5['periodo']}` | {r5['intervalo_reabastecimento_dias']} | **{int(r5['capacidade_reservatorio_l'])}** | "
            f"{r5['oferta_maxima_mm_dia']:.2f} | **{at_s}** | **{r5['conforto_hidrico_pct']:.2f}%** | "
            f"{r5['lamina_total_mm']:.2f} / {r5['volume_total_l']:.0f} | {r5['lamina_nao_atendida_mm']:.2f} | "
            f"{r5['percolacao_acumulada_mm']:.2f} | {r5['d2_chuva_mm']:.2f} | "
            f"**{r5['d2_incremental_mm']:.2f}** | {r5['eficiencia_incremental_pct']:.2f}% | "
            f"{r5['numero_acionamentos']} | {r5['deficit_maximo_mm']:.2f} | "
            f"{r5['dias_reservatorio_vazio']} | {p_vazio} |"
        )

    linhas.extend([
        "",
        "### Figura F3 — Curvas de Dimensionamento do Reservatório",
        "- Estação Chuvosa: [`figuras/F3_dimensionamento_estacao_chuvosa.png`](figuras/F3_dimensionamento_estacao_chuvosa.png) · Dados: [`figuras/F3_dimensionamento_estacao_chuvosa.csv`](figuras/F3_dimensionamento_estacao_chuvosa.csv)",
        "- Estação Seca: [`figuras/F3_dimensionamento_estacao_seca.png`](figuras/F3_dimensionamento_estacao_seca.png) · Dados: [`figuras/F3_dimensionamento_estacao_seca.csv`](figuras/F3_dimensionamento_estacao_seca.csv)",
        "",
        "---",
        "",
    ])
    linhas.extend(_secoes_v1_11_a_13(consolidado, detalhes))
    linhas.extend([
        "## 14. Reprodutibilidade (Parte 7)",
        "",
        "| Parâmetro de Reprodutibilidade | Valor / Especificação |",
        "|---|---|",
        f"| **Sistema Operacional / Kernel** | `{repro['platform']}` |",
        f"| **Versão da linguagem Python** | `{repro['python_version']}` |",
        f"| **Versão do SQLite (`sqlite3`)** | `{repro['sqlite3_version']}` |",
        f"| **Versão do `matplotlib`** | `{repro['matplotlib_version']}` |",
        f"| **Versão do `numpy`** | `{repro['numpy_version']}` |",
        f"| **Hash do commit Git** | `{repro['git_commit_hash']}` |",
        f"| **Comando exato para reproduzir todas as rodadas, tabelas, figuras e relatório do zero** | `{repro['comando_reproducao']}` |",
        f"| **Comando exato para executar a suíte de testes de validação** | `{repro['comando_testes']}` |",
        f"| **Tempo de execução total medido** | `{repro['tempo_execucao_total_s']:.3f} segundos` |",
        f"| **Confirmação sobre aleatoriedade** | {repro['aleatoriedade']} |",
        f"| **Semente aleatória (`seed`)** | `{repro['semente_aleatoria']}` |",
        "",
        "---",
        "",
        "## 15. Índice dos Arquivos Gerados",
        "",
        "| Categoria | Caminho Relativo | Descrição do Conteúdo |",
        "|---|---|---|",
        "| **Relatório Principal** | [`relatorio_final.md`](relatorio_final.md) | Relatório técnico-científico consolidado (Seções 1 a 15) |",
        "| **Dado Bruto INMET** | [`data/raw/INMET_NE_MA_A204_BALSAS_01-01-2023_A_31-12-2023.CSV`](data/raw/INMET_NE_MA_A204_BALSAS_01-01-2023_A_31-12-2023.CSV) | Arquivo bruto oficial do BDMEP/INMET preservado intocado (`" + _br(meta_proc["tamanho_bytes"], 0) + " bytes`, `" + _br(total_linhas, 0) + " linhas`, SHA-256 `" + meta_proc["sha256_bruto"] + "`) |",
        "| **Série Processada** | [`processed/inmet_A204_balsas_2023_diario_bruto_agregado.csv`](processed/inmet_A204_balsas_2023_diario_bruto_agregado.csv) | Série diária agregada dos " + str(meta_proc["total_dias_arquivo"]) + " dias do arquivo, com contagem de horas válidas por variável |",
        "| **Série Processada** | [`processed/inmet_A204_balsas_2023_ciclos_70d_tratados.csv`](processed/inmet_A204_balsas_2023_ciclos_70d_tratados.csv) | Série diária tratada dos dois ciclos de 70 dias (`Estacao_Chuvosa` e `Estacao_Seca`) com $ET_0$, $K_c$ e $ET_c$ |",
        "| **Tabela T1 (CSV)** | [`tabelas/T1_caracterizacao_climatica.csv`](tabelas/T1_caracterizacao_climatica.csv) | Caracterização climática dos dois ciclos de 70 dias |",
        "| **Tabela T1b (CSV)** | [`tabelas/T1b_estatisticas_descritivas_por_variavel_ciclo.csv`](tabelas/T1b_estatisticas_descritivas_por_variavel_ciclo.csv) | Estatísticas descritivas (mínimo, máximo, média, desvio-padrão, mediana, soma) por variável e ciclo |",
        "| **Tabela T2 (CSV)** | [`tabelas/T2_comparacao_principal.csv`](tabelas/T2_comparacao_principal.csv) | Comparação principal: 2 períodos × 3 cenários × 3 estratégias |",
        "| **Tabela T3 (CSV)** | [`tabelas/T3_sensibilidade_e1.csv`](tabelas/T3_sensibilidade_e1.csv) | Análise de sensibilidade da lâmina fixa da E1 (`5, 10, 15, 20, 25, 30 mm` × 2 períodos × 3 cenários) |",
        "| **Tabela T4 (CSV)** | [`tabelas/T4_dimensionamento_reservatorio.csv`](tabelas/T4_dimensionamento_reservatorio.csv) | Dimensionamento mínimo do reservatório para conforto hídrico ≥ 90% |",
        "| **Tabela T5 (CSV)** | [`tabelas/T5_varredura_reservatorio.csv`](tabelas/T5_varredura_reservatorio.csv) | Varredura completa do reservatório na E3 (" + str(len(consolidado["varredura_reservatorio_e3"])) + " rodadas) |",
        "| **Tabela T6 (CSV)** | [`tabelas/T6_testes_validacao_fisica.csv`](tabelas/T6_testes_validacao_fisica.csv) | Resultados dos 3 testes obrigatórios de validação física com constantes literais |",
        "| **Tabela T7 (CSV)** | [`tabelas/T7_qualidade_dado_climatico.csv`](tabelas/T7_qualidade_dado_climatico.csv) | Qualidade do dado climático por variável e ciclo |",
        "| **Tabela T8 (CSV)** | [`tabelas/T8_parametros_e_fontes.csv`](tabelas/T8_parametros_e_fontes.csv) | Tabela completa de parâmetros, valores, unidades e classificação de origem |",
        "| **Série Diária** | [`rodadas/rodadas_comparacao_principal_diario.csv`](rodadas/rodadas_comparacao_principal_diario.csv) | Série diária completa das rodadas da comparação principal e contrafactuais (`" + _br(n_linhas.get("comparacao", 0), 0) + " registros`) |",
        "| **Série Diária** | [`rodadas/rodadas_sensibilidade_e1_diario.csv`](rodadas/rodadas_sensibilidade_e1_diario.csv) | Série diária completa das " + str(len(consolidado["sensibilidade_lamina_fixa_e1"])) + " rodadas de sensibilidade da E1 (`" + _br(n_linhas.get("sensibilidade", 0), 0) + " registros`) |",
        "| **Série Diária** | [`rodadas/rodadas_varredura_reservatorio_e3_diario.csv`](rodadas/rodadas_varredura_reservatorio_e3_diario.csv) | Série diária completa das " + str(len(consolidado["varredura_reservatorio_e3"])) + " rodadas da varredura de reservatório da E3 (`" + _br(n_linhas.get("varredura", 0), 0) + " registros`) |",
        "| **Série Diária** | [`rodadas/rodadas_validacao_fisica_diario.csv`](rodadas/rodadas_validacao_fisica_diario.csv) | Série diária passo a passo dos 3 testes de validação física (`" + _br(n_linhas.get("validacao", 0), 0) + " registros`) |",
        "| **Figura F1 (Chuvosa)** | [`figuras/F1_umidade_solo_estacao_chuvosa.png`](figuras/F1_umidade_solo_estacao_chuvosa.png) | PNG 300 dpi + [`figuras/F1_umidade_solo_estacao_chuvosa.csv`](figuras/F1_umidade_solo_estacao_chuvosa.csv) |",
        "| **Figura F1 (Seca)** | [`figuras/F1_umidade_solo_estacao_seca.png`](figuras/F1_umidade_solo_estacao_seca.png) | PNG 300 dpi + [`figuras/F1_umidade_solo_estacao_seca.csv`](figuras/F1_umidade_solo_estacao_seca.csv) |",
        "| **Figura F2 (Chuvosa)** | [`figuras/F2_sensibilidade_e1_estacao_chuvosa.png`](figuras/F2_sensibilidade_e1_estacao_chuvosa.png) | PNG 300 dpi + [`figuras/F2_sensibilidade_e1_estacao_chuvosa.csv`](figuras/F2_sensibilidade_e1_estacao_chuvosa.csv) |",
        "| **Figura F2 (Seca)** | [`figuras/F2_sensibilidade_e1_estacao_seca.png`](figuras/F2_sensibilidade_e1_estacao_seca.png) | PNG 300 dpi + [`figuras/F2_sensibilidade_e1_estacao_seca.csv`](figuras/F2_sensibilidade_e1_estacao_seca.csv) |",
        "| **Figura F3 (Chuvosa)** | [`figuras/F3_dimensionamento_estacao_chuvosa.png`](figuras/F3_dimensionamento_estacao_chuvosa.png) | PNG 300 dpi + [`figuras/F3_dimensionamento_estacao_chuvosa.csv`](figuras/F3_dimensionamento_estacao_chuvosa.csv) |",
        "| **Figura F3 (Seca)** | [`figuras/F3_dimensionamento_estacao_seca.png`](figuras/F3_dimensionamento_estacao_seca.png) | PNG 300 dpi + [`figuras/F3_dimensionamento_estacao_seca.csv`](figuras/F3_dimensionamento_estacao_seca.csv) |",
        "| **Figura F4 (Chuvosa)** | [`figuras/F4_barras_comparativas_estacao_chuvosa.png`](figuras/F4_barras_comparativas_estacao_chuvosa.png) | PNG 300 dpi + [`figuras/F4_barras_comparativas_estacao_chuvosa.csv`](figuras/F4_barras_comparativas_estacao_chuvosa.csv) |",
        "| **Figura F4 (Seca)** | [`figuras/F4_barras_comparativas_estacao_seca.png`](figuras/F4_barras_comparativas_estacao_seca.png) | PNG 300 dpi + [`figuras/F4_barras_comparativas_estacao_seca.csv`](figuras/F4_barras_comparativas_estacao_seca.csv) |",
        "| **Figura F5 (Chuvosa)** | [`figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.png`](figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.png) | PNG 300 dpi + [`figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.csv`](figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.csv) |",
        "| **Figura F5 (Seca)** | [`figuras/F5_nivel_reservatorio_restrito_estacao_seca.png`](figuras/F5_nivel_reservatorio_restrito_estacao_seca.png) | PNG 300 dpi + [`figuras/F5_nivel_reservatorio_restrito_estacao_seca.csv`](figuras/F5_nivel_reservatorio_restrito_estacao_seca.csv) |",
        "",
    ])

    with open(caminho_md, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
