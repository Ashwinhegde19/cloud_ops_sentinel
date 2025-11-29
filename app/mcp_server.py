import os
import sys
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

# Add parent directory to path for imports when running as script
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Handle imports for both module and script execution
try:
    from .infra_simulation import generate_fake_infra, compute_idle_instances, generate_fake_metrics
    from .modal_client import restart_service_via_modal
    from .blaxel_client import restart_service_via_blaxel
    from .hyperbolic_client import detect_anomaly_from_metrics
    from .llm_client import generate_ops_report
    from .models import CostForecast, AnomalyResult
except ImportError:
    # Running as script - use absolute imports
    from app.infra_simulation import generate_fake_infra, compute_idle_instances, generate_fake_metrics
    from app.modal_client import restart_service_via_modal
    from app.blaxel_client import restart_service_via_blaxel
    from app.hyperbolic_client import detect_anomaly_from_metrics
    from app.llm_client import generate_ops_report
    from app.models import CostForecast, AnomalyResult


def serialize_datetime(obj):
    """Helper function to serialize datetime objects for JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def tool_list_idle_instances() -> Dict[str, Any]:
    """Get list of idle instances using fake infra generation and idle detection"""
    instances, services = generate_fake_infra()
    idle_instances = compute_idle_instances(instances)

    return {
        "idle_instances": [instance.model_dump() for instance in idle_instances]
    }


def tool_get_billing_forecast(month: str) -> Dict[str, Any]:
    """Generate billing forecast for given month"""
    # Simple cost calculation: base_cost + k * avg_usage
    base_cost = 1000.0  # Base monthly cost
    avg_usage_factor = 0.5  # Usage multiplier

    # Get current usage metrics for calculation
    instances, services = generate_fake_infra()
    total_avg_usage = 0
    for instance in instances:
        if instance.cpu_usage:
            avg_cpu = sum(instance.cpu_usage) / len(instance.cpu_usage)
            total_avg_usage += avg_cpu

    predicted_cost = base_cost + (total_avg_usage * avg_usage_factor)
    confidence = 0.75  # Simple confidence level

    forecast = CostForecast(
        month=month,
        predicted_cost=predicted_cost,
        confidence=confidence
    )

    return forecast.model_dump()


def tool_get_metrics(service_id: str) -> Dict[str, Any]:
    """Get metrics for specified service"""
    metrics = generate_fake_metrics(service_id)

    return {
        "service_id": service_id,
        "metrics": [json.loads(json.dumps(metric.model_dump(), default=serialize_datetime)) for metric in metrics]
    }


def tool_detect_anomaly(service_id: str) -> Dict[str, Any]:
    """Detect anomalies for specified service"""
    metrics = generate_fake_metrics(service_id)
    anomaly_result = detect_anomaly_from_metrics(service_id, metrics)

    return anomaly_result.model_dump()


def tool_restart_service(service_id: str) -> Dict[str, Any]:
    """Restart service via Modal or Blaxel"""
    use_blaxel = os.getenv("USE_BLAXEL", "").lower() == "true"

    if use_blaxel:
        result = restart_service_via_blaxel(service_id)
    else:
        result = restart_service_via_modal(service_id)

    return {
        "status": "restarted",
        "service_id": service_id,
        "result": result
    }


def tool_summarize_infra() -> Dict[str, Any]:
    """Generate infrastructure summary and ops report"""
    # Collect infrastructure data
    instances, services = generate_fake_infra()
    idle_instances = compute_idle_instances(instances)

    # Get billing forecast for current month
    current_month = datetime.now().strftime("%Y-%m")
    billing_forecast = tool_get_billing_forecast(current_month)

    # Get anomalies for each service
    anomalies = []
    for service in services:
        service_anomaly = tool_detect_anomaly(service.service_id)
        anomalies.append(service_anomaly)

    # Prepare summary data
    summary_data = {
        "instances": [json.loads(json.dumps(instance.model_dump(), default=serialize_datetime)) for instance in instances],
        "services": [json.loads(json.dumps(service.model_dump(), default=serialize_datetime)) for service in services],
        "idle_instances": [json.loads(json.dumps(instance.model_dump(), default=serialize_datetime)) for instance in idle_instances],
        "billing_forecast": billing_forecast,
        "anomalies": anomalies
    }

    # Generate ops report
    report = generate_ops_report(summary_data)

    return {
        "report": report,
        "summary_data": summary_data
    }


if __name__ == "__main__":
    print("Testing MCP Tools...")

    # Test tool_list_idle_instances
    print("\n=== Testing tool_list_idle_instances ===")
    result = tool_list_idle_instances()
    print(json.dumps(result, indent=2))

    # Test tool_get_billing_forecast
    print("\n=== Testing tool_get_billing_forecast ===")
    result = tool_get_billing_forecast("2024-12")
    print(json.dumps(result, indent=2))

    # Test tool_get_metrics
    print("\n=== Testing tool_get_metrics ===")
    result = tool_get_metrics("svc_web")
    print(json.dumps(result, indent=2))

    # Test tool_detect_anomaly
    print("\n=== Testing tool_detect_anomaly ===")
    result = tool_detect_anomaly("svc_web")
    print(json.dumps(result, indent=2))

    # Test tool_restart_service
    print("\n=== Testing tool_restart_service ===")
    result = tool_restart_service("svc_web")
    print(json.dumps(result, indent=2))

    # Test tool_summarize_infra
    print("\n=== Testing tool_summarize_infra ===")
    result = tool_summarize_infra()
    print("Report length:", len(result.get("report", "")))
    print("Summary data keys:", list(result.get("summary_data", {}).keys()))