import asyncio
import os

from fastapi import FastAPI

from api.rabbit import publisher
from api.service import router as data_router

app = FastAPI(title="Alpha Forge Data Service", version="0.1.0")
app.include_router(data_router)


@app.on_event("startup")
async def startup_rabbit():
    # Connect publisher and store on app.state for handlers to use
    rabbit_url = os.getenv("RABBITMQ_URL", None)
    await publisher.connect(rabbit_url)
    app.state.rabbit_publisher = publisher


@app.get("/")
async def root():
    return {"message": "Welcome to the Alpha Forge Data Service API"}


@app.on_event("shutdown")
async def shutdown_rabbit():
    try:
        if getattr(app.state, "rabbit_publisher", None):
            await app.state.rabbit_publisher.close()
    except Exception:
        pass
