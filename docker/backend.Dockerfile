FROM python:3.12-slim-bookworm

ARG EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/opt/huggingface \
    SPARK_EMBEDDING_MODEL=${EMBEDDING_MODEL}

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /app/requirements.txt

# Download the embedding model while building so RAG works with offline mode
# when the container starts.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBEDDING_MODEL}')"

RUN groupadd --gid 10001 learnloop \
    && useradd --uid 10001 --gid learnloop --create-home learnloop \
    && mkdir -p /app/data /app/seed /opt/huggingface \
    && chown -R learnloop:learnloop /app/data /app/seed /opt/huggingface

COPY --chown=learnloop:learnloop spark /app/spark
COPY --chown=learnloop:learnloop spark/student_learning.db /app/seed/student_learning.db
COPY --chown=learnloop:learnloop docker/backend-entrypoint.sh /app/backend-entrypoint.sh
RUN sed -i 's/\r$//' /app/backend-entrypoint.sh \
    && chmod +x /app/backend-entrypoint.sh

USER learnloop

EXPOSE 8000

ENTRYPOINT ["/app/backend-entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "spark.ai_api:app", "--host", "0.0.0.0", "--port", "8000"]
