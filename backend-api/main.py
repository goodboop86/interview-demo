from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
import asyncio
import os


app = FastAPI()
Instrumentator().instrument(app).expose(app)


@app.get("/")
def root():
    return {
        "service": "backend-api",
        "pod": os.getenv("HOSTNAME"),
        "message": "Hello from backend-api!"
    }


@app.get("/health")
def health():
    return {
        "service": "backend-api",
        "status": "ok",
        "pod": os.getenv("HOSTNAME")
    }


@app.get("/timeout")
async def timeout():
    # 意図的に10秒待つ
    await asyncio.sleep(10)

    return {
        "service": "backend-api",
        "pod": os.getenv("HOSTNAME"),
        "message": "This should not be reached by demo-api"
    }


@app.get("/error")
def error():
    raise HTTPException(
        status_code=500,
        detail="Intentional internal server error"
    )