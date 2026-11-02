# Relatório Final de Dados, Tabelas, Figuras e Evidências para o Artigo Científico

---

## 1. Identificação

| Campo | Informação |
|---|---|
| **Projeto** | Automação da Irrigação em Hortas Comunitárias com Sensores e IoT — PIC/FAPEMA |
| **Edital** | COORD.NUPEX nº 01/2026 |
| **Orientador** | Prof. Alex Rogaleski Marques |
| **Bolsista** | Erdeson |
| **Referência no Plano de Trabalho** | Atividade 2.3 — Desenvolvimento do software e integração IoT (out/2026 a fev/2027) |
| **Data de Geração do Relatório** | 2026-11-01 |

---

## 2. Procedência e Provas do Dado Climático

### 2.1 (a) Bloco de Metadados do Arquivo Bruto (Reproduzido Verbatim)

```text
REGIAO:;NE
UF:;MA
ESTACAO:;BALSAS
CODIGO (WMO):;A204
LATITUDE:;-7,45555555
LONGITUDE:;-46,02749999
ALTITUDE:;271,03
DATA DE FUNDACAO:;26/10/07
```

### 2.2 (b, c, e, f, g) Identificação Criptográfica, Dimensional, Origem e Metadados Extraídos

| Item de Auditoria | Valor Extraído Diretamente do Arquivo Bruto |
|---|---|
| **Caminho do arquivo bruto intocado** | `data/raw/INMET_NE_MA_A204_BALSAS_01-01-2023_A_31-12-2023.CSV` |
| **SHA-256 do arquivo bruto** | `7aa68f3a9a2c09ef19a822490fb5fe957c1e0b37bed7ca6b084e3e38d450b233` |
| **Tamanho exato em bytes** | `764609 bytes` |
| **Número total de linhas** | `8769 linhas` (`8` linhas de metadados + `1` linha de cabeçalho + `8760` linhas horárias de dados) |
| **Codificação original do arquivo** | `iso-8859-1 (latin1)` |
| **Data de download** | `2026-10-17` |
| **URL de origem oficial (INMET)** | `https://portal.inmet.gov.br/uploads/dadoshistoricos/2023.zip (entrada: INMET_NE_MA_A204_BALSAS_01-01-2023_A_31-12-2023.CSV)` |
| **Código da estação (extraído do cabeçalho)** | `A204` (campo `CODIGO (WMO):;`) |
| **Nome da estação (extraído do cabeçalho)** | `BALSAS` — `MA` / Região `NE` (campos `ESTACAO:;`, `UF:;`, `REGIAO:;`) |
| **Latitude extraída do arquivo (usada em Ra)** | `-7,45555555` → `-7.45555555°` (campo `LATITUDE:;`) |
| **Longitude extraída do arquivo** | `-46,02749999` → `-46.02749999°` (campo `LONGITUDE:;`) |
| **Altitude extraída do arquivo** | `271,03 m` → `271.03 m` (campo `ALTITUDE:;`) |
| **Data de fundação da estação** | `26/10/07` (campo `DATA DE FUNDACAO:;`) |
| **Intervalo de datas efetivamente presente no arquivo** | `2023-01-01` a `2023-12-31` (`365` dias, resolução `Horária (24 registros UTC/dia)`) |

### 2.3 (d) Cabeçalho de Colunas, 5 Primeiras e 5 Últimas Linhas de Dados (Verbatim)

**Linha de cabeçalho de dados (linha 9 do arquivo bruto):**
```text
Data;Hora UTC;PRECIPITAÇÃO TOTAL, HORÁRIO (mm);PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB);PRESSÃO ATMOSFERICA MAX.NA HORA ANT. (AUT) (mB);PRESSÃO ATMOSFERICA MIN. NA HORA ANT. (AUT) (mB);RADIACAO GLOBAL (Kj/m²);TEMPERATURA DO AR - BULBO SECO, HORARIA (°C);TEMPERATURA DO PONTO DE ORVALHO (°C);TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C);TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C);TEMPERATURA ORVALHO MAX. NA HORA ANT. (AUT) (°C);TEMPERATURA ORVALHO MIN. NA HORA ANT. (AUT) (°C);UMIDADE REL. MAX. NA HORA ANT. (AUT) (%);UMIDADE REL. MIN. NA HORA ANT. (AUT) (%);UMIDADE RELATIVA DO AR, HORARIA (%);VENTO, DIREÇÃO HORARIA (gr) (° (gr));VENTO, RAJADA MAXIMA (m/s);VENTO, VELOCIDADE HORARIA (m/s);
```

**5 primeiras linhas de dados (linhas 10 a 14 do arquivo bruto):**
```text
2023/01/01;0000 UTC;0;981;981;980;;25,7;21,3;27,7;25,7;21,3;20,2;77;64;77;238;4,4;,9;
2023/01/01;0100 UTC;0;981,7;981,7;981;;25,1;21,6;25,7;25;21,9;21,2;82;77;81;107;2,6;,2;
2023/01/01;0200 UTC;0;981,5;981,8;981,5;;24,8;21,2;25,2;24,8;21,7;21,2;81;79;81;141;1,8;0;
2023/01/01;0300 UTC;0;981,1;981,5;981,1;;24,6;21,3;24,8;24,3;22;21,2;85;81;82;137;1,7;,1;
2023/01/01;0400 UTC;0;980,3;981,1;980,3;;23,5;21,4;24,6;23,4;21,5;21,2;88;82;88;30;2,1;,9;
```

**5 últimas linhas de dados (linhas 8765 a 8769 do arquivo bruto):**
```text
2023/12/31;1900 UTC;0;979,8;980,1;979,8;625;29,5;22,8;30,5;29,5;23;22,1;68;62;67;262;2,7;,2;
2023/12/31;2000 UTC;6,2;979,9;979,9;979,5;343,9;25,5;23;29,5;25,5;23,8;22,6;87;67;86;234;4,4;1,1;
2023/12/31;2100 UTC;0;980,1;980,2;979,8;201,1;25,8;23,7;25,8;25,5;23,7;23;88;86;88;226;2;,1;
2023/12/31;2200 UTC;0;980,5;980,7;980;4,3;26;23,5;26;25,6;23,6;23,2;88;86;86;282;1,9;,2;
2023/12/31;2300 UTC;0;981,6;981,6;980,5;;25;22,3;26,2;25;23,6;22,3;86;84;85;345;5,3;,7;
```

### 2.4 (h) Estatísticas Descritivas por Variável e por Ciclo

Arquivo CSV correspondente: [`tabelas/T1b_estatisticas_descritivas_por_variavel_ciclo.csv`](tabelas/T1b_estatisticas_descritivas_por_variavel_ciclo.csv)

O confronto com a normal climatológica 1991–2020 de Balsas é feito pelo v2 (`resultados/v2/tabelas/tab_normal_climatologica.md`).

| Ciclo | Intervalo de Datas | Variável | Mínimo | Máximo | Média | Desvio-Padrão | Mediana | Soma no Ciclo |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `Estacao_Chuvosa` | `2023-01-15 a 2023-03-25` | Precipitação diária P (mm) | 0.00 | 96.80 | 4.27 | 12.96 | 0.20 | 299.20 |
| `Estacao_Chuvosa` | `2023-01-15 a 2023-03-25` | Temperatura máxima diária T_max (°C) | 23.90 | 35.90 | 32.25 | 2.15 | 32.50 | 2257.80 |
| `Estacao_Chuvosa` | `2023-01-15 a 2023-03-25` | Temperatura mínima diária T_min (°C) | 19.20 | 23.30 | 21.65 | 0.84 | 21.75 | 1515.80 |
| `Estacao_Chuvosa` | `2023-01-15 a 2023-03-25` | Temperatura média diária T_med (°C) | 21.89 | 27.97 | 25.63 | 1.21 | 25.67 | 1793.96 |
| `Estacao_Chuvosa` | `2023-01-15 a 2023-03-25` | Evapotranspiração de referência ET0 (mm/dia) | 2.35 | 6.35 | 5.10 | 0.70 | 5.09 | 356.77 |
| `Estacao_Chuvosa` | `2023-01-15 a 2023-03-25` | Evapotranspiração da cultura ETc (mm/dia) | 2.23 | 6.35 | 4.72 | 0.94 | 4.82 | 330.57 |
| `Estacao_Seca` | `2023-07-01 a 2023-09-08` | Precipitação diária P (mm) | 0.00 | 27.60 | 0.60 | 3.49 | 0.00 | 42.20 |
| `Estacao_Seca` | `2023-07-01 a 2023-09-08` | Temperatura máxima diária T_max (°C) | 33.10 | 40.10 | 36.75 | 1.31 | 36.95 | 2572.60 |
| `Estacao_Seca` | `2023-07-01 a 2023-09-08` | Temperatura mínima diária T_min (°C) | 14.20 | 24.70 | 18.95 | 2.28 | 18.75 | 1326.50 |
| `Estacao_Seca` | `2023-07-01 a 2023-09-08` | Temperatura média diária T_med (°C) | 24.30 | 30.20 | 27.36 | 1.32 | 27.55 | 1914.95 |
| `Estacao_Seca` | `2023-07-01 a 2023-09-08` | Evapotranspiração de referência ET0 (mm/dia) | 4.71 | 6.96 | 5.84 | 0.49 | 5.84 | 408.84 |
| `Estacao_Seca` | `2023-07-01 a 2023-09-08` | Evapotranspiração da cultura ETc (mm/dia) | 3.30 | 6.96 | 5.44 | 1.01 | 5.78 | 380.89 |

---

## 3. Qualidade e Tratamento do Dado (Tabela T7)

Arquivo CSV correspondente: [`tabelas/T7_qualidade_dado_climatico.csv`](tabelas/T7_qualidade_dado_climatico.csv)

- **Escolha do ano de 2023:** este relatório do v1 usa só o arquivo de 2023. A completude da estação `A204` em 2024 e 2025 é conferida pelo v2, a partir dos arquivos do INMET (`resultados/v2/tabelas/tab_completude_anos.md`). No arquivo de 2023, os dias inteiros sem dado somam `34` (maior lacuna de `17` dias): 2023-10-26 a 2023-11-11 (17d); 2023-11-16 a 2023-11-25 (10d); 2023-12-05 a 2023-12-11 (7d), todos fora dos ciclos.
- **Qualidade nos dois ciclos simulados (`Estacao_Chuvosa`: `2023-01-15` a `2023-03-25`; `Estacao_Seca`: `2023-07-01` a `2023-09-08`):** `0` dias ausentes e `0` horas ausentes somando todas as variáveis; registros horários esperados por ciclo: `Estacao_Chuvosa` `1.680`; `Estacao_Seca` `1.680`.

| Escopo | Intervalo de Datas | Variável | Coluna Original BDMEP | Dias Aval. | Dias Ausentes | % Dias Ausentes | Horas Aval. | Horas Ausentes | % Horas Ausentes | Maior Lacuna (dias) | Datas de Cada Lacuna | Tratamento Aplicado |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `Estacao_Chuvosa` | `2023-01-15 a 2023-03-25` | `t_max` | `TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C)` | 70 | 0 | 0.00% | 1680 | 0 | 0.00% | 0 | Nenhuma lacuna (0 ausentes) | Nenhum tratamento necessário (100% dos registros horários e diários presentes) |
| `Estacao_Chuvosa` | `2023-01-15 a 2023-03-25` | `t_min` | `TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C)` | 70 | 0 | 0.00% | 1680 | 0 | 0.00% | 0 | Nenhuma lacuna (0 ausentes) | Nenhum tratamento necessário (100% dos registros horários e diários presentes) |
| `Estacao_Chuvosa` | `2023-01-15 a 2023-03-25` | `t_med` | `TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)` | 70 | 0 | 0.00% | 1680 | 0 | 0.00% | 0 | Nenhuma lacuna (0 ausentes) | Nenhum tratamento necessário (100% dos registros horários e diários presentes) |
| `Estacao_Chuvosa` | `2023-01-15 a 2023-03-25` | `precipitacao_mm` | `PRECIPITAÇÃO TOTAL, HORÁRIO (mm)` | 70 | 0 | 0.00% | 1680 | 0 | 0.00% | 0 | Nenhuma lacuna (0 ausentes) | Nenhum tratamento necessário (100% dos registros horários e diários presentes) |
| `Estacao_Seca` | `2023-07-01 a 2023-09-08` | `t_max` | `TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C)` | 70 | 0 | 0.00% | 1680 | 0 | 0.00% | 0 | Nenhuma lacuna (0 ausentes) | Nenhum tratamento necessário (100% dos registros horários e diários presentes) |
| `Estacao_Seca` | `2023-07-01 a 2023-09-08` | `t_min` | `TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C)` | 70 | 0 | 0.00% | 1680 | 0 | 0.00% | 0 | Nenhuma lacuna (0 ausentes) | Nenhum tratamento necessário (100% dos registros horários e diários presentes) |
| `Estacao_Seca` | `2023-07-01 a 2023-09-08` | `t_med` | `TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)` | 70 | 0 | 0.00% | 1680 | 0 | 0.00% | 0 | Nenhuma lacuna (0 ausentes) | Nenhum tratamento necessário (100% dos registros horários e diários presentes) |
| `Estacao_Seca` | `2023-07-01 a 2023-09-08` | `precipitacao_mm` | `PRECIPITAÇÃO TOTAL, HORÁRIO (mm)` | 70 | 0 | 0.00% | 1680 | 0 | 0.00% | 0 | Nenhuma lacuna (0 ausentes) | Nenhum tratamento necessário (100% dos registros horários e diários presentes) |
| `Arquivo_Bruto_Anual_2023` | `2023-01-01 a 2023-12-31` | `t_max` | `TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C)` | 365 | 34 | 9.32% | 8760 | 890 | 10.16% | 17 | 2023-10-26 a 2023-11-11 (17d); 2023-11-16 a 2023-11-25 (10d); 2023-12-05 a 2023-12-11 (7d) | Fora da janela dos ciclos simulados (lacunas concentradas em out-dez/2023) |
| `Arquivo_Bruto_Anual_2023` | `2023-01-01 a 2023-12-31` | `t_min` | `TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C)` | 365 | 34 | 9.32% | 8760 | 890 | 10.16% | 17 | 2023-10-26 a 2023-11-11 (17d); 2023-11-16 a 2023-11-25 (10d); 2023-12-05 a 2023-12-11 (7d) | Fora da janela dos ciclos simulados (lacunas concentradas em out-dez/2023) |
| `Arquivo_Bruto_Anual_2023` | `2023-01-01 a 2023-12-31` | `t_med` | `TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)` | 365 | 34 | 9.32% | 8760 | 887 | 10.13% | 17 | 2023-10-26 a 2023-11-11 (17d); 2023-11-16 a 2023-11-25 (10d); 2023-12-05 a 2023-12-11 (7d) | Fora da janela dos ciclos simulados (lacunas concentradas em out-dez/2023) |
| `Arquivo_Bruto_Anual_2023` | `2023-01-01 a 2023-12-31` | `precipitacao_mm` | `PRECIPITAÇÃO TOTAL, HORÁRIO (mm)` | 365 | 34 | 9.32% | 8760 | 887 | 10.13% | 17 | 2023-10-26 a 2023-11-11 (17d); 2023-11-16 a 2023-11-25 (10d); 2023-12-05 a 2023-12-11 (7d) | Fora da janela dos ciclos simulados (lacunas concentradas em out-dez/2023) |

---

## 4. Parâmetros e Fontes (Tabela T8)

Arquivo CSV correspondente: [`tabelas/T8_parametros_e_fontes.csv`](tabelas/T8_parametros_e_fontes.csv)

| Símbolo | Significado | Valor | Unidade | Origem |
|---|---|---|---|---|
| `θ_sat` | Umidade volumétrica do solo na saturação | `0.45` | `cm³/cm³` | premissa do modelo; não altera nenhum resultado (a água acima de θ_cc drena no mesmo passo) |
| `θ_cc` | Umidade volumétrica do solo na capacidade de campo | `0.28` | `cm³/cm³` | FAO-56, Tabela 19 (solo franco: θcc 0,20–0,30), página [A CONFIRMAR PELO AUTOR]; valor dentro da faixa |
| `θ_pmp` | Umidade volumétrica do solo no ponto de murcha permanente | `0.14` | `cm³/cm³` | FAO-56, Tabela 19 (solo franco: θpmp 0,07–0,17), página [A CONFIRMAR PELO AUTOR]; valor dentro da faixa |
| `p` | Fração de depleção da água disponível tolerada antes do estresse hídrico | `0.35` | `adimensional` | sem fonte: o FAO-56, Tabela 22, indica p = 0,30 para alface (valor adotado no v2) |
| `z1` | Espessura da Camada 1 (zona radicular ativa: 0 a 20 cm) | `200` | `mm` | Marouelli, Silva e Silva (2008, p. 84), Tabela 25: 15 cm na fase vegetativa e 20 cm nas fases 3 e 4; o modelo usa 20 cm; FAO-56, Tabela 22 (profundidade máxima 0,3–0,5 m) |
| `z2` | Espessura da Camada 2 (abaixo da zona radicular: 20 a 40 cm) | `200` | `mm` | premissa do modelo |
| `AD` | Capacidade de água disponível na zona radicular | `28.0` | `mm` | derivado: AD = (θ_cc − θ_pmp) × z1 |
| `θ_lim` | Limiar crítico de umidade volumétrica na Camada 1 para conforto hídrico e disparo da E1 | `0.231` | `cm³/cm³` | derivado: θ_lim = θ_cc − p × (θ_cc − θ_pmp) |
| `S1_cc` | Lâmina máxima retida na Camada 1 na capacidade de campo | `56.0` | `mm` | derivado: S1_cc = θ_cc × z1 |
| `S2_cc` | Lâmina máxima retida na Camada 2 na capacidade de campo | `56.0` | `mm` | derivado: S2_cc = θ_cc × z2 |
| `S1_pmp` | Armazenamento residual mínimo na Camada 1 no ponto de murcha permanente | `28.0` | `mm` | derivado: S1_pmp = θ_pmp × z1 |
| `S1_sat` | Armazenamento de saturação por camada | `90.0` | `mm` | derivado: S1_sat = θ_sat × z1 |
| `Deficit_solo_lim` | Depleção hídrica na Camada 1 correspondente exatamente a θ_lim | `9.80` | `mm` | derivado: Deficit_solo_lim = (θ_cc − θ_lim) × z1 = p × AD |
| `Kc_ini` | Coeficiente de cultura na fase inicial (dias 1 a 15 do ciclo) | `0.70` | `adimensional` | valor: FAO-56, Tabela 12 (grupo Small Vegetables); fase em degrau (dias 1 a 15) sem fonte, trocada no v2 pela curva da eq. 66 com as fases da Tabela 11 |
| `Kc_med` | Coeficiente de cultura na fase intermediária (dias 16 a 55 do ciclo) | `1.00` | `adimensional` | valor: FAO-56, Tabela 12 (alface); fase em degrau (dias 16 a 55) sem fonte, trocada no v2 pela curva da eq. 66 |
| `Kc_fim` | Coeficiente de cultura na fase final (dias 56 a 70 do ciclo) | `0.95` | `adimensional` | valor: FAO-56, Tabela 12 (alface); fase em degrau (dias 56 a 70) sem fonte, trocada no v2 pela curva da eq. 66 |
| `lamina_fixa` | Lâmina nominal por acionamento na estratégia E1 (referência e varredura) | `10.0 (varredura: 5, 10, 15, 20, 25, 30)` | `mm` | premissa do modelo |
| `limiar_deficit` | Gatilho de déficit acumulado para acionamento nas estratégias E2 e E3 | `10.0` | `mm` | premissa do v1; não corresponde a p × AD = 9.80 mm (banda morta); no v2 o gatilho é o RAW calculado |
| `area_canteiro` | Área útil do canteiro monitorado para conversão entre lâmina (mm) e volume (L) | `10.0` | `m²` | premissa do modelo |
| `V_cap (Abundante / Moderado / Restrito)` | Capacidade nominal do reservatório nos cenários padrão (e varredura 250–2000 L) | `1000 / 500 / 500` | `L` | premissa de cenário |
| `Δt_reab (Abundante / Moderado / Restrito)` | Intervalo entre reabastecimentos do reservatório nos cenários padrão | `3 / 7 / 14` | `dias` | premissa de cenário |
| `Gsc` | Constante solar extraterrestre na equação de Ra | `0.0820` | `MJ·m⁻²·min⁻¹` | FAO-56, eq. 21 |
| `f_conv_Ra` | Fator de conversão de radiação (MJ·m⁻²·dia⁻¹) em equivalente de evaporação (mm·dia⁻¹) | `0.408` | `mm·m²·MJ⁻¹` | FAO-56, eq. 20 (1/λ) |
| `c_HS, T_offset, exp_HS` | Coeficientes empíricos da equação de ET0 (0,0023; 17,8 °C; expoente térmico 0,5) | `0.0023; 17.8; 0.5` | `°C⁻¹·⁵; °C; adim.` | Hargreaves e Samani (1985); FAO-56, eq. 52 |
| `c_dr, c_δ1, c_δ2` | Constantes astronômicas de distância relativa Terra-Sol (0,033) e declinação solar (0,409 rad; 1,39 rad) | `0.033; 0.409; 1.39` | `adim.; rad; rad` | FAO-56, eqs. 23 e 24 |
| `φ (latitude)` | Latitude geográfica da estação meteorológica usada no cálculo de Ra | `-7.45555555` | `graus decimais` | extraído do arquivo INMET (campo LATITUDE:; do bloco de metadados) |
| `λ (longitude)` | Longitude geográfica da estação meteorológica | `-46.02749999` | `graus decimais` | extraído do arquivo INMET (campo LONGITUDE:; do bloco de metadados) |
| `z_est (altitude)` | Altitude geométrica da estação meteorológica | `271.03` | `m` | extraído do arquivo INMET (campo ALTITUDE:; do bloco de metadados) |

---

## 5. Modelo Implementado: Equações como Implementadas vs. Especificação

As equações abaixo descrevem literalmente o que está implementado em [`src/water_balance.py`](src/water_balance.py) e [`src/climate.py`](src/climate.py).

### 5.1 Radiação Extraterrestre ($R_a$) e Evapotranspiração ($ET_0$ e $ET_c$)
Para cada dia $t$ do ciclo, com dia do ano $J \in [1, 365]$ e latitude $\phi = \text{radians}(\text{latitude\_deg})$ extraída do bloco de metadados do arquivo INMET ($\text{latitude\_deg} = -7,45555555^\circ$):

$$d_r = 1,0 + 0,033 \cdot \cos\left(\frac{2\pi J}{365,0}\right)$$
$$\delta = 0,409 \cdot \sin\left(\frac{2\pi J}{365,0} - 1,39\right)$$
$$\omega_s = \arccos\left(\min\left(1,0,\; \max\left(-1,0,\; -\tan(\phi)\tan(\delta)\right)\right)\right)$$
$$R_a\,[\text{MJ}\cdot\text{m}^{-2}\cdot\text{dia}^{-1}] = \frac{24 \times 60}{\pi} \cdot G_{sc} \cdot d_r \cdot \left(\omega_s \sin(\phi)\sin(\delta) + \cos(\phi)\cos(\delta)\sin(\omega_s)\right)$$
$$R_a\,[\text{mm}\cdot\text{dia}^{-1}] = 0,408 \cdot R_a\,[\text{MJ}\cdot\text{m}^{-2}\cdot\text{dia}^{-1}]$$
$$ET_0(t) = \max\left(0,0,\; 0,0023 \cdot R_a\,[\text{mm}\cdot\text{dia}^{-1}] \cdot \sqrt{\max(0,0,\; T_{\max}(t) - T_{\min}(t))} \cdot (T_{\text{med}}(t) + 17,8)\right)$$
$$ET_{c,\text{pot}}(t) = K_c(t) \cdot ET_0(t)$$

### 5.2 Balanço Hídrico do Solo em Duas Camadas (`passo_balanco_solo`)
Com armazenamentos iniciais $S_1(t) = \theta_1(t) \cdot z_1$ e $S_2(t) = \theta_2(t) \cdot z_2$, e limites $S_{1,\text{pmp}} = \theta_{\text{pmp}} \cdot z_1 = 28,0\,\text{mm}$, $S_{1,\text{cc}} = \theta_{\text{cc}} \cdot z_1 = 56,0\,\text{mm}$ e $S_{2,\text{cc}} = \theta_{\text{cc}} \cdot z_2 = 56,0\,\text{mm}$:

```python
agua_extraivel_1      = max(0.0, S1(t) + P(t) + I_efetiva(t) - S1_pmp)
ETc_real(t)           = min(ETc_pot(t), agua_extraivel_1)
armazenamento_prov_1  = S1(t) + P(t) + I_efetiva(t) - ETc_real(t)
D1(t)                 = max(0.0, armazenamento_prov_1 - S1_cc)
theta1(t+1)           = (armazenamento_prov_1 - D1(t)) / z1

armazenamento_prov_2  = S2(t) + D1(t)
D2(t)                 = max(0.0, armazenamento_prov_2 - S2_cc)
theta2(t+1)           = (armazenamento_prov_2 - D2(t)) / z2
```

### 5.3 Regras de Decisão, Racionamento Estratégico e Limite Físico de Reservatório (`simular_estrategia`)
Para o índice diário $k \in \{0, 1, \dots, 69\}$ (`dia_idx` $= k+1$):
1. **Reabastecimento periódico:** se $k \bmod \Delta t_{\text{reab}} == 0$, então $V(t) = V_{\text{cap}}$, e $\text{dias\_restantes} = \Delta t_{\text{reab}} - (k \bmod \Delta t_{\text{reab}})$.
2. **Atualização do déficit acumulado:** $\text{Deficit}(t) = \max(0,0,\; \text{Deficit}(t-1) + ET_{c,\text{pot}}(t) - P(t))$.
3. **Cálculo da lâmina desejada $I_{\text{desejada}}(t)$ por estratégia:**
   - **E1:** se $\theta_1(t) < \theta_{\text{lim}}$, $I_{\text{desejada}}(t) = \text{lamina\_fixa}$; senão $0,0$.
   - **E2:** se $\text{Deficit}(t) \ge \text{limiar\_deficit}$, $I_{\text{desejada}}(t) = \text{Deficit}(t)$ e $\text{Deficit}(t) \leftarrow 0,0$; senão $0,0$.
   - **E3:** se $\text{Deficit}(t) \ge \text{limiar\_deficit}$, $\text{lamina\_maxima}(t) = \frac{V(t)}{\text{dias\_restantes} \cdot A_{\text{canteiro}}}$ e $I_{\text{desejada}}(t) = \min(\text{Deficit}(t), \max(0,0, \text{lamina\_maxima}(t)))$.
4. **Aplicação do limite físico universal do reservatório (Parte 2 — vale para E1, E2 e E3):**
   $$I_{\text{efetiva}}(t) = \min\left(I_{\text{desejada}}(t),\; \frac{V(t)}{A_{\text{canteiro}}}\right)$$
   $$I_{\text{nao\_atendida}}(t) = \max\left(0,0,\; I_{\text{desejada}}(t) - I_{\text{efetiva}}(t)\right)$$
   $$V(t+1) = \max\left(0,0,\; V(t) - I_{\text{efetiva}}(t) \cdot A_{\text{canteiro}}\right)$$
   Para E1 e E3, após a irrigação efetiva: $\text{Deficit}(t) \leftarrow \max(0,0,\; \text{Deficit}(t) - I_{\text{efetiva}}(t))$.

### 5.4 Apontamento Explícito de Divergências e Detalhamentos em Relação à Especificação Original

| Aspecto | Como consta na especificação original do v1 | Como está implementado no código (`src/water_balance.py` e `src/climate.py`) | Justificativa Física / Metodológica |
|---|---|---|---|
| **Limitação de $ET_c$ no ponto de murcha ($\theta_{\text{pmp}}$)** | A Seção 3.3 escreve `armazenamento_prov_1 = θ1(t)·z1 + P(t) + I(t) − ETc(t)` e exige na linha 99 a invariante `θ1 >= θ_pmp`. | Implementado `ETc_real(t) = min(ETc_pot(t), max(0, S1(t) + P(t) + I_efetiva(t) - S1_pmp))`, usando `ETc_real(t)` no balanço de massa. | Sem limitar a extração real à água disponível acima de $\theta_{\text{pmp}}$, um período seco sem irrigação (como o Teste 2 de secagem monotônica ou o contrafactual em sequeiro) faria $\theta_1$ cair abaixo de $\theta_{\text{pmp}}$ ou violaria a conservação de massa. |
| **Teto de armazenamento por passo diário ($\theta_{\text{cc}}$ vs $\theta_{\text{sat}}$)** | A Seção 3.3 define `D1(t) = max(0, armazenamento_prov_1 − θ_cc·z1)` e declara `θ <= θ_sat` como invariante. | Implementado exatamente conforme a equação de `D1(t)` e `D2(t)`: toda água que excede $\theta_{\text{cc}} \cdot z$ drena no próprio passo diário, de modo que $\theta_1(t+1) \le \theta_{\text{cc}} = 0,28 < \theta_{\text{sat}} = 0,45$. | Em modelo de reservatório de passo diário sem equação cinética de redistribuição, a macro-porosidade entre $\theta_{\text{cc}}$ e $\theta_{\text{sat}}$ drena dentro de 24 h; logo $\theta_{\text{sat}}$ atua como teto invariante nunca ultrapassado. |
| **Limite físico do reservatório em E1 e E2** | Na Seção 4 original, o reservatório aparecia apenas na subseção da E3. | Na Parte 2 desta rodada final, o limite físico $I_{\text{efetiva}}(t) = \min(I_{\text{desejada}}(t), V(t)/A_{\text{canteiro}})$ foi estendido a **E1, E2 e E3**, permanecendo exclusivo da E3 apenas o racionamento estratégico por `dias_restantes`. | Impede que E1 e E2 apliquem água inexistente quando o reservatório se esgota nos cenários Moderado e Restrito. |
| **Desconto de $I(t)$ no déficit acumulado da E3** | A Seção 4.3 mostrava `I(t) = min(Deficit(t), lamina_maxima(t))` sem explicitar a linha de atualização de `Deficit(t)` após irrigação parcial. | Implementado `Deficit(t) = max(0.0, Deficit(t) - I_efetiva(t))` na E3 (enquanto na E2, quando acionada, `I_desejada(t) = Deficit(t)` e `Deficit(t) = 0`). | Como a E3 aplica lâmina deficitária ($I(t) < \text{Deficit}(t)$), apenas a fração efetivamente reposta deve ser abatida do déficit acumulado. |
| **Latitude geográfica $\phi$** | A Seção 3.4 mencionava um valor de exemplo para $\phi$. | Removido o valor fixo do código (Parte 1.5); o cálculo usa exclusivamente a latitude extraída do bloco de metadados do arquivo bruto do INMET ($\phi = -7,45555555^\circ$). | Fidelidade estrita aos metadados oficiais da estação automática `A204 (BALSAS)` do BDMEP/INMET. |
| **Agregação de série horária do BDMEP para passo diário** | A Seção 3.5 especifica variáveis diárias ($T_{\max}$, $T_{\min}$, $T_{\text{med}}$, $P$). | O arquivo oficial das estações automáticas do INMET fornece 24 registros horários UTC por dia; o parser agrega $P_{\text{dia}} = \sum P_{\text{hora}}$, $T_{\max,\text{dia}} = \max(T_{\max,\text{hora}})$, $T_{\min,\text{dia}} = \min(T_{\min,\text{hora}})$ e $T_{\text{med,dia}} = \overline{T}_{\text{bulbo seco,hora}}$. | Preserva o arquivo bruto oficial do INMET intocado em `data/raw/` e deriva a série diária em `resultados/v1/processed/`. |

---

## 6. Testes de Validação Física (Tabela T6)

Arquivo CSV correspondente: [`tabelas/T6_testes_validacao_fisica.csv`](tabelas/T6_testes_validacao_fisica.csv)  
Série diária completa dos 3 testes: [`rodadas/rodadas_validacao_fisica_diario.csv`](rodadas/rodadas_validacao_fisica_diario.csv)

| Teste | Dias | Condição Inicial | Forçantes | Valor Esperado Literal (Calculado à Mão) | Valor Observado no Simulador | Erro Absoluto | Erro Relativo | Status |
|---|---:|---|---|---|---|---|---|---|
| **1. Conservação de Massa Independente** | 10 | `theta1(0)=0.25; theta2(0)=0.26; S_ini=102.0 mm` | `ETc=4.0 mm/d; P=[0,15,0,0,0,0,15,0,0,0] (30 mm); I=[12,0,0,0,0,12,0,0,0,0] (24 mm)` | `Entradas=54.0; Saidas=56.0; Sigma_D2=16.0; S_fim=100.0; Lado_A=-2.0; Lado_B=-2.0 mm` | `Entradas=54.0000; Saidas=56.0000; Sigma_D2=16.0000; S_fim=100.0000; Lado_A=-2.0000; Lado_B=-2.0000 mm` | `0.00000000 mm` | `0.00000000% (< 0.1%)` | **APROVADO** |
| **2. Secagem Monotônica** | 60 | `theta1(0)=0.28 (theta_cc); theta2(0)=0.28` | `P=0.0 mm/d; I=0.0 mm/d; ETc_pot=4.0 mm/d constante por 60 dias` | `theta1(dia 7)=0.1400; theta1(dia 60)=0.1400 cm3/cm3; Sigma_ETc_real=28.0 mm` | `theta1(dia 7)=0.1400; theta1(dia 60)=0.1400 cm3/cm3; Sigma_ETc_real=28.0000 mm; monotonica=True` | `0.00000000` | `0.00000000%` | **APROVADO** |
| **3. Saturação Extrema** | 1 | `theta1(0)=0.28 (theta_cc); theta2(0)=0.28 (theta_cc)` | `P(1)=250.0 mm; I(1)=0.0 mm; ETc(1)=0.0 mm` | `D1=250.0 mm; D2=250.0 mm; theta1(1)=0.2800 <= 0.45; theta2(1)=0.2800 <= 0.45` | `D1=250.0000 mm; D2=250.0000 mm; theta1(1)=0.2800; theta2(1)=0.2800` | `0.00000000 mm` | `0.00000000%` | **APROVADO** |

---

## 7. Caracterização Climática dos Dois Ciclos (Tabela T1 e Figura F1)

Arquivo CSV correspondente: [`tabelas/T1_caracterizacao_climatica.csv`](tabelas/T1_caracterizacao_climatica.csv)

| Ciclo | Datas do Ciclo | Dias | $\Sigma P$ (mm) | $\Sigma ET_0$ (mm) | $ET_0$ Média (mm/d) | $\Sigma ET_c$ (mm) | $ET_c$ Média (mm/d) | $T$ Média (°C) | $T_{\max}$ Abs. (°C) | $T_{\min}$ Abs. (°C) | Nº Dias c/ Chuva | Maior Evento de Chuva (mm e data) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `Estacao_Chuvosa` | `2023-01-15 a 2023-03-25` | 70 | **299.20** | 356.77 | 5.10 | 330.57 | 4.72 | 25.63 | 35.90 | 19.20 | 39 | **96.80 mm** (`2023-03-18`) |
| `Estacao_Seca` | `2023-07-01 a 2023-09-08` | 70 | **42.20** | 408.84 | 5.84 | 380.89 | 5.44 | 27.36 | 40.10 | 14.20 | 4 | **27.60 mm** (`2023-08-31`) |

### Figura F1 — Série Diária de $\theta_1$ e $\theta_2$ ao Longo do Ciclo
- Estação Chuvosa: [`figuras/F1_umidade_solo_estacao_chuvosa.png`](figuras/F1_umidade_solo_estacao_chuvosa.png) · Dados: [`figuras/F1_umidade_solo_estacao_chuvosa.csv`](figuras/F1_umidade_solo_estacao_chuvosa.csv)
- Estação Seca: [`figuras/F1_umidade_solo_estacao_seca.png`](figuras/F1_umidade_solo_estacao_seca.png) · Dados: [`figuras/F1_umidade_solo_estacao_seca.csv`](figuras/F1_umidade_solo_estacao_seca.csv)

---

## 8. Resultados: Comparação Principal (Tabela T2, Figuras F4 e F5)

Arquivo CSV correspondente: [`tabelas/T2_comparacao_principal.csv`](tabelas/T2_comparacao_principal.csv)  
Série diária completa: [`rodadas/rodadas_comparacao_principal_diario.csv`](rodadas/rodadas_comparacao_principal_diario.csv)

### 8.1 Referência Contrafactual em Sequeiro ($I(t) = 0$)

| Período Climático | Precipitação $\Sigma P$ (mm) | `D2_chuva` (mm) | `D2_chuva` (L) | Conforto Hídrico em Sequeiro (%) | Déficit Máximo no Solo (mm) |
|---|---:|---:|---:|---:|---:|
| `Estacao_Chuvosa` | 299.20 | **84.39** | **844.0** | 25.71% | 28.00 |
| `Estacao_Seca` | 42.20 | **0.00** | **0.0** | 5.71% | 28.00 |

### 8.2 Tabela T2 — Comparação Principal (2 Períodos × 3 Cenários × 3 Estratégias)

| Período | Cenário | Estratégia | Lâmina Desejada (mm) | Lâmina Aplicada (mm / L) | Lâmina Não Atendida (mm / L) | `D2_total` (mm / L) | `D2_chuva` (mm / L) | `D2_incremental` (mm / L) | Eficiência de Aplicação Incremental (%) | Conforto Hídrico (%) | Nº Acion. | Déficit Máx. (mm) | Dias Reserv. Vazio | 1º Dia Vazio |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `Estacao_Chuvosa` | `Abundante` | **E1** | 190.00 | **190.00** / 1900 | 0.00 / 0 | 164.99 / 1650 | 84.39 / 844 | **80.60** / 806 | **57.58%** | **72.86%** | 19 | 15.90 | 0 | — |
| `Estacao_Chuvosa` | `Abundante` | **E2** | 196.92 | **196.92** / 1969 | 0.00 / 0 | 170.93 / 1709 | 84.39 / 844 | **86.54** / 865 | **56.05%** | **97.14%** | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | `Abundante` | **E3** | 196.92 | **196.92** / 1969 | 0.00 / 0 | 170.93 / 1709 | 84.39 / 844 | **86.54** / 865 | **56.05%** | **97.14%** | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | `Moderado` | **E1** | 190.00 | **190.00** / 1900 | 0.00 / 0 | 164.99 / 1650 | 84.39 / 844 | **80.60** / 806 | **57.58%** | **72.86%** | 19 | 15.90 | 0 | — |
| `Estacao_Chuvosa` | `Moderado` | **E2** | 196.92 | **196.92** / 1969 | 0.00 / 0 | 170.93 / 1709 | 84.39 / 844 | **86.54** / 865 | **56.05%** | **97.14%** | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | `Moderado` | **E3** | 195.71 | **195.71** / 1957 | 0.00 / 0 | 169.71 / 1697 | 84.39 / 844 | **85.32** / 853 | **56.40%** | **98.57%** | 19 | 9.90 | 0 | — |
| `Estacao_Chuvosa` | `Restrito` | **E1** | 200.00 | **190.00** / 1900 | 10.00 / 100 | 164.99 / 1650 | 84.39 / 844 | **80.60** / 806 | **57.58%** | **71.43%** | 19 | 15.90 | 7 | 27 |
| `Estacao_Chuvosa` | `Restrito` | **E2** | 196.92 | **185.03** / 1850 | 11.89 / 119 | 159.04 / 1590 | 84.39 / 844 | **74.65** / 746 | **59.66%** | **91.43%** | 16 | 14.12 | 5 | 27 |
| `Estacao_Chuvosa` | `Restrito` | **E3** | 175.86 | **175.86** / 1759 | 0.00 / 0 | 149.86 / 1499 | 84.39 / 844 | **65.47** / 655 | **62.77%** | **74.29%** | 35 | 20.85 | 0 | — |
| `Estacao_Seca` | `Abundante` | **E1** | 350.00 | **350.00** / 3500 | 0.00 / 0 | 18.30 / 183 | 0.00 / 0 | **18.30** / 183 | **94.77%** | **50.00%** | 35 | 16.56 | 0 | — |
| `Estacao_Seca` | `Abundante` | **E2** | 363.61 | **363.61** / 3636 | 0.00 / 0 | 24.92 / 249 | 0.00 / 0 | **24.92** / 249 | **93.15%** | **100.00%** | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | `Abundante` | **E3** | 363.61 | **363.61** / 3636 | 0.00 / 0 | 24.92 / 249 | 0.00 / 0 | **24.92** / 249 | **93.15%** | **100.00%** | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | `Moderado` | **E1** | 350.00 | **350.00** / 3500 | 0.00 / 0 | 18.30 / 183 | 0.00 / 0 | **18.30** / 183 | **94.77%** | **50.00%** | 35 | 16.56 | 1 | 49 |
| `Estacao_Seca` | `Moderado` | **E2** | 363.61 | **363.45** / 3635 | 0.16 / 2 | 24.76 / 248 | 0.00 / 0 | **24.76** / 248 | **93.19%** | **100.00%** | 31 | 7.82 | 1 | 49 |
| `Estacao_Seca` | `Moderado` | **E3** | 360.29 | **360.29** / 3603 | 0.00 / 0 | 21.60 / 216 | 0.00 / 0 | **21.60** / 216 | **94.00%** | **95.71%** | 41 | 9.93 | 1 | 42 |
| `Estacao_Seca` | `Restrito` | **E1** | 500.00 | **240.00** / 2400 | 260.00 / 2600 | 24.69 / 247 | 0.00 / 0 | **24.69** / 247 | **89.71%** | **27.14%** | 24 | 28.00 | 36 | 23 |
| `Estacao_Seca` | `Restrito` | **E2** | 363.61 | **243.22** / 2432 | 120.39 / 1204 | 2.61 / 26 | 0.00 / 0 | **2.61** / 26 | **98.93%** | **42.86%** | 23 | 28.00 | 23 | 23 |
| `Estacao_Seca` | `Restrito` | **E3** | 241.67 | **241.67** / 2417 | 0.00 / 0 | 4.06 / 41 | 0.00 / 0 | **4.06** / 41 | **98.32%** | **25.71%** | 64 | 28.00 | 4 | 28 |

### 8.3 Verificação da Separação entre Cenários da E1 após o Limite Físico de Reservatório (Parte 3.3)
- **E1 (lâmina fixa) nos três cenários, valores da Tabela T2:**
  - **Estação Chuvosa:** `Abundante`: `190,00 mm` aplicados em `19` acionamentos, `0,00 mm` não atendidos, conforto de `72,86%`, `0` dias com reservatório vazio; `Moderado`: `190,00 mm` aplicados em `19` acionamentos, `0,00 mm` não atendidos, conforto de `72,86%`, `0` dias com reservatório vazio; `Restrito`: `190,00 mm` aplicados em `19` acionamentos, `10,00 mm` não atendidos, conforto de `71,43%`, `7` dias com reservatório vazio, primeiro esvaziamento no dia 27.
  - **Estação Seca:** `Abundante`: `350,00 mm` aplicados em `35` acionamentos, `0,00 mm` não atendidos, conforto de `50,00%`, `0` dias com reservatório vazio; `Moderado`: `350,00 mm` aplicados em `35` acionamentos, `0,00 mm` não atendidos, conforto de `50,00%`, `1` dias com reservatório vazio, primeiro esvaziamento no dia 49; `Restrito`: `240,00 mm` aplicados em `24` acionamentos, `260,00 mm` não atendidos, conforto de `27,14%`, `36` dias com reservatório vazio, primeiro esvaziamento no dia 23.

### Figuras F4 e F5
- Figura F4 (Estação Chuvosa): [`figuras/F4_barras_comparativas_estacao_chuvosa.png`](figuras/F4_barras_comparativas_estacao_chuvosa.png) · Dados: [`figuras/F4_barras_comparativas_estacao_chuvosa.csv`](figuras/F4_barras_comparativas_estacao_chuvosa.csv)
- Figura F4 (Estação Seca): [`figuras/F4_barras_comparativas_estacao_seca.png`](figuras/F4_barras_comparativas_estacao_seca.png) · Dados: [`figuras/F4_barras_comparativas_estacao_seca.csv`](figuras/F4_barras_comparativas_estacao_seca.csv)
- Figura F5 (Nível do Reservatório — Restrito, Estação Chuvosa): [`figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.png`](figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.png) · Dados: [`figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.csv`](figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.csv)
- Figura F5 (Nível do Reservatório — Restrito, Estação Seca): [`figuras/F5_nivel_reservatorio_restrito_estacao_seca.png`](figuras/F5_nivel_reservatorio_restrito_estacao_seca.png) · Dados: [`figuras/F5_nivel_reservatorio_restrito_estacao_seca.csv`](figuras/F5_nivel_reservatorio_restrito_estacao_seca.csv)

---

## 9. Resultados: Sensibilidade da Lâmina Fixa da E1 (Tabela T3 e Figura F2)

Arquivo CSV correspondente: [`tabelas/T3_sensibilidade_e1.csv`](tabelas/T3_sensibilidade_e1.csv)  
Série diária completa: [`rodadas/rodadas_sensibilidade_e1_diario.csv`](rodadas/rodadas_sensibilidade_e1_diario.csv)

| Período | Cenário | `lamina_fixa` (mm) | Lâmina Desejada (mm) | Lâmina Aplicada (mm / L) | Lâmina Não Atendida (mm / L) | `D2_total` (mm) | `D2_chuva` (mm) | `D2_incremental` (mm / L) | Eficiência Incremental (%) | Conforto Hídrico (%) | Nº Acion. | Déficit Máx. (mm) | Dias Reserv. Vazio | 1º Dia Vazio |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `Estacao_Chuvosa` | `Abundante` | **5** | 170.0 | **170.0** / 1700 | 0.0 / 0 | 149.99 | 84.39 | **65.60** / 656 | 61.41% | **50.00%** | 34 | 16.67 | 0 | — |
| `Estacao_Chuvosa` | `Abundante` | **10** | 190.0 | **190.0** / 1900 | 0.0 / 0 | 164.99 | 84.39 | **80.60** / 806 | 57.58% | **72.86%** | 19 | 15.90 | 0 | — |
| `Estacao_Chuvosa` | `Abundante` | **15** | 225.0 | **225.0** / 2250 | 0.0 / 0 | 194.99 | 84.39 | **110.60** / 1106 | 50.84% | **78.57%** | 15 | 14.69 | 0 | — |
| `Estacao_Chuvosa` | `Abundante` | **20** | 280.0 | **280.0** / 2800 | 0.0 / 0 | 248.63 | 84.39 | **164.24** / 1642 | 41.34% | **80.00%** | 14 | 13.66 | 0 | — |
| `Estacao_Chuvosa` | `Abundante` | **25** | 350.0 | **350.0** / 3500 | 0.0 / 0 | 318.63 | 84.39 | **234.24** / 2342 | 33.07% | **80.00%** | 14 | 13.66 | 0 | — |
| `Estacao_Chuvosa` | `Abundante` | **30** | 420.0 | **420.0** / 4200 | 0.0 / 0 | 388.63 | 84.39 | **304.24** / 3042 | 27.56% | **80.00%** | 14 | 13.66 | 0 | — |
| `Estacao_Chuvosa` | `Moderado` | **5** | 170.0 | **170.0** / 1700 | 0.0 / 0 | 149.99 | 84.39 | **65.60** / 656 | 61.41% | **50.00%** | 34 | 16.67 | 0 | — |
| `Estacao_Chuvosa` | `Moderado` | **10** | 190.0 | **190.0** / 1900 | 0.0 / 0 | 164.99 | 84.39 | **80.60** / 806 | 57.58% | **72.86%** | 19 | 15.90 | 0 | — |
| `Estacao_Chuvosa` | `Moderado` | **15** | 225.0 | **225.0** / 2250 | 0.0 / 0 | 194.99 | 84.39 | **110.60** / 1106 | 50.84% | **78.57%** | 15 | 14.69 | 0 | — |
| `Estacao_Chuvosa` | `Moderado` | **20** | 280.0 | **280.0** / 2800 | 0.0 / 0 | 248.63 | 84.39 | **164.24** / 1642 | 41.34% | **80.00%** | 14 | 13.66 | 0 | — |
| `Estacao_Chuvosa` | `Moderado` | **25** | 350.0 | **350.0** / 3500 | 0.0 / 0 | 318.63 | 84.39 | **234.24** / 2342 | 33.07% | **80.00%** | 14 | 13.66 | 11 | 14 |
| `Estacao_Chuvosa` | `Moderado` | **30** | 420.0 | **370.0** / 3700 | 50.0 / 500 | 338.63 | 84.39 | **254.24** / 2542 | 31.29% | **80.00%** | 14 | 13.66 | 11 | 14 |
| `Estacao_Chuvosa` | `Restrito` | **5** | 175.0 | **170.0** / 1700 | 5.0 / 50 | 149.99 | 84.39 | **65.60** / 656 | 61.41% | **48.57%** | 34 | 16.67 | 2 | 55 |
| `Estacao_Chuvosa` | `Restrito` | **10** | 200.0 | **190.0** / 1900 | 10.0 / 100 | 164.99 | 84.39 | **80.60** / 806 | 57.58% | **71.43%** | 19 | 15.90 | 7 | 27 |
| `Estacao_Chuvosa` | `Restrito` | **15** | 240.0 | **215.0** / 2150 | 25.0 / 250 | 184.99 | 84.39 | **100.60** / 1006 | 53.21% | **77.14%** | 15 | 14.69 | 4 | 53 |
| `Estacao_Chuvosa` | `Restrito` | **20** | 360.0 | **240.0** / 2400 | 120.0 / 1200 | 208.63 | 84.39 | **124.24** / 1242 | 48.23% | **74.29%** | 14 | 19.06 | 14 | 14 |
| `Estacao_Chuvosa` | `Restrito` | **25** | 650.0 | **250.0** / 2500 | 400.0 / 4000 | 234.96 | 84.39 | **150.57** / 1506 | 39.77% | **62.86%** | 10 | 28.00 | 38 | 10 |
| `Estacao_Chuvosa` | `Restrito` | **30** | 780.0 | **250.0** / 2500 | 530.0 / 5300 | 234.96 | 84.39 | **150.57** / 1506 | 39.77% | **62.86%** | 10 | 28.00 | 38 | 10 |
| `Estacao_Seca` | `Abundante` | **5** | 305.0 | **305.0** / 3050 | 0.0 / 0 | 7.86 | 0.00 | **7.86** / 79 | 97.42% | **11.43%** | 61 | 28.00 | 0 | — |
| `Estacao_Seca` | `Abundante` | **10** | 350.0 | **350.0** / 3500 | 0.0 / 0 | 18.30 | 0.00 | **18.30** / 183 | 94.77% | **50.00%** | 35 | 16.56 | 0 | — |
| `Estacao_Seca` | `Abundante` | **15** | 360.0 | **360.0** / 3600 | 0.0 / 0 | 23.30 | 0.00 | **23.30** / 233 | 93.53% | **65.71%** | 24 | 16.38 | 0 | — |
| `Estacao_Seca` | `Abundante` | **20** | 400.0 | **400.0** / 4000 | 0.0 / 0 | 72.90 | 0.00 | **72.90** / 729 | 81.78% | **70.00%** | 20 | 12.99 | 0 | — |
| `Estacao_Seca` | `Abundante` | **25** | 500.0 | **500.0** / 5000 | 0.0 / 0 | 172.90 | 0.00 | **172.90** / 1729 | 65.42% | **70.00%** | 20 | 12.99 | 0 | — |
| `Estacao_Seca` | `Abundante` | **30** | 600.0 | **600.0** / 6000 | 0.0 / 0 | 272.90 | 0.00 | **272.90** / 2729 | 54.52% | **70.00%** | 20 | 12.99 | 0 | — |
| `Estacao_Seca` | `Moderado` | **5** | 305.0 | **305.0** / 3050 | 0.0 / 0 | 7.86 | 0.00 | **7.86** / 79 | 97.42% | **11.43%** | 61 | 28.00 | 0 | — |
| `Estacao_Seca` | `Moderado` | **10** | 350.0 | **350.0** / 3500 | 0.0 / 0 | 18.30 | 0.00 | **18.30** / 183 | 94.77% | **50.00%** | 35 | 16.56 | 1 | 49 |
| `Estacao_Seca` | `Moderado` | **15** | 360.0 | **360.0** / 3600 | 0.0 / 0 | 23.30 | 0.00 | **23.30** / 233 | 93.53% | **65.71%** | 24 | 16.38 | 0 | — |
| `Estacao_Seca` | `Moderado` | **20** | 420.0 | **400.0** / 4000 | 20.0 / 200 | 72.90 | 0.00 | **72.90** / 729 | 81.78% | **68.57%** | 21 | 14.48 | 2 | 28 |
| `Estacao_Seca` | `Moderado` | **25** | 575.0 | **475.0** / 4750 | 100.0 / 1000 | 147.90 | 0.00 | **147.90** / 1479 | 68.86% | **65.71%** | 19 | 18.69 | 33 | 12 |
| `Estacao_Seca` | `Moderado` | **30** | 690.0 | **480.0** / 4800 | 210.0 / 2100 | 152.90 | 0.00 | **152.90** / 1529 | 68.15% | **65.71%** | 19 | 18.69 | 33 | 12 |
| `Estacao_Seca` | `Restrito` | **5** | 305.0 | **240.0** / 2400 | 65.0 / 650 | 6.92 | 0.00 | **6.92** / 69 | 97.12% | **11.43%** | 48 | 28.00 | 17 | 25 |
| `Estacao_Seca` | `Restrito` | **10** | 500.0 | **240.0** / 2400 | 260.0 / 2600 | 24.69 | 0.00 | **24.69** / 247 | 89.71% | **27.14%** | 24 | 28.00 | 36 | 23 |
| `Estacao_Seca` | `Restrito` | **15** | 660.0 | **245.0** / 2450 | 415.0 / 4150 | 21.47 | 0.00 | **21.47** / 215 | 91.24% | **35.71%** | 19 | 28.00 | 29 | 24 |
| `Estacao_Seca` | `Restrito` | **20** | 860.0 | **250.0** / 2500 | 610.0 / 6100 | 43.23 | 0.00 | **43.23** / 432 | 82.71% | **37.14%** | 15 | 28.00 | 41 | 12 |
| `Estacao_Seca` | `Restrito` | **25** | 1125.0 | **250.0** / 2500 | 875.0 / 8750 | 60.69 | 0.00 | **60.69** / 607 | 75.72% | **34.29%** | 10 | 28.00 | 54 | 8 |
| `Estacao_Seca` | `Restrito` | **30** | 1320.0 | **250.0** / 2500 | 1070.0 / 10700 | 56.07 | 0.00 | **56.07** / 561 | 77.57% | **35.71%** | 10 | 28.00 | 52 | 8 |

### Figura F2 — Sensibilidade da E1 vs. Referência E2
- Estação Chuvosa: [`figuras/F2_sensibilidade_e1_estacao_chuvosa.png`](figuras/F2_sensibilidade_e1_estacao_chuvosa.png) · Dados: [`figuras/F2_sensibilidade_e1_estacao_chuvosa.csv`](figuras/F2_sensibilidade_e1_estacao_chuvosa.csv)
- Estação Seca: [`figuras/F2_sensibilidade_e1_estacao_seca.png`](figuras/F2_sensibilidade_e1_estacao_seca.png) · Dados: [`figuras/F2_sensibilidade_e1_estacao_seca.csv`](figuras/F2_sensibilidade_e1_estacao_seca.csv)

---

## 10. Resultados: Dimensionamento do Reservatório (Tabelas T4 e T5, Figura F3)

### 10.1 Tabela T4 — Dimensionamento Mínimo para Conforto Hídrico ≥ 90%
Arquivo CSV correspondente: [`tabelas/T4_dimensionamento_reservatorio.csv`](tabelas/T4_dimensionamento_reservatorio.csv)

| Período Climático | Intervalo de Reabastecimento | Demanda `ETc` Média (mm/d) | $\Sigma P$ no Ciclo (mm) | Capacidade Mínima p/ Conforto ≥ 90% (L) | Oferta Máxima na Cap. Mínima (mm/d) | Conforto Obtido (%) | Lâmina Aplicada (mm) | `D2_incremental` (mm) | Eficiência Incremental (%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `Estacao_Chuvosa` | **3 dias** | 4.72 | 299.20 | **250 L** | 8.33 | **97.14%** | 198.51 | 88.12 | 55.61% |
| `Estacao_Chuvosa` | **7 dias** | 4.72 | 299.20 | **500 L** | 7.14 | **98.57%** | 195.71 | 85.32 | 56.40% |
| `Estacao_Chuvosa` | **14 dias** | 4.72 | 299.20 | **750 L** | 5.36 | **98.57%** | 181.70 | 71.32 | 60.75% |
| `Estacao_Seca` | **3 dias** | 5.44 | 42.20 | **250 L** | 8.33 | **98.57%** | 354.83 | 19.65 | 94.46% |
| `Estacao_Seca` | **7 dias** | 5.44 | 42.20 | **500 L** | 7.14 | **95.71%** | 360.29 | 21.60 | 94.00% |
| `Estacao_Seca` | **14 dias** | 5.44 | 42.20 | **1000 L** | 7.14 | **95.71%** | 358.62 | 19.93 | 94.44% |

### 10.2 Tabela T5 — Varredura Completa do Reservatório na E3 (48 Rodadas)
Arquivo CSV correspondente: [`tabelas/T5_varredura_reservatorio.csv`](tabelas/T5_varredura_reservatorio.csv)  
Série diária completa: [`rodadas/rodadas_varredura_reservatorio_e3_diario.csv`](rodadas/rodadas_varredura_reservatorio_e3_diario.csv)

| Período | Intervalo (d) | Capacidade (L) | Oferta Máx. (mm/d) | Atende ≥ 90%? | Conforto Hídrico (%) | Lâmina Aplicada (mm / L) | Lâmina Não Atendida (mm) | `D2_total` (mm) | `D2_chuva` (mm) | `D2_incremental` (mm) | Eficiência Incremental (%) | Nº Acion. | Déficit Máx. (mm) | Dias Reserv. Vazio | 1º Dia Vazio |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `Estacao_Chuvosa` | 3 | **250** | 8.33 | **SIM** | **97.14%** | 198.51 / 1985 | 0.00 | 172.51 | 84.39 | **88.12** | 55.61% | 19 | 9.93 | 1 | 27 |
| `Estacao_Chuvosa` | 3 | **500** | 16.67 | **SIM** | **97.14%** | 196.92 / 1969 | 0.00 | 170.93 | 84.39 | **86.54** | 56.05% | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | 3 | **750** | 25.00 | **SIM** | **97.14%** | 196.92 / 1969 | 0.00 | 170.93 | 84.39 | **86.54** | 56.05% | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | 3 | **1000** | 33.33 | **SIM** | **97.14%** | 196.92 / 1969 | 0.00 | 170.93 | 84.39 | **86.54** | 56.05% | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | 3 | **1250** | 41.67 | **SIM** | **97.14%** | 196.92 / 1969 | 0.00 | 170.93 | 84.39 | **86.54** | 56.05% | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | 3 | **1500** | 50.00 | **SIM** | **97.14%** | 196.92 / 1969 | 0.00 | 170.93 | 84.39 | **86.54** | 56.05% | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | 3 | **1750** | 58.33 | **SIM** | **97.14%** | 196.92 / 1969 | 0.00 | 170.93 | 84.39 | **86.54** | 56.05% | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | 3 | **2000** | 66.67 | **SIM** | **97.14%** | 196.92 / 1969 | 0.00 | 170.93 | 84.39 | **86.54** | 56.05% | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | 7 | **250** | 3.57 | **Não** | **75.71%** | 175.16 / 1752 | 0.00 | 149.16 | 84.39 | **64.77** | 63.02% | 38 | 19.75 | 3 | 14 |
| `Estacao_Chuvosa` | 7 | **500** | 7.14 | **SIM** | **98.57%** | 195.71 / 1957 | 0.00 | 169.71 | 84.39 | **85.32** | 56.40% | 19 | 9.90 | 0 | — |
| `Estacao_Chuvosa` | 7 | **750** | 10.71 | **SIM** | **98.57%** | 201.84 / 2018 | 0.00 | 175.85 | 84.39 | **91.46** | 54.69% | 17 | 9.90 | 0 | — |
| `Estacao_Chuvosa` | 7 | **1000** | 14.29 | **SIM** | **97.14%** | 196.92 / 1969 | 0.00 | 170.93 | 84.39 | **86.54** | 56.05% | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | 7 | **1250** | 17.86 | **SIM** | **97.14%** | 196.92 / 1969 | 0.00 | 170.93 | 84.39 | **86.54** | 56.05% | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | 7 | **1500** | 21.43 | **SIM** | **97.14%** | 196.92 / 1969 | 0.00 | 170.93 | 84.39 | **86.54** | 56.05% | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | 7 | **1750** | 25.00 | **SIM** | **97.14%** | 196.92 / 1969 | 0.00 | 170.93 | 84.39 | **86.54** | 56.05% | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | 7 | **2000** | 28.57 | **SIM** | **97.14%** | 196.92 / 1969 | 0.00 | 170.93 | 84.39 | **86.54** | 56.05% | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | 14 | **250** | 1.79 | **Não** | **48.57%** | 112.50 / 1125 | 0.00 | 113.62 | 84.39 | **29.23** | 74.02% | 49 | 28.00 | 3 | 14 |
| `Estacao_Chuvosa` | 14 | **500** | 3.57 | **Não** | **74.29%** | 175.86 / 1759 | 0.00 | 149.86 | 84.39 | **65.47** | 62.77% | 35 | 20.85 | 0 | — |
| `Estacao_Chuvosa` | 14 | **750** | 5.36 | **SIM** | **98.57%** | 181.70 / 1817 | 0.00 | 155.71 | 84.39 | **71.32** | 60.75% | 23 | 9.90 | 0 | — |
| `Estacao_Chuvosa` | 14 | **1000** | 7.14 | **SIM** | **97.14%** | 196.38 / 1964 | 0.00 | 170.39 | 84.39 | **86.00** | 56.21% | 20 | 9.90 | 0 | — |
| `Estacao_Chuvosa` | 14 | **1250** | 8.93 | **SIM** | **98.57%** | 202.49 / 2025 | 0.00 | 176.49 | 84.39 | **92.10** | 54.51% | 18 | 9.90 | 0 | — |
| `Estacao_Chuvosa` | 14 | **1500** | 10.71 | **SIM** | **97.14%** | 193.34 / 1933 | 0.00 | 167.34 | 84.39 | **82.95** | 57.09% | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | 14 | **1750** | 12.50 | **SIM** | **97.14%** | 195.92 / 1959 | 0.00 | 169.93 | 84.39 | **85.54** | 56.34% | 16 | 9.93 | 0 | — |
| `Estacao_Chuvosa` | 14 | **2000** | 14.29 | **SIM** | **97.14%** | 196.92 / 1969 | 0.00 | 170.93 | 84.39 | **86.54** | 56.05% | 16 | 9.93 | 0 | — |
| `Estacao_Seca` | 3 | **250** | 8.33 | **SIM** | **98.57%** | 354.83 / 3548 | 0.00 | 19.65 | 0.00 | **19.65** | 94.46% | 33 | 10.00 | 1 | 48 |
| `Estacao_Seca` | 3 | **500** | 16.67 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | 3 | **750** | 25.00 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | 3 | **1000** | 33.33 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | 3 | **1250** | 41.67 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | 3 | **1500** | 50.00 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | 3 | **1750** | 58.33 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | 3 | **2000** | 66.67 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | 7 | **250** | 3.57 | **Não** | **30.00%** | 243.33 / 2433 | 0.00 | 4.06 | 0.00 | **4.06** | 98.33% | 62 | 28.00 | 9 | 7 |
| `Estacao_Seca` | 7 | **500** | 7.14 | **SIM** | **95.71%** | 360.29 / 3603 | 0.00 | 21.60 | 0.00 | **21.60** | 94.00% | 41 | 9.93 | 1 | 42 |
| `Estacao_Seca` | 7 | **750** | 10.71 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 8.13 | 0 | — |
| `Estacao_Seca` | 7 | **1000** | 14.29 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | 7 | **1250** | 17.86 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | 7 | **1500** | 21.43 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | 7 | **1750** | 25.00 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | 7 | **2000** | 28.57 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | 14 | **250** | 1.79 | **Não** | **8.57%** | 125.00 / 1250 | 0.00 | 0.49 | 0.00 | **0.49** | 99.61% | 68 | 28.00 | 5 | 14 |
| `Estacao_Seca` | 14 | **500** | 3.57 | **Não** | **25.71%** | 241.67 / 2417 | 0.00 | 4.06 | 0.00 | **4.06** | 98.32% | 64 | 28.00 | 4 | 28 |
| `Estacao_Seca` | 14 | **750** | 5.36 | **Não** | **50.00%** | 341.99 / 3420 | 0.00 | 5.71 | 0.00 | **5.71** | 98.33% | 57 | 28.00 | 3 | 28 |
| `Estacao_Seca` | 14 | **1000** | 7.14 | **SIM** | **95.71%** | 358.62 / 3586 | 0.00 | 19.93 | 0.00 | **19.93** | 94.44% | 37 | 9.89 | 0 | — |
| `Estacao_Seca` | 14 | **1250** | 8.93 | **SIM** | **98.57%** | 361.48 / 3615 | 0.00 | 22.79 | 0.00 | **22.79** | 93.69% | 32 | 9.86 | 0 | — |
| `Estacao_Seca` | 14 | **1500** | 10.71 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 9.15 | 0 | — |
| `Estacao_Seca` | 14 | **1750** | 12.50 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 7.82 | 0 | — |
| `Estacao_Seca` | 14 | **2000** | 14.29 | **SIM** | **100.00%** | 363.61 / 3636 | 0.00 | 24.92 | 0.00 | **24.92** | 93.15% | 31 | 7.82 | 0 | — |

### Figura F3 — Curvas de Dimensionamento do Reservatório
- Estação Chuvosa: [`figuras/F3_dimensionamento_estacao_chuvosa.png`](figuras/F3_dimensionamento_estacao_chuvosa.png) · Dados: [`figuras/F3_dimensionamento_estacao_chuvosa.csv`](figuras/F3_dimensionamento_estacao_chuvosa.csv)
- Estação Seca: [`figuras/F3_dimensionamento_estacao_seca.png`](figuras/F3_dimensionamento_estacao_seca.png) · Dados: [`figuras/F3_dimensionamento_estacao_seca.csv`](figuras/F3_dimensionamento_estacao_seca.csv)

---

## 11. Nota Metodológica sobre a Decomposição da Percolação (`D2_incremental`)

1. **Definição das grandezas:**
   - `D2_total`: percolação profunda acumulada abaixo da Camada 2 na rodada com irrigação ativa.
   - `D2_chuva`: percolação profunda acumulada no contrafactual em sequeiro ($I(t) = 0$), com a mesma série climática e as mesmas condições iniciais ($\theta_1(0) = \theta_2(0) = \theta_{\text{cc}} = 0,28$).
   - `D2_incremental = D2_total − D2_chuva`.
   - `Eficiência de Aplicação Incremental (%) = ((Lâmina Aplicada − D2_incremental) / Lâmina Aplicada) × 100`.
2. **Limitação metodológica (interação solo–chuva–irrigação):**
   - No sequeiro, a ETc esgota a Camada 1 até perto de $\theta_{\text{pmp}}$, abrindo até $AD = 28,0\,\text{mm}$ de espaço antes de qualquer drenagem. Valores calculados: `D2_chuva` = `84,39 mm` na Estação Chuvosa, com $\Sigma P = 299,20\,\text{mm}$; `D2_chuva` = `0,00 mm` na Estação Seca, com $\Sigma P = 42,20\,\text{mm}$.
   - Nas rodadas irrigadas, o controle mantém $\theta_1 \ge \theta_{\text{lim}} = 0,231$, o que limita a folga de retenção na Camada 1 a $S_{1,\text{cc}} - \theta_{\text{lim}} z_1 = 9,80\,\text{mm}$.
   - Por isso `D2_incremental` não é uma atribuição física limpa à água da irrigação: inclui a chuva que, no solo seco do sequeiro, teria ficado retida.

---

## 12. Investigação da Não-Monotonicidade da E3 (Parte 3.2)

### 12.1 Casos na série real do INMET de 2023

- `Estacao_Chuvosa`, intervalo `7d`: `750 L` → conforto `98,57%`; `1.000 L` → `97,14%`.
- `Estacao_Chuvosa`, intervalo `14d`: `750 L` → conforto `98,57%`; `1.000 L` → `97,14%`.
- `Estacao_Chuvosa`, intervalo `14d`: `1.250 L` → conforto `98,57%`; `1.500 L` → `97,14%`.

### 12.2 Comparação dia a dia (primeiro caso da lista)

| Dia | Data | 750 L: $I$ (mm) | 750 L: Deficit (mm) | 750 L: $\theta_{1,\text{fim}}$ | 1.000 L: $I$ (mm) | 1.000 L: Deficit (mm) | 1.000 L: $\theta_{1,\text{fim}}$ |
|---:|---|---:|---:|---:|---:|---:|---:|
| 52 | `2023-03-07` | 10,25 | 0,0000 | 0,280000 | 0,00 | 9,9278 | 0,230361 |

### 12.3 Causa: banda morta entre o limiar de conforto e o gatilho
- No v1, $\theta_{\text{lim}}$ corresponde a uma depleção de $p \times AD = 0,35 \times 28,0 = 9,80\,\text{mm}$, mas E2 e E3 só disparam com `Deficit` ≥ `10,0 mm`.
- Quando o déficit do fim do dia cai em $[9,80;\ 10,00)\,\text{mm}$, não há irrigação e o dia termina abaixo de $\theta_{\text{lim}}$. Doses menores (capacidade menor na E3) podem deslocar essa fase e evitar a banda, o que explica a não monotonicidade. No v2 o gatilho é o RAW calculado e a banda não existe.

---

## 13. Limitações e Anomalias Observadas

1. **Percolação da `E1` no ciclo seco, `Restrito` × `Abundante`:** `D2_total` = `24,69 mm` com `240,00 mm` aplicados (`Restrito`) e `18,30 mm` com `350,00 mm` (`Abundante`).
   - Dias com percolação na `E1 Restrito` (série diária): dia 61 (`2023-08-30`): I = `10,00 mm`, P = `8,60 mm`, D2 = `2,73 mm`; dia 62 (`2023-08-31`): I = `0,00 mm`, P = `27,60 mm`, D2 = `21,96 mm`.
2. **Dias sem conforto na `E2` e na `E3` com o cenário `Abundante`** (ver a banda morta da seção 12.3):
   - `E2`, Estação Chuvosa: dia 3 (`2023-01-17`, $\theta_1$ = 0,230495, Deficit = 9,9010 mm); dia 52 (`2023-03-07`, $\theta_1$ = 0,230361, Deficit = 9,9278 mm).
   - `E3`, Estação Chuvosa: dia 3 (`2023-01-17`, $\theta_1$ = 0,230495, Deficit = 9,9010 mm); dia 52 (`2023-03-07`, $\theta_1$ = 0,230361, Deficit = 9,9278 mm).
   - `E2`, Estação Seca: nenhum.
   - `E3`, Estação Seca: nenhum.
3. **Lâmina fixa da `E1`:**
   - Estação Chuvosa: no `Abundante`, o conforto chega ao máximo (`80,00%`) a partir de `20 mm`; no `Restrito`, por lâmina: `5 mm` → `48,57%`; `10 mm` → `71,43%`; `15 mm` → `77,14%`; `20 mm` → `74,29%`; `25 mm` → `62,86%`; `30 mm` → `62,86%`.
   - Estação Seca: no `Abundante`, o conforto chega ao máximo (`70,00%`) a partir de `20 mm`; no `Restrito`, por lâmina: `5 mm` → `11,43%`; `10 mm` → `27,14%`; `15 mm` → `35,71%`; `20 mm` → `37,14%`; `25 mm` → `34,29%`; `30 mm` → `35,71%`.
4. **Teto da `E1` com água sobrando:** a regra é avaliada no início do dia e o conforto no fim, então cada ciclo de secagem custa um dia abaixo de $\theta_{\text{lim}}$ (no v2, com passo horário, custa uma hora):
   - Estação Chuvosa: conforto de `72,86%` = 1 − `19`/`70`.
   - Estação Seca: conforto de `50,00%` = 1 − `35`/`70`.
5. **Acumulador `Deficit(t)` × déficit físico do solo:** com o reservatório vazio, o acumulador da `E2` soma a ETc potencial enquanto o solo, perto de $\theta_{\text{pmp}}$, quase não perde água; e a `E2` zera o contador ao comandar uma irrigação mesmo sem água no tanque.
6. **Simplificações do modelo de duas camadas:** sem extração radicular e sem ascensão capilar na Camada 2; drenagem instantânea no passo diário; ET0 por Hargreaves-Samani, cujo viés em relação a Penman-Monteith é quantificado pelo v2 (`resultados/v2/tabelas/tab_clima_ciclos.md`).
7. **Anos vizinhos:** a completude da `A204` em 2024 e 2025 não é avaliada por este relatório; ver o v2 (`resultados/v2/tabelas/tab_completude_anos.md`).

---

## 14. Reprodutibilidade (Parte 7)

| Parâmetro de Reprodutibilidade | Valor / Especificação |
|---|---|
| **Sistema Operacional / Kernel** | `Linux-6.17.0-29-generic-x86_64-with-glibc2.39` |
| **Versão da linguagem Python** | `3.12.3 (main, Aug 31 2026, 10:18:26) [GCC 13.3.0]` |
| **Versão do SQLite (`sqlite3`)** | `3.45.1` |
| **Versão do `matplotlib`** | `3.11.2` |
| **Versão do `numpy`** | `2.5.4` |
| **Hash do commit Git** | `52287bb1eb6488fa0d95b405d44a358b111a0f6b` |
| **Comando exato para reproduzir todas as rodadas, tabelas, figuras e relatório do zero** | `python3 main.py pipeline --modelo v1` |
| **Comando exato para executar a suíte de testes de validação** | `python3 -m unittest discover -s tests -v` |
| **Tempo de execução total medido** | `6.414 segundos` |
| **Confirmação sobre aleatoriedade** | Não há aleatoriedade em nenhum componente do projeto. Nenhum gerador pseudoaleatório (random / numpy.random) é importado ou invocado; todas as equações físicas, regras de decisão e agregações são estritamente determinísticas. |
| **Semente aleatória (`seed`)** | `Não aplicável (modelo 100% determinístico)` |

---

## 15. Índice dos Arquivos Gerados

| Categoria | Caminho Relativo | Descrição do Conteúdo |
|---|---|---|
| **Relatório Principal** | [`relatorio_final.md`](relatorio_final.md) | Relatório técnico-científico consolidado (Seções 1 a 15) |
| **Dado Bruto INMET** | [`data/raw/INMET_NE_MA_A204_BALSAS_01-01-2023_A_31-12-2023.CSV`](data/raw/INMET_NE_MA_A204_BALSAS_01-01-2023_A_31-12-2023.CSV) | Arquivo bruto oficial do BDMEP/INMET preservado intocado (`764.609 bytes`, `8.769 linhas`, SHA-256 `7aa68f3a9a2c09ef19a822490fb5fe957c1e0b37bed7ca6b084e3e38d450b233`) |
| **Série Processada** | [`processed/inmet_A204_balsas_2023_diario_bruto_agregado.csv`](processed/inmet_A204_balsas_2023_diario_bruto_agregado.csv) | Série diária agregada dos 365 dias do arquivo, com contagem de horas válidas por variável |
| **Série Processada** | [`processed/inmet_A204_balsas_2023_ciclos_70d_tratados.csv`](processed/inmet_A204_balsas_2023_ciclos_70d_tratados.csv) | Série diária tratada dos dois ciclos de 70 dias (`Estacao_Chuvosa` e `Estacao_Seca`) com $ET_0$, $K_c$ e $ET_c$ |
| **Tabela T1 (CSV)** | [`tabelas/T1_caracterizacao_climatica.csv`](tabelas/T1_caracterizacao_climatica.csv) | Caracterização climática dos dois ciclos de 70 dias |
| **Tabela T1b (CSV)** | [`tabelas/T1b_estatisticas_descritivas_por_variavel_ciclo.csv`](tabelas/T1b_estatisticas_descritivas_por_variavel_ciclo.csv) | Estatísticas descritivas (mínimo, máximo, média, desvio-padrão, mediana, soma) por variável e ciclo |
| **Tabela T2 (CSV)** | [`tabelas/T2_comparacao_principal.csv`](tabelas/T2_comparacao_principal.csv) | Comparação principal: 2 períodos × 3 cenários × 3 estratégias |
| **Tabela T3 (CSV)** | [`tabelas/T3_sensibilidade_e1.csv`](tabelas/T3_sensibilidade_e1.csv) | Análise de sensibilidade da lâmina fixa da E1 (`5, 10, 15, 20, 25, 30 mm` × 2 períodos × 3 cenários) |
| **Tabela T4 (CSV)** | [`tabelas/T4_dimensionamento_reservatorio.csv`](tabelas/T4_dimensionamento_reservatorio.csv) | Dimensionamento mínimo do reservatório para conforto hídrico ≥ 90% |
| **Tabela T5 (CSV)** | [`tabelas/T5_varredura_reservatorio.csv`](tabelas/T5_varredura_reservatorio.csv) | Varredura completa do reservatório na E3 (48 rodadas) |
| **Tabela T6 (CSV)** | [`tabelas/T6_testes_validacao_fisica.csv`](tabelas/T6_testes_validacao_fisica.csv) | Resultados dos 3 testes obrigatórios de validação física com constantes literais |
| **Tabela T7 (CSV)** | [`tabelas/T7_qualidade_dado_climatico.csv`](tabelas/T7_qualidade_dado_climatico.csv) | Qualidade do dado climático por variável e ciclo |
| **Tabela T8 (CSV)** | [`tabelas/T8_parametros_e_fontes.csv`](tabelas/T8_parametros_e_fontes.csv) | Tabela completa de parâmetros, valores, unidades e classificação de origem |
| **Série Diária** | [`rodadas/rodadas_comparacao_principal_diario.csv`](rodadas/rodadas_comparacao_principal_diario.csv) | Série diária completa das rodadas da comparação principal e contrafactuais (`1.400 registros`) |
| **Série Diária** | [`rodadas/rodadas_sensibilidade_e1_diario.csv`](rodadas/rodadas_sensibilidade_e1_diario.csv) | Série diária completa das 36 rodadas de sensibilidade da E1 (`2.520 registros`) |
| **Série Diária** | [`rodadas/rodadas_varredura_reservatorio_e3_diario.csv`](rodadas/rodadas_varredura_reservatorio_e3_diario.csv) | Série diária completa das 48 rodadas da varredura de reservatório da E3 (`3.360 registros`) |
| **Série Diária** | [`rodadas/rodadas_validacao_fisica_diario.csv`](rodadas/rodadas_validacao_fisica_diario.csv) | Série diária passo a passo dos 3 testes de validação física (`71 registros`) |
| **Figura F1 (Chuvosa)** | [`figuras/F1_umidade_solo_estacao_chuvosa.png`](figuras/F1_umidade_solo_estacao_chuvosa.png) | PNG 300 dpi + [`figuras/F1_umidade_solo_estacao_chuvosa.csv`](figuras/F1_umidade_solo_estacao_chuvosa.csv) |
| **Figura F1 (Seca)** | [`figuras/F1_umidade_solo_estacao_seca.png`](figuras/F1_umidade_solo_estacao_seca.png) | PNG 300 dpi + [`figuras/F1_umidade_solo_estacao_seca.csv`](figuras/F1_umidade_solo_estacao_seca.csv) |
| **Figura F2 (Chuvosa)** | [`figuras/F2_sensibilidade_e1_estacao_chuvosa.png`](figuras/F2_sensibilidade_e1_estacao_chuvosa.png) | PNG 300 dpi + [`figuras/F2_sensibilidade_e1_estacao_chuvosa.csv`](figuras/F2_sensibilidade_e1_estacao_chuvosa.csv) |
| **Figura F2 (Seca)** | [`figuras/F2_sensibilidade_e1_estacao_seca.png`](figuras/F2_sensibilidade_e1_estacao_seca.png) | PNG 300 dpi + [`figuras/F2_sensibilidade_e1_estacao_seca.csv`](figuras/F2_sensibilidade_e1_estacao_seca.csv) |
| **Figura F3 (Chuvosa)** | [`figuras/F3_dimensionamento_estacao_chuvosa.png`](figuras/F3_dimensionamento_estacao_chuvosa.png) | PNG 300 dpi + [`figuras/F3_dimensionamento_estacao_chuvosa.csv`](figuras/F3_dimensionamento_estacao_chuvosa.csv) |
| **Figura F3 (Seca)** | [`figuras/F3_dimensionamento_estacao_seca.png`](figuras/F3_dimensionamento_estacao_seca.png) | PNG 300 dpi + [`figuras/F3_dimensionamento_estacao_seca.csv`](figuras/F3_dimensionamento_estacao_seca.csv) |
| **Figura F4 (Chuvosa)** | [`figuras/F4_barras_comparativas_estacao_chuvosa.png`](figuras/F4_barras_comparativas_estacao_chuvosa.png) | PNG 300 dpi + [`figuras/F4_barras_comparativas_estacao_chuvosa.csv`](figuras/F4_barras_comparativas_estacao_chuvosa.csv) |
| **Figura F4 (Seca)** | [`figuras/F4_barras_comparativas_estacao_seca.png`](figuras/F4_barras_comparativas_estacao_seca.png) | PNG 300 dpi + [`figuras/F4_barras_comparativas_estacao_seca.csv`](figuras/F4_barras_comparativas_estacao_seca.csv) |
| **Figura F5 (Chuvosa)** | [`figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.png`](figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.png) | PNG 300 dpi + [`figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.csv`](figuras/F5_nivel_reservatorio_restrito_estacao_chuvosa.csv) |
| **Figura F5 (Seca)** | [`figuras/F5_nivel_reservatorio_restrito_estacao_seca.png`](figuras/F5_nivel_reservatorio_restrito_estacao_seca.png) | PNG 300 dpi + [`figuras/F5_nivel_reservatorio_restrito_estacao_seca.csv`](figuras/F5_nivel_reservatorio_restrito_estacao_seca.csv) |
