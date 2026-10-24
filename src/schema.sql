-- Schema SQLite — Plataforma de Irrigação Automatizada PIC/FAPEMA
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS canteiro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    area_m2 REAL NOT NULL,
    cultura TEXT NOT NULL,
    profundidade_raiz_mm REAL NOT NULL,
    volume_camada_1_mm REAL NOT NULL,
    volume_camada_2_mm REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS estrategia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    parametros TEXT NOT NULL -- JSON
);

CREATE TABLE IF NOT EXISTS canteiro_estrategia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canteiro_id INTEGER NOT NULL REFERENCES canteiro(id),
    estrategia_id INTEGER NOT NULL REFERENCES estrategia(id),
    inicio TEXT NOT NULL,
    fim TEXT NULL
);

CREATE TABLE IF NOT EXISTS dispositivo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('simulador', 'microcontrolador')),
    token TEXT UNIQUE NOT NULL,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS calibracao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id TEXT NOT NULL,
    coeficientes TEXT NOT NULL, -- JSON
    metodo TEXT NOT NULL,
    data TEXT NOT NULL,
    observacoes TEXT NULL
);

CREATE TABLE IF NOT EXISTS leitura (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dispositivo_id INTEGER NOT NULL REFERENCES dispositivo(id),
    canteiro_id INTEGER NOT NULL REFERENCES canteiro(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('umidade_solo', 'temperatura_ar', 'precipitacao', 'nivel_reservatorio')),
    profundidade_cm REAL NULL,
    valor_bruto REAL NOT NULL,
    valor_calibrado REAL NOT NULL,
    unidade TEXT NOT NULL,
    calibracao_id INTEGER NOT NULL REFERENCES calibracao(id),
    sequencia INTEGER NOT NULL,
    registrado_em TEXT NOT NULL,
    recebido_em TEXT NOT NULL,
    UNIQUE(dispositivo_id, sequencia)
);

CREATE INDEX IF NOT EXISTS idx_leitura_canteiro_tempo ON leitura(canteiro_id, registrado_em);
CREATE INDEX IF NOT EXISTS idx_leitura_tipo ON leitura(tipo);

CREATE TABLE IF NOT EXISTS evento_irrigacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dispositivo_id INTEGER NOT NULL REFERENCES dispositivo(id),
    canteiro_id INTEGER NOT NULL REFERENCES canteiro(id),
    estrategia_id INTEGER NOT NULL REFERENCES estrategia(id),
    inicio TEXT NOT NULL,
    fim TEXT NOT NULL,
    lamina_mm REAL NOT NULL,
    volume_litros REAL NOT NULL,
    origem TEXT NOT NULL CHECK (origem IN ('automatico', 'manual', 'simulado')),
    sequencia INTEGER NOT NULL,
    registrado_em TEXT NOT NULL,
    recebido_em TEXT NOT NULL,
    UNIQUE(dispositivo_id, sequencia)
);

CREATE INDEX IF NOT EXISTS idx_evento_canteiro_tempo ON evento_irrigacao(canteiro_id, inicio);
