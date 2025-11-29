# ☁️ Cloud Ops Sentinel

**AI-Powered Cloud Operations Assistant** - Enterprise-grade infrastructure monitoring, anomaly detection, cost optimization, and automated remediation.

![Cloud Ops Sentinel](https://img.shields.io/badge/Cloud%20Ops-Sentinel-6366f1?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-3776ab?style=flat-square&logo=python)
![Gradio](https://img.shields.io/badge/Gradio-6.0-ff7c00?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## 🎯 One-liner Pitch

> AI-powered cloud operations assistant that detects idle instances, forecasts costs, detects anomalies with embeddings, and provides LLM-generated ops reports through MCP tools.

## ✨ Features

### Core Features
- 📊 **Real-time Dashboard** - Infrastructure health score, instance counts, daily costs
- 🚫 **Idle Resource Detection** - Find underutilized instances with savings calculator
- 💰 **Cost Forecasting** - Predict future costs with confidence intervals
- 🔍 **Anomaly Detection** - AI-powered service health analysis
- 🔄 **Service Control** - Restart services via Modal/Blaxel backends
- 📋 **AI Ops Reports** - LLM-generated infrastructure analysis with recommendations

### 🆕 Advanced Features (Hackathon Enhancements)
- 💬 **Ops Chat** - Natural language interface that auto-calls MCP tools ("Show me idle instances", "Restart svc_web")
- 🤖 **Auto-Remediation** - Autonomous anomaly detection → restart → verify → report loop
- 🏥 **Hygiene Score** - Single 0-100 score measuring overall infrastructure health with weighted factors
- 📥 **PDF/Markdown Reports** - Downloadable reports with SambaNova-generated narratives

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Cloud Ops Sentinel                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Gradio 6   │  │ LangChain   │  │    MCP      │             │
│  │     UI      │──│ Orchestrator│──│   Server    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│         │                │                │                     │
│  ┌──────┴────────────────┴────────────────┴──────┐             │
│  │              Sponsor Integrations              │             │
│  ├────────┬────────┬────────┬────────┬──────────┤             │
│  │ Modal  │Hyper-  │ Blaxel │Samba-  │ Hugging  │             │
│  │Compute │bolic   │  Alt   │Nova    │  Face    │             │
│  │        │Vectors │Compute │  LLM   │  LLM     │             │
│  └────────┴────────┴────────┴────────┴──────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Option 1: One-Command Start (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/cloud-ops-sentinel.git
cd cloud-ops-sentinel

# Run the start script
chmod +x start.sh
./start.sh
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys (optional - works without them)

# Start the UI
python app/ui_gradio.py
```

### Access the Dashboard

Open your browser to: **http://localhost:7860**

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure your API keys:

| Variable | Purpose | Get Key At |
|----------|---------|------------|
| `SAMBANOVA_API_KEY` | Primary LLM for AI reports | https://sambanova.ai |
| `HF_API_KEY` | Fallback LLM + UI hosting | https://huggingface.co/settings/tokens |
| `MODAL_API_TOKEN` | Compute jobs & restarts | https://modal.com/settings |
| `HYPERBOLIC_API_KEY` | Vector embeddings | https://hyperbolic.xyz |
| `BLAXEL_API_KEY` | Alternative compute | https://blaxel.ai |

**Note:** All integrations are optional. The app runs in simulation mode without API keys.

## 🛠️ MCP Tools

Cloud Ops Sentinel exposes 6 core tools via Model Context Protocol:

| Tool | Description |
|------|-------------|
| `list_idle_instances` | Detect idle VMs/containers with cost savings |
| `get_billing_forecast` | Predict monthly costs with confidence |
| `get_metrics` | Get service performance metrics |
| `detect_anomaly` | AI-powered anomaly detection |
| `restart_service` | Restart via Modal or Blaxel |
| `summarize_infra` | LLM-generated ops report |

## 🤖 AI Integrations

### SambaNova (Primary LLM)
- Model: Meta-Llama-3.1-8B-Instruct
- Used for: Ops reports, executive summaries, recommendations

### Hyperbolic (Embeddings)
- Used for: Log analysis, anomaly pattern detection

### LangChain (Orchestration)
- Used for: Multi-step workflows, tool chaining

## 📁 Project Structure

```
cloud-ops-sentinel/
├── app/
│   ├── ui_gradio.py        # Gradio 6 web interface
│   ├── mcp_server.py       # MCP tools implementation
│   ├── llm_client.py       # SambaNova/HF LLM integration
│   ├── orchestrator.py     # LangChain workflows
│   ├── hyperbolic_client.py# Anomaly detection
│   ├── modal_client.py     # Modal compute
│   ├── blaxel_client.py    # Blaxel compute
│   ├── infra_simulation.py # Synthetic data generation
│   ├── models.py           # Pydantic data models
│   ├── config.py           # Configuration management
│   ├── ops_chat.py         # 🆕 Natural language chat agent
│   ├── auto_remediate.py   # 🆕 Auto-remediation engine
│   ├── hygiene_score.py    # 🆕 Infrastructure hygiene scoring
│   └── pdf_report.py       # 🆕 PDF/Markdown report generation
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── start.sh               # Quick start script (Linux/Mac)
├── start.bat              # Quick start script (Windows)
└── README.md              # This file
```

## 🧪 Testing Tools

```bash
# Test all MCP tools
python demo.py --all

# Test specific tool
python demo.py --tool idle
python demo.py --tool forecast
python demo.py --tool metrics
python demo.py --tool anomaly
python demo.py --tool restart
python demo.py --tool report
```

## 🌐 Deploy to Hugging Face Spaces

1. Create a new Space at https://huggingface.co/spaces
2. Choose **Gradio** as the SDK
3. Upload all project files
4. Set environment variables in Space settings
5. The app will auto-deploy from `app/ui_gradio.py`

## 🏆 Sponsor Integrations

This project integrates with hackathon sponsors:

- 🚀 **Modal** - Serverless compute for service restarts
- 🔮 **Hyperbolic** - Vector embeddings for anomaly detection
- ⚡ **Blaxel** - Alternative compute backend
- 🤗 **Hugging Face** - Gradio UI hosting + fallback LLM
- 🧠 **SambaNova** - Primary LLM for AI-powered reports
- 🔗 **LangChain** - Workflow orchestration
- 🔌 **MCP** - Model Context Protocol tools

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

Built with ❤️ for the AI Hackathon
