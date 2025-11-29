# Design Document

## Overview

This design extends Cloud Ops Sentinel with three high-impact hackathon features: Ops Chat (agentic conversational interface), Auto-Remediation Mode (autonomous anomaly resolution), and Infra Hygiene Score with PDF Report generation. These features demonstrate advanced MCP + LangChain orchestration, enterprise value, and deep sponsor integration.

The design prioritizes:
- **Agentic automation**: LangChain agent with tool-calling for natural language operations
- **Autonomous remediation**: Detect → Restart → Verify → Report loop without human intervention
- **Gamification**: Single 0-100 score for instant infrastructure health assessment
- **Enterprise polish**: Downloadable PDF reports for stakeholder communication

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Enhanced Gradio 6 UI                                │
│  ┌─────────────────┬──────────────────┬─────────────────┬────────────────┐  │
│  │   Ops Chat      │ Auto-Remediation │ Hygiene Score   │  PDF Report    │  │
│  │   Panel         │ Toggle + Log     │ Gauge           │  Download      │  │
│  └────────┬────────┴────────┬─────────┴────────┬────────┴───────┬────────┘  │
└───────────┼─────────────────┼──────────────────┼────────────────┼───────────┘
            │                 │                  │                │
┌───────────▼─────────────────▼──────────────────▼────────────────▼───────────┐
│                        New Feature Modules                                  │
│  ┌─────────────────┬──────────────────┬─────────────────┬────────────────┐  │
│  │  ops_chat.py    │ auto_remediate.py│ hygiene_score.py│ pdf_report.py  │  │
│  │  - ChatAgent    │ - RemediationLoop│ - ScoreCalculator│ - PDFGenerator │  │
│  │  - IntentParser │ - HealthVerifier │ - StatusClassifier│ - MarkdownFallback│
│  └────────┬────────┴────────┬─────────┴────────┬────────┴───────┬────────┘  │
└───────────┼─────────────────┼──────────────────┼────────────────┼───────────┘
            │                 │                  │                │
┌───────────▼─────────────────▼──────────────────▼────────────────▼───────────┐
│                    Existing MCP Server + Orchestrator                       │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ tool_list_idle_instances | tool_detect_anomaly | tool_restart_service│   │
│  │ tool_get_billing_forecast| tool_get_metrics    | tool_summarize_infra│   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
            │
┌───────────▼─────────────────────────────────────────────────────────────────┐
│                    Sponsor Integrations                                     │
│  Modal (Compute) | Hyperbolic (Vectors) | Blaxel (Alt) | SambaNova (LLM)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Ops Chat Agent (`app/ops_chat.py`)

LangChain-powered conversational agent with MCP tool-calling:

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `process_chat_message(message, history)` | `str, List[Dict]` | `ChatResponse` | Process user message and return response |
| `parse_intent(message)` | `str` | `Intent` | Extract intent and entities from message |
| `execute_tool_chain(intents)` | `List[Intent]` | `Dict` | Execute required tools and aggregate results |
| `format_response(results)` | `Dict` | `str` | Format tool results as natural language |

**Intent Types:**
- `query_idle` - List idle instances
- `query_metrics` - Get service metrics
- `query_forecast` - Get billing forecast
- `query_anomaly` - Detect anomalies
- `action_restart` - Restart a service
- `query_summary` - Get infrastructure summary
- `query_hygiene` - Get hygiene score
- `ambiguous` - Needs clarification

### 2. Auto-Remediation Engine (`app/auto_remediate.py`)

Autonomous anomaly detection and remediation loop:

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `start_remediation_loop()` | None | `None` | Start background monitoring |
| `stop_remediation_loop()` | None | `None` | Stop background monitoring |
| `check_all_services()` | None | `List[AnomalyResult]` | Scan all services for anomalies |
| `remediate_service(service_id, anomaly)` | `str, AnomalyResult` | `RemediationResult` | Execute remediation workflow |
| `verify_health(service_id)` | `str` | `float` | Check post-restart health score |
| `generate_incident_report(event)` | `RemediationEvent` | `IncidentReport` | Create incident documentation |

**Remediation Flow:**
1. Detect anomaly via `tool_detect_anomaly()`
2. If severity is "high" or "critical", trigger restart
3. Execute `tool_restart_service()`
4. Wait and verify health > 0.7
5. If health < 0.7, escalate and disable auto-restart for service
6. Generate incident report

### 3. Hygiene Score Calculator (`app/hygiene_score.py`)

Composite infrastructure health scoring:

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `calculate_hygiene_score()` | None | `HygieneScore` | Compute overall score |
| `get_factor_scores()` | None | `Dict[str, float]` | Get individual factor scores |
| `classify_status(score)` | `float` | `str` | Map score to status label |
| `generate_suggestions(factors)` | `Dict` | `List[str]` | Create improvement recommendations |

**Scoring Formula:**
```
score = (
    (100 - idle_percentage) * 0.25 +
    (100 - anomaly_penalty) * 0.30 +
    (100 - cost_risk_penalty) * 0.25 +
    (100 - restart_failure_rate) * 0.20
)
```

### 4. PDF Report Generator (`app/pdf_report.py`)

Enterprise report generation with SambaNova narratives:

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `generate_pdf_report()` | None | `bytes` | Generate PDF document |
| `generate_markdown_report()` | None | `str` | Fallback Markdown generation |
| `create_section_narrative(section, data)` | `str, Dict` | `str` | LLM-generated section text |
| `build_report_data()` | None | `ReportData` | Aggregate all report data |

## Data Models

### ChatResponse
```python
class ChatResponse(BaseModel):
    message: str                    # Response text
    tools_called: List[str]         # Tools invoked
    results: Dict[str, Any]         # Raw tool results
    clarification_needed: bool      # Whether clarification was requested
    timestamp: datetime
```

### Intent
```python
class Intent(BaseModel):
    type: str                       # Intent type (query_idle, action_restart, etc.)
    entities: Dict[str, str]        # Extracted entities (service_id, month, etc.)
    confidence: float               # Intent classification confidence
```

### RemediationEvent
```python
class RemediationEvent(BaseModel):
    event_id: str
    service_id: str
    anomaly: AnomalyResult
    action_taken: str               # "restart", "escalate", "none"
    restart_result: Optional[RestartResult]
    post_health: Optional[float]
    escalated: bool
    timestamp: datetime
```

### IncidentReport
```python
class IncidentReport(BaseModel):
    event_id: str
    service_id: str
    root_cause: str
    action_taken: str
    outcome: str                    # "resolved", "escalated", "failed"
    duration_ms: float
    generated_at: datetime
```

### HygieneScore
```python
class HygieneScore(BaseModel):
    score: float                    # 0-100
    status: str                     # "critical", "needs_attention", "healthy"
    breakdown: Dict[str, float]     # Factor scores
    suggestions: List[str]          # Improvement recommendations
    calculated_at: datetime
```

### ReportData
```python
class ReportData(BaseModel):
    generated_at: datetime
    report_period: str              # e.g., "Last 24 hours"
    executive_summary: str
    hygiene_score: HygieneScore
    idle_instances: List[Instance]
    anomalies: List[AnomalyResult]
    cost_forecast: CostForecast
    recommendations: List[str]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Intent Parsing Correctness
*For any* valid natural language query containing a known intent keyword (e.g., "idle", "restart", "forecast"), the intent parser SHALL return an Intent with the correct type and confidence > 0.5.
**Validates: Requirements 1.1**

### Property 2: Query Response Completeness
*For any* query requesting data or action, the ChatResponse SHALL contain a non-empty message and the tools_called list SHALL include at least one tool name.
**Validates: Requirements 1.2, 1.3**

### Property 3: Ambiguity Detection
*For any* query that lacks specific intent keywords or contains conflicting intents, the system SHALL set clarification_needed=true and return a message asking for clarification.
**Validates: Requirements 1.4**

### Property 4: Multi-Tool Aggregation
*For any* query requiring multiple tools (e.g., "give me a full analysis"), the ChatResponse.tools_called SHALL contain all required tool names and results SHALL contain aggregated data from each tool.
**Validates: Requirements 1.5**

### Property 5: Error Graceful Handling
*For any* tool execution failure, the ChatResponse SHALL contain an error message that does not expose internal details and SHALL suggest alternative actions.
**Validates: Requirements 1.6**

### Property 6: Severity-Based Restart Trigger
*For any* detected anomaly, auto-remediation SHALL trigger a restart if and only if severity is "high" or "critical".
**Validates: Requirements 2.2**

### Property 7: Post-Restart Health Handling
*For any* restart triggered by auto-remediation, if post_health >= 0.7 the event SHALL be marked resolved, otherwise the event SHALL be escalated and auto-restart disabled for that service.
**Validates: Requirements 2.3, 2.4**

### Property 8: Incident Report Completeness
*For any* completed remediation event, the IncidentReport SHALL contain non-empty root_cause, action_taken, and outcome fields.
**Validates: Requirements 2.5**

### Property 9: Disabled Mode Behavior
*For any* anomaly detected when auto-remediation is disabled, no restart action SHALL be triggered and action_taken SHALL be "none".
**Validates: Requirements 2.6**

### Property 10: Hygiene Score Range
*For any* infrastructure state, the calculated hygiene score SHALL be in the range [0, 100].
**Validates: Requirements 3.1**

### Property 11: Hygiene Score Formula
*For any* set of factor values (idle_percentage, anomaly_count, cost_risk, restart_failures), the score SHALL equal the weighted sum: (100-idle)*0.25 + (100-anomaly_penalty)*0.30 + (100-cost_risk)*0.25 + (100-restart_failures)*0.20.
**Validates: Requirements 3.2**

### Property 12: Score Classification Correctness
*For any* hygiene score, status SHALL be "critical" if score < 50, "needs_attention" if 50 <= score <= 75, and "healthy" if score > 75.
**Validates: Requirements 3.3, 3.4, 3.5**

### Property 13: Score Response Completeness
*For any* hygiene score response, the breakdown dict SHALL contain keys for all four factors and suggestions SHALL be a non-empty list.
**Validates: Requirements 3.6**

### Property 14: PDF Content Completeness
*For any* generated PDF report, the document SHALL contain sections titled "Executive Summary", "Infrastructure Hygiene Score", "Idle Instances", "Anomalies Detected", "Cost Forecast", and "Recommendations".
**Validates: Requirements 4.2**

### Property 15: Report Metadata Presence
*For any* generated report (PDF or Markdown), the document SHALL include a timestamp and report period string.
**Validates: Requirements 4.3**

### Property 16: PDF Fallback Behavior
*For any* PDF generation failure, the system SHALL return a valid Markdown string containing the same report sections.
**Validates: Requirements 4.5**

## Error Handling

### Chat Agent Errors
- Invalid or unparseable queries return a friendly message asking for rephrasing
- Tool execution failures are caught and reported without exposing stack traces
- LLM API failures fall back to template-based responses

### Auto-Remediation Errors
- Restart failures trigger escalation rather than retry loops
- Health check timeouts are treated as failures (health = 0)
- Background loop errors are logged but don't crash the application

### PDF Generation Errors
- PDF library failures trigger Markdown fallback
- Missing data sections are filled with "No data available" placeholders
- LLM narrative failures use template-based summaries

## Testing Strategy

### Property-Based Testing Framework
The project will use **Hypothesis** (Python) for property-based testing.

Each property-based test MUST:
1. Be annotated with the property number and requirements reference
2. Run a minimum of 100 iterations
3. Use smart generators that constrain inputs to valid ranges

### Unit Tests
Unit tests cover:
- Intent parsing edge cases (empty strings, special characters)
- Score calculation boundary values (0%, 100%)
- PDF section rendering
- Remediation state transitions

### Test Organization
```
tests/
├── test_ops_chat.py           # Chat agent property tests
├── test_auto_remediate.py     # Remediation loop property tests
├── test_hygiene_score.py      # Score calculation property tests
├── test_pdf_report.py         # Report generation property tests
└── test_integration.py        # End-to-end workflow tests
```

### Test Annotations
Each property-based test will include:
```python
# **Feature: hackathon-enhancements, Property 10: Hygiene Score Range**
# **Validates: Requirements 3.1**
@given(...)
def test_hygiene_score_range(...):
    ...
```
