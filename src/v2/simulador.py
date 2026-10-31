"""
Simulador de dispositivo do v2.

Três canteiros virtuais (C1 = E1, C2 = E2, C3 = E3) rodam o modelo v2 num ciclo e num cenário
e enviam as leituras horárias pela API de ingestão (`POST /api/v1/leituras` e
`POST /api/v1/eventos-irrigacao`), com o mesmo contrato e a mesma idempotência por
(dispositivo, seq) do microcontrolador de campo. Padrão: ciclo seco, cenário restrito.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import timedelta
import json
import threading
from typing import Any, Dict, List, Optional, Tuple
import urllib.request

from src.v2.clima import carregar_ciclos
from src.v2.modelo import ESTRATEGIAS, SEQUEIRO, Rodada, forcante_do_ciclo, simular
from src.v2.parametros import CENARIOS, PARAMETROS_PADRAO, ParametrosModelo


DISPOSITIVO = "sim-001"
CANTEIRO_DA_ESTRATEGIA = {"E1": "C1", "E2": "C2", "E3": "C3"}
CICLO_PADRAO = "seco"
CENARIO_PADRAO = "Restrito"
TAMANHO_LOTE = 500

# Escalas das calibrações cadastradas (valor_calibrado = valor_bruto × escala; src/database.py).
ESCALA_BRUTA = {"umidade_solo": 10000.0, "nivel_reservatorio": 10.0, "precipitacao": 10.0, "temperatura_ar": 10.0}


def rodar_canteiros(ciclo: str, cenario: str, par: ParametrosModelo = PARAMETROS_PADRAO) -> Tuple[Dict[str, Rodada], Any]:
    c = carregar_ciclos()[ciclo]
    f = forcante_do_ciclo(c)
    seq = simular(SEQUEIRO, f, par, nome_ciclo=ciclo)
    rodadas = {e: simular(e, f, par, CENARIOS[cenario], ciclo, seq.metricas.percolacao_mm) for e in ESTRATEGIAS}
    return rodadas, c


def gerar_lotes(ciclo: str = CICLO_PADRAO, cenario: str = CENARIO_PADRAO,
                par: ParametrosModelo = PARAMETROS_PADRAO) -> Dict[str, Any]:
    """Converte as rodadas em leituras e eventos no formato do contrato HTTP."""
    rodadas, c = rodar_canteiros(ciclo, cenario, par)
    leituras: List[Dict[str, Any]] = []
    eventos: List[Dict[str, Any]] = []
    for e in ESTRATEGIAS:
        r, canteiro = rodadas[e], CANTEIRO_DA_ESTRATEGIA[e]
        for k, h in enumerate(c.horas):
            inicio = h.inicio_local
            fim = (inicio + timedelta(hours=1)).isoformat()
            medidas = (
                ("umidade_solo", 10, r.serie["theta1"][k]),
                ("umidade_solo", 30, r.serie["theta2"][k]),
                ("nivel_reservatorio", None, r.serie["v_l"][k]),
                ("precipitacao", None, h.p_mm),
                ("temperatura_ar", None, h.t_c),
            )
            for tipo, prof, valor in medidas:
                leituras.append({
                    "seq": len(leituras) + 1, "canteiro": canteiro, "tipo": tipo, "profundidade_cm": prof,
                    "valor_bruto": round(valor * ESCALA_BRUTA[tipo], 2), "registrado_em": fim,
                })
            irrigacao = r.serie["i_mm"][k]
            if irrigacao > 0:
                eventos.append({
                    "seq": len(eventos) + 1, "canteiro": canteiro, "estrategia": e,
                    "inicio": inicio.isoformat(), "fim": inicio.isoformat(), "lamina_mm": round(irrigacao, 4),
                    "volume_litros": round(irrigacao * par.area_m2, 3), "origem": "simulado",
                    "registrado_em": inicio.isoformat(),
                })
    cen = CENARIOS[cenario]
    metadados = {
        "modelo": "v2", "ciclo": ciclo, "cenario": cenario, "capacidade_l": cen.capacidade_l,
        "intervalo_dias": cen.intervalo_dias, "inicio": c.inicio.isoformat(), "fim": c.fim.isoformat(),
        "parametros": par.como_dict(), "canteiros": dict((v, k) for k, v in CANTEIRO_DA_ESTRATEGIA.items()),
        "metricas": {e: asdict(rodadas[e].metricas) for e in ESTRATEGIAS},
    }
    return {"leituras": leituras, "eventos": eventos, "simulacao": metadados}


def _post(url: str, payload: Dict[str, Any], token: str) -> Dict[str, Any]:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def enviar(api_base_url: str, token: str, itens: List[Dict[str, Any]], tipo: str,
           tamanho_lote: int = TAMANHO_LOTE) -> Dict[str, int]:
    rota = {"leituras": "/api/v1/leituras", "eventos": "/api/v1/eventos-irrigacao"}[tipo]
    resumo = {"aceitos": 0, "ignorados": 0, "ultima_sequencia": 0, "lotes": 0}
    for i in range(0, len(itens), tamanho_lote):
        resp = _post(api_base_url.rstrip("/") + rota, {"dispositivo": DISPOSITIVO, tipo: itens[i:i + tamanho_lote]}, token)
        resumo["aceitos"] += resp["aceitos"]
        resumo["ignorados"] += resp["ignorados"]
        resumo["ultima_sequencia"] = resp["ultima_sequencia"]
        resumo["lotes"] += 1
    return resumo


def popular_banco(db_path: str, token: str, ciclo: str = CICLO_PADRAO, cenario: str = CENARIO_PADRAO,
                  dir_resultados: Optional[str] = None) -> Dict[str, Any]:
    """
    Sobe a API numa porta livre só de 127.0.0.1, apaga os dados anteriores do simulador, envia
    leituras e eventos por HTTP, reenvia o primeiro lote (prova de idempotência) e grava os
    metadados da simulação para o painel.
    """
    from src.api_server import iniciar_servidor
    from src.database import gravar_simulacao, limpar_dados_dispositivo

    lotes = gerar_lotes(ciclo, cenario)
    srv = iniciar_servidor(host="127.0.0.1", port=0, db_path=db_path, token_dispositivo=token,
                           dir_resultados=dir_resultados)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        apagados = limpar_dados_dispositivo(db_path, DISPOSITIVO)
        url = f"http://127.0.0.1:{srv.server_address[1]}"
        res_l = enviar(url, token, lotes["leituras"], "leituras")
        res_e = enviar(url, token, lotes["eventos"], "eventos")
        reenvio = enviar(url, token, lotes["leituras"][:TAMANHO_LOTE], "leituras")
    finally:
        srv.shutdown()
        srv.server_close()
    gravar_simulacao(db_path, lotes["simulacao"])
    return {"ciclo": ciclo, "cenario": cenario, "apagados": apagados, "leituras": res_l, "eventos": res_e,
            "reenvio": reenvio}
