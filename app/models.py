from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class Instance(BaseModel):
    instance_id: str
    cpu_usage: List[float]
    ram_usage: List[float]
    last_request: datetime
    tags: Dict[str, str]
    idle_state: Optional[bool] = None
    network_activity: Optional[float] = 0.0


class Service(BaseModel):
    service_id: str
    instance_id: str
    name: str
    status: str
    last_restart: datetime
    health_score: Optional[float] = 100.0


class MetricPoint(BaseModel):
    timestamp: datetime
    cpu: float
    ram: float
    latency_ms: float
    error_rate: float
    network_in: Optional[float] = 0.0
    network_out: Optional[float] = 0.0


class AnomalyResult(BaseModel):
    service_id: str
    has_anomaly: bool
    severity: str  # "none", "low", "medium", "high", "critical"
    reason: str
    evidence: List[str]
    anomaly_type: Optional[str] = None  # "cpu_spike", "memory_leak", "latency_surge", "error_burst"
    affected_services: Optional[List[str]] = []
    recommended_action: Optional[str] = None


class CostForecast(BaseModel):
    month: str
    predicted_cost: float
    confidence: float
    narrative: Optional[str] = None
    breakdown: Optional[Dict[str, float]] = None
    risk_factors: Optional[List[str]] = []


class RestartResult(BaseModel):
    service_id: str
    restart_status: str  # "success", "failed", "pending"
    time_taken_ms: float
    post_restart_health: Optional[float] = None
    via: str  # "modal", "blaxel", "simulation"
    timestamp: datetime


class OpsReport(BaseModel):
    generated_at: datetime
    infra_health: str
    idle_waste_summary: str
    anomaly_root_causes: List[str]
    cost_forecast_summary: str
    recommended_actions: List[str]
    full_narrative: str
    sponsor_integrations_used: List[str]


class InfraSummary(BaseModel):
    total_instances: int
    running_instances: int
    idle_instances: int
    error_instances: int
    total_services: int
    healthy_services: int
    degraded_services: int
    total_daily_cost: float
    health_score: float
    regions: List[str]
    last_updated: datetime