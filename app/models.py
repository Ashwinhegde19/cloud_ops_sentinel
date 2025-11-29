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

# ============== HACKATHON ENHANCEMENT MODELS ==============

class Intent(BaseModel):
    """Parsed intent from natural language query."""
    type: str  # "query_idle", "query_metrics", "query_forecast", "query_anomaly", "action_restart", "query_summary", "query_hygiene", "ambiguous"
    entities: Dict[str, str] = {}  # Extracted entities (service_id, month, etc.)
    confidence: float = 0.0  # Intent classification confidence


class ChatResponse(BaseModel):
    """Response from the Ops Chat agent."""
    message: str  # Response text
    tools_called: List[str] = []  # Tools invoked
    results: Dict = {}  # Raw tool results
    clarification_needed: bool = False  # Whether clarification was requested
    timestamp: datetime


class RemediationEvent(BaseModel):
    """Event from auto-remediation loop."""
    event_id: str
    service_id: str
    anomaly: Optional[AnomalyResult] = None
    action_taken: str  # "restart", "escalate", "none"
    restart_result: Optional[RestartResult] = None
    post_health: Optional[float] = None
    escalated: bool = False
    timestamp: datetime


class IncidentReport(BaseModel):
    """Incident report generated after remediation."""
    event_id: str
    service_id: str
    root_cause: str
    action_taken: str
    outcome: str  # "resolved", "escalated", "failed"
    duration_ms: float
    generated_at: datetime


class HygieneScore(BaseModel):
    """Infrastructure hygiene score (0-100)."""
    score: float  # 0-100
    status: str  # "critical", "needs_attention", "healthy"
    breakdown: Dict[str, float] = {}  # Factor scores
    suggestions: List[str] = []  # Improvement recommendations
    calculated_at: datetime


class ReportData(BaseModel):
    """Data for PDF/Markdown report generation."""
    generated_at: datetime
    report_period: str  # e.g., "Last 24 hours"
    executive_summary: str
    hygiene_score: Optional[HygieneScore] = None
    idle_instances: List[Instance] = []
    anomalies: List[AnomalyResult] = []
    cost_forecast: Optional[CostForecast] = None
    recommendations: List[str] = []


# ============== AUTH & PLATFORM MANAGEMENT MODELS ==============


class User(BaseModel):
    """User model for authentication."""

    id: str
    username: str
    password_hash: str
    role: str  # "viewer", "operator", "admin"
    email: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True


class Session(BaseModel):
    """Session model for authentication."""

    token: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True


class Platform(BaseModel):
    """Platform connection model."""

    id: str
    name: str
    type: str  # "aws", "gcp", "azure", "custom"
    encrypted_credentials: str
    is_active: bool = True
    last_tested: Optional[datetime] = None
    connection_status: str = "unknown"  # "connected", "failed", "unknown"
    created_at: datetime


class PlatformConfig(BaseModel):
    """Configuration for adding/updating a platform."""

    name: str
    type: str  # "aws", "gcp", "azure", "custom"
    credentials: Dict[str, str]  # Plaintext credentials before encryption


class ApiKey(BaseModel):
    """API key model (internal with encrypted value)."""

    id: str
    name: str
    service: str  # "sambanova", "modal", "hyperbolic", "blaxel", "huggingface"
    encrypted_value: str
    created_at: datetime
    last_used: Optional[datetime] = None


class ApiKeyInfo(BaseModel):
    """API key info for display (masked value)."""

    id: str
    name: str
    service: str
    masked_value: str  # "****xxxx"
    created_at: datetime


class ConnectionResult(BaseModel):
    """Result of platform connection test."""

    platform_id: str
    success: bool
    message: str
    latency_ms: Optional[float] = None
    tested_at: datetime
