"""
Dados externos do v2: normal climatológica 1991–2020 e arquivos da
A204 de 2024 e 2025. Nada aqui baixa arquivos nem estima valores: quando um arquivo falta,
o programa diz a URL exata e a pasta onde colocá-lo.

Passo a passo para o autor:
  1. baixar `Normal-Climatologica-PREC.xlsx` para `data/raw/normais/`;
  2. baixar `2024.zip` e `2025.zip` para `data/raw/downloads/` (pasta fora do git);
  3. rodar `python3 main.py dados --preparar`: extrai só o arquivo da A204 de cada zip
     para `data/raw/` e registra o SHA-256 de tudo em `data/raw/SHA256SUMS`;
  4. rodar `python3 main.py pipeline`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import math
import os
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from typing import Dict, List, Optional, Sequence, Tuple

from src.v2 import fao56
from src.v2.clima import FUSO_LOCAL, LIMIAR_RA_NOITE_MJ, LZ_UTC_GRAUS, VARIAVEIS_OBRIGATORIAS
from src.v2.inmet import (
    DIR_RAW,
    REGISTRO_SHA256,
    ROOT_DIR,
    EstacaoINMET,
    RegistroINMET,
    ler_arquivo_inmet,
    ler_registro_sha256,
    sha256_arquivo,
)


PAGINA_NORMAIS = "https://portal.inmet.gov.br/normais"
URL_NORMAL_PREC = "https://portal.inmet.gov.br/uploads/normais/Normal-Climatologica-PREC.xlsx"
URL_DADOS_ANO = "https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip"
DIR_NORMAIS = os.path.join(DIR_RAW, "normais")
DIR_DOWNLOADS = os.path.join(DIR_RAW, "downloads")
ARQUIVO_NORMAL_PREC = os.path.join(DIR_NORMAIS, "Normal-Climatologica-PREC.xlsx")
ANOS_VIZINHOS = (2024, 2025)
REFERENCIA_NORMAL = (
    "INSTITUTO NACIONAL DE METEOROLOGIA (Brasil). Normais climatológicas do Brasil: período "
    "1991-2020. Organização de Marcia dos Santos Seabra e Edmundo Wallace Monteiro Lucas. "
    "Ed. digital. Brasília, DF: INMET, 2022."
)

# Pesos por mês para a normal de cada janela (soma proporcional por dias).
PESOS_JANELA_NORMAL: Dict[str, Dict[int, float]] = {
    "chuvoso": {1: 17 / 31, 2: 28 / 28, 3: 25 / 31},
    "seco": {7: 1.0, 8: 1.0, 9: 8 / 30},
}

MESES = {
    1: ("jan", "janeiro"), 2: ("fev", "fevereiro"), 3: ("mar", "marco"), 4: ("abr", "abril"),
    5: ("mai", "maio"), 6: ("jun", "junho"), 7: ("jul", "julho"), 8: ("ago", "agosto"),
    9: ("set", "setembro"), 10: ("out", "outubro"), 11: ("nov", "novembro"), 12: ("dez", "dezembro"),
}


class FormatoNaoReconhecido(ValueError):
    """Planilha ou arquivo fora do formato esperado: o programa para em vez de adivinhar."""


def _rel(caminho: str) -> str:
    return os.path.relpath(caminho, ROOT_DIR).replace(os.sep, "/")


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").lower().strip()


# ---------------------------------------------------------------------------
# Registro de SHA-256
# ---------------------------------------------------------------------------

def registrar_sha256(caminho: str, comentario: Optional[str] = None) -> str:
    """Acrescenta o arquivo ao registro; se ele já estiver lá com outro hash, é erro."""
    nome = os.path.relpath(caminho, DIR_RAW).replace(os.sep, "/")
    hash_hex = sha256_arquivo(caminho)
    registrado = ler_registro_sha256().get(nome)
    if registrado == hash_hex:
        return hash_hex
    if registrado is not None:
        raise FormatoNaoReconhecido(f"{nome} já está registrado com outro SHA-256 ({registrado}).")
    with open(REGISTRO_SHA256, "a", encoding="utf-8") as f:
        if comentario:
            f.write(f"# {comentario}\n")
        f.write(f"{hash_hex}  {nome}\n")
    return hash_hex


# ---------------------------------------------------------------------------
# Leitura mínima de xlsx (só biblioteca padrão)
# ---------------------------------------------------------------------------

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _indice_coluna(ref: str) -> int:
    letras = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for c in letras:
        n = n * 26 + (ord(c) - 64)
    return n - 1


def ler_xlsx(caminho: str) -> List[List[object]]:
    """Linhas da primeira planilha, com texto como str e números como float."""
    with zipfile.ZipFile(caminho) as z:
        compartilhadas: List[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            raiz = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in raiz.findall("m:si", _NS):
                compartilhadas.append("".join(t.text or "" for t in si.iter(f"{{{_NS['m']}}}t")))
        planilhas = sorted(n for n in z.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", n))
        if not planilhas:
            raise FormatoNaoReconhecido(f"{caminho}: nenhuma planilha encontrada.")
        raiz = ET.fromstring(z.read(planilhas[0]))
    linhas: List[List[object]] = []
    for row in raiz.iter(f"{{{_NS['m']}}}row"):
        valores: Dict[int, object] = {}
        for c in row.findall("m:c", _NS):
            tipo, ref = c.get("t"), c.get("r")
            v = c.find("m:v", _NS)
            if tipo == "s" and v is not None:
                valor: object = compartilhadas[int(v.text)]
            elif tipo == "inlineStr":
                valor = "".join(t.text or "" for t in c.iter(f"{{{_NS['m']}}}t"))
            elif v is not None and v.text is not None:
                try:
                    valor = float(v.text)
                except ValueError:
                    valor = v.text
            else:
                continue
            valores[_indice_coluna(ref)] = valor
        if valores:
            linha = [None] * (max(valores) + 1)
            for i, val in valores.items():
                linha[i] = val
            linhas.append(linha)
    return linhas


def _numero(valor: object) -> Optional[float]:
    if isinstance(valor, float):
        return valor
    if isinstance(valor, str):
        s = valor.strip().replace(".", "").replace(",", ".") if "," in valor else valor.strip()
        try:
            return float(s)
        except ValueError:
            return None
    return None


@dataclass
class NormalEstacao:
    nome: str
    codigo: Optional[str]
    uf: Optional[str]
    mensal_mm: Dict[int, Optional[float]]
    linha_planilha: int
    arquivo: str
    sha256: str

    def janela(self, pesos: Dict[int, float]) -> Optional[float]:
        if any(self.mensal_mm.get(m) is None for m in pesos):
            return None
        return sum(self.mensal_mm[m] * w for m, w in pesos.items())


def ler_normal_balsas(caminho: str = ARQUIVO_NORMAL_PREC) -> NormalEstacao:
    """
    Localiza a linha de BALSAS (MA) pelo nome e lê os 12 meses pelo cabeçalho. Qualquer
    ambiguidade (nenhuma ou mais de uma linha, cabeçalho sem os 12 meses) é erro.
    """
    if not os.path.exists(caminho):
        raise FileNotFoundError(caminho)
    linhas = ler_xlsx(caminho)

    idx_cab, col_mes = None, {}
    for i, linha in enumerate(linhas):
        achados = {}
        for j, cel in enumerate(linha):
            if isinstance(cel, str):
                t = _sem_acento(cel)
                for m, (abrev, nome) in MESES.items():
                    if t in (abrev, nome):
                        achados[m] = j
        if len(achados) == 12:
            idx_cab, col_mes = i, achados
            break
    if idx_cab is None:
        raise FormatoNaoReconhecido(f"{caminho}: cabeçalho com os 12 meses não encontrado.")

    cabecalho = [(_sem_acento(c) if isinstance(c, str) else "") for c in linhas[idx_cab]]
    col_uf = next((j for j, c in enumerate(cabecalho) if c == "uf"), None)
    col_codigo = next((j for j, c in enumerate(cabecalho) if c.startswith("codigo")), None)

    candidatas = []
    for i in range(idx_cab + 1, len(linhas)):
        linha = linhas[i]
        textos = [_sem_acento(c) for c in linha if isinstance(c, str)]
        if not any(re.search(r"\bbalsas\b", t) for t in textos):
            continue
        uf = linha[col_uf] if col_uf is not None and col_uf < len(linha) else None
        if uf is not None and _sem_acento(str(uf)) != "ma":
            continue
        candidatas.append(i)
    if len(candidatas) != 1:
        raise FormatoNaoReconhecido(
            f"{caminho}: esperada uma linha de BALSAS (MA); encontradas {len(candidatas)}."
        )
    i = candidatas[0]
    linha = linhas[i]
    nome = next(c for c in linha if isinstance(c, str) and re.search(r"\bbalsas\b", _sem_acento(c)))
    mensal = {m: _numero(linha[j]) if j < len(linha) else None for m, j in col_mes.items()}
    codigo = linha[col_codigo] if col_codigo is not None and col_codigo < len(linha) else None
    return NormalEstacao(
        nome=str(nome).strip(),
        codigo=None if codigo is None else str(codigo).replace(".0", ""),
        uf=None if col_uf is None else str(linha[col_uf]),
        mensal_mm=mensal,
        linha_planilha=i + 1,
        arquivo=_rel(caminho),
        sha256=sha256_arquivo(caminho),
    )


# ---------------------------------------------------------------------------
# Anos vizinhos: extração do arquivo da A204 e completude
# ---------------------------------------------------------------------------

def arquivo_a204_do_ano(ano: int) -> Optional[str]:
    padrao = re.compile(rf"INMET_.*_A204_.*_01-01-{ano}_A_.*\.CSV$", re.IGNORECASE)
    for nome in sorted(os.listdir(DIR_RAW)):
        if padrao.match(nome):
            return os.path.join(DIR_RAW, nome)
    return None


def extrair_a204_do_zip(caminho_zip: str, destino: str = DIR_RAW) -> str:
    """Extrai só o arquivo da A204 (pelo nome, sem subpastas) e devolve o caminho gravado."""
    with zipfile.ZipFile(caminho_zip) as z:
        membros = [n for n in z.namelist() if re.search(r"_A204_.*\.CSV$", os.path.basename(n), re.IGNORECASE)]
        if len(membros) != 1:
            raise FormatoNaoReconhecido(f"{caminho_zip}: esperado 1 arquivo da A204; encontrados {len(membros)}.")
        nome = os.path.basename(membros[0])
        caminho = os.path.join(destino, nome)
        conteudo = z.read(membros[0])
    if os.path.exists(caminho):
        with open(caminho, "rb") as f:
            if f.read() != conteudo:
                raise FormatoNaoReconhecido(f"{caminho} já existe com conteúdo diferente do zip.")
        return caminho
    with open(caminho, "wb") as f:
        f.write(conteudo)
    return caminho


@dataclass
class StatusArquivo:
    descricao: str
    destino: str
    url: str
    presente: bool
    registrado: bool


def status_dados_externos() -> List[StatusArquivo]:
    registro = ler_registro_sha256()
    itens = [StatusArquivo(
        "Normal climatológica 1991–2020, precipitação (planilha do INMET)",
        _rel(ARQUIVO_NORMAL_PREC), URL_NORMAL_PREC, os.path.exists(ARQUIVO_NORMAL_PREC),
        os.path.relpath(ARQUIVO_NORMAL_PREC, DIR_RAW).replace(os.sep, "/") in registro,
    )]
    for ano in ANOS_VIZINHOS:
        extraido = arquivo_a204_do_ano(ano)
        itens.append(StatusArquivo(
            f"Dados horários de {ano}, estação A204 (extraídos de {ano}.zip)",
            _rel(extraido) if extraido else f"{_rel(DIR_DOWNLOADS)}/{ano}.zip",
            URL_DADOS_ANO.format(ano=ano), extraido is not None,
            extraido is not None and os.path.basename(extraido) in registro,
        ))
    return itens


def preparar_dados_externos() -> List[str]:
    """Extrai a A204 dos zips em data/raw/downloads/ e registra o SHA-256 dos arquivos novos."""
    mensagens = []
    for ano in ANOS_VIZINHOS:
        zip_ano = os.path.join(DIR_DOWNLOADS, f"{ano}.zip")
        if not os.path.exists(zip_ano):
            if arquivo_a204_do_ano(ano) is None:
                mensagens.append(f"{ano}: falta {_rel(zip_ano)} (baixar de {URL_DADOS_ANO.format(ano=ano)}).")
            continue
        extraido = extrair_a204_do_zip(zip_ano)
        h = registrar_sha256(extraido, f"extraído de {ano}.zip ({URL_DADOS_ANO.format(ano=ano)}), "
                                       f"SHA-256 do zip {sha256_arquivo(zip_ano)}")
        mensagens.append(f"{ano}: {_rel(extraido)} registrado (SHA-256 {h}).")
    if os.path.exists(ARQUIVO_NORMAL_PREC):
        h = registrar_sha256(ARQUIVO_NORMAL_PREC, f"baixado de {URL_NORMAL_PREC}")
        mensagens.append(f"normal: {_rel(ARQUIVO_NORMAL_PREC)} registrado (SHA-256 {h}).")
    else:
        mensagens.append(f"normal: falta {_rel(ARQUIVO_NORMAL_PREC)} (baixar de {URL_NORMAL_PREC}).")
    return mensagens


@dataclass
class CompletudeJanela:
    ano: int
    janela: str
    inicio: date
    fim: date
    dias: int
    dias_completos: int
    dias_parciais: int
    dias_sem_registro: int
    maior_lacuna_sem_registro_dias: int
    maior_sequencia_incompleta_dias: int
    horas_validas: int
    arquivo: str
    sha256: str
    dias_sem_registro_por_mes: Dict[int, int]


def _hora_valida(reg: Optional[RegistroINMET], lat_rad: float, lm_graus: float) -> Tuple[bool, bool]:
    """(tem algum valor, tem tudo o que o v2 usa, com a regra da radiação)."""
    if reg is None:
        return False, False
    v = reg.valores
    algum = any(x is not None for x in v.values())
    if not all(v[c] is not None for c in VARIAVEIS_OBRIGATORIAS):
        return algum, False
    if v["rs_kj_m2"] is None:
        meio = reg.fim_utc - timedelta(minutes=30)
        geo = fao56.geometria_horaria(meio.timetuple().tm_yday, meio.hour + meio.minute / 60, lat_rad,
                                      LZ_UTC_GRAUS, lm_graus)
        return algum, geo.ra_mj < LIMIAR_RA_NOITE_MJ
    return algum, True


def completude_janela(estacao: EstacaoINMET, registros: Sequence[RegistroINMET], ano: int,
                      nome: str, inicio: date, fim: date) -> CompletudeJanela:
    por_hora = {r.fim_utc: r for r in registros}
    lat_rad, lm = math.radians(estacao.latitude), -estacao.longitude
    completos = sem_registro = 0
    lacuna = maior_lacuna = seq_incompleta = maior_seq = 0
    horas_validas = 0
    por_mes: Dict[int, int] = {}
    d = inicio
    while d <= fim:
        algum_dia = False
        validas_dia = 0
        for hl in range(24):
            fim_utc = (datetime(d.year, d.month, d.day, hl, tzinfo=FUSO_LOCAL) + timedelta(hours=1)).astimezone(timezone.utc)
            algum, ok = _hora_valida(por_hora.get(fim_utc), lat_rad, lm)
            algum_dia |= algum
            validas_dia += ok
        horas_validas += validas_dia
        if validas_dia == 24:
            completos += 1
            seq_incompleta = 0
        else:
            seq_incompleta += 1
            maior_seq = max(maior_seq, seq_incompleta)
        if not algum_dia:
            sem_registro += 1
            por_mes[d.month] = por_mes.get(d.month, 0) + 1
            lacuna += 1
            maior_lacuna = max(maior_lacuna, lacuna)
        else:
            lacuna = 0
        d += timedelta(days=1)
    n = (fim - inicio).days + 1
    return CompletudeJanela(
        ano=ano, janela=nome, inicio=inicio, fim=fim, dias=n, dias_completos=completos,
        dias_parciais=n - completos - sem_registro, dias_sem_registro=sem_registro,
        maior_lacuna_sem_registro_dias=maior_lacuna, maior_sequencia_incompleta_dias=maior_seq,
        horas_validas=horas_validas, arquivo=estacao.arquivo, sha256=estacao.sha256,
        dias_sem_registro_por_mes=por_mes,
    )


def janelas_do_ano(ano: int) -> Dict[str, Tuple[date, date]]:
    return {
        "chuvoso": (date(ano, 1, 15), date(ano, 3, 25)),
        "seco": (date(ano, 7, 1), date(ano, 9, 8)),
        "julho_a_setembro": (date(ano, 7, 1), date(ano, 9, 30)),
        "maio_a_dezembro": (date(ano, 5, 1), date(ano, 12, 31)),
    }


# Afirmações do texto atual do artigo sobre os anos vizinhos, a conferir
# contra os arquivos do INMET. São entradas de texto, não resultados: o valor obtido sai do arquivo.
# (ano, janela, grandeza, valor afirmado; None = todos os dias da janela)
AFIRMACOES_ARTIGO = (
    (2024, "seco", "dias_sem_registro", 60, "2024: dias sem registro na janela do ciclo seco (01/07 a 08/09)"),
    (2024, "seco", "maior_lacuna_sem_registro_dias", 27, "2024: maior lacuna contínua na janela do ciclo seco (dias)"),
    (2025, "maio_a_dezembro", "dias_sem_registro", None, "2025: sem registros de maio a dezembro"),
)


def completude_ano(ano: int, caminho: str) -> List[CompletudeJanela]:
    estacao, registros = ler_arquivo_inmet(caminho)
    return [completude_janela(estacao, registros, ano, nome, ini, fim) for nome, (ini, fim) in janelas_do_ano(ano).items()]
