# Design Document

## Overview

Cloud Ops Sentinel is an enterprise-grade MCP-based cloud operations assistant. The system architecture follows a layered approach with a Gradio 6 UI frontend, MCP Server middleware exposing 6 core tools, and multiple backend integrations (Modal, Hyperbolic, Blaxel, SambaNova, HuggingFace) with simulation fallbacks.

The design prioritizes:
- **Graceful degradation**: All external integrations have simulation fallbacks
- **JSON-serializable outputs**: All tool responses are structured JSON
- **Synchronous execution**: No async complexity unless required
- **Sponsor compliance**: All hackathon sponsor integrations are properly wired

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    HuggingFace Spaces                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   Gradio 6 UI (ui_gradio.py)              │  │
│  │  ┌─────────┬─────────┬─────────┬─────────┬─────────────┐  │  │
│  │  │ Infra   │ Idle    │ Cost    │ Anomaly │ Ops Report  │  │  │
│  │  │ Summary │ Detect  │ Forecast│ Detect  │ Generator   │  │  │
│  │  └────┬────┴────┬────┴────┬────┴────┬────┴──────┬──────┘  │  │
│  └───────┼─────────┼─────────┼─────────┼───────────┼─────────┘  │
│          │         │         │         │           │            │
│  ┌───────▼─────────▼─────────▼─────────▼───────────▼─────────┐  │
│  │                   MCP Server (mcp_server.py)              │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │ tool_list_idle_instances() │ tool_get_billing_forecast│ │  │
│  │  │ tool_get_metrics()         │ tool_detect_anomaly()    │ │  │
│  │  │ tool_restart_service()     │ tool_summarize_infra()   │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  └───────┬─────────┬─────────┬─────────┬───────────┬─────────┘  │
└──────────┼─────────┼─────────┼─────────┼───────────┼────────────┘
           │         │         │         │           │
    ┌──────▼──┐ ┌────▼────┐ ┌──▼───┐ ┌───▼────┐ ┌────▼─────┐
    │  Modal  │ │Hyperbolic│ │Blaxel│ │SambaNova│ │HuggingFace│
    │(Compute)│ │(Vectors) │ │(Alt) │ │ (LLM)  │ │  (LLM)   │
    └────┬────┘ └────┬─────┘ └──┬───┘ └───┬────┘ └────┬─────┘
         │          │          │         │           │
    ┌────▼──────────▼──────────▼─────────▼───────────▼─────┐
    │              Simulation Fallback Layer               │
    │              (infra_simulation.py)                   │
    └──────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. MCP Server (`app/mcp_server.py`)

Exposes 6 core tools as functions:

| Tool | Input | Output | Description |
|------|-------|--------|-------------|
| `tool_list_idle_instances()` | None | `{idle_instances: Instance[]}` | Detect idle VMs |
| `tool_get_billing_forecast(month)` | `str` | `CostForecast` | Cost prediction |
| `tool_get_metrics(service_id)` | `str` | `{service_id, metrics: MetricPoint[]}` | Service metrics |
| `tool_detect_anomaly(service_id)` | `str` | `AnomalyResult` | Anomaly detection |
| `tool_restart_service(service_id)` | `str` | `RestartResult` | Service restart |
| `tool_summarize_infra()` | None | `{report, summary_data}` | Ops report |

### 2. Infrastructure Simulation (`app/infra_simulation.py`)

Generates realistic mock data:
- `generate_fake_infra()` → `(List[Instance], List[Service])`
- `generate_fake_metrics(service_id, hours)` → `List[MetricPoint]`
- `compute_idle_instances(instances)` → `List[Instance]`
- `compute_infra_summary(instances, services)` → `InfraSummary`
- `estimate_monthly_cost(instances, days)` → `Dict`

### 3. Client Modules

#### Modal Client (`app/modal_client.py`)
- `simulate_metrics_job(services)` → `Dict[str, List[MetricPoint]]`
- `restart_service_via_modal(service_id)` → `Dict`

#### Hyperbolic Client (`app/hyperbolic_client.py`)
- `embed_logs(log_lines)` → `List[List[float]]`
- `detect_anomaly_from_metrics(service_id, metrics)` → `AnomalyResult`

#### Blaxel Client (`app/blaxel_client.py`)
- `restart_service_via_blaxel(service_id)` → `Dict`
- `run_heavy_analysis(service_id, metrics)` → `Dict`

#### LLM Client (`app/llm_client.py`)
- `generate_ops_report(context)` → `str`
- `generate_short_explanation(prompt)` → `str`

### 4. Orchestrator (`app/orchestrator.py`)

LangChain-style workflow orchestration:
- `execute_workflow(workflow_type, params)` → `Dict`
- Supported workflows: `cost_optimization`, `health_check`, `full_analysis`

### 5. Gradio UI (`app/ui_gradio.py`)

7-section dashboard:
1. Infrastructure Summary
2. Idle Instances Table
3. Cost Forecast Panel
4. Service Metrics Display
5. Anomaly Detection Results
6. Service Restart Panel
7. Full Ops Report

## Data Models

### Instance
```python
class Instance(BaseModel):
    instance_id: str
    cpu_usage: List[float]      # 24-hour samples
    ram_usage: List[float]      # 24-hour samples
    last_request: datetime
    tags: Dict[str, str]
    idle_state: Optional[bool]
    network_activity: Optional[float]
```

### Service
```python
class Service(BaseModel):
    service_id: str
    instance_id: str
    name: str
    status: str                 # "healthy", "degraded", "stopped", "error"
    last_restart: datetime
    health_score: Optional[float]
```

### MetricPoint
```python
class MetricPoint(BaseModel):
    timestamp: datetime
    cpu: float
    ram: float
    latency_ms: float
    error_rate: float
    network_in: Optional[float]
    network_out: Optional[float]
```

### AnomalyResult
```python
class AnomalyResult(BaseModel):
    service_id: str
    has_anomaly: bool
    severity: str               # "none", "low", "medium", "high", "critical"
    reason: str
    evidence: List[str]
    anomaly_type: Optional[str]
    affected_services: Optional[List[str]]
    recommended_action: Optional[str]
```

### CostForecast
```python
class CostForecast(BaseModel):
    month: str
    predicted_cost: float
    confidence: float
    narrative: Optional[str]
    breakdown: Optional[Dict[str, float]]
    risk_factors: Optional[List[str]]
```

### RestartResult
```python
class RestartResult(BaseModel):
    service_id: str
    restart_status: str         # "success", "failed", "pending"
    time_taken_ms: float
    post_restart_health: Optional[float]
    via: str                    # "modal", "blaxel", "simulation"
    timestamp: datetime
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Idle Instance Classification Correctness
*For any* instance with metrics, the idle_state classification SHALL be true if and only if avg_cpu < 5%, avg_ram < 15%, network_activity < 1 MB/s, and hours_since_last_request > 24.
**Validates: Requirements 1.2**

### Property 2: Idle Instance Output Structure
*For any* call to list_idle_instances(), the response SHALL contain an idle_instances array where each element has instance_id, cpu_usage, ram_usage, last_request, and tags fields.
**Validates: Requirements 1.1**

### Property 3: Cost Forecast Output Structure
*For any* call to get_billing_forecast(month), the response SHALL contain month, predicted_cost, and confidence fields with predicted_cost > 0 and 0 <= confidence <= 1.
**Validates: Requirements 2.1**

### Property 4: Metrics Time Series Length
*For any* call to get_metrics(service_id) with a valid service, the response SHALL contain at least 24 MetricPoint entries.
**Validates: Requirements 3.2**

### Property 5: Metrics Field Completeness
*For any* MetricPoint in a metrics response, the point SHALL contain timestamp, cpu, ram, latency_ms, and error_rate fields with valid numeric values.
**Validates: Requirements 3.1**

### Property 6: Anomaly Severity Enum Validity
*For any* AnomalyResult, the severity field SHALL be one of: "none", "low", "medium", "high", or "critical".
**Validates: Requirements 4.3**

### Property 7: Anomaly Threshold Detection
*For any* service metrics where avg_latency > 500ms OR avg_error_rate > 0.1, the detect_anomaly() response SHALL have has_anomaly=true.
**Validates: Requirements 4.5**

### Property 8: Restart Result Structure
*For any* call to restart_service(service_id), the response SHALL contain service_id, status, and via fields where via is one of "modal", "blaxel", or "simulation".
**Validates: Requirements 5.1, 5.4**

### Property 9: Backend Selection Based on Configuration
*For any* restart operation, when USE_BLAXEL=true the via field SHALL be "blaxel" or "blaxel-sim", otherwise it SHALL be "modal" or "simulation".
**Validates: Requirements 5.2, 5.3**

### Property 10: Infrastructure Summary Completeness
*For any* call to summarize_infra(), the summary_data SHALL contain instances, services, idle_instances, billing_forecast, and anomalies fields.
**Validates: Requirements 6.1**

### Property 11: LLM Provider Fallback Chain
*For any* ops report generation, the system SHALL try SambaNova first, then HuggingFace, then simulation, returning a non-empty report string in all cases.
**Validates: Requirements 6.2, 6.3, 6.4**

### Property 12: MCP Tools Availability
*For any* MCP server initialization, all 6 tools (tool_list_idle_instances, tool_get_billing_forecast, tool_get_metrics, tool_detect_anomaly, tool_restart_service, tool_summarize_infra) SHALL be callable functions.
**Validates: Requirements 9.6**

### Property 13: Workflow Aggregation
*For any* orchestrator workflow execution, the response SHALL contain results from all constituent tool calls aggregated into a single response object.
**Validates: Requirements 8.4**

## Error Handling

### API Failures
- All external API calls (Modal, Hyperbolic, Blaxel, SambaNova, HuggingFace) are wrapped in try/except blocks
- On failure, the system falls back to simulation mode
- Error details are logged but not exposed to users

### Invalid Inputs
- Invalid service_id returns empty metrics array with the service_id echoed back
- Invalid month format in billing forecast uses current month as default
- Missing required fields in requests return descriptive error messages

### Configuration Errors
- Missing API keys trigger simulation mode automatically
- Config validation happens at startup via `config.is_*_available()` methods
- Environment variable parsing errors use sensible defaults

## Testing Strategy

### Property-Based Testing Framework
The project will use **Hypothesis** (Python) for property-based testing.

Each property-based test MUST:
1. Be annotated with the property number and requirements reference
2. Run a minimum of 100 iterations
3. Use smart generators that constrain inputs to valid ranges

### Unit Tests
Unit tests cover:
- Specific edge cases (empty inputs, boundary values)
- Integration points between components
- Error condition handling

### Test Organization
```
tests/
├── test_models.py           # Data model validation
├── test_infra_simulation.py # Simulation logic
├── test_mcp_server.py       # MCP tool functions
├── test_idle_detection.py   # Property tests for idle detection
├── test_cost_forecast.py    # Property tests for forecasting
├── test_anomaly_detection.py# Property tests for anomalies
├── test_restart_service.py  # Property tests for restart
├── test_llm_client.py       # LLM fallback chain tests
└── test_orchestrator.py     # Workflow orchestration tests
```

### Test Annotations
Each property-based test will include:
```python
# **Feature: enterprise-cloud-ops, Property 1: Idle Instance Classification Correctness**
# **Validates: Requirements 1.2**
@given(...)
def test_idle_classification_correctness(...):
    ...
```
