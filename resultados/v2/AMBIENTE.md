# Ambiente de execução

**Ferramenta usada na simulação:** código próprio em Python (pacote `src/v2/` deste repositório), sem software de simulação de terceiros. O balanço hídrico, a ET0 de Penman-Monteith e o Hargreaves-Samani seguem as equações do FAO-56, implementadas em `src/v2/fao56.py` e conferidas contra o Exemplo 19 do FAO-56. As figuras usam matplotlib; o núcleo do modelo usa só a biblioteca padrão do Python.

| Item | Valor |
|---|---|
| Python | 3.12.3 |
| Implementação | CPython |
| Sistema operacional | Linux-6.17.0-29-generic-x86_64-with-glibc2.39 |
| Processador | x86_64 |
| SQLite | 3.45.1 |
| Fonte das figuras | LiberationSerif-Regular.ttf |
| Impressão digital do código (SHA-256 de src/, main.py, requirements.txt e data/raw/) | `d3fe1a05a09a470f6b69a40583d4cd53ca694fbcc0bb91c58e61f73dae2e2ac5` |
| Último commit do git que alterou o código | 35f218c0bbc7de63e76c8bfaf7e416676741e3e1 |
| Comando | `python3 main.py pipeline` |
| Rodadas simuladas | 196 |
| Tempo das rodadas | 5,4 s |
| Tempo total do pipeline | 8,9 s |

| Biblioteca | Versão |
|---|---|
| numpy | 2.5.4 |
| matplotlib | 3.11.2 |
| contourpy | 1.4.0 |
| cycler | 0.12.1 |
| fonttools | 4.67.0 |
| kiwisolver | 1.5.1 |
| packaging | 24.0 |
| pillow | 10.2.0 |
| pyparsing | 3.1.1 |
| python-dateutil | 2.8.2 |

Versões exatas de numpy e matplotlib fixadas em `requirements.txt`.

A impressão digital identifica exatamente o código e os dados que geraram estes resultados; `python3 main.py conferir` recalcula e compara com a do código atual.

O modelo é determinístico: não há gerador aleatório em nenhuma parte. Os CSVs não contêm data, hora, caminho absoluto nem hash de commit, e por isso os mesmos dados de entrada geram os mesmos SHA-256 (`CHECKSUMS.txt`).
