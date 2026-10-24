# Etapa 1 — Modelo de Dados e Contrato da Interface de Ingestão

**Projeto:** Automação da Irrigação em Hortas Comunitárias com Sensores e IoT — PIC/FAPEMA  
**Edital:** COORD.NUPEX nº 01/2026  

Este documento formaliza o modelo relacional de persistência e o contrato HTTP/JSON da interface de ingestão e consulta, garantindo a intercambialidade transparente entre o **simulador** (`tipo = 'simulador'`) e o **microcontrolador físico** (`tipo = 'microcontrolador'`).

---

## 1. Modelo de Dados Relacional (SQLite / SQL Padrão)

### 1.1 `canteiro`
Representa a unidade física de cultivo monitorada.
| Campo | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Identificador interno |
| `codigo` | `TEXT` | `UNIQUE NOT NULL` | Código curto usado no payload (ex.: `C1`, `C2`, `C3`) |
| `nome` | `TEXT` | `NOT NULL` | Nome descritivo do canteiro |
| `area_m2` | `REAL` | `NOT NULL` | Área útil de cultivo em m² (ex.: `10.0`) |
| `cultura` | `TEXT` | `NOT NULL` | Cultura plantada (ex.: `Alface (Hortaliça folhosa)`) |
| `profundidade_raiz_mm` | `REAL` | `NOT NULL` | Espessura da zona radicular `z1` em mm (`200.0`) |
| `volume_camada_1_mm` | `REAL` | `NOT NULL` | Capacidade da camada 1 (`z1 = 200.0` mm) |
| `volume_camada_2_mm` | `REAL` | `NOT NULL` | Capacidade da camada 2 (`z2 = 200.0` mm) |

### 1.2 `estrategia`
Define a política de acionamento da irrigação.
| Campo | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Identificador interno |
| `codigo` | `TEXT` | `UNIQUE NOT NULL` | `E1`, `E2` ou `E3` |
| `nome` | `TEXT` | `NOT NULL` | Nome da estratégia |
| `parametros` | `TEXT (JSON)` | `NOT NULL` | Parâmetros estruturados em JSON (`theta_lim`, `lamina_fixa_mm`, `limiar_deficit_mm`, `capacidade_reservatorio_l`, `intervalo_reabastecimento_dias`) |

### 1.3 `canteiro_estrategia`
Histórico temporal de vinculação entre canteiro e estratégia vigente.
| Campo | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Identificador interno |
| `canteiro_id` | `INTEGER` | ` NOT NULL REFERENCES canteiro(id)` | Canteiro associado |
| `estrategia_id` | `INTEGER` | `NOT NULL REFERENCES estrategia(id)` | Estratégia ativa no período |
| `inicio` | `TEXT (ISO-8601)` | `NOT NULL` | Início de vigência |
| `fim` | `TEXT (ISO-8601)` | `NULL` | Fim de vigência (`NULL` se ainda ativa) |

### 1.4 `dispositivo`
Emissor autorizado (simulador ou microcontrolador em campo).
| Campo | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Identificador interno |
| `codigo` | `TEXT` | `UNIQUE NOT NULL` | Identificador enviado no payload (ex.: `sim-001`, `esp32-001`) |
| `nome` | `TEXT` | `NOT NULL` | Descrição do dispositivo |
| `tipo` | `TEXT` | `CHECK (tipo IN ('simulador', 'microcontrolador'))` | Distingue dado sintético de dado medido em campo |
| `token` | `TEXT` | `UNIQUE NOT NULL` | Token Bearer de autenticação |
| `criado_em` | `TEXT (ISO-8601)` | `NOT NULL` | Timestamp de criação |

### 1.5 `calibracao`
Curva de calibração para conversão de leitura bruta (ex.: ADC / mV) em grandeza física calibrada.
| Campo | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Identificador interno |
| `sensor_id` | `TEXT` | `NOT NULL` | Identificador do sensor ou tipo (`umidade_solo`, `temperatura_ar`, etc.) |
| `coeficientes` | `TEXT (JSON)` | `NOT NULL` | Coeficientes da equação (ex.: `{"escala": 0.0001, "offset": 0.0}`) |
| `metodo` | `TEXT` | `NOT NULL` | Método de calibração (`linear_sintetica`, `gravimetrica_campo`) |
| `data` | `TEXT (ISO-8601)` | `NOT NULL` | Data da calibração |
| `observacoes` | `TEXT` | `NULL` | Observações adicionais |

### 1.6 `leitura`
Série temporal de variáveis medidas ou simuladas.
| Campo | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Identificador interno |
| `dispositivo_id` | `INTEGER` | `NOT NULL REFERENCES dispositivo(id)` | Dispositivo emissor |
| `canteiro_id` | `INTEGER` | `NOT NULL REFERENCES canteiro(id)` | Canteiro monitorado |
| `tipo` | `TEXT` | `CHECK (tipo IN ('umidade_solo', 'temperatura_ar', 'precipitacao', 'nivel_reservatorio'))` | Grandeza medida |
| `profundidade_cm` | `REAL` | `NULL` | `10` (Camada 1: 0–20 cm), `30` (Camada 2: 20–40 cm) ou `NULL` |
| `valor_bruto` | `REAL` | `NOT NULL` | Valor original emitido pelo dispositivo (preservado integralmente) |
| `valor_calibrado` | `REAL` | `NOT NULL` | Valor em unidade física após aplicação da calibração vigente |
| `unidade` | `TEXT` | `NOT NULL` | `cm3/cm3`, `°C`, `mm`, `L` |
| `calibracao_id` | `INTEGER` | `NOT NULL REFERENCES calibracao(id)` | Referência à calibração aplicada |
| `sequencia` | `INTEGER` | `NOT NULL` | Número de sequência monotônico por dispositivo |
| `registrado_em` | `TEXT (ISO-8601)` | `NOT NULL` | Timestamp do relógio do dispositivo |
| `recebido_em` | `TEXT (ISO-8601)` | `NOT NULL` | Timestamp de recepção no servidor |

- **Restrição de Idempotência:** `UNIQUE(dispositivo_id, sequencia)`

### 1.7 `evento_irrigacao`
Registro de acionamentos da irrigação.
| Campo | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Identificador interno |
| `dispositivo_id` | `INTEGER` | `NOT NULL REFERENCES dispositivo(id)` | Dispositivo emissor |
| `canteiro_id` | `INTEGER` | `NOT NULL REFERENCES canteiro(id)` | Canteiro irrigado |
| `estrategia_id` | `INTEGER` | `NOT NULL REFERENCES estrategia(id)` | Estratégia que comandou o evento |
| `inicio` | `TEXT (ISO-8601)` | `NOT NULL` | Início da aplicação |
| `fim` | `TEXT (ISO-8601)` | `NOT NULL` | Término da aplicação |
| `lamina_mm` | `REAL` | `NOT NULL` | Lâmina aplicada (mm) |
| `volume_litros` | `REAL` | `NOT NULL` | Volume correspondente (L = `lamina_mm * area_m2`) |
| `origem` | `TEXT` | `CHECK (origem IN ('automatico', 'manual', 'simulado'))` | Origem do acionamento |
| `sequencia` | `INTEGER` | `NOT NULL` | Número de sequência monotônico por dispositivo |
| `registrado_em` | `TEXT (ISO-8601)` | `NOT NULL` | Timestamp do relógio do dispositivo |
| `recebido_em` | `TEXT (ISO-8601)` | `NOT NULL` | Timestamp de recepção no servidor |

- **Restrição de Idempotência:** `UNIQUE(dispositivo_id, sequencia)`

---

## 2. Contrato HTTP da Interface de Ingestão e Consulta

### 2.1 Autenticação
Endpoints `POST` exigem cabeçalho:
```http
Authorization: Bearer <token-do-dispositivo>
```
O token deve pertencer ao `dispositivo` informado no corpo da requisição (`401 Unauthorized` ou `403 Forbidden` caso inválido ou divergente).

### 2.2 `POST /api/v1/leituras`
Recebe um lote de leituras. Aplica calibração vigente e garante idempotência pelo par `(dispositivo, seq)`.

**Request:**
```json
{
  "dispositivo": "sim-001",
  "leituras": [
    {
      "seq": 1042,
      "canteiro": "C1",
      "tipo": "umidade_solo",
      "profundidade_cm": 10,
      "valor_bruto": 2310,
      "registrado_em": "2026-10-16T14:00:00-03:00"
    }
  ]
}
```

**Response (`200 OK`):**
```json
{
  "aceitos": 1,
  "ignorados": 0,
  "ultima_sequencia": 1042
}
```

### 2.3 `POST /api/v1/eventos-irrigacao`
Recebe um lote de eventos de irrigação com semântica idêntica de idempotência por `(dispositivo, seq)`.

**Request:**
```json
{
  "dispositivo": "sim-001",
  "eventos": [
    {
      "seq": 501,
      "canteiro": "C1",
      "estrategia": "E1",
      "inicio": "2026-10-16T06:00:00-03:00",
      "fim": "2026-10-16T06:30:00-03:00",
      "lamina_mm": 10.0,
      "volume_litros": 100.0,
      "origem": "simulado",
      "registrado_em": "2026-10-16T06:30:00-03:00"
    }
  ]
}
```

**Response (`200 OK`):**
```json
{
  "aceitos": 1,
  "ignorados": 0,
  "ultima_sequencia": 501
}
```

### 2.4 Endpoints de Consulta e Exportação
- `GET /api/v1/canteiros`: Lista todos os canteiros cadastrados, suas estratégias vigentes e metadados.
- `GET /api/v1/canteiros/{id}/series?de=&ate=&tipo=`: Retorna a série temporal de leituras calibradas e brutas do canteiro (`{id}` aceita `id` numérico ou `codigo` como `C1`).
- `GET /api/v1/canteiros/{id}/eventos?de=&ate=`: Retorna os eventos de irrigação do canteiro no período.
- `GET /api/v1/export.csv?canteiro=&de=&ate=`: Exporta em formato CSV as leituras e eventos consolidados para análise externa.
- `GET /api/v1/comparativo`: Retorna a matriz completa de métricas de saída (Seção 5) das três estratégias (`E1`, `E2`, `E3`) nos cenários de escassez (`Abundante`, `Moderado`, `Restrito`) e períodos climáticos (`Seca`, `Chuvosa`), além do relatório de validação física do modelo (Seção 6).
