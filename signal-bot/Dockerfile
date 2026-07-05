FROM mcr.microsoft.com/playwright/python:v1.48.0-noble

WORKDIR /app

# Instala dependências Python
COPY requirements-worker.txt .
RUN pip install --no-cache-dir -r requirements-worker.txt

# Copia o código
COPY . .

EXPOSE 8080

# Inicia bot Telegram (webhook mode no Railway, polling mode local)
CMD ["bash", "start_worker.sh"]
