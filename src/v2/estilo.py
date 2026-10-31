"""
Estilo único das figuras do v2.

Liberation Serif (compatível com Times New Roman) em 10 pt; largura de 15 cm; sem título
dentro da figura; painéis (a) e (b); vírgula decimal nos eixos; PNG 300 dpi e PDF.
Toda série é distinguível por cor, marcador e tipo de linha, para funcionar em preto e branco.
"""

from __future__ import annotations

import os
from typing import Dict, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from src.v2.formatacao import num  # noqa: E402


FONTE = "Liberation Serif"
TAMANHO_FONTE_PT = 10
LARGURA_CM = 15.0
CM = 1 / 2.54
DPI = 300

ESTILOS: Dict[str, Dict[str, object]] = {
    "E1": {"color": "#1F3A5F", "linestyle": "-", "marker": "o"},
    "E2": {"color": "#D9822B", "linestyle": "--", "marker": "s"},
    "E3": {"color": "#555555", "linestyle": ":", "marker": "^"},
    "chuvoso": {"color": "#1F3A5F", "linestyle": "-", "marker": "o"},
    "seco": {"color": "#D9822B", "linestyle": "--", "marker": "s"},
}
COR_REFERENCIA = "#888888"


def aplicar_estilo() -> None:
    nomes = {f.name for f in font_manager.fontManager.ttflist}
    if FONTE not in nomes:
        raise RuntimeError(
            f"Fonte {FONTE} não encontrada. Instale o pacote fonts-liberation (Debian/Ubuntu) "
            "para gerar as figuras no padrão do artigo."
        )
    plt.rcParams.update({
        "font.family": FONTE,
        "font.size": TAMANHO_FONTE_PT,
        "axes.labelsize": TAMANHO_FONTE_PT,
        "xtick.labelsize": TAMANHO_FONTE_PT,
        "ytick.labelsize": TAMANHO_FONTE_PT,
        "legend.fontsize": TAMANHO_FONTE_PT,
        "axes.titlesize": TAMANHO_FONTE_PT,
        "axes.linewidth": 0.6,
        "lines.linewidth": 1.0,
        "lines.markersize": 4.0,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.formatter.use_locale": False,
        "svg.hashsalt": "pic-fapema-v2",
    })


def formatador_virgula(casas: Optional[int] = None) -> FuncFormatter:
    """Rótulos de eixo com vírgula decimal e ponto de milhar; `casas=None` escolhe o mínimo necessário."""
    def _fmt(x, _pos):
        if casas is not None:
            return num(x, casas)
        for c in range(0, 4):
            if abs(round(x, c) - x) < 1e-9:
                return num(x, c)
        return num(x, 3)
    return FuncFormatter(_fmt)


def eixos_com_virgula(ax, casas_x: Optional[int] = None, casas_y: Optional[int] = None) -> None:
    ax.xaxis.set_major_formatter(formatador_virgula(casas_x))
    ax.yaxis.set_major_formatter(formatador_virgula(casas_y))


def rotulo_painel(ax, letra: str) -> None:
    ax.text(-0.02, 1.02, f"({letra})", transform=ax.transAxes, ha="right", va="bottom")


def nova_figura(altura_cm: float, nlinhas: int = 1, ncolunas: int = 1, **kwargs):
    aplicar_estilo()
    return plt.subplots(nlinhas, ncolunas, figsize=(LARGURA_CM * CM, altura_cm * CM), **kwargs)


def salvar(fig, caminho_sem_extensao: str, descricao: str) -> Dict[str, str]:
    """Grava PNG (300 dpi) e PDF sem data de criação, com a descrição (parâmetros) nos metadados."""
    os.makedirs(os.path.dirname(caminho_sem_extensao), exist_ok=True)
    png, pdf = caminho_sem_extensao + ".png", caminho_sem_extensao + ".pdf"
    fig.savefig(png, dpi=DPI, metadata={"Description": descricao})
    fig.savefig(pdf, metadata={"CreationDate": None, "ModDate": None, "Subject": descricao})
    plt.close(fig)
    return {"png": png, "pdf": pdf}
