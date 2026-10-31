# Números do artigo (modelo v2)

Gerado por `python3 main.py pipeline`. Cada valor vem do arquivo, da linha física e da coluna indicados (caminhos relativos a `resultados/v2/`; as linhas contam o cabeçalho `#` de metadados). Para conferir todos contra os CSVs: `python3 main.py conferir`.

## 1. Clima dos ciclos, viés PM × HS e normal

| Nº | Descrição | Valor | Fonte |
|---:|---|---:|---|
| 1 | Chuva no ciclo chuvoso | 299,2 mm | `tabelas/tab_clima_ciclos.csv:6` (`chuva_mm`) |
| 2 | ΣET0 Penman-Monteith, ciclo chuvoso | 279,0 mm | `tabelas/tab_clima_ciclos.csv:6` (`et0_pm_mm`) |
| 3 | ET0 Penman-Monteith média, ciclo chuvoso | 3,99 mm/d | `tabelas/tab_clima_ciclos.csv:6` (`et0_pm_mm_dia`) |
| 4 | ΣET0 Hargreaves-Samani (dias locais), ciclo chuvoso | 357,4 mm | `tabelas/tab_clima_ciclos.csv:6` (`et0_hs_mm`) |
| 5 | Viés HS em relação a PM, ciclo chuvoso | +28,1% | `tabelas/tab_clima_ciclos.csv:6` (`vies_hs_pct`) |
| 6 | ΣETc potencial (curva de Kc), ciclo chuvoso | 237,9 mm | `tabelas/tab_clima_ciclos.csv:6` (`etc_mm`) |
| 7 | T média do ar, ciclo chuvoso | 25,6 °C | `tabelas/tab_clima_ciclos.csv:6` (`t_media_c`) |
| 8 | u₂ médio, ciclo chuvoso | 0,71 m/s | `tabelas/tab_clima_ciclos.csv:6` (`u2_medio_ms`) |
| 9 | Dias com chuva, ciclo chuvoso | 41 | `tabelas/tab_clima_ciclos.csv:6` (`dias_com_chuva`) |
| 10 | Maior chuva diária (dia local), ciclo chuvoso | 77,8 mm | `tabelas/tab_clima_ciclos.csv:6` (`maior_chuva_diaria_mm`) |
| 11 | Data da maior chuva diária, ciclo chuvoso | 17/03/2023 | `tabelas/tab_clima_ciclos.csv:6` (`data_maior_chuva_diaria`) |
| 12 | Maior chuva horária, ciclo chuvoso | 40,0 mm | `tabelas/tab_clima_ciclos.csv:6` (`maior_chuva_horaria_mm`) |
| 13 | Normal 1991–2020 da janela, ciclo chuvoso | [A CONFIRMAR PELO AUTOR] | `tabelas/tab_normal_climatologica.csv:6` (`normal_janela_mm`) |
| 14 | Chuva de 2023 em % da normal, ciclo chuvoso | [A CONFIRMAR PELO AUTOR] | `tabelas/tab_normal_climatologica.csv:6` (`chuva_sobre_normal_pct`) |
| 15 | Chuva no ciclo seco | 42,2 mm | `tabelas/tab_clima_ciclos.csv:7` (`chuva_mm`) |
| 16 | ΣET0 Penman-Monteith, ciclo seco | 358,5 mm | `tabelas/tab_clima_ciclos.csv:7` (`et0_pm_mm`) |
| 17 | ET0 Penman-Monteith média, ciclo seco | 5,12 mm/d | `tabelas/tab_clima_ciclos.csv:7` (`et0_pm_mm_dia`) |
| 18 | ΣET0 Hargreaves-Samani (dias locais), ciclo seco | 409,4 mm | `tabelas/tab_clima_ciclos.csv:7` (`et0_hs_mm`) |
| 19 | Viés HS em relação a PM, ciclo seco | +14,2% | `tabelas/tab_clima_ciclos.csv:7` (`vies_hs_pct`) |
| 20 | ΣETc potencial (curva de Kc), ciclo seco | 308,5 mm | `tabelas/tab_clima_ciclos.csv:7` (`etc_mm`) |
| 21 | T média do ar, ciclo seco | 27,4 °C | `tabelas/tab_clima_ciclos.csv:7` (`t_media_c`) |
| 22 | u₂ médio, ciclo seco | 1,04 m/s | `tabelas/tab_clima_ciclos.csv:7` (`u2_medio_ms`) |
| 23 | Dias com chuva, ciclo seco | 4 | `tabelas/tab_clima_ciclos.csv:7` (`dias_com_chuva`) |
| 24 | Maior chuva diária (dia local), ciclo seco | 26,2 mm | `tabelas/tab_clima_ciclos.csv:7` (`maior_chuva_diaria_mm`) |
| 25 | Data da maior chuva diária, ciclo seco | 31/08/2023 | `tabelas/tab_clima_ciclos.csv:7` (`data_maior_chuva_diaria`) |
| 26 | Maior chuva horária, ciclo seco | 16,2 mm | `tabelas/tab_clima_ciclos.csv:7` (`maior_chuva_horaria_mm`) |
| 27 | Normal 1991–2020 da janela, ciclo seco | [A CONFIRMAR PELO AUTOR] | `tabelas/tab_normal_climatologica.csv:7` (`normal_janela_mm`) |
| 28 | Chuva de 2023 em % da normal, ciclo seco | [A CONFIRMAR PELO AUTOR] | `tabelas/tab_normal_climatologica.csv:7` (`chuva_sobre_normal_pct`) |

## 2. Parâmetros e cenários

| Nº | Descrição | Valor | Fonte |
|---:|---|---:|---|
| 29 | TAW (z₁ = 200 mm) | 28,0 mm | `tabelas/tab_parametros.csv:14` (`valor`) |
| 30 | RAW (z₁ = 200 mm) | 8,4 mm | `tabelas/tab_parametros.csv:15` (`valor`) |
| 31 | θlim | 0,238 cm³ cm⁻³ | `tabelas/tab_parametros.csv:16` (`valor`) |
| 32 | Fases do Kc (dias) | 19/28/14/9 | `tabelas/tab_parametros.csv:20` (`valor`) |
| 33 | Oferta máxima, cenário abundante | 33,3 mm/d | `tabelas/tab_cenarios.csv:6` (`oferta_maxima_mm_dia`) |
| 34 | Oferta no ciclo, cenário abundante | 2.400,0 mm | `tabelas/tab_cenarios.csv:6` (`oferta_no_ciclo_mm`) |
| 35 | Oferta máxima, cenário moderado | 7,1 mm/d | `tabelas/tab_cenarios.csv:7` (`oferta_maxima_mm_dia`) |
| 36 | Oferta no ciclo, cenário moderado | 500,0 mm | `tabelas/tab_cenarios.csv:7` (`oferta_no_ciclo_mm`) |
| 37 | Oferta máxima, cenário restrito | 3,6 mm/d | `tabelas/tab_cenarios.csv:8` (`oferta_maxima_mm_dia`) |
| 38 | Oferta no ciclo, cenário restrito | 250,0 mm | `tabelas/tab_cenarios.csv:8` (`oferta_no_ciclo_mm`) |

## 3. Desempenho, ciclo chuvoso

| Nº | Descrição | Valor | Fonte |
|---:|---|---:|---|
| 39 | E1, abundante: aplicada | 180,0 mm | `tabelas/tab_desempenho_chuvoso.csv:6` (`aplicada_mm`) |
| 40 | E1, abundante: acionamentos | 18 | `tabelas/tab_desempenho_chuvoso.csv:6` (`acionamentos`) |
| 41 | E1, abundante: percolação incremental | 103,4 mm | `tabelas/tab_desempenho_chuvoso.csv:6` (`percolacao_incremental_mm`) |
| 42 | E1, abundante: eficiência incremental | 42,5% | `tabelas/tab_desempenho_chuvoso.csv:6` (`eficiencia_incremental_pct`) |
| 43 | E1, abundante: TSE | 98,9% | `tabelas/tab_desempenho_chuvoso.csv:6` (`tse_pct`) |
| 44 | E1, abundante: ETa/ETc | 100,0% | `tabelas/tab_desempenho_chuvoso.csv:6` (`eta_etc_pct`) |
| 45 | E1, abundante: Dr máx | 9,0 mm | `tabelas/tab_desempenho_chuvoso.csv:6` (`dr_max_mm`) |
| 46 | E1, abundante: dias com reservatório vazio | 0 | `tabelas/tab_desempenho_chuvoso.csv:6` (`dias_reservatorio_vazio`) |
| 47 | E2, abundante: aplicada | 164,0 mm | `tabelas/tab_desempenho_chuvoso.csv:7` (`aplicada_mm`) |
| 48 | E2, abundante: acionamentos | 19 | `tabelas/tab_desempenho_chuvoso.csv:7` (`acionamentos`) |
| 49 | E2, abundante: percolação incremental | 88,0 mm | `tabelas/tab_desempenho_chuvoso.csv:7` (`percolacao_incremental_mm`) |
| 50 | E2, abundante: eficiência incremental | 46,3% | `tabelas/tab_desempenho_chuvoso.csv:7` (`eficiencia_incremental_pct`) |
| 51 | E2, abundante: TSE | 98,9% | `tabelas/tab_desempenho_chuvoso.csv:7` (`tse_pct`) |
| 52 | E2, abundante: ETa/ETc | 100,0% | `tabelas/tab_desempenho_chuvoso.csv:7` (`eta_etc_pct`) |
| 53 | E2, abundante: Dr máx | 9,0 mm | `tabelas/tab_desempenho_chuvoso.csv:7` (`dr_max_mm`) |
| 54 | E2, abundante: dias com reservatório vazio | 0 | `tabelas/tab_desempenho_chuvoso.csv:7` (`dias_reservatorio_vazio`) |
| 55 | E3, abundante: aplicada | 164,0 mm | `tabelas/tab_desempenho_chuvoso.csv:8` (`aplicada_mm`) |
| 56 | E3, abundante: acionamentos | 19 | `tabelas/tab_desempenho_chuvoso.csv:8` (`acionamentos`) |
| 57 | E3, abundante: percolação incremental | 88,0 mm | `tabelas/tab_desempenho_chuvoso.csv:8` (`percolacao_incremental_mm`) |
| 58 | E3, abundante: eficiência incremental | 46,3% | `tabelas/tab_desempenho_chuvoso.csv:8` (`eficiencia_incremental_pct`) |
| 59 | E3, abundante: TSE | 98,9% | `tabelas/tab_desempenho_chuvoso.csv:8` (`tse_pct`) |
| 60 | E3, abundante: ETa/ETc | 100,0% | `tabelas/tab_desempenho_chuvoso.csv:8` (`eta_etc_pct`) |
| 61 | E3, abundante: Dr máx | 9,0 mm | `tabelas/tab_desempenho_chuvoso.csv:8` (`dr_max_mm`) |
| 62 | E3, abundante: dias com reservatório vazio | 0 | `tabelas/tab_desempenho_chuvoso.csv:8` (`dias_reservatorio_vazio`) |
| 63 | E1, moderado: aplicada | 180,0 mm | `tabelas/tab_desempenho_chuvoso.csv:9` (`aplicada_mm`) |
| 64 | E1, moderado: acionamentos | 18 | `tabelas/tab_desempenho_chuvoso.csv:9` (`acionamentos`) |
| 65 | E1, moderado: percolação incremental | 103,4 mm | `tabelas/tab_desempenho_chuvoso.csv:9` (`percolacao_incremental_mm`) |
| 66 | E1, moderado: eficiência incremental | 42,5% | `tabelas/tab_desempenho_chuvoso.csv:9` (`eficiencia_incremental_pct`) |
| 67 | E1, moderado: TSE | 98,9% | `tabelas/tab_desempenho_chuvoso.csv:9` (`tse_pct`) |
| 68 | E1, moderado: ETa/ETc | 100,0% | `tabelas/tab_desempenho_chuvoso.csv:9` (`eta_etc_pct`) |
| 69 | E1, moderado: Dr máx | 9,0 mm | `tabelas/tab_desempenho_chuvoso.csv:9` (`dr_max_mm`) |
| 70 | E1, moderado: dias com reservatório vazio | 0 | `tabelas/tab_desempenho_chuvoso.csv:9` (`dias_reservatorio_vazio`) |
| 71 | E2, moderado: aplicada | 164,0 mm | `tabelas/tab_desempenho_chuvoso.csv:10` (`aplicada_mm`) |
| 72 | E2, moderado: acionamentos | 19 | `tabelas/tab_desempenho_chuvoso.csv:10` (`acionamentos`) |
| 73 | E2, moderado: percolação incremental | 88,0 mm | `tabelas/tab_desempenho_chuvoso.csv:10` (`percolacao_incremental_mm`) |
| 74 | E2, moderado: eficiência incremental | 46,3% | `tabelas/tab_desempenho_chuvoso.csv:10` (`eficiencia_incremental_pct`) |
| 75 | E2, moderado: TSE | 98,9% | `tabelas/tab_desempenho_chuvoso.csv:10` (`tse_pct`) |
| 76 | E2, moderado: ETa/ETc | 100,0% | `tabelas/tab_desempenho_chuvoso.csv:10` (`eta_etc_pct`) |
| 77 | E2, moderado: Dr máx | 9,0 mm | `tabelas/tab_desempenho_chuvoso.csv:10` (`dr_max_mm`) |
| 78 | E2, moderado: dias com reservatório vazio | 0 | `tabelas/tab_desempenho_chuvoso.csv:10` (`dias_reservatorio_vazio`) |
| 79 | E3, moderado: aplicada | 158,9 mm | `tabelas/tab_desempenho_chuvoso.csv:11` (`aplicada_mm`) |
| 80 | E3, moderado: acionamentos | 19 | `tabelas/tab_desempenho_chuvoso.csv:11` (`acionamentos`) |
| 81 | E3, moderado: percolação incremental | 82,9 mm | `tabelas/tab_desempenho_chuvoso.csv:11` (`percolacao_incremental_mm`) |
| 82 | E3, moderado: eficiência incremental | 47,8% | `tabelas/tab_desempenho_chuvoso.csv:11` (`eficiencia_incremental_pct`) |
| 83 | E3, moderado: TSE | 98,9% | `tabelas/tab_desempenho_chuvoso.csv:11` (`tse_pct`) |
| 84 | E3, moderado: ETa/ETc | 100,0% | `tabelas/tab_desempenho_chuvoso.csv:11` (`eta_etc_pct`) |
| 85 | E3, moderado: Dr máx | 9,0 mm | `tabelas/tab_desempenho_chuvoso.csv:11` (`dr_max_mm`) |
| 86 | E3, moderado: dias com reservatório vazio | 0 | `tabelas/tab_desempenho_chuvoso.csv:11` (`dias_reservatorio_vazio`) |
| 87 | E1, restrito: aplicada | 170,0 mm | `tabelas/tab_desempenho_chuvoso.csv:12` (`aplicada_mm`) |
| 88 | E1, restrito: acionamentos | 17 | `tabelas/tab_desempenho_chuvoso.csv:12` (`acionamentos`) |
| 89 | E1, restrito: percolação incremental | 93,7 mm | `tabelas/tab_desempenho_chuvoso.csv:12` (`percolacao_incremental_mm`) |
| 90 | E1, restrito: eficiência incremental | 44,9% | `tabelas/tab_desempenho_chuvoso.csv:12` (`eficiencia_incremental_pct`) |
| 91 | E1, restrito: TSE | 98,5% | `tabelas/tab_desempenho_chuvoso.csv:12` (`tse_pct`) |
| 92 | E1, restrito: ETa/ETc | 99,9% | `tabelas/tab_desempenho_chuvoso.csv:12` (`eta_etc_pct`) |
| 93 | E1, restrito: Dr máx | 11,4 mm | `tabelas/tab_desempenho_chuvoso.csv:12` (`dr_max_mm`) |
| 94 | E1, restrito: dias com reservatório vazio | 4 | `tabelas/tab_desempenho_chuvoso.csv:12` (`dias_reservatorio_vazio`) |
| 95 | E2, restrito: aplicada | 162,0 mm | `tabelas/tab_desempenho_chuvoso.csv:13` (`aplicada_mm`) |
| 96 | E2, restrito: acionamentos | 19 | `tabelas/tab_desempenho_chuvoso.csv:13` (`acionamentos`) |
| 97 | E2, restrito: percolação incremental | 86,1 mm | `tabelas/tab_desempenho_chuvoso.csv:13` (`percolacao_incremental_mm`) |
| 98 | E2, restrito: eficiência incremental | 46,9% | `tabelas/tab_desempenho_chuvoso.csv:13` (`eficiencia_incremental_pct`) |
| 99 | E2, restrito: TSE | 98,9% | `tabelas/tab_desempenho_chuvoso.csv:13` (`tse_pct`) |
| 100 | E2, restrito: ETa/ETc | 100,0% | `tabelas/tab_desempenho_chuvoso.csv:13` (`eta_etc_pct`) |
| 101 | E2, restrito: Dr máx | 9,0 mm | `tabelas/tab_desempenho_chuvoso.csv:13` (`dr_max_mm`) |
| 102 | E2, restrito: dias com reservatório vazio | 1 | `tabelas/tab_desempenho_chuvoso.csv:13` (`dias_reservatorio_vazio`) |
| 103 | E3, restrito: aplicada | 139,9 mm | `tabelas/tab_desempenho_chuvoso.csv:14` (`aplicada_mm`) |
| 104 | E3, restrito: acionamentos | 25 | `tabelas/tab_desempenho_chuvoso.csv:14` (`acionamentos`) |
| 105 | E3, restrito: percolação incremental | 64,1 mm | `tabelas/tab_desempenho_chuvoso.csv:14` (`percolacao_incremental_mm`) |
| 106 | E3, restrito: eficiência incremental | 54,2% | `tabelas/tab_desempenho_chuvoso.csv:14` (`eficiencia_incremental_pct`) |
| 107 | E3, restrito: TSE | 94,4% | `tabelas/tab_desempenho_chuvoso.csv:14` (`tse_pct`) |
| 108 | E3, restrito: ETa/ETc | 99,9% | `tabelas/tab_desempenho_chuvoso.csv:14` (`eta_etc_pct`) |
| 109 | E3, restrito: Dr máx | 10,0 mm | `tabelas/tab_desempenho_chuvoso.csv:14` (`dr_max_mm`) |
| 110 | E3, restrito: dias com reservatório vazio | 0 | `tabelas/tab_desempenho_chuvoso.csv:14` (`dias_reservatorio_vazio`) |
| 111 | Sequeiro: percolação total | 145,3 mm | `tabelas/tab_desempenho_chuvoso.csv:15` (`percolacao_mm`) |
| 112 | Sequeiro: TSE | 39,2% | `tabelas/tab_desempenho_chuvoso.csv:15` (`tse_pct`) |
| 113 | Sequeiro: ETa/ETc | 71,2% | `tabelas/tab_desempenho_chuvoso.csv:15` (`eta_etc_pct`) |
| 114 | Sequeiro: Dr máx | 24,8 mm | `tabelas/tab_desempenho_chuvoso.csv:15` (`dr_max_mm`) |

## 3. Desempenho, ciclo seco

| Nº | Descrição | Valor | Fonte |
|---:|---|---:|---|
| 115 | E1, abundante: aplicada | 320,0 mm | `tabelas/tab_desempenho_seco.csv:6` (`aplicada_mm`) |
| 116 | E1, abundante: acionamentos | 32 | `tabelas/tab_desempenho_seco.csv:6` (`acionamentos`) |
| 117 | E1, abundante: percolação incremental | 52,7 mm | `tabelas/tab_desempenho_seco.csv:6` (`percolacao_incremental_mm`) |
| 118 | E1, abundante: eficiência incremental | 83,5% | `tabelas/tab_desempenho_seco.csv:6` (`eficiencia_incremental_pct`) |
| 119 | E1, abundante: TSE | 98,1% | `tabelas/tab_desempenho_seco.csv:6` (`tse_pct`) |
| 120 | E1, abundante: ETa/ETc | 100,0% | `tabelas/tab_desempenho_seco.csv:6` (`eta_etc_pct`) |
| 121 | E1, abundante: Dr máx | 9,0 mm | `tabelas/tab_desempenho_seco.csv:6` (`dr_max_mm`) |
| 122 | E1, abundante: dias com reservatório vazio | 0 | `tabelas/tab_desempenho_seco.csv:6` (`dias_reservatorio_vazio`) |
| 123 | E2, abundante: aplicada | 285,1 mm | `tabelas/tab_desempenho_seco.csv:7` (`aplicada_mm`) |
| 124 | E2, abundante: acionamentos | 33 | `tabelas/tab_desempenho_seco.csv:7` (`acionamentos`) |
| 125 | E2, abundante: percolação incremental | 19,3 mm | `tabelas/tab_desempenho_seco.csv:7` (`percolacao_incremental_mm`) |
| 126 | E2, abundante: eficiência incremental | 93,2% | `tabelas/tab_desempenho_seco.csv:7` (`eficiencia_incremental_pct`) |
| 127 | E2, abundante: TSE | 98,0% | `tabelas/tab_desempenho_seco.csv:7` (`tse_pct`) |
| 128 | E2, abundante: ETa/ETc | 100,0% | `tabelas/tab_desempenho_seco.csv:7` (`eta_etc_pct`) |
| 129 | E2, abundante: Dr máx | 9,1 mm | `tabelas/tab_desempenho_seco.csv:7` (`dr_max_mm`) |
| 130 | E2, abundante: dias com reservatório vazio | 0 | `tabelas/tab_desempenho_seco.csv:7` (`dias_reservatorio_vazio`) |
| 131 | E3, abundante: aplicada | 285,1 mm | `tabelas/tab_desempenho_seco.csv:8` (`aplicada_mm`) |
| 132 | E3, abundante: acionamentos | 33 | `tabelas/tab_desempenho_seco.csv:8` (`acionamentos`) |
| 133 | E3, abundante: percolação incremental | 19,3 mm | `tabelas/tab_desempenho_seco.csv:8` (`percolacao_incremental_mm`) |
| 134 | E3, abundante: eficiência incremental | 93,2% | `tabelas/tab_desempenho_seco.csv:8` (`eficiencia_incremental_pct`) |
| 135 | E3, abundante: TSE | 98,0% | `tabelas/tab_desempenho_seco.csv:8` (`tse_pct`) |
| 136 | E3, abundante: ETa/ETc | 100,0% | `tabelas/tab_desempenho_seco.csv:8` (`eta_etc_pct`) |
| 137 | E3, abundante: Dr máx | 9,1 mm | `tabelas/tab_desempenho_seco.csv:8` (`dr_max_mm`) |
| 138 | E3, abundante: dias com reservatório vazio | 0 | `tabelas/tab_desempenho_seco.csv:8` (`dias_reservatorio_vazio`) |
| 139 | E1, moderado: aplicada | 320,0 mm | `tabelas/tab_desempenho_seco.csv:9` (`aplicada_mm`) |
| 140 | E1, moderado: acionamentos | 32 | `tabelas/tab_desempenho_seco.csv:9` (`acionamentos`) |
| 141 | E1, moderado: percolação incremental | 52,7 mm | `tabelas/tab_desempenho_seco.csv:9` (`percolacao_incremental_mm`) |
| 142 | E1, moderado: eficiência incremental | 83,5% | `tabelas/tab_desempenho_seco.csv:9` (`eficiencia_incremental_pct`) |
| 143 | E1, moderado: TSE | 98,1% | `tabelas/tab_desempenho_seco.csv:9` (`tse_pct`) |
| 144 | E1, moderado: ETa/ETc | 100,0% | `tabelas/tab_desempenho_seco.csv:9` (`eta_etc_pct`) |
| 145 | E1, moderado: Dr máx | 9,0 mm | `tabelas/tab_desempenho_seco.csv:9` (`dr_max_mm`) |
| 146 | E1, moderado: dias com reservatório vazio | 0 | `tabelas/tab_desempenho_seco.csv:9` (`dias_reservatorio_vazio`) |
| 147 | E2, moderado: aplicada | 285,1 mm | `tabelas/tab_desempenho_seco.csv:10` (`aplicada_mm`) |
| 148 | E2, moderado: acionamentos | 33 | `tabelas/tab_desempenho_seco.csv:10` (`acionamentos`) |
| 149 | E2, moderado: percolação incremental | 19,3 mm | `tabelas/tab_desempenho_seco.csv:10` (`percolacao_incremental_mm`) |
| 150 | E2, moderado: eficiência incremental | 93,2% | `tabelas/tab_desempenho_seco.csv:10` (`eficiencia_incremental_pct`) |
| 151 | E2, moderado: TSE | 98,0% | `tabelas/tab_desempenho_seco.csv:10` (`tse_pct`) |
| 152 | E2, moderado: ETa/ETc | 100,0% | `tabelas/tab_desempenho_seco.csv:10` (`eta_etc_pct`) |
| 153 | E2, moderado: Dr máx | 9,1 mm | `tabelas/tab_desempenho_seco.csv:10` (`dr_max_mm`) |
| 154 | E2, moderado: dias com reservatório vazio | 0 | `tabelas/tab_desempenho_seco.csv:10` (`dias_reservatorio_vazio`) |
| 155 | E3, moderado: aplicada | 297,9 mm | `tabelas/tab_desempenho_seco.csv:11` (`aplicada_mm`) |
| 156 | E3, moderado: acionamentos | 36 | `tabelas/tab_desempenho_seco.csv:11` (`acionamentos`) |
| 157 | E3, moderado: percolação incremental | 25,1 mm | `tabelas/tab_desempenho_seco.csv:11` (`percolacao_incremental_mm`) |
| 158 | E3, moderado: eficiência incremental | 91,6% | `tabelas/tab_desempenho_seco.csv:11` (`eficiencia_incremental_pct`) |
| 159 | E3, moderado: TSE | 97,9% | `tabelas/tab_desempenho_seco.csv:11` (`tse_pct`) |
| 160 | E3, moderado: ETa/ETc | 100,0% | `tabelas/tab_desempenho_seco.csv:11` (`eta_etc_pct`) |
| 161 | E3, moderado: Dr máx | 9,1 mm | `tabelas/tab_desempenho_seco.csv:11` (`dr_max_mm`) |
| 162 | E3, moderado: dias com reservatório vazio | 0 | `tabelas/tab_desempenho_seco.csv:11` (`dias_reservatorio_vazio`) |
| 163 | E1, restrito: aplicada | 250,0 mm | `tabelas/tab_desempenho_seco.csv:12` (`aplicada_mm`) |
| 164 | E1, restrito: acionamentos | 25 | `tabelas/tab_desempenho_seco.csv:12` (`acionamentos`) |
| 165 | E1, restrito: percolação incremental | 39,4 mm | `tabelas/tab_desempenho_seco.csv:12` (`percolacao_incremental_mm`) |
| 166 | E1, restrito: eficiência incremental | 84,2% | `tabelas/tab_desempenho_seco.csv:12` (`eficiencia_incremental_pct`) |
| 167 | E1, restrito: TSE | 74,3% | `tabelas/tab_desempenho_seco.csv:12` (`tse_pct`) |
| 168 | E1, restrito: ETa/ETc | 87,1% | `tabelas/tab_desempenho_seco.csv:12` (`eta_etc_pct`) |
| 169 | E1, restrito: Dr máx | 23,0 mm | `tabelas/tab_desempenho_seco.csv:12` (`dr_max_mm`) |
| 170 | E1, restrito: dias com reservatório vazio | 28 | `tabelas/tab_desempenho_seco.csv:12` (`dias_reservatorio_vazio`) |
| 171 | E2, restrito: aplicada | 242,6 mm | `tabelas/tab_desempenho_seco.csv:13` (`aplicada_mm`) |
| 172 | E2, restrito: acionamentos | 27 | `tabelas/tab_desempenho_seco.csv:13` (`acionamentos`) |
| 173 | E2, restrito: percolação incremental | 19,8 mm | `tabelas/tab_desempenho_seco.csv:13` (`percolacao_incremental_mm`) |
| 174 | E2, restrito: eficiência incremental | 91,9% | `tabelas/tab_desempenho_seco.csv:13` (`eficiencia_incremental_pct`) |
| 175 | E2, restrito: TSE | 79,3% | `tabelas/tab_desempenho_seco.csv:13` (`tse_pct`) |
| 176 | E2, restrito: ETa/ETc | 90,9% | `tabelas/tab_desempenho_seco.csv:13` (`eta_etc_pct`) |
| 177 | E2, restrito: Dr máx | 22,2 mm | `tabelas/tab_desempenho_seco.csv:13` (`dr_max_mm`) |
| 178 | E2, restrito: dias com reservatório vazio | 19 | `tabelas/tab_desempenho_seco.csv:13` (`dias_reservatorio_vazio`) |
| 179 | E3, restrito: aplicada | 241,6 mm | `tabelas/tab_desempenho_seco.csv:14` (`aplicada_mm`) |
| 180 | E3, restrito: acionamentos | 62 | `tabelas/tab_desempenho_seco.csv:14` (`acionamentos`) |
| 181 | E3, restrito: percolação incremental | 14,2 mm | `tabelas/tab_desempenho_seco.csv:14` (`percolacao_incremental_mm`) |
| 182 | E3, restrito: eficiência incremental | 94,1% | `tabelas/tab_desempenho_seco.csv:14` (`eficiencia_incremental_pct`) |
| 183 | E3, restrito: TSE | 54,9% | `tabelas/tab_desempenho_seco.csv:14` (`tse_pct`) |
| 184 | E3, restrito: ETa/ETc | 89,3% | `tabelas/tab_desempenho_seco.csv:14` (`eta_etc_pct`) |
| 185 | E3, restrito: Dr máx | 17,4 mm | `tabelas/tab_desempenho_seco.csv:14` (`dr_max_mm`) |
| 186 | E3, restrito: dias com reservatório vazio | 4 | `tabelas/tab_desempenho_seco.csv:14` (`dias_reservatorio_vazio`) |
| 187 | Sequeiro: percolação total | 6,7 mm | `tabelas/tab_desempenho_seco.csv:15` (`percolacao_mm`) |
| 188 | Sequeiro: TSE | 6,4% | `tabelas/tab_desempenho_seco.csv:15` (`tse_pct`) |
| 189 | Sequeiro: ETa/ETc | 19,5% | `tabelas/tab_desempenho_seco.csv:15` (`eta_etc_pct`) |
| 190 | Sequeiro: Dr máx | 28,0 mm | `tabelas/tab_desempenho_seco.csv:15` (`dr_max_mm`) |

## 4. Sensibilidade de E1 à lâmina (cenário abundante; Figura 1)

| Nº | Descrição | Valor | Fonte |
|---:|---|---:|---|
| 191 | E1, L = 5 mm, chuvoso: TSE | 98,3% | `tabelas/tab_sensibilidade_e1.csv:6` (`tse_pct`) |
| 192 | E1, L = 5 mm, chuvoso: percolação incremental | 63,1 mm | `tabelas/tab_sensibilidade_e1.csv:6` (`percolacao_incremental_mm`) |
| 193 | E1, L = 10 mm, chuvoso: TSE | 98,9% | `tabelas/tab_sensibilidade_e1.csv:7` (`tse_pct`) |
| 194 | E1, L = 10 mm, chuvoso: percolação incremental | 103,4 mm | `tabelas/tab_sensibilidade_e1.csv:7` (`percolacao_incremental_mm`) |
| 195 | E1, L = 15 mm, chuvoso: TSE | 98,9% | `tabelas/tab_sensibilidade_e1.csv:8` (`tse_pct`) |
| 196 | E1, L = 15 mm, chuvoso: percolação incremental | 193,4 mm | `tabelas/tab_sensibilidade_e1.csv:8` (`percolacao_incremental_mm`) |
| 197 | E1, L = 20 mm, chuvoso: TSE | 98,9% | `tabelas/tab_sensibilidade_e1.csv:9` (`tse_pct`) |
| 198 | E1, L = 20 mm, chuvoso: percolação incremental | 283,4 mm | `tabelas/tab_sensibilidade_e1.csv:9` (`percolacao_incremental_mm`) |
| 199 | E1, L = 25 mm, chuvoso: TSE | 98,9% | `tabelas/tab_sensibilidade_e1.csv:10` (`tse_pct`) |
| 200 | E1, L = 25 mm, chuvoso: percolação incremental | 373,4 mm | `tabelas/tab_sensibilidade_e1.csv:10` (`percolacao_incremental_mm`) |
| 201 | E1, L = 30 mm, chuvoso: TSE | 98,9% | `tabelas/tab_sensibilidade_e1.csv:11` (`tse_pct`) |
| 202 | E1, L = 30 mm, chuvoso: percolação incremental | 463,4 mm | `tabelas/tab_sensibilidade_e1.csv:11` (`percolacao_incremental_mm`) |
| 203 | E2 (referência), chuvoso: TSE | 98,9% | `tabelas/tab_sensibilidade_e1.csv:12` (`tse_pct`) |
| 204 | E2 (referência), chuvoso: percolação incremental | 88,0 mm | `tabelas/tab_sensibilidade_e1.csv:12` (`percolacao_incremental_mm`) |
| 205 | E1, L = 5 mm, seco: TSE | 96,6% | `tabelas/tab_sensibilidade_e1.csv:13` (`tse_pct`) |
| 206 | E1, L = 5 mm, seco: percolação incremental | 19,1 mm | `tabelas/tab_sensibilidade_e1.csv:13` (`percolacao_incremental_mm`) |
| 207 | E1, L = 10 mm, seco: TSE | 98,1% | `tabelas/tab_sensibilidade_e1.csv:14` (`tse_pct`) |
| 208 | E1, L = 10 mm, seco: percolação incremental | 52,7 mm | `tabelas/tab_sensibilidade_e1.csv:14` (`percolacao_incremental_mm`) |
| 209 | E1, L = 15 mm, seco: TSE | 98,1% | `tabelas/tab_sensibilidade_e1.csv:15` (`tse_pct`) |
| 210 | E1, L = 15 mm, seco: percolação incremental | 212,7 mm | `tabelas/tab_sensibilidade_e1.csv:15` (`percolacao_incremental_mm`) |
| 211 | E1, L = 20 mm, seco: TSE | 98,1% | `tabelas/tab_sensibilidade_e1.csv:16` (`tse_pct`) |
| 212 | E1, L = 20 mm, seco: percolação incremental | 372,7 mm | `tabelas/tab_sensibilidade_e1.csv:16` (`percolacao_incremental_mm`) |
| 213 | E1, L = 25 mm, seco: TSE | 98,1% | `tabelas/tab_sensibilidade_e1.csv:17` (`tse_pct`) |
| 214 | E1, L = 25 mm, seco: percolação incremental | 532,7 mm | `tabelas/tab_sensibilidade_e1.csv:17` (`percolacao_incremental_mm`) |
| 215 | E1, L = 30 mm, seco: TSE | 98,1% | `tabelas/tab_sensibilidade_e1.csv:18` (`tse_pct`) |
| 216 | E1, L = 30 mm, seco: percolação incremental | 692,7 mm | `tabelas/tab_sensibilidade_e1.csv:18` (`percolacao_incremental_mm`) |
| 217 | E2 (referência), seco: TSE | 98,0% | `tabelas/tab_sensibilidade_e1.csv:19` (`tse_pct`) |
| 218 | E2 (referência), seco: percolação incremental | 19,3 mm | `tabelas/tab_sensibilidade_e1.csv:19` (`percolacao_incremental_mm`) |

## 5. Ciclo seco, cenário restrito (Figura 2)

| Nº | Descrição | Valor | Fonte |
|---:|---|---:|---|
| 219 | E1: TSE | 74,3% | `tabelas/tab_desempenho_seco.csv:12` (`tse_pct`) |
| 220 | E1: ETa/ETc | 87,1% | `tabelas/tab_desempenho_seco.csv:12` (`eta_etc_pct`) |
| 221 | E1: Dr máx | 23,0 mm | `tabelas/tab_desempenho_seco.csv:12` (`dr_max_mm`) |
| 222 | E1: θ₁ mínima | 0,165 cm³ cm⁻³ | `tabelas/tab_desempenho_seco.csv:12` (`theta1_min`) |
| 223 | E1: acionamentos | 25 | `tabelas/tab_desempenho_seco.csv:12` (`acionamentos`) |
| 224 | E1: lâmina média por acionamento | 10,0 mm | `tabelas/tab_desempenho_seco.csv:12` (`lamina_media_mm`) |
| 225 | E1: dias com reservatório vazio | 28 | `tabelas/tab_desempenho_seco.csv:12` (`dias_reservatorio_vazio`) |
| 226 | E2: TSE | 79,3% | `tabelas/tab_desempenho_seco.csv:13` (`tse_pct`) |
| 227 | E2: ETa/ETc | 90,9% | `tabelas/tab_desempenho_seco.csv:13` (`eta_etc_pct`) |
| 228 | E2: Dr máx | 22,2 mm | `tabelas/tab_desempenho_seco.csv:13` (`dr_max_mm`) |
| 229 | E2: θ₁ mínima | 0,169 cm³ cm⁻³ | `tabelas/tab_desempenho_seco.csv:13` (`theta1_min`) |
| 230 | E2: acionamentos | 27 | `tabelas/tab_desempenho_seco.csv:13` (`acionamentos`) |
| 231 | E2: lâmina média por acionamento | 9,0 mm | `tabelas/tab_desempenho_seco.csv:13` (`lamina_media_mm`) |
| 232 | E2: dias com reservatório vazio | 19 | `tabelas/tab_desempenho_seco.csv:13` (`dias_reservatorio_vazio`) |
| 233 | E3: TSE | 54,9% | `tabelas/tab_desempenho_seco.csv:14` (`tse_pct`) |
| 234 | E3: ETa/ETc | 89,3% | `tabelas/tab_desempenho_seco.csv:14` (`eta_etc_pct`) |
| 235 | E3: Dr máx | 17,4 mm | `tabelas/tab_desempenho_seco.csv:14` (`dr_max_mm`) |
| 236 | E3: θ₁ mínima | 0,193 cm³ cm⁻³ | `tabelas/tab_desempenho_seco.csv:14` (`theta1_min`) |
| 237 | E3: acionamentos | 62 | `tabelas/tab_desempenho_seco.csv:14` (`acionamentos`) |
| 238 | E3: lâmina média por acionamento | 3,9 mm | `tabelas/tab_desempenho_seco.csv:14` (`lamina_media_mm`) |
| 239 | E3: dias com reservatório vazio | 4 | `tabelas/tab_desempenho_seco.csv:14` (`dias_reservatorio_vazio`) |

## 6. Capacidade mínima do reservatório (TSE ≥ 90%)

Varredura de 250 a 2.000 L, passo de 250 L. Quando nenhuma capacidade atende, TSE e ETa/ETc são os de 2.000 L.

| Nº | Descrição | Valor | Fonte |
|---:|---|---:|---|
| 240 | Chuvoso, reposição a cada 3 d, E1: capacidade mínima | 250 L | `tabelas/tab_capacidade_minima.csv:6` (`capacidade_minima_texto`) |
| 241 | Chuvoso, reposição a cada 3 d, E1: TSE obtido | 98,9% | `tabelas/tab_capacidade_minima.csv:6` (`tse_pct`) |
| 242 | Chuvoso, reposição a cada 3 d, E1: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:6` (`eta_etc_pct`) |
| 243 | Chuvoso, reposição a cada 3 d, E2: capacidade mínima | 250 L | `tabelas/tab_capacidade_minima.csv:7` (`capacidade_minima_texto`) |
| 244 | Chuvoso, reposição a cada 3 d, E2: TSE obtido | 98,9% | `tabelas/tab_capacidade_minima.csv:7` (`tse_pct`) |
| 245 | Chuvoso, reposição a cada 3 d, E2: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:7` (`eta_etc_pct`) |
| 246 | Chuvoso, reposição a cada 3 d, E3: capacidade mínima | 250 L | `tabelas/tab_capacidade_minima.csv:8` (`capacidade_minima_texto`) |
| 247 | Chuvoso, reposição a cada 3 d, E3: TSE obtido | 98,9% | `tabelas/tab_capacidade_minima.csv:8` (`tse_pct`) |
| 248 | Chuvoso, reposição a cada 3 d, E3: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:8` (`eta_etc_pct`) |
| 249 | Chuvoso, reposição a cada 7 d, E1: capacidade mínima | 250 L | `tabelas/tab_capacidade_minima.csv:9` (`capacidade_minima_texto`) |
| 250 | Chuvoso, reposição a cada 7 d, E1: TSE obtido | 98,9% | `tabelas/tab_capacidade_minima.csv:9` (`tse_pct`) |
| 251 | Chuvoso, reposição a cada 7 d, E1: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:9` (`eta_etc_pct`) |
| 252 | Chuvoso, reposição a cada 7 d, E2: capacidade mínima | 250 L | `tabelas/tab_capacidade_minima.csv:10` (`capacidade_minima_texto`) |
| 253 | Chuvoso, reposição a cada 7 d, E2: TSE obtido | 98,9% | `tabelas/tab_capacidade_minima.csv:10` (`tse_pct`) |
| 254 | Chuvoso, reposição a cada 7 d, E2: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:10` (`eta_etc_pct`) |
| 255 | Chuvoso, reposição a cada 7 d, E3: capacidade mínima | 250 L | `tabelas/tab_capacidade_minima.csv:11` (`capacidade_minima_texto`) |
| 256 | Chuvoso, reposição a cada 7 d, E3: TSE obtido | 97,1% | `tabelas/tab_capacidade_minima.csv:11` (`tse_pct`) |
| 257 | Chuvoso, reposição a cada 7 d, E3: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:11` (`eta_etc_pct`) |
| 258 | Chuvoso, reposição a cada 14 d, E1: capacidade mínima | 500 L | `tabelas/tab_capacidade_minima.csv:12` (`capacidade_minima_texto`) |
| 259 | Chuvoso, reposição a cada 14 d, E1: TSE obtido | 98,5% | `tabelas/tab_capacidade_minima.csv:12` (`tse_pct`) |
| 260 | Chuvoso, reposição a cada 14 d, E1: ETa/ETc obtida | 99,9% | `tabelas/tab_capacidade_minima.csv:12` (`eta_etc_pct`) |
| 261 | Chuvoso, reposição a cada 14 d, E2: capacidade mínima | 500 L | `tabelas/tab_capacidade_minima.csv:13` (`capacidade_minima_texto`) |
| 262 | Chuvoso, reposição a cada 14 d, E2: TSE obtido | 98,9% | `tabelas/tab_capacidade_minima.csv:13` (`tse_pct`) |
| 263 | Chuvoso, reposição a cada 14 d, E2: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:13` (`eta_etc_pct`) |
| 264 | Chuvoso, reposição a cada 14 d, E3: capacidade mínima | 500 L | `tabelas/tab_capacidade_minima.csv:14` (`capacidade_minima_texto`) |
| 265 | Chuvoso, reposição a cada 14 d, E3: TSE obtido | 94,4% | `tabelas/tab_capacidade_minima.csv:14` (`tse_pct`) |
| 266 | Chuvoso, reposição a cada 14 d, E3: ETa/ETc obtida | 99,9% | `tabelas/tab_capacidade_minima.csv:14` (`eta_etc_pct`) |
| 267 | Seco, reposição a cada 3 d, E1: capacidade mínima | 250 L | `tabelas/tab_capacidade_minima.csv:15` (`capacidade_minima_texto`) |
| 268 | Seco, reposição a cada 3 d, E1: TSE obtido | 98,1% | `tabelas/tab_capacidade_minima.csv:15` (`tse_pct`) |
| 269 | Seco, reposição a cada 3 d, E1: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:15` (`eta_etc_pct`) |
| 270 | Seco, reposição a cada 3 d, E2: capacidade mínima | 250 L | `tabelas/tab_capacidade_minima.csv:16` (`capacidade_minima_texto`) |
| 271 | Seco, reposição a cada 3 d, E2: TSE obtido | 98,0% | `tabelas/tab_capacidade_minima.csv:16` (`tse_pct`) |
| 272 | Seco, reposição a cada 3 d, E2: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:16` (`eta_etc_pct`) |
| 273 | Seco, reposição a cada 3 d, E3: capacidade mínima | 250 L | `tabelas/tab_capacidade_minima.csv:17` (`capacidade_minima_texto`) |
| 274 | Seco, reposição a cada 3 d, E3: TSE obtido | 98,0% | `tabelas/tab_capacidade_minima.csv:17` (`tse_pct`) |
| 275 | Seco, reposição a cada 3 d, E3: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:17` (`eta_etc_pct`) |
| 276 | Seco, reposição a cada 7 d, E1: capacidade mínima | 500 L | `tabelas/tab_capacidade_minima.csv:18` (`capacidade_minima_texto`) |
| 277 | Seco, reposição a cada 7 d, E1: TSE obtido | 98,1% | `tabelas/tab_capacidade_minima.csv:18` (`tse_pct`) |
| 278 | Seco, reposição a cada 7 d, E1: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:18` (`eta_etc_pct`) |
| 279 | Seco, reposição a cada 7 d, E2: capacidade mínima | 500 L | `tabelas/tab_capacidade_minima.csv:19` (`capacidade_minima_texto`) |
| 280 | Seco, reposição a cada 7 d, E2: TSE obtido | 98,0% | `tabelas/tab_capacidade_minima.csv:19` (`tse_pct`) |
| 281 | Seco, reposição a cada 7 d, E2: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:19` (`eta_etc_pct`) |
| 282 | Seco, reposição a cada 7 d, E3: capacidade mínima | 500 L | `tabelas/tab_capacidade_minima.csv:20` (`capacidade_minima_texto`) |
| 283 | Seco, reposição a cada 7 d, E3: TSE obtido | 97,9% | `tabelas/tab_capacidade_minima.csv:20` (`tse_pct`) |
| 284 | Seco, reposição a cada 7 d, E3: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:20` (`eta_etc_pct`) |
| 285 | Seco, reposição a cada 14 d, E1: capacidade mínima | 750 L | `tabelas/tab_capacidade_minima.csv:21` (`capacidade_minima_texto`) |
| 286 | Seco, reposição a cada 14 d, E1: TSE obtido | 98,1% | `tabelas/tab_capacidade_minima.csv:21` (`tse_pct`) |
| 287 | Seco, reposição a cada 14 d, E1: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:21` (`eta_etc_pct`) |
| 288 | Seco, reposição a cada 14 d, E2: capacidade mínima | 750 L | `tabelas/tab_capacidade_minima.csv:22` (`capacidade_minima_texto`) |
| 289 | Seco, reposição a cada 14 d, E2: TSE obtido | 98,0% | `tabelas/tab_capacidade_minima.csv:22` (`tse_pct`) |
| 290 | Seco, reposição a cada 14 d, E2: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:22` (`eta_etc_pct`) |
| 291 | Seco, reposição a cada 14 d, E3: capacidade mínima | 750 L | `tabelas/tab_capacidade_minima.csv:23` (`capacidade_minima_texto`) |
| 292 | Seco, reposição a cada 14 d, E3: TSE obtido | 97,1% | `tabelas/tab_capacidade_minima.csv:23` (`tse_pct`) |
| 293 | Seco, reposição a cada 14 d, E3: ETa/ETc obtida | 100,0% | `tabelas/tab_capacidade_minima.csv:23` (`eta_etc_pct`) |

## 7. Comparação v1 × v2

| Nº | Descrição | Valor | Fonte |
|---:|---|---:|---|
| 294 | Chuvoso, abundante, E1: conforto v1 (% dias) | 72,9% | `tabelas/tab_comparacao_v1_v2.csv:6` (`conforto_v1_pct`) |
| 295 | Chuvoso, abundante, E1: TSE v2 (% horas) | 98,9% | `tabelas/tab_comparacao_v1_v2.csv:6` (`tse_v2_pct`) |
| 296 | Chuvoso, abundante, E1: TSE diário v2 (% dias) | 74,3% | `tabelas/tab_comparacao_v1_v2.csv:6` (`tse_diaria_v2_pct`) |
| 297 | Chuvoso, abundante, E1: aplicada v1 | 190,0 mm | `tabelas/tab_comparacao_v1_v2.csv:6` (`aplicada_v1_mm`) |
| 298 | Chuvoso, abundante, E1: aplicada v2 | 180,0 mm | `tabelas/tab_comparacao_v1_v2.csv:6` (`aplicada_v2_mm`) |
| 299 | Chuvoso, abundante, E1: percolação incremental v1 | 80,6 mm | `tabelas/tab_comparacao_v1_v2.csv:6` (`percolacao_incremental_v1_mm`) |
| 300 | Chuvoso, abundante, E1: percolação incremental v2 | 103,4 mm | `tabelas/tab_comparacao_v1_v2.csv:6` (`percolacao_incremental_v2_mm`) |
| 301 | Chuvoso, abundante, E2: conforto v1 (% dias) | 97,1% | `tabelas/tab_comparacao_v1_v2.csv:7` (`conforto_v1_pct`) |
| 302 | Chuvoso, abundante, E2: TSE v2 (% horas) | 98,9% | `tabelas/tab_comparacao_v1_v2.csv:7` (`tse_v2_pct`) |
| 303 | Chuvoso, abundante, E2: TSE diário v2 (% dias) | 72,9% | `tabelas/tab_comparacao_v1_v2.csv:7` (`tse_diaria_v2_pct`) |
| 304 | Chuvoso, abundante, E2: aplicada v1 | 196,9 mm | `tabelas/tab_comparacao_v1_v2.csv:7` (`aplicada_v1_mm`) |
| 305 | Chuvoso, abundante, E2: aplicada v2 | 164,0 mm | `tabelas/tab_comparacao_v1_v2.csv:7` (`aplicada_v2_mm`) |
| 306 | Chuvoso, abundante, E2: percolação incremental v1 | 86,5 mm | `tabelas/tab_comparacao_v1_v2.csv:7` (`percolacao_incremental_v1_mm`) |
| 307 | Chuvoso, abundante, E2: percolação incremental v2 | 88,0 mm | `tabelas/tab_comparacao_v1_v2.csv:7` (`percolacao_incremental_v2_mm`) |
| 308 | Chuvoso, abundante, E3: conforto v1 (% dias) | 97,1% | `tabelas/tab_comparacao_v1_v2.csv:8` (`conforto_v1_pct`) |
| 309 | Chuvoso, abundante, E3: TSE v2 (% horas) | 98,9% | `tabelas/tab_comparacao_v1_v2.csv:8` (`tse_v2_pct`) |
| 310 | Chuvoso, abundante, E3: TSE diário v2 (% dias) | 72,9% | `tabelas/tab_comparacao_v1_v2.csv:8` (`tse_diaria_v2_pct`) |
| 311 | Chuvoso, abundante, E3: aplicada v1 | 196,9 mm | `tabelas/tab_comparacao_v1_v2.csv:8` (`aplicada_v1_mm`) |
| 312 | Chuvoso, abundante, E3: aplicada v2 | 164,0 mm | `tabelas/tab_comparacao_v1_v2.csv:8` (`aplicada_v2_mm`) |
| 313 | Chuvoso, abundante, E3: percolação incremental v1 | 86,5 mm | `tabelas/tab_comparacao_v1_v2.csv:8` (`percolacao_incremental_v1_mm`) |
| 314 | Chuvoso, abundante, E3: percolação incremental v2 | 88,0 mm | `tabelas/tab_comparacao_v1_v2.csv:8` (`percolacao_incremental_v2_mm`) |
| 315 | Chuvoso, moderado, E1: conforto v1 (% dias) | 72,9% | `tabelas/tab_comparacao_v1_v2.csv:9` (`conforto_v1_pct`) |
| 316 | Chuvoso, moderado, E1: TSE v2 (% horas) | 98,9% | `tabelas/tab_comparacao_v1_v2.csv:9` (`tse_v2_pct`) |
| 317 | Chuvoso, moderado, E1: TSE diário v2 (% dias) | 74,3% | `tabelas/tab_comparacao_v1_v2.csv:9` (`tse_diaria_v2_pct`) |
| 318 | Chuvoso, moderado, E1: aplicada v1 | 190,0 mm | `tabelas/tab_comparacao_v1_v2.csv:9` (`aplicada_v1_mm`) |
| 319 | Chuvoso, moderado, E1: aplicada v2 | 180,0 mm | `tabelas/tab_comparacao_v1_v2.csv:9` (`aplicada_v2_mm`) |
| 320 | Chuvoso, moderado, E1: percolação incremental v1 | 80,6 mm | `tabelas/tab_comparacao_v1_v2.csv:9` (`percolacao_incremental_v1_mm`) |
| 321 | Chuvoso, moderado, E1: percolação incremental v2 | 103,4 mm | `tabelas/tab_comparacao_v1_v2.csv:9` (`percolacao_incremental_v2_mm`) |
| 322 | Chuvoso, moderado, E2: conforto v1 (% dias) | 97,1% | `tabelas/tab_comparacao_v1_v2.csv:10` (`conforto_v1_pct`) |
| 323 | Chuvoso, moderado, E2: TSE v2 (% horas) | 98,9% | `tabelas/tab_comparacao_v1_v2.csv:10` (`tse_v2_pct`) |
| 324 | Chuvoso, moderado, E2: TSE diário v2 (% dias) | 72,9% | `tabelas/tab_comparacao_v1_v2.csv:10` (`tse_diaria_v2_pct`) |
| 325 | Chuvoso, moderado, E2: aplicada v1 | 196,9 mm | `tabelas/tab_comparacao_v1_v2.csv:10` (`aplicada_v1_mm`) |
| 326 | Chuvoso, moderado, E2: aplicada v2 | 164,0 mm | `tabelas/tab_comparacao_v1_v2.csv:10` (`aplicada_v2_mm`) |
| 327 | Chuvoso, moderado, E2: percolação incremental v1 | 86,5 mm | `tabelas/tab_comparacao_v1_v2.csv:10` (`percolacao_incremental_v1_mm`) |
| 328 | Chuvoso, moderado, E2: percolação incremental v2 | 88,0 mm | `tabelas/tab_comparacao_v1_v2.csv:10` (`percolacao_incremental_v2_mm`) |
| 329 | Chuvoso, moderado, E3: conforto v1 (% dias) | 98,6% | `tabelas/tab_comparacao_v1_v2.csv:11` (`conforto_v1_pct`) |
| 330 | Chuvoso, moderado, E3: TSE v2 (% horas) | 98,9% | `tabelas/tab_comparacao_v1_v2.csv:11` (`tse_v2_pct`) |
| 331 | Chuvoso, moderado, E3: TSE diário v2 (% dias) | 72,9% | `tabelas/tab_comparacao_v1_v2.csv:11` (`tse_diaria_v2_pct`) |
| 332 | Chuvoso, moderado, E3: aplicada v1 | 195,7 mm | `tabelas/tab_comparacao_v1_v2.csv:11` (`aplicada_v1_mm`) |
| 333 | Chuvoso, moderado, E3: aplicada v2 | 158,9 mm | `tabelas/tab_comparacao_v1_v2.csv:11` (`aplicada_v2_mm`) |
| 334 | Chuvoso, moderado, E3: percolação incremental v1 | 85,3 mm | `tabelas/tab_comparacao_v1_v2.csv:11` (`percolacao_incremental_v1_mm`) |
| 335 | Chuvoso, moderado, E3: percolação incremental v2 | 82,9 mm | `tabelas/tab_comparacao_v1_v2.csv:11` (`percolacao_incremental_v2_mm`) |
| 336 | Chuvoso, restrito, E1: conforto v1 (% dias) | 71,4% | `tabelas/tab_comparacao_v1_v2.csv:12` (`conforto_v1_pct`) |
| 337 | Chuvoso, restrito, E1: TSE v2 (% horas) | 98,5% | `tabelas/tab_comparacao_v1_v2.csv:12` (`tse_v2_pct`) |
| 338 | Chuvoso, restrito, E1: TSE diário v2 (% dias) | 74,3% | `tabelas/tab_comparacao_v1_v2.csv:12` (`tse_diaria_v2_pct`) |
| 339 | Chuvoso, restrito, E1: aplicada v1 | 190,0 mm | `tabelas/tab_comparacao_v1_v2.csv:12` (`aplicada_v1_mm`) |
| 340 | Chuvoso, restrito, E1: aplicada v2 | 170,0 mm | `tabelas/tab_comparacao_v1_v2.csv:12` (`aplicada_v2_mm`) |
| 341 | Chuvoso, restrito, E1: percolação incremental v1 | 80,6 mm | `tabelas/tab_comparacao_v1_v2.csv:12` (`percolacao_incremental_v1_mm`) |
| 342 | Chuvoso, restrito, E1: percolação incremental v2 | 93,7 mm | `tabelas/tab_comparacao_v1_v2.csv:12` (`percolacao_incremental_v2_mm`) |
| 343 | Chuvoso, restrito, E2: conforto v1 (% dias) | 91,4% | `tabelas/tab_comparacao_v1_v2.csv:13` (`conforto_v1_pct`) |
| 344 | Chuvoso, restrito, E2: TSE v2 (% horas) | 98,9% | `tabelas/tab_comparacao_v1_v2.csv:13` (`tse_v2_pct`) |
| 345 | Chuvoso, restrito, E2: TSE diário v2 (% dias) | 72,9% | `tabelas/tab_comparacao_v1_v2.csv:13` (`tse_diaria_v2_pct`) |
| 346 | Chuvoso, restrito, E2: aplicada v1 | 185,0 mm | `tabelas/tab_comparacao_v1_v2.csv:13` (`aplicada_v1_mm`) |
| 347 | Chuvoso, restrito, E2: aplicada v2 | 162,0 mm | `tabelas/tab_comparacao_v1_v2.csv:13` (`aplicada_v2_mm`) |
| 348 | Chuvoso, restrito, E2: percolação incremental v1 | 74,7 mm | `tabelas/tab_comparacao_v1_v2.csv:13` (`percolacao_incremental_v1_mm`) |
| 349 | Chuvoso, restrito, E2: percolação incremental v2 | 86,1 mm | `tabelas/tab_comparacao_v1_v2.csv:13` (`percolacao_incremental_v2_mm`) |
| 350 | Chuvoso, restrito, E3: conforto v1 (% dias) | 74,3% | `tabelas/tab_comparacao_v1_v2.csv:14` (`conforto_v1_pct`) |
| 351 | Chuvoso, restrito, E3: TSE v2 (% horas) | 94,4% | `tabelas/tab_comparacao_v1_v2.csv:14` (`tse_v2_pct`) |
| 352 | Chuvoso, restrito, E3: TSE diário v2 (% dias) | 67,1% | `tabelas/tab_comparacao_v1_v2.csv:14` (`tse_diaria_v2_pct`) |
| 353 | Chuvoso, restrito, E3: aplicada v1 | 175,9 mm | `tabelas/tab_comparacao_v1_v2.csv:14` (`aplicada_v1_mm`) |
| 354 | Chuvoso, restrito, E3: aplicada v2 | 139,9 mm | `tabelas/tab_comparacao_v1_v2.csv:14` (`aplicada_v2_mm`) |
| 355 | Chuvoso, restrito, E3: percolação incremental v1 | 65,5 mm | `tabelas/tab_comparacao_v1_v2.csv:14` (`percolacao_incremental_v1_mm`) |
| 356 | Chuvoso, restrito, E3: percolação incremental v2 | 64,1 mm | `tabelas/tab_comparacao_v1_v2.csv:14` (`percolacao_incremental_v2_mm`) |
| 357 | Seco, abundante, E1: conforto v1 (% dias) | 50,0% | `tabelas/tab_comparacao_v1_v2.csv:15` (`conforto_v1_pct`) |
| 358 | Seco, abundante, E1: TSE v2 (% horas) | 98,1% | `tabelas/tab_comparacao_v1_v2.csv:15` (`tse_v2_pct`) |
| 359 | Seco, abundante, E1: TSE diário v2 (% dias) | 54,3% | `tabelas/tab_comparacao_v1_v2.csv:15` (`tse_diaria_v2_pct`) |
| 360 | Seco, abundante, E1: aplicada v1 | 350,0 mm | `tabelas/tab_comparacao_v1_v2.csv:15` (`aplicada_v1_mm`) |
| 361 | Seco, abundante, E1: aplicada v2 | 320,0 mm | `tabelas/tab_comparacao_v1_v2.csv:15` (`aplicada_v2_mm`) |
| 362 | Seco, abundante, E1: percolação incremental v1 | 18,3 mm | `tabelas/tab_comparacao_v1_v2.csv:15` (`percolacao_incremental_v1_mm`) |
| 363 | Seco, abundante, E1: percolação incremental v2 | 52,7 mm | `tabelas/tab_comparacao_v1_v2.csv:15` (`percolacao_incremental_v2_mm`) |
| 364 | Seco, abundante, E2: conforto v1 (% dias) | 100,0% | `tabelas/tab_comparacao_v1_v2.csv:16` (`conforto_v1_pct`) |
| 365 | Seco, abundante, E2: TSE v2 (% horas) | 98,0% | `tabelas/tab_comparacao_v1_v2.csv:16` (`tse_v2_pct`) |
| 366 | Seco, abundante, E2: TSE diário v2 (% dias) | 52,9% | `tabelas/tab_comparacao_v1_v2.csv:16` (`tse_diaria_v2_pct`) |
| 367 | Seco, abundante, E2: aplicada v1 | 363,6 mm | `tabelas/tab_comparacao_v1_v2.csv:16` (`aplicada_v1_mm`) |
| 368 | Seco, abundante, E2: aplicada v2 | 285,1 mm | `tabelas/tab_comparacao_v1_v2.csv:16` (`aplicada_v2_mm`) |
| 369 | Seco, abundante, E2: percolação incremental v1 | 24,9 mm | `tabelas/tab_comparacao_v1_v2.csv:16` (`percolacao_incremental_v1_mm`) |
| 370 | Seco, abundante, E2: percolação incremental v2 | 19,3 mm | `tabelas/tab_comparacao_v1_v2.csv:16` (`percolacao_incremental_v2_mm`) |
| 371 | Seco, abundante, E3: conforto v1 (% dias) | 100,0% | `tabelas/tab_comparacao_v1_v2.csv:17` (`conforto_v1_pct`) |
| 372 | Seco, abundante, E3: TSE v2 (% horas) | 98,0% | `tabelas/tab_comparacao_v1_v2.csv:17` (`tse_v2_pct`) |
| 373 | Seco, abundante, E3: TSE diário v2 (% dias) | 52,9% | `tabelas/tab_comparacao_v1_v2.csv:17` (`tse_diaria_v2_pct`) |
| 374 | Seco, abundante, E3: aplicada v1 | 363,6 mm | `tabelas/tab_comparacao_v1_v2.csv:17` (`aplicada_v1_mm`) |
| 375 | Seco, abundante, E3: aplicada v2 | 285,1 mm | `tabelas/tab_comparacao_v1_v2.csv:17` (`aplicada_v2_mm`) |
| 376 | Seco, abundante, E3: percolação incremental v1 | 24,9 mm | `tabelas/tab_comparacao_v1_v2.csv:17` (`percolacao_incremental_v1_mm`) |
| 377 | Seco, abundante, E3: percolação incremental v2 | 19,3 mm | `tabelas/tab_comparacao_v1_v2.csv:17` (`percolacao_incremental_v2_mm`) |
| 378 | Seco, moderado, E1: conforto v1 (% dias) | 50,0% | `tabelas/tab_comparacao_v1_v2.csv:18` (`conforto_v1_pct`) |
| 379 | Seco, moderado, E1: TSE v2 (% horas) | 98,1% | `tabelas/tab_comparacao_v1_v2.csv:18` (`tse_v2_pct`) |
| 380 | Seco, moderado, E1: TSE diário v2 (% dias) | 54,3% | `tabelas/tab_comparacao_v1_v2.csv:18` (`tse_diaria_v2_pct`) |
| 381 | Seco, moderado, E1: aplicada v1 | 350,0 mm | `tabelas/tab_comparacao_v1_v2.csv:18` (`aplicada_v1_mm`) |
| 382 | Seco, moderado, E1: aplicada v2 | 320,0 mm | `tabelas/tab_comparacao_v1_v2.csv:18` (`aplicada_v2_mm`) |
| 383 | Seco, moderado, E1: percolação incremental v1 | 18,3 mm | `tabelas/tab_comparacao_v1_v2.csv:18` (`percolacao_incremental_v1_mm`) |
| 384 | Seco, moderado, E1: percolação incremental v2 | 52,7 mm | `tabelas/tab_comparacao_v1_v2.csv:18` (`percolacao_incremental_v2_mm`) |
| 385 | Seco, moderado, E2: conforto v1 (% dias) | 100,0% | `tabelas/tab_comparacao_v1_v2.csv:19` (`conforto_v1_pct`) |
| 386 | Seco, moderado, E2: TSE v2 (% horas) | 98,0% | `tabelas/tab_comparacao_v1_v2.csv:19` (`tse_v2_pct`) |
| 387 | Seco, moderado, E2: TSE diário v2 (% dias) | 52,9% | `tabelas/tab_comparacao_v1_v2.csv:19` (`tse_diaria_v2_pct`) |
| 388 | Seco, moderado, E2: aplicada v1 | 363,4 mm | `tabelas/tab_comparacao_v1_v2.csv:19` (`aplicada_v1_mm`) |
| 389 | Seco, moderado, E2: aplicada v2 | 285,1 mm | `tabelas/tab_comparacao_v1_v2.csv:19` (`aplicada_v2_mm`) |
| 390 | Seco, moderado, E2: percolação incremental v1 | 24,8 mm | `tabelas/tab_comparacao_v1_v2.csv:19` (`percolacao_incremental_v1_mm`) |
| 391 | Seco, moderado, E2: percolação incremental v2 | 19,3 mm | `tabelas/tab_comparacao_v1_v2.csv:19` (`percolacao_incremental_v2_mm`) |
| 392 | Seco, moderado, E3: conforto v1 (% dias) | 95,7% | `tabelas/tab_comparacao_v1_v2.csv:20` (`conforto_v1_pct`) |
| 393 | Seco, moderado, E3: TSE v2 (% horas) | 97,9% | `tabelas/tab_comparacao_v1_v2.csv:20` (`tse_v2_pct`) |
| 394 | Seco, moderado, E3: TSE diário v2 (% dias) | 48,6% | `tabelas/tab_comparacao_v1_v2.csv:20` (`tse_diaria_v2_pct`) |
| 395 | Seco, moderado, E3: aplicada v1 | 360,3 mm | `tabelas/tab_comparacao_v1_v2.csv:20` (`aplicada_v1_mm`) |
| 396 | Seco, moderado, E3: aplicada v2 | 297,9 mm | `tabelas/tab_comparacao_v1_v2.csv:20` (`aplicada_v2_mm`) |
| 397 | Seco, moderado, E3: percolação incremental v1 | 21,6 mm | `tabelas/tab_comparacao_v1_v2.csv:20` (`percolacao_incremental_v1_mm`) |
| 398 | Seco, moderado, E3: percolação incremental v2 | 25,1 mm | `tabelas/tab_comparacao_v1_v2.csv:20` (`percolacao_incremental_v2_mm`) |
| 399 | Seco, restrito, E1: conforto v1 (% dias) | 27,1% | `tabelas/tab_comparacao_v1_v2.csv:21` (`conforto_v1_pct`) |
| 400 | Seco, restrito, E1: TSE v2 (% horas) | 74,3% | `tabelas/tab_comparacao_v1_v2.csv:21` (`tse_v2_pct`) |
| 401 | Seco, restrito, E1: TSE diário v2 (% dias) | 41,4% | `tabelas/tab_comparacao_v1_v2.csv:21` (`tse_diaria_v2_pct`) |
| 402 | Seco, restrito, E1: aplicada v1 | 240,0 mm | `tabelas/tab_comparacao_v1_v2.csv:21` (`aplicada_v1_mm`) |
| 403 | Seco, restrito, E1: aplicada v2 | 250,0 mm | `tabelas/tab_comparacao_v1_v2.csv:21` (`aplicada_v2_mm`) |
| 404 | Seco, restrito, E1: percolação incremental v1 | 24,7 mm | `tabelas/tab_comparacao_v1_v2.csv:21` (`percolacao_incremental_v1_mm`) |
| 405 | Seco, restrito, E1: percolação incremental v2 | 39,4 mm | `tabelas/tab_comparacao_v1_v2.csv:21` (`percolacao_incremental_v2_mm`) |
| 406 | Seco, restrito, E2: conforto v1 (% dias) | 42,9% | `tabelas/tab_comparacao_v1_v2.csv:22` (`conforto_v1_pct`) |
| 407 | Seco, restrito, E2: TSE v2 (% horas) | 79,3% | `tabelas/tab_comparacao_v1_v2.csv:22` (`tse_v2_pct`) |
| 408 | Seco, restrito, E2: TSE diário v2 (% dias) | 44,3% | `tabelas/tab_comparacao_v1_v2.csv:22` (`tse_diaria_v2_pct`) |
| 409 | Seco, restrito, E2: aplicada v1 | 243,2 mm | `tabelas/tab_comparacao_v1_v2.csv:22` (`aplicada_v1_mm`) |
| 410 | Seco, restrito, E2: aplicada v2 | 242,6 mm | `tabelas/tab_comparacao_v1_v2.csv:22` (`aplicada_v2_mm`) |
| 411 | Seco, restrito, E2: percolação incremental v1 | 2,6 mm | `tabelas/tab_comparacao_v1_v2.csv:22` (`percolacao_incremental_v1_mm`) |
| 412 | Seco, restrito, E2: percolação incremental v2 | 19,8 mm | `tabelas/tab_comparacao_v1_v2.csv:22` (`percolacao_incremental_v2_mm`) |
| 413 | Seco, restrito, E3: conforto v1 (% dias) | 25,7% | `tabelas/tab_comparacao_v1_v2.csv:23` (`conforto_v1_pct`) |
| 414 | Seco, restrito, E3: TSE v2 (% horas) | 54,9% | `tabelas/tab_comparacao_v1_v2.csv:23` (`tse_v2_pct`) |
| 415 | Seco, restrito, E3: TSE diário v2 (% dias) | 11,4% | `tabelas/tab_comparacao_v1_v2.csv:23` (`tse_diaria_v2_pct`) |
| 416 | Seco, restrito, E3: aplicada v1 | 241,7 mm | `tabelas/tab_comparacao_v1_v2.csv:23` (`aplicada_v1_mm`) |
| 417 | Seco, restrito, E3: aplicada v2 | 241,6 mm | `tabelas/tab_comparacao_v1_v2.csv:23` (`aplicada_v2_mm`) |
| 418 | Seco, restrito, E3: percolação incremental v1 | 4,1 mm | `tabelas/tab_comparacao_v1_v2.csv:23` (`percolacao_incremental_v1_mm`) |
| 419 | Seco, restrito, E3: percolação incremental v2 | 14,2 mm | `tabelas/tab_comparacao_v1_v2.csv:23` (`percolacao_incremental_v2_mm`) |

## 8. Sensibilidade de z₁ = 300 mm

| Nº | Descrição | Valor | Fonte |
|---:|---|---:|---|
| 420 | Chuvoso, abundante, E1: TSE com z₁ = 300 mm | 99,3% | `tabelas/tab_sensibilidade_z1.csv:7` (`tse_pct_z1_300`) |
| 421 | Chuvoso, abundante, E1: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:7` (`eta_etc_pct_z1_300`) |
| 422 | Chuvoso, abundante, E1: aplicada com z₁ = 300 mm | 120,0 mm | `tabelas/tab_sensibilidade_z1.csv:7` (`aplicada_mm_z1_300`) |
| 423 | Chuvoso, abundante, E1: percolação incremental com z₁ = 300 mm | 64,7 mm | `tabelas/tab_sensibilidade_z1.csv:7` (`percolacao_incremental_mm_z1_300`) |
| 424 | Chuvoso, abundante, E2: TSE com z₁ = 300 mm | 99,5% | `tabelas/tab_sensibilidade_z1.csv:8` (`tse_pct_z1_300`) |
| 425 | Chuvoso, abundante, E2: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:8` (`eta_etc_pct_z1_300`) |
| 426 | Chuvoso, abundante, E2: aplicada com z₁ = 300 mm | 115,6 mm | `tabelas/tab_sensibilidade_z1.csv:8` (`aplicada_mm_z1_300`) |
| 427 | Chuvoso, abundante, E2: percolação incremental com z₁ = 300 mm | 57,4 mm | `tabelas/tab_sensibilidade_z1.csv:8` (`percolacao_incremental_mm_z1_300`) |
| 428 | Chuvoso, abundante, E3: TSE com z₁ = 300 mm | 99,5% | `tabelas/tab_sensibilidade_z1.csv:9` (`tse_pct_z1_300`) |
| 429 | Chuvoso, abundante, E3: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:9` (`eta_etc_pct_z1_300`) |
| 430 | Chuvoso, abundante, E3: aplicada com z₁ = 300 mm | 115,6 mm | `tabelas/tab_sensibilidade_z1.csv:9` (`aplicada_mm_z1_300`) |
| 431 | Chuvoso, abundante, E3: percolação incremental com z₁ = 300 mm | 57,4 mm | `tabelas/tab_sensibilidade_z1.csv:9` (`percolacao_incremental_mm_z1_300`) |
| 432 | Chuvoso, moderado, E1: TSE com z₁ = 300 mm | 99,3% | `tabelas/tab_sensibilidade_z1.csv:10` (`tse_pct_z1_300`) |
| 433 | Chuvoso, moderado, E1: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:10` (`eta_etc_pct_z1_300`) |
| 434 | Chuvoso, moderado, E1: aplicada com z₁ = 300 mm | 120,0 mm | `tabelas/tab_sensibilidade_z1.csv:10` (`aplicada_mm_z1_300`) |
| 435 | Chuvoso, moderado, E1: percolação incremental com z₁ = 300 mm | 64,7 mm | `tabelas/tab_sensibilidade_z1.csv:10` (`percolacao_incremental_mm_z1_300`) |
| 436 | Chuvoso, moderado, E2: TSE com z₁ = 300 mm | 99,5% | `tabelas/tab_sensibilidade_z1.csv:11` (`tse_pct_z1_300`) |
| 437 | Chuvoso, moderado, E2: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:11` (`eta_etc_pct_z1_300`) |
| 438 | Chuvoso, moderado, E2: aplicada com z₁ = 300 mm | 115,6 mm | `tabelas/tab_sensibilidade_z1.csv:11` (`aplicada_mm_z1_300`) |
| 439 | Chuvoso, moderado, E2: percolação incremental com z₁ = 300 mm | 57,4 mm | `tabelas/tab_sensibilidade_z1.csv:11` (`percolacao_incremental_mm_z1_300`) |
| 440 | Chuvoso, moderado, E3: TSE com z₁ = 300 mm | 99,4% | `tabelas/tab_sensibilidade_z1.csv:12` (`tse_pct_z1_300`) |
| 441 | Chuvoso, moderado, E3: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:12` (`eta_etc_pct_z1_300`) |
| 442 | Chuvoso, moderado, E3: aplicada com z₁ = 300 mm | 117,2 mm | `tabelas/tab_sensibilidade_z1.csv:12` (`aplicada_mm_z1_300`) |
| 443 | Chuvoso, moderado, E3: percolação incremental com z₁ = 300 mm | 58,9 mm | `tabelas/tab_sensibilidade_z1.csv:12` (`percolacao_incremental_mm_z1_300`) |
| 444 | Chuvoso, restrito, E1: TSE com z₁ = 300 mm | 99,3% | `tabelas/tab_sensibilidade_z1.csv:13` (`tse_pct_z1_300`) |
| 445 | Chuvoso, restrito, E1: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:13` (`eta_etc_pct_z1_300`) |
| 446 | Chuvoso, restrito, E1: aplicada com z₁ = 300 mm | 120,0 mm | `tabelas/tab_sensibilidade_z1.csv:13` (`aplicada_mm_z1_300`) |
| 447 | Chuvoso, restrito, E1: percolação incremental com z₁ = 300 mm | 64,7 mm | `tabelas/tab_sensibilidade_z1.csv:13` (`percolacao_incremental_mm_z1_300`) |
| 448 | Chuvoso, restrito, E2: TSE com z₁ = 300 mm | 99,5% | `tabelas/tab_sensibilidade_z1.csv:14` (`tse_pct_z1_300`) |
| 449 | Chuvoso, restrito, E2: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:14` (`eta_etc_pct_z1_300`) |
| 450 | Chuvoso, restrito, E2: aplicada com z₁ = 300 mm | 115,6 mm | `tabelas/tab_sensibilidade_z1.csv:14` (`aplicada_mm_z1_300`) |
| 451 | Chuvoso, restrito, E2: percolação incremental com z₁ = 300 mm | 57,4 mm | `tabelas/tab_sensibilidade_z1.csv:14` (`percolacao_incremental_mm_z1_300`) |
| 452 | Chuvoso, restrito, E3: TSE com z₁ = 300 mm | 98,5% | `tabelas/tab_sensibilidade_z1.csv:15` (`tse_pct_z1_300`) |
| 453 | Chuvoso, restrito, E3: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:15` (`eta_etc_pct_z1_300`) |
| 454 | Chuvoso, restrito, E3: aplicada com z₁ = 300 mm | 118,5 mm | `tabelas/tab_sensibilidade_z1.csv:15` (`aplicada_mm_z1_300`) |
| 455 | Chuvoso, restrito, E3: percolação incremental com z₁ = 300 mm | 60,3 mm | `tabelas/tab_sensibilidade_z1.csv:15` (`percolacao_incremental_mm_z1_300`) |
| 456 | Seco, abundante, E1: TSE com z₁ = 300 mm | 98,3% | `tabelas/tab_sensibilidade_z1.csv:16` (`tse_pct_z1_300`) |
| 457 | Seco, abundante, E1: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:16` (`eta_etc_pct_z1_300`) |
| 458 | Seco, abundante, E1: aplicada com z₁ = 300 mm | 280,0 mm | `tabelas/tab_sensibilidade_z1.csv:16` (`aplicada_mm_z1_300`) |
| 459 | Seco, abundante, E1: percolação incremental com z₁ = 300 mm | 25,8 mm | `tabelas/tab_sensibilidade_z1.csv:16` (`percolacao_incremental_mm_z1_300`) |
| 460 | Seco, abundante, E2: TSE com z₁ = 300 mm | 98,7% | `tabelas/tab_sensibilidade_z1.csv:17` (`tse_pct_z1_300`) |
| 461 | Seco, abundante, E2: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:17` (`eta_etc_pct_z1_300`) |
| 462 | Seco, abundante, E2: aplicada com z₁ = 300 mm | 282,9 mm | `tabelas/tab_sensibilidade_z1.csv:17` (`aplicada_mm_z1_300`) |
| 463 | Seco, abundante, E2: percolação incremental com z₁ = 300 mm | 20,2 mm | `tabelas/tab_sensibilidade_z1.csv:17` (`percolacao_incremental_mm_z1_300`) |
| 464 | Seco, abundante, E3: TSE com z₁ = 300 mm | 98,7% | `tabelas/tab_sensibilidade_z1.csv:18` (`tse_pct_z1_300`) |
| 465 | Seco, abundante, E3: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:18` (`eta_etc_pct_z1_300`) |
| 466 | Seco, abundante, E3: aplicada com z₁ = 300 mm | 282,9 mm | `tabelas/tab_sensibilidade_z1.csv:18` (`aplicada_mm_z1_300`) |
| 467 | Seco, abundante, E3: percolação incremental com z₁ = 300 mm | 20,2 mm | `tabelas/tab_sensibilidade_z1.csv:18` (`percolacao_incremental_mm_z1_300`) |
| 468 | Seco, moderado, E1: TSE com z₁ = 300 mm | 98,3% | `tabelas/tab_sensibilidade_z1.csv:19` (`tse_pct_z1_300`) |
| 469 | Seco, moderado, E1: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:19` (`eta_etc_pct_z1_300`) |
| 470 | Seco, moderado, E1: aplicada com z₁ = 300 mm | 280,0 mm | `tabelas/tab_sensibilidade_z1.csv:19` (`aplicada_mm_z1_300`) |
| 471 | Seco, moderado, E1: percolação incremental com z₁ = 300 mm | 25,8 mm | `tabelas/tab_sensibilidade_z1.csv:19` (`percolacao_incremental_mm_z1_300`) |
| 472 | Seco, moderado, E2: TSE com z₁ = 300 mm | 98,7% | `tabelas/tab_sensibilidade_z1.csv:20` (`tse_pct_z1_300`) |
| 473 | Seco, moderado, E2: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:20` (`eta_etc_pct_z1_300`) |
| 474 | Seco, moderado, E2: aplicada com z₁ = 300 mm | 282,9 mm | `tabelas/tab_sensibilidade_z1.csv:20` (`aplicada_mm_z1_300`) |
| 475 | Seco, moderado, E2: percolação incremental com z₁ = 300 mm | 20,2 mm | `tabelas/tab_sensibilidade_z1.csv:20` (`percolacao_incremental_mm_z1_300`) |
| 476 | Seco, moderado, E3: TSE com z₁ = 300 mm | 98,3% | `tabelas/tab_sensibilidade_z1.csv:21` (`tse_pct_z1_300`) |
| 477 | Seco, moderado, E3: ETa/ETc com z₁ = 300 mm | 100,0% | `tabelas/tab_sensibilidade_z1.csv:21` (`eta_etc_pct_z1_300`) |
| 478 | Seco, moderado, E3: aplicada com z₁ = 300 mm | 285,7 mm | `tabelas/tab_sensibilidade_z1.csv:21` (`aplicada_mm_z1_300`) |
| 479 | Seco, moderado, E3: percolação incremental com z₁ = 300 mm | 29,6 mm | `tabelas/tab_sensibilidade_z1.csv:21` (`percolacao_incremental_mm_z1_300`) |
| 480 | Seco, restrito, E1: TSE com z₁ = 300 mm | 80,9% | `tabelas/tab_sensibilidade_z1.csv:22` (`tse_pct_z1_300`) |
| 481 | Seco, restrito, E1: ETa/ETc com z₁ = 300 mm | 93,9% | `tabelas/tab_sensibilidade_z1.csv:22` (`eta_etc_pct_z1_300`) |
| 482 | Seco, restrito, E1: aplicada com z₁ = 300 mm | 240,0 mm | `tabelas/tab_sensibilidade_z1.csv:22` (`aplicada_mm_z1_300`) |
| 483 | Seco, restrito, E1: percolação incremental com z₁ = 300 mm | 19,5 mm | `tabelas/tab_sensibilidade_z1.csv:22` (`percolacao_incremental_mm_z1_300`) |
| 484 | Seco, restrito, E2: TSE com z₁ = 300 mm | 80,8% | `tabelas/tab_sensibilidade_z1.csv:23` (`tse_pct_z1_300`) |
| 485 | Seco, restrito, E2: ETa/ETc com z₁ = 300 mm | 93,0% | `tabelas/tab_sensibilidade_z1.csv:23` (`eta_etc_pct_z1_300`) |
| 486 | Seco, restrito, E2: aplicada com z₁ = 300 mm | 238,1 mm | `tabelas/tab_sensibilidade_z1.csv:23` (`aplicada_mm_z1_300`) |
| 487 | Seco, restrito, E2: percolação incremental com z₁ = 300 mm | 21,9 mm | `tabelas/tab_sensibilidade_z1.csv:23` (`percolacao_incremental_mm_z1_300`) |
| 488 | Seco, restrito, E3: TSE com z₁ = 300 mm | 58,8% | `tabelas/tab_sensibilidade_z1.csv:24` (`tse_pct_z1_300`) |
| 489 | Seco, restrito, E3: ETa/ETc com z₁ = 300 mm | 90,8% | `tabelas/tab_sensibilidade_z1.csv:24` (`eta_etc_pct_z1_300`) |
| 490 | Seco, restrito, E3: aplicada com z₁ = 300 mm | 239,0 mm | `tabelas/tab_sensibilidade_z1.csv:24` (`aplicada_mm_z1_300`) |
| 491 | Seco, restrito, E3: percolação incremental com z₁ = 300 mm | 14,6 mm | `tabelas/tab_sensibilidade_z1.csv:24` (`percolacao_incremental_mm_z1_300`) |

## 9. Diagnósticos (o modelo não aplica)

| Nº | Descrição | Valor | Fonte |
|---:|---|---:|---|
| 492 | Kc,mid ajustado pela eq. 62, chuvoso | 0,956 | `tabelas/tab_diagnosticos.csv:6` (`valor`) |
| 493 | Diferença para o Kc,mid tabelado, chuvoso | -0,044 | `tabelas/tab_diagnosticos.csv:8` (`valor`) |
| 494 | p ajustado mínimo, chuvoso | 0,29 | `tabelas/tab_diagnosticos.csv:18` (`valor`) |
| 495 | p ajustado máximo, chuvoso | 0,46 | `tabelas/tab_diagnosticos.csv:20` (`valor`) |
| 496 | Horas com ET0 negativa zerada, chuvoso | 694 h | `tabelas/tab_diagnosticos.csv:22` (`valor`) |
| 497 | Soma da ET0 negativa zerada, chuvoso | -8,23 mm | `tabelas/tab_diagnosticos.csv:24` (`valor`) |
| 498 | ΣET0 com Ra zerada pelo meio da hora, chuvoso | 278,4 mm | `tabelas/tab_diagnosticos.csv:28` (`valor`) |
| 499 | Kc,mid ajustado pela eq. 62, seco | 1,016 | `tabelas/tab_diagnosticos.csv:7` (`valor`) |
| 500 | Diferença para o Kc,mid tabelado, seco | +0,016 | `tabelas/tab_diagnosticos.csv:9` (`valor`) |
| 501 | p ajustado mínimo, seco | 0,26 | `tabelas/tab_diagnosticos.csv:19` (`valor`) |
| 502 | p ajustado máximo, seco | 0,38 | `tabelas/tab_diagnosticos.csv:21` (`valor`) |
| 503 | Horas com ET0 negativa zerada, seco | 706 h | `tabelas/tab_diagnosticos.csv:23` (`valor`) |
| 504 | Soma da ET0 negativa zerada, seco | -14,16 mm | `tabelas/tab_diagnosticos.csv:25` (`valor`) |
| 505 | ΣET0 com Ra zerada pelo meio da hora, seco | 357,9 mm | `tabelas/tab_diagnosticos.csv:29` (`valor`) |
| 506 | Rs/Rso bruta máxima em 2023 (Ra > 1,5 MJ m⁻² h⁻¹) | 1,109 | `tabelas/tab_diagnosticos.csv:34` (`valor`) |
| 507 | Rs/Rso bruta, percentil 99, em 2023 | 1,021 | `tabelas/tab_diagnosticos.csv:35` (`valor`) |

## 10. Anos vizinhos (completude da A204)

| Nº | Descrição | Valor | Fonte |
|---:|---|---:|---|
| 508 | 2023, janela chuvoso: dias sem registro | 0 | `tabelas/tab_completude_anos.csv:6` (`dias_sem_registro`) |
| 509 | 2023, janela chuvoso: maior lacuna contínua | 0 d | `tabelas/tab_completude_anos.csv:6` (`maior_lacuna_sem_registro_dias`) |
| 510 | 2023, janela seco: dias sem registro | 0 | `tabelas/tab_completude_anos.csv:7` (`dias_sem_registro`) |
| 511 | 2023, janela seco: maior lacuna contínua | 0 d | `tabelas/tab_completude_anos.csv:7` (`maior_lacuna_sem_registro_dias`) |
| 512 | 2024: dias sem registro na janela do ciclo seco (01/07 a 08/09): valor no arquivo | [A CONFIRMAR PELO AUTOR] | `tabelas/tab_afirmacoes_anos_vizinhos.csv:6` (`valor_obtido`) |
| 513 | 2024: dias sem registro na janela do ciclo seco (01/07 a 08/09): confere? | [A CONFIRMAR PELO AUTOR] | `tabelas/tab_afirmacoes_anos_vizinhos.csv:6` (`confere`) |
| 514 | 2024: maior lacuna contínua na janela do ciclo seco (dias): valor no arquivo | [A CONFIRMAR PELO AUTOR] | `tabelas/tab_afirmacoes_anos_vizinhos.csv:7` (`valor_obtido`) |
| 515 | 2024: maior lacuna contínua na janela do ciclo seco (dias): confere? | [A CONFIRMAR PELO AUTOR] | `tabelas/tab_afirmacoes_anos_vizinhos.csv:7` (`confere`) |
| 516 | 2025: sem registros de maio a dezembro: valor no arquivo | [A CONFIRMAR PELO AUTOR] | `tabelas/tab_afirmacoes_anos_vizinhos.csv:8` (`valor_obtido`) |
| 517 | 2025: sem registros de maio a dezembro: confere? | [A CONFIRMAR PELO AUTOR] | `tabelas/tab_afirmacoes_anos_vizinhos.csv:8` (`confere`) |
| 518 | Normal climatológica 1991–2020, precipitação (planilha do INMET) | [A CONFIRMAR PELO AUTOR] | arquivo ausente: https://portal.inmet.gov.br/uploads/normais/Normal-Climatologica-PREC.xlsx → `data/raw/normais/Normal-Climatologica-PREC.xlsx` |
| 519 | Dados horários de 2024, estação A204 (extraídos de 2024.zip) | [A CONFIRMAR PELO AUTOR] | arquivo ausente: https://portal.inmet.gov.br/uploads/dadoshistoricos/2024.zip → `data/raw/downloads/2024.zip` |
| 520 | Dados horários de 2025, estação A204 (extraídos de 2025.zip) | [A CONFIRMAR PELO AUTOR] | arquivo ausente: https://portal.inmet.gov.br/uploads/dadoshistoricos/2025.zip → `data/raw/downloads/2025.zip` |

## 11. Execução

| Nº | Descrição | Valor | Fonte |
|---:|---|---:|---|
| 521 | Tempo de execução do pipeline | 8,9 s | `AMBIENTE.md` |
