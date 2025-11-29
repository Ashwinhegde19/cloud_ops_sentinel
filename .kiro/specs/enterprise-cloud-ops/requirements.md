# Requirements Document

## Introduction

Cloud Ops Sentinel is an MCP-based intelligent cloud-operations assistant that inspects, analyzes, and optimizes cloud infrastructure using LLM reasoning, vector intelligence, and compute automation. The system provides resource insights, cost forecasting, idle-resource detection, anomaly detection, service restart automation, and human-readable operations summaries through a Gradio 6 interface.

## Glossary

- **MCP Server**: Model Context Protocol server exposing cloud operations tools
- **Instance**: A simulated cloud compute instance with CPU, RAM, and network metrics
- **Service**: A logical service running on one or more instances
- **Idle Instance**: An instance with CPU < 5%, RAM < 15%, network < 1 MB/s, and no requests for > 24 hours
- **Anomaly**: A deviation from normal service behavior detected via metrics analysis
- **Cost Forecast**: Predicted cloud spending based on historical usage patterns
- **Ops Report**: LLM-generated summary of infrastructure health and recommendations
- **Modal**: Serverless compute platform for running jobs
- **Hyperbolic**: Vector embedding and similarity search service
- **Blaxel**: Alternative compute backend for service operations
- **SambaNova**: LLM provider for generating reports and narratives

## Requirements

### Requirement 1: Idle Instance Detection

**User Story:** As a DevOps engineer, I want to identify idle compute instances, so that I can optimize cloud costs by terminating or downsizing unused resources.

#### Acceptance Criteria

1. WHEN a user requests idle instances THEN the System SHALL return a JSON list containing instance_id, avg_cpu, avg_ram, last_request_time, and idle_state for each idle instance
2. WHEN computing idle state THEN the System SHALL classify an instance as idle if avg_cpu < 5%, avg_ram < 15%, network_activity < 1 MB/s, and hours_since_last_request > 24
3. WHEN Modal is available THEN the System SHALL use Modal to generate simulated metrics for idle detection
4. WHEN Modal is unavailable THEN the System SHALL fall back to local simulation for metric generation
5. WHEN idle instances are found THEN the System SHALL include potential monthly savings calculation for each instance

### Requirement 2: Cost Forecast Engine

**User Story:** As a cloud architect, I want to forecast next month's cloud bill, so that I can plan budgets and identify cost optimization opportunities.

#### Acceptance Criteria

1. WHEN a user requests a billing forecast for a specific month THEN the System SHALL return predicted_cost, confidence score, and narrative summary
2. WHEN Hyperbolic is available THEN the System SHALL use vector embeddings for regression-based cost prediction
3. WHEN SambaNova is available THEN the System SHALL generate a human-readable narrative explaining the forecast
4. WHEN generating forecasts THEN the System SHALL include cost breakdown by service tier and region
5. WHEN forecast confidence is below 0.6 THEN the System SHALL include risk factors in the response

### Requirement 3: Service Metrics Retrieval

**User Story:** As an SRE, I want to retrieve performance metrics for a specific service, so that I can monitor service health and troubleshoot issues.

#### Acceptance Criteria

1. WHEN a user requests metrics for a service_id THEN the System SHALL return time-series data including cpu, ram, latency_ms, error_rate, network_in, and network_out
2. WHEN generating metrics THEN the System SHALL provide at least 24 hours of historical data points
3. WHEN the service_id does not exist THEN the System SHALL return an empty metrics array with the service_id
4. WHEN metrics are returned THEN the System SHALL include timestamps in ISO 8601 format

### Requirement 4: Anomaly Detection

**User Story:** As an SRE, I want to detect anomalies in service behavior, so that I can proactively address issues before they impact users.

#### Acceptance Criteria

1. WHEN a user requests anomaly detection for a service_id THEN the System SHALL return has_anomaly, severity, reason, evidence, and anomaly_type
2. WHEN Hyperbolic is available THEN the System SHALL use vector similarity to detect deviations from normal patterns
3. WHEN an anomaly is detected THEN the System SHALL classify severity as none, low, medium, high, or critical
4. WHEN an anomaly is detected THEN the System SHALL provide a recommended_action for remediation
5. WHEN latency exceeds 500ms or error_rate exceeds 10% THEN the System SHALL flag as anomaly with appropriate severity

### Requirement 5: Service Restart Automation

**User Story:** As a DevOps engineer, I want to restart a service with one click, so that I can quickly remediate issues without manual intervention.

#### Acceptance Criteria

1. WHEN a user requests a service restart THEN the System SHALL return restart_status, time_taken_ms, post_restart_health, via, and timestamp
2. WHEN USE_BLAXEL is true THEN the System SHALL use Blaxel API for the restart operation
3. WHEN USE_BLAXEL is false or unset THEN the System SHALL use Modal for the restart operation
4. WHEN neither Modal nor Blaxel is available THEN the System SHALL simulate the restart and return via as "simulation"
5. WHEN restart completes THEN the System SHALL verify post_restart_health score

### Requirement 6: Infrastructure Summary and Ops Report

**User Story:** As a cloud architect, I want a comprehensive infrastructure summary with actionable recommendations, so that I can make informed decisions about resource optimization.

#### Acceptance Criteria

1. WHEN a user requests infrastructure summary THEN the System SHALL return total_instances, running_instances, idle_instances, error_instances, health_score, and total_daily_cost
2. WHEN SambaNova is available THEN the System SHALL generate a full narrative ops report with sections for infra_health, idle_waste_summary, anomaly_root_causes, cost_forecast_summary, and recommended_actions
3. WHEN SambaNova is unavailable THEN the System SHALL fall back to HuggingFace inference for report generation
4. WHEN both LLM providers are unavailable THEN the System SHALL generate a template-based simulation report
5. WHEN generating the report THEN the System SHALL list all sponsor integrations used in the response

### Requirement 7: Gradio UI Dashboard

**User Story:** As a user, I want an intuitive web interface to interact with all cloud operations tools, so that I can monitor and manage infrastructure without using CLI commands.

#### Acceptance Criteria

1. WHEN the application starts THEN the System SHALL display a Gradio 6 interface with sections for Infra Summary, Idle Instances, Cost Forecast, Service Metrics, Anomaly Detection, Restart Panel, and Ops Report
2. WHEN a user clicks an action button THEN the System SHALL call the corresponding MCP tool and display results in the appropriate output area
3. WHEN displaying idle instances THEN the System SHALL show a table with Instance ID, Name, Type, CPU %, Memory %, Cost/Hr, Region, and Monthly Savings
4. WHEN displaying anomalies THEN the System SHALL show risk level, anomaly count, and comparison of baseline vs current metrics
5. WHEN the UI loads THEN the System SHALL initialize within 3 seconds on HuggingFace Spaces CPU environment

### Requirement 8: LangChain Orchestration

**User Story:** As a developer, I want LLM calls routed through LangChain, so that I can leverage tool-calling pipelines and workflow orchestration.

#### Acceptance Criteria

1. WHEN executing multi-step workflows THEN the System SHALL use LangChain to orchestrate tool calls
2. WHEN LangChain is available THEN the System SHALL support cost_optimization, health_check, and full_analysis workflow types
3. WHEN LangChain is unavailable THEN the System SHALL fall back to direct function calls
4. WHEN orchestrating workflows THEN the System SHALL aggregate results from multiple tools into a unified response

### Requirement 9: Sponsor Integration Compliance

**User Story:** As a hackathon participant, I want all sponsor integrations properly implemented, so that the submission qualifies for maximum prize eligibility.

#### Acceptance Criteria

1. WHEN Modal is configured THEN the System SHALL execute at least one Modal Function for compute operations
2. WHEN Hyperbolic is configured THEN the System SHALL use the embedding API for vector operations
3. WHEN Blaxel is configured THEN the System SHALL call Blaxel API for service restart operations
4. WHEN the application runs THEN the System SHALL be hosted on HuggingFace Spaces using Gradio 6
5. WHEN generating reports THEN the System SHALL use SambaNova LLM as the primary provider
6. WHEN the MCP server starts THEN the System SHALL expose all 6 core tools: list_idle_instances, get_billing_forecast, get_metrics, detect_anomaly, restart_service, summarize_infra
