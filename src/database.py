"""
Camada de persistência SQLite — Inicialização do schema, dados de referência,
ingestão idempotente em lote e consultas (Seções 7 e 8).

O banco roda em modo WAL. O token de cada dispositivo nunca é guardado, só o SHA-256 dele
(`src/seguranca.py`); a autenticação compara os hashes em tempo constante.
"""

from __future__ import annotations
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import json
import os
import sqlite3
from typing import Dict, Any, Iterator, List, Optional, Tuple

from src.seguranca import HASH_TOKEN_TESTE_CONTRATO, HASHES_COMPROMETIDOS, hash_token, tokens_conferem
from src.v2.modelo import NOMES_ESTRATEGIAS
from src.v2.parametros import PARAMETROS_PADRAO


FUSO_BR = timezone(timedelta(hours=-3))
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "irrigacao.db"
)
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def agora_iso() -> str:
    """Retorna o timestamp atual em ISO-8601 com fuso -03:00."""
    return datetime.now(FUSO_BR).isoformat(timespec="seconds")


class BancoFormatoAntigo(RuntimeError):
    """Banco criado pelo v1, com o token do dispositivo em texto puro."""


def obter_conexao(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Abre conexão SQLite em modo WAL, com chaves estrangeiras e row_factory configurados."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 15000;")
    return conn


@contextmanager
def conexao(db_path: str = DEFAULT_DB_PATH) -> Iterator[sqlite3.Connection]:
    """Conexão que faz commit ao sair sem erro, rollback com erro, e sempre fecha."""
    conn = obter_conexao(db_path)
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def banco_no_formato_antigo(db_path: str) -> bool:
    if not os.path.exists(db_path):
        return False
    conn = sqlite3.connect(db_path)
    try:
        colunas = [r[1] for r in conn.execute("PRAGMA table_info(dispositivo)")]
    finally:
        conn.close()
    return "token" in colunas


def inicializar_banco(db_path: str = DEFAULT_DB_PATH, token_dispositivo: Optional[str] = None) -> None:
    """
    Executa o schema SQL e insere os registros base caso ainda não existam.

    `token_dispositivo` (o DEVICE_TOKEN do `serve` e do `pipeline`) passa a ser o token do
    `sim-001`: só o SHA-256 dele é gravado. Sem ele, um `sim-001` recém-criado recebe o hash
    do token de teste do contrato HTTP (src/seguranca.py), que o `serve` nunca aceita.
    """
    if banco_no_formato_antigo(db_path):
        raise BancoFormatoAntigo(
            f"{db_path} foi criado pelo v1 e guarda o token em texto puro. Rode python3 main.py pipeline, "
            "que guarda uma cópia em backups/ e recria o banco."
        )
    par = PARAMETROS_PADRAO
    with conexao(db_path) as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

        # 1. Calibrações de referência (Seção 7 - calibracao)
        calibracoes_iniciais = [
            (
                1,
                "umidade_solo",
                json.dumps({"escala": 0.0001, "offset": 0.0, "formula": "valor_bruto * 0.0001"}),
                "linear_sintetica",
                "2026-01-01T00:00:00-03:00",
                "Calibração sintética padrão: converte leitura bruta (ex: 2310) em cm3/cm3 (0.2310).",
            ),
            (
                2,
                "temperatura_ar",
                json.dumps({"escala": 0.1, "offset": 0.0, "formula": "valor_bruto * 0.1"}),
                "linear_sintetica",
                "2026-01-01T00:00:00-03:00",
                "Calibração sintética de temperatura em décimos de °C.",
            ),
            (
                3,
                "precipitacao",
                json.dumps({"escala": 0.1, "offset": 0.0, "formula": "valor_bruto * 0.1"}),
                "linear_sintetica",
                "2026-01-01T00:00:00-03:00",
                "Calibração sintética de pluviômetro em décimos de mm.",
            ),
            (
                4,
                "nivel_reservatorio",
                json.dumps({"escala": 0.1, "offset": 0.0, "formula": "valor_bruto * 0.1"}),
                "linear_sintetica",
                "2026-01-01T00:00:00-03:00",
                "Calibração sintética de volume do reservatório em décimos de litro.",
            ),
        ]
        for cal in calibracoes_iniciais:
            conn.execute(
                """
                INSERT OR IGNORE INTO calibracao (id, sensor_id, coeficientes, metodo, data, observacoes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                cal,
            )

        # 2. Estratégias do modelo v2 (parâmetros lidos da configuração, não digitados)
        estrategias = [
            (1, "E1", NOMES_ESTRATEGIAS["E1"].capitalize(),
             {"regra": "θ₁ ≤ θlim → lâmina fixa L", "theta_lim": par.theta_lim, "lamina_mm": par.lamina_e1_mm}),
            (2, "E2", NOMES_ESTRATEGIAS["E2"].capitalize(),
             {"regra": "Dr ≥ RAW → repõe Dr", "raw_mm": par.raw_mm}),
            (3, "E3", NOMES_ESTRATEGIAS["E3"].capitalize(),
             {"regra": "Dr ≥ RAW → mín(Dr; B − aplicado no dia), B = (V/A)/n", "raw_mm": par.raw_mm}),
        ]
        for est_id, cod, nome, parametros in estrategias:
            conn.execute(
                """
                INSERT INTO estrategia (id, codigo, nome, parametros) VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET codigo = excluded.codigo, nome = excluded.nome,
                                              parametros = excluded.parametros
                """,
                (est_id, cod, nome, json.dumps(parametros, ensure_ascii=False)),
            )

        # 3. Canteiros virtuais do v2: um por estratégia
        canteiros = [
            (1, "C1", f"Canteiro virtual 1 — E1 ({NOMES_ESTRATEGIAS['E1']})", 1),
            (2, "C2", f"Canteiro virtual 2 — E2 ({NOMES_ESTRATEGIAS['E2']})", 2),
            (3, "C3", f"Canteiro virtual 3 — E3 ({NOMES_ESTRATEGIAS['E3']})", 3),
        ]
        for c_id, cod, nome, est_id in canteiros:
            conn.execute(
                """
                INSERT INTO canteiro
                (id, codigo, nome, area_m2, cultura, profundidade_raiz_mm, volume_camada_1_mm, volume_camada_2_mm)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET nome = excluded.nome, area_m2 = excluded.area_m2,
                    profundidade_raiz_mm = excluded.profundidade_raiz_mm,
                    volume_camada_1_mm = excluded.volume_camada_1_mm, volume_camada_2_mm = excluded.volume_camada_2_mm
                """,
                (c_id, cod, nome, par.area_m2, "Alface", par.z1_mm, par.z1_mm, par.z2_mm),
            )
            cur = conn.execute("SELECT COUNT(*) AS cnt FROM canteiro_estrategia WHERE canteiro_id = ?", (c_id,))
            if cur.fetchone()["cnt"] == 0:
                conn.execute(
                    "INSERT INTO canteiro_estrategia (canteiro_id, estrategia_id, inicio, fim) VALUES (?, ?, ?, NULL)",
                    (c_id, est_id, "2026-01-01T00:00:00-03:00"),
                )

        # 4. Dispositivos: o simulador e o microcontrolador de campo (desabilitado até ter token)
        dispositivos = [
            (1, "sim-001", "Simulador do modelo v2 (canteiros virtuais)", "simulador", HASH_TOKEN_TESTE_CONTRATO),
            (2, "esp32-001", "Protótipo de microcontrolador de campo", "microcontrolador", None),
        ]
        for d_id, cod, nome, tipo, hash_inicial in dispositivos:
            conn.execute(
                """
                INSERT OR IGNORE INTO dispositivo (id, codigo, nome, tipo, token_sha256, criado_em)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (d_id, cod, nome, tipo, hash_inicial, "2026-01-01T00:00:00-03:00"),
            )
        if token_dispositivo:
            conn.execute("UPDATE dispositivo SET token_sha256 = ? WHERE codigo = 'sim-001'",
                         (hash_token(token_dispositivo),))
        # Nenhum dispositivo de campo fica com um token comprometido.
        conn.execute(
            f"UPDATE dispositivo SET token_sha256 = NULL WHERE tipo = 'microcontrolador' AND token_sha256 IN "
            f"({','.join('?' * len(HASHES_COMPROMETIDOS))})",
            tuple(sorted(HASHES_COMPROMETIDOS)),
        )


def autenticar_dispositivo(
    conn: sqlite3.Connection, codigo_dispositivo: str, token_header: Optional[str]
) -> sqlite3.Row:
    """
    Valida o cabeçalho `Authorization: Bearer <token>` contra o dispositivo informado.
    Retorna a linha do dispositivo ou levanta PermissionError.
    """
    if not token_header or not token_header.startswith("Bearer "):
        raise PermissionError("Cabeçalho Authorization Bearer ausente ou malformado.")
    token = token_header[len("Bearer "):].strip()
    row = conn.execute(
        "SELECT * FROM dispositivo WHERE codigo = ?", (codigo_dispositivo,)
    ).fetchone()
    if not row or not tokens_conferem(token, row["token_sha256"]):
        raise PermissionError("Dispositivo ou token inválido.")
    return row


def _obter_calibracao_e_unidade(
    conn: sqlite3.Connection, tipo_leitura: str, valor_bruto: float
) -> Tuple[int, float, str]:
    """
    Aplica a calibração cadastrada para o tipo de leitura e retorna:
    (calibracao_id, valor_calibrado, unidade).
    """
    unidades = {
        "umidade_solo": "cm3/cm3",
        "temperatura_ar": "°C",
        "precipitacao": "mm",
        "nivel_reservatorio": "L",
    }
    if tipo_leitura not in unidades:
        raise ValueError(f"Tipo de leitura inválido: '{tipo_leitura}'.")

    row = conn.execute(
        "SELECT id, coeficientes FROM calibracao WHERE sensor_id = ? ORDER BY id DESC LIMIT 1",
        (tipo_leitura,),
    ).fetchone()
    if not row:
        row = conn.execute("SELECT id, coeficientes FROM calibracao ORDER BY id ASC LIMIT 1").fetchone()

    coef = json.loads(row["coeficientes"])
    escala = float(coef.get("escala", 1.0))
    offset = float(coef.get("offset", 0.0))
    valor_calibrado = round(valor_bruto * escala + offset, 6)
    return int(row["id"]), valor_calibrado, unidades[tipo_leitura]


def _resolver_canteiro_id(conn: sqlite3.Connection, identificador: Any) -> int:
    """Resolve um canteiro por código (ex: 'C1') ou id numérico."""
    row = conn.execute(
        "SELECT id FROM canteiro WHERE codigo = ? OR CAST(id AS TEXT) = ?",
        (str(identificador), str(identificador)),
    ).fetchone()
    if not row:
        raise ValueError(f"Canteiro '{identificador}' não encontrado.")
    return int(row["id"])


def _resolver_estrategia_id(conn: sqlite3.Connection, identificador: Any, canteiro_id: int) -> int:
    """Resolve uma estratégia por código ('E1', 'E2', 'E3') ou obtém a vigente do canteiro."""
    if identificador:
        row = conn.execute(
            "SELECT id FROM estrategia WHERE codigo = ? OR CAST(id AS TEXT) = ?",
            (str(identificador), str(identificador)),
        ).fetchone()
        if row:
            return int(row["id"])

    row_hist = conn.execute(
        """
        SELECT estrategia_id FROM canteiro_estrategia
        WHERE canteiro_id = ?
        ORDER BY inicio DESC LIMIT 1
        """,
        (canteiro_id,),
    ).fetchone()
    if not row_hist:
        raise ValueError(f"Nenhuma estratégia associada ao canteiro_id={canteiro_id}.")
    return int(row_hist["estrategia_id"])


def ingerir_lote_leituras(
    db_path: str, payload: Dict[str, Any], auth_header: Optional[str]
) -> Dict[str, int]:
    """
    Processa `POST /api/v1/leituras` em lote com idempotência por `(dispositivo_id, sequencia)`.
    Retorna `{"aceitos": N, "ignorados": M, "ultima_sequencia": S}`.
    """
    codigo_disp = payload.get("dispositivo")
    leituras = payload.get("leituras")
    if not codigo_disp or not isinstance(leituras, list):
        raise ValueError("Payload deve conter 'dispositivo' e lista 'leituras'.")

    with conexao(db_path) as conn:
        disp = autenticar_dispositivo(conn, codigo_disp, auth_header)
        disp_id = int(disp["id"])
        recebido_em = agora_iso()

        aceitos = 0
        ignorados = 0
        ultima_seq = 0

        for item in leituras:
            seq = int(item["seq"])
            ultima_seq = max(ultima_seq, seq)
            canteiro_id = _resolver_canteiro_id(conn, item["canteiro"])
            tipo = str(item["tipo"])
            prof_cm = item.get("profundidade_cm")
            valor_bruto = float(item["valor_bruto"])
            registrado_em = str(item["registrado_em"])

            cal_id, valor_calibrado, unidade = _obter_calibracao_e_unidade(conn, tipo, valor_bruto)

            cur = conn.execute(
                """
                INSERT OR IGNORE INTO leitura (
                    dispositivo_id, canteiro_id, tipo, profundidade_cm,
                    valor_bruto, valor_calibrado, unidade, calibracao_id,
                    sequencia, registrado_em, recebido_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    disp_id,
                    canteiro_id,
                    tipo,
                    prof_cm,
                    valor_bruto,
                    valor_calibrado,
                    unidade,
                    cal_id,
                    seq,
                    registrado_em,
                    recebido_em,
                ),
            )
            if cur.rowcount == 1:
                aceitos += 1
            else:
                ignorados += 1

        conn.commit()

        if ultima_seq == 0:
            row_max = conn.execute(
                "SELECT COALESCE(MAX(sequencia), 0) AS max_s FROM leitura WHERE dispositivo_id = ?",
                (disp_id,),
            ).fetchone()
            ultima_seq = int(row_max["max_s"])

        return {
            "aceitos": aceitos,
            "ignorados": ignorados,
            "ultima_sequencia": ultima_seq,
        }


def ingerir_lote_eventos_irrigacao(
    db_path: str, payload: Dict[str, Any], auth_header: Optional[str]
) -> Dict[str, int]:
    """
    Processa `POST /api/v1/eventos-irrigacao` em lote com idempotência por `(dispositivo_id, sequencia)`.
    Retorna `{"aceitos": N, "ignorados": M, "ultima_sequencia": S}`.
    """
    codigo_disp = payload.get("dispositivo")
    eventos = payload.get("eventos")
    if not codigo_disp or not isinstance(eventos, list):
        raise ValueError("Payload deve conter 'dispositivo' e lista 'eventos'.")

    with conexao(db_path) as conn:
        disp = autenticar_dispositivo(conn, codigo_disp, auth_header)
        disp_id = int(disp["id"])
        recebido_em = agora_iso()

        aceitos = 0
        ignorados = 0
        ultima_seq = 0

        for item in eventos:
            seq = int(item["seq"])
            ultima_seq = max(ultima_seq, seq)
            canteiro_id = _resolver_canteiro_id(conn, item["canteiro"])
            estrategia_id = _resolver_estrategia_id(conn, item.get("estrategia"), canteiro_id)
            inicio = str(item["inicio"])
            fim = str(item.get("fim") or inicio)
            lamina_mm = float(item["lamina_mm"])

            # Se volume_litros não vier explícito, calcula pela área do canteiro
            if "volume_litros" in item and item["volume_litros"] is not None:
                volume_litros = float(item["volume_litros"])
            else:
                row_c = conn.execute(
                    "SELECT area_m2 FROM canteiro WHERE id = ?", (canteiro_id,)
                ).fetchone()
                volume_litros = round(lamina_mm * float(row_c["area_m2"]), 2)

            origem = str(item.get("origem") or ("simulado" if disp["tipo"] == "simulador" else "automatico"))
            registrado_em = str(item.get("registrado_em") or fim)

            cur = conn.execute(
                """
                INSERT OR IGNORE INTO evento_irrigacao (
                    dispositivo_id, canteiro_id, estrategia_id,
                    inicio, fim, lamina_mm, volume_litros,
                    origem, sequencia, registrado_em, recebido_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    disp_id,
                    canteiro_id,
                    estrategia_id,
                    inicio,
                    fim,
                    lamina_mm,
                    volume_litros,
                    origem,
                    seq,
                    registrado_em,
                    recebido_em,
                ),
            )
            if cur.rowcount == 1:
                aceitos += 1
            else:
                ignorados += 1

        conn.commit()

        if ultima_seq == 0:
            row_max = conn.execute(
                "SELECT COALESCE(MAX(sequencia), 0) AS max_s FROM evento_irrigacao WHERE dispositivo_id = ?",
                (disp_id,),
            ).fetchone()
            ultima_seq = int(row_max["max_s"])

        return {
            "aceitos": aceitos,
            "ignorados": ignorados,
            "ultima_sequencia": ultima_seq,
        }


def listar_canteiros(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retorna todos os canteiros com sua estratégia ativa e contagens de registros."""
    with conexao(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
                c.*,
                e.codigo AS estrategia_codigo,
                e.nome AS estrategia_nome,
                e.parametros AS estrategia_parametros,
                ce.inicio AS estrategia_inicio,
                (SELECT COUNT(*) FROM leitura l WHERE l.canteiro_id = c.id) AS total_leituras,
                (SELECT COUNT(*) FROM evento_irrigacao ev WHERE ev.canteiro_id = c.id) AS total_eventos
            FROM canteiro c
            LEFT JOIN canteiro_estrategia ce ON ce.canteiro_id = c.id AND ce.fim IS NULL
            LEFT JOIN estrategia e ON e.id = ce.estrategia_id
            ORDER BY c.id ASC
            """
        ).fetchall()
        resultado = []
        for r in rows:
            d = dict(r)
            if d.get("estrategia_parametros"):
                d["estrategia_parametros"] = json.loads(d["estrategia_parametros"])
            resultado.append(d)
        return resultado


def consultar_series_canteiro(
    db_path: str,
    canteiro_identificador: str,
    de: Optional[str] = None,
    ate: Optional[str] = None,
    tipo: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Consulta `GET /api/v1/canteiros/{id}/series?de=&ate=&tipo=`."""
    with conexao(db_path) as conn:
        canteiro_id = _resolver_canteiro_id(conn, canteiro_identificador)
        sql = """
            SELECT
                l.id,
                c.codigo AS canteiro,
                d.codigo AS dispositivo,
                d.tipo AS dispositivo_tipo,
                l.tipo,
                l.profundidade_cm,
                l.valor_bruto,
                l.valor_calibrado,
                l.unidade,
                l.calibracao_id,
                l.sequencia,
                l.registrado_em,
                l.recebido_em
            FROM leitura l
            JOIN canteiro c ON c.id = l.canteiro_id
            JOIN dispositivo d ON d.id = l.dispositivo_id
            WHERE l.canteiro_id = ?
        """
        params: List[Any] = [canteiro_id]
        if de:
            sql += " AND l.registrado_em >= ?"
            params.append(de)
        if ate:
            sql += " AND l.registrado_em <= ?"
            params.append(ate + ("T23:59:59-03:00" if len(ate) == 10 else ""))
        if tipo:
            sql += " AND l.tipo = ?"
            params.append(tipo)

        sql += " ORDER BY l.registrado_em ASC, l.id ASC"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def consultar_eventos_canteiro(
    db_path: str,
    canteiro_identificador: str,
    de: Optional[str] = None,
    ate: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Consulta `GET /api/v1/canteiros/{id}/eventos?de=&ate=`."""
    with conexao(db_path) as conn:
        canteiro_id = _resolver_canteiro_id(conn, canteiro_identificador)
        sql = """
            SELECT
                ev.id,
                c.codigo AS canteiro,
                e.codigo AS estrategia,
                d.codigo AS dispositivo,
                d.tipo AS dispositivo_tipo,
                ev.inicio,
                ev.fim,
                ev.lamina_mm,
                ev.volume_litros,
                ev.origem,
                ev.sequencia,
                ev.registrado_em,
                ev.recebido_em
            FROM evento_irrigacao ev
            JOIN canteiro c ON c.id = ev.canteiro_id
            JOIN estrategia e ON e.id = ev.estrategia_id
            JOIN dispositivo d ON d.id = ev.dispositivo_id
            WHERE ev.canteiro_id = ?
        """
        params: List[Any] = [canteiro_id]
        if de:
            sql += " AND ev.inicio >= ?"
            params.append(de)
        if ate:
            sql += " AND ev.inicio <= ?"
            params.append(ate + ("T23:59:59-03:00" if len(ate) == 10 else ""))

        sql += " ORDER BY ev.inicio ASC, ev.id ASC"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def exportar_csv_dados(
    db_path: str,
    canteiro_identificador: Optional[str] = None,
    de: Optional[str] = None,
    ate: Optional[str] = None,
) -> str:
    """
    Gera o conteúdo CSV consolidado para `GET /api/v1/export.csv?canteiro=&de=&ate=`.
    Inclui leituras (umidade das 2 camadas, precipitação, temperatura, nível do reservatório)
    e eventos de irrigação com distinção de dispositivo (`simulador` vs `microcontrolador`).
    """
    with conexao(db_path) as conn:
        sql = """
            SELECT
                'leitura' AS categoria_registro,
                c.codigo AS canteiro,
                d.codigo AS dispositivo,
                d.tipo AS fonte_dado,
                l.tipo AS variavel,
                COALESCE(CAST(l.profundidade_cm AS TEXT), '') AS profundidade_cm,
                l.valor_bruto AS valor_bruto,
                l.valor_calibrado AS valor_calibrado,
                l.unidade AS unidade,
                l.sequencia AS sequencia,
                l.registrado_em AS registrado_em,
                l.recebido_em AS recebido_em
            FROM leitura l
            JOIN canteiro c ON c.id = l.canteiro_id
            JOIN dispositivo d ON d.id = l.dispositivo_id
            WHERE 1=1
        """
        params: List[Any] = []
        if canteiro_identificador:
            cid = _resolver_canteiro_id(conn, canteiro_identificador)
            sql += " AND l.canteiro_id = ?"
            params.append(cid)
        if de:
            sql += " AND l.registrado_em >= ?"
            params.append(de)
        if ate:
            sql += " AND l.registrado_em <= ?"
            params.append(ate + ("T23:59:59-03:00" if len(ate) == 10 else ""))

        sql += " ORDER BY l.registrado_em ASC, l.sequencia ASC"
        rows_leituras = conn.execute(sql, params).fetchall()

        # Também busca eventos de irrigação para compor o CSV completo
        sql_ev = """
            SELECT
                'evento_irrigacao' AS categoria_registro,
                c.codigo AS canteiro,
                d.codigo AS dispositivo,
                d.tipo AS fonte_dado,
                ('irrigacao_' || e.codigo) AS variavel,
                '' AS profundidade_cm,
                ev.lamina_mm AS valor_bruto,
                ev.volume_litros AS valor_calibrado,
                'mm | L' AS unidade,
                ev.sequencia AS sequencia,
                ev.inicio AS registrado_em,
                ev.recebido_em AS recebido_em
            FROM evento_irrigacao ev
            JOIN canteiro c ON c.id = ev.canteiro_id
            JOIN estrategia e ON e.id = ev.estrategia_id
            JOIN dispositivo d ON d.id = ev.dispositivo_id
            WHERE 1=1
        """
        params_ev: List[Any] = []
        if canteiro_identificador:
            cid = _resolver_canteiro_id(conn, canteiro_identificador)
            sql_ev += " AND ev.canteiro_id = ?"
            params_ev.append(cid)
        if de:
            sql_ev += " AND ev.inicio >= ?"
            params_ev.append(de)
        if ate:
            sql_ev += " AND ev.inicio <= ?"
            params_ev.append(ate + ("T23:59:59-03:00" if len(ate) == 10 else ""))

        rows_ev = conn.execute(sql_ev, params_ev).fetchall()

    todas = [dict(r) for r in rows_leituras] + [dict(r) for r in rows_ev]
    todas.sort(key=lambda x: (x["registrado_em"], x["categoria_registro"], x["sequencia"]))

    colunas = [
        "categoria_registro",
        "canteiro",
        "dispositivo",
        "fonte_dado",
        "variavel",
        "profundidade_cm",
        "valor_bruto",
        "valor_calibrado",
        "unidade",
        "sequencia",
        "registrado_em",
        "recebido_em",
    ]
    linhas_csv = [",".join(colunas)]
    for item in todas:
        vals = [str(item.get(col, "")) for col in colunas]
        linhas_csv.append(",".join(vals))
    return "\n".join(linhas_csv) + "\n"


def limpar_dados_dispositivo(db_path: str, codigo_dispositivo: str) -> Dict[str, int]:
    """Apaga leituras e eventos de um dispositivo (o simulador antes de repopular o banco)."""
    with conexao(db_path) as conn:
        row = conn.execute("SELECT id FROM dispositivo WHERE codigo = ?", (codigo_dispositivo,)).fetchone()
        if not row:
            return {"leituras": 0, "eventos": 0}
        n_l = conn.execute("DELETE FROM leitura WHERE dispositivo_id = ?", (row["id"],)).rowcount
        n_e = conn.execute("DELETE FROM evento_irrigacao WHERE dispositivo_id = ?", (row["id"],)).rowcount
    return {"leituras": n_l, "eventos": n_e}


def gravar_simulacao(db_path: str, dados: Dict[str, Any]) -> None:
    campos = ("modelo", "ciclo", "cenario", "capacidade_l", "intervalo_dias", "inicio", "fim")
    with conexao(db_path) as conn:
        conn.execute(
            """
            INSERT INTO simulacao (id, modelo, ciclo, cenario, capacidade_l, intervalo_dias, inicio, fim,
                                   parametros, canteiros, metricas, gerado_em)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET modelo = excluded.modelo, ciclo = excluded.ciclo,
                cenario = excluded.cenario, capacidade_l = excluded.capacidade_l,
                intervalo_dias = excluded.intervalo_dias, inicio = excluded.inicio, fim = excluded.fim,
                parametros = excluded.parametros, canteiros = excluded.canteiros, metricas = excluded.metricas,
                gerado_em = excluded.gerado_em
            """,
            tuple(dados[c] for c in campos) + (
                json.dumps(dados["parametros"], ensure_ascii=False),
                json.dumps(dados["canteiros"], ensure_ascii=False),
                json.dumps(dados["metricas"], ensure_ascii=False),
                agora_iso(),
            ),
        )


def ler_simulacao(db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    with conexao(db_path) as conn:
        row = conn.execute("SELECT * FROM simulacao WHERE id = 1").fetchone()
    if not row:
        return None
    d = dict(row)
    for chave in ("parametros", "canteiros", "metricas"):
        d[chave] = json.loads(d[chave])
    return d


def verificar_banco(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Para o GET /healthz: o banco abre e responde."""
    with conexao(db_path) as conn:
        modo = conn.execute("PRAGMA journal_mode").fetchone()[0]
        leituras = conn.execute("SELECT COUNT(*) FROM leitura").fetchone()[0]
    return {"journal_mode": modo, "leituras": leituras}
