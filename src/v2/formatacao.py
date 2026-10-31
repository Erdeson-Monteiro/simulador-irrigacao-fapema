"""
Formatação pt-BR e gravação de tabelas (CSV + Markdown) do v2.

- CSV: separador ',', ponto decimal, valores com até 6 casas; começa com linhas '# '
  de metadados (descrição e parâmetros), como o cabeçalho dos arquivos do INMET. Nada de
  data, hora, caminho absoluto ou hash de commit: o mesmo cálculo gera os mesmos bytes.
- Markdown: ponto de milhar e vírgula decimal (1.000; 8,4), uma casa em mm e %, inteiros em
  contagens, abreviaturas definidas em nota.
"""

from __future__ import annotations

import csv
import io
import math
import os
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


TRACO = "—"


def num(x: Optional[float], casas: int = 1, milhar: bool = True) -> str:
    """Número em pt-BR: 1.234,5. None ou NaN viram '—'."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return TRACO
    if casas == 0:
        x = round(x)
    texto = f"{x:,.{casas}f}" if milhar else f"{x:.{casas}f}"
    texto = texto.replace(",", "\u0000").replace(".", ",").replace("\u0000", ".")
    if texto.startswith("-") and float(texto.replace(".", "").replace(",", ".")) == 0:
        texto = texto[1:]  # evita "-0,0"
    return texto


def inteiro(x: Optional[int]) -> str:
    return TRACO if x is None else num(x, 0)


def pct(x: Optional[float], casas: int = 1) -> str:
    return TRACO if x is None else f"{num(x, casas)}%"


def data_br(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def data_curta(d: date) -> str:
    return d.strftime("%d/%m")


def valor_csv(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if math.isnan(v):
            return ""
        texto = f"{v:.6f}"
        return "0.000000" if texto == "-0.000000" else texto
    if isinstance(v, date):
        return v.isoformat()
    return str(v)


@dataclass
class TabelaCSV:
    """Tabela gravada: caminho relativo e número da linha física de cada registro (por chave)."""
    caminho_relativo: str
    campos: List[str]
    linhas: Dict[str, int] = field(default_factory=dict)
    valores: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def ref(self, chave: str, coluna: str) -> Tuple[str, int, str]:
        if coluna not in self.campos:
            raise KeyError(f"{self.caminho_relativo}: coluna {coluna!r} não existe")
        return self.caminho_relativo, self.linhas[chave], coluna

    def valor(self, chave: str, coluna: str) -> str:
        return self.valores[chave][coluna]


def escrever_csv(
    caminho: str,
    raiz: str,
    campos: Sequence[str],
    registros: Iterable[Tuple[str, Dict[str, object]]],
    metadados: Sequence[str] = (),
) -> TabelaCSV:
    """
    Grava o CSV e devolve, para cada chave, a linha física (contando as linhas de metadados),
    para que outros documentos citem a origem exata de cada número.
    """
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    tabela = TabelaCSV(os.path.relpath(caminho, raiz).replace(os.sep, "/"), list(campos))
    buffer = io.StringIO()
    escritor = csv.writer(buffer, lineterminator="\n")
    linha = 0
    for m in metadados:
        buffer.write(f"# {m}\n")
        linha += 1
    escritor.writerow(campos)
    linha += 1
    for chave, registro in registros:
        texto = [valor_csv(registro.get(c)) for c in campos]
        escritor.writerow(texto)
        linha += 1
        if chave in tabela.linhas:
            raise ValueError(f"Chave repetida em {tabela.caminho_relativo}: {chave}")
        tabela.linhas[chave] = linha
        tabela.valores[chave] = dict(zip(campos, texto))
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        f.write(buffer.getvalue())
    return tabela


def ler_csv_com_metadados(caminho: str) -> Tuple[List[str], List[Dict[str, str]]]:
    """Lê um CSV do v2 ignorando as linhas '# '."""
    with open(caminho, encoding="utf-8", newline="") as f:
        linhas = [l for l in f if not l.startswith("#")]
    leitor = csv.DictReader(linhas)
    return list(leitor.fieldnames or []), list(leitor)


def tabela_markdown(
    colunas: Sequence[str],
    linhas: Sequence[Sequence[str]],
    alinhamento: Optional[Sequence[str]] = None,
    titulo: Optional[str] = None,
    notas: Sequence[str] = (),
) -> str:
    """Tabela Markdown; `alinhamento` com 'e' (esquerda) ou 'd' (direita) por coluna."""
    alinhamento = alinhamento or ["e"] + ["d"] * (len(colunas) - 1)
    sep = ["---:" if a == "d" else "---" for a in alinhamento]
    partes = []
    if titulo:
        partes += [titulo, ""]
    partes.append("| " + " | ".join(colunas) + " |")
    partes.append("|" + "|".join(sep) + "|")
    for l in linhas:
        partes.append("| " + " | ".join(l) + " |")
    if notas:
        partes.append("")
        partes += [f"{n}  " for n in notas[:-1]] + [notas[-1]]
    return "\n".join(partes) + "\n"
