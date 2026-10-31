**Parâmetros do modelo v2**

| Símbolo | Significado | Valor | Unidade | Fonte |
|---|---|---:|---|---|
| θcc | Umidade na capacidade de campo | 0,28 | cm³ cm⁻³ | FAO-56, Tabela 19 (solo franco: θcc 0,20–0,30; θpmp 0,07–0,17); página [A CONFIRMAR PELO AUTOR] |
| θpmp | Umidade no ponto de murcha permanente | 0,14 | cm³ cm⁻³ | FAO-56, Tabela 19 (solo franco: θcc 0,20–0,30; θpmp 0,07–0,17); página [A CONFIRMAR PELO AUTOR] |
| θsat | Umidade na saturação | 0,45 | cm³ cm⁻³ | premissa do modelo, sem efeito nas métricas (teste) |
| p | Fração da TAW esgotável sem estresse | 0,30 | — | FAO-56, Tabela 22 (alface, p = 0,30) |
| z₁ | Espessura da camada 1 (zona radicular efetiva, 0–20 cm) | 200,0 | mm | Marouelli et al. (2008), página [A CONFIRMAR PELO AUTOR]; FAO-56, Tabela 22 (0,3–0,5 m) |
| z₂ | Espessura da camada 2 (20–40 cm) | 200,0 | mm | premissa do modelo, sem efeito nas métricas (teste) |
| f_ext2 | Fração da ETa retirada da camada 2 | 0,0 | — | premissa do modelo |
| θ₁(0), θ₂(0) | Umidade inicial das camadas (perfil na capacidade de campo) | 0,28 | cm³ cm⁻³ | premissa do modelo |
| TAW | Água disponível total, (θcc − θpmp)·z₁ | 28,0 | mm | derivado (calculado pelo código) |
| RAW | Água facilmente disponível, p·TAW | 8,4 | mm | derivado (calculado pelo código) |
| θlim | Umidade em que Dr = RAW, θcc − p·(θcc − θpmp) | 0,238 | cm³ cm⁻³ | derivado (calculado pelo código) |
| Kc,ini | Coeficiente de cultura, fase inicial | 0,70 | — | FAO-56, Tabela 12 |
| Kc,mid | Coeficiente de cultura, fase média | 1,00 | — | FAO-56, Tabela 12 |
| Kc,end | Coeficiente de cultura, fim do ciclo | 0,95 | — | FAO-56, Tabela 12 |
| Lini/Ldev/Lmid/Llate | Duração das fases do Kc | 19/28/14/9 | d | FAO-56, Tabela 11 (alface 20/30/15/10 d), escalonada a 70 d |
| L | Lâmina fixa de E1 (sensibilidade de 5 a 30 mm) | 10,0 | mm | premissa do modelo |
| A | Área do canteiro (1 mm = 10 L) | 10 | m² | premissa do modelo |
| V / N | Capacidade e intervalo de reposição dos cenários | 1.000/3; 500/7; 500/14 | L / d | premissa de cenário |
| z_u | Altura do anemômetro | 10 | m | INMET, NT 001/2011 (mastro de 10 m); anemômetro no topo, premissa |

Derivados calculados pelo código. Fontes completas em docs/FONTES_PARAMETROS.md.
