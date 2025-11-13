FROM python:3.12-slim as builder

WORKDIR /app

RUN pip install poetry==1.8.2

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# Install the package in the container
COPY pyproject.toml poetry.lock ./
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
