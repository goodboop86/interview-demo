## Minikube
see: https://kubernetes.io/ja/docs/tutorials/hello-minikube/


## API docker image

minikubeが認識するようにbuildする

demo-api

```shell
minikube image build -t demo-api:latest ./demo-api

% minikube image ls | grep demo-api
docker.io/library/demo-api:latest
```

backend-api
```shell
minikube image build -t backend-api:latest ./backend-api

% minikube image ls | grep backend-api
docker.io/library/backend-api:latest
```


## prometheus/grafana

関連パッケージを追加し、デプロイする

```shell
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

kubens monitoring
```


### カスタムダッシュボード

```
kubectl delete configmap dashboard-demo -n monitoring
kubectl create configmap dashboard-demo --from-file=monitoring/dashboard-demo.json -n monitoring
kubectl label configmap dashboard-demo -n monitoring grafana_dashboard="1"
```


### imageの更新とdeployの更新

```shell
minikube image build -t backend-api:latest ./backend-api && minikube image build -t demo-api:latest ./demo-api && kubectl rollout restart deployment/backend-api deployment/demo-api -n demo && kubectl rollout status deployment/backend-api -n demo --timeout=120s && kubectl rollout status deployment/demo-api -n demo --timeout=120s
```