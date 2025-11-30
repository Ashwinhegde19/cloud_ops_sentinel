---
title: Cloud Ops Sentinel
emoji: 🛡️
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 5.31.0
app_file: app.py
pinned: false
license: mit
tags:
  - mcp-in-action-track-xx
  - agents
  - cloud-ops
  - devops
---

# Cloud Ops Sentinel 🛡️

**Enterprise Cloud Operations Assistant with AI-Powered Intelligence**

An autonomous AI agent for cloud infrastructure management using MCP (Model Context Protocol) tools.

## 🎯 Track: MCP in Action

This project demonstrates autonomous agent behavior with:
- **Planning**: Analyzes infrastructure state and plans remediation
- **Reasoning**: Uses LLM to interpret metrics and detect anomalies
- **Execution**: Automatically restarts services and optimizes resources

## 🔧 MCP Tools (6 Core Tools)

| Tool | Description |
|------|-------------|
| `list_idle_instances` | Detect underutilized compute instances |
| `get_billing_forecast` | Predict cloud costs for upcoming months |
| `get_metrics` | Retrieve service performance metrics |
| `detect_anomaly` | AI-powered anomaly detection |
| `restart_service` | Automated service restart via Modal/Blaxel |
| `summarize_infra` | LLM-generated infrastructure reports |

## ✨ Features

- 📊 **Dashboard** - Real-time infrastructure overview
- 🚫 **Idle Resources** - Cost optimization recommendations
- 💰 **Cost Forecast** - Predictive billing analysis
- 📈 **Metrics & Anomalies** - Service health monitoring
- 🔄 **Service Control** - One-click service management
- 📝 **Ops Report** - AI-generated PDF reports
- 💬 **Ops Chat** - Natural language infrastructure queries
- 🏥 **Hygiene Score** - Infrastructure health scoring
- 🔧 **Auto-Remediation** - Autonomous issue resolution

## 🏆 Sponsor Integrations

- **Modal** - Serverless compute for ML workloads
- **Hyperbolic** - AI inference optimization
- **Blaxel** - Infrastructure automation
- **HuggingFace** - Gradio UI hosting
- **SambaNova** - LLM inference
- **LangChain** - Workflow orchestration

## 🔐 Authentication

Role-based access control with three roles:
- **Admin** - Full access to all features
- **Operator** - Can restart services and run remediation
- **Viewer** - Read-only dashboard access

*Note: Auth works locally. HF Spaces has Gradio auth limitations.*

## 🚀 Local Setup

```bash
git clone https://github.com/yourusername/cloud-ops-sentinel
cd cloud-ops-sentinel
pip install -r requirements.txt
ENABLE_AUTH=true python app.py
```

## 📹 Demo Video

[Link to demo video]

## 📱 Social Media

[Link to social media post]

## 👤 Team

- **ashwinredmi** - [HuggingFace Profile](https://huggingface.co/ashwinredmi)

## 📄 License

MIT License
