# Fontes dos parâmetros e dos dados

Todo valor externo usado pelo simulador está listado aqui com a fonte. Onde a fonte não pôde ser conferida, o item está marcado `[A CONFIRMAR PELO AUTOR]`; nada foi preenchido por suposição. Os valores do v2 estão em [`src/v2/parametros.py`](../src/v2/parametros.py) e saem na tabela `resultados/v2/tabelas/tab_parametros.md`; os do v1, na T8 (`resultados/v1/tabelas/T8_parametros_e_fontes.csv`).

## 1. Solo e cultura

| Parâmetro | Valor no v2 | Fonte |
|---|---|---|
| θcc; θpmp | 0,28; 0,14 cm³ cm⁻³ | ALLEN et al. (1998), FAO-56, Tabela 19: solo franco, θcc 0,20–0,30 e θpmp 0,07–0,17. Os valores adotados estão dentro da faixa e serão substituídos pela caracterização do solo na fase de campo. **Conferir a tabela no PDF do FAO-56; página [A CONFIRMAR PELO AUTOR].** |
| p | 0,30 | ALLEN et al. (1998), FAO-56, Tabela 22 ("Ranges of maximum effective rooting depth (Zr), and soil water depletion fraction for no stress (p)"): alface, p = 0,30 para ETc ≈ 5 mm/d. O ajuste p = p_tab + 0,04·(5 − ETc), limitado a 0,1–0,8, não é aplicado (a faixa resultante é calculada como diagnóstico). https://www.fao.org/4/x0490e/x0490e0e.htm |
| Profundidade radicular máxima da alface | 0,3–0,5 m | FAO-56, Tabela 22 (mesma fonte acima). Justifica a sensibilidade com z₁ = 300 mm. |
| z₁ | 200 mm (0–20 cm) | MAROUELLI, W. A.; SILVA, W. L. de C. e; SILVA, H. R. da. *Irrigação por aspersão em hortaliças: qualidade da água, aspectos do sistema e método prático de manejo*. 2. ed. rev. atual. ampl. Brasília, DF: Embrapa Informação Tecnológica, 2008. 150 p. ISBN 978-85-7383-428-4. Tabela 25 (p. 84): profundidade efetiva das raízes da alface de 15 cm na fase vegetativa e de 20 cm nas fases 3 e 4; o modelo usa 20 cm. |
| Kc,ini; Kc,mid; Kc,end | 0,70; 1,00; 0,95 | FAO-56, Tabela 12: Kc,ini = 0,7 do grupo "Small Vegetables"; alface Kc,mid = 1,00 e Kc,end = 0,95. https://www.fao.org/4/x0490e/x0490e0b.htm |
| Altura da cultura (h) | 0,3 m | FAO-56, Tabela 12 (alface). Usada só no diagnóstico do ajuste climático do Kc,mid (eq. 62). |
| Fases do Kc | 19/28/14/9 d | FAO-56, Tabela 11: alface 20/30/15/10 = 75 d (abril, Mediterrâneo), escalonadas proporcionalmente a 70 d com arredondamento pelo maior resto (premissa do autor; cálculo em `escalonar_fases`). Outras entradas da tabela para alface: 30/40/25/10, 25/35/30/10 e 35/50/45/10. |
| Curva de Kc | eq. 66 | FAO-56, cap. 6, eq. 66 (interpolação linear entre as fases). |

## 2. Clima e ET0

| Item | Fonte |
|---|---|
| ET0 horária (eq. 53), σ horária (2,043×10⁻¹⁰ MJ m⁻² h⁻¹ K⁻⁴), G horário (eqs. 45–46), Rs/Rso noturna (período 2–3 h antes do pôr do sol, ωs − 0,79 ≤ ω ≤ ωs − 0,52), Exemplo 19 | ALLEN et al. (1998), FAO-56, cap. 4. https://www.fao.org/4/x0490e/x0490e08.htm |
| Ra, Rso, Rnl, u₂, P, γ, e°, Δ, ea (eqs. 7, 8, 11, 13, 21, 23–25, 28–33, 37–39, 47, 54); constante solar Gsc = 0,0820 MJ m⁻² min⁻¹; albedo 0,23; limites de Rs/Rso [0,3; 1,0] | ALLEN et al. (1998), FAO-56, cap. 3. https://www.fao.org/4/x0490e/x0490e07.htm |
| Hargreaves-Samani (só comparação) | HARGREAVES, G. H.; SAMANI, Z. A. *Applied Engineering in Agriculture*, v. 1, n. 2, p. 96-99, 1985. DOI 10.13031/2013.26773. Na forma da eq. 52 do FAO-56. |
| Vento a 10 m; dados integralizados por hora, em UTC; vento horário = média dos 10 min antes da hora | INSTITUTO NACIONAL DE METEOROLOGIA (Brasil). *Rede de estações meteorológicas automáticas do INMET*. Nota Técnica nº 001/2011/SEGER/LAIME/CSC/INMET. Brasília, DF: INMET, 2011: "sensores e demais instrumentos são fixados em um mastro metálico de 10 metros de altura" (p. 3). Cópia: https://www.cemtec.ms.gov.br/wp-content/uploads/2019/02/Nota_Tecnica-Rede_estacoes_INMET.pdf. Que o anemômetro está no topo do mastro é premissa. |
| Série de 2023 da A204 (Balsas-MA) | INMET, dados históricos anuais: https://portal.inmet.gov.br/uploads/dadoshistoricos/2023.zip, arquivo `INMET_NE_MA_A204_BALSAS_01-01-2023_A_31-12-2023.CSV`, SHA-256 `7aa68f3a9a2c09ef19a822490fb5fe957c1e0b37bed7ca6b084e3e38d450b233` (registrado em `data/raw/SHA256SUMS`). |
| Média de chuva 1991–2021 de Balsas (comparação com 2023) | CORRÊA, W. C.; CARVALHO, M. W. L.; MENDES, T. J. Atualização da classificação climática e balanço hídrico climatológico no Estado do Maranhão. *Revista Brasileira de Climatologia*, v. 32, p. 517-543, 2023. https://ojs.ufgd.edu.br/rbclima/article/download/16727/9412/58836. Tabela 6: médias mensais de 1991 a 2021 da estação convencional 82768 (Balsas). Os seis meses das janelas estão em [`data/referencias/correa_2023_balsas_82768.csv`](../data/referencias/correa_2023_balsas_82768.csv); a média de cada janela pondera cada mês pelos dias que caem nela (cálculo em `src/v2/dados_externos.py`). |
| Dados de 2024 e 2025 da A204 | INMET, dados históricos anuais: https://portal.inmet.gov.br/uploads/dadoshistoricos/2024.zip e https://portal.inmet.gov.br/uploads/dadoshistoricos/2025.zip. Só o arquivo da A204 de cada zip é extraído para `data/raw/` (`python3 main.py dados --preparar`), com o SHA-256 do arquivo e do zip em `data/raw/SHA256SUMS`. Usados só para a completude da estação (`resultados/v2/tabelas/tab_completude_anos.md`); não são simulados. |

## 3. Premissas do modelo (declaradas como tais)

| Parâmetro | Valor | Observação |
|---|---|---|
| θsat | 0,45 cm³ cm⁻³ | sem efeito em nenhuma métrica (a água acima de θcc drena na mesma hora); provado pelo teste `test_theta_sat_e_z2_nao_mudam_nenhuma_metrica` |
| z₂ | 200 mm (20–40 cm) | sem efeito com f_ext2 = 0; mesmo teste |
| f_ext2 | 0 | camada 2 sem extração radicular |
| θ₁(0), θ₂(0) | θcc | perfil na capacidade de campo no transplante, após a irrigação de plantio |
| L (E1) | 10 mm | sensibilidade de 5 a 30 mm |
| A | 10 m² | 1 mm sobre 10 m² = 10 L |
| Cenários | 1.000 L / 3 d; 500 L / 7 d; 500 L / 14 d | premissa de cenário (abundante, moderado, restrito) |
| Ra mínima para radiação vazia valer 0 | 0,1 MJ m⁻² h⁻¹ | regra de tratamento de falta ([`MODELO.md`](MODELO.md), seção 2.1) |

## 4. Derivados

TAW, RAW, θlim, os armazenamentos (θcc·z, θpmp·z) e as fases escalonadas são calculados pelo código a partir dos valores acima (`ParametrosModelo` em `src/v2/parametros.py`) e gravados em todo arquivo de saída.

## 5. Pendências para o autor

- Página da Tabela 19 do FAO-56 (θcc e θpmp do solo franco), conferida no PDF.
