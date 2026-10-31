#!/usr/bin/env python3
"""
Simulador de irrigação PIC/FAPEMA (Edital COORD.NUPEX nº 01/2026).

Uso:
  python3 main.py pipeline               # modelo v2: resultados/v2/ e banco do painel
  python3 main.py pipeline --modelo v1   # modelo v1 (linha de base do parecer): resultados/v1/
  python3 main.py simular --ciclo chuvoso --cenario Abundante   # só recarrega o banco do painel
  python3 main.py serve                  # API e painel (não roda simulação)
  python3 main.py dados [--preparar]     # normal 1991–2020 e arquivos de 2024/2025
  python3 main.py conferir               # confere NUMEROS_ARTIGO.md e CHECKSUMS.txt

Variáveis de ambiente (veja .env.example): PORT, HOST, DB_PATH, DEVICE_TOKEN, CORS_ORIGIN.
Um arquivo .env na raiz é lido se existir; variáveis já definidas no ambiente têm prioridade.
"""

from __future__ import annotations

import argparse
import os
import secrets
import shutil
import sys
import time

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CICLOS = ("seco", "chuvoso")
CENARIOS = ("Restrito", "Moderado", "Abundante")


def carregar_env(caminho: str = os.path.join(ROOT_DIR, ".env")) -> None:
    """Lê CHAVE=VALOR de um .env sem sobrescrever o ambiente e sem imprimir valores."""
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            valor = valor.strip().strip('"').strip("'")
            if valor:
                os.environ.setdefault(chave.strip(), valor)


def caminho_banco() -> str:
    from src.database import DEFAULT_DB_PATH

    caminho = os.environ.get("DB_PATH") or DEFAULT_DB_PATH
    return caminho if os.path.isabs(caminho) else os.path.join(ROOT_DIR, caminho)


def preparar_banco(db_path: str) -> None:
    """Banco do v1 (token em texto puro): guarda uma cópia em backups/ e começa um banco novo."""
    from src.database import banco_no_formato_antigo

    if not banco_no_formato_antigo(db_path):
        return
    destino_dir = os.path.join(ROOT_DIR, "backups")
    os.makedirs(destino_dir, exist_ok=True)
    marca = time.strftime("%Y%m%d-%H%M%S")
    for sufixo in ("", "-wal", "-shm"):
        if os.path.exists(db_path + sufixo):
            shutil.move(db_path + sufixo, os.path.join(destino_dir, f"irrigacao_v1_{marca}.db{sufixo}"))
    print(f"  banco do v1 movido para backups/irrigacao_v1_{marca}.db (guardava o token em texto puro)")


def token_para_carga() -> str:
    """DEVICE_TOKEN, se definido (validado); senão, um token só desta carga, que ninguém conhece."""
    from src.seguranca import VARIAVEL_TOKEN, token_de_producao

    if os.environ.get(VARIAVEL_TOKEN):
        return token_de_producao()
    print(f"  {VARIAVEL_TOKEN} não definido: a carga usa um token temporário; o serve troca pelo seu DEVICE_TOKEN")
    return secrets.token_urlsafe(32)


def carregar_banco(ciclo: str, cenario: str) -> None:
    from src.v2.simulador import popular_banco

    db = caminho_banco()
    preparar_banco(db)
    res = popular_banco(db, token_para_carga(), ciclo=ciclo, cenario=cenario)
    nome_db = os.path.relpath(db, ROOT_DIR) if os.path.abspath(db).startswith(ROOT_DIR + os.sep) else db
    print(f"  banco {nome_db}: ciclo {ciclo}, cenário {cenario.lower()}; "
          f"leituras aceitas {res['leituras']['aceitos']} em {res['leituras']['lotes']} lotes, "
          f"eventos {res['eventos']['aceitos']}; reenvio de um lote: {res['reenvio']['ignorados']} ignoradas "
          "(idempotência)")


def comando_pipeline(args: argparse.Namespace) -> int:
    if args.modelo == "v1":
        from src.experiments import executar_estudo_completo

        t0 = time.perf_counter()
        estudo = executar_estudo_completo()
        cons = estudo["consolidado"]
        print("Modelo v1 (linha de base do parecer de 18/10/2026)")
        print("  resultados em resultados/v1/")
        print(f"  tabelas: {len(cons['arquivos_tabelas_csv'])} CSVs em tabelas/")
        print(f"  séries diárias: {len(cons['arquivos_rodadas_csv'])} CSVs em rodadas/")
        print(f"  figuras: {len(cons['figuras_geradas'])} em figuras/; relatório: relatorio_final.md")
        print(f"  tempo: {time.perf_counter() - t0:.1f} s")
        return 0

    from src.v2.pipeline import executar_pipeline

    t0 = time.perf_counter()
    res = executar_pipeline()
    print("Modelo v2: resultados em resultados/v2/")
    print(f"  tabelas: {len(res.tabelas)} (CSV + Markdown) em tabelas/")
    print(f"  séries horárias: {len(res.series)} CSVs em series/")
    print("  figuras: figura1_sensibilidade_e1 e figura2_seco_restrito (PNG + PDF + dados)")
    print("  documentos: NUMEROS_ARTIGO.md, RELATORIO.md, AMBIENTE.md, CHECKSUMS.txt, resultados.json")
    pendentes = [s for s in res.externos if not (s.presente and s.registrado)]
    for s in pendentes:
        print(f"  [A CONFIRMAR PELO AUTOR] {s.descricao}: baixar {s.url} para {s.destino}")
    if pendentes:
        print("  depois de baixar: python3 main.py dados --preparar && python3 main.py pipeline")
    if not args.sem_banco:
        codigo = carregar_banco_ou_erro(args.ciclo, args.cenario)
        if codigo:
            return codigo
    print(f"  tempo: {time.perf_counter() - t0:.1f} s")
    return 0


def carregar_banco_ou_erro(ciclo: str, cenario: str) -> int:
    from src.seguranca import TokenInvalido

    try:
        carregar_banco(ciclo, cenario)
    except TokenInvalido as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
    return 0


def comando_simular(args: argparse.Namespace) -> int:
    print("Carga do banco do painel (modelo v2)")
    return carregar_banco_ou_erro(args.ciclo, args.cenario)


def comando_serve(_args: argparse.Namespace) -> int:
    from src.api_server import iniciar_servidor
    from src.database import ler_simulacao
    from src.seguranca import TokenInvalido, token_de_producao

    try:
        token = token_de_producao()
    except TokenInvalido as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
    db = caminho_banco()
    host = os.environ.get("HOST", "127.0.0.1")
    try:
        porta = int(os.environ.get("PORT", "8000"))
    except ValueError:
        print("Erro: PORT precisa ser um número inteiro.", file=sys.stderr)
        return 2
    try:
        srv = iniciar_servidor(host=host, port=porta, db_path=db, token_dispositivo=token,
                               cors_origem=os.environ.get("CORS_ORIGIN") or None, registrar_acessos=True)
    except OSError as exc:
        print(f"Erro: não foi possível usar {host}:{porta} ({exc.strerror or exc}). "
              "A porta não é trocada automaticamente; defina outra em PORT.", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
    if ler_simulacao(db) is None:
        print("Aviso: o banco ainda não tem simulação carregada; rode python3 main.py pipeline.", file=sys.stderr)
    print(f"Painel e API em http://{host}:{porta}/ (banco {db}). Ctrl+C para encerrar.", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando.")
    finally:
        srv.server_close()
    return 0


def comando_dados(args: argparse.Namespace) -> int:
    from src.v2.dados_externos import preparar_dados_externos, status_dados_externos

    if args.preparar:
        for linha in preparar_dados_externos():
            print(linha)
    for s in status_dados_externos():
        situacao = "ok" if s.presente and s.registrado else ("sem SHA-256 registrado" if s.presente else "ausente")
        print(f"[{situacao}] {s.descricao}\n         destino: {s.destino}\n         URL: {s.url}")
    return 0


def comando_conferir(_args: argparse.Namespace) -> int:
    from src.v2.conferencia import (agrupar_pendencias, conferir_ambiente, conferir_checksums,
                                    conferir_numeros, pendencias)

    dir_res = os.path.join(ROOT_DIR, "resultados", "v2")
    n, erros = conferir_numeros(dir_res)
    print(f"NUMEROS_ARTIGO.md: {n} números conferidos contra os CSVs; {len(erros)} divergência(s)")
    for e in erros:
        print(f"  {e}")
    m, erros_c, nao_conferidos = conferir_checksums(dir_res)
    print(f"CHECKSUMS.txt: {m} CSVs; {len(erros_c)} divergência(s)"
          + (f"; {nao_conferidos} da varredura não conferidos (pasta fora do git, recriada por "
             "python3 main.py pipeline)" if nao_conferidos else ""))
    for e in erros_c:
        print(f"  {e}")
    ok_amb, gravada, atual = conferir_ambiente(dir_res)
    print(f"AMBIENTE.md: impressão digital do código {'confere' if ok_amb else 'NÃO confere'} com o código atual"
          + ("" if ok_amb else f" (gravada {gravada[:12] or '—'}…, atual {atual[:12]}…; rode python3 main.py pipeline)"))
    lista = pendencias()
    grupos = agrupar_pendencias(lista)
    print(f"[A CONFIRMAR PELO AUTOR]: {len(grupos)} assunto(s), {len(lista)} ocorrência(s)")
    for titulo, itens in grupos.items():
        print(f"  {titulo}: " + ", ".join(f"{a}:{l}" for a, l, _ in itens))
    return 1 if erros or erros_c or not ok_amb else 0


def main(argv=None) -> int:
    carregar_env()
    parser = argparse.ArgumentParser(description="Simulador de irrigação PIC/FAPEMA")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("pipeline", help="roda as simulações e gera tabelas, figuras, documentos e o banco do painel")
    p.add_argument("--modelo", choices=("v2", "v1"), default="v2", help="v2 (padrão) ou v1 (linha de base)")
    p.add_argument("--ciclo", choices=CICLOS, default="seco", help="ciclo carregado no banco do painel")
    p.add_argument("--cenario", choices=CENARIOS, default="Restrito", help="cenário carregado no banco do painel")
    p.add_argument("--sem-banco", action="store_true", help="não carrega o banco do painel")
    p.set_defaults(func=comando_pipeline)

    s = sub.add_parser("simular", help="só recarrega o banco do painel com outro ciclo ou cenário")
    s.add_argument("--ciclo", choices=CICLOS, default="seco")
    s.add_argument("--cenario", choices=CENARIOS, default="Restrito")
    s.set_defaults(func=comando_simular)

    sv = sub.add_parser("serve", help="serve a API e o painel (exige DEVICE_TOKEN)")
    sv.set_defaults(func=comando_serve)

    d = sub.add_parser("dados", help="situação dos arquivos externos (normal 1991–2020, 2024 e 2025)")
    d.add_argument("--preparar", action="store_true", help="extrai a A204 dos zips e registra os SHA-256")
    d.set_defaults(func=comando_dados)

    c = sub.add_parser("conferir", help="confere NUMEROS_ARTIGO.md e CHECKSUMS.txt e lista as pendências")
    c.set_defaults(func=comando_conferir)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
