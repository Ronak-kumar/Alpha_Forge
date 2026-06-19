# Alpha Forge Data Service — Local Run Instructions

Quick instructions to run the data service and the RabbitMQ worker locally for development.

Prerequisites
- Python 3.10+ (project uses a virtual environment at `.venv`)
- Docker & Docker Compose (for RabbitMQ)

Install python deps

```bash
python -m venv .venv
.
.venv\Scripts\activate  # Windows PowerShell / cmd
pip install -r requirements.txt
```

Start RabbitMQ with Docker Compose

```bash
docker-compose up -d rabbitmq
# RabbitMQ management UI: http://localhost:15672 (guest/guest)
```

Run the API (development)

```bash
python apps/data_service/src/main.py
# or using uvicorn directly if preferred:
# uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

Run the worker (consumes messages and writes monthly parquet + manifest)

```bash
python apps/data_service/src/api/worker.py
```

Sample POST to enqueue a monthly job

```bash
curl -X POST http://localhost:8000/data/month \
  -H "Content-Type: application/json" \
  -d '{
    "segment": "equity",
    "year": 2021,
    "month": 5,
    "events": [
      {
        "segment": "equity",
        "symbol": "TEST",
        "exchange": "EX",
        "timestamp": 1620000000000000,
        "price": 10.0,
        "size": 100,
        "recv_timestamp": 1620000000001000,
        "source": "test",
        "message_type": "trade",
        "metadata": {"source_id": "unit"},
        "year": 2021,
        "month": 5
      }
    ]
  }'
```

Notes
- The worker expects RabbitMQ accessible at `amqp://guest:guest@localhost/` by default. Use `RABBITMQ_URL` env var to customize.
- For production use, replace the in-repo worker with a managed consumer and add dead-letter handling and retries.
