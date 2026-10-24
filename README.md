# Plataforma de Irrigação Automatizada e Simulação de Balanço Hídrico — PIC/FAPEMA

Implementação de ponta a ponta da especificação técnica do projeto **"Automação da Irrigação em Hortas Comunitárias com Sensores e IoT — PIC/FAPEMA"** (Edital COORD.NUPEX nº 01/2026), cobrindo integralmente as **7 etapas** da Seção 11 de [`projeto-irigaçao.md`](./projeto-iriga%C3%A7ao.md).

---

## Arquitetura e Estrutura do Projeto

- [`docs/CONTRATO_E_MODELO_DADOS.md`](./docs/CONTRATO_E_MODELO_DADOS.md) — **Etapa 1:** Especificação formal do esquema relacional e contrato HTTP/JSON (`POST /api/v1/leituras`, `POST /api/v1/eventos-irrigacao`, consultas e exportação CSV).
- [`docs/RELATORIO_RESULTADOS_ARTIGO.md`](./docs/RELATORIO_RESULTADOS_ARTIGO.md) — **Etapas 2, 3 e 4:** Relatório consolidado com os resultados dos 3 testes obrigatórios de validação física (Seção 6), diagnóstico de falhas da série INMET de Balsas-MA (Seção 3.5) e tabela comparativa de métricas das estratégias `E1`, `E2` e `E3` nos cenários `Abundante`, `Moderado` e `Restrito` (Seções 4 e 5).
- [`src/schema.sql`](./src/schema.sql) e [`src/database.py`](./src/database.py) — **Etapa 5:** Persistência SQLite (`canteiro`, `estrategia`, `canteiro_estrategia`, `dispositivo`, `calibracao`, `leitura`, `evento_irrigacao`) com autenticação por token Bearer, preservação do valor bruto junto ao calibrado, duplo timestamp (`registrado_em` e `recebido_em`) e idempotência por `(dispositivo_id, sequencia)`.
- [`src/water_balance.py`](./src/water_balance.py) — **Etapa 2:** Modelo de balanço hídrico de duas camadas (`0–20 cm` e `20–40 cm`), evapotranspiração de referência por Hargreaves-Samani (`ET0` e `Ra` para Balsas-MA, `φ = -7,53°`), estratégias `E1`, `E2`, `E3` e testes de validação da Seção 6.
- [`src/climate.py`](./src/climate.py) — **Etapa 3:** Leitura e tratamento de falhas da série climática histórica do INMET (`data/inmet_balsas_ma.csv`), interpolação linear de lacunas curtas (`<= 3 dias`) e descarte de lacunas longas.
- [`src/experiments.py`](./src/experiments.py) — **Etapa 4:** Execução automatizada da matriz experimental completa e geração de relatórios em JSON (`data/relatorio_simulacao.json`) e Markdown.
- [`src/simulator.py`](./src/simulator.py) — **Etapa 6:** Simulador que executa o modelo sobre a série climática e transmite lotes HTTP idempotentes para a interface de ingestão como dispositivo `sim-001` (`tipo = 'simulador'`).
- [`src/api_server.py`](./src/api_server.py) e [`src/static/index.html`](./src/static/index.html) — **Etapas 5 e 7:** Servidor HTTP e Painel Web em página única com gráficos SVG de umidade das duas camadas, eventos de irrigação, limiar de referência (`θ_lim = 0,231 cm³/cm³`), nível do reservatório, comparativo `E1 × E2 × E3` e exportação CSV.
- [`tests/test_end_to_end.py`](./tests/test_end_to_end.py) — Suíte de testes automatizados de ponta a ponta.

---

## Como Executar

Não há dependências externas obrigatórias além do **Python 3.10+** (biblioteca padrão `sqlite3`, `http.server`, `unittest`).

### 1. Rodar a suíte de testes automatizados
```bash
python3 -m unittest discover -s tests -v
```

### 2. Executar o pipeline completo de ponta a ponta (Etapas 1 a 6)
```bash
python3 main.py
```

### 3. Iniciar o servidor HTTP e o Painel Web (Etapa 7)
```bash
python3 main.py --serve --port 8000
```
Acesse **`http://localhost:8000`** no navegador para visualizar o Painel Web ou consultar os endpoints:
- `GET  http://localhost:8000/api/v1/canteiros`
- `GET  http://localhost:8000/api/v1/canteiros/C1/series?de=2026-07-01&ate=2026-09-08`
- `GET  http://localhost:8000/api/v1/canteiros/C1/eventos`
- `GET  http://localhost:8000/api/v1/export.csv?canteiro=C1`
- `POST http://localhost:8000/api/v1/leituras`
- `POST http://localhost:8000/api/v1/eventos-irrigacao`
