FROM python:3.12-slim

WORKDIR /app

COPY backend /app/backend
COPY docs/runtime /app/docs/runtime

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e '/app/backend[dev]'

WORKDIR /app/backend

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
