import os
import random
import requests
from typing import List, Optional, Tuple
from .config import config
from .models import MetricPoint, AnomalyResult


# Anomaly thresholds
LATENCY_THRESHOLD_MS = 500
ERROR_RATE_THRESHOLD = 0.1
CPU_SPIKE_THRESHOLD = 90
MEMORY_LEAK_THRESHOLD = 85


def embed_logs(log_lines: List[str]) -> List[List[float]]:
    """Generate embeddings for log lines using Hyperbolic or simulation."""
    if not config.is_hyperbolic_available():
        return [[random.uniform(-1, 1) for _ in range(384)] for _ in log_lines]

    try:
        headers = {
            "Authorization": f"Bearer {config.hyperbolic_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": log_lines,
            "model": "hyperbolic-embedding-v1"
        }
        response = requests.post(
            f"{config.hyperbolic_endpoint}/embeddings",
            json=payload,
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        return response.json().get("data", [])
    except Exception:
        # Fallback to random embeddings
        return [[random.uniform(-1, 1) for _ in range(384)] for _ in log_lines]


def _classify_anomaly_type(
    avg_cpu: float,
    avg_ram: float,
    avg_latency: float,
    avg_error_rate: float
) -> Tuple[Optional[str], str]:
    """Classify anomaly type and determine recommended action."""
    if avg_cpu > CPU_SPIKE_THRESHOLD:
        return "cpu_spike", "Scale horizontally or investigate CPU-intensive processes"
    elif avg_ram > MEMORY_LEAK_THRESHOLD:
        return "memory_leak", "Restart service and investigate memory allocation patterns"
    elif avg_latency > LATENCY_THRESHOLD_MS:
        return "latency_surge", "Check network connectivity and downstream dependencies"
    elif avg_error_rate > ERROR_RATE_THRESHOLD:
        return "error_burst", "Review error logs and check for failing dependencies"
    return None, "Continue monitoring"


def _determine_severity(
    avg_cpu: float,
    avg_ram: float,
    avg_latency: float,
    avg_error_rate: float
) -> str:
    """Determine anomaly severity based on metric thresholds."""
    critical_count = 0
    high_count = 0
    
    # CPU severity
    if avg_cpu > 95:
        critical_count += 1
    elif avg_cpu > CPU_SPIKE_THRESHOLD:
        high_count += 1
    
    # Memory severity
    if avg_ram > 95:
        critical_count += 1
    elif avg_ram > MEMORY_LEAK_THRESHOLD:
        high_count += 1
    
    # Latency severity
    if avg_latency > 1000:
        critical_count += 1
    elif avg_latency > LATENCY_THRESHOLD_MS:
        high_count += 1
    
    # Error rate severity
    if avg_error_rate > 0.2:
        critical_count += 1
    elif avg_error_rate > ERROR_RATE_THRESHOLD:
        high_count += 1
    
    if critical_count >= 2:
        return "critical"
    elif critical_count >= 1 or high_count >= 2:
        return "high"
    elif high_count >= 1:
        return "medium"
    elif avg_latency > 300 or avg_error_rate > 0.05:
        return "low"
    return "none"


def detect_anomaly_from_metrics(service_id: str, metrics: List[MetricPoint]) -> AnomalyResult:
    """Detect anomalies in service metrics using thresholds and classification."""
    if not metrics:
        return AnomalyResult(
            service_id=service_id,
            has_anomaly=False,
            severity="none",
            reason="No metrics data available",
            evidence=[],
            anomaly_type=None,
            affected_services=[],
            recommended_action="Ensure metrics collection is working"
        )

    # Calculate averages
    avg_cpu = sum(m.cpu for m in metrics) / len(metrics)
    avg_ram = sum(m.ram for m in metrics) / len(metrics)
    avg_latency = sum(m.latency_ms for m in metrics) / len(metrics)
    avg_error_rate = sum(m.error_rate for m in metrics) / len(metrics)
    
    # Build evidence list
    evidence = [
        f"avg_cpu={avg_cpu:.2f}%",
        f"avg_ram={avg_ram:.2f}%",
        f"avg_latency={avg_latency:.2f}ms",
        f"avg_error_rate={avg_error_rate:.2%}",
        f"sample_count={len(metrics)}"
    ]
    
    # Check for anomalies based on thresholds (Requirements 4.5)
    has_anomaly = (
        avg_latency > LATENCY_THRESHOLD_MS or
        avg_error_rate > ERROR_RATE_THRESHOLD or
        avg_cpu > CPU_SPIKE_THRESHOLD or
        avg_ram > MEMORY_LEAK_THRESHOLD
    )
    
    # Determine severity (Requirements 4.3)
    severity = _determine_severity(avg_cpu, avg_ram, avg_latency, avg_error_rate)
    
    # Classify anomaly type and get recommendation (Requirements 4.1, 4.4)
    anomaly_type, recommended_action = _classify_anomaly_type(
        avg_cpu, avg_ram, avg_latency, avg_error_rate
    )
    
    # Build reason string
    if has_anomaly:
        reasons = []
        if avg_latency > LATENCY_THRESHOLD_MS:
            reasons.append(f"high latency ({avg_latency:.2f}ms > {LATENCY_THRESHOLD_MS}ms)")
        if avg_error_rate > ERROR_RATE_THRESHOLD:
            reasons.append(f"high error rate ({avg_error_rate:.2%} > {ERROR_RATE_THRESHOLD:.0%})")
        if avg_cpu > CPU_SPIKE_THRESHOLD:
            reasons.append(f"CPU spike ({avg_cpu:.2f}% > {CPU_SPIKE_THRESHOLD}%)")
        if avg_ram > MEMORY_LEAK_THRESHOLD:
            reasons.append(f"high memory ({avg_ram:.2f}% > {MEMORY_LEAK_THRESHOLD}%)")
        reason = "Anomaly detected: " + ", ".join(reasons)
    else:
        reason = "All metrics within normal thresholds"
    
    return AnomalyResult(
        service_id=service_id,
        has_anomaly=has_anomaly,
        severity=severity,
        reason=reason,
        evidence=evidence,
        anomaly_type=anomaly_type,
        affected_services=[service_id] if has_anomaly else [],
        recommended_action=recommended_action
    )