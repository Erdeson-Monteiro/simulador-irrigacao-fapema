**Dados externos**

| Arquivo | Pasta de destino | URL | Situação |
|---|---|---|---|
| Dados horários de 2024, estação A204 (extraídos de 2024.zip) | `data/raw/INMET_NE_MA_A204_BALSAS_01-01-2024_A_31-12-2024.CSV` | https://portal.inmet.gov.br/uploads/dadoshistoricos/2024.zip | presente e registrado |
| Dados horários de 2025, estação A204 (extraídos de 2025.zip) | `data/raw/INMET_NE_MA_A204_BALSAS_01-01-2025_A_31-12-2025.CSV` | https://portal.inmet.gov.br/uploads/dadoshistoricos/2025.zip | presente e registrado |

Arquivos ausentes não são estimados. Depois de baixá-los, rode `python3 main.py dados --preparar` e `python3 main.py pipeline`.
