# Multi-stage build for SENAMHI Tracker

# Stage 1: Builder - Install dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies for GDAL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    gdal-bin \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools
RUN pip install --upgrade pip setuptools wheel

RUN pip install poetry==1.8.2

COPY pyproject.toml poetry.lock ./

# Install GDAL Python bindings first
RUN pip install "GDAL==$(gdal-config --version).*"

# Install all dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Stage 2: Runtime - Minimal image with only necessary dependencies
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies for GDAL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code (BEFORE poetry install --only-root)
COPY app ./app
COPY config ./config
COPY scripts ./scripts
COPY alembic ./alembic
COPY alembic.ini ./
COPY pyproject.toml poetry.lock ./

# Install the package in the container (AFTER copying all code)
RUN pip install poetry==1.8.2 && \
    poetry config virtualenvs.create false && \
    poetry install --only-root --no-interaction --no-ansi && \
    pip uninstall poetry -y

# Create directories
RUN mkdir -p data logs

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run migrations and start scheduler
CMD ["sh", "-c", "alembic upgrade head && python -m app.main daemon start"]
