"""
Geração das Figuras Científicas F1 a F5 em PNG (300 dpi, escala de cinza e padrões
distinguíveis sem cor, eixos com unidade, sem título interno) e exportação dos CSVs
correspondentes aos dados de cada figura (Parte 6).
"""

from __future__ import annotations
import csv
import os
from typing import Dict, Any, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_FIGURES_DIR = os.path.join(ROOT_DIR, "figuras")


def _salvar_csv_figura(caminho_csv: str, linhas: List[Dict[str, Any]]) -> str:
    os.makedirs(os.path.dirname(caminho_csv), exist_ok=True)
    fieldnames = list(linhas[0].keys()) if linhas else []
    with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(linhas)
    return caminho_csv


def _configurar_estilo_matplotlib() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9.5,
        "axes.labelsize": 10.0,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.0,
        "axes.edgecolor": "#222222",
        "axes.linewidth": 0.9,
        "grid.color": "#cccccc",
        "grid.linestyle": ":",
        "grid.linewidth": 0.6,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
    })


def gerar_f1_series_umidade(
    simulacoes_detalhadas: Dict[str, Any],
    theta_lim: float,
    theta_cc: float,
    theta_pmp: float,
    diretorio_figuras: str = DEFAULT_FIGURES_DIR,
    cenario_f1: str = "Restrito",
) -> List[Dict[str, str]]:
    """
    F1 — Série diária de θ1 e θ2 ao longo do ciclo, uma estratégia por painel (E1, E2, E3),
    com linha do limiar (θ_lim) e marcação dos eventos de irrigação. Uma figura por período.
    """
    arquivos: List[Dict[str, str]] = []
    estrategias = ["E1", "E2", "E3"]
    painel_tags = {"E1": "(a) Estratégia E1", "E2": "(b) Estratégia E2", "E3": "(c) Estratégia E3"}

    for periodo, sufixo in (
        ("Estacao_Chuvosa", "estacao_chuvosa"),
        ("Estacao_Seca", "estacao_seca"),
    ):
        fig, axes = plt.subplots(3, 1, figsize=(7.5, 7.2), sharex=True, sharey=True)
        linhas_csv: List[Dict[str, Any]] = []

        for idx_est, est in enumerate(estrategias):
            ax = axes[idx_est]
            chave = f"{periodo}__{cenario_f1}__{est}"
            hist = simulacoes_detalhadas[chave]["historico"]

            dias = [d.dia_idx for d in hist]
            th1 = [d.theta1_final for d in hist]
            th2 = [d.theta2_final for d in hist]
            irr_dias = [d.dia_idx for d in hist if d.acionou_irrigacao]
            irr_th1 = [d.theta1_final for d in hist if d.acionou_irrigacao]

            for d in hist:
                linhas_csv.append({
                    "periodo": periodo,
                    "cenario": cenario_f1,
                    "estrategia": est,
                    "dia_ciclo": d.dia_idx,
                    "data": d.data,
                    "theta1_cm3_cm3": round(d.theta1_final, 6),
                    "theta2_cm3_cm3": round(d.theta2_final, 6),
                    "theta_lim_cm3_cm3": round(theta_lim, 6),
                    "theta_cc_cm3_cm3": round(theta_cc, 6),
                    "theta_pmp_cm3_cm3": round(theta_pmp, 6),
                    "acionou_irrigacao": int(d.acionou_irrigacao),
                    "lamina_aplicada_mm": round(d.i_mm, 2),
                    "precipitacao_mm": round(d.p_mm, 2),
                })

            ax.plot(
                dias,
                th1,
                color="#111111",
                linestyle="-",
                linewidth=1.5,
                label=f"{painel_tags[est]} — Camada 1 (θ1, 0–20 cm)",
            )
            ax.plot(
                dias,
                th2,
                color="#666666",
                linestyle="--",
                linewidth=1.2,
                label="Camada 2 (θ2, 20–40 cm)",
            )
            ax.axhline(
                theta_lim,
                color="#333333",
                linestyle=":",
                linewidth=1.1,
                label=f"Limiar crítico θ_lim ({theta_lim:.3f} cm³/cm³)",
            )
            ax.axhline(
                theta_cc,
                color="#999999",
                linestyle="-.",
                linewidth=0.8,
                label=f"Capacidade de campo θ_cc ({theta_cc:.2f} cm³/cm³)",
            )
            if irr_dias:
                ax.scatter(
                    irr_dias,
                    irr_th1,
                    color="#000000",
                    marker="^",
                    s=28,
                    zorder=5,
                    label=f"Eventos de irrigação (n={len(irr_dias)})",
                )

            ax.set_ylabel("Umidade θ (cm³/cm³)")
            ax.set_ylim(max(0.12, theta_pmp - 0.015), theta_cc + 0.03)
            ax.set_xlim(1, 70)
            ax.grid(True)
            ax.legend(loc="lower left", ncol=2, frameon=True, edgecolor="#cccccc", framealpha=0.92)

        axes[-1].set_xlabel("Tempo do ciclo (dias)")
        fig.tight_layout()

        png_path = os.path.join(diretorio_figuras, f"F1_umidade_solo_{sufixo}.png")
        csv_path = os.path.join(diretorio_figuras, f"F1_umidade_solo_{sufixo}.csv")
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        _salvar_csv_figura(csv_path, linhas_csv)
        arquivos.append({"figura": f"F1_{sufixo}", "png": png_path, "csv": csv_path})

    return arquivos


def gerar_f2_sensibilidade_e1(
    sensibilidade_e1: List[Dict[str, Any]],
    metricas_comparativas: List[Dict[str, Any]],
    diretorio_figuras: str = DEFAULT_FIGURES_DIR,
) -> List[Dict[str, str]]:
    """
    F2 — Sensibilidade da E1: lâmina fixa no eixo x (5 a 30 mm), dois eixos y
    (conforto hídrico e D2_incremental), com a E2 como linha horizontal de referência.
    Uma figura por período.
    """
    arquivos: List[Dict[str, str]] = []
    cenarios = ["Abundante", "Moderado", "Restrito"]
    marcadores = {"Abundante": "o", "Moderado": "s", "Restrito": "^"}
    tons_cinza = {"Abundante": "#111111", "Moderado": "#444444", "Restrito": "#777777"}

    for periodo, sufixo in (
        ("Estacao_Chuvosa", "estacao_chuvosa"),
        ("Estacao_Seca", "estacao_seca"),
    ):
        fig, ax1 = plt.subplots(figsize=(7.4, 4.6))
        ax2 = ax1.twinx()
        linhas_csv: List[Dict[str, Any]] = []

        # Referência E2 no cenário Abundante (demanda plena sem restrição) e Restrito
        e2_abund = next(
            m
            for m in metricas_comparativas
            if m["periodo"] == periodo and m["cenario"] == "Abundante" and m["estrategia"] == "E2"
        )
        e2_rest = next(
            m
            for m in metricas_comparativas
            if m["periodo"] == periodo and m["cenario"] == "Restrito" and m["estrategia"] == "E2"
        )

        for cen in cenarios:
            sub = sorted(
                [r for r in sensibilidade_e1 if r["periodo"] == periodo and r["cenario"] == cen],
                key=lambda x: x["lamina_fixa_mm"],
            )
            xs = [r["lamina_fixa_mm"] for r in sub]
            ys_conf = [r["conforto_hidrico_pct"] for r in sub]
            ys_d2 = [r["d2_incremental_mm"] for r in sub]

            for r in sub:
                linhas_csv.append({
                    "periodo": periodo,
                    "cenario": cen,
                    "lamina_fixa_e1_mm": r["lamina_fixa_mm"],
                    "conforto_hidrico_e1_pct": r["conforto_hidrico_pct"],
                    "d2_incremental_e1_mm": r["d2_incremental_mm"],
                    "lamina_aplicada_e1_mm": r["lamina_total_mm"],
                    "lamina_nao_atendida_e1_mm": r["lamina_nao_atendida_mm"],
                    "e2_ref_abundante_conforto_pct": e2_abund["conforto_hidrico_pct"],
                    "e2_ref_abundante_d2_incremental_mm": e2_abund["d2_incremental_mm"],
                    "e2_ref_restrito_conforto_pct": e2_rest["conforto_hidrico_pct"],
                    "e2_ref_restrito_d2_incremental_mm": e2_rest["d2_incremental_mm"],
                })

            ax1.plot(
                xs,
                ys_conf,
                color=tons_cinza[cen],
                linestyle="-",
                marker=marcadores[cen],
                markersize=5.5,
                linewidth=1.5,
                label=f"Conforto E1 ({cen})",
            )
            ax2.plot(
                xs,
                ys_d2,
                color=tons_cinza[cen],
                linestyle="--",
                marker=marcadores[cen],
                markersize=5.0,
                 markerfacecolor="white",
                linewidth=1.2,
                label=f"D2_incremental E1 ({cen})",
            )

        # Linhas horizontais de referência da E2
        ax1.axhline(
            e2_abund["conforto_hidrico_pct"],
            color="#000000",
            linestyle=":",
            linewidth=1.2,
            label=f"Ref. Conforto E2 Abund./Mod. ({e2_abund['conforto_hidrico_pct']:.1f}%)",
        )
        ax2.axhline(
            e2_abund["d2_incremental_mm"],
            color="#555555",
            linestyle="-.",
            linewidth=1.0,
            label=f"Ref. D2_inc E2 Abund./Mod. ({e2_abund['d2_incremental_mm']:.1f} mm)",
        )

        ax1.set_xlabel("Lâmina fixa da estratégia E1 (mm)")
        ax1.set_ylabel("Conforto hídrico (%)")
        ax2.set_ylabel("Percolação incremental D2_incremental (mm)")
        ax1.set_xticks([5, 10, 15, 20, 25, 30])
        ax1.set_ylim(0, 105)
        ax1.grid(True)

        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax1.legend(
            h1 + h2,
            l1 + l2,
            loc="upper left",
            ncol=2,
            fontsize=7.3,
            frameon=True,
            edgecolor="#cccccc",
            framealpha=0.92,
        )

        fig.tight_layout()
        png_path = os.path.join(diretorio_figuras, f"F2_sensibilidade_e1_{sufixo}.png")
        csv_path = os.path.join(diretorio_figuras, f"F2_sensibilidade_e1_{sufixo}.csv")
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        _salvar_csv_figura(csv_path, linhas_csv)
        arquivos.append({"figura": f"F2_{sufixo}", "png": png_path, "csv": csv_path})

    return arquivos


def gerar_f3_dimensionamento_reservatorio(
    varredura_e3: List[Dict[str, Any]],
    diretorio_figuras: str = DEFAULT_FIGURES_DIR,
) -> List[Dict[str, str]]:
    """
    F3 — Dimensionamento: capacidade do reservatório no eixo x (L), conforto hídrico
    no eixo y (%), uma curva por intervalo de reabastecimento (3, 7 e 14 dias),
    linha horizontal no critério de 90%. Uma figura por período.
    """
    arquivos: List[Dict[str, str]] = []
    estilos = {
        3: ("#111111", "-", "o", "Reabastecimento a cada 3 dias"),
        7: ("#444444", "--", "s", "Reabastecimento a cada 7 dias"),
        14: ("#777777", "-.", "^", "Reabastecimento a cada 14 dias"),
    }

    for periodo, sufixo in (
        ("Estacao_Chuvosa", "estacao_chuvosa"),
        ("Estacao_Seca", "estacao_seca"),
    ):
        fig, ax = plt.subplots(figsize=(6.8, 4.4))
        linhas_csv: List[Dict[str, Any]] = []

        for interv in (3, 7, 14):
            sub = sorted(
                [
                    r
                    for r in varredura_e3
                    if r["periodo"] == periodo and r["intervalo_reabastecimento_dias"] == interv
                ],
                key=lambda x: x["capacidade_reservatorio_l"],
            )
            xs = [r["capacidade_reservatorio_l"] for r in sub]
            ys = [r["conforto_hidrico_pct"] for r in sub]
            cor, ls, mk, rotulo = estilos[interv]

            for r in sub:
                linhas_csv.append({
                    "periodo": periodo,
                    "intervalo_reabastecimento_dias": interv,
                    "capacidade_reservatorio_l": r["capacidade_reservatorio_l"],
                    "conforto_hidrico_pct": r["conforto_hidrico_pct"],
                    "criterio_90_pct": 90.0,
                    "atende_criterio_90": int(r["atende_conforto_90pct"]),
                    "lamina_aplicada_mm": r["lamina_total_mm"],
                    "d2_incremental_mm": r["d2_incremental_mm"],
                })

            ax.plot(
                xs,
                ys,
                color=cor,
                linestyle=ls,
                marker=mk,
                markersize=6.0,
                linewidth=1.5,
                label=rotulo,
            )

        ax.axhline(
            90.0,
            color="#000000",
            linestyle=":",
            linewidth=1.3,
            label="Critério de dimensionamento (90,0%)",
        )

        ax.set_xlabel("Capacidade do reservatório (L)")
        ax.set_ylabel("Conforto hídrico (%)")
        ax.set_xticks([250, 500, 750, 1000, 1250, 1500, 1750, 2000])
        ax.set_ylim(0, 105)
        ax.grid(True)
        ax.legend(loc="lower right", frameon=True, edgecolor="#cccccc", framealpha=0.92)

        fig.tight_layout()
        png_path = os.path.join(diretorio_figuras, f"F3_dimensionamento_{sufixo}.png")
        csv_path = os.path.join(diretorio_figuras, f"F3_dimensionamento_{sufixo}.csv")
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        _salvar_csv_figura(csv_path, linhas_csv)
        arquivos.append({"figura": f"F3_{sufixo}", "png": png_path, "csv": csv_path})

    return arquivos


def gerar_f4_barras_comparativas(
    metricas_comparativas: List[Dict[str, Any]],
    diretorio_figuras: str = DEFAULT_FIGURES_DIR,
) -> List[Dict[str, str]]:
    """
    F4 — Barras comparativas por estratégia: lâmina aplicada e D2_incremental
    lado a lado, agrupadas por cenário. Gera figuras individuais por período e
    uma figura combinada de dois painéis.
    """
    arquivos: List[Dict[str, str]] = []
    cenarios = ["Abundante", "Moderado", "Restrito"]
    estrategias = ["E1", "E2", "E3"]
    cores_lamina = {"E1": "#222222", "E2": "#666666", "E3": "#aaaaaa"}
    cores_d2 = {"E1": "#dddddd", "E2": "#eeeeee", "E3": "#ffffff"}
    hachuras_d2 = {"E1": "///", "E2": "...", "E3": "xxx"}

    linhas_csv_global: List[Dict[str, Any]] = []

    for periodo, sufixo in (
        ("Estacao_Chuvosa", "estacao_chuvosa"),
        ("Estacao_Seca", "estacao_seca"),
    ):
        fig, ax = plt.subplots(figsize=(7.4, 4.5))
        linhas_csv_per: List[Dict[str, Any]] = []

        x_base = np.arange(len(cenarios))
        largura = 0.12
        offsets = {
            ("E1", "I"): -2.5 * largura,
            ("E1", "D2"): -1.5 * largura,
            ("E2", "I"): -0.5 * largura,
            ("E2", "D2"): 0.5 * largura,
            ("E3", "I"): 1.5 * largura,
            ("E3", "D2"): 2.5 * largura,
        }

        for est in estrategias:
            vals_i = []
            vals_d2 = []
            for cen in cenarios:
                m = next(
                    r
                    for r in metricas_comparativas
                    if r["periodo"] == periodo and r["cenario"] == cen and r["estrategia"] == est
                )
                vals_i.append(m["lamina_total_mm"])
                vals_d2.append(m["d2_incremental_mm"])
                reg_csv = {
                    "periodo": periodo,
                    "cenario": cen,
                    "estrategia": est,
                    "lamina_aplicada_mm": m["lamina_total_mm"],
                    "d2_incremental_mm": m["d2_incremental_mm"],
                    "d2_total_mm": m["percolacao_acumulada_mm"],
                    "d2_chuva_mm": m["d2_chuva_mm"],
                    "eficiencia_incremental_pct": m["eficiencia_incremental_pct"],
                    "conforto_hidrico_pct": m["conforto_hidrico_pct"],
                }
                linhas_csv_per.append(reg_csv)
                linhas_csv_global.append(reg_csv)

            ax.bar(
                x_base + offsets[(est, "I")],
                vals_i,
                width=largura,
                color=cores_lamina[est],
                edgecolor="#000000",
                linewidth=0.8,
                label=f"{est} — Lâmina aplicada (mm)",
            )
            ax.bar(
                x_base + offsets[(est, "D2")],
                vals_d2,
                width=largura,
                color=cores_d2[est],
                edgecolor="#000000",
                hatch=hachuras_d2[est],
                linewidth=0.8,
                label=f"{est} — D2_incremental (mm)",
            )

        ax.set_xticks(x_base)
        ax.set_xticklabels([f"Cenário {c}" for c in cenarios])
        ax.set_xlabel("Cenário de disponibilidade hídrica")
        ax.set_ylabel("Lâmina acumulada no ciclo (mm)")
        ax.grid(True, axis="y")
        ax.legend(loc="upper right", ncol=2, frameon=True, edgecolor="#cccccc", framealpha=0.92)

        fig.tight_layout()
        png_path = os.path.join(diretorio_figuras, f"F4_barras_comparativas_{sufixo}.png")
        csv_path = os.path.join(diretorio_figuras, f"F4_barras_comparativas_{sufixo}.csv")
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        _salvar_csv_figura(csv_path, linhas_csv_per)
        arquivos.append({"figura": f"F4_{sufixo}", "png": png_path, "csv": csv_path})

    return arquivos


def gerar_f5_nivel_reservatorio_restrito(
    simulacoes_detalhadas: Dict[str, Any],
    diretorio_figuras: str = DEFAULT_FIGURES_DIR,
) -> List[Dict[str, str]]:
    """
    F5 — Nível do reservatório ao longo do tempo, uma linha por estratégia (E1, E2, E3),
    para o cenário Restrito (500 L / 14 dias) de cada período.
    """
    arquivos: List[Dict[str, str]] = []
    estilos = {
        "E1": ("#111111", "-", "o", "Estratégia E1 (Limiar fixo)"),
        "E2": ("#555555", "--", "s", "Estratégia E2 (Balanço hídrico)"),
        "E3": ("#888888", "-.", "^", "Estratégia E3 (Racionamento de reservatório)"),
    }

    for periodo, sufixo in (
        ("Estacao_Chuvosa", "estacao_chuvosa"),
        ("Estacao_Seca", "estacao_seca"),
    ):
        fig, ax = plt.subplots(figsize=(7.4, 4.3))
        linhas_csv: List[Dict[str, Any]] = []

        for est in ("E1", "E2", "E3"):
            chave = f"{periodo}__Restrito__{est}"
            hist = simulacoes_detalhadas[chave]["historico"]
            dias = [d.dia_idx for d in hist]
            vols = [d.volume_reservatorio_final_l for d in hist]
            cor, ls, mk, rotulo = estilos[est]

            for d in hist:
                linhas_csv.append({
                    "periodo": periodo,
                    "cenario": "Restrito",
                    "estrategia": est,
                    "dia_ciclo": d.dia_idx,
                    "data": d.data,
                    "volume_reservatorio_inicial_l": round(d.volume_reservatorio_inicial_l, 2),
                    "volume_reservatorio_final_l": round(d.volume_reservatorio_final_l, 2),
                    "reabastecido": int(d.reabastecido),
                    "lamina_desejada_mm": round(d.i_desejada_mm, 2),
                    "lamina_aplicada_mm": round(d.i_mm, 2),
                    "lamina_nao_atendida_mm": round(d.i_nao_atendida_mm, 2),
                    "reservatorio_vazio": int(d.reservatorio_vazio),
                })

            ax.plot(
                dias,
                vols,
                color=cor,
                linestyle=ls,
                marker=mk,
                markevery=3,
                markersize=4.5,
                linewidth=1.4,
                label=rotulo,
            )

        ax.set_xlabel("Tempo do ciclo (dias)")
        ax.set_ylabel("Volume disponível no reservatório (L)")
        ax.set_xlim(1, 70)
        ax.set_ylim(-15, 535)
        ax.grid(True)
        ax.legend(loc="upper right", frameon=True, edgecolor="#cccccc", framealpha=0.92)

        fig.tight_layout()
        png_path = os.path.join(diretorio_figuras, f"F5_nivel_reservatorio_restrito_{sufixo}.png")
        csv_path = os.path.join(diretorio_figuras, f"F5_nivel_reservatorio_restrito_{sufixo}.csv")
        fig.savefig(png_path, dpi=300, bbox_inches="tight")
        plt.close(fig)
        _salvar_csv_figura(csv_path, linhas_csv)
        arquivos.append({"figura": f"F5_{sufixo}", "png": png_path, "csv": csv_path})

    return arquivos


def gerar_todas_figuras(
    simulacoes_detalhadas: Dict[str, Any],
    sensibilidade_e1: List[Dict[str, Any]],
    varredura_e3: List[Dict[str, Any]],
    metricas_comparativas: List[Dict[str, Any]],
    theta_lim: float,
    theta_cc: float,
    theta_pmp: float,
    diretorio_figuras: str = DEFAULT_FIGURES_DIR,
) -> List[Dict[str, str]]:
    """Gera todas as figuras F1 a F5 (PNG 300 dpi + CSV de dados de cada uma)."""
    _configurar_estilo_matplotlib()
    os.makedirs(diretorio_figuras, exist_ok=True)
    gerados: List[Dict[str, str]] = []
    gerados.extend(
        gerar_f1_series_umidade(
            simulacoes_detalhadas, theta_lim, theta_cc, theta_pmp, diretorio_figuras
        )
    )
    gerados.extend(
        gerar_f2_sensibilidade_e1(sensibilidade_e1, metricas_comparativas, diretorio_figuras)
    )
    gerados.extend(gerar_f3_dimensionamento_reservatorio(varredura_e3, diretorio_figuras))
    gerados.extend(gerar_f4_barras_comparativas(metricas_comparativas, diretorio_figuras))
    gerados.extend(
        gerar_f5_nivel_reservatorio_restrito(simulacoes_detalhadas, diretorio_figuras)
    )
    return gerados
