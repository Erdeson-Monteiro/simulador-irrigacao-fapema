# Painel e API do simulador de irrigação PIC/FAPEMA (modelo v2).
# Na primeira subida (volume vazio), roda o pipeline, que gera os resultados e popula o banco;
# depois só serve. O token do dispositivo vem de DEVICE_TOKEN (nunca da imagem).
FROM python:3.12.3-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8000 \
    DB_PATH=/dados/irrigacao.db

RUN apt-get update \
 && apt-get install -y --no-install-recommends fonts-liberation \
 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin app \
 && mkdir -p /dados \
 && chown app:app /dados

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app . .

USER app
EXPOSE 8000
VOLUME ["/dados"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/healthz' % os.environ.get('PORT', '8000'), timeout=4)" || exit 1

CMD ["sh", "-c", "[ -f \"$DB_PATH\" ] || python main.py pipeline; exec python main.py serve"]
