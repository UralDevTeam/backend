# ---- Build stage (зависимости) ----
FROM python:3.12-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv (статичный бинарник)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Чтобы максимально использовать кеш слоёв, копируем только файлы проекта,
# влияющие на резолв зависимостей
COPY pyproject.toml uv.lock ./

# Создаём изолированное окружение с зависимостями.
# --frozen: строго по uv.lock
# --no-dev: без dev-группы
# По умолчанию uv создаёт .venv в корне проекта.
RUN uv sync --frozen --no-dev

# ---- Runtime stage ----
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY app ./app

RUN useradd -m appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
