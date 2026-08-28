# アーキテクチャ

このプロジェクトは、商品検索を題材にしたオブザーバビリティのデモです。
ブラウザから検索したリクエストが2つのAPIを通り、同時にリクエスト数・応答時間・エラーなどがPrometheusへ集められ、Grafanaで確認できます。

## 全体構成

```mermaid
flowchart TB
    user[User Browser]
    host[Host PC]

    subgraph minikube[Minikube]
        subgraph demo[Demo Namespace]
            demoSvc[Demo API Service]
            demoDeploy[Demo API Deployment]
            demoPod[Demo API Pod]

            backendSvc[Backend API Service]
            backendDeploy[Backend API Deployment]
            backendPods[Backend API Pods]
        end

        subgraph monitoring[Monitoring Namespace]
            stack[Prometheus Stack]
            prometheus[Prometheus]
            grafana[Grafana]
        end
    end

    user -->|search| host
    host -->|port forward| demoSvc
    demoSvc --> demoDeploy
    demoDeploy --> demoPod
    demoPod -->|http| backendSvc
    backendSvc --> backendDeploy
    backendDeploy --> backendPods

    stack --> prometheus
    stack --> grafana
```

### 役割

| 要素 | 役割 |
| --- | --- |
| 利用者 / ブラウザ | 商品検索やデモ操作を行う入口 |
| demo-api | 検索画面を表示し、backend-apiへ検索を中継 |
| backend-api | アプリ内の固定商品データを検索して返す |
| demo-api Service | 外部からdemo-apiへ接続する入口 |
| backend-api Service | backend-api Podへリクエストを振り分ける内部入口 |
| Prometheus | APIが公開するメトリクスを収集・保存 |
| Grafana | Prometheusのデータをグラフで表示 |

## Kubernetes上のデータの流れ

```mermaid
flowchart LR
    browser[Browser] --> demo[Demo API]
    demo --> backend[Backend API]
    backend --> data[Product Data]
    data --> backend
    backend --> demo
    demo --> browser

    demo -.->|metrics| monitor[Service Monitor]
    backend -.->|metrics| monitor
    monitor --> prometheus[Prometheus]
    prometheus --> grafana[Grafana]
```

実線は商品検索のリクエスト、点線は観測用のメトリクス収集を表します。
ServiceMonitorは3秒間隔で各Serviceの`/metrics`を収集します。

## Minikubeの構成

```mermaid
flowchart TB
    subgraph cluster[Minikube]
        subgraph demo[Demo Namespace]
            ddep[Demo API Deployment]
            dsvc[Demo API Service]
            bdep[Backend API Deployment]
            bsvc[Backend API Service]
            sm1[Demo API Monitor]
            sm2[Backend API Monitor]
        end
        subgraph monitoring[Monitoring Namespace]
            prom[Prometheus]
            graf[Grafana]
        end
    end

    dsvc --> ddep
    bsvc --> bdep
    sm1 -.-> prom
    sm2 -.-> prom
    prom --> graf
```

アプリケーションのコンテナイメージは、通常のDockerレジストリから取得せず、次のコマンドでMinikubeが利用できる場所へビルドします。

```shell
minikube image build -t demo-api:latest ./demo-api
minikube image build -t backend-api:latest ./backend-api
kubectl apply -f deploy
```

Deploymentでは`imagePullPolicy: Never`を指定しているため、コード変更後はイメージを再ビルドし、必要に応じてDeploymentを再起動します。

## デモで観測するもの

```mermaid
sequenceDiagram
    participant User as 利用者
    participant Demo as Demo API
    participant Backend as Backend API
    participant K8s as Kubernetes
    participant Grafana as Grafana

    User->>Demo: Normal search and failure scenarios
    Demo->>Backend: 商品検索リクエスト
    Backend-->>Demo: 商品結果またはエラー
    Demo-->>User: 画面に結果を表示
    Note over User,Backend: Random load runs at about 10 requests per second for one minute
    Demo->>K8s: publish metrics
    Backend->>K8s: publish metrics
    K8s->>Grafana: show metrics through Prometheus
```

画面上の負荷テストを実行すると、正常なレスポンスだけでなく、遅延やHTTPエラーも発生します。その変化をGrafanaで見ることで、アプリケーションの状態を数字とグラフで把握できます。

## Kubernetesの自己修復

```mermaid
sequenceDiagram
    participant User as 利用者
    participant Demo as Demo API
    participant Backend as Backend Pod
    participant Deployment as Kubernetes Deployment
    participant NewPod as New Backend Pod

    User->>Demo: Stop one backend pod
    Demo->>Backend: POST shutdown
    Backend--xDemo: Podが終了
    Deployment->>Deployment: レプリカ数を確認
    Deployment->>NewPod: 不足したPodを作成
    NewPod-->>Deployment: Ready
    User->>Demo: 商品検索
    Demo->>NewPod: 検索リクエスト
    NewPod-->>User: 商品結果
```

backend-apiは2レプリカで動作しています。画面の停止ボタンはService経由で通常1つのPodを終了させますが、Deploymentが不足分を自動的に作り直すため、最終的に2レプリカへ戻ります。

## ローカルからのアクセス

```shell
# 商品検索アプリ
kubectl port-forward -n demo svc/demo-api 8000:8000
# http://localhost:8000

# Prometheus
kubectl port-forward -n monitoring \
  svc/monitoring-kube-prometheus-prometheus 9090:9090
# http://localhost:9090

# Grafana
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
# http://localhost:3000
```
