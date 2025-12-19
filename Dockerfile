# syntax=docker/dockerfile:1.6

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libpq5 \
    postgresql-client \
  && rm -rf /var/lib/apt/lists/*

# ставим uv в runtime
RUN python -m pip install --no-cache-dir uv

# зависимости: сначала lock-файлы (кеш)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen --no-install-project

# код и alembic
COPY alembic.ini ./alembic.ini
COPY src ./src

# теперь ставим проект (если нужно) / финализируем окружение
RUN uv sync --no-dev --frozen

# PATH на venv, который создал uv в /app/.venv
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:${PATH}" \
    PYTHONPATH=/app

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
