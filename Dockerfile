FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder
WORKDIR /build

COPY pyproject.toml uv.lock ./

RUN uv export --no-dev --frozen -o requirements.txt
RUN uv pip wheel -r requirements.txt -w /wheelhouse


FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libpq5 \
    postgresql-client \
  && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheelhouse /wheelhouse
COPY --from=builder /build/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --no-index --find-links=/wheelhouse -r /app/requirements.txt

COPY alembic.ini /app/alembic.ini
COPY src /app/src

ENV PYTHONPATH=/app

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
