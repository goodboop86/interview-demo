import os

import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI(title="Product Search Observability Demo")
Instrumentator(should_group_status_codes=False).instrument(app).expose(app)
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
        <title>商品検索Demo</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <main class="container">
            <header>
                <h1>商品検索Demo</h1>
                <p class="subtitle">FastAPI + Kubernetes + Prometheus + Grafana</p>
            </header>

            <section class="card intro">
                <h2>このデモについて</h2>
                <p>
                    - シンプルな商品検索システムのデモです。
                    - このシステムはローカルのkubernetes環境にデプロイされています
                    - このデモで商品を検索すると、さらに裏側のAPIにリクエストを行い、マッチした商品を取得します。
                    - これらの仕組みはPrometheusによりモニタリングされ、Grafanaにより可視化できます。
                </p>
            </section>

            <section class="card">
                <h2>商品を検索</h2>
                <div class="search-controls">
                    <input id="query" type="search" placeholder="例: モニター" autocomplete="off">
                    <button class="normal" type="button" id="search-button">検索</button>
                </div>
                <div class="buttons">
                    <button class="timeout" type="button" onclick="runScenario('遅延')">遅延を再現</button>
                    <button class="error" type="button" onclick="runScenario('エラー')">エラーを再現</button>
                    <button class="random" type="button" id="load-test-button">3分間ランダム負荷</button>
                    <button class="shutdown" type="button" id="shutdown-button">backend-apiを1台停止</button>
                </div>
                <p class="hint">負荷テストは約20RPSで、正常・遅延・エラーの検索をランダムに3分間実行します。</p>
                <p id="load-test-status" class="load-status" aria-live="polite"></p>
                <p id="shutdown-status" class="shutdown-status" aria-live="polite"></p>
                <h3>検索結果</h3>
                <pre id="result">検索キーワードを入力してください。</pre>
            </section>
        </main>

        <script>
            const query = document.getElementById("query");
            const result = document.getElementById("result");
            const searchButton = document.getElementById("search-button");
            const loadTestButton = document.getElementById("load-test-button");
            const loadTestStatus = document.getElementById("load-test-status");
            const shutdownButton = document.getElementById("shutdown-button");
            const shutdownStatus = document.getElementById("shutdown-status");
            let loadTestTimer = null;
            let loadTestEnd = 0;
            let loadTestSent = 0;
            let loadTestCompleted = 0;

            searchButton.addEventListener("click", () => {
                search(query.value);
            });

            loadTestButton.addEventListener("click", startLoadTest);
            shutdownButton.addEventListener("click", shutdownBackend);

            query.addEventListener("keydown", (event) => {
                if (event.key === "Enter") {
                    event.preventDefault();
                    search(query.value);
                }
            });

            function runScenario(value) {
                query.value = value;
                search(value);
            }

            function startLoadTest() {
                if (loadTestTimer !== null) {
                    return;
                }

                const duration = 180 * 1000;
                const interval = 50;
                loadTestEnd = Date.now() + duration;
                loadTestSent = 0;
                loadTestCompleted = 0;
                loadTestButton.disabled = true;
                loadTestStatus.textContent = "負荷テスト実行中: 約20 RPS / 残り180秒";

                loadTestTimer = setInterval(() => {
                    if (Date.now() >= loadTestEnd) {
                        stopLoadTest();
                        return;
                    }

                    const scenarios = ["", "遅延", "エラー"];
                    const scenario = scenarios[Math.floor(Math.random() * scenarios.length)];
                    loadTestSent += 1;
                    sendLoadRequest(scenario);

                    const remaining = Math.ceil((loadTestEnd - Date.now()) / 1000);
                    loadTestStatus.textContent =
                        "負荷テスト実行中: 約20 RPS / 残り" + remaining + "秒 / 送信" + loadTestSent + "件";
                }, interval);
            }

            function stopLoadTest() {
                clearInterval(loadTestTimer);
                loadTestTimer = null;
                loadTestButton.disabled = false;
                loadTestStatus.textContent =
                    "負荷テスト完了: " + loadTestSent + "件送信 / " + loadTestCompleted + "件応答";
            }

            async function sendLoadRequest(value) {
                try {
                    await fetch("/search?q=" + encodeURIComponent(value));
                } catch (error) {
                    // 負荷生成中の個別リクエスト失敗は、次のリクエストを止めない。
                } finally {
                    loadTestCompleted += 1;
                }
            }

            async function shutdownBackend() {
                shutdownButton.disabled = true;
                shutdownStatus.textContent = "backend-apiを停止しています...";
                try {
                    const response = await fetch("/shutdown", {method: "POST"});
                    const body = await response.json();
                    shutdownStatus.textContent = body.message;
                } catch (error) {
                    shutdownStatus.textContent =
                        "停止リクエストを送信しました。KubernetesがPodを再作成するまで少し待ってください。";
                }
            }

            async function search(value) {
                result.className = "";
                result.textContent = "検索中...";
                try {
                    const response = await fetch("/search?q=" + encodeURIComponent(value));
                    const body = await response.text();
                    result.textContent = "HTTP " + response.status + "\\n\\n" + body;
                    result.classList.add(response.ok ? "success" : "failure");
                } catch (error) {
                    result.textContent = "Request failed:\\n\\n" + error;
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


@app.post("/shutdown")
def shutdown():
    try:
        requests.post(f"{BACKEND_API_URL}/shutdown", timeout=1.0)
    except requests.RequestException:
        pass

    return JSONResponse(
        status_code=202,
        content={
            "message": "停止リクエストを送信しました。KubernetesがPodを再作成します。",
        },
    )
