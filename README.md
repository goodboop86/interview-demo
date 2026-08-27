デモ用

see: https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack


### API

```shell
kubectl port-forward svc/demo-api 8000:8000
```


### Prometheus

```
kubectl port-forward -n monitoring \
  svc/monitoring-kube-prometheus-prometheus 9090:9090
```

http://localhost:9090


### Grafana

```
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
```

http://localhost:3000

```
kubectl get secret -n monitoring monitoring-grafana \
  -o jsonpath="{.data.admin-password}" | base64 -d
echo
```