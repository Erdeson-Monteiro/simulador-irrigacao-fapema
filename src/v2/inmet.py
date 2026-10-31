"""
Leitura do arquivo horário de estação automática do INMET para o v2.

Formato (verificado no arquivo da A204, 2023): latin1, separador ';', vírgula decimal
(valores como ',9'), 8 linhas de metadados e cabeçalho 'Data;Hora UTC;...'.
O registro 'HHMM UTC' marca o FIM do intervalo de uma hora, (HH−1, HH] UTC
(Nota Técnica 001/2011 do INMET; verificado em `tests/test_v2_clima.py` pelo centroide
da radiação). Nada é imputado: campo vazio ou -9999 vira None.

O SHA-256 de cada arquivo bruto fica registrado em `data/raw/SHA256SUMS`; um arquivo
fora do registro, ou com hash diferente, é recusado.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import os
from typing import Dict, List, Optional, Tuple


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR_RAW = os.path.join(ROOT_DIR, "data", "raw")
REGISTRO_SHA256 = os.path.join(DIR_RAW, "SHA256SUMS")
ARQUIVO_A204_2023 = os.path.join(DIR_RAW, "INMET_NE_MA_A204_BALSAS_01-01-2023_A_31-12-2023.CSV")

# Colunas usadas no v2 (docs/MODELO.md, seção 2.1), pelo nome exato do cabeçalho do INMET.
COLUNAS = {
    "p_mm": "PRECIPITAÇÃO TOTAL, HORÁRIO (mm)",
    "rs_kj_m2": "RADIACAO GLOBAL (Kj/m²)",
    "t_c": "TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)",
    "ur_pct": "UMIDADE RELATIVA DO AR, HORARIA (%)",
    "u10_ms": "VENTO, VELOCIDADE HORARIA (m/s)",
    "tmax_c": "TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C)",
    "tmin_c": "TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C)",
    "urmin_pct": "UMIDADE REL. MIN. NA HORA ANT. (AUT) (%)",
}


class ArquivoINMETInvalido(ValueError):
    """Arquivo bruto ausente, fora do registro de SHA-256 ou fora do formato esperado."""


@dataclass(frozen=True)
class EstacaoINMET:
    codigo: str
    nome: str
    uf: str
    latitude: float
    longitude: float
    altitude: float
    arquivo: str
    sha256: str


@dataclass(frozen=True)
class RegistroINMET:
    fim_utc: datetime
    linha: int
    valores: Dict[str, Optional[float]]


def sha256_arquivo(caminho: str) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def ler_registro_sha256(caminho_registro: str = REGISTRO_SHA256) -> Dict[str, str]:
    """Lê o registro no formato do `sha256sum` (hash, dois espaços, caminho relativo a data/raw)."""
    registro: Dict[str, str] = {}
    if not os.path.exists(caminho_registro):
        return registro
    with open(caminho_registro, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            hash_hex, nome = linha.split(None, 1)
            registro[nome.strip().lstrip("*")] = hash_hex.lower()
    return registro


def conferir_sha256(caminho: str, caminho_registro: str = REGISTRO_SHA256) -> str:
    """Devolve o SHA-256 do arquivo; erro se ele não estiver registrado ou não bater."""
    nome = os.path.relpath(os.path.abspath(caminho), os.path.dirname(os.path.abspath(caminho_registro)))
    esperado = ler_registro_sha256(caminho_registro).get(nome.replace(os.sep, "/"))
    obtido = sha256_arquivo(caminho)
    if esperado is None:
        raise ArquivoINMETInvalido(f"Arquivo bruto sem SHA-256 registrado em {caminho_registro}: {nome}")
    if obtido != esperado:
        raise ArquivoINMETInvalido(
            f"SHA-256 de {nome} não confere com o registro: obtido {obtido}, registrado {esperado}"
        )
    return obtido


def converter_valor(texto: str) -> Optional[float]:
    """Converte '25,7', ',9' ou '-,5' em float; vazio e -9999 viram None."""
    s = texto.strip()
    if s == "":
        return None
    s = s.replace(",", ".")
    if s.startswith("."):
        s = "0" + s
    elif s.startswith("-."):
        s = "-0" + s[1:]
    valor = float(s)
    if valor <= -9990.0:
        return None
    return valor


def ler_arquivo_inmet(
    caminho: str = ARQUIVO_A204_2023,
    verificar_sha256: bool = True,
) -> Tuple[EstacaoINMET, List[RegistroINMET]]:
    """
    Lê metadados e registros horários. Com `verificar_sha256`, o arquivo precisa constar
    em `data/raw/SHA256SUMS` com o mesmo hash.
    """
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo do INMET não encontrado: {caminho}. Nenhum dado é gerado no lugar.")
    sha = conferir_sha256(caminho) if verificar_sha256 else sha256_arquivo(caminho)

    with open(caminho, encoding="latin1", newline="") as f:
        linhas = f.read().splitlines()

    meta: Dict[str, str] = {}
    idx_cab: Optional[int] = None
    for i, linha in enumerate(linhas):
        partes = linha.split(";")
        if partes[0].strip().upper() == "DATA":
            idx_cab = i
            break
        if len(partes) >= 2:
            meta[partes[0].strip().rstrip(":").upper()] = partes[1].strip()
    if idx_cab is None:
        raise ArquivoINMETInvalido(f"Cabeçalho 'Data;Hora UTC;...' não encontrado em {caminho}")

    try:
        estacao = EstacaoINMET(
            codigo=meta["CODIGO (WMO)"],
            nome=meta["ESTACAO"],
            uf=meta["UF"],
            latitude=float(meta["LATITUDE"].replace(",", ".")),
            longitude=float(meta["LONGITUDE"].replace(",", ".")),
            altitude=float(meta["ALTITUDE"].replace(",", ".")),
            arquivo=os.path.relpath(os.path.abspath(caminho), ROOT_DIR).replace(os.sep, "/"),
            sha256=sha,
        )
    except KeyError as exc:
        raise ArquivoINMETInvalido(f"Metadado ausente no cabeçalho do arquivo: {exc}") from exc

    cabecalho = [c.strip() for c in linhas[idx_cab].split(";")]
    if cabecalho[:2] != ["Data", "Hora UTC"]:
        raise ArquivoINMETInvalido(f"Colunas iniciais inesperadas: {cabecalho[:2]}")
    indices: Dict[str, int] = {}
    for chave, nome_coluna in COLUNAS.items():
        if nome_coluna not in cabecalho:
            raise ArquivoINMETInvalido(f"Coluna obrigatória ausente: {nome_coluna!r}")
        indices[chave] = cabecalho.index(nome_coluna)

    registros: List[RegistroINMET] = []
    vistos = set()
    for num, linha in enumerate(linhas[idx_cab + 1:], start=idx_cab + 2):
        if not linha.strip():
            continue
        partes = linha.split(";")
        data_txt = partes[0].strip().replace("/", "-")
        hora_txt = partes[1].strip()
        if not hora_txt.endswith(" UTC") or len(hora_txt) != 8:
            raise ArquivoINMETInvalido(f"Hora fora do formato 'HHMM UTC' na linha {num}: {hora_txt!r}")
        fim = datetime.fromisoformat(data_txt).replace(
            hour=int(hora_txt[:2]), minute=int(hora_txt[2:4]), tzinfo=timezone.utc
        )
        if fim.minute != 0:
            raise ArquivoINMETInvalido(f"Registro fora da hora cheia na linha {num}: {hora_txt!r}")
        if fim in vistos:
            raise ArquivoINMETInvalido(f"Registro duplicado na linha {num}: {fim.isoformat()}")
        vistos.add(fim)
        valores = {
            chave: (converter_valor(partes[idx]) if idx < len(partes) else None)
            for chave, idx in indices.items()
        }
        registros.append(RegistroINMET(fim_utc=fim, linha=num, valores=valores))

    registros.sort(key=lambda r: r.fim_utc)
    return estacao, registros


def grade_horaria(registros: List[RegistroINMET]) -> List[Optional[RegistroINMET]]:
    """Coloca os registros numa grade horária contínua; horas sem linha no arquivo viram None."""
    if not registros:
        return []
    por_hora = {r.fim_utc: r for r in registros}
    t, fim = registros[0].fim_utc, registros[-1].fim_utc
    grade: List[Optional[RegistroINMET]] = []
    while t <= fim:
        grade.append(por_hora.get(t))
        t += timedelta(hours=1)
    return grade
