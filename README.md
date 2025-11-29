# Cloud Ops Sentinel

MCP-based Cloud Operations Assistant for hackathon MVP - minimal, boring, reliable Python code.

## One-liner Pitch

**AI-powered cloud operations assistant that detects idle instances, forecasts costs, detects anomalies, and provides automated remediation through MCP tools.**

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gradio 6 UI   │────│   MCP Server     │────│ Simulation      │
│ (Hugging Face)  │    │ (6 Core Tools)   │    │ Engine          │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                    ┌─────────┼─────────┐
                    │         │         │
            ┌───────▼───┐ ┌───▼───┐ ┌───▼────┐
            │  Modal    │ │Hyper- │ │ Blaxel │
            │(Compute)  │ │bolic  │ │(Alt)   │
            └───────────┘ │(Vector)│ └────────┘
                         └────────┘
                    ┌─────────┼─────────┐
                    │         │         │
            ┌───────▼───┐ ┌───▼───┐ ┌───▼────┐
            │SambaNova  │ │   HF  │ │LangChain│
            │(LLM)      │ │(LLM)  │ │(Orch)  │
            └───────────┘ └───────┘ └────────┘
```

- **MCP Server**: 6 core tools for cloud operations
- **Gradio 6 UI**: Simple web interface hosted on Hugging Face Spaces
- **Simulation Engine**: Synthetic infrastructure data (no real cloud calls)
- **External Integrations**: Modal, Hyperbolic, Blaxel, SambaNova, Hugging Face

## Core Capabilities

1. **list_idle_instances()** - Detect idle VMs/containers from simulated metrics
2. **get_billing_forecast()** - Simple cost forecast based on synthetic metric history
3. **get_metrics(service_id)** - Return metrics for a given service
4. **detect_anomaly(service_id)** - Run anomaly detection on metrics/logs
5. **restart_service(id)** - Simulate service restart via Modal or Blaxel
6. **summarize_infra()** - LLM-generated Ops report (SambaNova or HF fallback)

## Project Structure

```
app/
├── __init__.py              # Package initialization
├── config.py               # Environment variables & API availability checks
├── models.py               # Data classes (Instance, Service, Metrics, etc.)
├── infra_simulation.py     # Synthetic infrastructure data generation
├── modal_client.py         # Modal compute wrapper (stubbed with TODOs)
├── hyperbolic_client.py    # Hyperbolic vector embeddings (stubbed)
├── blaxel_client.py        # Blaxel compute wrapper (stubbed)
├── llm_client.py           # SambaNova + HF LLM integration
├── mcp_server.py           # MCP tools implementation
├── orchestrator.py         # Optional LangChain workflows
└── ui_gradio.py            # Gradio 6 web interface

# Root files
├── app.py                  # Main entry point
├── mcp_server.py           # Direct MCP server execution
├── data_generator.py       # Test data generation
├── requirements.txt        # Python dependencies
├── sponsor_config.py       # Integration configuration
└── .env.example           # Environment variables template
```

## How to Run Locally

### Prerequisites

- Python 3.8+
- pip

### Installation & Setup

```bash
# Clone and setup
git clone <your-repo>
cd cloud_ops_sentinel

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your API keys (optional - runs in simulation mode without)
```

### Run the Application

```bash
# Run with Gradio UI (simulation mode)
python app/ui_gradio.py

# Or run the MCP server directly
python app/mcp_server.py

# Or run the main app
python app.py
```

### Access the UI

- Open browser to `http://localhost:7860`
- All features work in simulation mode without API keys

## How to Deploy on Hugging Face Space

### Method 1: Direct Upload

1. **Create Space**: Go to https://huggingface.co/spaces and create new space
2. **Choose**: Python SDK, Gradio template
3. **Upload**: Copy all files to the space repository
4. **Configure**: The space should auto-build from `app/ui_gradio.py`

### Method 2: Git Integration

```bash
# Clone your space
git clone https://huggingface.co/spaces/YOUR_USERNAME/cloud-ops-sentinel

# Copy project files
cp -r app/ README.md requirements.txt .env.example <space-folder>/

# Commit and push
cd <space-folder>
git add .
git commit -m "Deploy Cloud Ops Sentinel"
git push
```

### Required Files for HF Spaces

- `app/ui_gradio.py` (main entry point)
- `requirements.txt` (dependencies)
- `README.md` (documentation)
- `app/` directory (all modules)

### Environment Variables in HF Spaces

Set in Space settings → Variables:

- `MODAL_API_TOKEN`, `MODAL_APP_NAME`
- `HYPERBOLIC_API_KEY`
- `BLAXEL_API_KEY`, `BLAXEL_ENDPOINT`
- `SAMBANOVA_API_KEY`
- `HF_API_KEY`
- `USE_BLAXEL` (optional, set to "true" to use Blaxel instead of Modal)

## Environment Variables

Required environment variables (optional - simulation mode without them):

```bash
# Modal Configuration
MODAL_API_TOKEN=your_modal_api_token
MODAL_APP_NAME=cloud-ops-sentinel

# Hyperbolic Configuration
HYPERBOLIC_API_KEY=your_hyperbolic_api_key

# Blaxel Configuration
BLAXEL_API_KEY=your_blaxel_api_key
BLAXEL_ENDPOINT=https://api.blaxel.ai/v1

# SambaNova Configuration
SAMBANOVA_API_KEY=your_sambanova_api_key

# Hugging Face Configuration
HF_API_KEY=your_huggingface_api_key

# Application Configuration
USE_BLAXEL=false  # Set to "true" to use Blaxel instead of Modal for restarts
DEBUG=false
HOST=0.0.0.0
PORT=7860
```

## Sponsor Integrations

### Modal

- **Purpose**: Used for simulated compute jobs and service restart
- **Integration**: `app/modal_client.py` - restart_service_via_modal()
- **Fallback**: Simulation mode when MODAL_API_TOKEN missing
- **TODO**: Real Modal deployment, job queue integration

### Hyperbolic

- **Purpose**: Used for embeddings and anomaly detection logic
- **Integration**: `app/hyperbolic_client.py` - detect_anomaly_from_metrics()
- **Fallback**: Random vector simulation when HYPERBOLIC_API_KEY missing
- **TODO**: Real vector similarity for anomaly detection

### Blaxel

- **Purpose**: Used as alternative restart / heavy compute backend
- **Integration**: `app/blaxel_client.py` - restart_service_via_blaxel()
- **Fallback**: Simulation mode when USE_BLAXEL=true but BLAXEL_API_KEY missing
- **TODO**: Real compute job submission

### Hugging Face

- **Purpose**: Gradio UI hosting and optional LLM fallback
- **Integration**: `app/ui_gradio.py` - Web interface, `app/llm_client.py` - LLM fallback
- **Fallback**: Local simulation when HF_API_KEY missing
- **TODO**: Model-specific fine-tuning for ops reports

### SambaNova

- **Purpose**: Primary LLM for ops report and explanations
- **Integration**: `app/llm_client.py` - generate_ops_report()
- **Fallback**: Hugging Face LLM → Simulation when SAMBANOVA_API_KEY missing
- **TODO**: Model optimization for technical documentation

### LangChain

- **Purpose**: Orchestration for LLM calls and tools workflow
- **Integration**: `app/orchestrator.py` - Multi-step operations
- **Fallback**: Direct function calls when LangChain unavailable
- **TODO**: Complex workflow chains, tool composition

### MCP (Model Context Protocol)

- **Purpose**: Tools exposed in `app/mcp_server.py`
- **Integration**: 6 core cloud operations tools
- **Usage**: Direct function calls from UI or external MCP clients
- **Tools**: list_idle_instances, get_billing_forecast, get_metrics, detect_anomaly, restart_service, summarize_infra

## Development Philosophy

- Keep everything simple, direct, explicit, and readable
- Avoid architectural flights of fancy
- Functions should be short and pure
- JSON-serializable outputs only
- Synchronous code (no async unless required)
- Fail gracefully with simulation mode
- No over-engineering, no magic

## Quick Commands Reference

```bash
# Quick start (recommended)
./start.sh          # Linux/Mac
start.bat           # Windows

# Manual setup
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run applications
python app/ui_gradio.py   # Start Gradio UI
python app/mcp_server.py  # Test MCP tools directly
python demo.py           # Run comprehensive demo
python demo.py --tool idle  # Test specific tool

# Additional utilities
python data_generator.py
python -c "from app.config import config; print(config.status())"
```

---

# RUNBOOK

## How to Run Locally

### Step 1: Setup

```bash
# Clone and navigate
git clone <your-repo>
cd cloud_ops_sentinel

# Option 1: Use the startup script (recommended for quick start)
chmod +x start.sh
./start.sh

# Option 2: Manual setup
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment (optional)
cp .env.example .env
# Edit .env with your API keys if available
```

### Step 2: Run the Application

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the Gradio UI (recommended)
python app/ui_gradio.py

# Alternative: Run MCP server directly
python app/mcp_server.py

# Alternative: Run main app
python app.py

# Alternative: Run demo script
python demo.py
```

### Step 3: Access Interface

- Open browser: `http://localhost:7860`
- UI loads with all tools available in simulation mode

## Quick Smoke Test of Each Tool

### Test 1: List Idle Instances

```bash
# Via command line
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -c "from app.mcp_server import tool_list_idle_instances; print(tool_list_idle_instances())"

# Via UI
# 1. Click "List Idle Instances" button
# 2. See formatted list in "Idle Instances" textbox
# 3. Expected: 2-3 fake idle instances with CPU/Memory usage
```

### Test 2: Get Billing Forecast

```bash
# Via command line
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -c "from app.mcp_server import tool_get_billing_forecast; print(tool_get_billing_forecast('2024-12'))"

# Via UI
# 1. Click "Get Billing Forecast" button
# 2. See JSON result in "Billing Forecast" section
# 3. Expected: Month, predicted cost, confidence level
```

### Test 3: Get Metrics & Detect Anomaly

```bash
# Via command line
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -c "from app.mcp_server import tool_get_metrics, tool_detect_anomaly; print('Metrics:', tool_get_metrics('svc_web')); print('Anomaly:', tool_detect_anomaly('svc_web'))"

# Via UI
# 1. Enter "svc_web" in Service ID field
# 2. Click "Get Metrics & Detect Anomaly" button
# 3. See metrics + anomaly detection in "Metrics & Anomalies" section
# 4. Expected: Service metrics + anomaly detection results
```

### Test 4: Restart Service

```bash
# Via command line
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -c "from app.mcp_server import tool_restart_service; print(tool_restart_service('svc_web'))"

# Via UI
# 1. Enter "svc_web" in Service ID field
# 2. Click "Restart Service" button
# 3. See status in "Restart Status" textbox
# 4. Expected: "Service svc_web restart: restarted"
```

### Test 5: Generate Ops Report

```bash
# Via command line
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -c "from app.mcp_server import tool_summarize_infra; result = tool_summarize_infra(); print('Report length:', len(result.get('report', '')))"

# Via UI
# 1. Click "Generate Ops Report" button
# 2. See full report in "Ops Report" textbox
# 3. Expected: Comprehensive infrastructure summary with LLM-generated insights
```

## Example Flow: "Click this, see that"

### Complete Workflow Example

1. **Start**: Open `http://localhost:7860`

2. **Check Infrastructure Health**:

   - Click "List Idle Instances"
   - **See**: 2-3 idle instances with CPU/Memory usage percentages

3. **Get Cost Forecast**:

   - Click "Get Billing Forecast"
   - **See**: JSON with month, predicted cost ($1200-1500), confidence (0.75)

4. **Analyze Specific Service**:

   - Enter "svc_web" in Service ID field
   - Click "Get Metrics & Detect Anomaly"
   - **See**: Metrics data + anomaly detection results (may show true/false)

5. **Take Action**:

   - With "svc_web" still in Service ID field
   - Click "Restart Service"
   - **See**: "Service svc_web restart: restarted"

6. **Generate Summary Report**:
   - Click "Generate Ops Report"
   - **See**: 2-3 paragraph LLM-generated ops report with insights, recommendations

### Expected Results Summary

- **Idle Instances**: Fake instances with realistic CPU/Memory usage
- **Billing Forecast**: Monthly cost prediction with confidence interval
- **Metrics**: Service performance data over time
- **Anomalies**: Detection results with explanations
- **Restart**: Simulated service restart confirmation
- **Ops Report**: Natural language infrastructure summary and recommendations

All tools work without external API keys using simulated data. Add real API keys to `.env` for live integrations.

- Enter "svc_web" in Service ID field
- Click "Get Metrics & Detect Anomaly"
- **See**: Metrics data + anomaly detection results (may show true/false)

5. **Take Action**:

   - With "svc_web" still in Service ID field
   - Click "Restart Service"
   - **See**: "Service svc_web restart: restarted"

6. **Generate Summary Report**:
   - Click "Generate Ops Report"
   - **See**: 2-3 paragraph LLM-generated ops report with insights, recommendations

### Expected Results Summary

- **Idle Instances**: Fake instances with realistic CPU/Memory usage
- **Billing Forecast**: Monthly cost prediction with confidence interval
- **Metrics**: Service performance data over time
- **Anomalies**: Detection results with explanations
- **Restart**: Simulated service restart confirmation
- **Ops Report**: Natural language infrastructure summary and recommendations

All tools work without external API keys using simulated data. Add real API keys to `.env` for live integrations.
