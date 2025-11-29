# Cloud Ops Sentinel - Project Standards

## Project Overview
Cloud Ops Sentinel is an MCP-based cloud operations assistant for hackathon MVP. It uses Modal, Hyperbolic, Blaxel, HuggingFace, SambaNova, and LangChain integrations.

## Code Standards

### Python Style
- Use Python 3.8+ compatible code
- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Use Pydantic models for data validation

### Architecture Principles
- Keep functions short and pure
- JSON-serializable outputs only
- Synchronous code (no async unless required)
- Fail gracefully with simulation fallbacks
- No over-engineering

### File Organization
```
app/
├── models.py           # Pydantic data models
├── config.py           # Environment configuration
├── infra_simulation.py # Mock data generation
├── mcp_server.py       # MCP tool functions
├── modal_client.py     # Modal integration
├── hyperbolic_client.py# Hyperbolic integration
├── blaxel_client.py    # Blaxel integration
├── llm_client.py       # SambaNova/HF LLM
├── orchestrator.py     # LangChain workflows
└── ui_gradio.py        # Gradio 6 UI
```

### Testing
- Use Hypothesis for property-based testing
- Run minimum 100 iterations per property test
- Annotate tests with property numbers from design.md

### Environment
- Use `uv` for fast package management
- Virtual environment in `venv/`
- Activate with: `source venv/bin/activate`

## Sponsor Integration Requirements
- Modal: At least 1 compute function
- Hyperbolic: Embedding API for anomaly detection
- Blaxel: Service restart fallback
- HuggingFace: Gradio 6 UI hosting
- SambaNova: Primary LLM for ops reports
- LangChain: Workflow orchestration
- MCP: 6 core tools exposed
