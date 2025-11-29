"""
Auto-Remediation Engine
Autonomous anomaly detection and service restart with health verification.
"""

import uuid
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

from .models import (
    AnomalyResult, RestartResult, RemediationEvent, IncidentReport
)
from .mcp_server import (
    tool_detect_anomaly,
    tool_restart_service,
    tool_get_metrics
)
from .infra_simulation import generate_fake_infra


# Global state
_remediation_enabled = False
_disabled_services: Dict[str, datetime] = {}  # Services with auto-restart disabled
_event_log: List[RemediationEvent] = []
_event_callbacks: List[Callable[[RemediationEvent], None]] = []
_loop_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()

# Configuration
HEALTH_THRESHOLD = 0.7
CHECK_INTERVAL_SECONDS = 30
HIGH_SEVERITY_LEVELS = {"high", "critical"}


def is_enabled() -> bool:
    """Check if auto-remediation is enabled."""
    return _remediation_enabled


def enable_remediation() -> None:
    """Enable auto-remediation mode."""
    global _remediation_enabled
    _remediation_enabled = True


def disable_remediation() -> None:
    """Disable auto-remediation mode."""
    global _remediation_enabled
    _remediation_enabled = False


def get_event_log() -> List[RemediationEvent]:
    """Get the remediation event log."""
    return _event_log.copy()


def clear_event_log() -> None:
    """Clear the event log."""
    global _event_log
    _event_log = []


def register_event_callback(callback: Callable[[RemediationEvent], None]) -> None:
    """Register a callback to be called when events occur."""
    _event_callbacks.append(callback)


def _notify_callbacks(event: RemediationEvent) -> None:
    """Notify all registered callbacks of an event."""
    for callback in _event_callbacks:
        try:
            callback(event)
        except Exception:
            pass  # Don't let callback errors break the loop


def check_all_services() -> List[Dict]:
    """
    Check all services for anomalies.
    
    Returns:
        List of anomaly results for services with detected anomalies
    """
    # Get list of services from simulation
    _, services = generate_fake_infra()
    
    anomalies = []
    for service in services:
        try:
            result = tool_detect_anomaly(service.service_id)
            if result.get("has_anomaly", False):
                anomalies.append(result)
        except Exception:
            pass  # Skip services that fail
    
    return anomalies


def verify_health(service_id: str) -> float:
    """
    Verify service health after restart.
    
    Args:
        service_id: Service to check
    
    Returns:
        Health score (0.0 - 1.0)
    """
    try:
        metrics = tool_get_metrics(service_id)
        metric_points = metrics.get("metrics", [])
        
        if not metric_points:
            return 0.0
        
        # Calculate health based on recent metrics
        recent = metric_points[-5:] if len(metric_points) >= 5 else metric_points
        
        avg_error_rate = sum(m.get("error_rate", 0) for m in recent) / len(recent)
        avg_latency = sum(m.get("latency_ms", 0) for m in recent) / len(recent)
        
        # Health score: penalize high error rates and latency
        health = 1.0
        health -= avg_error_rate * 2  # Error rate penalty
        health -= (avg_latency / 1000) * 0.5  # Latency penalty (500ms = 0.25 penalty)
        
        return max(0.0, min(1.0, health))
        
    except Exception:
        return 0.0


def remediate_service(service_id: str, anomaly: Dict) -> RemediationEvent:
    """
    Execute remediation workflow for a service.
    
    Args:
        service_id: Service to remediate
        anomaly: Anomaly detection result
    
    Returns:
        RemediationEvent documenting the action taken
    """
    event_id = str(uuid.uuid4())[:8]
    start_time = datetime.now()
    
    severity = anomaly.get("severity", "none")
    
    # Check if auto-restart is disabled for this service
    if service_id in _disabled_services:
        event = RemediationEvent(
            event_id=event_id,
            service_id=service_id,
            anomaly=AnomalyResult(**anomaly) if isinstance(anomaly, dict) else anomaly,
            action_taken="none",
            restart_result=None,
            post_health=None,
            escalated=False,
            timestamp=start_time
        )
        _event_log.append(event)
        _notify_callbacks(event)
        return event
    
    # Check if remediation is enabled
    if not _remediation_enabled:
        event = RemediationEvent(
            event_id=event_id,
            service_id=service_id,
            anomaly=AnomalyResult(**anomaly) if isinstance(anomaly, dict) else anomaly,
            action_taken="none",
            restart_result=None,
            post_health=None,
            escalated=False,
            timestamp=start_time
        )
        _event_log.append(event)
        _notify_callbacks(event)
        return event
    
    # Only restart for high/critical severity
    if severity not in HIGH_SEVERITY_LEVELS:
        event = RemediationEvent(
            event_id=event_id,
            service_id=service_id,
            anomaly=AnomalyResult(**anomaly) if isinstance(anomaly, dict) else anomaly,
            action_taken="none",
            restart_result=None,
            post_health=None,
            escalated=False,
            timestamp=start_time
        )
        _event_log.append(event)
        _notify_callbacks(event)
        return event
    
    # Execute restart
    try:
        restart_result = tool_restart_service(service_id)
        
        # Wait briefly for service to stabilize
        time.sleep(1)
        
        # Verify health
        post_health = verify_health(service_id)
        
        # Check if escalation needed
        escalated = post_health < HEALTH_THRESHOLD
        
        if escalated:
            # Disable auto-restart for this service
            _disabled_services[service_id] = datetime.now()
        
        event = RemediationEvent(
            event_id=event_id,
            service_id=service_id,
            anomaly=AnomalyResult(**anomaly) if isinstance(anomaly, dict) else anomaly,
            action_taken="restart",
            restart_result=RestartResult(**restart_result) if isinstance(restart_result, dict) else restart_result,
            post_health=post_health,
            escalated=escalated,
            timestamp=start_time
        )
        
    except Exception as e:
        event = RemediationEvent(
            event_id=event_id,
            service_id=service_id,
            anomaly=AnomalyResult(**anomaly) if isinstance(anomaly, dict) else anomaly,
            action_taken="restart",
            restart_result=None,
            post_health=0.0,
            escalated=True,
            timestamp=start_time
        )
        _disabled_services[service_id] = datetime.now()
    
    _event_log.append(event)
    _notify_callbacks(event)
    return event


def generate_incident_report(event: RemediationEvent) -> IncidentReport:
    """
    Generate incident report from remediation event.
    
    Args:
        event: Remediation event to document
    
    Returns:
        IncidentReport with root cause, action, and outcome
    """
    # Determine root cause from anomaly
    root_cause = "Unknown"
    if event.anomaly:
        anomaly_type = event.anomaly.anomaly_type or "unknown"
        reason = event.anomaly.reason or "No details available"
        root_cause = f"{anomaly_type}: {reason}"
    
    # Determine outcome
    if event.action_taken == "none":
        outcome = "no_action"
    elif event.escalated:
        outcome = "escalated"
    elif event.post_health and event.post_health >= HEALTH_THRESHOLD:
        outcome = "resolved"
    else:
        outcome = "failed"
    
    # Calculate duration
    duration_ms = 0
    if event.restart_result:
        duration_ms = event.restart_result.time_taken_ms
    
    return IncidentReport(
        event_id=event.event_id,
        service_id=event.service_id,
        root_cause=root_cause,
        action_taken=event.action_taken,
        outcome=outcome,
        duration_ms=duration_ms,
        generated_at=datetime.now()
    )


def _remediation_loop() -> None:
    """Background loop for continuous monitoring and remediation."""
    while not _stop_event.is_set():
        if _remediation_enabled:
            try:
                anomalies = check_all_services()
                for anomaly in anomalies:
                    service_id = anomaly.get("service_id")
                    if service_id:
                        remediate_service(service_id, anomaly)
            except Exception:
                pass  # Don't crash the loop
        
        # Wait for next check interval
        _stop_event.wait(CHECK_INTERVAL_SECONDS)


def start_remediation_loop() -> None:
    """Start the background remediation loop."""
    global _loop_thread, _remediation_enabled
    
    if _loop_thread and _loop_thread.is_alive():
        return  # Already running
    
    _remediation_enabled = True
    _stop_event.clear()
    _loop_thread = threading.Thread(target=_remediation_loop, daemon=True)
    _loop_thread.start()


def stop_remediation_loop() -> None:
    """Stop the background remediation loop."""
    global _remediation_enabled
    
    _remediation_enabled = False
    _stop_event.set()
    
    if _loop_thread:
        _loop_thread.join(timeout=5)


def get_disabled_services() -> Dict[str, datetime]:
    """Get services with auto-restart disabled."""
    return _disabled_services.copy()


def re_enable_service(service_id: str) -> bool:
    """Re-enable auto-restart for a service."""
    if service_id in _disabled_services:
        del _disabled_services[service_id]
        return True
    return False
