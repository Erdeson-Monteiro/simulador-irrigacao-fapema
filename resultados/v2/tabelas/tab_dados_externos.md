**Dados externos**

| Arquivo | Pasta de destino | URL | Situação |
|---|---|---|---|
| Normal climatológica 1991–2020, precipitação (planilha do INMET) | `data/raw/normais/Normal-Climatologica-PREC.xlsx` | https://portal.inmet.gov.br/uploads/normais/Normal-Climatologica-PREC.xlsx | ausente |
| Dados horários de 2024, estação A204 (extraídos de 2024.zip) | `data/raw/downloads/2024.zip` | https://portal.inmet.gov.br/uploads/dadoshistoricos/2024.zip | ausente |
| Dados horários de 2025, estação A204 (extraídos de 2025.zip) | `data/raw/downloads/2025.zip` | https://portal.inmet.gov.br/uploads/dadoshistoricos/2025.zip | ausente |

Arquivos ausentes não são estimados. Depois de baixá-los, rode `python3 main.py dados --preparar` e `python3 main.py pipeline`.
