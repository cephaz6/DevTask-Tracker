FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN useradd --create-home appuser

COPY --from=builder /root/.local /home/appuser/.local

COPY . .

RUN chown -R appuser:appuser /app

USER appuser

ENV PATH="/home/appuser/.local/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]