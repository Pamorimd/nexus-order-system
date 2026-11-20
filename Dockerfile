FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

COPY pyproject.toml /app/
RUN pip install --no-cache-dir ruff pytest

COPY src/ /app/src/
COPY tests/ /app/tests/

CMD ["python", "src/nexus/adapters/entrypoints/cli.py"]
