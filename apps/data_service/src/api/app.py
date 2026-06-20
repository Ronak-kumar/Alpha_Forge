import os

from fastapi import FastAPI

from api.service import router as data_router

app = FastAPI(title="Alpha Forge Data Service", version="0.1.0")
app.include_router(data_router)


@app.get("/")
async def root():
    return {"message": "Welcome to the Alpha Forge Data Service API"}
