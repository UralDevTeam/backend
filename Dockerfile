# ---- Build stage ----
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder
WORKDIR /src

# Кэш зависимостей
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Копируем весь проект (включая src/)
COPY . .

# Устанавливаем проект и (пере)создаём окружение
RUN uv sync --frozen --no-dev

# ---- Runtime stage ----
FROM python:3.12-slim
WORKDIR /src
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Сертификаты и системные библиотеки (libpq5 для asyncpg/PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libpq5 \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Переносим виртуальное окружение и код
COPY --from=builder /src/.venv /opt/venv
COPY --from=builder /src /src
COPY docker/entrypoint.sh /entrypoint.sh

# Ensure entrypoint has Unix line endings (convert if it was committed with CRLF)
RUN dos2unix /entrypoint.sh || true

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

# Безопасный пользователь
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /src
RUN chmod +x /entrypoint.sh

USER appuser

EXPOSE 8000

# Точка входа
# Точка входа запускает миграции перед стартом API
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
