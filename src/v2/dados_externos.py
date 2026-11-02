"""
Dados externos do v2: média de chuva de referência e arquivos da A204 de 2024 e 2025. Nada
aqui baixa arquivos nem estima valores: quando um arquivo falta, o programa diz a URL exata e
a pasta onde colocá-lo.

- Média de chuva: médias mensais de 1991–2021 da estação convencional 82768 (Balsas), da
  Tabela 6 de Corrêa, Carvalho e Mendes (2023), em `data/referencias/` (versionado).
- Anos vizinhos, passo a passo para o autor:
  1. baixar `2024.zip` e `2025.zip` para `data/raw/downloads/` (pasta fora do git);
  2. rodar `python3 main.py dados --preparar`: extrai só o arquivo da A204 de cada zip
     para `data/raw/` e registra o SHA-256 em `data/raw/SHA256SUMS`;
  3. rodar `python3 main.py pipeline`.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import math
import os
import re
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


URL_DADOS_ANO = "https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip"
DIR_DOWNLOADS = os.path.join(DIR_RAW, "downloads")
ANOS_VIZINHOS = (2024, 2025)

ARQUIVO_MEDIA_CHUVA = os.path.join(ROOT_DIR, "data", "referencias", "correa_2023_balsas_82768.csv")
FONTE_MEDIA_CHUVA = (
    "Corrêa, Carvalho e Mendes (2023), Tabela 6: média 1991–2021 da estação convencional 82768 (Balsas)"
)

# Pesos por mês para a média de cada janela (fração dos dias do mês que caem na janela).
PESOS_JANELA_MEDIA: Dict[str, Dict[int, float]] = {
    "chuvoso": {1: 17 / 31, 2: 28 / 28, 3: 25 / 31},
    "seco": {7: 1.0, 8: 1.0, 9: 8 / 30},
}


class FormatoNaoReconhecido(ValueError):
    """Planilha ou arquivo fora do formato esperado: o programa para em vez de adivinhar."""


def _rel(caminho: str) -> str:
    return os.path.relpath(caminho, ROOT_DIR).replace(os.sep, "/")


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
# Média de chuva de referência (Corrêa, Carvalho e Mendes, 2023)
# ---------------------------------------------------------------------------

@dataclass
class MediaChuva:
    mensal_mm: Dict[int, float]
    arquivo: str
    sha256: str

    def janela(self, pesos: Dict[int, float]) -> float:
        faltam = sorted(m for m in pesos if m not in self.mensal_mm)
        if faltam:
            raise FormatoNaoReconhecido(f"{self.arquivo}: faltam os meses {faltam} para calcular a janela.")
        return sum(self.mensal_mm[m] * w for m, w in pesos.items())


def ler_media_chuva(caminho: str = ARQUIVO_MEDIA_CHUVA) -> MediaChuva:
    """
    Médias mensais de chuva (mm), com colunas `mes,precipitacao_media_mm` e linhas `#` de
    comentário. Mês fora de 1–12 ou repetido, valor negativo ou não numérico é erro.
    """
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo de referência não encontrado: {caminho}.")
    with open(caminho, encoding="utf-8", newline="") as f:
        leitor = csv.DictReader(linha for linha in f if not linha.startswith("#"))
        if leitor.fieldnames != ["mes", "precipitacao_media_mm"]:
            raise FormatoNaoReconhecido(
                f"{caminho}: colunas esperadas mes,precipitacao_media_mm; lidas {leitor.fieldnames}.")
        mensal: Dict[int, float] = {}
        for linha in leitor:
            try:
                mes, valor = int(linha["mes"]), float(linha["precipitacao_media_mm"])
            except (TypeError, ValueError) as exc:
                raise FormatoNaoReconhecido(f"{caminho}: linha inválida {dict(linha)}.") from exc
            if not 1 <= mes <= 12 or mes in mensal or valor < 0:
                raise FormatoNaoReconhecido(f"{caminho}: mês {mes} fora de 1–12, repetido ou com valor negativo.")
            mensal[mes] = valor
    return MediaChuva(mensal_mm=mensal, arquivo=_rel(caminho), sha256=sha256_arquivo(caminho))


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
    itens = []
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
