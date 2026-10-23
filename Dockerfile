FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY artifacts/ ./artifacts/
COPY data/processed/ ./data/processed/
COPY server/ ./server/
COPY src/ ./src/
COPY simulation/ ./simulation/
COPY web/ ./web/
COPY docs/ ./docs/
COPY picture/ ./picture/
RUN mkdir -p runtime
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
