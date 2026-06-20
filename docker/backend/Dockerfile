# syntax=docker/dockerfile:1
# Build context: ./backend   |   Application code & manifests are added in S1-T5.
FROM python:3.14-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# ---- dependency layer ----
FROM base AS deps
# Manifests (pyproject.toml / requirements.txt) are introduced in S1-T5.
# Copy whichever exists and install.
COPY pyproject.toml* requirements.txt* ./
RUN pip install --upgrade pip \
 && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi \
 && if [ -f pyproject.toml ] && [ ! -f requirements.txt ]; then pip install .; fi

# ---- development image (hot reload) ----
FROM deps AS development
ENV APP_ENV=local
COPY . .
RUN useradd -m appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
# app.main:app is provided by the S1-T5 scaffold.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]

# ---- production image ----
FROM deps AS production
ENV APP_ENV=production
COPY . .
RUN useradd -m appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
