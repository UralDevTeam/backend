FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder
WORKDIR /src

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project

COPY . .

RUN uv sync --no-dev

FROM python:3.12-slim
WORKDIR /src
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libpq5 \
    dos2unix \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /src/.venv /opt/venv
COPY --from=builder /src /src
COPY docker/entrypoint.sh /entrypoint.sh

RUN dos2unix /entrypoint.sh || true

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /src
RUN chmod +x /entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
