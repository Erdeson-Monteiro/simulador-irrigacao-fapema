"""
Simulador de Telemetria e Irrigação (Etapa 6) — Executa o modelo de balanço hídrico
sobre a série climática real do INMET (Balsas-MA) e envia lotes de leituras e eventos
para a interface de ingestão (`POST /api/v1/leituras` e `POST /api/v1/eventos-irrigacao`),
usando exatamente o mesmo contrato HTTP/JSON que será utilizado pelo microcontrolador.
"""

from __future__ import annotations
import json
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error

from src.water_balance import SoilParams, SCENARIOS_PADRAO, simular_estrategia
from src.climate import DEFAULT_RAW_INMET_CSV, carregar_e_tratar_serie_climatica
from src.database import (
    DEFAULT_DB_PATH,
    inicializar_banco,
    ingerir_lote_leituras,
    ingerir_lote_eventos_irrigacao,
)


DISPOSITIVO_SIMULADOR = "sim-001"
TOKEN_SIMULADOR = "tok-sim-001-fapema"

# Mapeamento dos canteiros monitorados para simulação contínua
CONFIG_CANTEIROS_SIMULADOS = [
    {"canteiro": "C1", "estrategia": "E1", "cenario": "Moderado"},
    {"canteiro": "C2", "estrategia": "E2", "cenario": "Moderado"},
    {"canteiro": "C3", "estrategia": "E3", "cenario": "Moderado"},
    {"canteiro": "C4", "estrategia": "E3", "cenario": "Restrito"},
    {"canteiro": "C5", "estrategia": "E3", "cenario": "Abundante"},
]


def _enviar_http_post(url: str, payload: Dict[str, Any], token: str) -> Dict[str, Any]:
    """Envia requisição HTTP POST JSON autenticada com Bearer token."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def gerar_lotes_simulacao(
    caminho_csv_clima: str = DEFAULT_RAW_INMET_CSV,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Executa o modelo físico para cada canteiro nos períodos de Estação Chuvosa e Estação Seca
    e converte os estados físicos em leituras brutas de sensores e eventos de irrigação.
    """
    soil = SoilParams()
    dados_clima = carregar_e_tratar_serie_climatica(caminho_csv_clima)
    series_por_periodo = dados_clima["series"]
    latitude_deg = dados_clima["latitude_deg"]

    leituras_geradas: List[Dict[str, Any]] = []
    eventos_geradas: List[Dict[str, Any]] = []

    seq_leitura = 1001
    seq_evento = 501

    for cfg in CONFIG_CANTEIROS_SIMULADOS:
        cod_canteiro = cfg["canteiro"]
        cod_estrategia = cfg["estrategia"]
        cenario_obj = SCENARIOS_PADRAO[cfg["cenario"]]

        for periodo_nome in ("Estacao_Chuvosa", "Estacao_Seca"):
            serie_dias = series_por_periodo[periodo_nome]
            resultado = simular_estrategia(
                estrategia_codigo=cod_estrategia,
                serie_climatica=serie_dias,
                latitude_deg=latitude_deg,
                soil=soil,
                cenario=cenario_obj,
                periodo_nome=periodo_nome,
            )

            for idx_d, passo in enumerate(resultado["historico"]):
                dia_clima = serie_dias[idx_d]
                ts_leitura = f"{passo.data}T14:00:00-03:00"

                # 1. Umidade do solo Camada 1 (profundidade 10 cm): bruto em décimos de milésimo
                leituras_geradas.append(
                    {
                        "seq": seq_leitura,
                        "canteiro": cod_canteiro,
                        "tipo": "umidade_solo",
                        "profundidade_cm": 10,
                        "valor_bruto": round(passo.theta1_final * 10000.0, 1),
                        "registrado_em": ts_leitura,
                    }
                )
                seq_leitura += 1

                # 2. Umidade do solo Camada 2 (profundidade 30 cm)
                leituras_geradas.append(
                    {
                        "seq": seq_leitura,
                        "canteiro": cod_canteiro,
                        "tipo": "umidade_solo",
                        "profundidade_cm": 30,
                        "valor_bruto": round(passo.theta2_final * 10000.0, 1),
                        "registrado_em": ts_leitura,
                    }
                )
                seq_leitura += 1

                # 3. Nível do reservatório (décimos de litro)
                leituras_geradas.append(
                    {
                        "seq": seq_leitura,
                        "canteiro": cod_canteiro,
                        "tipo": "nivel_reservatorio",
                        "profundidade_cm": None,
                        "valor_bruto": round(passo.volume_reservatorio_final_l * 10.0, 1),
                        "registrado_em": ts_leitura,
                    }
                )
                seq_leitura += 1

                # 4. Temperatura média do ar (décimos de °C)
                leituras_geradas.append(
                    {
                        "seq": seq_leitura,
                        "canteiro": cod_canteiro,
                        "tipo": "temperatura_ar",
                        "profundidade_cm": None,
                        "valor_bruto": round(dia_clima.t_med * 10.0, 1),
                        "registrado_em": ts_leitura,
                    }
                )
                seq_leitura += 1

                # 5. Precipitação diária (décimos de mm)
                leituras_geradas.append(
                    {
                        "seq": seq_leitura,
                        "canteiro": cod_canteiro,
                        "tipo": "precipitacao",
                        "profundidade_cm": None,
                        "valor_bruto": round(passo.p_mm * 10.0, 1),
                        "registrado_em": ts_leitura,
                    }
                )
                seq_leitura += 1

                # 6. Evento de irrigação quando houver acionamento efetivo (I_efetiva(t) > 0)
                if passo.acionou_irrigacao:
                    inicio_iso = f"{passo.data}T06:00:00-03:00"
                    fim_iso = f"{passo.data}T06:30:00-03:00"
                    eventos_geradas.append(
                        {
                            "seq": seq_evento,
                            "canteiro": cod_canteiro,
                            "estrategia": cod_estrategia,
                            "inicio": inicio_iso,
                            "fim": fim_iso,
                            "lamina_mm": round(passo.i_mm, 2),
                            "volume_litros": round(passo.volume_irrigado_l, 2),
                            "origem": "simulado",
                            "registrado_em": fim_iso,
                        }
                    )
                    seq_evento += 1

    return {
        "leituras": leituras_geradas,
        "eventos": eventos_geradas,
    }


def executar_simulador(
    api_base_url: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
    caminho_csv_clima: str = DEFAULT_RAW_INMET_CSV,
    tamanho_lote: int = 250,
    dispositivo: str = DISPOSITIVO_SIMULADOR,
    token: str = TOKEN_SIMULADOR,
) -> Dict[str, Any]:
    """
    Gera todas as leituras e eventos da simulação e os envia em lotes para a interface
    de ingestão (via HTTP quando `api_base_url` é informado, ou diretamente para a camada
    de ingestão).
    """
    inicializar_banco(db_path)
    dados = gerar_lotes_simulacao(caminho_csv_clima)
    leituras = dados["leituras"]
    eventos = dados["eventos"]

    resumo_leituras = {"aceitos": 0, "ignorados": 0, "ultima_sequencia": 0, "lotes": 0}
    for i in range(0, len(leituras), tamanho_lote):
        fatia = leituras[i : i + tamanho_lote]
        payload = {"dispositivo": dispositivo, "leituras": fatia}
        if api_base_url:
            resp = _enviar_http_post(f"{api_base_url.rstrip('/')}/api/v1/leituras", payload, token)
        else:
            resp = ingerir_lote_leituras(db_path, payload, f"Bearer {token}")
        resumo_leituras["aceitos"] += resp["aceitos"]
        resumo_leituras["ignorados"] += resp["ignorados"]
        resumo_leituras["ultima_sequencia"] = resp["ultima_sequencia"]
        resumo_leituras["lotes"] += 1

    resumo_eventos = {"aceitos": 0, "ignorados": 0, "ultima_sequencia": 0, "lotes": 0}
    for i in range(0, len(eventos), tamanho_lote):
        fatia = eventos[i : i + tamanho_lote]
        payload = {"dispositivo": dispositivo, "eventos": fatia}
        if api_base_url:
            resp = _enviar_http_post(
                f"{api_base_url.rstrip('/')}/api/v1/eventos-irrigacao", payload, token
            )
        else:
            resp = ingerir_lote_eventos_irrigacao(db_path, payload, f"Bearer {token}")
        resumo_eventos["aceitos"] += resp["aceitos"]
        resumo_eventos["ignorados"] += resp["ignorados"]
        resumo_eventos["ultima_sequencia"] = resp["ultima_sequencia"]
        resumo_eventos["lotes"] += 1

    return {
        "dispositivo": dispositivo,
        "modo_envio": "http" if api_base_url else "direto",
        "leituras": resumo_leituras,
        "eventos": resumo_eventos,
    }
