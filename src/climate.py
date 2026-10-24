"""
Parser e pipeline de tratamento para arquivos reais do BDMEP/INMET (Seção 3.5 e Parte 1).

Regras estritas implementadas:
  1. Proibida qualquer geração, estimação sintética ou fabricação de dados climáticos.
     Se o arquivo bruto real não existir ou não cobrir integralmente os períodos solicitados,
     levanta erro explícito (FileNotFoundError / ValueError) e interrompe a execução.
  2. Faz o parsing do formato oficial do BDMEP/INMET:
     - Bloco de metadados no início (antes do cabeçalho de dados), reproduzido verbatim
       e parseado dinamicamente para extrair código, nome, latitude, longitude e altitude.
     - Separador ';' e vírgula ',' como separador decimal.
     - Valores ausentes representados como campo vazio '' ou '-9999'.
     - Nomes de coluna em português com unidade embutida.
  3. Preserva o arquivo bruto intocado em `data/raw/` e grava as séries processadas
     exclusivamente em `data/processed/`.
  4. Calcula Ra e ET0 utilizando exclusivamente a latitude extraída do bloco de metadados
     do próprio arquivo bruto do INMET.
"""

from __future__ import annotations
import csv
from datetime import date, timedelta
import hashlib
import os
import statistics
from typing import List, Dict, Any, Tuple, Optional

from src.water_balance import ClimateDay, calcular_et0_hargreaves_samani


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_RAW_INMET_CSV = os.path.join(
    ROOT_DIR, "data", "raw", "INMET_NE_MA_A204_BALSAS_01-01-2023_A_31-12-2023.CSV"
)
DEFAULT_PROCESSED_DIR = os.path.join(ROOT_DIR, "data", "processed")

CICLOS_PADRAO = {
    "Estacao_Chuvosa": ("2023-01-15", "2023-03-25"),  # 70 dias
    "Estacao_Seca": ("2023-07-01", "2023-09-08"),     # 70 dias
}

URL_ORIGEM_BDMEP_2023 = (
    "https://portal.inmet.gov.br/uploads/dadoshistoricos/2023.zip "
    "(entrada: INMET_NE_MA_A204_BALSAS_01-01-2023_A_31-12-2023.CSV)"
)
DATA_DOWNLOAD_ARQUIVO = "2026-10-17"


def kc_hortalica_folhosa(dia_ciclo: int, usar_kc_fases: bool = True) -> float:
    """
    Coeficiente de cultura Kc por fase do ciclo de 70 dias para hortaliça folhosa (Seção 3.4):
      - Fase inicial (dias 1 a 15): 0,70
      - Fase intermediária (dias 16 a 55): 1,00
      - Fase final (dias 56 a 70+): 0,95
    Caso `usar_kc_fases=False`, retorna Kc = 1,0 constante.
    """
    if not usar_kc_fases:
        return 1.0
    if dia_ciclo <= 15:
        return 0.70
    if dia_ciclo <= 55:
        return 1.00
    return 0.95


def _parse_valor_bdmep(texto: Optional[str]) -> Optional[float]:
    """
    Converte string numérica do formato BDMEP (vírgula decimal, ex.: '25,7' ou ',9')
    para float. Retorna None se o campo for vazio ou código de ausente (-9999).
    """
    if texto is None:
        return None
    s = texto.strip()
    if s == "" or s in ("-9999", "-9999,0", "-9999.0", "-9999,00"):
        return None
    s_norm = s.replace(",", ".")
    if s_norm.startswith("."):
        s_norm = "0" + s_norm
    elif s_norm.startswith("-."):
        s_norm = "-0" + s_norm[1:]
    try:
        val = float(s_norm)
    except ValueError as exc:
        raise ValueError(f"Valor numérico inválido no arquivo BDMEP: {texto!r}") from exc
    if val <= -9990.0:
        return None
    return val


def _normalizar_data_bdmep(texto_data: str) -> str:
    """Converte data do BDMEP ('YYYY/MM/DD' ou 'YYYY-MM-DD') para ISO 'YYYY-MM-DD'."""
    s = texto_data.strip().replace("/", "-")
    # Valida formato ISO
    _ = date.fromisoformat(s)
    return s


def _identificar_colunas_bdmep(cabecalho: List[str]) -> Dict[str, int]:
    """
    Localiza os índices das colunas no cabeçalho em português com unidade embutida do BDMEP.
    Suporta tanto o formato horário oficial das estações automáticas quanto o diário.
    """
    mapa: Dict[str, int] = {}
    for idx, col in enumerate(cabecalho):
        c_up = col.strip().upper()
        if not c_up:
            continue
        if c_up in ("DATA", "DATA MEDICAO", "DATA MEDIÇÃO"):
            mapa["data"] = idx
        elif c_up.startswith("HORA"):
            mapa["hora"] = idx
        elif "PRECIPITA" in c_up and "(MM)" in c_up:
            mapa["precipitacao_mm"] = idx
        elif "TEMPERATURA" in c_up and "ORVALHO" not in c_up:
            if "BULBO SECO" in c_up or "MEDIA" in c_up or "MÉDIA" in c_up:
                mapa["t_med"] = idx
            elif "MÁXIMA" in c_up or "MAXIMA" in c_up or "MAX." in c_up:
                mapa["t_max"] = idx
            elif "MÍNIMA" in c_up or "MINIMA" in c_up or "MIN." in c_up:
                mapa["t_min"] = idx

    obrigatorias = ("data", "precipitacao_mm", "t_max", "t_min", "t_med")
    faltando = [k for k in obrigatorias if k not in mapa]
    if faltando:
        raise ValueError(
            f"Cabeçalho BDMEP não contém todas as colunas obrigatórias ({faltando}). "
            f"Cabeçalho lido: {cabecalho}"
        )
    return mapa


def ler_arquivo_bruto_bdmep(caminho_csv_bruto: str) -> Dict[str, Any]:
    """
    Lê e faz o parsing de um arquivo bruto oficial do BDMEP/INMET sem modificá-lo.
    Extrai:
      - Bloco de metadados verbatim e campos estruturados (código, nome, latitude, longitude, altitude)
      - SHA-256, tamanho em bytes e número total de linhas
      - As 5 primeiras e 5 últimas linhas de dados verbatim
      - Registros agregados por dia e estatísticas de ausentes horários e diários
    """
    if not os.path.exists(caminho_csv_bruto):
        raise FileNotFoundError(
            f"ERRO EXPLÍCITO: Arquivo climático real do INMET não encontrado em '{caminho_csv_bruto}'. "
            "A geração ou síntese de dados climáticos é estritamente proibida."
        )

    with open(caminho_csv_bruto, "rb") as fb:
        raw_bytes = fb.read()

    tamanho_bytes = len(raw_bytes)
    sha256_hex = hashlib.sha256(raw_bytes).hexdigest()

    # Arquivos oficiais do BDMEP/INMET utilizam codificação ISO-8859-1 (latin1) ou UTF-8
    try:
        texto = raw_bytes.decode("utf-8")
        codificacao_detectada = "utf-8"
    except UnicodeDecodeError:
        texto = raw_bytes.decode("latin1")
        codificacao_detectada = "iso-8859-1 (latin1)"

    linhas_brutas = texto.splitlines()
    numero_linhas_total = len(linhas_brutas)
    if numero_linhas_total < 10:
        raise ValueError(
            f"Arquivo BDMEP inválido ou truncado ({numero_linhas_total} linhas): {caminho_csv_bruto}"
        )

    linhas_metadados_verbatim: List[str] = []
    metadados_dict: Dict[str, str] = {}
    idx_cabecalho: Optional[int] = None

    for idx, linha in enumerate(linhas_brutas):
        partes = linha.split(";")
        primeiro = partes[0].strip().upper()
        if primeiro in ("DATA", "DATA MEDICAO", "DATA MEDIÇÃO"):
            idx_cabecalho = idx
            break
        linhas_metadados_verbatim.append(linha)
        if len(partes) >= 2:
            chave = partes[0].strip().rstrip(":").upper()
            valor = partes[1].strip()
            metadados_dict[chave] = valor

    if idx_cabecalho is None:
        raise ValueError(
            f"Não foi encontrado o cabeçalho de dados ('Data;...') no arquivo BDMEP: {caminho_csv_bruto}"
        )

    # Extração obrigatória dos metadados da estação diretamente do bloco inicial do arquivo
    try:
        latitude_deg = _parse_valor_bdmep(metadados_dict.get("LATITUDE"))
        longitude_deg = _parse_valor_bdmep(metadados_dict.get("LONGITUDE"))
        altitude_m = _parse_valor_bdmep(metadados_dict.get("ALTITUDE"))
    except ValueError as exc:
        raise ValueError(f"Erro ao converter coordenadas do bloco de metadados: {exc}") from exc

    codigo_estacao = (
        metadados_dict.get("CODIGO (WMO)")
        or metadados_dict.get("CODIGO ESTACAO")
        or metadados_dict.get("CÓDIGO (WMO)")
    )
    nome_estacao = metadados_dict.get("ESTACAO") or metadados_dict.get("ESTAÇÃO")
    uf_estacao = metadados_dict.get("UF") or ""
    regiao_estacao = metadados_dict.get("REGIAO") or metadados_dict.get("REGIÃO") or ""
    data_fundacao = metadados_dict.get("DATA DE FUNDACAO") or metadados_dict.get("DATA DE FUNDAÇÃO") or ""

    if latitude_deg is None or longitude_deg is None or altitude_m is None or not codigo_estacao or not nome_estacao:
        raise ValueError(
            f"Metadados obrigatórios (código, nome, latitude, longitude, altitude) ausentes no cabeçalho do arquivo: {metadados_dict}"
        )

    linha_cabecalho_verbatim = linhas_brutas[idx_cabecalho]
    colunas_cabecalho = linha_cabecalho_verbatim.split(";")
    mapa_colunas = _identificar_colunas_bdmep(colunas_cabecalho)
    nomes_colunas_originais = {
        var: colunas_cabecalho[col_idx].strip()
        for var, col_idx in mapa_colunas.items()
    }

    linhas_dados_verbatim = [
        ln for ln in linhas_brutas[idx_cabecalho + 1 :] if ln.strip() != ""
    ]
    if not linhas_dados_verbatim:
        raise ValueError(f"Arquivo BDMEP sem linhas de dados após o cabeçalho: {caminho_csv_bruto}")

    primeiras_5_verbatim = linhas_dados_verbatim[:5]
    ultimas_5_verbatim = linhas_dados_verbatim[-5:]

    eh_horario = "hora" in mapa_colunas

    # Estrutura de agregação diária preservando contagem de observações horárias válidas
    agrupado_diario: Dict[str, Dict[str, Any]] = {}
    for ln in linhas_dados_verbatim:
        partes = ln.split(";")
        dt_iso = _normalizar_data_bdmep(partes[mapa_colunas["data"]])
        v_p = _parse_valor_bdmep(partes[mapa_colunas["precipitacao_mm"]]) if mapa_colunas["precipitacao_mm"] < len(partes) else None
        v_tmax = _parse_valor_bdmep(partes[mapa_colunas["t_max"]]) if mapa_colunas["t_max"] < len(partes) else None
        v_tmin = _parse_valor_bdmep(partes[mapa_colunas["t_min"]]) if mapa_colunas["t_min"] < len(partes) else None
        v_tmed = _parse_valor_bdmep(partes[mapa_colunas["t_med"]]) if mapa_colunas["t_med"] < len(partes) else None

        reg = agrupado_diario.setdefault(
            dt_iso,
            {
                "total_linhas_dia": 0,
                "p_vals": [],
                "tmax_vals": [],
                "tmin_vals": [],
                "tmed_vals": [],
                "p_ausentes_horarios": 0,
                "tmax_ausentes_horarios": 0,
                "tmin_ausentes_horarios": 0,
                "tmed_ausentes_horarios": 0,
            },
        )
        reg["total_linhas_dia"] += 1
        if v_p is not None:
            reg["p_vals"].append(v_p)
        else:
            reg["p_ausentes_horarios"] += 1

        if v_tmax is not None:
            reg["tmax_vals"].append(v_tmax)
        else:
            reg["tmax_ausentes_horarios"] += 1

        if v_tmin is not None:
            reg["tmin_vals"].append(v_tmin)
        else:
            reg["tmin_ausentes_horarios"] += 1

        if v_tmed is not None:
            reg["tmed_vals"].append(v_tmed)
        else:
            reg["tmed_ausentes_horarios"] += 1

    datas_presentes = sorted(agrupado_diario.keys())
    data_ini_arq = datas_presentes[0]
    data_fim_arq = datas_presentes[-1]

    # Garante grade diária contínua entre data_ini_arq e data_fim_arq para detectar qualquer data omitida
    dt_cursor = date.fromisoformat(data_ini_arq)
    dt_fim = date.fromisoformat(data_fim_arq)
    serie_diaria_bruta: Dict[str, Dict[str, Any]] = {}
    while dt_cursor <= dt_fim:
        d_str = dt_cursor.isoformat()
        info = agrupado_diario.get(d_str)
        esperado_h = 24 if eh_horario else 1
        if info is None:
            serie_diaria_bruta[d_str] = {
                "data": d_str,
                "t_max": None,
                "t_min": None,
                "t_med": None,
                "precipitacao_mm": None,
                "horas_esperadas": esperado_h,
                "horas_validas_p": 0,
                "horas_validas_tmax": 0,
                "horas_validas_tmin": 0,
                "horas_validas_tmed": 0,
                "horas_ausentes_p": esperado_h,
                "horas_ausentes_tmax": esperado_h,
                "horas_ausentes_tmin": esperado_h,
                "horas_ausentes_tmed": esperado_h,
            }
        else:
            p_val = sum(info["p_vals"]) if len(info["p_vals"]) > 0 else None
            tmax_val = max(info["tmax_vals"]) if len(info["tmax_vals"]) > 0 else None
            tmin_val = min(info["tmin_vals"]) if len(info["tmin_vals"]) > 0 else None
            tmed_val = statistics.mean(info["tmed_vals"]) if len(info["tmed_vals"]) > 0 else None
            serie_diaria_bruta[d_str] = {
                "data": d_str,
                "t_max": tmax_val,
                "t_min": tmin_val,
                "t_med": tmed_val,
                "precipitacao_mm": p_val,
                "horas_esperadas": info["total_linhas_dia"],
                "horas_validas_p": len(info["p_vals"]),
                "horas_validas_tmax": len(info["tmax_vals"]),
                "horas_validas_tmin": len(info["tmin_vals"]),
                "horas_validas_tmed": len(info["tmed_vals"]),
                "horas_ausentes_p": info["p_ausentes_horarios"],
                "horas_ausentes_tmax": info["tmax_ausentes_horarios"],
                "horas_ausentes_tmin": info["tmin_ausentes_horarios"],
                "horas_ausentes_tmed": info["tmed_ausentes_horarios"],
            }
        dt_cursor += timedelta(days=1)

    return {
        "caminho_arquivo_bruto": os.path.abspath(caminho_csv_bruto),
        "nome_arquivo_bruto": os.path.basename(caminho_csv_bruto),
        "sha256_bruto": sha256_hex,
        "tamanho_bytes": tamanho_bytes,
        "codificacao": codificacao_detectada,
        "numero_linhas_total": numero_linhas_total,
        "numero_linhas_metadados": len(linhas_metadados_verbatim),
        "numero_linhas_dados": len(linhas_dados_verbatim),
        "bloco_metadados_verbatim": "\n".join(linhas_metadados_verbatim),
        "linhas_metadados_lista": linhas_metadados_verbatim,
        "linha_cabecalho_verbatim": linha_cabecalho_verbatim,
        "primeiras_5_linhas_dados_verbatim": primeiras_5_verbatim,
        "ultimas_5_linhas_dados_verbatim": ultimas_5_verbatim,
        "metadados_estacao": {
            "regiao": regiao_estacao,
            "uf": uf_estacao,
            "nome_estacao": nome_estacao,
            "codigo_wmo": codigo_estacao,
            "latitude_deg": latitude_deg,
            "latitude_verbatim": metadados_dict.get("LATITUDE", ""),
            "longitude_deg": longitude_deg,
            "longitude_verbatim": metadados_dict.get("LONGITUDE", ""),
            "altitude_m": altitude_m,
            "altitude_verbatim": metadados_dict.get("ALTITUDE", ""),
            "data_fundacao": data_fundacao,
        },
        "nomes_colunas_originais": nomes_colunas_originais,
        "data_inicial_arquivo": data_ini_arq,
        "data_final_arquivo": data_fim_arq,
        "total_dias_arquivo": len(serie_diaria_bruta),
        "resolucao_original": "Horária (24 registros UTC/dia)" if eh_horario else "Diária",
        "url_origem": URL_ORIGEM_BDMEP_2023,
        "data_download": DATA_DOWNLOAD_ARQUIVO,
        "serie_diaria_bruta": serie_diaria_bruta,
    }


def _mapear_lacunas_com_datas(
    datas: List[str], valores: List[Optional[float]]
) -> Dict[str, Any]:
    """
    Identifica todas as lacunas em um vetor diário (onde valor is None),
    retornando quantidade de dias ausentes, percentual, maior lacuna consecutiva
    e a lista detalhada de cada lacuna com suas datas de início, fim e duração.
    """
    n = len(valores)
    faltantes = 0
    maior_lacuna = 0
    lacunas_detalhadas: List[Dict[str, Any]] = []

    i = 0
    while i < n:
        if valores[i] is None:
            ini = i
            while i < n and valores[i] is None:
                i += 1
            fim = i - 1
            tam = fim - ini + 1
            faltantes += tam
            maior_lacuna = max(maior_lacuna, tam)
            lacunas_detalhadas.append({
                "data_inicio": datas[ini],
                "data_fim": datas[fim],
                "duracao_dias": tam,
                "intervalo_str": (
                    f"{datas[ini]} (1d)"
                    if tam == 1
                    else f"{datas[ini]} a {datas[fim]} ({tam}d)"
                ),
            })
        else:
            i += 1

    return {
        "total_registros": n,
        "registros_faltantes": faltantes,
        "percentual_falhas_pct": round((faltantes / n * 100.0) if n > 0 else 0.0, 2),
        "maior_lacuna_consecutiva_dias": maior_lacuna,
        "lacunas": lacunas_detalhadas,
        "datas_lacunas_resumo": (
            "; ".join(lc["intervalo_str"] for lc in lacunas_detalhadas)
            if lacunas_detalhadas
            else "Nenhuma lacuna (0 ausentes)"
        ),
    }


def _interpolar_vetor(
    valores: List[Optional[float]],
    max_lacuna: int = 3,
    datas: Optional[List[str]] = None,
    nome_variavel: str = "",
) -> Tuple[List[float], int, int]:
    """
    Interpola linearmente lacunas de tamanho <= `max_lacuna`.
    Se encontrar lacuna > `max_lacuna`, levanta ValueError explícito informando
    as datas da lacuna e interrompendo a execução (Parte 1.7).
    """
    n = len(valores)
    resultado: List[Optional[float]] = list(valores)
    faltantes = 0
    maior_lacuna = 0

    i = 0
    while i < n:
        if resultado[i] is None:
            ini = i
            while i < n and resultado[i] is None:
                i += 1
            fim = i
            tam = fim - ini
            faltantes += tam
            maior_lacuna = max(maior_lacuna, tam)
            if tam > max_lacuna:
                dt_ini_str = datas[ini] if datas and ini < len(datas) else f"idx={ini}"
                dt_fim_str = datas[fim - 1] if datas and (fim - 1) < len(datas) else f"idx={fim-1}"
                raise ValueError(
                    f"PARADA OBRIGATÓRIA (Parte 1.7): Lacuna longa detectada em '{nome_variavel}' "
                    f"de {dt_ini_str} a {dt_fim_str} ({tam} dias consecutivos > limite de {max_lacuna} dias). "
                    "O período não pode ser interpolado."
                )
            if ini == 0 and fim >= n:
                raise ValueError(f"Série inteira ausente para a variável '{nome_variavel}'.")
            val_esq = resultado[ini - 1] if ini > 0 else resultado[fim]
            val_dir = resultado[fim] if fim < n else val_esq
            assert val_esq is not None and val_dir is not None
            for k in range(tam):
                frac = (k + 1) / (tam + 1)
                resultado[ini + k] = float(val_esq) + frac * (float(val_dir) - float(val_esq))
        else:
            i += 1

    return [float(x) for x in resultado if x is not None], faltantes, maior_lacuna


def _calcular_estatisticas_descritivas(valores: List[float]) -> Dict[str, float]:
    """Calcula mínimo, máximo, média, desvio-padrão, mediana e soma (Parte 1.4h)."""
    if not valores:
        raise ValueError("Lista vazia ao calcular estatísticas descritivas.")
    return {
        "minimo": round(min(valores), 2),
        "maximo": round(max(valores), 2),
        "media": round(statistics.mean(valores), 2),
        "desvio_padrao": round(statistics.stdev(valores), 2) if len(valores) > 1 else 0.0,
        "mediana": round(statistics.median(valores), 2),
        "soma": round(sum(valores), 2),
    }


def carregar_e_tratar_serie_climatica(
    caminho_csv: str = DEFAULT_RAW_INMET_CSV,
    max_lacuna_interpolavel: int = 3,
    usar_kc_fases: bool = True,
    ciclos_datas: Optional[Dict[str, Tuple[str, str]]] = None,
    diretorio_processed: str = DEFAULT_PROCESSED_DIR,
) -> Dict[str, Any]:
    """
    Lê o arquivo bruto do INMET/BDMEP (ou um CSV processado em formato BDMEP),
    valida que todas as datas dos ciclos solicitados existem no arquivo bruto,
    verifica a ausência de lacunas > `max_lacuna_interpolavel` dias (Parte 1.7),
    calcula `ET0` usando a latitude extraída dos metadados do arquivo (Parte 1.5),
    salva a série tratada em `data/processed/` (Parte 1.3) e retorna todas as
    provas de procedência e estatísticas descritivas (Partes 1.4 e 1.6).
    """
    bruto = ler_arquivo_bruto_bdmep(caminho_csv)
    serie_diaria_bruta = bruto["serie_diaria_bruta"]
    latitude_deg = float(bruto["metadados_estacao"]["latitude_deg"])
    ciclos = ciclos_datas or CICLOS_PADRAO

    # Auditoria da série anual completa presente no arquivo bruto (365 dias)
    datas_ano = sorted(serie_diaria_bruta.keys())
    qualidade_arquivo_completo: Dict[str, Any] = {}
    for var_key, col_orig in (
        ("t_max", bruto["nomes_colunas_originais"]["t_max"]),
        ("t_min", bruto["nomes_colunas_originais"]["t_min"]),
        ("t_med", bruto["nomes_colunas_originais"]["t_med"]),
        ("precipitacao_mm", bruto["nomes_colunas_originais"]["precipitacao_mm"]),
    ):
        vetor_ano = [serie_diaria_bruta[d][var_key] for d in datas_ano]
        lac_ano = _mapear_lacunas_com_datas(datas_ano, vetor_ano)
        sufixo_h = {
            "t_max": "tmax",
            "t_min": "tmin",
            "t_med": "tmed",
            "precipitacao_mm": "p",
        }[var_key]
        horas_esp_ano = sum(serie_diaria_bruta[d]["horas_esperadas"] for d in datas_ano)
        horas_aus_ano = sum(serie_diaria_bruta[d][f"horas_ausentes_{sufixo_h}"] for d in datas_ano)
        dias_parciais_ano = [
            f"{d} ({serie_diaria_bruta[d][f'horas_validas_{sufixo_h}']}/{serie_diaria_bruta[d]['horas_esperadas']}h)"
            for d in datas_ano
            if 0 < serie_diaria_bruta[d][f"horas_validas_{sufixo_h}"] < serie_diaria_bruta[d]["horas_esperadas"]
        ]
        qualidade_arquivo_completo[var_key] = {
            "coluna_original_bdmep": col_orig,
            **lac_ano,
            "horas_esperadas_total": horas_esp_ano,
            "horas_ausentes_total": horas_aus_ano,
            "percentual_horas_ausentes_pct": round(
                (horas_aus_ano / horas_esp_ano * 100.0) if horas_esp_ano > 0 else 0.0, 2
            ),
            "dias_com_falha_horaria_parcial": dias_parciais_ano,
        }

    series_tratadas: Dict[str, List[ClimateDay]] = {}
    relatorio_qualidade: Dict[str, Any] = {}
    linhas_processadas_ciclos: List[Dict[str, Any]] = []

    total_registros_ciclos = 0
    total_faltantes_ciclos = 0
    acum_por_variavel_ciclos: Dict[str, List[Optional[float]]] = {
        "t_max": [],
        "t_min": [],
        "t_med": [],
        "precipitacao_mm": [],
    }
    datas_acum_ciclos: List[str] = []

    for periodo, (dt_ini, dt_fim) in ciclos.items():
        # Verifica se o intervalo está integralmente contido no arquivo bruto
        if dt_ini < bruto["data_inicial_arquivo"] or dt_fim > bruto["data_final_arquivo"]:
            raise ValueError(
                f"ERRO EXPLÍCITO (Proibição 1): O ciclo '{periodo}' ({dt_ini} a {dt_fim}) "
                f"não está coberto pelo arquivo bruto ({bruto['data_inicial_arquivo']} a {bruto['data_final_arquivo']})."
            )

        datas_ciclo = [d for d in datas_ano if dt_ini <= d <= dt_fim]
        n = len(datas_ciclo)
        if n == 0:
            raise ValueError(f"Nenhum registro encontrado para o ciclo '{periodo}' ({dt_ini} a {dt_fim}).")

        total_registros_ciclos += n

        tmax_raw: List[Optional[float]] = []
        tmin_raw: List[Optional[float]] = []
        tmed_raw: List[Optional[float]] = []
        prec_opt_raw: List[Optional[float]] = []
        flags_faltante: List[bool] = []

        for d_str in datas_ciclo:
            reg_d = serie_diaria_bruta[d_str]
            v_tmax = reg_d["t_max"]
            v_tmin = reg_d["t_min"]
            v_tmed = reg_d["t_med"]
            v_prec = reg_d["precipitacao_mm"]

            faltou = (v_tmax is None) or (v_tmin is None) or (v_tmed is None) or (v_prec is None)
            flags_faltante.append(faltou)

            tmax_raw.append(v_tmax)
            tmin_raw.append(v_tmin)
            tmed_raw.append(v_tmed)
            prec_opt_raw.append(v_prec)

            acum_por_variavel_ciclos["t_max"].append(v_tmax)
            acum_por_variavel_ciclos["t_min"].append(v_tmin)
            acum_por_variavel_ciclos["t_med"].append(v_tmed)
            acum_por_variavel_ciclos["precipitacao_mm"].append(v_prec)
            datas_acum_ciclos.append(d_str)

        # Verifica lacunas por variável no ciclo e aplica tratamento (ou falha se > 3 dias)
        stats_variaveis_periodo: Dict[str, Any] = {}
        for var_key, vetor_var, regra_str in (
            (
                "t_max",
                tmax_raw,
                f"Interpolação linear para lacunas <= {max_lacuna_interpolavel}d; parada se > {max_lacuna_interpolavel}d",
            ),
            (
                "t_min",
                tmin_raw,
                f"Interpolação linear para lacunas <= {max_lacuna_interpolavel}d; parada se > {max_lacuna_interpolavel}d",
            ),
            (
                "t_med",
                tmed_raw,
                f"Interpolação linear para lacunas <= {max_lacuna_interpolavel}d; parada se > {max_lacuna_interpolavel}d",
            ),
            (
                "precipitacao_mm",
                prec_opt_raw,
                f"Verificação de ausentes (parada se lacuna > {max_lacuna_interpolavel}d; 0,0 mm se falha curta isolada)",
            ),
        ):
            lac_info = _mapear_lacunas_com_datas(datas_ciclo, vetor_var)
            sufixo_h = {
                "t_max": "tmax",
                "t_min": "tmin",
                "t_med": "tmed",
                "precipitacao_mm": "p",
            }[var_key]
            horas_esp = sum(serie_diaria_bruta[d]["horas_esperadas"] for d in datas_ciclo)
            horas_aus = sum(serie_diaria_bruta[d][f"horas_ausentes_{sufixo_h}"] for d in datas_ciclo)
            tratamento_efetivo = (
                "Nenhum tratamento necessário (100% dos registros horários e diários presentes)"
                if lac_info["registros_faltantes"] == 0 and horas_aus == 0
                else regra_str
            )
            stats_variaveis_periodo[var_key] = {
                "coluna_original_bdmep": bruto["nomes_colunas_originais"][var_key],
                **lac_info,
                "horas_esperadas": horas_esp,
                "horas_ausentes": horas_aus,
                "percentual_horas_ausentes_pct": round(
                    (horas_aus / horas_esp * 100.0) if horas_esp > 0 else 0.0, 2
                ),
                "tratamento_adotado": tratamento_efetivo,
            }

        # Se qualquer variável tiver lacuna > max_lacuna_interpolavel, _interpolar_vetor levanta ValueError (Parte 1.7)
        tmax_interp, _, maior_lac_tmax = _interpolar_vetor(
            tmax_raw, max_lacuna_interpolavel, datas_ciclo, f"{periodo}:t_max"
        )
        tmin_interp, _, maior_lac_tmin = _interpolar_vetor(
            tmin_raw, max_lacuna_interpolavel, datas_ciclo, f"{periodo}:t_min"
        )
        tmed_interp, _, maior_lac_tmed = _interpolar_vetor(
            tmed_raw, max_lacuna_interpolavel, datas_ciclo, f"{periodo}:t_med"
        )
        # Verifica também se precipitação tem lacuna > max_lacuna_interpolavel
        _, _, maior_lac_prec = _interpolar_vetor(
            prec_opt_raw, max_lacuna_interpolavel, datas_ciclo, f"{periodo}:precipitacao_mm"
        )
        prec_tratada = [float(p) if p is not None else 0.0 for p in prec_opt_raw]
        maior_lacuna_ciclo = max(maior_lac_tmax, maior_lac_tmin, maior_lac_tmed, maior_lac_prec)

        dias_periodo: List[ClimateDay] = []
        et0_lista: List[float] = []
        etc_lista: List[float] = []

        for idx_r, d_str in enumerate(datas_ciclo):
            dt_obj = date.fromisoformat(d_str)
            j = dt_obj.timetuple().tm_yday
            kc_dia = kc_hortalica_folhosa(idx_r + 1, usar_kc_fases=usar_kc_fases)
            dia_obj = ClimateDay(
                data=d_str,
                dia_do_ano=j,
                t_max=round(tmax_interp[idx_r], 2),
                t_min=round(tmin_interp[idx_r], 2),
                t_med=round(tmed_interp[idx_r], 2),
                precipitacao_mm=round(prec_tratada[idx_r], 2),
                kc=kc_dia,
                interpolado=flags_faltante[idx_r],
            )
            et0_dia = calcular_et0_hargreaves_samani(
                dia_obj.dia_do_ano,
                dia_obj.t_max,
                dia_obj.t_min,
                dia_obj.t_med,
                latitude_deg=latitude_deg,
            )
            etc_dia = et0_dia * kc_dia
            et0_lista.append(et0_dia)
            etc_lista.append(etc_dia)
            dias_periodo.append(dia_obj)

            linhas_processadas_ciclos.append({
                "periodo": periodo,
                "dia_ciclo": idx_r + 1,
                "data": d_str,
                "dia_do_ano_j": j,
                "t_max_c": f"{dia_obj.t_max:.2f}",
                "t_min_c": f"{dia_obj.t_min:.2f}",
                "t_med_c": f"{dia_obj.t_med:.2f}",
                "precipitacao_mm": f"{dia_obj.precipitacao_mm:.2f}",
                "et0_hargreaves_mm": f"{et0_dia:.4f}",
                "kc": f"{kc_dia:.2f}",
                "etc_mm": f"{etc_dia:.4f}",
                "interpolado": int(dia_obj.interpolado),
            })

        qtd_faltantes = sum(1 for fl in flags_faltante if fl)
        total_faltantes_ciclos += qtd_faltantes
        pct_falhas = (qtd_faltantes / n * 100.0) if n > 0 else 0.0

        # Estatísticas descritivas por variável e por ciclo (Parte 1.4h e T1)
        p_vals_ciclo = [d.precipitacao_mm for d in dias_periodo]
        tmax_vals_ciclo = [d.t_max for d in dias_periodo]
        tmin_vals_ciclo = [d.t_min for d in dias_periodo]
        tmed_vals_ciclo = [d.t_med for d in dias_periodo]

        estatisticas_descritivas_ciclo = {
            "precipitacao_mm": _calcular_estatisticas_descritivas(p_vals_ciclo),
            "t_max": _calcular_estatisticas_descritivas(tmax_vals_ciclo),
            "t_min": _calcular_estatisticas_descritivas(tmin_vals_ciclo),
            "t_med": _calcular_estatisticas_descritivas(tmed_vals_ciclo),
            "et0_mm": _calcular_estatisticas_descritivas(et0_lista),
            "etc_mm": _calcular_estatisticas_descritivas(etc_lista),
        }

        dias_com_chuva = sum(1 for p in p_vals_ciclo if p > 0.0)
        maior_chuva_mm = max(p_vals_ciclo) if p_vals_ciclo else 0.0
        idx_maior_chuva = p_vals_ciclo.index(maior_chuva_mm) if p_vals_ciclo else 0
        data_maior_chuva = datas_ciclo[idx_maior_chuva] if datas_ciclo else ""

        series_tratadas[periodo] = dias_periodo
        relatorio_qualidade[periodo] = {
            "data_inicial": datas_ciclo[0],
            "data_final": datas_ciclo[-1],
            "dia_do_ano_inicial": dias_periodo[0].dia_do_ano,
            "dia_do_ano_final": dias_periodo[-1].dia_do_ano,
            "ano": int(datas_ciclo[0][:4]),
            "total_dias": n,
            "dias_com_falha_interpolados": qtd_faltantes,
            "percentual_falhas_pct": round(pct_falhas, 2),
            "maior_lacuna_consecutiva_dias": maior_lacuna_ciclo,
            "por_variavel": stats_variaveis_periodo,
            "estatisticas_descritivas": estatisticas_descritivas_ciclo,
            "metodo_tratamento": (
                f"Interpolação linear para lacunas curtas (<= {max_lacuna_interpolavel} dias); "
                f"parada obrigatória para lacunas > {max_lacuna_interpolavel} dias."
            ),
            "et0_total_mm": round(sum(et0_lista), 2),
            "et0_medio_mm_dia": round(statistics.mean(et0_lista), 2),
            "etc_total_mm": round(sum(etc_lista), 2),
            "etc_medio_mm_dia": round(statistics.mean(etc_lista), 2),
            "precipitacao_total_mm": round(sum(p_vals_ciclo), 2),
            "t_med_ciclo_c": round(statistics.mean(tmed_vals_ciclo), 2),
            "t_max_abs_c": round(max(tmax_vals_ciclo), 2),
            "t_min_abs_c": round(min(tmin_vals_ciclo), 2),
            "dias_com_chuva": dias_com_chuva,
            "maior_evento_chuva_mm": round(maior_chuva_mm, 2),
            "data_maior_evento_chuva": data_maior_chuva,
        }

    # Salva os arquivos derivados em data/processed/ sem jamais tocar em data/raw/ (Parte 1.3)
    os.makedirs(diretorio_processed, exist_ok=True)
    caminho_proc_anual = os.path.join(
        diretorio_processed, "inmet_A204_balsas_2023_diario_bruto_agregado.csv"
    )
    with open(caminho_proc_anual, "w", newline="", encoding="utf-8") as f_anual:
        writer = csv.DictWriter(
            f_anual,
            fieldnames=[
                "data",
                "t_max",
                "t_min",
                "t_med",
                "precipitacao_mm",
                "horas_esperadas",
                "horas_validas_p",
                "horas_validas_tmax",
                "horas_validas_tmin",
                "horas_validas_tmed",
            ],
        )
        writer.writeheader()
        for d_str in datas_ano:
            r = serie_diaria_bruta[d_str]
            writer.writerow({
                "data": d_str,
                "t_max": f"{r['t_max']:.2f}" if r["t_max"] is not None else "",
                "t_min": f"{r['t_min']:.2f}" if r["t_min"] is not None else "",
                "t_med": f"{r['t_med']:.2f}" if r["t_med"] is not None else "",
                "precipitacao_mm": f"{r['precipitacao_mm']:.2f}" if r["precipitacao_mm"] is not None else "",
                "horas_esperadas": r["horas_esperadas"],
                "horas_validas_p": r["horas_validas_p"],
                "horas_validas_tmax": r["horas_validas_tmax"],
                "horas_validas_tmin": r["horas_validas_tmin"],
                "horas_validas_tmed": r["horas_validas_tmed"],
            })

    caminho_proc_ciclos = os.path.join(
        diretorio_processed, "inmet_A204_balsas_2023_ciclos_70d_tratados.csv"
    )
    with open(caminho_proc_ciclos, "w", newline="", encoding="utf-8") as f_ciclos:
        writer = csv.DictWriter(
            f_ciclos,
            fieldnames=list(linhas_processadas_ciclos[0].keys()) if linhas_processadas_ciclos else [],
        )
        writer.writeheader()
        writer.writerows(linhas_processadas_ciclos)

    stats_variaveis_ciclos = {
        var: _mapear_lacunas_com_datas(datas_acum_ciclos, valores)
        for var, valores in acum_por_variavel_ciclos.items()
    }

    relatorio_qualidade["global"] = {
        "estacao": (
            f"INMET {bruto['metadados_estacao']['codigo_wmo']} - "
            f"{bruto['metadados_estacao']['nome_estacao']} ({bruto['metadados_estacao']['uf']}) "
            f"[lat = {latitude_deg:.8f}°]"
        ),
        "latitude_extraida_deg": latitude_deg,
        "longitude_extraida_deg": bruto["metadados_estacao"]["longitude_deg"],
        "altitude_extraida_m": bruto["metadados_estacao"]["altitude_m"],
        "metadados_procedencia": {
            "origem_real_inmet": True,
            "codigo_wmo": bruto["metadados_estacao"]["codigo_wmo"],
            "nome_estacao": bruto["metadados_estacao"]["nome_estacao"],
            "uf": bruto["metadados_estacao"]["uf"],
            "regiao": bruto["metadados_estacao"]["regiao"],
            "latitude_graus": latitude_deg,
            "latitude_verbatim": bruto["metadados_estacao"]["latitude_verbatim"],
            "longitude_graus": bruto["metadados_estacao"]["longitude_deg"],
            "longitude_verbatim": bruto["metadados_estacao"]["longitude_verbatim"],
            "altitude_m": bruto["metadados_estacao"]["altitude_m"],
            "altitude_verbatim": bruto["metadados_estacao"]["altitude_verbatim"],
            "data_fundacao": bruto["metadados_estacao"]["data_fundacao"],
            "arquivo_bruto_caminho": bruto["caminho_arquivo_bruto"],
            "arquivo_bruto_nome": bruto["nome_arquivo_bruto"],
            "sha256_bruto": bruto["sha256_bruto"],
            "tamanho_bytes": bruto["tamanho_bytes"],
            "codificacao": bruto["codificacao"],
            "numero_linhas_total": bruto["numero_linhas_total"],
            "numero_linhas_metadados": bruto["numero_linhas_metadados"],
            "numero_linhas_dados": bruto["numero_linhas_dados"],
            "bloco_metadados_verbatim": bruto["bloco_metadados_verbatim"],
            "linha_cabecalho_verbatim": bruto["linha_cabecalho_verbatim"],
            "primeiras_5_linhas_dados_verbatim": bruto["primeiras_5_linhas_dados_verbatim"],
            "ultimas_5_linhas_dados_verbatim": bruto["ultimas_5_linhas_dados_verbatim"],
            "data_inicial_arquivo": bruto["data_inicial_arquivo"],
            "data_final_arquivo": bruto["data_final_arquivo"],
            "total_dias_arquivo": bruto["total_dias_arquivo"],
            "resolucao_original": bruto["resolucao_original"],
            "url_origem": bruto["url_origem"],
            "data_download": bruto["data_download"],
            "nomes_colunas_originais": bruto["nomes_colunas_originais"],
            "arquivos_processados_gerados": [caminho_proc_anual, caminho_proc_ciclos],
        },
        "total_dias": total_registros_ciclos,
        "total_dias_interpolados": total_faltantes_ciclos,
        "percentual_falhas_global_pct": round(
            (total_faltantes_ciclos / total_registros_ciclos * 100.0)
            if total_registros_ciclos > 0
            else 0.0,
            2,
        ),
        "por_variavel": stats_variaveis_ciclos,
        "qualidade_arquivo_anual_completo": qualidade_arquivo_completo,
    }

    return {
        "series": series_tratadas,
        "qualidade": relatorio_qualidade,
        "latitude_deg": latitude_deg,
    }
