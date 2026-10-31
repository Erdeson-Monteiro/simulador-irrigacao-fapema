"""
Pipeline do v2: `python3 main.py pipeline`.

Gera do zero, em `resultados/v2/`: séries horárias de cada rodada, tabelas (CSV + Markdown),
figuras (PNG, PDF e dados), NUMEROS_ARTIGO.md, RELATORIO.md, AMBIENTE.md, CHECKSUMS.txt e
resultados.json. Tudo é escrito numa pasta temporária, que só substitui `resultados/v2/`
se a execução terminar sem erro. Nenhum número de texto é digitado: tabelas e documentos
saem dos resultados calculados.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
import os
import shutil
import time
from typing import Dict, List, Optional, Sequence, Tuple

from src.v2 import figuras
from src.v2.clima import CICLOS_2023, CicloClima, extrair_ciclo, montar_serie_horaria
from src.v2.comparacao_v1 import ResultadosV1, rodar_v1
from src.v2.dados_externos import (
    AFIRMACOES_ARTIGO,
    ANOS_VIZINHOS,
    PESOS_JANELA_NORMAL,
    CompletudeJanela,
    FormatoNaoReconhecido,
    NormalEstacao,
    StatusArquivo,
    arquivo_a204_do_ano,
    completude_ano,
    completude_janela,
    janelas_do_ano,
    ler_normal_balsas,
    status_dados_externos,
)
from src.v2.diagnosticos import DiagnosticoCiclo, diagnosticar_ciclo, rs_rso_no_ano
from src.v2.formatacao import TRACO, TabelaCSV, escrever_csv, inteiro, num, tabela_markdown
from src.v2.inmet import ROOT_DIR, EstacaoINMET, ler_arquivo_inmet, ler_registro_sha256
from src.v2.modelo import (
    ESTRATEGIAS,
    NOMES_ESTRATEGIAS,
    SEQUEIRO,
    Forcante,
    Metricas,
    Rodada,
    forcante_do_ciclo,
    simular,
)
from src.v2.parametros import CENARIOS, PARAMETROS_PADRAO, Cenario, ParametrosModelo


DIR_SAIDA_PADRAO = os.path.join(ROOT_DIR, "resultados", "v2")
CICLOS = ("chuvoso", "seco")
CENARIOS_ORDEM = ("Abundante", "Moderado", "Restrito")
LAMINAS_E1_MM = (5.0, 10.0, 15.0, 20.0, 25.0, 30.0)
CAPACIDADES_L = tuple(float(c) for c in range(250, 2001, 250))
INTERVALOS_DIAS = (3, 7, 14)
LIMIAR_TSE_CAPACIDADE_PCT = 90.0
Z1_SENSIBILIDADE_MM = 300.0
NOME_CICLO = {"chuvoso": "Chuvoso", "seco": "Seco"}

COLUNAS_SERIE_CSV = (
    "hora_local_inicio", "dia_ciclo", "p_mm", "et0_mm", "kc", "etc_mm", "ks", "eta_mm", "i_mm",
    "theta1", "theta2", "dr_mm", "d1_mm", "d2_mm", "v_l",
)
CASAS_SERIE = {
    "p_mm": 4, "et0_mm": 4, "kc": 4, "etc_mm": 4, "ks": 4, "eta_mm": 4, "i_mm": 4,
    "theta1": 6, "theta2": 6, "dr_mm": 4, "d1_mm": 4, "d2_mm": 4, "v_l": 3,
}


@dataclass
class Resultados:
    raiz: str
    estacao: EstacaoINMET
    ciclos: Dict[str, CicloClima]
    par: ParametrosModelo
    par_z1: ParametrosModelo
    forcantes: Dict[str, Forcante]
    principal: Dict[Tuple[str, str, str], Rodada]
    sequeiro: Dict[str, Rodada]
    sens_e1: Dict[Tuple[str, float], Rodada]
    varredura: Dict[Tuple[str, int, float, str], Metricas]
    capacidade_minima: Dict[Tuple[str, int, str], dict]
    z1: Dict[Tuple[str, str, str], Rodada]
    sequeiro_z1: Dict[str, Rodada]
    v1: ResultadosV1
    diagnosticos: Dict[str, DiagnosticoCiclo]
    rs_rso_ano: Dict[str, float]
    normal: Optional[NormalEstacao]
    normal_situacao: str
    completude: List[CompletudeJanela]
    externos: List[StatusArquivo]
    sens_e1_laminas: Tuple[float, ...] = LAMINAS_E1_MM
    intervalos: Tuple[int, ...] = INTERVALOS_DIAS
    tabelas: Dict[str, TabelaCSV] = field(default_factory=dict)
    markdown: Dict[str, str] = field(default_factory=dict)
    figuras: Dict[str, dict] = field(default_factory=dict)
    series: List[str] = field(default_factory=list)
    tempo_rodadas_s: float = 0.0


def _slug(texto: str) -> str:
    return texto.lower().replace(" ", "_")


# ---------------------------------------------------------------------------
# Rodadas
# ---------------------------------------------------------------------------

def rodar_principal(forcantes, par) -> Tuple[Dict[Tuple[str, str, str], Rodada], Dict[str, Rodada]]:
    principal, sequeiro = {}, {}
    for ciclo in CICLOS:
        f = forcantes[ciclo]
        seq = simular(SEQUEIRO, f, par, nome_ciclo=ciclo)
        sequeiro[ciclo] = seq
        for cen in CENARIOS_ORDEM:
            for e in ESTRATEGIAS:
                principal[(ciclo, cen, e)] = simular(e, f, par, CENARIOS[cen], ciclo, seq.metricas.percolacao_mm)
    return principal, sequeiro


def rodar_sensibilidade_e1(forcantes, par, sequeiro) -> Dict[Tuple[str, float], Rodada]:
    return {
        (ciclo, L): simular("E1", forcantes[ciclo], par.com(lamina_e1_mm=L), CENARIOS["Abundante"], ciclo,
                            sequeiro[ciclo].metricas.percolacao_mm)
        for ciclo in CICLOS for L in LAMINAS_E1_MM
    }


def rodar_varredura(forcantes, par, sequeiro, gravar) -> Tuple[dict, dict]:
    metricas, minima = {}, {}
    for ciclo in CICLOS:
        for n in INTERVALOS_DIAS:
            for e in ESTRATEGIAS:
                escolhida = None
                for cap in CAPACIDADES_L:
                    cen = Cenario(f"{int(cap)} L a cada {n} d", cap, n)
                    r = simular(e, forcantes[ciclo], par, cen, ciclo, sequeiro[ciclo].metricas.percolacao_mm)
                    gravar(r, os.path.join("series", "varredura", f"{ciclo}_{n:02d}d_{int(cap):04d}L_{e}.csv"))
                    metricas[(ciclo, n, cap, e)] = r.metricas
                    if escolhida is None and r.metricas.tse_pct >= LIMIAR_TSE_CAPACIDADE_PCT:
                        escolhida = cap
                ref = escolhida if escolhida is not None else CAPACIDADES_L[-1]
                m = metricas[(ciclo, n, ref, e)]
                minima[(ciclo, n, e)] = {
                    "capacidade_l": escolhida,
                    "texto": (num(escolhida, 0) + " L") if escolhida is not None else f"> {num(CAPACIDADES_L[-1], 0)} L",
                    "oferta_mm_dia": (escolhida / (n * par.area_m2)) if escolhida is not None else None,
                    "tse_pct": m.tse_pct,
                    "eta_etc_pct": m.eta_etc_pct,
                    "capacidade_referencia_l": ref,
                }
    return metricas, minima


def rodar_z1(forcantes, par_z1):
    return rodar_principal(forcantes, par_z1)


# ---------------------------------------------------------------------------
# Gravação das séries horárias
# ---------------------------------------------------------------------------

def metadados_base(estacao: EstacaoINMET, par: ParametrosModelo, conteudo: str) -> List[str]:
    return [
        f"conteudo: {conteudo}",
        "origem: PIC/FAPEMA, simulador de irrigação v2 (docs/MODELO.md); gerado por python3 main.py pipeline",
        f"clima: {estacao.arquivo} (SHA-256 {estacao.sha256}); estação {estacao.codigo} {estacao.nome}-{estacao.uf}, "
        f"lat {estacao.latitude:.8f}, lon {estacao.longitude:.8f}, alt {estacao.altitude:.2f} m",
        f"parametros: {par.resumo()}",
    ]


def gravar_serie_rodada(caminho: str, rodada: Rodada, metadados: Sequence[str]) -> None:
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    s, f = rodada.serie, rodada.forcante
    linhas = [f"# {m}" for m in metadados]
    linhas.append(",".join(COLUNAS_SERIE_CSV))
    colunas = COLUNAS_SERIE_CSV[2:]
    for k in range(len(f)):
        valores = [f.rotulos[k], str(f.dia[k])]
        for c in colunas:
            v = s[c][k]
            valores.append("" if math.isnan(v) else f"{v:.{CASAS_SERIE[c]}f}")
        linhas.append(",".join(valores))
    with open(caminho, "w", encoding="utf-8", newline="") as arq:
        arq.write("\n".join(linhas) + "\n")


def descricao_rodada(r: Rodada) -> str:
    cen = r.cenario
    reservatorio = f"{cen.nome}: {num(cen.capacidade_l, 0)} L a cada {cen.intervalo_dias} d" if cen else "sem irrigação"
    extra = f"; L = {r.parametros.lamina_e1_mm:g} mm" if r.estrategia == "E1" else ""
    return (f"rodada: ciclo {r.ciclo}; {reservatorio}; estratégia {r.estrategia} "
            f"({NOMES_ESTRATEGIAS[r.estrategia]}){extra}")


NOTA_COLUNAS_SERIE = (
    "colunas: hora_local_inicio = início da hora em hora local (UTC−3); p, et0, etc, eta, i, d1 e d2 "
    "são da hora (mm); theta1, theta2, dr e v são do fim da hora; v_l vazio no sequeiro"
)


def gravar_serie_clima(dir_saida: str, ciclo: CicloClima, par: ParametrosModelo, metadados: Sequence[str]) -> List[str]:
    base = os.path.join(dir_saida, "series", "clima")
    os.makedirs(base, exist_ok=True)
    horario = os.path.join(base, f"{ciclo.nome}_horario.csv")
    campos = ["hora_local_inicio", "registro_inmet_utc", "dia_ciclo", "j", "t_meio_utc_h", "p_mm", "t_c", "ur_pct",
              "u10_ms", "u2_ms", "tmax_c", "tmin_c", "urmin_pct", "rs_bruta_kj_m2", "rs_mj", "ra_mj", "rso_mj",
              "rs_rso_bruta", "rs_rso", "origem_rs_rso", "e0_kpa", "ea_kpa", "delta_kpa_c", "rn_mj", "g_mj",
              "et0_bruta_mm", "et0_mm"]
    linhas = [f"# {m}" for m in metadados] + [",".join(campos)]

    def f6(x):
        return "" if x is None else f"{x:.6f}"

    for k, h in enumerate(ciclo.horas):
        t = h.termos
        linhas.append(",".join([
            h.inicio_local.strftime("%Y-%m-%d %H:%M"), h.fim_utc.strftime("%Y-%m-%d %H%M"), str(k // 24 + 1),
            str(h.j), f"{h.t_meio_utc_h:.1f}", f6(h.p_mm), f6(h.t_c), f6(h.ur_pct), f6(h.u10_ms), f6(h.u2_ms),
            f6(h.tmax_c), f6(h.tmin_c), f6(h.urmin_pct), f6(h.rs_bruta_kj_m2), f6(h.rs_mj), f6(h.ra_mj), f6(t.rso),
            f6(t.rs_rso_bruta), f6(t.rs_rso), "medida" if h.ra_mj > 0 else "fim_da_tarde", f6(t.e0), f6(t.ea),
            f6(t.delta_curva), f6(t.rn), f6(t.g), f6(h.et0_bruta_mm), f6(h.et0_mm),
        ]))
    with open(horario, "w", encoding="utf-8", newline="") as arq:
        arq.write("\n".join(linhas) + "\n")

    diario = os.path.join(base, f"{ciclo.nome}_diario.csv")
    campos_d = ["data", "dia_ciclo", "j", "p_mm", "p_max_horaria_mm", "et0_pm_mm", "et0_hs_mm", "tmax_c", "tmin_c",
                "tmed_c", "urmin_pct", "u2_medio_ms", "ra_dia_mj", "kc", "etc_mm"]
    linhas = [f"# {m}" for m in metadados] + [",".join(campos_d)]
    for i, d in enumerate(ciclo.dias):
        kc = par.kc(i + 1)
        linhas.append(",".join([
            d.data.isoformat(), str(i + 1), str(d.j), f6(d.p_mm), f6(d.p_max_horaria_mm), f6(d.et0_pm_mm),
            f6(d.et0_hs_mm), f6(d.tmax_c), f6(d.tmin_c), f6(d.tmed_c), f6(d.urmin_pct), f6(d.u2_medio_ms),
            f6(d.ra_dia_mj), f6(kc), f6(kc * d.et0_pm_mm),
        ]))
    with open(diario, "w", encoding="utf-8", newline="") as arq:
        arq.write("\n".join(linhas) + "\n")
    return [horario, diario]


# ---------------------------------------------------------------------------
# Tabelas
# ---------------------------------------------------------------------------

ABREV = {
    "P": "P = chuva",
    "ET0": "ET0 = evapotranspiração de referência",
    "PM": "PM = Penman-Monteith horário (FAO-56, eq. 53)",
    "HS": "HS = Hargreaves-Samani (FAO-56, eq. 52), por dia local",
    "ETc": "ETc = Kc·ET0, evapotranspiração potencial da cultura",
    "ETa": "ETa = Ks·ETc, evapotranspiração real",
    "TSE": "TSE = tempo sem estresse hídrico, % das horas com Dr ≤ RAW no fim da hora",
    "TSEd": "TSE diário = % dos dias sem nenhuma hora com Dr > RAW",
    "Dr": "Dr = depleção da zona radicular",
    "RAW": "RAW = água facilmente disponível (p·TAW)",
    "TAW": "TAW = água disponível total ((θcc − θpmp)·z₁)",
    "Acion": "Acion. = acionamentos (horas com irrigação)",
    "Perc": "Perc. incr. = percolação abaixo da zona radicular menos a do sequeiro do mesmo ciclo",
    "Efic": "Efic. = eficiência incremental, (aplicada − perc. incr.)/aplicada",
    "Vazio": "Dias vazio = dias com o reservatório abaixo de 0,5 L no fim de alguma hora",
    "E1": "E1 = limiar fixo",
    "E2": "E2 = reposição por balanço hídrico",
    "E3": "E3 = racionamento uniforme",
    "u2": "u₂ = vento a 2 m (eq. 47, anemômetro a 10 m)",
    "Oferta": "Oferta = capacidade/(intervalo·área), em mm/d",
}


def notas(*chaves: str, extra: Sequence[str] = ()) -> List[str]:
    return list(extra) + ["Abreviaturas: " + "; ".join(ABREV[c] for c in chaves) + "."]


class Escritor:
    """Grava cada tabela em CSV (dados) e Markdown (pt-BR) e guarda as referências."""

    def __init__(self, res: Resultados, dir_saida: str):
        self.res, self.dir = res, dir_saida

    def tabela(self, nome, conteudo, par, campos, registros, md, metadados_extra=()):
        meta = metadados_base(self.res.estacao, par, conteudo) + list(metadados_extra)
        t = escrever_csv(os.path.join(self.dir, "tabelas", f"{nome}.csv"), self.dir, campos, registros, meta)
        self.res.tabelas[nome] = t
        self.res.markdown[nome] = md
        with open(os.path.join(self.dir, "tabelas", f"{nome}.md"), "w", encoding="utf-8") as f:
            f.write(md)
        return t


def tab_clima_ciclos(esc: Escritor) -> None:
    res = esc.res
    registros, por_ciclo = [], {}
    for ciclo in CICLOS:
        c = res.ciclos[ciclo]
        pm = sum(h.et0_mm for h in c.horas)
        hs = sum(d.et0_hs_mm for d in c.dias)
        etc = res.sequeiro[ciclo].metricas.etc_mm
        maior = max(c.dias, key=lambda d: d.p_mm)
        normal = res.normal.janela(PESOS_JANELA_NORMAL[ciclo]) if res.normal else None
        chuva = sum(h.p_mm for h in c.horas)
        r = {
            "ciclo": ciclo, "inicio": c.inicio, "fim": c.fim, "horas": len(c.horas), "dias": c.n_dias,
            "chuva_mm": chuva, "et0_pm_mm": pm, "et0_pm_mm_dia": pm / c.n_dias, "et0_hs_mm": hs,
            "et0_hs_mm_dia": hs / c.n_dias, "vies_hs_pct": (hs - pm) / pm * 100.0, "etc_mm": etc,
            "etc_mm_dia": etc / c.n_dias,
            "t_media_c": sum(h.t_c for h in c.horas) / len(c.horas),
            "u2_medio_ms": sum(h.u2_ms for h in c.horas) / len(c.horas),
            "dias_com_chuva": sum(1 for d in c.dias if d.p_mm > 0),
            "maior_chuva_diaria_mm": maior.p_mm, "data_maior_chuva_diaria": maior.data,
            "maior_chuva_horaria_mm": max(h.p_mm for h in c.horas),
            "normal_janela_mm": normal,
            "chuva_sobre_normal_pct": (chuva / normal * 100.0) if normal else None,
        }
        por_ciclo[ciclo] = r
        registros.append((ciclo, r))
    campos = list(registros[0][1].keys())
    sem_normal = "[A CONFIRMAR PELO AUTOR]"

    def linha(rot, chave, fmt):
        return [rot] + [fmt(por_ciclo[c][chave], c) for c in CICLOS]

    linhas_md = [
        linha("Período (dias locais)", "inicio", lambda v, c: f"{por_ciclo[c]['inicio']:%d/%m} a {por_ciclo[c]['fim']:%d/%m/%Y}"),
        linha("Horas", "horas", lambda v, c: inteiro(v)),
        linha("P (mm)", "chuva_mm", lambda v, c: num(v)),
        linha("Normal 1991–2020 da janela (mm)", "normal_janela_mm", lambda v, c: num(v) if v is not None else sem_normal),
        linha("P/normal (%)", "chuva_sobre_normal_pct", lambda v, c: num(v) if v is not None else sem_normal),
        linha("ΣET0 PM (mm)", "et0_pm_mm", lambda v, c: num(v)),
        linha("ET0 PM média (mm/d)", "et0_pm_mm_dia", lambda v, c: num(v, 2)),
        linha("ΣET0 HS (mm)", "et0_hs_mm", lambda v, c: num(v)),
        linha("Viés HS em relação a PM (%)", "vies_hs_pct", lambda v, c: ("+" if v > 0 else "") + num(v)),
        linha("ΣETc (mm)", "etc_mm", lambda v, c: num(v)),
        linha("T média do ar (°C)", "t_media_c", lambda v, c: num(v, 1)),
        linha("u₂ médio (m/s)", "u2_medio_ms", lambda v, c: num(v, 2)),
        linha("Dias com chuva (P > 0)", "dias_com_chuva", lambda v, c: inteiro(v)),
        linha("Maior chuva diária (mm)", "maior_chuva_diaria_mm",
              lambda v, c: f"{num(v)} ({por_ciclo[c]['data_maior_chuva_diaria']:%d/%m})"),
        linha("Maior chuva horária (mm)", "maior_chuva_horaria_mm", lambda v, c: num(v)),
    ]
    extra_normal = [] if res.normal else [
        f"A normal 1991–2020 não foi calculada: {res.normal_situacao}"]
    md = tabela_markdown(["Variável", "Chuvoso", "Seco"], linhas_md, titulo="**Clima dos ciclos (A204, Balsas-MA, 2023)**",
                         notas=notas("P", "ET0", "PM", "HS", "ETc", "u2", extra=[
                             "Viés = (ΣET0 HS − ΣET0 PM)/ΣET0 PM. ETc com a curva de Kc do FAO-56 (eq. 66). "
                             "Dia local = UTC − 3. ET0 horária negativa zerada."] + extra_normal))
    esc.tabela("tab_clima_ciclos", "clima dos dois ciclos (uma linha por ciclo)", res.par, campos, registros, md)


def tab_parametros(esc: Escritor) -> None:
    par = esc.res.par
    f = FONTES_PARAMETROS
    linhas = [
        ("theta_cc", "θcc", "Umidade na capacidade de campo", par.theta_cc, "cm³ cm⁻³", f["solo"]),
        ("theta_pmp", "θpmp", "Umidade no ponto de murcha permanente", par.theta_pmp, "cm³ cm⁻³", f["solo"]),
        ("theta_sat", "θsat", "Umidade na saturação", par.theta_sat, "cm³ cm⁻³", f["premissa_sem_efeito"]),
        ("p", "p", "Fração da TAW esgotável sem estresse", par.p, "—", f["p"]),
        ("z1", "z₁", "Espessura da camada 1 (zona radicular efetiva, 0–20 cm)", par.z1_mm, "mm", f["z1"]),
        ("z2", "z₂", "Espessura da camada 2 (20–40 cm)", par.z2_mm, "mm", f["premissa_sem_efeito"]),
        ("f_ext2", "f_ext2", "Fração da ETa retirada da camada 2", par.f_ext2, "—", f["premissa"]),
        ("theta0", "θ₁(0), θ₂(0)", "Umidade inicial das camadas (perfil na capacidade de campo)", par.theta1_0, "cm³ cm⁻³", f["premissa"]),
        ("taw", "TAW", "Água disponível total, (θcc − θpmp)·z₁", par.taw_mm, "mm", f["derivado"]),
        ("raw", "RAW", "Água facilmente disponível, p·TAW", par.raw_mm, "mm", f["derivado"]),
        ("theta_lim", "θlim", "Umidade em que Dr = RAW, θcc − p·(θcc − θpmp)", par.theta_lim, "cm³ cm⁻³", f["derivado"]),
        ("kc_ini", "Kc,ini", "Coeficiente de cultura, fase inicial", par.kc_ini, "—", f["kc"]),
        ("kc_mid", "Kc,mid", "Coeficiente de cultura, fase média", par.kc_mid, "—", f["kc"]),
        ("kc_end", "Kc,end", "Coeficiente de cultura, fim do ciclo", par.kc_end, "—", f["kc"]),
        ("fases", "Lini/Ldev/Lmid/Llate", "Duração das fases do Kc", "/".join(str(x) for x in par.fases_dias), "d", f["fases"]),
        ("L", "L", "Lâmina fixa de E1 (sensibilidade de 5 a 30 mm)", par.lamina_e1_mm, "mm", f["premissa"]),
        ("A", "A", "Área do canteiro (1 mm = 10 L)", par.area_m2, "m²", f["premissa"]),
        ("cenarios", "V / N", "Capacidade e intervalo de reposição dos cenários", "1.000/3; 500/7; 500/14", "L / d", f["cenarios"]),
        ("z_anemometro", "z_u", "Altura do anemômetro", 10.0, "m", f["vento"]),
    ]
    registros, md_linhas = [], []
    for chave, simb, sig, valor, unid, fonte in linhas:
        if chave == "cenarios":
            valor = "; ".join(f"{int(CENARIOS[c].capacidade_l)}/{CENARIOS[c].intervalo_dias}" for c in CENARIOS_ORDEM)
            valor_md = "; ".join(f"{num(CENARIOS[c].capacidade_l, 0)}/{CENARIOS[c].intervalo_dias}" for c in CENARIOS_ORDEM)
        elif isinstance(valor, float):
            valor_md = num(valor, CASAS_PARAMETROS[chave])
        else:
            valor_md = str(valor)
        registros.append((chave, {"simbolo": simb, "significado": sig, "valor": valor, "unidade": unid, "fonte": fonte}))
        md_linhas.append([simb, sig, valor_md, unid, fonte])
    md = tabela_markdown(["Símbolo", "Significado", "Valor", "Unidade", "Fonte"], md_linhas, ["e", "e", "d", "e", "e"],
                         titulo="**Parâmetros do modelo v2**",
                         notas=["Derivados calculados pelo código. Fontes completas em docs/FONTES_PARAMETROS.md."])
    esc.tabela("tab_parametros", "parâmetros do modelo e fontes", par,
               ["simbolo", "significado", "valor", "unidade", "fonte"], registros, md)


CASAS_PARAMETROS = {
    "theta_cc": 2, "theta_pmp": 2, "theta_sat": 2, "p": 2, "z1": 1, "z2": 1, "f_ext2": 1, "theta0": 2,
    "taw": 1, "raw": 1, "theta_lim": 3, "kc_ini": 2, "kc_mid": 2, "kc_end": 2, "L": 1, "A": 0, "z_anemometro": 0,
}

FONTES_PARAMETROS = {
    "solo": "FAO-56, Tabela 19 (solo franco: θcc 0,20–0,30; θpmp 0,07–0,17); página [A CONFIRMAR PELO AUTOR]",
    "p": "FAO-56, Tabela 22 (alface, p = 0,30)",
    "z1": "Marouelli et al. (2008), página [A CONFIRMAR PELO AUTOR]; FAO-56, Tabela 22 (0,3–0,5 m)",
    "kc": "FAO-56, Tabela 12",
    "fases": "FAO-56, Tabela 11 (alface 20/30/15/10 d), escalonada a 70 d",
    "derivado": "derivado (calculado pelo código)",
    "premissa": "premissa do modelo",
    "premissa_sem_efeito": "premissa do modelo, sem efeito nas métricas (teste)",
    "cenarios": "premissa de cenário",
    "vento": "INMET, NT 001/2011 (mastro de 10 m); anemômetro no topo, premissa",
}


def tab_cenarios(esc: Escritor) -> None:
    par = esc.res.par
    registros, md = [], []
    for nome in CENARIOS_ORDEM:
        c = CENARIOS[nome]
        reposicoes = sum(1 for d in range(1, par.duracao_ciclo_dias + 1) if (d - 1) % c.intervalo_dias == 0)
        r = {"cenario": nome, "capacidade_l": c.capacidade_l, "intervalo_dias": c.intervalo_dias,
             "oferta_maxima_mm_dia": c.oferta_maxima_mm_dia(par.area_m2), "reposicoes_no_ciclo": reposicoes,
             "oferta_no_ciclo_mm": c.capacidade_l * reposicoes / par.area_m2}
        registros.append((nome, r))
        md.append([nome, num(c.capacidade_l, 0), inteiro(c.intervalo_dias), num(r["oferta_maxima_mm_dia"]),
                   inteiro(reposicoes), num(r["oferta_no_ciclo_mm"])])
    texto = tabela_markdown(["Cenário", "Capacidade (L)", "Intervalo (d)", "Oferta máxima (mm/d)",
                             "Reposições no ciclo", "Oferta no ciclo (mm)"], md, titulo="**Cenários de reservatório**",
                            notas=notas("Oferta", extra=[
                                "Reservatório cheio às 00:00 do dia 1 e reposto às 00:00 dos dias 1 + N, 1 + 2N, …; "
                                f"área do canteiro de {num(par.area_m2, 0)} m²."]))
    esc.tabela("tab_cenarios", "cenários de reservatório", par, list(registros[0][1]), registros, texto)


CAMPOS_DESEMPENHO = [
    "cenario", "estrategia", "aplicada_mm", "acionamentos", "lamina_media_mm", "percolacao_mm",
    "percolacao_incremental_mm", "eficiencia_incremental_pct", "tse_pct", "tse_diaria_pct", "eta_etc_pct",
    "dr_max_mm", "theta1_min", "dias_reservatorio_vazio", "primeiro_dia_vazio", "eta_mm", "etc_mm",
    "erro_balanco_mm",
]


def _registro_metricas(m: Metricas) -> dict:
    return {
        "cenario": m.cenario, "estrategia": m.estrategia, "aplicada_mm": m.aplicada_mm, "acionamentos": m.acionamentos,
        "lamina_media_mm": m.lamina_media_mm, "percolacao_mm": m.percolacao_mm,
        "percolacao_incremental_mm": m.percolacao_incremental_mm,
        "eficiencia_incremental_pct": m.eficiencia_incremental_pct, "tse_pct": m.tse_pct,
        "tse_diaria_pct": m.tse_diaria_pct, "eta_etc_pct": m.eta_etc_pct, "dr_max_mm": m.dr_max_mm,
        "theta1_min": m.theta1_min, "dias_reservatorio_vazio": m.dias_reservatorio_vazio,
        "primeiro_dia_vazio": m.primeiro_dia_vazio, "eta_mm": m.eta_mm, "etc_mm": m.etc_mm,
        "erro_balanco_mm": m.erro_balanco_mm,
    }


def _linha_md_desempenho(m: Metricas) -> List[str]:
    seq = m.estrategia == SEQUEIRO
    return [
        TRACO if seq else m.cenario, m.estrategia, num(m.aplicada_mm), inteiro(m.acionamentos),
        num(m.percolacao_incremental_mm) if not seq else f"({num(m.percolacao_mm)})",
        num(m.eficiencia_incremental_pct), num(m.tse_pct), num(m.eta_etc_pct), num(m.dr_max_mm),
        inteiro(m.dias_reservatorio_vazio),
    ]


def tab_desempenho(esc: Escritor, ciclo: str) -> None:
    res = esc.res
    registros, md = [], []
    for cen in CENARIOS_ORDEM:
        for e in ESTRATEGIAS:
            m = res.principal[(ciclo, cen, e)].metricas
            registros.append((f"{cen}|{e}", _registro_metricas(m)))
            md.append(_linha_md_desempenho(m))
    seq = res.sequeiro[ciclo].metricas
    registros.append((SEQUEIRO, _registro_metricas(seq)))
    md.append(_linha_md_desempenho(seq))
    texto = tabela_markdown(
        ["Cenário", "Estr.", "Aplicada (mm)", "Acion.", "Perc. incr. (mm)", "Efic. (%)", "TSE (%)", "ETa/ETc (%)",
         "Dr máx (mm)", "Dias vazio"], md, ["e", "e"] + ["d"] * 8,
        titulo=f"**Desempenho das estratégias, ciclo {NOME_CICLO[ciclo].lower()} "
               f"({res.ciclos[ciclo].inicio:%d/%m} a {res.ciclos[ciclo].fim:%d/%m/%Y})**",
        notas=notas("E1", "E2", "E3", "Acion", "Perc", "Efic", "TSE", "ETa", "Dr", "Vazio", extra=[
            "Na linha do sequeiro, entre parênteses, a percolação total, que é a referência da percolação incremental.",
            f"RAW = {num(res.par.raw_mm)} mm; TAW = {num(res.par.taw_mm)} mm; {inteiro(len(res.forcantes[ciclo]))} horas."]))
    esc.tabela(f"tab_desempenho_{ciclo}", f"desempenho das estratégias, ciclo {ciclo}", res.par, CAMPOS_DESEMPENHO, registros, texto)


def tab_sensibilidade_e1(esc: Escritor) -> None:
    res = esc.res
    campos = ["ciclo", "estrategia", "lamina_e1_mm"] + CAMPOS_DESEMPENHO[2:]
    registros, md = [], []
    for ciclo in CICLOS:
        for L in LAMINAS_E1_MM:
            m = res.sens_e1[(ciclo, L)].metricas
            registros.append((f"{ciclo}|{L:g}", {"ciclo": ciclo, "lamina_e1_mm": L, **_registro_metricas(m)}))
            md.append([NOME_CICLO[ciclo], "E1", num(L, 0), num(m.aplicada_mm), inteiro(m.acionamentos),
                       num(m.percolacao_incremental_mm), num(m.eficiencia_incremental_pct), num(m.tse_pct),
                       num(m.eta_etc_pct), num(m.dr_max_mm)])
        m2 = res.principal[(ciclo, "Abundante", "E2")].metricas
        registros.append((f"{ciclo}|E2", {"ciclo": ciclo, "lamina_e1_mm": None, **_registro_metricas(m2)}))
        md.append([NOME_CICLO[ciclo], "E2", TRACO, num(m2.aplicada_mm), inteiro(m2.acionamentos),
                   num(m2.percolacao_incremental_mm), num(m2.eficiencia_incremental_pct), num(m2.tse_pct),
                   num(m2.eta_etc_pct), num(m2.dr_max_mm)])
    texto = tabela_markdown(
        ["Ciclo", "Estr.", "L (mm)", "Aplicada (mm)", "Acion.", "Perc. incr. (mm)", "Efic. (%)", "TSE (%)",
         "ETa/ETc (%)", "Dr máx (mm)"], md, ["e", "e"] + ["d"] * 8,
        titulo="**Sensibilidade de E1 à lâmina fixa (cenário abundante), com E2 como referência**",
        notas=notas("E1", "E2", "Acion", "Perc", "Efic", "TSE", "ETa", "Dr"))
    esc.tabela("tab_sensibilidade_e1", "sensibilidade de E1 à lâmina (cenário abundante) e E2 de referência",
               res.par, campos, registros, texto)


def tab_varredura(esc: Escritor) -> None:
    res = esc.res
    campos = ["ciclo", "intervalo_dias", "capacidade_l", "estrategia", "oferta_mm_dia", "atende_tse_90"] + CAMPOS_DESEMPENHO[2:]
    registros, md = [], []
    for ciclo in CICLOS:
        for n in INTERVALOS_DIAS:
            for cap in CAPACIDADES_L:
                for e in ESTRATEGIAS:
                    m = res.varredura[(ciclo, n, cap, e)]
                    oferta = cap / (n * res.par.area_m2)
                    registros.append((f"{ciclo}|{n}|{int(cap)}|{e}", {
                        "ciclo": ciclo, "intervalo_dias": n, "capacidade_l": cap, "oferta_mm_dia": oferta,
                        "atende_tse_90": m.tse_pct >= LIMIAR_TSE_CAPACIDADE_PCT, **_registro_metricas(m)}))
                    md.append([NOME_CICLO[ciclo], inteiro(n), num(cap, 0), e, num(oferta), num(m.tse_pct),
                               num(m.eta_etc_pct), num(m.aplicada_mm), num(m.percolacao_incremental_mm),
                               inteiro(m.dias_reservatorio_vazio)])
    texto = tabela_markdown(
        ["Ciclo", "Intervalo (d)", "Capacidade (L)", "Estr.", "Oferta (mm/d)", "TSE (%)", "ETa/ETc (%)",
         "Aplicada (mm)", "Perc. incr. (mm)", "Dias vazio"], md, ["e", "d", "d", "e"] + ["d"] * 6,
        titulo="**Varredura do reservatório (250 a 2.000 L, passo de 250 L)**",
        notas=notas("Oferta", "TSE", "ETa", "Perc", "Vazio", "E1", "E2", "E3"))
    esc.tabela("tab_varredura_reservatorio", "varredura do reservatório: 2 ciclos × 3 intervalos × 8 capacidades × 3 estratégias",
               res.par, campos, registros, texto)


def tab_capacidade_minima(esc: Escritor) -> None:
    res = esc.res
    campos = ["ciclo", "intervalo_dias", "estrategia", "capacidade_minima_l", "capacidade_minima_texto",
              "oferta_mm_dia", "tse_pct", "eta_etc_pct", "capacidade_referencia_l"]
    registros, md = [], []
    for ciclo in CICLOS:
        for n in INTERVALOS_DIAS:
            for e in ESTRATEGIAS:
                c = res.capacidade_minima[(ciclo, n, e)]
                registros.append((f"{ciclo}|{n}|{e}", {
                    "ciclo": ciclo, "intervalo_dias": n, "estrategia": e, "capacidade_minima_l": c["capacidade_l"],
                    "capacidade_minima_texto": c["texto"], "oferta_mm_dia": c["oferta_mm_dia"], "tse_pct": c["tse_pct"],
                    "eta_etc_pct": c["eta_etc_pct"], "capacidade_referencia_l": c["capacidade_referencia_l"]}))
                marca = "" if c["capacidade_l"] is not None else "ᵃ"
                md.append([NOME_CICLO[ciclo], inteiro(n), e, c["texto"], num(c["oferta_mm_dia"]),
                           num(c["tse_pct"]) + marca, num(c["eta_etc_pct"]) + marca])
    texto = tabela_markdown(
        ["Ciclo", "Intervalo (d)", "Estr.", "Capacidade mínima", "Oferta (mm/d)", "TSE (%)", "ETa/ETc (%)"], md,
        ["e", "d", "e", "d", "d", "d", "d"],
        titulo=f"**Capacidade mínima do reservatório para TSE ≥ {num(LIMIAR_TSE_CAPACIDADE_PCT, 0)}%**",
        notas=notas("TSE", "ETa", "Oferta", "E1", "E2", "E3", extra=[
            f"Varredura de {num(CAPACIDADES_L[0], 0)} a {num(CAPACIDADES_L[-1], 0)} L, passo de "
            f"{num(CAPACIDADES_L[1] - CAPACIDADES_L[0], 0)} L. Capacidade mínima = menor capacidade da varredura "
            f"com TSE ≥ {num(LIMIAR_TSE_CAPACIDADE_PCT, 0)}%."] + (
            [f"ᵃ Nenhuma capacidade da varredura atendeu; TSE e ETa/ETc obtidos com {num(CAPACIDADES_L[-1], 0)} L."]
            if any(c["capacidade_l"] is None for c in res.capacidade_minima.values()) else [])))
    esc.tabela("tab_capacidade_minima", "capacidade mínima do reservatório para TSE >= 90%", res.par, campos, registros, texto)


def tab_comparacao_v1_v2(esc: Escritor) -> None:
    res = esc.res
    campos = ["ciclo", "cenario", "estrategia", "conforto_v1_pct", "tse_v2_pct", "tse_diaria_v2_pct",
              "aplicada_v1_mm", "aplicada_v2_mm", "acionamentos_v1", "acionamentos_v2",
              "percolacao_incremental_v1_mm", "percolacao_incremental_v2_mm"]
    registros, md = [], []
    for ciclo in CICLOS:
        for cen in CENARIOS_ORDEM:
            for e in ESTRATEGIAS:
                v1 = res.v1.metricas[(ciclo, cen, e)]
                m = res.principal[(ciclo, cen, e)].metricas
                r = {"ciclo": ciclo, "cenario": cen, "estrategia": e,
                     "conforto_v1_pct": v1["conforto_hidrico_pct"], "tse_v2_pct": m.tse_pct,
                     "tse_diaria_v2_pct": m.tse_diaria_pct, "aplicada_v1_mm": v1["lamina_total_mm"],
                     "aplicada_v2_mm": m.aplicada_mm, "acionamentos_v1": v1["numero_acionamentos"],
                     "acionamentos_v2": m.acionamentos, "percolacao_incremental_v1_mm": v1["d2_incremental_mm"],
                     "percolacao_incremental_v2_mm": m.percolacao_incremental_mm}
                registros.append((f"{ciclo}|{cen}|{e}", r))
                md.append([NOME_CICLO[ciclo], cen, e, num(r["conforto_v1_pct"]), num(m.tse_pct), num(m.tse_diaria_pct),
                           num(r["aplicada_v1_mm"]), num(m.aplicada_mm), inteiro(r["acionamentos_v1"]),
                           inteiro(m.acionamentos), num(r["percolacao_incremental_v1_mm"]),
                           num(m.percolacao_incremental_mm)])
    texto = tabela_markdown(
        ["Ciclo", "Cenário", "Estr.", "Conforto v1 (% dias)", "TSE v2 (% horas)", "TSE diário v2 (% dias)",
         "Aplicada v1 (mm)", "Aplicada v2 (mm)", "Acion. v1", "Acion. v2", "Perc. incr. v1 (mm)",
         "Perc. incr. v2 (mm)"], md, ["e", "e", "e"] + ["d"] * 9,
        titulo="**Comparação v1 × v2**",
        notas=notas("TSE", "TSEd", "Acion", "Perc", "E1", "E2", "E3", extra=[
            "Conforto v1 = % dos dias com θ₁ ≥ θlim no fim do dia (passo diário, p = 0,35). "
            "TSE diário v2 = mesma ideia de medida por dia, recalculada na série horária do v2.",
            "No v1 um acionamento é um dia com irrigação; no v2, uma hora com irrigação."]))
    esc.tabela("tab_comparacao_v1_v2", "comparação v1 × v2 por ciclo, cenário e estratégia", res.par, campos, registros, texto)


def tab_sensibilidade_z1(esc: Escritor) -> None:
    res = esc.res
    metricas_z = ("tse_pct", "eta_etc_pct", "aplicada_mm", "acionamentos", "percolacao_incremental_mm", "dr_max_mm")
    campos = ["ciclo", "cenario", "estrategia"] + [f"{m}_z1_{int(z)}" for m in metricas_z for z in (res.par.z1_mm, res.par_z1.z1_mm)]
    registros, md = [], []
    chaves = [(ciclo, cen, e) for ciclo in CICLOS for cen in CENARIOS_ORDEM for e in ESTRATEGIAS] + \
             [(ciclo, SEQUEIRO, SEQUEIRO) for ciclo in CICLOS]
    for ciclo, cen, e in chaves:
        if e == SEQUEIRO:
            m200, m300 = res.sequeiro[ciclo].metricas, res.sequeiro_z1[ciclo].metricas
        else:
            m200, m300 = res.principal[(ciclo, cen, e)].metricas, res.z1[(ciclo, cen, e)].metricas
        r = {"ciclo": ciclo, "cenario": cen, "estrategia": e}
        for mz in metricas_z:
            r[f"{mz}_z1_{int(res.par.z1_mm)}"] = getattr(m200, mz)
            r[f"{mz}_z1_{int(res.par_z1.z1_mm)}"] = getattr(m300, mz)
        registros.append((f"{ciclo}|{cen}|{e}", r))
        md.append([NOME_CICLO[ciclo], TRACO if e == SEQUEIRO else cen, e,
                   num(m200.tse_pct), num(m300.tse_pct), num(m200.eta_etc_pct), num(m300.eta_etc_pct),
                   num(m200.aplicada_mm), num(m300.aplicada_mm), inteiro(m200.acionamentos), inteiro(m300.acionamentos),
                   num(m200.percolacao_incremental_mm) if e != SEQUEIRO else TRACO,
                   num(m300.percolacao_incremental_mm) if e != SEQUEIRO else TRACO])
    z_a, z_b = num(res.par.z1_mm, 0), num(res.par_z1.z1_mm, 0)
    texto = tabela_markdown(
        ["Ciclo", "Cenário", "Estr.", f"TSE {z_a}", f"TSE {z_b}", f"ETa/ETc {z_a}", f"ETa/ETc {z_b}",
         f"Aplicada {z_a}", f"Aplicada {z_b}", f"Acion. {z_a}", f"Acion. {z_b}", f"Perc. incr. {z_a}",
         f"Perc. incr. {z_b}"], md, ["e", "e", "e"] + ["d"] * 10,
        titulo=f"**Sensibilidade à profundidade da zona radicular (z₁ = {z_a} mm × {z_b} mm)**",
        notas=notas("TSE", "ETa", "Acion", "Perc", "E1", "E2", "E3", extra=[
            f"TSE e ETa/ETc em %; aplicada e percolação em mm. Com z₁ = {z_b} mm: TAW = {num(res.par_z1.taw_mm)} mm, "
            f"RAW = {num(res.par_z1.raw_mm)} mm (com z₁ = {z_a} mm: {num(res.par.taw_mm)} e {num(res.par.raw_mm)} mm); "
            f"L de E1 = {num(res.par.lamina_e1_mm, 0)} mm nos dois casos."]))
    esc.tabela("tab_sensibilidade_z1", f"sensibilidade a z1 = {z_b} mm (rodada principal completa)", res.par_z1,
               campos, registros, texto, metadados_extra=[f"comparacao: z1 = {res.par.z1_mm:g} mm (padrão) × {res.par_z1.z1_mm:g} mm"])


def tab_diagnosticos(esc: Escritor) -> None:
    res = esc.res
    itens = [
        ("kc_mid_ajustado", "Kc,mid com o ajuste climático (eq. 62; h = 0,3 m)", "—", 3),
        ("kc_mid_diferenca", "Diferença para o Kc,mid da Tabela 12", "—", 3),
        ("u2_medio_fase_media_ms", "u₂ médio da fase média", "m/s", 2),
        ("urmin_media_fase_media_pct", "URmin média da fase média", "%", 1),
        ("etc_diaria_min_mm", "ETc diária mínima", "mm/d", 2),
        ("etc_diaria_max_mm", "ETc diária máxima", "mm/d", 2),
        ("p_ajustado_min", "p ajustado pela ETc diária, mínimo", "—", 2),
        ("p_ajustado_max", "p ajustado pela ETc diária, máximo", "—", 2),
        ("et0_negativa_horas", "Horas com ET0 horária negativa (zerada)", "h", 0),
        ("et0_negativa_soma_mm", "Soma da ET0 negativa zerada", "mm", 2),
        ("et0_pm_mm", "ΣET0 PM adotada (ω₁, ω₂ limitados a ±ωs)", "mm", 1),
        ("et0_pm_ra_pelo_meio_mm", "ΣET0 PM com Ra zerada pelo meio da hora (texto do FAO-56)", "mm", 1),
        ("rs_rso_bruta_max_ciclo", "Rs/Rso bruta máxima (horas com Ra > 1,5 MJ m⁻² h⁻¹)", "—", 3),
        ("rs_rso_bruta_p99_ciclo", "Rs/Rso bruta, percentil 99 (mesmas horas)", "—", 3),
    ]
    registros, md = [], []
    for chave, descricao, unidade, casas in itens:
        valores = {c: getattr(res.diagnosticos[c], chave) for c in CICLOS}
        for c in CICLOS:
            registros.append((f"{chave}|{c}", {"diagnostico": chave, "descricao": descricao, "escopo": c,
                                               "valor": valores[c], "unidade": unidade}))
        fmt = (lambda v: inteiro(v)) if casas == 0 else (lambda v, k=casas: ("+" if chave == "kc_mid_diferenca" and v > 0 else "") + num(v, k))
        md.append([descricao, unidade] + [fmt(valores[c]) for c in CICLOS])
    ano = res.rs_rso_ano
    for chave, descricao, casas, unidade in (("maximo", "Rs/Rso bruta máxima no ano (Ra > 1,5 MJ m⁻² h⁻¹)", 3, "—"),
                                             ("p99", "Rs/Rso bruta, percentil 99 no ano", 3, "—"),
                                             ("n_horas", "Horas do ano com Ra > 1,5 MJ m⁻² h⁻¹", 0, "h"),
                                             ("acima_de_1", "Dessas horas, com Rs/Rso bruta > 1 (limitadas a 1)", 0, "h")):
        registros.append((f"rs_rso_ano_{chave}|2023", {"diagnostico": f"rs_rso_ano_{chave}", "descricao": descricao,
                                                       "escopo": "ano_2023", "valor": ano[chave], "unidade": unidade}))
        v = inteiro(ano[chave]) if casas == 0 else num(ano[chave], casas)
        md.append([descricao, unidade, v, v])
    texto = tabela_markdown(["Diagnóstico", "Unidade", "Chuvoso", "Seco"], md, ["e", "e", "d", "d"],
                            titulo="**Diagnósticos (grandezas que o modelo não aplica)**",
                            notas=[f"Fase média do Kc: dias {res.diagnosticos['seco'].dias_fase_media[0]} a "
                                   f"{res.diagnosticos['seco'].dias_fase_media[-1]} do ciclo. p ajustado = 0,30 + "
                                   "0,04·(5 − ETc), limitado a 0,1–0,8 (FAO-56, Tabela 22). As linhas \"no ano\" valem "
                                   "para 2023 inteiro e aparecem iguais nas duas colunas."])
    esc.tabela("tab_diagnosticos", "diagnósticos para as limitações (formato longo)", res.par,
               ["diagnostico", "descricao", "escopo", "valor", "unidade"], registros, texto)


def tab_afirmacoes(esc: Escritor) -> None:
    res = esc.res
    por_chave = {(c.ano, c.janela): c for c in res.completude}
    registros, md = [], []
    for i, (ano, janela, grandeza, afirmado, descricao) in enumerate(AFIRMACOES_ARTIGO):
        c = por_chave.get((ano, janela))
        obtido = getattr(c, grandeza) if c else None
        esperado = (c.dias if c else None) if afirmado is None else afirmado
        confere = None if c is None else ("sim" if obtido == esperado else "não")
        registros.append((str(i), {"afirmacao": descricao, "ano": ano, "janela": janela, "grandeza": grandeza,
                                   "valor_afirmado": esperado, "valor_obtido": obtido,
                                   "confere": confere if confere else "[A CONFIRMAR PELO AUTOR]"}))
        md.append([descricao, inteiro(esperado) if esperado is not None else "todos os dias",
                   inteiro(obtido) if obtido is not None else "[A CONFIRMAR PELO AUTOR]",
                   confere or "[A CONFIRMAR PELO AUTOR]"])
    texto = tabela_markdown(["Afirmação do artigo", "Valor afirmado", "Valor no arquivo do INMET", "Confere?"], md,
                            ["e", "d", "d", "e"], titulo="**Conferência das afirmações sobre 2024 e 2025**",
                            notas=["Dias locais; \"sem registro\" = nenhuma variável em nenhuma hora do dia. Sem o arquivo do "
                                   "ano, a afirmação fica a confirmar (nada é estimado)."])
    esc.tabela("tab_afirmacoes_anos_vizinhos", "conferência das afirmações do artigo sobre 2024 e 2025", res.par,
               ["afirmacao", "ano", "janela", "grandeza", "valor_afirmado", "valor_obtido", "confere"], registros, texto)


def tab_dados_externos(esc: Escritor) -> None:
    res = esc.res
    registros, md = [], []
    for i, s in enumerate(res.externos):
        situacao = "presente e registrado" if s.presente and s.registrado else (
            "presente, sem SHA-256 registrado (rode python3 main.py dados --preparar)" if s.presente else "ausente")
        registros.append((str(i), {"descricao": s.descricao, "destino": s.destino, "url": s.url, "situacao": situacao}))
        md.append([s.descricao, f"`{s.destino}`", s.url, situacao])
    texto = tabela_markdown(["Arquivo", "Pasta de destino", "URL", "Situação"], md, ["e", "e", "e", "e"],
                            titulo="**Dados externos**",
                            notas=["Arquivos ausentes não são estimados. Depois de baixá-los, rode "
                                   "`python3 main.py dados --preparar` e `python3 main.py pipeline`."])
    esc.tabela("tab_dados_externos", "situação dos arquivos externos (normal e anos vizinhos)", res.par,
               ["descricao", "destino", "url", "situacao"], registros, texto)


def tab_normal(esc: Escritor) -> None:
    res = esc.res
    campos = ["ciclo", "meses_e_pesos", "normal_jan_mm", "normal_fev_mm", "normal_mar_mm", "normal_jul_mm",
              "normal_ago_mm", "normal_set_mm", "normal_janela_mm", "chuva_2023_mm", "chuva_sobre_normal_pct",
              "estacao_normal", "arquivo", "sha256", "situacao"]
    registros, md = [], []
    for ciclo in CICLOS:
        pesos = PESOS_JANELA_NORMAL[ciclo]
        chuva = sum(h.p_mm for h in res.ciclos[ciclo].horas)
        n = res.normal
        normal = n.janela(pesos) if n else None
        mensal = n.mensal_mm if n else {}
        r = {"ciclo": ciclo,
             "meses_e_pesos": "; ".join(f"{m}:{w:.6f}" for m, w in pesos.items()),
             **{f"normal_{nome}_mm": mensal.get(m) for m, nome in ((1, "jan"), (2, "fev"), (3, "mar"), (7, "jul"), (8, "ago"), (9, "set"))},
             "normal_janela_mm": normal, "chuva_2023_mm": chuva,
             "chuva_sobre_normal_pct": chuva / normal * 100 if normal else None,
             "estacao_normal": f"{n.nome} ({n.codigo})" if n else None, "arquivo": n.arquivo if n else None,
             "sha256": n.sha256 if n else None, "situacao": "calculada" if n else res.normal_situacao}
        registros.append((ciclo, r))
        pend = "[A CONFIRMAR PELO AUTOR]"
        md.append([NOME_CICLO[ciclo], num(chuva), num(normal) if normal is not None else pend,
                   num(r["chuva_sobre_normal_pct"]) if normal else pend])
    notas_md = [
        "Normal da janela = soma proporcional por dias: chuvoso = jan × 17/31 + fev × 28/28 + mar × 25/31; "
        "seco = jul + ago + set × 8/30. Fonte: " + "INMET, Normais climatológicas do Brasil 1991-2020 (2022).",
    ]
    if not res.normal:
        notas_md.append(f"Normal não calculada: {res.normal_situacao}")
    texto = tabela_markdown(["Ciclo", "P 2023 (mm)", "Normal 1991–2020 (mm)", "P/normal (%)"], md,
                            titulo="**Chuva dos ciclos de 2023 × normal climatológica 1991–2020 (Balsas-MA)**", notas=notas_md)
    esc.tabela("tab_normal_climatologica", "chuva dos ciclos × normal 1991-2020", res.par, campos, registros, texto)


def tab_completude(esc: Escritor) -> None:
    res = esc.res
    campos = ["ano", "janela", "inicio", "fim", "dias", "dias_completos", "dias_parciais", "dias_sem_registro",
              "maior_lacuna_sem_registro_dias", "maior_sequencia_incompleta_dias", "horas_validas_pct", "arquivo", "sha256"]
    registros, md = [], []
    for c in res.completude:
        r = {"ano": c.ano, "janela": c.janela, "inicio": c.inicio, "fim": c.fim, "dias": c.dias,
             "dias_completos": c.dias_completos, "dias_parciais": c.dias_parciais, "dias_sem_registro": c.dias_sem_registro,
             "maior_lacuna_sem_registro_dias": c.maior_lacuna_sem_registro_dias,
             "maior_sequencia_incompleta_dias": c.maior_sequencia_incompleta_dias,
             "horas_validas_pct": 100.0 * c.horas_validas / (24 * c.dias), "arquivo": c.arquivo, "sha256": c.sha256}
        registros.append((f"{c.ano}|{c.janela}", r))
        md.append([str(c.ano), c.janela.replace("_", " "), f"{c.inicio:%d/%m} a {c.fim:%d/%m}", inteiro(c.dias),
                   inteiro(c.dias_completos), inteiro(c.dias_parciais), inteiro(c.dias_sem_registro),
                   inteiro(c.maior_lacuna_sem_registro_dias), num(r["horas_validas_pct"])])
    faltando = [s for s in res.externos if not s.descricao.startswith("Normal") and not (s.presente and s.registrado)]
    notas_md = ["Dia completo = 24 horas com todas as variáveis usadas no v2. Dia sem registro = nenhuma variável em "
                "nenhuma hora. Lacuna = dias consecutivos sem registro. Dias locais (UTC − 3); o último dia local do ano "
                "depende das 3 primeiras horas UTC do arquivo do ano seguinte."]
    for s in faltando:
        notas_md.append(f"{s.descricao}: [A CONFIRMAR PELO AUTOR], arquivo ausente (baixar de {s.url} para `{s.destino}`).")
    texto = tabela_markdown(["Ano", "Janela", "Período", "Dias", "Completos", "Parciais", "Sem registro",
                             "Maior lacuna (d)", "Horas válidas (%)"], md, ["d", "e", "e"] + ["d"] * 6,
                            titulo="**Completude da estação A204 nas janelas dos ciclos**", notas=notas_md)
    esc.tabela("tab_completude_anos", "completude da A204 por ano e janela", res.par, campos, registros, texto)


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------

def carregar_dados_externos(estacao: EstacaoINMET, registros_2023) -> Tuple[Optional[NormalEstacao], str, List[CompletudeJanela], List[StatusArquivo]]:
    externos = status_dados_externos()
    registro = ler_registro_sha256()
    normal, situacao = None, ""
    s_normal = externos[0]
    if not s_normal.presente:
        situacao = f"arquivo ausente; baixar de {s_normal.url} para {s_normal.destino}"
    elif not s_normal.registrado:
        situacao = f"{s_normal.destino} sem SHA-256 registrado; rode python3 main.py dados --preparar"
    else:
        try:
            normal = ler_normal_balsas()
            if registro.get("normais/" + os.path.basename(normal.arquivo)) != normal.sha256:
                normal, situacao = None, f"SHA-256 de {s_normal.destino} não confere com o registro"
        except FormatoNaoReconhecido as exc:
            situacao = f"planilha em formato não reconhecido ({exc})"
    completude = [completude_janela(estacao, registros_2023, 2023, nome, ini, fim)
                  for nome, (ini, fim) in janelas_do_ano(2023).items() if nome in ("chuvoso", "seco")]
    for ano in ANOS_VIZINHOS:
        caminho = arquivo_a204_do_ano(ano)
        if caminho and os.path.basename(caminho) in registro:
            completude += completude_ano(ano, caminho)
    return normal, situacao, completude, externos


def executar_pipeline(dir_saida: str = DIR_SAIDA_PADRAO, gravar_varredura: bool = True) -> Resultados:
    from src.v2 import relatorios

    t0 = time.perf_counter()
    dir_final = os.path.abspath(dir_saida)
    dir_tmp = dir_final + ".tmp"
    if os.path.exists(dir_tmp):
        shutil.rmtree(dir_tmp)
    os.makedirs(dir_tmp)

    estacao, registros = ler_arquivo_inmet()
    serie = montar_serie_horaria(estacao, registros)
    serie_alt = montar_serie_horaria(estacao, registros, ra_zerada_pelo_meio_da_hora=True)
    ciclos = {n: extrair_ciclo(serie, estacao, n, a, b) for n, (a, b) in CICLOS_2023.items()}
    ciclos_alt = {n: extrair_ciclo(serie_alt, estacao, n, a, b) for n, (a, b) in CICLOS_2023.items()}
    par = PARAMETROS_PADRAO
    par_z1 = par.com(z1_mm=Z1_SENSIBILIDADE_MM)
    forcantes = {n: forcante_do_ciclo(c) for n, c in ciclos.items()}

    series_gravadas: List[str] = []

    def gravar(rodada: Rodada, relativo: str, par_r: Optional[ParametrosModelo] = None) -> None:
        if not gravar_varredura and relativo.startswith(os.path.join("series", "varredura")):
            return
        caminho = os.path.join(dir_tmp, relativo)
        meta = metadados_base(estacao, par_r or rodada.parametros, "série horária de uma rodada") + [
            descricao_rodada(rodada), NOTA_COLUNAS_SERIE]
        gravar_serie_rodada(caminho, rodada, meta)
        series_gravadas.append(caminho)

    t_rod = time.perf_counter()
    principal, sequeiro = rodar_principal(forcantes, par)
    sens_e1 = rodar_sensibilidade_e1(forcantes, par, sequeiro)
    varredura, minima = rodar_varredura(forcantes, par, sequeiro, gravar)
    z1, sequeiro_z1 = rodar_z1(forcantes, par_z1)
    tempo_rodadas = time.perf_counter() - t_rod

    normal, normal_sit, completude, externos = carregar_dados_externos(estacao, registros)
    res = Resultados(
        raiz=dir_tmp, estacao=estacao, ciclos=ciclos, par=par, par_z1=par_z1, forcantes=forcantes,
        principal=principal, sequeiro=sequeiro, sens_e1=sens_e1, varredura=varredura, capacidade_minima=minima,
        z1=z1, sequeiro_z1=sequeiro_z1, v1=rodar_v1(LAMINAS_E1_MM),
        diagnosticos={n: diagnosticar_ciclo(ciclos[n], ciclos_alt[n], par) for n in CICLOS},
        rs_rso_ano=rs_rso_no_ano(serie), normal=normal, normal_situacao=normal_sit, completude=completude,
        externos=externos, tempo_rodadas_s=tempo_rodadas,
    )

    for ciclo in CICLOS:
        gravar(sequeiro[ciclo], os.path.join("series", "principal", f"{ciclo}_sequeiro.csv"))
        gravar(sequeiro_z1[ciclo], os.path.join("series", "sensibilidade_z1", f"{ciclo}_sequeiro.csv"))
        for cen in CENARIOS_ORDEM:
            for e in ESTRATEGIAS:
                gravar(principal[(ciclo, cen, e)], os.path.join("series", "principal", f"{ciclo}_{_slug(cen)}_{e}.csv"))
                gravar(z1[(ciclo, cen, e)], os.path.join("series", "sensibilidade_z1", f"{ciclo}_{_slug(cen)}_{e}.csv"))
        for L in LAMINAS_E1_MM:
            gravar(sens_e1[(ciclo, L)], os.path.join("series", "sensibilidade_e1", f"{ciclo}_abundante_E1_L{int(L):02d}.csv"))
        series_gravadas.extend(gravar_serie_clima(dir_tmp, ciclos[ciclo], par, metadados_base(
            estacao, par, f"clima horário e diário do ciclo {ciclo} (entrada do modelo, com os termos do Penman-Monteith)")))
    res.series = sorted(os.path.relpath(c, dir_tmp).replace(os.sep, "/") for c in series_gravadas)

    esc = Escritor(res, dir_tmp)
    tab_clima_ciclos(esc)
    tab_normal(esc)
    tab_parametros(esc)
    tab_cenarios(esc)
    for ciclo in CICLOS:
        tab_desempenho(esc, ciclo)
    tab_sensibilidade_e1(esc)
    tab_capacidade_minima(esc)
    tab_varredura(esc)
    tab_comparacao_v1_v2(esc)
    tab_sensibilidade_z1(esc)
    tab_diagnosticos(esc)
    tab_completude(esc)
    tab_afirmacoes(esc)
    tab_dados_externos(esc)

    dir_fig = os.path.join(dir_tmp, "figuras")
    meta_fig = metadados_base(estacao, par, "dados da figura")
    res.figuras["figura1"] = figuras.figura_sensibilidade_e1(
        sens_e1, {c: principal[(c, "Abundante", "E2")] for c in CICLOS}, LAMINAS_E1_MM, dir_fig, dir_tmp, meta_fig)
    res.figuras["figura2"] = figuras.figura_seco_restrito(
        {e: principal[("seco", "Restrito", e)] for e in ESTRATEGIAS}, par.raw_mm, par.taw_mm, dir_fig, dir_tmp, meta_fig)

    relatorios.gerar_documentos(res, dir_tmp, tempo_total_s=time.perf_counter() - t0)

    if os.path.exists(dir_final):
        shutil.rmtree(dir_final)
    os.replace(dir_tmp, dir_final)
    res.raiz = dir_final
    return res
