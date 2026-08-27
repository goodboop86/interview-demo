import os
import random

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)


BACKEND_API_URL = "http://backend-api:8000"


@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>プレゼンテーション Demo</title>

        <link rel="stylesheet" href="/static/style.css">
    </head>

    <body>

        <main class="container">

            <header>
                <h1>Observability Demo</h1>
                <p class="subtitle">
                    FastAPI + Kubernetes + Prometheus + Grafana
                </p>
            </header>

            <section class="card">
                <h2>概要</h2>

                <p>
                    これはデモアプリです。ローカルにkubernetes環境を立ち上げ、そこにデプロイされています。
                    他にもバックエンドAPIがデプロイされており、
                    can be observed using metrics.
                </p>

                <ul>
                    <li>
                        <strong>Normal</strong>
                        — Successful request
                    </li>
                    <li>
                        <strong>Timeout</strong>
                        — Backend intentionally delays the response
                    </li>
                    <li>
                        <strong>Error</strong>
                        — Backend intentionally returns HTTP 500
                    </li>
                    <li>
                        <strong>Random</strong>
                        — Randomly triggers one of the above scenarios
                    </li>
                </ul>
            </section>


            <section class="card">

                <h2>API Demo</h2>

                <div class="buttons">

                    <button
                        class="normal"
                        onclick="callApi('normal')">
                        Normal
                    </button>

                    <button
                        class="timeout"
                        onclick="callApi('timeout')">
                        Timeout
                    </button>

                    <button
                        class="error"
                        onclick="callApi('error')">
                        Error
                    </button>

                    <button
                        class="random"
                        onclick="callApi('random')">
                        Random
                    </button>

                </div>

                <h3>Response</h3>

                <pre id="result">-</pre>

            </section>


            <section class="card">

                <h2>Architecture</h2>

                <div class="architecture">

                    <div class="service">
                        Browser
                    </div>

                    <div class="arrow">↓</div>

                    <div class="service">
                        demo-api
                    </div>

                    <div class="arrow">↓</div>

                    <div class="service">
                        backend-api
                    </div>

                    <div class="arrow">↓</div>

                    <div class="service">
                        Prometheus / Grafana
                    </div>

                </div>

            </section>

        </main>


        <script>

            async function callApi(type) {

                const result =
                    document.getElementById("result");

                result.textContent = "Loading...";
                result.className = "";

                try {

                    const response =
                        await fetch("/backend?type=" + type);

                    const text =
                        await response.text();

                    result.textContent =
                        "HTTP " +
                        response.status +
                        "\\n\\n" +
                        text;

                    if (response.ok) {
                        result.classList.add("success");
                    } else {
                        result.classList.add("failure");
                    }

                } catch (error) {

                    result.textContent =
                        "Request failed:\\n\\n" +
                        error;

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
        "pod": os.getenv("HOSTNAME")
    }


@app.get("/backend")
def backend(type: str = "normal"):
    if type == "normal":
        path = "/"

    elif type == "timeout":
        path = "/timeout"

    elif type == "error":
        path = "/error"

    elif type == "random":
        path = random.choice([
            "/",
            "/timeout",
            "/error",
        ])

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown type: {type}"
        )

    try:
        response = requests.get(
            f"{BACKEND_API_URL}{path}",
            timeout=0.5
        )

        response.raise_for_status()

        return {
            "service": "demo-api",
            "pod": os.getenv("HOSTNAME"),
            "backend": response.json()
        }

    except requests.Timeout:
        raise HTTPException(
            status_code=504,
            detail="backend-api request timed out"
        )

    except requests.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"backend-api request failed: {str(e)}"
        )