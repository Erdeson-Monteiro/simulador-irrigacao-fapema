"""
Camada de persistência SQLite — Inicialização do schema, dados de referência,
ingestão idempotente em lote e consultas (Seções 7 e 8).
"""

from __future__ import annotations
from datetime import datetime, timezone, timedelta
import json
import os
import sqlite3
from typing import Dict, Any, List, Optional, Tuple


FUSO_BR = timezone(timedelta(hours=-3))
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "irrigacao.db"
)
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def agora_iso() -> str:
    """Retorna o timestamp atual em ISO-8601 com fuso -03:00."""
    return datetime.now(FUSO_BR).isoformat(timespec="seconds")


def obter_conexao(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Abre conexão SQLite com chaves estrangeiras e row_factory configurados."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def inicializar_banco(db_path: str = DEFAULT_DB_PATH) -> None:
    """Executa o schema SQL e insere os registros base caso ainda não existam."""
    with obter_conexao(db_path) as conn:
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

        # 2. Estratégias de acionamento (Seção 4 e Seção 7)
        estrategias_iniciais = [
            (
                1,
                "E1",
                "Limiar Fixo",
                json.dumps({"theta_lim": 0.231, "lamina_fixa_mm": 10.0}),
            ),
            (
                2,
                "E2",
                "Balanço Hídrico",
                json.dumps({"limiar_deficit_mm": 10.0}),
            ),
            (
                3,
                "E3",
                "Balanço Hídrico com Restrição de Reservatório",
                json.dumps(
                    {
                        "limiar_deficit_mm": 10.0,
                        "cenarios": {
                            "Abundante": {"capacidade_l": 1000.0, "intervalo_dias": 3},
                            "Moderado": {"capacidade_l": 500.0, "intervalo_dias": 7},
                            "Restrito": {"capacidade_l": 500.0, "intervalo_dias": 14},
                        },
                    }
                ),
            ),
        ]
        for est in estrategias_iniciais:
            conn.execute(
                """
                INSERT OR IGNORE INTO estrategia (id, codigo, nome, parametros)
                VALUES (?, ?, ?, ?)
                """,
                est,
            )

        # 3. Canteiros monitorados (Seção 7)
        canteiros_iniciais = [
            (1, "C1", "Canteiro 1 — E1 (Limiar Fixo)", 10.0, "Alface (Hortaliça Folhosa)", 200.0, 200.0, 200.0, 1),
            (2, "C2", "Canteiro 2 — E2 (Balanço Hídrico)", 10.0, "Alface (Hortaliça Folhosa)", 200.0, 200.0, 200.0, 2),
            (3, "C3", "Canteiro 3 — E3 (Reservatório Moderado 500L/7d)", 10.0, "Alface (Hortaliça Folhosa)", 200.0, 200.0, 200.0, 3),
            (4, "C4", "Canteiro 4 — E3 (Reservatório Restrito 500L/14d)", 10.0, "Alface (Hortaliça Folhosa)", 200.0, 200.0, 200.0, 3),
            (5, "C5", "Canteiro 5 — E3 (Reservatório Abundante 1000L/3d)", 10.0, "Alface (Hortaliça Folhosa)", 200.0, 200.0, 200.0, 3),
        ]
        for c_id, cod, nome, area, cult, prof, v1, v2, est_id in canteiros_iniciais:
            conn.execute(
                """
                INSERT OR IGNORE INTO canteiro
                (id, codigo, nome, area_m2, cultura, profundidade_raiz_mm, volume_camada_1_mm, volume_camada_2_mm)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (c_id, cod, nome, area, cult, prof, v1, v2),
            )
            # Vincula histórico em canteiro_estrategia se não existir
            cur = conn.execute(
                "SELECT COUNT(*) AS cnt FROM canteiro_estrategia WHERE canteiro_id = ?", (c_id,)
            )
            if cur.fetchone()["cnt"] == 0:
                conn.execute(
                    """
                    INSERT INTO canteiro_estrategia (canteiro_id, estrategia_id, inicio, fim)
                    VALUES (?, ?, ?, NULL)
                    """,
                    (c_id, est_id, "2026-01-01T00:00:00-03:00"),
                )

        # 4. Dispositivos emissores (Seção 7 e Seção 12)
        dispositivos_iniciais = [
            (
                1,
                "sim-001",
                "Simulador de Balanço Hídrico v1",
                "simulador",
                "tok-sim-001-fapema",
                "2026-01-01T00:00:00-03:00",
            ),
            (
                2,
                "esp32-001",
                "Protótipo Microcontrolador Campo v1",
                "microcontrolador",
                "tok-esp32-001-fapema",
                "2026-01-01T00:00:00-03:00",
            ),
        ]
        for disp in dispositivos_iniciais:
            conn.execute(
                """
                INSERT OR IGNORE INTO dispositivo (id, codigo, nome, tipo, token, criado_em)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                disp,
            )
        conn.commit()


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
    if not row:
        raise PermissionError(f"Dispositivo '{codigo_dispositivo}' não cadastrado.")
    if row["token"] != token:
        raise PermissionError("Token inválido para o dispositivo informado.")
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

    with obter_conexao(db_path) as conn:
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

    with obter_conexao(db_path) as conn:
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
    with obter_conexao(db_path) as conn:
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
    with obter_conexao(db_path) as conn:
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
    with obter_conexao(db_path) as conn:
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
    with obter_conexao(db_path) as conn:
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
