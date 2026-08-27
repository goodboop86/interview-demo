#!/bin/bash

set -e

echo "Starting port-forwards..."

kubectl port-forward svc/demo-api 8000:8000 &
API_PID=$!

kubectl port-forward \
  -n monitoring \
  svc/monitoring-grafana 3000:80 &
GRAFANA_PID=$!

kubectl port-forward \
  -n monitoring \
  svc/monitoring-kube-prometheus-prometheus 9090:9090 &
PROMETHEUS_PID=$!

echo "Grafana password:"
kubectl get secret monitoring-grafana -o jsonpath='{.data.admin-password}' -n monitoring | base64 -d
echo

cleanup() {
    echo ""
    echo "Stopping port-forwards..."
    kill $API_PID $GRAFANA_PID $PROMETHEUS_PID 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo ""
echo "FastAPI:    http://localhost:8000"
echo "Grafana:    http://localhost:3000"
echo "Prometheus: http://localhost:9090"
echo ""
echo "Press Ctrl+C to stop."

wait