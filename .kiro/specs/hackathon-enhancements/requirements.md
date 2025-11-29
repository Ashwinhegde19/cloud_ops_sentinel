# Requirements Document

## Introduction

This specification defines three high-impact enhancement features for Cloud Ops Sentinel to maximize hackathon scoring: Ops Chat (agentic tool-calling), Auto-Remediation Mode (autonomous anomaly resolution), and Infra Hygiene Score with PDF Report generation. These features demonstrate advanced MCP + LangChain orchestration, enterprise value, and sponsor integration depth.

## Glossary

- **Ops Chat**: A conversational agent interface that interprets natural language queries and automatically calls MCP tools to fulfill requests
- **Auto-Remediation**: An autonomous loop that detects anomalies, restarts affected services, verifies health, and generates incident reports without human intervention
- **Infra Hygiene Score**: A 0-100 composite score measuring overall infrastructure health based on idle percentage, anomalies, cost risk, and restart failures
- **Agentic Loop**: A LangChain-orchestrated workflow where the LLM decides which tools to call based on context
- **Incident Report**: A structured document summarizing an auto-remediation event including root cause, actions taken, and outcome
- **PDF Report**: A downloadable document containing the 24-hour ops summary with all metrics and recommendations

## Requirements

### Requirement 1: Ops Chat Conversational Agent

**User Story:** As a DevOps engineer, I want to interact with Cloud Ops Sentinel using natural language, so that I can query infrastructure status and execute operations without navigating multiple UI panels.

#### Acceptance Criteria

1. WHEN a user submits a natural language query THEN the System SHALL parse the intent and call appropriate MCP tools automatically
2. WHEN the query requests data (e.g., "list idle instances") THEN the System SHALL return formatted results from the corresponding tool
3. WHEN the query requests an action (e.g., "restart service web-2") THEN the System SHALL execute the action and confirm completion
4. WHEN the query is ambiguous THEN the System SHALL ask clarifying questions before executing
5. WHEN the LLM determines multiple tools are needed THEN the System SHALL chain tool calls and aggregate results
6. WHEN a tool call fails THEN the System SHALL report the error gracefully and suggest alternatives

### Requirement 2: Auto-Remediation Mode

**User Story:** As an SRE, I want Cloud Ops Sentinel to automatically detect and fix service anomalies, so that issues are resolved faster without manual intervention.

#### Acceptance Criteria

1. WHEN auto-remediation mode is enabled THEN the System SHALL continuously monitor all services for anomalies
2. WHEN an anomaly with severity "high" or "critical" is detected THEN the System SHALL automatically trigger a service restart
3. WHEN a restart is triggered THEN the System SHALL wait for completion and verify post-restart health score exceeds 0.7
4. WHEN post-restart health is below 0.7 THEN the System SHALL escalate by generating an alert and disabling auto-restart for that service
5. WHEN auto-remediation completes successfully THEN the System SHALL generate an incident report with root cause, action taken, and outcome
6. WHEN auto-remediation is disabled THEN the System SHALL only detect anomalies without taking action

### Requirement 3: Infra Hygiene Score

**User Story:** As a cloud architect, I want a single score representing overall infrastructure health, so that I can quickly assess operational status and track improvements over time.

#### Acceptance Criteria

1. WHEN a user requests the hygiene score THEN the System SHALL return a score from 0 to 100
2. WHEN computing the score THEN the System SHALL weight factors: idle_percentage (25%), anomaly_count (30%), cost_forecast_risk (25%), restart_failure_rate (20%)
3. WHEN the score is below 50 THEN the System SHALL classify status as "critical"
4. WHEN the score is between 50 and 75 THEN the System SHALL classify status as "needs_attention"
5. WHEN the score is above 75 THEN the System SHALL classify status as "healthy"
6. WHEN returning the score THEN the System SHALL include breakdown by factor and improvement suggestions

### Requirement 4: PDF Report Generation

**User Story:** As a manager, I want to download a PDF summary of the 24-hour ops report, so that I can share infrastructure status with stakeholders who don't have system access.

#### Acceptance Criteria

1. WHEN a user requests a PDF report THEN the System SHALL generate a downloadable PDF document
2. WHEN generating the PDF THEN the System SHALL include sections for executive summary, infra hygiene score, idle instances, anomalies detected, cost forecast, and recommendations
3. WHEN generating the PDF THEN the System SHALL include timestamp and report period
4. WHEN generating the PDF THEN the System SHALL use SambaNova to create narrative summaries for each section
5. WHEN PDF generation fails THEN the System SHALL fall back to generating a Markdown report

### Requirement 5: UI Integration

**User Story:** As a user, I want the new features integrated into the existing Gradio dashboard, so that I can access all functionality from a single interface.

#### Acceptance Criteria

1. WHEN the UI loads THEN the System SHALL display an Ops Chat panel with text input and conversation history
2. WHEN the UI loads THEN the System SHALL display an Auto-Remediation toggle with status indicator and event log
3. WHEN the UI loads THEN the System SHALL display the Infra Hygiene Score as a prominent gauge with breakdown
4. WHEN the UI loads THEN the System SHALL display a "Download PDF Report" button
5. WHEN auto-remediation events occur THEN the System SHALL update the event log in real-time

