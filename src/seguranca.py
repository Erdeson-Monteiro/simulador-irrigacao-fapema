"""
Tokens dos dispositivos.

- O token nunca fica no código nem no git: vem da variável de ambiente DEVICE_TOKEN.
- O banco guarda só o SHA-256 do token; a comparação é em tempo constante.
- Os dois tokens que estiveram no código até o v1 estão comprometidos. Aqui fica apenas o
  SHA-256 deles, para recusá-los como token de produção.
- Um banco novo criado sem token (uso pela biblioteca, como no teste de contrato HTTP) recebe
  para `sim-001` o SHA-256 do token de teste do contrato. `python3 main.py serve` troca esse
  hash pelo do DEVICE_TOKEN antes de aceitar qualquer requisição.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Optional


# SHA-256 dos tokens comprometidos (estiveram em src/simulator.py e src/database.py até a tag v1-parecer).
HASH_TOKEN_TESTE_CONTRATO = "d93ceaaac94e0d362221684d7c66e9fd4156dc6417ec856e292ba95f64739750"  # sim-001
HASHES_COMPROMETIDOS = frozenset({
    HASH_TOKEN_TESTE_CONTRATO,
    "b0feee106b6a7cbcefd2359c4cc9c3d22b397114d65e769ed1c2e92ae8e5f19d",  # esp32-001
})
TAMANHO_MINIMO_TOKEN = 24
VARIAVEL_TOKEN = "DEVICE_TOKEN"


class TokenInvalido(ValueError):
    """Token de produção ausente, curto demais ou comprometido."""


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def tokens_conferem(token_recebido: str, hash_armazenado: Optional[str]) -> bool:
    """Compara em tempo constante o SHA-256 do token recebido com o hash guardado."""
    if not hash_armazenado:
        return False
    return hmac.compare_digest(hash_token(token_recebido), hash_armazenado)


def token_de_producao(ambiente: Optional[dict] = None) -> str:
    """Lê e valida o DEVICE_TOKEN; nunca devolve nem registra o valor em mensagens de erro."""
    ambiente = os.environ if ambiente is None else ambiente
    token = (ambiente.get(VARIAVEL_TOKEN) or "").strip()
    if not token:
        raise TokenInvalido(
            f"Defina a variável de ambiente {VARIAVEL_TOKEN} (veja .env.example). Para gerar um token: "
            "python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    if hash_token(token) in HASHES_COMPROMETIDOS:
        raise TokenInvalido(f"O {VARIAVEL_TOKEN} informado é um token comprometido (esteve no código do v1). Gere outro.")
    if len(token) < TAMANHO_MINIMO_TOKEN:
        raise TokenInvalido(f"O {VARIAVEL_TOKEN} precisa ter pelo menos {TAMANHO_MINIMO_TOKEN} caracteres.")
    return token
