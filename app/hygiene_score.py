"""
Infrastructure Hygiene Score Calculator
Computes a 0-100 score based on idle instances, anomalies, cost risk, and restart failures.
"""

from datetime import datetime
from typing import Dict, List, Tuple
from .models import HygieneScore, AnomalyResult, CostForecast


# Scoring weights
WEIGHT_IDLE = 0.25
WEIGHT_ANOMALY = 0.30
WEIGHT_COST_RISK = 0.25
WEIGHT_RESTART_FAILURE = 0.20


def calculate_hygiene_score(
    total_instances: int,
    idle_instances: int,
    anomalies: List[AnomalyResult],
    cost_forecast: CostForecast,
    restart_failures: int = 0,
    total_restarts: int = 0
) -> HygieneScore:
    """
    Calculate overall infrastructure hygiene score.
    
    Args:
        total_instances: Total number of instances
        idle_instances: Number of idle instances
        anomalies: List of anomaly results
        cost_forecast: Cost forecast data
        restart_failures: Number of failed restarts
        total_restarts: Total restart attempts
    
    Returns:
        HygieneScore with score, status, breakdown, and suggestions
    """
    factors = get_factor_scores(
        total_instances, idle_instances, anomalies, 
        cost_forecast, restart_failures, total_restarts
    )
    
    # Calculate weighted score
    score = (
        factors["idle_score"] * WEIGHT_IDLE +
        factors["anomaly_score"] * WEIGHT_ANOMALY +
        factors["cost_risk_score"] * WEIGHT_COST_RISK +
        factors["restart_score"] * WEIGHT_RESTART_FAILURE
    )
    
    # Clamp to 0-100
    score = max(0.0, min(100.0, score))
    
    status = classify_status(score)
    suggestions = generate_suggestions(factors)
    
    return HygieneScore(
        score=round(score, 1),
        status=status,
        breakdown=factors,
        suggestions=suggestions,
        calculated_at=datetime.now()
    )


def get_factor_scores(
    total_instances: int,
    idle_instances: int,
    anomalies: List[AnomalyResult],
    cost_forecast: CostForecast,
    restart_failures: int,
    total_restarts: int
) -> Dict[str, float]:
    """
    Compute individual factor scores (0-100 each).
    
    Returns:
        Dict with idle_score, anomaly_score, cost_risk_score, restart_score
    """
    # Idle score: 100 - idle_percentage
    if total_instances > 0:
        idle_percentage = (idle_instances / total_instances) * 100
    else:
        idle_percentage = 0
    idle_score = max(0, 100 - idle_percentage)
    
    # Anomaly score: Penalize based on count and severity
    anomaly_penalty = _calculate_anomaly_penalty(anomalies)
    anomaly_score = max(0, 100 - anomaly_penalty)
    
    # Cost risk score: Based on forecast confidence
    cost_risk_penalty = _calculate_cost_risk_penalty(cost_forecast)
    cost_risk_score = max(0, 100 - cost_risk_penalty)
    
    # Restart score: Based on failure rate
    if total_restarts > 0:
        failure_rate = (restart_failures / total_restarts) * 100
    else:
        failure_rate = 0
    restart_score = max(0, 100 - failure_rate)
    
    return {
        "idle_score": round(idle_score, 1),
        "anomaly_score": round(anomaly_score, 1),
        "cost_risk_score": round(cost_risk_score, 1),
        "restart_score": round(restart_score, 1),
        "idle_percentage": round(idle_percentage, 1),
        "anomaly_count": len([a for a in anomalies if a.has_anomaly]),
        "restart_failure_rate": round(failure_rate, 1)
    }


def _calculate_anomaly_penalty(anomalies: List[AnomalyResult]) -> float:
    """Calculate penalty based on anomaly count and severity."""
    severity_weights = {
        "none": 0,
        "low": 5,
        "medium": 15,
        "high": 30,
        "critical": 50
    }
    
    total_penalty = 0
    for anomaly in anomalies:
        if anomaly.has_anomaly:
            weight = severity_weights.get(anomaly.severity, 10)
            total_penalty += weight
    
    # Cap at 100
    return min(100, total_penalty)


def _calculate_cost_risk_penalty(cost_forecast: CostForecast) -> float:
    """Calculate penalty based on cost forecast confidence and risk factors."""
    if not cost_forecast:
        return 20  # Default penalty for missing forecast
    
    # Low confidence = higher risk
    confidence_penalty = (1 - cost_forecast.confidence) * 50
    
    # Risk factors add penalty
    risk_count = len(cost_forecast.risk_factors) if cost_forecast.risk_factors else 0
    risk_penalty = risk_count * 10
    
    return min(100, confidence_penalty + risk_penalty)


def classify_status(score: float) -> str:
    """
    Classify hygiene status based on score.
    
    Args:
        score: Hygiene score (0-100)
    
    Returns:
        "critical" if score < 50
        "needs_attention" if 50 <= score <= 75
        "healthy" if score > 75
    """
    if score < 50:
        return "critical"
    elif score <= 75:
        return "needs_attention"
    else:
        return "healthy"


def generate_suggestions(factors: Dict[str, float]) -> List[str]:
    """
    Generate improvement suggestions based on factor scores.
    
    Args:
        factors: Dict with factor scores
    
    Returns:
        List of actionable suggestions
    """
    suggestions = []
    
    # Idle instances suggestions
    idle_pct = factors.get("idle_percentage", 0)
    if idle_pct > 20:
        suggestions.append(f"Terminate or downsize {idle_pct:.0f}% idle instances to reduce costs")
    elif idle_pct > 10:
        suggestions.append("Review idle instances for potential consolidation")
    
    # Anomaly suggestions
    anomaly_count = factors.get("anomaly_count", 0)
    if anomaly_count > 2:
        suggestions.append(f"Investigate {anomaly_count} service anomalies immediately")
    elif anomaly_count > 0:
        suggestions.append("Monitor detected anomalies and set up alerting")
    
    # Cost risk suggestions
    cost_score = factors.get("cost_risk_score", 100)
    if cost_score < 60:
        suggestions.append("Review cost forecast risk factors and implement budget alerts")
    elif cost_score < 80:
        suggestions.append("Consider reserved instances for predictable workloads")
    
    # Restart failure suggestions
    failure_rate = factors.get("restart_failure_rate", 0)
    if failure_rate > 20:
        suggestions.append("Investigate restart failures - check service dependencies")
    elif failure_rate > 5:
        suggestions.append("Review restart procedures and health check configurations")
    
    # Always add general best practices if score is not perfect
    if not suggestions:
        suggestions.append("Infrastructure is healthy - continue monitoring")
    
    return suggestions
