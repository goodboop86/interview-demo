import os

import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI(title="Product Search Observability Demo")
Instrumentator().instrument(app).expose(app)
app.mount("/static", StaticFiles(directory="static"), name="static")


BACKEND_API_URL = "http://backend-api:8000"


@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>商品検索 Observability Demo</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <main class="container">
            <header>
                <h1>商品検索 Observability Demo</h1>
                <p class="subtitle">FastAPI + Kubernetes + Prometheus + Grafana</p>
            </header>

            <section class="card intro">
                <h2>このデモについて</h2>
                <p>
                    シンプルな商品検索を通じて、アプリケーションのリクエストが
                    Prometheusに記録され、Grafanaで可視化される流れを確認できます。
                </p>
                <div class="architecture">
                    <span class="service">Browser</span><span class="arrow">→</span>
                    <span class="service">demo-api</span><span class="arrow">→</span>
                    <span class="service">backend-api</span><span class="arrow">→</span>
                    <span class="service">Prometheus / Grafana</span>
                </div>
            </section>

            <section class="card">
                <h2>商品を検索</h2>
                <form id="search-form">
                    <input id="query" type="search" placeholder="例: モニター" autocomplete="off">
                    <button class="normal" type="submit">検索</button>
                </form>
                <div class="buttons">
                    <button class="timeout" type="button" onclick="runScenario('遅延')">遅延を再現</button>
                    <button class="error" type="button" onclick="runScenario('エラー')">エラーを再現</button>
                    <button class="random" type="button" onclick="runScenario('ランダム')">ランダム障害</button>
                </div>
                <p class="hint">障害ボタンはbackend-apiの遅延・500エラーを発生させ、Grafanaのメトリクス変化を確認するためのものです。</p>
                <h3>検索結果</h3>
                <pre id="result">検索キーワードを入力してください。</pre>
            </section>

            <section class="card observability">
                <h2>Grafanaで見るポイント</h2>
                <ul>
                    <li>リクエスト数とHTTPステータスコード</li>
                    <li>遅延発生時のレスポンスタイム</li>
                    <li>demo-apiからbackend-apiへ伝播する障害</li>
                </ul>
                <p>Prometheusの <code>/metrics</code> をServiceMonitorが収集しています。</p>
            </section>
        </main>

        <script>
            const form = document.getElementById("search-form");
            const query = document.getElementById("query");
            const result = document.getElementById("result");

            form.addEventListener("submit", (event) => {
                event.preventDefault();
                search(query.value);
            });

            function runScenario(value) {
                query.value = value;
                search(value);
            }

            async function search(value) {
                result.className = "";
                result.textContent = "検索中...";
                try {
                    const response = await fetch("/search?q=" + encodeURIComponent(value));
                    const body = await response.text();
                    result.textContent = "HTTP " + response.status + "\n\n" + body;
                    result.classList.add(response.ok ? "success" : "failure");
                } catch (error) {
                    result.textContent = "Request failed:\n\n" + error;
                    result.classList.add("failure");
                }
            }
        </script>
    </body>
    </html>
    """


@app.get("/health")
def health():
    return {
        "service": "demo-api",
        "status": "ok",
        "pod": os.getenv("HOSTNAME"),
    }


@app.get("/search")
def search(q: str = Query(default="", description="商品名の検索キーワード")):
    try:
        response = requests.get(
            f"{BACKEND_API_URL}/search",
            params={"q": q},
            timeout=1.0,
        )
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="backend-api request timed out")
    except requests.RequestException as error:
        raise HTTPException(status_code=502, detail=f"backend-api request failed: {error}")
