"""
Figuras do artigo, todas pelo estilo único de `src/v2/estilo.py`.

- Figura 1: sensibilidade de E1 à lâmina; (a) TSE × L e (b) percolação incremental × L, nos dois
  ciclos, com E2 como linha de referência.
- Figura 2: ciclo seco, cenário restrito; (a) volume do reservatório e (b) Dr, com RAW e TAW,
  para E1, E2 e E3, em série horária com marcador a cada 24 h.
Os dados de cada figura são gravados em CSV ao lado dela.
"""

from __future__ import annotations

import os
from typing import Dict, List, Sequence

from src.v2 import estilo
from src.v2.formatacao import TabelaCSV, escrever_csv
from src.v2.modelo import Rodada


NOMES_CICLOS = {"chuvoso": "chuvoso", "seco": "seco"}


def figura_sensibilidade_e1(
    sens: Dict[tuple, Rodada],
    e2_ref: Dict[str, Rodada],
    laminas: Sequence[float],
    dir_figuras: str,
    raiz: str,
    metadados: Sequence[str],
) -> Dict[str, object]:
    registros = []
    for ciclo in ("chuvoso", "seco"):
        for L in laminas:
            m = sens[(ciclo, L)].metricas
            registros.append((f"{ciclo}|E1|{L:g}", {
                "ciclo": ciclo, "estrategia": "E1", "lamina_e1_mm": L, "tse_pct": m.tse_pct,
                "percolacao_incremental_mm": m.percolacao_incremental_mm,
            }))
        m2 = e2_ref[ciclo].metricas
        registros.append((f"{ciclo}|E2", {
            "ciclo": ciclo, "estrategia": "E2", "lamina_e1_mm": None, "tse_pct": m2.tse_pct,
            "percolacao_incremental_mm": m2.percolacao_incremental_mm,
        }))
    base = os.path.join(dir_figuras, "figura1_sensibilidade_e1")
    dados = escrever_csv(base + "_dados.csv", raiz,
                         ["ciclo", "estrategia", "lamina_e1_mm", "tse_pct", "percolacao_incremental_mm"],
                         registros, metadados)

    fig, (ax_a, ax_b) = estilo.nova_figura(7.5, 1, 2)
    estilo_ref = {"chuvoso": ":", "seco": "-."}
    for ciclo in ("chuvoso", "seco"):
        st = estilo.ESTILOS[ciclo]
        x = list(laminas)
        tse = [sens[(ciclo, L)].metricas.tse_pct for L in laminas]
        perc = [sens[(ciclo, L)].metricas.percolacao_incremental_mm for L in laminas]
        rotulo = f"E1, {NOMES_CICLOS[ciclo]}"
        ax_a.plot(x, tse, label=rotulo, **st)
        ax_b.plot(x, perc, label=rotulo, **st)
        m2 = e2_ref[ciclo].metricas
        ref = dict(color=st["color"], linestyle=estilo_ref[ciclo], linewidth=0.9)
        ax_a.axhline(m2.tse_pct, label=f"E2, {NOMES_CICLOS[ciclo]} (referência)", **ref)
        ax_b.axhline(m2.percolacao_incremental_mm, label=f"E2, {NOMES_CICLOS[ciclo]} (referência)", **ref)
    for ax, letra, rot_y in ((ax_a, "a", "TSE (%)"), (ax_b, "b", "Percolação incremental (mm)")):
        ax.set_xlabel("Lâmina fixa de E1, L (mm)")
        ax.set_ylabel(rot_y)
        ax.set_xticks(list(laminas))
        estilo.eixos_com_virgula(ax)
        estilo.rotulo_painel(ax, letra)
    handles, labels = ax_a.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.2, 1, 1))
    arquivos = estilo.salvar(fig, base, " | ".join(metadados))
    return {"arquivos": arquivos, "dados": dados}


def figura_seco_restrito(
    rodadas: Dict[str, Rodada],
    raw_mm: float,
    taw_mm: float,
    dir_figuras: str,
    raiz: str,
    metadados: Sequence[str],
) -> Dict[str, object]:
    estrategias = ("E1", "E2", "E3")
    ref = rodadas["E1"]
    n = len(ref.serie["v_l"])
    t_dias = [(k + 1) / 24.0 for k in range(n)]
    registros = []
    for k in range(n):
        linha = {"hora_local_inicio": ref.forcante.rotulos[k], "tempo_dias": t_dias[k]}
        for e in estrategias:
            linha[f"v_l_{e}"] = rodadas[e].serie["v_l"][k]
            linha[f"dr_mm_{e}"] = rodadas[e].serie["dr_mm"][k]
        registros.append((str(k), linha))
    base = os.path.join(dir_figuras, "figura2_seco_restrito")
    campos = ["hora_local_inicio", "tempo_dias"] + [f"v_l_{e}" for e in estrategias] + [f"dr_mm_{e}" for e in estrategias]
    dados = escrever_csv(base + "_dados.csv", raiz, campos, registros, list(metadados) + [
        f"RAW_mm={raw_mm:.6g}; TAW_mm={taw_mm:.6g}; tempo_dias = fim da hora, em dias desde 00:00 do dia 1"])

    fig, (ax_a, ax_b) = estilo.nova_figura(12.0, 2, 1, sharex=True)
    for i, e in enumerate(estrategias):
        st = dict(estilo.ESTILOS[e])
        marca = dict(markevery=(8 * i, 24), markersize=3.0, linewidth=0.8)
        ax_a.plot(t_dias, rodadas[e].serie["v_l"], label=e, **st, **marca)
        ax_b.plot(t_dias, rodadas[e].serie["dr_mm"], label=e, **st, **marca)
    for valor, nome in ((raw_mm, "RAW"), (taw_mm, "TAW")):
        ax_b.axhline(valor, color=estilo.COR_REFERENCIA, linewidth=0.7, linestyle=(0, (6, 2)))
        ax_b.text(t_dias[-1], valor, f" {nome}", va="center", ha="left", color="#333333")
    ax_a.set_ylabel("Volume no reservatório (L)")
    ax_b.set_ylabel("Depleção da zona radicular, Dr (mm)")
    ax_b.set_xlabel("Tempo desde o início do ciclo (d)")
    ax_b.set_xlim(0, t_dias[-1])
    ax_b.set_xticks(list(range(0, int(t_dias[-1]) + 1, 7)))
    ax_a.set_ylim(bottom=0)
    ax_b.set_ylim(bottom=0, top=taw_mm * 1.05)
    for ax, letra in ((ax_a, "a"), (ax_b, "b")):
        estilo.eixos_com_virgula(ax)
        estilo.rotulo_painel(ax, letra)
    ax_a.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.22))
    fig.tight_layout()
    arquivos = estilo.salvar(fig, base, " | ".join(metadados))
    return {"arquivos": arquivos, "dados": dados}
