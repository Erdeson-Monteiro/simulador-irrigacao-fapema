# Modelo v2: balanço hídrico horário com estratégias de irrigação

Projeto PIC/FAPEMA "Automação da Irrigação em Hortas Comunitárias com Sensores e IoT" (Edital COORD.NUPEX nº 01/2026).
Código: [`src/v2/`](../src/v2/). Fontes de cada parâmetro: [`FONTES_PARAMETROS.md`](FONTES_PARAMETROS.md).

Este documento descreve o que o código faz. Ele não traz resultados: todo número de resultado sai do pipeline (`python3 main.py pipeline`) para `resultados/v2/`, em especial `NUMEROS_ARTIGO.md` e `RELATORIO.md`.

## 1. Visão geral

O modelo simula, hora a hora, um canteiro de alface de 10 m² durante um ciclo de 70 dias, com o solo em duas camadas (0–20 cm e 20–40 cm), um reservatório reposto em intervalos fixos e uma de quatro regras de manejo (E1, E2, E3 ou sequeiro). A entrada climática é a série horária real da estação automática A204 do INMET (Balsas-MA, 2023), com ET0 horária pelo método de Penman-Monteith do FAO-56. Nenhum dado climático é sintético, estimado ou interpolado: faltou dado dentro de um ciclo, o programa para com erro.

## 2. Dados climáticos e ET0

### 2.1 Série horária ([`inmet.py`](../src/v2/inmet.py), [`clima.py`](../src/v2/clima.py))

- Arquivo: `data/raw/INMET_NE_MA_A204_BALSAS_01-01-2023_A_31-12-2023.CSV` (latin1, separador `;`, vírgula decimal). O SHA-256 de cada arquivo bruto está em `data/raw/SHA256SUMS`; arquivo fora do registro, ou com hash diferente, é recusado.
- Latitude, longitude e altitude vêm do cabeçalho do próprio arquivo.
- **Convenção de horário:** o registro `HH00 UTC` marca o fim do intervalo de uma hora, ou seja, cobre (HH−1, HH] UTC (Nota Técnica 001/2011 do INMET: dados integralizados por hora, em UTC). O teste `test_convencao_registro_marca_o_fim_do_intervalo` confere isso no próprio arquivo: com o meio de cada intervalo em HH − 0,5, o centroide da radiação média cai sobre o meio-dia solar; se o registro marcasse o início, ficaria uma hora depois.
- **Hora local = UTC − 3**, sem horário de verão. O dia local d reúne os registros de `0400 UTC` do dia d a `0300 UTC` do dia d+1. Os ciclos são definidos em dias locais: chuvoso de 15/01 a 25/03/2023 e seco de 01/07 a 08/09/2023, com 1.680 horas cada.
- **Regras de falta, sem imputação:** radiação vazia com Ra da hora < 0,1 MJ m⁻² h⁻¹ vale 0 (noite e hora do pôr do sol); radiação vazia com Ra ≥ 0,1 é erro; radiação negativa vale 0; qualquer outra variável vazia dentro de um ciclo é erro. Faltas fora dos ciclos não impedem a simulação.
- Radiação: kJ m⁻² ÷ 1.000 = MJ m⁻² h⁻¹.

### 2.2 ET0 horária: Penman-Monteith do FAO-56 ([`fao56.py`](../src/v2/fao56.py))

Para cada hora, com t = meio do intervalo em UTC (HH − 0,5) e J = dia do ano desse instante:

| Termo | Cálculo | FAO-56 |
|---|---|---|
| Pressão atmosférica | P = 101,3·[(293 − 0,0065·z)/293]^5,26 | eq. 7 |
| Constante psicrométrica | γ = 0,665×10⁻³·P | eq. 8 |
| e°, Δ | pela temperatura do ar horária | eqs. 11 e 13 |
| ea | e°(T)·UR/100 | eq. 54 |
| u₂ | u₂ = u₁₀·4,87/ln(67,8·10 − 5,42) | eq. 47 |
| ω | π/12·[(t + 0,06667·(Lz − Lm) + Sc) − 12], com Lz = 0 (hora em UTC) e Lm = longitude do arquivo, em graus a oeste | eqs. 31–33 |
| Ra horária | eq. 28, com ω₁ = ω − π/24 e ω₂ = ω + π/24 limitados a [−ωs, ωs] | eqs. 23–25, 28–30 |
| Rso | (0,75 + 2×10⁻⁵·z)·Ra | eq. 37 |
| Rns | (1 − 0,23)·Rs | eq. 38 |
| Rnl | σ·(T + 273,16)⁴·(0,34 − 0,14·√ea)·(1,35·Rs/Rso − 0,35), com σ = 2,043×10⁻¹⁰ MJ m⁻² h⁻¹ K⁻⁴ | eq. 39 |
| G | 0,1·Rn com Ra > 0; 0,5·Rn com Ra = 0 | eqs. 45–46 |
| ET0 | [0,408·Δ·(Rn − G) + γ·37/(T + 273)·u₂·(e° − ea)] / [Δ + γ·(1 + 0,34·u₂)] | eq. 53 |

A implementação reproduz o Exemplo 19 do FAO-56 ("Determination of ETo with hourly data") dentro de ±0,002 nos termos intermediários e ±0,005 mm h⁻¹ na ET0 (`tests/test_v2_clima.py`).

**Ra na hora do nascer e do pôr do sol.** Com ω₁ e ω₂ limitados a [−ωs, ωs], Ra = 0 só quando a hora inteira está com o Sol abaixo do horizonte; a hora que contém o pôr do sol recebe a parte iluminada (Ra pequena, mas positiva). O texto do FAO-56 sugere outra leitura: zerar Ra sempre que o meio da hora estiver abaixo do horizonte. As duas diferem apenas nessas horas de transição. O v2 adota a primeira leitura (ω₁ e ω₂ limitados), com a qual a ET0 dos ciclos coincide com a de uma implementação independente (`TestConferenciaIndependenteClima` em `tests/test_v2_clima.py`); o pipeline calcula a ET0 também pela outra leitura, como diagnóstico, para mostrar o tamanho da diferença.

**Rs/Rso.** Nas horas com Ra > 0, usa-se a razão medida, limitada a [0,3; 1,0]: o FAO-56 limita Rs/Rso a 1,0, e 0,3 corresponde a céu totalmente encoberto. Nas horas com Ra = 0, usa-se a razão do período 2–3 h antes do pôr do sol anterior (ωs − 0,79 ≤ ω ≤ ωs − 0,52), limitada da mesma forma. Na série de 2023, esse período corresponde a uma única hora por tarde (registro `1900 UTC`).

**ET0 negativa.** À noite, com Rn − G negativo e déficit de pressão de vapor pequeno, a eq. 53 dá valores negativos (condensação). No balanço, a ET0 horária negativa vale 0; a soma dos valores zerados e o número de horas ficam registrados como diagnóstico.

**Vento.** Os sensores das estações automáticas ficam num mastro metálico de 10 m (INMET, NT 001/2011). Assume-se o anemômetro no topo do mastro (premissa).

### 2.3 Hargreaves-Samani (só para comparação)

Por dia local: Tmax = máximo das máximas horárias ("TEMPERATURA MÁXIMA NA HORA ANT."), Tmin = mínimo das mínimas horárias, Tmed = média da temperatura horária, Ra diária pela eq. 21 com J do dia local. ET0 = 0,0023·(Tmed + 17,8)·(Tmax − Tmin)^0,5·0,408·Ra (Hargreaves e Samani, 1985; FAO-56, eq. 52). O modelo não usa essa ET0; ela serve para medir o viés do método usado no v1.

## 3. Parâmetros ([`parametros.py`](../src/v2/parametros.py))

Todos ficam num único objeto (`ParametrosModelo`), gravado em todo arquivo de saída. Os derivados são calculados pelo código.

| Símbolo | Valor | Observação |
|---|---|---|
| θcc / θpmp | 0,28 / 0,14 cm³ cm⁻³ | faixa de solo franco do FAO-56 |
| θsat | 0,45 | premissa sem efeito no modelo (provado por teste) |
| p | 0,30 | FAO-56, Tabela 22 (alface), fixo |
| z₁ | 200 mm (0–20 cm) | zona radicular efetiva; sensibilidade com 300 mm |
| z₂ | 200 mm (20–40 cm) | abaixo da zona radicular |
| f_ext2 | 0,0 | fração da extração (ETa) retirada da camada 2 |
| θ₁(0), θ₂(0) | θcc | perfil na capacidade de campo no transplante, após a irrigação de plantio (premissa) |
| TAW | (θcc − θpmp)·z₁ | derivado |
| RAW | p·TAW | derivado |
| θlim | θcc − p·(θcc − θpmp) | derivado; θ₁ = θlim equivale a Dr = RAW |
| Kc | ini 0,70; mid 1,00; end 0,95 | FAO-56, Tabela 12 |
| Fases | Tabela 11 (alface: 20/30/15/10 = 75 d) escalonada a 70 d | derivado: proporção com arredondamento pelo maior resto |
| L (E1) | 10 mm | premissa; sensibilidade de 5 a 30 mm |
| A | 10 m² | 1 mm sobre 10 m² = 10 L |
| Cenários | Abundante 1.000 L / 3 d; Moderado 500 L / 7 d; Restrito 500 L / 14 d | premissa de cenário |

**Curva de Kc (FAO-56, eq. 66).** Com i = dia do ciclo e fases Lini, Ldev, Lmid, Llate:
Kc = Kc,ini até o fim da fase inicial; cresce linearmente até Kc,mid no fim da fase de desenvolvimento; fica em Kc,mid na fase média; varia linearmente até Kc,end no fim do ciclo. O Kc é constante dentro do dia local. O modelo não aplica o ajuste climático do Kc,mid (eq. 62); o pipeline calcula esse ajuste como diagnóstico.

**Condições iniciais.** θ₁(0) = θ₂(0) = θcc, isto é, Dr = 0 às 00:00 locais do primeiro dia; o reservatório começa cheio. Ambas ficam gravadas nas saídas.

## 4. Passo horário ([`modelo.py`](../src/v2/modelo.py))

Para cada hora h do ciclo, nesta ordem:

1. **Decisão** no início da hora, com o estado no fim da hora h−1 → lâmina pedida.
2. **Reservatório:** I = mín(pedida; V/A); V ← V − I·A. A irrigação é um pulso no início da hora.
3. **Ks** pela depleção depois da irrigação: Dr = (θcc − θ₁)·z₁; Ks = 1 se Dr ≤ RAW; senão Ks = (TAW − Dr)/(TAW − RAW) (FAO-56, eq. 84).
4. **ETc = Kc·ET0; ETa = Ks·ETc**, limitada para θ₁ nunca ficar abaixo de θpmp. Com f_ext2 > 0, a fração f_ext2 da ETa sai da camada 2 (também limitada a θpmp); no padrão, f_ext2 = 0.
5. **Camada 1:** S₁ = θ₁·z₁ + I + P − ETa₁; D₁ = máx(0; S₁ − θcc·z₁); θ₁ = (S₁ − D₁)/z₁.
6. **Camada 2:** S₂ = θ₂·z₂ + D₁ − ETa₂; D₂ = máx(0; S₂ − θcc·z₂); θ₂ = (S₂ − D₂)/z₂.
7. **Percolação profunda = D₂.**
8. Toda a chuva infiltra (sem escoamento superficial) e a drenagem acima de θcc é instantânea dentro da hora.
9. **Reabastecimento:** reservatório cheio às 00:00 locais do dia 1 e reposto à capacidade às 00:00 dos dias 1 + N, 1 + 2N, …

## 5. Estratégias: o que cada uma sabe ao decidir

Todas as estratégias decidem no início de cada hora h usando apenas informação disponível até o fim da hora h−1. Nenhuma conhece a chuva nem a ET0 da hora h. Para isolar o efeito da **regra de decisão**, todas recebem informação perfeita do estado do solo: E1 lê a umidade real da camada 1 (sensor sem erro, lido de hora em hora) e E2/E3 conhecem a depleção real, calculada pelo mesmo balanço do FAO-56. Erros de sensor e de estimativa ficam para a fase de campo.

- **E1, limiar fixo:** se θ₁ ≤ θlim (equivale a Dr ≥ RAW), pede a lâmina fixa L.
- **E2, reposição por balanço hídrico:** se Dr ≥ RAW, pede Dr (repõe até θcc). O gatilho é o mesmo de E1; muda só a lâmina.
- **E3, racionamento uniforme:** às 00:00 locais calcula a cota do dia, B = (V/A)/n, em que n é o número de dias até a próxima reposição, contando o dia atual. Durante o dia, se Dr ≥ RAW, pede mín(Dr; B − já aplicado no dia). Conhece o calendário de reposição, que é periódico e continua além do fim do ciclo: com N = 3, o dia 70 é dia de reposição e a próxima seria no dia 73, então n = 3 nesse dia.
- **Sequeiro:** I = 0. É o contrafactual usado na percolação incremental.
- **Acionamento** = hora com I > 0.

O teste `TestNaoAntecipacao` prova a regra de informação: alterar P e ET0 das horas ≥ k não muda nenhuma lâmina das horas ≤ k, para as três estratégias.

**Tempo de detecção.** Como a decisão é tomada de hora em hora, cada acionamento é precedido de no máximo uma hora com Dr > RAW (enquanto houver água no reservatório): a hora em que a depleção cruza o RAW. No v1, com passo diário, esse atraso era de um dia inteiro. O teste `test_deteccao_em_no_maximo_uma_hora` verifica isso.

## 6. Camada 2

Com f_ext2 = 0 e θ₂(0) = θcc, a camada 2 fica em θcc e D₂ = D₁ em todas as horas. Isso é esperado. A percolação reportada é, portanto, a drenagem abaixo da zona radicular. A camada 2 corresponde à segunda profundidade de sensor da fase de campo (30 cm), onde a redistribuição será medida. Mudar θsat (0,40 e 0,50) ou z₂ (100 e 300 mm) não altera nenhuma métrica (teste `test_theta_sat_e_z2_nao_mudam_nenhuma_metrica`).

## 7. Métricas por rodada

| Métrica | Definição |
|---|---|
| **TSE — tempo sem estresse hídrico (%)** | % das horas do ciclo com Dr ≤ RAW no fim da hora (Ks = 1). Substitui o "conforto hídrico" do v1 |
| TSE diário (%) | % dos dias locais sem nenhuma hora com Dr > RAW no fim da hora. Serve para a comparação com o v1 |
| ETa/ETc (%) | ΣETa/ΣETc: mede a intensidade do estresse, não só a duração |
| Dr máx (mm) e θ₁ mín | pior momento do ciclo |
| Aplicada (mm) e acionamentos | ΣI; número de horas com I > 0 |
| Percolação total e incremental (mm) | ΣD₂; ΣD₂ − ΣD₂ do sequeiro do mesmo ciclo |
| Eficiência incremental (%) | (aplicada − percolação incremental)/aplicada |
| Dias com reservatório vazio | dias locais com V < 0,5 L no fim de alguma hora |
| Erro de balanço (mm) | ΔS₁ + ΔS₂ − (ΣP + ΣI − ΣETa − ΣD₂); fica abaixo de 10⁻⁶ mm em todas as rodadas |

**Por que não há "lâmina não atendida" no v2.** No v1, com decisão diária, o pedido não atendido era um por dia. Com decisão horária, quando o tanque está vazio a estratégia continua pedindo a cada hora, e a soma desses pedidos repetidos deixa de ter sentido físico. O efeito do tanque vazio aparece no TSE, na ETa/ETc, no Dr máximo e nos dias com reservatório vazio.

**Dias vazios em E3.** No último dia antes de cada reposição, n = 1 e a cota é toda a água restante; se ela for usada, o tanque termina o dia vazio. Nesse caso o "dia vazio" de E3 indica água aproveitada até o fim do período, não falta antecipada.

## 8. Tolerâncias numéricas

- Lâminas abaixo de 10⁻⁹ mm são tratadas como zero (resíduos de ponto flutuante não contam como acionamento).
- As comparações Dr ≥ RAW (gatilho) e Dr ≤ RAW (TSE) usam folga de 10⁻⁹ mm.

## 9. Limitações

1. **Um só ano.** As simulações usam 2023, o ano mais recente com os dois ciclos completos na estação A204. O pipeline compara a chuva dos ciclos com a normal 1991–2020 e confere a completude de 2024 e 2025, mas não simula outros anos.
2. **Camada 2 sem extração** (f_ext2 = 0) e sem ascensão capilar.
3. **Drenagem instantânea:** toda água acima de θcc sai da camada na mesma hora, sem curva de condutividade.
4. **Sem escoamento superficial:** toda a chuva infiltra, inclusive nas horas de chuva intensa.
5. **Parâmetros de literatura:** θcc, θpmp, p, Kc e fases vêm do FAO-56; serão substituídos pela caracterização do solo e da cultura na fase de campo.
6. **Informação perfeita:** as estratégias conhecem o estado real do solo; erros de sensor e de estimativa ficam para a fase de campo.
7. **Kc sem ajuste climático:** o Kc,mid da Tabela 12 não é corrigido pela eq. 62 (o ajuste é calculado como diagnóstico).
8. **p fixo:** p = 0,30 em todo o ciclo, sem o ajuste pela ETc diária (a faixa do ajuste é calculada como diagnóstico).
9. **ET0 negativa zerada:** a condensação noturna não entra no balanço.
10. **Anemômetro assumido a 10 m**, no topo do mastro da estação.

## 10. Diferenças em relação ao v1

| Aspecto | v1 | v2 |
|---|---|---|
| Passo de tempo | diário (dias UTC) | horário (dias locais, UTC − 3) |
| ET0 | Hargreaves-Samani | Penman-Monteith horário (FAO-56, eq. 53) |
| Estresse | ETc integral até θpmp | Ks do FAO-56 (eq. 84) |
| Kc | degraus 0,70 / 1,00 / 0,95 | curva da eq. 66 com fases da Tabela 11 |
| p | 0,35 | 0,30 (Tabela 22, alface) |
| Gatilho de E2/E3 | déficit acumulado ≥ 10,0 mm (θlim correspondia a 9,8 mm) | Dr ≥ RAW, calculado |
| Informação | E2/E3 usavam ETc e chuva do próprio dia antes de decidir | só informação até a hora anterior (teste de não antecipação) |
| Métrica de estresse | "conforto hídrico": % de dias com θ₁ ≥ θlim no fim do dia | TSE: % de horas com Dr ≤ RAW; mais ETa/ETc e Dr máx |
| Condições iniciais | implícitas | parâmetros explícitos, gravados nas saídas |
| Lâmina não atendida | reportada | retirada (seção 7) |

O v1 continua reproduzível com `python3 main.py pipeline --modelo v1`.
