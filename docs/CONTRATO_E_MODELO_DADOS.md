# Modelo de dados e contrato da interface de ingestão

**Projeto:** Automação da Irrigação em Hortas Comunitárias com Sensores e IoT — PIC/FAPEMA  
**Edital:** COORD.NUPEX nº 01/2026  

Este documento formaliza o modelo relacional de persistência e o contrato HTTP/JSON da interface de ingestão e consulta, garantindo a intercambialidade transparente entre o **simulador** (`tipo = 'simulador'`) e o **microcontrolador físico** (`tipo = 'microcontrolador'`).

**Versão do modelo v2.** O banco é populado por `python3 main.py pipeline` (ou `simular`) com três canteiros virtuais, `C1` (E1, limiar fixo), `C2` (E2, reposição por balanço hídrico) e `C3` (E3, racionamento uniforme), que enviam leituras horárias do modelo v2 por este mesmo contrato. O SQLite roda em modo WAL. O token do dispositivo nunca é guardado: só o SHA-256 dele.

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
| `parametros` | `TEXT (JSON)` | `NOT NULL` | Regra e parâmetros em JSON, lidos da configuração do modelo v2 (`regra`; `theta_lim` e `lamina_mm` em E1; `raw_mm` em E2 e E3) |

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
| `token_sha256` | `TEXT` | `UNIQUE NULL` | SHA-256 do token Bearer (o token em si nunca é guardado); `NULL` = dispositivo desabilitado |
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

### 1.8 `simulacao`
Simulação do modelo v2 carregada no banco (uma única linha, `id = 1`), lida pelo painel: `modelo`, `ciclo`, `cenario`, `capacidade_l`, `intervalo_dias`, `inicio`, `fim`, `parametros` (JSON com todos os parâmetros e derivados, inclusive `theta_lim`, `raw_mm` e `taw_mm`), `canteiros` (JSON, canteiro → estratégia), `metricas` (JSON, estratégia → métricas da rodada) e `gerado_em`.

---

## 2. Contrato HTTP da Interface de Ingestão e Consulta

### 2.1 Autenticação
Endpoints `POST` exigem cabeçalho:
```http
Authorization: Bearer <token-do-dispositivo>
```
O token deve pertencer ao `dispositivo` informado no corpo da requisição (`401 Unauthorized` caso inválido, divergente ou de dispositivo desabilitado).

- O servidor compara o SHA-256 do token recebido com o hash guardado, em tempo constante (`hmac.compare_digest`), e nunca escreve o token em log: o log de acesso traz só método, caminho e status.
- O token de produção do `sim-001` vem da variável de ambiente `DEVICE_TOKEN` (pelo menos 24 caracteres); `python3 main.py serve` não sobe sem ela e troca o hash guardado pelo do token configurado.
- Os tokens que estiveram no código até a tag `v1-parecer` estão comprometidos: `serve` e `pipeline` os recusam como `DEVICE_TOKEN`, e o `esp32-001` fica desabilitado até receber um token novo.

### 2.1.1 Limites e CORS
- Corpo de requisição limitado a 1 MB (`413 Payload Too Large`); `Content-Length` é obrigatório (`411 Length Required`); o corpo precisa ser um objeto JSON (`400`).
- CORS só para a origem configurada em `CORS_ORIGIN`; sem ela, nenhum cabeçalho `Access-Control-Allow-Origin` é enviado (o painel é servido pela mesma origem da API).
- Erros internos respondem `500` com mensagem genérica, sem detalhes do servidor.

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
- `GET /api/v1/resultados` (e o nome antigo `GET /api/v1/comparativo`): devolve `resultados/v2/resultados.json`, com parâmetros, cenários e as métricas do v2 de cada ciclo, cenário e estratégia. O servidor não roda simulação: se o arquivo não existir, responde `404` pedindo `python3 main.py pipeline`.
- `GET /api/v1/simulacao`: a simulação carregada no banco (tabela `simulacao`).
- `GET /api/v1/tabelas/{nome}`: uma tabela do artigo em JSON (`campos`, `linhas`); só `tab_desempenho_chuvoso`, `tab_desempenho_seco`, `tab_capacidade_minima`, `tab_clima_ciclos` e `tab_cenarios`.
- `GET /resultados/figuras/{nome}.png`: as Figuras 1 e 2 do artigo (`figura1_sensibilidade_e1.png`, `figura2_seco_restrito.png`).
- `GET /healthz`: `{"status": "ok", "banco": {...}}` quando o banco abre e responde (usado pelo HEALTHCHECK do Docker).
