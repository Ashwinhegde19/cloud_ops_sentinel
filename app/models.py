from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime


class Instance(BaseModel):
    instance_id: str
    cpu_usage: List[float]
    ram_usage: List[float]
    last_request: datetime
    tags: Dict[str, str]


class Service(BaseModel):
    service_id: str
    instance_id: str
    name: str
    status: str
    last_restart: datetime


class MetricPoint(BaseModel):
    timestamp: datetime
    cpu: float
    ram: float
    latency_ms: float
    error_rate: float


class AnomalyResult(BaseModel):
    service_id: str
    has_anomaly: bool
    severity: str
    reason: str
    evidence: List[str]


class CostForecast(BaseModel):
    month: str
    predicted_cost: float
    confidence: float