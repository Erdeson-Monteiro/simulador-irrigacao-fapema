"""
Parâmetros do modelo v2 num único objeto de configuração (docs/MODELO.md, seção 3).

Os valores de base vêm da literatura ou são premissas declaradas (docs/FONTES_PARAMETROS.md).
Os derivados (TAW, RAW, θlim, fases escalonadas, armazenamentos) são calculados aqui, nunca
digitados. `como_dict()` devolve tudo, para ser gravado em cada arquivo de saída.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import math
from typing import Dict, Optional, Tuple


FASES_TABELA_11_ALFACE_DIAS = (20, 30, 15, 10)  # FAO-56, Tabela 11: alface (abril, Mediterrâneo), 75 d


def escalonar_fases(fases: Tuple[int, ...], duracao: int) -> Tuple[int, ...]:
    """Escalona as fases proporcionalmente à duração e arredonda pelo maior resto (a soma fecha)."""
    total = sum(fases)
    brutas = [f * duracao / total for f in fases]
    inteiras = [math.floor(b) for b in brutas]
    ordem = sorted(range(len(fases)), key=lambda i: (inteiras[i] - brutas[i], i))
    for i in ordem[: duracao - sum(inteiras)]:
        inteiras[i] += 1
    return tuple(inteiras)


@dataclass(frozen=True)
class ParametrosModelo:
    theta_cc: float = 0.28              # cm³ cm⁻³
    theta_pmp: float = 0.14             # cm³ cm⁻³
    theta_sat: float = 0.45             # cm³ cm⁻³ (premissa sem efeito; teste em test_v2_modelo)
    p: float = 0.30                     # FAO-56, Tabela 22 (alface)
    z1_mm: float = 200.0                # camada 1 (0–20 cm), zona radicular efetiva
    z2_mm: float = 200.0                # camada 2 (20–40 cm), abaixo da zona radicular
    f_ext2: float = 0.0                 # fração da extração (ETa) retirada da camada 2
    theta1_inicial: Optional[float] = None  # None = θcc (perfil na capacidade de campo no transplante)
    theta2_inicial: Optional[float] = None
    kc_ini: float = 0.70                # FAO-56, Tabela 12
    kc_mid: float = 1.00
    kc_end: float = 0.95
    fases_tabela_dias: Tuple[int, ...] = FASES_TABELA_11_ALFACE_DIAS
    duracao_ciclo_dias: int = 70
    lamina_e1_mm: float = 10.0          # premissa; sensibilidade de 5 a 30 mm
    area_m2: float = 10.0               # 1 mm sobre 10 m² = 10 L

    def com(self, **mudancas) -> "ParametrosModelo":
        return replace(self, **mudancas)

    @property
    def taw_mm(self) -> float:
        """TAW = (θcc − θpmp)·z₁."""
        return (self.theta_cc - self.theta_pmp) * self.z1_mm

    @property
    def raw_mm(self) -> float:
        """RAW = p·TAW."""
        return self.p * self.taw_mm

    @property
    def theta_lim(self) -> float:
        """θlim = θcc − p·(θcc − θpmp), a umidade em que Dr = RAW."""
        return self.theta_cc - self.p * (self.theta_cc - self.theta_pmp)

    @property
    def theta1_0(self) -> float:
        return self.theta_cc if self.theta1_inicial is None else self.theta1_inicial

    @property
    def theta2_0(self) -> float:
        return self.theta_cc if self.theta2_inicial is None else self.theta2_inicial

    @property
    def fases_dias(self) -> Tuple[int, ...]:
        return escalonar_fases(self.fases_tabela_dias, self.duracao_ciclo_dias)

    def kc(self, dia: int) -> float:
        """Curva de Kc do FAO-56 (eq. 66), constante dentro do dia; `dia` = 1..duração."""
        l_ini, l_dev, l_mid, l_late = self.fases_dias
        if dia <= l_ini:
            return self.kc_ini
        if dia <= l_ini + l_dev:
            return self.kc_ini + (dia - l_ini) / l_dev * (self.kc_mid - self.kc_ini)
        if dia <= l_ini + l_dev + l_mid:
            return self.kc_mid
        return self.kc_mid + (dia - (l_ini + l_dev + l_mid)) / l_late * (self.kc_end - self.kc_mid)

    def como_dict(self) -> Dict[str, object]:
        base = asdict(self)
        base["fases_tabela_dias"] = list(self.fases_tabela_dias)
        base.update({
            "theta1_inicial": self.theta1_0,
            "theta2_inicial": self.theta2_0,
            "taw_mm": self.taw_mm,
            "raw_mm": self.raw_mm,
            "theta_lim": self.theta_lim,
            "fases_dias": list(self.fases_dias),
            "s1_cc_mm": self.theta_cc * self.z1_mm,
            "s1_pmp_mm": self.theta_pmp * self.z1_mm,
            "s2_cc_mm": self.theta_cc * self.z2_mm,
        })
        return base

    def resumo(self) -> str:
        """Linha curta com todos os parâmetros, para cabeçalhos de arquivo."""
        d = self.como_dict()
        partes = []
        for k, v in d.items():
            if isinstance(v, float):
                v = f"{v:.6g}"
            elif isinstance(v, list):
                v = "/".join(str(x) for x in v)
            partes.append(f"{k}={v}")
        return "; ".join(partes)


@dataclass(frozen=True)
class Cenario:
    nome: str
    capacidade_l: float
    intervalo_dias: int

    def oferta_maxima_mm_dia(self, area_m2: float) -> float:
        return self.capacidade_l / (self.intervalo_dias * area_m2)


CENARIOS: Dict[str, Cenario] = {
    "Abundante": Cenario("Abundante", 1000.0, 3),
    "Moderado": Cenario("Moderado", 500.0, 7),
    "Restrito": Cenario("Restrito", 500.0, 14),
}

PARAMETROS_PADRAO = ParametrosModelo()
