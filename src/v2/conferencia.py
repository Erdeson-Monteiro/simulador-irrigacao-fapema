"""
Conferência dos resultados do v2.

- `conferir_numeros`: cada número de NUMEROS_ARTIGO.md é relido na linha e na coluna citadas
  do CSV, reformatado com as mesmas casas decimais e comparado com o valor do documento.
- `conferir_checksums`: o SHA-256 de cada CSV bate com CHECKSUMS.txt, e todo CSV está listado
  (as séries da varredura, fora do git, só são conferidas se existirem).
- `pendencias`: tudo o que ficou marcado `[A CONFIRMAR PELO AUTOR]` no projeto.
"""

from __future__ import annotations

import csv
from datetime import date
import hashlib
import os
import re
from typing import Dict, List, Tuple

from src.v2.formatacao import num
from src.v2.inmet import ROOT_DIR


PENDENTE = "[A CONFIRMAR PELO AUTOR]"
_LINHA = re.compile(r"^\| (\d+) \| (.+?) \| (.+?) \| (.+) \|$")
_FONTE_CSV = re.compile(r"^`([^`]+\.csv):(\d+)` \(`([^`]+)`\)$")
_NUMERO = re.compile(r"^([+-]?)(\d[\d.]*)(?:,(\d+))?(.*)$")
_DATA_BR = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def _ler_linha_csv(caminho: str, linha: int, coluna: str) -> str:
    with open(caminho, encoding="utf-8", newline="") as f:
        linhas = f.read().split("\n")
    cabecalho = next(l for l in linhas if not l.startswith("#"))
    campos = next(csv.reader([cabecalho]))
    if coluna not in campos:
        raise KeyError(f"coluna {coluna!r} não existe")
    valores = next(csv.reader([linhas[linha - 1]]))
    return valores[campos.index(coluna)]


def _confere(valor: str, bruto: str) -> bool:
    if valor == PENDENTE:
        return bruto in ("", PENDENTE)
    m = _DATA_BR.match(valor)
    if m:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat() == bruto
    m = _NUMERO.match(valor)
    try:
        x = float(bruto)
    except ValueError:
        return valor == bruto
    if not m:
        return False
    sinal, _inteiro, decimais, sufixo = m.groups()
    casas = len(decimais) if decimais else 0
    esperado = num(x, casas)
    if sinal == "+":
        esperado = "+" + esperado if x > 0 else esperado
    return (sinal + m.group(2) + ("," + decimais if decimais else "")) == esperado and sufixo == sufixo.lstrip("0123456789,.")


def conferir_numeros(dir_resultados: str) -> Tuple[int, List[str]]:
    """Devolve (quantidade conferida, lista de divergências)."""
    erros: List[str] = []
    n = 0
    with open(os.path.join(dir_resultados, "NUMEROS_ARTIGO.md"), encoding="utf-8") as f:
        linhas = f.read().splitlines()
    with open(os.path.join(dir_resultados, "AMBIENTE.md"), encoding="utf-8") as f:
        ambiente = f.read()
    for texto in linhas:
        m = _LINHA.match(texto)
        if not m:
            continue
        num_item, descricao, valor, fonte = m.groups()
        n += 1
        fm = _FONTE_CSV.match(fonte)
        if fm:
            arquivo, linha, coluna = fm.group(1), int(fm.group(2)), fm.group(3)
            caminho = os.path.join(dir_resultados, arquivo)
            try:
                bruto = _ler_linha_csv(caminho, linha, coluna)
            except (OSError, KeyError, IndexError, StopIteration) as exc:
                erros.append(f"nº {num_item} ({descricao}): fonte {fonte} inválida: {exc}")
                continue
            if not _confere(valor, bruto):
                erros.append(f"nº {num_item} ({descricao}): documento diz {valor!r}, {arquivo}:{linha} ({coluna}) tem {bruto!r}")
        elif fonte == "`AMBIENTE.md`":
            if valor.replace(" s", "") not in ambiente:
                erros.append(f"nº {num_item} ({descricao}): {valor!r} não aparece em AMBIENTE.md")
        elif fonte.startswith("arquivo ausente"):
            if valor != PENDENTE:
                erros.append(f"nº {num_item} ({descricao}): arquivo ausente, mas o valor não está pendente")
        else:
            erros.append(f"nº {num_item} ({descricao}): fonte não reconhecida: {fonte}")
    return n, erros


# Séries que ficam fora do git (.gitignore) e são recriadas pelo pipeline.
SERIES_RECRIADAS = "series/varredura/"


def conferir_checksums(dir_resultados: str) -> Tuple[int, List[str], int]:
    """
    (CSVs registrados, divergências, CSVs não conferidos). Num clone limpo a pasta
    `series/varredura/` não existe, e os arquivos dela ficam sem conferir; se a pasta existe,
    todos são conferidos.
    """
    erros: List[str] = []
    registrados: Dict[str, str] = {}
    with open(os.path.join(dir_resultados, "CHECKSUMS.txt"), encoding="utf-8") as f:
        for linha in f:
            h, rel = linha.rstrip("\n").split("  ", 1)
            registrados[rel] = h
    encontrados = set()
    for raiz, _d, arquivos in os.walk(dir_resultados):
        for a in arquivos:
            if a.endswith(".csv"):
                rel = os.path.relpath(os.path.join(raiz, a), dir_resultados).replace(os.sep, "/")
                encontrados.add(rel)
                with open(os.path.join(raiz, a), "rb") as fb:
                    h = hashlib.sha256(fb.read()).hexdigest()
                if registrados.get(rel) != h:
                    erros.append(f"{rel}: SHA-256 {h} não confere com CHECKSUMS.txt ({registrados.get(rel)})")
    sem_recriadas = not os.path.isdir(os.path.join(dir_resultados, *SERIES_RECRIADAS.strip("/").split("/")))
    nao_conferidos = 0
    for rel in sorted(set(registrados) - encontrados):
        if sem_recriadas and rel.startswith(SERIES_RECRIADAS):
            nao_conferidos += 1
        else:
            erros.append(f"{rel}: listado em CHECKSUMS.txt, mas não existe")
    return len(registrados), erros, nao_conferidos


GRUPOS_PENDENCIAS = (  # chave procurada (sem distinção de maiúsculas) na linha e no título da seção
    ("tabela 19", "Página da Tabela 19 do FAO-56 (θcc e θpmp do solo franco), conferida no PDF"),
    ("marouelli", "Página de Marouelli et al. (2008) com a profundidade da zona radicular da alface (z₁)"),
    ("normal", "Normal climatológica 1991–2020 de Balsas (planilha do INMET ainda não baixada)"),
    ("2024", "Arquivos de 2024 e 2025 da A204 (zips do INMET ainda não baixados)"),
    ("2025", "Arquivos de 2024 e 2025 da A204 (zips do INMET ainda não baixados)"),
)


def pendencias(raiz: str = ROOT_DIR, dir_resultados: str = None) -> List[Tuple[str, int, str]]:
    """
    Linhas com `[A CONFIRMAR PELO AUTOR]` nos documentos e nas saídas (README, docs/, tabelas e
    relatório do v1 em resultados/v1/, resultados do v2). O código-fonte, que só produz a marcação,
    fica de fora, assim como menções explicativas entre crases.
    """
    dir_resultados = dir_resultados or os.path.join(raiz, "resultados", "v2")
    alvos: List[Tuple[str, str]] = []
    for nome in ("README.md", os.path.join("resultados", "v1", "relatorio_final.md")):
        alvos.append((os.path.join(raiz, nome), nome.replace(os.sep, "/")))
    for pasta in ("docs", os.path.join("resultados", "v1", "tabelas")):
        base = os.path.join(raiz, pasta)
        if os.path.isdir(base):
            alvos += [(os.path.join(base, a), f"{pasta}/{a}".replace(os.sep, "/")) for a in sorted(os.listdir(base))]
    if os.path.isdir(dir_resultados):
        for r, _d, arquivos in os.walk(dir_resultados):
            if "series" in os.path.relpath(r, dir_resultados).split(os.sep):
                continue
            for a in sorted(arquivos):
                rel = os.path.relpath(os.path.join(r, a), dir_resultados).replace(os.sep, "/")
                alvos.append((os.path.join(r, a), f"resultados/v2/{rel}"))
    achados = []
    for caminho, rotulo in sorted(alvos, key=lambda x: x[1]):
        if not os.path.isfile(caminho) or not caminho.endswith((".md", ".csv")) or rotulo.endswith("PENDENCIAS.md"):
            continue
        contexto = rotulo
        with open(caminho, encoding="utf-8", errors="replace") as f:
            for i, linha in enumerate(f, 1):
                if linha.startswith(("#", "**")):
                    contexto = linha.strip()
                if PENDENTE in linha and f"`{PENDENTE}`" not in linha:
                    achados.append((rotulo, i, f"{linha.strip()} ⟨{contexto}⟩"))
    return achados


def agrupar_pendencias(achados: List[Tuple[str, int, str]]) -> Dict[str, List[Tuple[str, int, str]]]:
    grupos: Dict[str, List[Tuple[str, int, str]]] = {}
    for item in achados:
        titulo = next((t for chave, t in GRUPOS_PENDENCIAS if chave in item[2].lower()), "Outros")
        grupos.setdefault(titulo, []).append(item)
    return grupos


def markdown_pendencias(achados: List[Tuple[str, int, str]]) -> str:
    grupos = agrupar_pendencias(achados)
    partes = [
        "# Pendências para o autor",
        "",
        f"Tudo o que ficou marcado `{PENDENTE}` nos documentos e nas saídas, agrupado por assunto "
        f"({len(grupos)} assuntos, {len(achados)} ocorrências). Nenhum desses valores foi estimado. "
        "Gerado pelo pipeline; a mesma lista sai em `python3 main.py conferir`.",
        "",
    ]
    for titulo, itens in grupos.items():
        partes += [f"## {titulo}", ""]
        partes += [f"- `{arquivo}:{linha}`" for arquivo, linha, _ in itens]
        partes.append("")
    return "\n".join(partes)


CAMINHOS_DO_CODIGO = ("main.py", "requirements.txt", "src", os.path.join("data", "raw"))


def impressao_digital_do_codigo(raiz: str = ROOT_DIR) -> str:
    """SHA-256 dos arquivos que definem os resultados (código, dependências e dados brutos), em ordem."""
    arquivos = []
    for item in CAMINHOS_DO_CODIGO:
        caminho = os.path.join(raiz, item)
        if os.path.isfile(caminho):
            arquivos.append(caminho)
        for r, dirs, nomes in os.walk(caminho):
            dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", "downloads"))
            arquivos += [os.path.join(r, n) for n in sorted(nomes) if not n.endswith(".pyc")]
    h = hashlib.sha256()
    for caminho in sorted(arquivos, key=lambda c: os.path.relpath(c, raiz)):
        with open(caminho, "rb") as f:
            conteudo = hashlib.sha256(f.read()).hexdigest()
        h.update(f"{os.path.relpath(caminho, raiz).replace(os.sep, '/')}\0{conteudo}\n".encode())
    return h.hexdigest()


def conferir_ambiente(dir_resultados: str, raiz: str = ROOT_DIR) -> Tuple[bool, str, str]:
    """(confere?, impressão gravada em AMBIENTE.md, impressão do código atual)."""
    with open(os.path.join(dir_resultados, "AMBIENTE.md"), encoding="utf-8") as f:
        m = re.search(r"Impressão digital do código[^|]*\| `([0-9a-f]{64})`", f.read())
    gravada = m.group(1) if m else ""
    atual = impressao_digital_do_codigo(raiz)
    return gravada == atual, gravada, atual
