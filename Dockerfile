FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder
WORKDIR /src

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev --frozen --no-install-project

COPY alembic.ini ./
COPY src ./src

RUN uv sync --no-dev --frozen


FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libpq5 \
    postgresql-client \
  && rm -rf /var/lib/apt/lists/*

COPY --from=builder /src/.venv /opt/venv

COPY --from=builder /src/alembic.ini /app/alembic.ini
COPY --from=builder /src/src /app/src

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
