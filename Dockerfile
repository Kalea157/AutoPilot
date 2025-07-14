# Dockerfile für Super-KI-Agent
FROM python:3.11-slim

# Setze Arbeitsverzeichnis
WORKDIR /app

# Installiere System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Kopiere Requirements und installiere Python-Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere Anwendungscode
COPY src/ ./src/
COPY config.yaml .
COPY .env.example .
COPY start.py .

# Erstelle logs-Verzeichnis
RUN mkdir -p logs

# Setze Umgebungsvariablen
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Exponiere Port (falls Web-Interface hinzugefügt wird)
EXPOSE 8000

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Starte Anwendung
CMD ["python", "start.py"]