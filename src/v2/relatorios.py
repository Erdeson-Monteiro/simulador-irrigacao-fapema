"""
Documentos gerados pelo pipeline do v2: NUMEROS_ARTIGO.md,
RELATORIO.md, AMBIENTE.md, CHECKSUMS.txt e resultados.json.

Regra: nenhum número é digitado. Todo valor citado sai de uma tabela CSV gravada pelo
pipeline (lido de volta pela referência arquivo:linha:coluna) ou do próprio cálculo.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
import hashlib
import json
import os
import platform
import sqlite3
import subprocess
import sys
from importlib import metadata
from typing import Dict, List, Optional, Sequence

from src.v2.dados_externos import FONTE_MEDIA_CHUVA, PESOS_JANELA_MEDIA
from src.v2.formatacao import data_br, inteiro, num, tabela_markdown
from src.v2.inmet import ROOT_DIR
from src.v2.modelo import ESTRATEGIAS, NOMES_ESTRATEGIAS, SEQUEIRO
from src.v2.parametros import CENARIOS


PENDENTE = "[A CONFIRMAR PELO AUTOR]"
CICLOS = ("chuvoso", "seco")
CENARIOS_ORDEM = ("Abundante", "Moderado", "Restrito")
NOME_CICLO = {"chuvoso": "chuvoso", "seco": "seco"}


# ---------------------------------------------------------------------------
# NUMEROS_ARTIGO.md
# ---------------------------------------------------------------------------

@dataclass
class Entrada:
    descricao: str
    valor: str
    fonte: str


@dataclass
class Numeros:
    """Lista de números citáveis; cada valor é formatado a partir do texto gravado no CSV."""
    res: object
    secoes: List[tuple] = field(default_factory=list)

    def secao(self, titulo: str, texto: str = "") -> None:
        self.secoes.append((titulo, texto, []))

    def add(self, descricao: str, tabela: str, chave: str, coluna: str, casas: int = 1,
            sufixo: str = "", tipo: str = "num", sinal: bool = False) -> str:
        t = self.res.tabelas[tabela]
        arquivo, linha, col = t.ref(chave, coluna)
        bruto = t.valor(chave, coluna)
        if bruto == "":
            valor = PENDENTE
        elif tipo == "int":
            valor = inteiro(int(bruto)) + sufixo
        elif tipo == "data":
            valor = data_br(date.fromisoformat(bruto))
        elif tipo == "texto":
            valor = bruto
        else:
            x = float(bruto)
            valor = ("+" if sinal and x > 0 else "") + num(x, casas) + sufixo
        self.secoes[-1][2].append(Entrada(descricao, valor, f"`{arquivo}:{linha}` (`{col}`)"))
        return valor

    def add_livre(self, descricao: str, valor: str, fonte: str) -> None:
        self.secoes[-1][2].append(Entrada(descricao, valor, fonte))

    def markdown(self) -> str:
        partes = [
            "# Números do artigo (modelo v2)",
            "",
            "Gerado por `python3 main.py pipeline`. Cada valor vem do arquivo, da linha física e da coluna "
            "indicados (caminhos relativos a `resultados/v2/`; as linhas contam o cabeçalho `#` de metadados). "
            "Para conferir todos contra os CSVs: `python3 main.py conferir`.",
            "",
        ]
        n = 0
        for titulo, texto, entradas in self.secoes:
            partes += [f"## {titulo}", ""]
            if texto:
                partes += [texto, ""]
            partes += ["| Nº | Descrição | Valor | Fonte |", "|---:|---|---:|---|"]
            for e in entradas:
                n += 1
                partes.append(f"| {n} | {e.descricao} | {e.valor} | {e.fonte} |")
            partes.append("")
        return "\n".join(partes)


def montar_numeros(res, tempo_total_s: float) -> Numeros:
    N = Numeros(res)
    par = res.par

    N.secao("1. Clima dos ciclos, viés PM × HS e média de chuva")
    for c in CICLOS:
        nc = NOME_CICLO[c]
        N.add(f"Chuva no ciclo {nc}", "tab_clima_ciclos", c, "chuva_mm", 1, " mm")
        N.add(f"ΣET0 Penman-Monteith, ciclo {nc}", "tab_clima_ciclos", c, "et0_pm_mm", 1, " mm")
        N.add(f"ET0 Penman-Monteith média, ciclo {nc}", "tab_clima_ciclos", c, "et0_pm_mm_dia", 2, " mm/d")
        N.add(f"ΣET0 Hargreaves-Samani (dias locais), ciclo {nc}", "tab_clima_ciclos", c, "et0_hs_mm", 1, " mm")
        N.add(f"Viés HS em relação a PM, ciclo {nc}", "tab_clima_ciclos", c, "vies_hs_pct", 1, "%", sinal=True)
        N.add(f"ΣETc potencial (curva de Kc), ciclo {nc}", "tab_clima_ciclos", c, "etc_mm", 1, " mm")
        N.add(f"T média do ar, ciclo {nc}", "tab_clima_ciclos", c, "t_media_c", 1, " °C")
        N.add(f"u₂ médio, ciclo {nc}", "tab_clima_ciclos", c, "u2_medio_ms", 2, " m/s")
        N.add(f"Dias com chuva, ciclo {nc}", "tab_clima_ciclos", c, "dias_com_chuva", tipo="int")
        N.add(f"Maior chuva diária (dia local), ciclo {nc}", "tab_clima_ciclos", c, "maior_chuva_diaria_mm", 1, " mm")
        N.add(f"Data da maior chuva diária, ciclo {nc}", "tab_clima_ciclos", c, "data_maior_chuva_diaria", tipo="data")
        N.add(f"Maior chuva horária, ciclo {nc}", "tab_clima_ciclos", c, "maior_chuva_horaria_mm", 1, " mm")
        N.add(f"Média 1991–2021 da janela (Corrêa, Carvalho e Mendes, 2023), ciclo {nc}", "tab_normal_climatologica", c,
              "media_janela_mm", 1, " mm")
        N.add(f"Chuva de 2023 em % da média 1991–2021, ciclo {nc}", "tab_normal_climatologica", c,
              "chuva_sobre_media_pct", 1, "%")

    N.secao("2. Parâmetros e cenários")
    N.add("TAW (z₁ = 200 mm)", "tab_parametros", "taw", "valor", 1, " mm")
    N.add("RAW (z₁ = 200 mm)", "tab_parametros", "raw", "valor", 1, " mm")
    N.add("θlim", "tab_parametros", "theta_lim", "valor", 3, " cm³ cm⁻³")
    N.add("Fases do Kc (dias)", "tab_parametros", "fases", "valor", tipo="texto")
    for cen in CENARIOS_ORDEM:
        N.add(f"Oferta máxima, cenário {cen.lower()}", "tab_cenarios", cen, "oferta_maxima_mm_dia", 1, " mm/d")
        N.add(f"Oferta no ciclo, cenário {cen.lower()}", "tab_cenarios", cen, "oferta_no_ciclo_mm", 1, " mm")

    for c in CICLOS:
        N.secao(f"3. Desempenho, ciclo {NOME_CICLO[c]}")
        tab = f"tab_desempenho_{c}"
        for cen in CENARIOS_ORDEM:
            for e in ESTRATEGIAS:
                k, rot = f"{cen}|{e}", f"{e}, {cen.lower()}"
                N.add(f"{rot}: aplicada", tab, k, "aplicada_mm", 1, " mm")
                N.add(f"{rot}: acionamentos", tab, k, "acionamentos", tipo="int")
                N.add(f"{rot}: percolação incremental", tab, k, "percolacao_incremental_mm", 1, " mm")
                N.add(f"{rot}: eficiência incremental", tab, k, "eficiencia_incremental_pct", 1, "%")
                N.add(f"{rot}: TSE", tab, k, "tse_pct", 1, "%")
                N.add(f"{rot}: ETa/ETc", tab, k, "eta_etc_pct", 1, "%")
                N.add(f"{rot}: Dr máx", tab, k, "dr_max_mm", 1, " mm")
                N.add(f"{rot}: dias com reservatório vazio", tab, k, "dias_reservatorio_vazio", tipo="int")
        N.add("Sequeiro: percolação total", tab, SEQUEIRO, "percolacao_mm", 1, " mm")
        N.add("Sequeiro: TSE", tab, SEQUEIRO, "tse_pct", 1, "%")
        N.add("Sequeiro: ETa/ETc", tab, SEQUEIRO, "eta_etc_pct", 1, "%")
        N.add("Sequeiro: Dr máx", tab, SEQUEIRO, "dr_max_mm", 1, " mm")

    N.secao("4. Sensibilidade de E1 à lâmina (cenário abundante; Figura 1)")
    for c in CICLOS:
        for L in res.sens_e1_laminas:
            k = f"{c}|{L:g}"
            N.add(f"E1, L = {num(L, 0)} mm, {NOME_CICLO[c]}: TSE", "tab_sensibilidade_e1", k, "tse_pct", 1, "%")
            N.add(f"E1, L = {num(L, 0)} mm, {NOME_CICLO[c]}: percolação incremental", "tab_sensibilidade_e1", k,
                  "percolacao_incremental_mm", 1, " mm")
        N.add(f"E2 (referência), {NOME_CICLO[c]}: TSE", "tab_sensibilidade_e1", f"{c}|E2", "tse_pct", 1, "%")
        N.add(f"E2 (referência), {NOME_CICLO[c]}: percolação incremental", "tab_sensibilidade_e1", f"{c}|E2",
              "percolacao_incremental_mm", 1, " mm")

    N.secao("5. Ciclo seco, cenário restrito (Figura 2)")
    for e in ESTRATEGIAS:
        k = f"Restrito|{e}"
        N.add(f"{e}: TSE", "tab_desempenho_seco", k, "tse_pct", 1, "%")
        N.add(f"{e}: ETa/ETc", "tab_desempenho_seco", k, "eta_etc_pct", 1, "%")
        N.add(f"{e}: Dr máx", "tab_desempenho_seco", k, "dr_max_mm", 1, " mm")
        N.add(f"{e}: θ₁ mínima", "tab_desempenho_seco", k, "theta1_min", 3, " cm³ cm⁻³")
        N.add(f"{e}: acionamentos", "tab_desempenho_seco", k, "acionamentos", tipo="int")
        N.add(f"{e}: lâmina média por acionamento", "tab_desempenho_seco", k, "lamina_media_mm", 1, " mm")
        N.add(f"{e}: dias com reservatório vazio", "tab_desempenho_seco", k, "dias_reservatorio_vazio", tipo="int")

    N.secao("6. Capacidade mínima do reservatório (TSE ≥ 90%)",
            "Varredura de 250 a 2.000 L, passo de 250 L. Quando nenhuma capacidade atende, TSE e ETa/ETc são os de 2.000 L.")
    for c in CICLOS:
        for n in res.intervalos:
            for e in ESTRATEGIAS:
                k, rot = f"{c}|{n}|{e}", f"{NOME_CICLO[c].capitalize()}, reposição a cada {n} d, {e}"
                N.add(f"{rot}: capacidade mínima", "tab_capacidade_minima", k, "capacidade_minima_texto", tipo="texto")
                N.add(f"{rot}: TSE obtido", "tab_capacidade_minima", k, "tse_pct", 1, "%")
                N.add(f"{rot}: ETa/ETc obtida", "tab_capacidade_minima", k, "eta_etc_pct", 1, "%")

    N.secao("7. Comparação v1 × v2")
    for c in CICLOS:
        for cen in CENARIOS_ORDEM:
            for e in ESTRATEGIAS:
                k, rot = f"{c}|{cen}|{e}", f"{NOME_CICLO[c].capitalize()}, {cen.lower()}, {e}"
                N.add(f"{rot}: conforto v1 (% dias)", "tab_comparacao_v1_v2", k, "conforto_v1_pct", 1, "%")
                N.add(f"{rot}: TSE v2 (% horas)", "tab_comparacao_v1_v2", k, "tse_v2_pct", 1, "%")
                N.add(f"{rot}: TSE diário v2 (% dias)", "tab_comparacao_v1_v2", k, "tse_diaria_v2_pct", 1, "%")
                N.add(f"{rot}: aplicada v1", "tab_comparacao_v1_v2", k, "aplicada_v1_mm", 1, " mm")
                N.add(f"{rot}: aplicada v2", "tab_comparacao_v1_v2", k, "aplicada_v2_mm", 1, " mm")
                N.add(f"{rot}: percolação incremental v1", "tab_comparacao_v1_v2", k, "percolacao_incremental_v1_mm", 1, " mm")
                N.add(f"{rot}: percolação incremental v2", "tab_comparacao_v1_v2", k, "percolacao_incremental_v2_mm", 1, " mm")

    N.secao("8. Sensibilidade de z₁ = 300 mm")
    for c in CICLOS:
        for cen in CENARIOS_ORDEM:
            for e in ESTRATEGIAS:
                k, rot = f"{c}|{cen}|{e}", f"{NOME_CICLO[c].capitalize()}, {cen.lower()}, {e}"
                N.add(f"{rot}: TSE com z₁ = 300 mm", "tab_sensibilidade_z1", k, "tse_pct_z1_300", 1, "%")
                N.add(f"{rot}: ETa/ETc com z₁ = 300 mm", "tab_sensibilidade_z1", k, "eta_etc_pct_z1_300", 1, "%")
                N.add(f"{rot}: aplicada com z₁ = 300 mm", "tab_sensibilidade_z1", k, "aplicada_mm_z1_300", 1, " mm")
                N.add(f"{rot}: percolação incremental com z₁ = 300 mm", "tab_sensibilidade_z1", k,
                      "percolacao_incremental_mm_z1_300", 1, " mm")

    N.secao("9. Diagnósticos (o modelo não aplica)")
    for c in CICLOS:
        nc = NOME_CICLO[c]
        N.add(f"Kc,mid ajustado pela eq. 62, {nc}", "tab_diagnosticos", f"kc_mid_ajustado|{c}", "valor", 3)
        N.add(f"Diferença para o Kc,mid tabelado, {nc}", "tab_diagnosticos", f"kc_mid_diferenca|{c}", "valor", 3, sinal=True)
        N.add(f"p ajustado mínimo, {nc}", "tab_diagnosticos", f"p_ajustado_min|{c}", "valor", 2)
        N.add(f"p ajustado máximo, {nc}", "tab_diagnosticos", f"p_ajustado_max|{c}", "valor", 2)
        N.add(f"Horas com ET0 negativa zerada, {nc}", "tab_diagnosticos", f"et0_negativa_horas|{c}", "valor", 0, " h")
        N.add(f"Soma da ET0 negativa zerada, {nc}", "tab_diagnosticos", f"et0_negativa_soma_mm|{c}", "valor", 2, " mm")
        N.add(f"ΣET0 com Ra zerada pelo meio da hora, {nc}", "tab_diagnosticos", f"et0_pm_ra_pelo_meio_mm|{c}", "valor", 1, " mm")
    N.add("Rs/Rso bruta máxima em 2023 (Ra > 1,5 MJ m⁻² h⁻¹)", "tab_diagnosticos", "rs_rso_ano_maximo|2023", "valor", 3)
    N.add("Rs/Rso bruta, percentil 99, em 2023", "tab_diagnosticos", "rs_rso_ano_p99|2023", "valor", 3)

    N.secao("10. Anos vizinhos (completude da A204)")
    for chave in sorted(res.tabelas["tab_completude_anos"].linhas):
        ano, janela = chave.split("|")
        N.add(f"{ano}, janela {janela.replace('_', ' ')}: dias sem registro", "tab_completude_anos", chave,
              "dias_sem_registro", tipo="int")
        N.add(f"{ano}, janela {janela.replace('_', ' ')}: maior lacuna contínua", "tab_completude_anos", chave,
              "maior_lacuna_sem_registro_dias", 0, " d")
    for chave in sorted(res.tabelas["tab_afirmacoes_anos_vizinhos"].linhas, key=int):
        afirmacao = res.tabelas["tab_afirmacoes_anos_vizinhos"].valor(chave, "afirmacao")
        N.add(f"{afirmacao}: valor no arquivo", "tab_afirmacoes_anos_vizinhos", chave, "valor_obtido", tipo="int")
        N.add(f"{afirmacao}: confere?", "tab_afirmacoes_anos_vizinhos", chave, "confere", tipo="texto")
    for s in res.externos:
        if not (s.presente and s.registrado):
            N.add_livre(s.descricao, PENDENTE, f"arquivo ausente: {s.url} → `{s.destino}`")

    N.secao("11. Execução")
    N.add_livre("Tempo de execução do pipeline", f"{num(tempo_total_s, 1)} s", "`AMBIENTE.md`")
    return N


# ---------------------------------------------------------------------------
# RELATORIO.md
# ---------------------------------------------------------------------------

def _m(res, ciclo, cen, e):
    return res.principal[(ciclo, cen, e)].metricas


def _anomalia_e1(res) -> List[str]:
    """Confere se E1 percola mais no seco restrito que no seco abundante e, se sim, explica pela série horária."""
    ab, re_ = _m(res, "seco", "Abundante", "E1"), _m(res, "seco", "Restrito", "E1")
    v1 = res.v1.metricas
    v1_ab, v1_re = v1[("seco", "Abundante", "E1")], v1[("seco", "Restrito", "E1")]
    linhas = [
        f"No v1, E1 percolava {num(v1_re['percolacao_acumulada_mm'], 2)} mm no ciclo seco com o cenário restrito e "
        f"{num(v1_ab['percolacao_acumulada_mm'], 2)} mm com o abundante, mesmo aplicando menos água "
        f"({num(v1_re['lamina_total_mm'])} × {num(v1_ab['lamina_total_mm'])} mm).",
    ]
    if re_.percolacao_mm > ab.percolacao_mm:
        r = res.principal[("seco", "Restrito", "E1")]
        s, f = r.serie, r.forcante
        por_dia: Dict[int, List[float]] = {}
        for k in range(len(f)):
            d = por_dia.setdefault(f.dia[k], [0.0, 0.0, 0.0])
            d[0] += s["i_mm"][k]
            d[1] += s["p_mm"][k]
            d[2] += s["d2_mm"][k]
        dias = [d for d, v in por_dia.items() if v[2] > 1e-9]
        linhas.append(
            f"No v2 a anomalia persiste: {num(re_.percolacao_mm)} mm (restrito) × {num(ab.percolacao_mm)} mm "
            "(abundante). Dias do ciclo seco restrito com percolação, pela série horária de E1:")
        linhas.append("")
        linhas.append(tabela_markdown(
            ["Dia", "Data", "Irrigação (mm)", "Chuva (mm)", "Percolação (mm)"],
            [[inteiro(d), f.rotulos[24 * (d - 1)][:10], num(por_dia[d][0]), num(por_dia[d][1]), num(por_dia[d][2], 2)]
             for d in dias]))
    else:
        linhas.append(
            f"No v2 a anomalia não se repete: E1 percola {num(re_.percolacao_mm)} mm no restrito e "
            f"{num(ab.percolacao_mm)} mm no abundante, aplicando {num(re_.aplicada_mm)} e {num(ab.aplicada_mm)} mm.")
    return linhas


def _plato_v1(res, ciclo: str, cenario: str = "Abundante") -> tuple:
    """Menor L do v1 em que o conforto de E1 atinge o máximo da varredura de lâminas."""
    valores = {L: res.v1.sensibilidade_e1[(ciclo, cenario, L)]["conforto_hidrico_pct"] for L in res.sens_e1_laminas}
    maximo = max(valores.values())
    return min(L for L, v in valores.items() if v == maximo), maximo


def montar_relatorio(res, tempo_total_s: float) -> str:
    par, md = res.par, res.markdown
    t = []
    a = t.append
    a("# Relatório de resultados do modelo v2")
    a("")
    a("Projeto PIC/FAPEMA \"Automação da Irrigação em Hortas Comunitárias com Sensores e IoT\" (Edital COORD.NUPEX "
      "nº 01/2026). Autor: Erdeson Monteiro Candeias. Orientador: Prof. Alex Rogaleski Marques.")
    a("")
    a(f"Gerado por `python3 main.py pipeline` em {date.today():%d/%m/%Y}. Todos os números saem dos resultados "
      "calculados; nada foi digitado. Modelo descrito em [`docs/MODELO.md`](../../docs/MODELO.md); "
      "números para citação em [`NUMEROS_ARTIGO.md`](NUMEROS_ARTIGO.md).")
    a("")

    a("## 1. Dados")
    a("")
    e = res.estacao
    a(f"Série horária da estação automática {e.codigo} ({e.nome}-{e.uf}) do INMET, arquivo `{e.arquivo}`, "
      f"SHA-256 `{e.sha256}`; latitude {num(e.latitude, 5)}°, longitude {num(e.longitude, 5)}°, altitude "
      f"{num(e.altitude, 2)} m, lidas do cabeçalho do arquivo. Nenhum dado foi estimado ou interpolado: os dois ciclos "
      "não têm falhas sem regra de tratamento (seção 2 de `docs/MODELO.md`).")
    a("")
    a(md["tab_clima_ciclos"])
    for c in CICLOS:
        cc = res.ciclos[c]
        pm = sum(h.et0_mm for h in cc.horas)
        hs = sum(d.et0_hs_mm for d in cc.dias)
        a(f"- Ciclo {NOME_CICLO[c]}: Hargreaves-Samani dá {num(hs)} mm, contra {num(pm)} mm de Penman-Monteith "
          f"({'+' if hs > pm else ''}{num((hs - pm) / pm * 100)}%).")
    a("")
    a(md["tab_normal_climatologica"])
    a(f"Média de referência: {FONTE_MEDIA_CHUVA}.")
    a("")
    for c in CICLOS:
        media = res.media_chuva.janela(PESOS_JANELA_MEDIA[c])
        chuva = sum(h.p_mm for h in res.ciclos[c].horas)
        a(f"- Ciclo {NOME_CICLO[c]}: {num(chuva)} mm em 2023 contra {num(media)} mm da média 1991–2021 "
          f"({num(chuva / media * 100)}% da média).")
    a("")

    a("## 2. Parâmetros e cenários")
    a("")
    a(md["tab_parametros"])
    a(md["tab_cenarios"])

    a("## 3. Desempenho das estratégias")
    a("")
    a("Todas as estratégias decidem no início de cada hora com o estado do fim da hora anterior e recebem informação "
      "perfeita do estado do solo (seção 5 de `docs/MODELO.md`).")
    a("")
    for c in CICLOS:
        a(md[f"tab_desempenho_{c}"])
        e1, e2 = _m(res, c, "Abundante", "E1"), _m(res, c, "Abundante", "E2")
        a(f"Com água sobrando (abundante, ciclo {NOME_CICLO[c]}), E1 fica com TSE de {num(e1.tse_pct)}% e E2 com "
          f"{num(e2.tse_pct)}%; ETa/ETc de {num(e1.eta_etc_pct)}% e {num(e2.eta_etc_pct)}%. E1 aplica "
          f"{num(e1.aplicada_mm)} mm e E2 {num(e2.aplicada_mm)} mm; a percolação incremental é "
          f"{num(e1.percolacao_incremental_mm)} e {num(e2.percolacao_incremental_mm)} mm.")
        a("")

    a("## 4. Sensibilidade de E1 à lâmina fixa (Figura 1)")
    a("")
    a(md["tab_sensibilidade_e1"])
    for c in CICLOS:
        tse = [res.sens_e1[(c, L)].metricas.tse_pct for L in res.sens_e1_laminas]
        perc = [res.sens_e1[(c, L)].metricas.percolacao_incremental_mm for L in res.sens_e1_laminas]
        e2 = _m(res, c, "Abundante", "E2")
        a(f"- Ciclo {NOME_CICLO[c]}: de L = {num(res.sens_e1_laminas[0], 0)} a {num(res.sens_e1_laminas[-1], 0)} mm, o TSE "
          f"de E1 varia de {num(min(tse))}% a {num(max(tse))}% e a percolação incremental de {num(min(perc))} a "
          f"{num(max(perc))} mm; E2 tem {num(e2.tse_pct)}% e {num(e2.percolacao_incremental_mm)} mm.")
    a("")
    a("![Figura 1](figuras/figura1_sensibilidade_e1.png)")
    a("")
    a("Figura 1. Sensibilidade de E1 à lâmina fixa L no cenário abundante: (a) TSE; (b) percolação incremental. "
      "Linhas horizontais: E2.")
    a("")

    a("## 5. Ciclo seco, cenário restrito (Figura 2)")
    a("")
    linhas = []
    for e_ in ESTRATEGIAS:
        m = _m(res, "seco", "Restrito", e_)
        linhas.append([f"{e_} ({NOMES_ESTRATEGIAS[e_]})", num(m.tse_pct), num(m.eta_etc_pct), num(m.dr_max_mm),
                       num(m.theta1_min, 3), inteiro(m.acionamentos), num(m.lamina_media_mm), num(m.aplicada_mm),
                       inteiro(m.dias_reservatorio_vazio)])
    a(tabela_markdown(["Estratégia", "TSE (%)", "ETa/ETc (%)", "Dr máx (mm)", "θ₁ mín", "Acion.",
                       "Lâmina média (mm)", "Aplicada (mm)", "Dias vazio"], linhas, ["e"] + ["d"] * 8,
                      notas=[f"θpmp = {num(par.theta_pmp, 2)}; RAW = {num(par.raw_mm)} mm; TAW = {num(par.taw_mm)} mm. "
                             "Lâmina média = aplicada/acionamentos."]))
    melhor_tse = max(ESTRATEGIAS, key=lambda x: _m(res, "seco", "Restrito", x).tse_pct)
    melhor_eta = max(ESTRATEGIAS, key=lambda x: _m(res, "seco", "Restrito", x).eta_etc_pct)
    menor_dr = min(ESTRATEGIAS, key=lambda x: _m(res, "seco", "Restrito", x).dr_max_mm)
    theta_min = min(_m(res, "seco", "Restrito", x).theta1_min for x in ESTRATEGIAS)
    if theta_min > par.theta_pmp + 1e-6:
        frase_pmp = (f"Nenhuma estratégia leva θ₁ ao ponto de murcha: o menor θ₁ do ciclo é {num(theta_min, 3)}, acima de "
                     f"θpmp = {num(par.theta_pmp, 2)}, porque o Ks reduz a ETa à medida que o solo seca.")
    else:
        frase_pmp = f"θ₁ chega ao ponto de murcha (θpmp = {num(par.theta_pmp, 2)}) em pelo menos uma estratégia."
    a(f"Maior TSE: {melhor_tse}. Maior ETa/ETc: {melhor_eta}. Menor Dr máximo: {menor_dr}. {frase_pmp}")
    a("")
    a("![Figura 2](figuras/figura2_seco_restrito.png)")
    a("")
    a("Figura 2. Ciclo seco, cenário restrito: (a) volume no reservatório; (b) depleção da zona radicular, com RAW e TAW. "
      "Série horária, marcador a cada 24 h.")
    a("")

    a("## 6. Capacidade mínima do reservatório")
    a("")
    a(md["tab_capacidade_minima"])
    a("A varredura completa está em `tabelas/tab_varredura_reservatorio.md`.")
    a("")

    a("## 7. Sensibilidade à profundidade radicular (z₁ = 300 mm)")
    a("")
    a(md["tab_sensibilidade_z1"])
    for c in CICLOS:
        e1, e2 = res.z1[(c, "Abundante", "E1")].metricas, res.z1[(c, "Abundante", "E2")].metricas
        relacao = ("menor" if res.par_z1.lamina_e1_mm < res.par_z1.raw_mm else "maior ou igual")
        efeito = ("cada acionamento de E1 não chega a repor a zona radicular até θcc"
                  if relacao == "menor" else "cada acionamento de E1 repõe a zona radicular até θcc e o excesso percola")
        a(f"- Ciclo {NOME_CICLO[c]}, abundante, z₁ = {num(res.par_z1.z1_mm, 0)} mm: E1 com TSE de {num(e1.tse_pct)}% e "
          f"{inteiro(e1.acionamentos)} acionamentos; E2 com {num(e2.tse_pct)}% e {inteiro(e2.acionamentos)}. "
          f"Como L = {num(res.par_z1.lamina_e1_mm, 0)} mm é {relacao} que RAW = {num(res.par_z1.raw_mm)} mm, {efeito}.")
    a("")

    a("## 8. Comparação v1 × v2")
    a("")
    a(md["tab_comparacao_v1_v2"])
    for c in CICLOS:
        v1e1 = res.v1.metricas[(c, "Abundante", "E1")]
        e1 = _m(res, c, "Abundante", "E1")
        a(f"- Ciclo {NOME_CICLO[c]}, abundante, E1: conforto v1 de {num(v1e1['conforto_hidrico_pct'])}% "
          f"(1 − {inteiro(v1e1['numero_acionamentos'])}/{inteiro(v1e1['dias_simulados'])} dias = "
          f"{num(100 * (1 - v1e1['numero_acionamentos'] / v1e1['dias_simulados']))}%); no v2, TSE de {num(e1.tse_pct)}% das "
          f"horas e TSE diário de {num(e1.tse_diaria_pct)}% dos dias.")
    a("")
    a("A coluna \"TSE diário v2\" aplica ao v2 uma medida por dia: basta uma hora com Dr > RAW para o dia contar como "
      "estressado. Com decisão horária, cada acionamento é precedido de uma hora de detecção com Dr > RAW, então a medida "
      "por dia rebaixa também E2: " + "; ".join(
          f"no ciclo {NOME_CICLO[c]} abundante, E2 tem TSE de {num(_m(res, c, 'Abundante', 'E2').tse_pct)}% das horas e "
          f"TSE diário de {num(_m(res, c, 'Abundante', 'E2').tse_diaria_pct)}% dos dias" for c in CICLOS) +
      ". A diferença entre \"TSE v2\" e \"TSE diário v2\" mostra quanto do \"teto\" de E1 no v1 vinha da medida por dia.")
    a("")

    a("## 9. Correções em relação ao relatório do v1")
    a("")
    v1 = res.v1
    seq_v1 = v1.metricas[("chuvoso", "Sequeiro", "Sequeiro")]
    aw_v1 = v1.soil.agua_disponivel_mm
    a("1. **Seção 2.4 (confronto com normais).** O v1 anunciava o confronto e não o fazia. No v2 a chuva dos ciclos "
      "é comparada com a média 1991–2021 da estação 82768 (Corrêa, Carvalho e Mendes, 2023), na seção 1.")
    a(f"2. **Seção 11 (percolação do sequeiro).** O texto fixo citava outro valor; a percolação do sequeiro no ciclo "
      f"chuvoso calculada pelo v1 é {num(seq_v1['percolacao_acumulada_mm'], 2)} mm. No v2 ela é "
      f"{num(res.sequeiro['chuvoso'].metricas.percolacao_mm, 2)} mm.")
    a("3. **Seção 12.1 (\"série sintética\").** A menção foi retirada do gerador do v1. Todo resultado usa só o arquivo "
      "do INMET, conferido pelo SHA-256.")
    a(f"4. **Seções 12.2 e 12.3 (banda morta).** No v1, θlim correspondia a p·AD = {num(v1.soil.p, 2)} × {num(aw_v1)} = "
      f"{num(v1.soil.p * aw_v1, 2)} mm de depleção, mas E2/E3 só disparavam com déficit ≥ {num(v1.limiar_deficit_mm)} mm. "
      f"No v2 o gatilho é o próprio RAW = {num(par.raw_mm)} mm, calculado, e a banda deixa de existir.")
    planos = [(_plato_v1(res, c), c) for c in CICLOS]
    frase_plato = "; ".join(
        f"no ciclo {NOME_CICLO[c]}, o conforto de E1 do v1 no cenário abundante chega ao máximo ({num(mx)}%) a partir "
        f"de L = {num(L, 0)} mm" for (L, mx), c in planos)
    a("5. **Seção 13, item 3 (platô de E1).** O texto fixo do v1 situava o platô em outra faixa de lâminas. Calculado: "
      + frase_plato + ".")
    a("6. **Seção 13, item 4 (\"teto estrutural\" de E1).** Ver seção 8: no v2 a regra de E1 é avaliada de hora em hora.")
    a("7. **\"Nenhuma estratégia evitou o ponto de murcha\".** No v2, com Ks, θ₁ não chega a θpmp em nenhuma rodada "
      f"principal (menor θ₁: {num(min(r.metricas.theta1_min for r in res.principal.values()), 3)}). O pior momento é "
      "descrito por Dr máx e ETa/ETc.")
    a("")
    a("**Percolação de E1 no ciclo seco (seção 13, item 1, do v1).**")
    a("")
    t += _anomalia_e1(res)
    a("")

    a("## 10. Diagnósticos")
    a("")
    a(md["tab_diagnosticos"])

    a("## 11. Anos vizinhos")
    a("")
    a(md["tab_completude_anos"])
    a(md["tab_afirmacoes_anos_vizinhos"])
    a(md["tab_dados_externos"])
    a("O objetivo (c) do artigo fica restrito a 2023; os outros anos só têm a completude conferida.")
    a("")

    a("## 12. Limitações")
    a("")
    a("Lista completa na seção 9 de `docs/MODELO.md`: um só ano; camada 2 sem extração; drenagem instantânea; sem "
      "escoamento superficial; parâmetros de literatura; informação perfeita; Kc sem ajuste climático; p fixo; ET0 negativa "
      "zerada; anemômetro assumido a 10 m.")
    a("")

    a("## 13. Reprodutibilidade")
    a("")
    a(f"Ambiente e tempo de execução em [`AMBIENTE.md`](AMBIENTE.md) ({num(tempo_total_s, 1)} s nesta execução). "
      "SHA-256 de cada CSV em [`CHECKSUMS.txt`](CHECKSUMS.txt).")
    a("")
    a("## 14. Arquivos")
    a("")
    linhas = [[f"`tabelas/{n}.csv`", f"`tabelas/{n}.md`"] for n in sorted(res.tabelas)]
    a(tabela_markdown(["Tabela (dados)", "Tabela (formatada)"], linhas, ["e", "e"]))
    a(f"Séries horárias: {inteiro(len(res.series))} arquivos em `series/` (uma por rodada, mais o clima de cada ciclo).")
    a("")
    return "\n".join(t)


# ---------------------------------------------------------------------------
# AMBIENTE.md, CHECKSUMS.txt e resultados.json
# ---------------------------------------------------------------------------

CAMINHOS_DO_CODIGO = ("src", "main.py", "requirements.txt", "data/raw")
BIBLIOTECAS = ("numpy", "matplotlib", "contourpy", "cycler", "fonttools", "kiwisolver", "packaging", "pillow",
               "pyparsing", "python-dateutil")


def _git(*args) -> Optional[str]:
    try:
        r = subprocess.run(["git", *args], cwd=ROOT_DIR, capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def montar_ambiente(tempo_total_s: float, tempo_rodadas_s: float, n_rodadas: int) -> str:
    from matplotlib import font_manager
    from src.v2.conferencia import impressao_digital_do_codigo
    versoes = []
    for b in BIBLIOTECAS:
        try:
            versoes.append([b, metadata.version(b)])
        except metadata.PackageNotFoundError:
            versoes.append([b, "não instalada"])
    fonte = font_manager.findfont("Liberation Serif", fallback_to_default=False)
    commit = _git("log", "-1", "--format=%H", "--", *CAMINHOS_DO_CODIGO)
    sujo = _git("status", "--porcelain", "--", *CAMINHOS_DO_CODIGO)
    linhas = [
        "# Ambiente de execução",
        "",
        "**Ferramenta usada na simulação:** código próprio em Python (pacote `src/v2/` deste repositório), sem software "
        "de simulação de terceiros. O balanço hídrico, a ET0 de Penman-Monteith e o Hargreaves-Samani seguem as equações "
        "do FAO-56, implementadas em `src/v2/fao56.py` e conferidas contra o Exemplo 19 do FAO-56. As figuras usam "
        "matplotlib; o núcleo do modelo usa só a biblioteca padrão do Python.",
        "",
        tabela_markdown(["Item", "Valor"], [
            ["Python", sys.version.split()[0]],
            ["Implementação", platform.python_implementation()],
            ["Sistema operacional", platform.platform()],
            ["Processador", platform.machine()],
            ["SQLite", sqlite3.sqlite_version],
            ["Fonte das figuras", os.path.basename(fonte)],
            ["Impressão digital do código (SHA-256 de src/, main.py, requirements.txt, data/raw/ e data/referencias/)",
             f"`{impressao_digital_do_codigo(ROOT_DIR)}`"],
            ["Último commit do git que alterou o código",
             (commit or "indisponível") + (" (havia alterações ainda não commitadas)" if sujo else "")],
            ["Comando", "`python3 main.py pipeline`"],
            ["Rodadas simuladas", inteiro(n_rodadas)],
            ["Tempo das rodadas", f"{num(tempo_rodadas_s, 1)} s"],
            ["Tempo total do pipeline", f"{num(tempo_total_s, 1)} s"],
        ], ["e", "e"]),
        tabela_markdown(["Biblioteca", "Versão"], versoes, ["e", "e"],
                        notas=["Versões exatas de numpy e matplotlib fixadas em `requirements.txt`."]),
        "A impressão digital identifica exatamente o código e os dados que geraram estes resultados; "
        "`python3 main.py conferir` recalcula e compara com a do código atual.",
        "",
        "O modelo é determinístico: não há gerador aleatório em nenhuma parte. Os CSVs não contêm data, hora, caminho "
        "absoluto nem hash de commit, e por isso os mesmos dados de entrada geram os mesmos SHA-256 (`CHECKSUMS.txt`).",
        "",
    ]
    return "\n".join(linhas)


def gravar_checksums(dir_saida: str) -> str:
    entradas = []
    for raiz, _dirs, arquivos in os.walk(dir_saida):
        for a in arquivos:
            if a.endswith(".csv"):
                caminho = os.path.join(raiz, a)
                with open(caminho, "rb") as f:
                    entradas.append((os.path.relpath(caminho, dir_saida).replace(os.sep, "/"),
                                     hashlib.sha256(f.read()).hexdigest()))
    entradas.sort()
    caminho = os.path.join(dir_saida, "CHECKSUMS.txt")
    with open(caminho, "w", encoding="utf-8") as f:
        for rel, h in entradas:
            f.write(f"{h}  {rel}\n")
    return caminho


def montar_json(res) -> dict:
    def met(m):
        d = asdict(m)
        return {k: v for k, v in d.items()}

    return {
        "parametros": res.par.como_dict(),
        "parametros_z1_300": res.par_z1.como_dict(),
        "cenarios": {n: {"capacidade_l": c.capacidade_l, "intervalo_dias": c.intervalo_dias,
                         "oferta_maxima_mm_dia": c.oferta_maxima_mm_dia(res.par.area_m2)}
                     for n, c in CENARIOS.items()},
        "estacao": asdict(res.estacao),
        "ciclos": {c: {"inicio": res.ciclos[c].inicio.isoformat(), "fim": res.ciclos[c].fim.isoformat()} for c in CICLOS},
        "principal": {f"{c}|{cen}|{e}": met(_m(res, c, cen, e)) for c in CICLOS for cen in CENARIOS_ORDEM for e in ESTRATEGIAS},
        "sequeiro": {c: met(res.sequeiro[c].metricas) for c in CICLOS},
        "capacidade_minima": {f"{c}|{n}|{e}": v for (c, n, e), v in res.capacidade_minima.items()},
        "tabelas": {n: {"csv": f"tabelas/{n}.csv", "md": f"tabelas/{n}.md"} for n in sorted(res.tabelas)},
        "figuras": {"figura1": "figuras/figura1_sensibilidade_e1.png", "figura2": "figuras/figura2_seco_restrito.png"},
    }


def gerar_documentos(res, dir_saida: str, tempo_total_s: float) -> None:
    n_rodadas = len(res.principal) + len(res.sequeiro) + len(res.sens_e1) + len(res.varredura) + len(res.z1) + len(res.sequeiro_z1)
    with open(os.path.join(dir_saida, "NUMEROS_ARTIGO.md"), "w", encoding="utf-8") as f:
        f.write(montar_numeros(res, tempo_total_s).markdown())
    with open(os.path.join(dir_saida, "RELATORIO.md"), "w", encoding="utf-8") as f:
        f.write(montar_relatorio(res, tempo_total_s))
    with open(os.path.join(dir_saida, "AMBIENTE.md"), "w", encoding="utf-8") as f:
        f.write(montar_ambiente(tempo_total_s, res.tempo_rodadas_s, n_rodadas))
    with open(os.path.join(dir_saida, "resultados.json"), "w", encoding="utf-8") as f:
        json.dump(montar_json(res), f, ensure_ascii=False, indent=1, sort_keys=True, default=str)
    from src.v2.conferencia import markdown_pendencias, pendencias
    with open(os.path.join(dir_saida, "PENDENCIAS.md"), "w", encoding="utf-8") as f:
        f.write(markdown_pendencias(pendencias(ROOT_DIR, dir_resultados=dir_saida)))
    gravar_checksums(dir_saida)
