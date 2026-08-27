import asyncio
import os
import random

from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI(title="Product Search Backend API")
Instrumentator().instrument(app).expose(app)


PRODUCTS = [
    {"id": 1, "name": "ノートパソコン"},
    {"id": 2, "name": "ワイヤレスイヤホン"},
    {"id": 3, "name": "スマートフォン"},
    {"id": 4, "name": "メカニカルキーボード"},
    {"id": 5, "name": "4Kモニター"},
]


async def search_products(query: str) -> list[dict[str, int | str]]:
    if query == "遅延":
        await asyncio.sleep(3)
        query = ""
    elif query == "エラー":
        raise HTTPException(status_code=500, detail="Intentional backend error")
    elif query == "ランダム":
        scenario = random.choice(["normal", "slow", "error"])
        if scenario == "slow":
            await asyncio.sleep(3)
        elif scenario == "error":
            raise HTTPException(status_code=500, detail="Random backend error")
        query = ""

    normalized_query = query.casefold().strip()
    if not normalized_query:
        return PRODUCTS

    return [
        product
        for product in PRODUCTS
        if normalized_query in str(product["name"]).casefold()
    ]


@app.get("/")
async def root():
    return {"service": "backend-api", "message": "Product search backend"}


@app.get("/search")
async def search(q: str = Query(default="", description="商品名の検索キーワード")):
    return await search_products(q)


@app.get("/health")
def health():
    return {
        "service": "backend-api",
        "status": "ok",
        "pod": os.getenv("HOSTNAME"),
    }
