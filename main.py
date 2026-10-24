#!/usr/bin/env python3
"""
Orquestrador de Ponta a Ponta — Plataforma de Irrigação Automatizada e Simulação Hídrica
Projeto PIC/FAPEMA — Edital COORD.NUPEX nº 01/2026

Uso:
  python3 main.py            # Executa as Etapas 1 a 6 de ponta a ponta e gera todos os artefatos
  python3 main.py --serve    # Executa tudo e mantém o servidor HTTP + Painel Web ativo na porta 8000
"""

from __future__ import annotations
import argparse
import os
import threading
import time

from src.database import DEFAULT_DB_PATH, inicializar_banco, listar_canteiros
from src.experiments import (
    DEFAULT_CLIMATE_CSV,
    DEFAULT_REPORT_JSON,
    DEFAULT_REPORT_MD,
    executar_estudo_completo,
)
from src.simulator import executar_simulador
from src.api_server import iniciar_servidor


def executar_pipeline_completo(porta_teste: int = 18080) -> None:
    print("=" * 78)
    print("PLATAFORMA DE IRRIGAÇÃO AUTOMATIZADA E BALANÇO HÍDRICO — PIC/FAPEMA")
    print("=" * 78)

    # Etapa 1: Modelo de dados e contrato
    print("\n[Etapa 1/7] Inicializando banco de dados relacional (SQLite) e sementes...")
    inicializar_banco(DEFAULT_DB_PATH)
    print(f"  -> Banco pronto em: {DEFAULT_DB_PATH}")

    # Etapas 2, 3 e 4: Validação física, Série Climática INMET e Matriz de Estratégias
    print("\n[Etapas 2, 3 e 4/7] Executando validação física (Seção 6), série INMET Balsas-MA e simulações...")
    estudo = executar_estudo_completo(
        caminho_csv_clima=DEFAULT_CLIMATE_CSV,
        caminho_json_saida=DEFAULT_REPORT_JSON,
        caminho_md_saida=DEFAULT_REPORT_MD,
    )
    val = estudo["consolidado"]["validacao_secao6"]
    qual = estudo["consolidado"]["qualidade_serie_climatica"]
    print(
        f"  -> Teste 1 (Conservação de Massa): APROVADO "
        f"(erro = {val['teste_1_conservacao_massa']['erro_relativo_pct']:.6f}% < 0,1%)"
    )
    print(
        f"  -> Teste 2 (Secagem Monotônica):   APROVADO "
        f"(θ1 estabilizou em {val['teste_2_secagem_monotonica']['theta1_final']:.2f} = θ_pmp)"
    )
    print(
        f"  -> Teste 3 (Saturação Extrema):    APROVADO "
        f"(D2 = {val['teste_3_saturacao']['drenagem_profunda_d2_mm']:.2f} mm; θ <= θ_sat)"
    )
    print(
        f"  -> Série Climática INMET Balsas-MA: {qual['global']['total_dias']} dias processados "
        f"({qual['global']['percentual_falhas_global_pct']:.2f}% de falhas interpoladas)"
    )
    print(f"  -> Relatório científico salvo em: {DEFAULT_REPORT_MD}")

    # Etapas 5 e 6: Subir API HTTP e executar Simulador enviando lotes reais via HTTP
    print("\n[Etapas 5 e 6/7] Iniciando API de ingestão e transmitindo lotes do simulador via HTTP...")
    servidor = iniciar_servidor(host="127.0.0.1", port=porta_teste, db_path=DEFAULT_DB_PATH)
    th = threading.Thread(target=servidor.serve_forever, daemon=True)
    th.start()
    try:
        url_api = f"http://127.0.0.1:{porta_teste}"
        res_sim = executar_simulador(api_base_url=url_api, db_path=DEFAULT_DB_PATH)
        print(
            f"  -> Leituras enviadas ({res_sim['leituras']['lotes']} lotes): "
            f"aceitos={res_sim['leituras']['aceitos']}, ignorados={res_sim['leituras']['ignorados']}, "
            f"ultima_seq={res_sim['leituras']['ultima_sequencia']}"
        )
        print(
            f"  -> Eventos enviados  ({res_sim['eventos']['lotes']} lotes): "
            f"aceitos={res_sim['eventos']['aceitos']}, ignorados={res_sim['eventos']['ignorados']}, "
            f"ultima_seq={res_sim['eventos']['ultima_sequencia']}"
        )

        # Demonstração de idempotência: reenvio do lote não duplica registros
        res_reenvio = executar_simulador(api_base_url=url_api, db_path=DEFAULT_DB_PATH)
        print(
            f"  -> Verificação de idempotência (reenvio integral): "
            f"aceitos={res_reenvio['leituras']['aceitos']}, "
            f"ignorados={res_reenvio['leituras']['ignorados']}"
        )
    finally:
        servidor.shutdown()
        servidor.server_close()

    canteiros = listar_canteiros(DEFAULT_DB_PATH)
    print("\n[Etapa 7/7] Estado final do armazenamento para o Painel Web:")
    for c in canteiros:
        print(
            f"  -> {c['codigo']} ({c['nome']}): "
            f"{c['total_leituras']} leituras | {c['total_eventos']} eventos de irrigação"
        )
    print("\nPipeline concluído com sucesso!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plataforma de Irrigação PIC/FAPEMA")
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Mantém o servidor HTTP e o Painel Web ativos após executar o pipeline",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8000")),
        help="Porta HTTP do servidor (padrão: 8000)",
    )
    args = parser.parse_args()

    executar_pipeline_completo()

    if args.serve:
        porta_escolhida = args.port
        srv = None
        for tentativa in [args.port, 8080, 8081, 8888, 0]:
            try:
                srv = iniciar_servidor(host="0.0.0.0", port=tentativa, db_path=DEFAULT_DB_PATH)
                porta_escolhida = srv.server_address[1]
                break
            except OSError:
                continue
        if srv is None:
            raise RuntimeError("Não foi possível alocar uma porta HTTP disponível.")
        print(f"\n[Servidor Ativo] Acesse o Painel em: http://localhost:{porta_escolhida}", flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\nEncerrando servidor...")
            srv.server_close()


if __name__ == "__main__":
    main()
