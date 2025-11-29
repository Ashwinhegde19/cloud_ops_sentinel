import os
import random
from typing import List
from .config import config
from .models import MetricPoint, AnomalyResult


def embed_logs(log_lines: List[str]) -> List[List[float]]:
    if not config.is_hyperbolic_available():
        return [[random.uniform(-1, 1) for _ in range(384)] for _ in log_lines]

    # TODO: Implement actual Hyperbolic API call
    # Expected to be something like:
    # import requests
    # headers = {"Authorization": f"Bearer {config.hyperbolic_api_key}"}
    # payload = {"input": log_lines, "model": "hyperbolic-embedding-v1"}
    # response = requests.post(f"{config.hyperbolic_endpoint}/embeddings", json=payload, headers=headers)
    # return response.json()["data"]

    # Fallback to random embeddings for now
    return [[random.uniform(-1, 1) for _ in range(384)] for _ in log_lines]


def detect_anomaly_from_metrics(service_id: str, metrics: List[MetricPoint]) -> AnomalyResult:
    if not metrics:
        return AnomalyResult(
            service_id=service_id,
            has_anomaly=False,
            severity="none",
            reason="No metrics data",
            evidence=[]
        )

    if not config.is_hyperbolic_available():
        # Simple heuristic fallback
        avg_latency = sum(m.latency_ms for m in metrics) / len(metrics)
        avg_error_rate = sum(m.error_rate for m in metrics) / len(metrics)

        if avg_latency > 500 or avg_error_rate > 0.1:
            return AnomalyResult(
                service_id=service_id,
                has_anomaly=True,
                severity="high" if avg_latency > 1000 or avg_error_rate > 0.2 else "medium",
                reason=f"High latency ({avg_latency:.2f}ms) or error rate ({avg_error_rate:.2%})",
                evidence=[f"avg_latency={avg_latency:.2f}ms", f"avg_error_rate={avg_error_rate:.2%}"]
            )
        else:
            return AnomalyResult(
                service_id=service_id,
                has_anomaly=False,
                severity="none",
                reason="Metrics within normal thresholds",
                evidence=[f"avg_latency={avg_latency:.2f}ms", f"avg_error_rate={avg_error_rate:.2%}"]
            )

    # TODO: Implement actual Hyperbolic anomaly detection
    # Would typically:
    # 1. Format metrics for embedding
    # 2. Send to Hyperbolic API for similarity/threshold analysis
    # 3. Process response to determine anomalies

    # For now, return simple heuristic as fallback
    return detect_anomaly_from_metrics(service_id, metrics)