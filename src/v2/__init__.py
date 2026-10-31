"""
Modelo v2 do simulador de irrigação PIC/FAPEMA (descrição em docs/MODELO.md).

- `fao56`: equações do FAO-56 (Allen et al., 1998), sem entrada/saída.
- `inmet`: leitura do arquivo horário do INMET, sem imputação.
- `clima`: série horária em hora local, ET0 horária (Penman-Monteith) e ciclos de 70 dias.

O v1 (`src/water_balance.py`, `src/climate.py`, `src/experiments.py`) continua intacto.
"""
