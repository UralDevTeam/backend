# ---- Build stage ----
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS builder
WORKDIR /app

# Кэш зависимостей
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Теперь код проекта
COPY . .

# Устанавливаем проект и (пере)создаём окружение, если нужно
RUN uv sync --frozen --no-dev

# ---- Runtime stage ----
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# сертификаты (и тут можно добавить системные либы, напр. libpq5)
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# переносим виртуальное окружение и код
COPY --from=builder /app/.venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv PATH="/opt/venv/bin:${PATH}"
COPY src ./src

# безопасный пользователь
RUN useradd -m appuser
USER appuser

EXPOSE 8000
# ВНИМАНИЕ к импорту: если у тебя структура src/app/main.py, то нужно "app.main:app"
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
