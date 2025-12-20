FROM python:3.12-slim AS builder
WORKDIR /build

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml uv.lock ./

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install uv \
    && uv export --no-dev --frozen -o requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip wheel --wheel-dir /wheelhouse -r requirements.txt


FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      libpq5 \
      postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheelhouse /wheelhouse
COPY --from=builder /build/requirements.txt /app/requirements.txt

COPY alembic.ini /app/alembic.ini
COPY src /app/src

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --no-cache-dir --find-links=/wheelhouse -r /app/requirements.txt \
    && rm -rf /wheelhouse /app/requirements.txt \
    && useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
