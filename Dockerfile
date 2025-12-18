# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder
WORKDIR /app

# Важно: uv будет ставить всё в /opt/venv, а не в /app/.venv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen

# Фейлим сборку, если alembic не установился
RUN /opt/venv/bin/python -c "import alembic; print('alembic ok')"
RUN /opt/venv/bin/alembic --version


FROM python:3.12-slim-bookworm AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      libpq5 \
      postgresql-client \
    ; \
    rm -rf /var/lib/apt/lists/*; \
    useradd -m -u 1000 -s /usr/sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/alembic.ini /app/alembic.ini
COPY --from=builder /app/pyproject.toml /app/pyproject.toml
COPY --from=builder /app/uv.lock /app/uv.lock

RUN chown -R appuser:appuser /app /opt/venv
USER appuser

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
