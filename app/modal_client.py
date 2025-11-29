import os
from typing import Dict, Any, List
from datetime import datetime
from .config import config
from .models import Service, MetricPoint
from .infra_simulation import generate_fake_metrics


def simulate_metrics_job(services: List[Service]) -> Dict[str, List[MetricPoint]]:
    """Generate metrics for a list of services using Modal or simulation.

    Args:
        services: List of Service objects to generate metrics for

    Returns:
        Dict mapping service_id to list of MetricPoint objects

    TODO: Replace with actual Modal function call when available:
        - Authenticate with Modal using config.modal_token
        - Submit metrics job to Modal function
        - Return results from Modal execution
    """
    if not config.is_modal_available():
        # Simulation mode
        result = {}
        for service in services:
            metrics = generate_fake_metrics(service.service_id)
            result[service.service_id] = metrics
        return result

    # TODO: Implement actual Modal metrics job
    # This would typically involve:
    # 1. Submit a Modal function call to generate metrics
    # 2. Wait for completion and return results
    # For now, fall back to simulation
    result = {}
    for service in services:
        metrics = generate_fake_metrics(service.service_id)
        result[service.service_id] = metrics
    return result


def restart_service_via_modal(service_id: str) -> Dict[str, Any]:
    """Restart a service via Modal or simulate restart.

    Args:
        service_id: ID of the service to restart

    Returns:
        Dict with RestartResult-compatible fields:
        - service_id, restart_status, time_taken_ms, post_restart_health, via, timestamp
    """
    import random
    import time
    
    start_time = time.time()
    
    if not config.is_modal_available():
        # Simulation mode - simulate restart delay
        time.sleep(random.uniform(0.1, 0.3))
        elapsed_ms = (time.time() - start_time) * 1000
        
        return {
            "service_id": service_id,
            "restart_status": "success",
            "time_taken_ms": round(elapsed_ms, 2),
            "post_restart_health": round(random.uniform(85, 100), 1),
            "via": "simulation",
            "timestamp": datetime.now().isoformat()
        }

    # TODO: Implement actual Modal restart
    try:
        # Simulate Modal API call
        time.sleep(random.uniform(0.2, 0.5))
        elapsed_ms = (time.time() - start_time) * 1000
        
        return {
            "service_id": service_id,
            "restart_status": "success",
            "time_taken_ms": round(elapsed_ms, 2),
            "post_restart_health": round(random.uniform(90, 100), 1),
            "via": "modal",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "service_id": service_id,
            "restart_status": "failed",
            "time_taken_ms": round(elapsed_ms, 2),
            "post_restart_health": None,
            "via": "modal",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }