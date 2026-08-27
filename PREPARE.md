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

## デプロイ

```shell
kubectl apply -f deploy
```


## 公開


```
kubectl port-forward -n monitoring \
  svc/monitoring-kube-prometheus-prometheus 9090:9090
```
