"""
LLM Client for Cloud Ops Sentinel
Supports SambaNova (primary), HuggingFace (fallback), and simulation mode
"""

import os
import requests
from datetime import datetime
from typing import Dict, Any, List, Tuple
from .config import config


# Track which integrations were used
_integrations_used: List[str] = []


def get_integrations_used() -> List[str]:
    """Return list of sponsor integrations used in the last operation."""
    return _integrations_used.copy()


def generate_ops_report(context: dict) -> Dict[str, Any]:
    """Generate operations report via SambaNova, HF, or fallback simulation.
    
    Returns:
        Dict with structured OpsReport fields:
        - infra_health, idle_waste_summary, anomaly_root_causes,
        - cost_forecast_summary, recommended_actions, full_narrative,
        - sponsor_integrations_used
    """
    global _integrations_used
    _integrations_used = []
    
    sambanova_key = os.getenv("SAMBANOVA_API_KEY", "")
    hf_key = os.getenv("HF_API_KEY", "")
    
    # Check if keys are real (not placeholders)
    sambanova_valid = sambanova_key and "your_" not in sambanova_key.lower() and len(sambanova_key) > 10
    hf_valid = hf_key and "your_" not in hf_key.lower() and len(hf_key) > 10

    # Try SambaNova first (primary)
    if sambanova_valid:
        narrative, provider = _call_sambanova_ops_report(context)
        _integrations_used.append("SambaNova")
    # Fallback to HuggingFace
    elif hf_valid:
        narrative, provider = _call_hf_ops_report(context)
        _integrations_used.append("HuggingFace")
    # Final fallback to simulation
    else:
        narrative, provider = _simulate_ops_report(context)
        _integrations_used.append("Simulation")
    
    # Always add MCP as it's the transport layer
    _integrations_used.append("MCP")
    
    # Build structured report
    return _build_structured_report(context, narrative, provider)


def _build_structured_report(context: dict, narrative: str, provider: str) -> Dict[str, Any]:
    """Build structured OpsReport from context and narrative."""
    # Extract data from context
    instances = context.get("instances", [])
    services = context.get("services", [])
    idle_instances = context.get("idle_instances", [])
    anomalies = context.get("anomalies", [])
    billing = context.get("billing_forecast", {})
    
    # Calculate infra health
    total = len(instances)
    idle_count = len(idle_instances)
    anomaly_count = sum(1 for a in anomalies if a.get("has_anomaly", False))
    
    if anomaly_count == 0 and idle_count <= 1:
        infra_health = "Healthy"
    elif anomaly_count <= 2 and idle_count <= 3:
        infra_health = "Degraded"
    else:
        infra_health = "Critical"
    
    # Build idle waste summary
    idle_cost = sum(0.10 * 24 * 30 for _ in idle_instances)  # Estimate
    idle_waste_summary = f"{idle_count} idle instances detected, potential monthly savings: ${idle_cost:.2f}"
    
    # Extract anomaly root causes
    anomaly_root_causes = []
    for a in anomalies:
        if a.get("has_anomaly"):
            cause = f"{a.get('service_id', 'unknown')}: {a.get('anomaly_type', 'unknown')} - {a.get('reason', 'no details')}"
            anomaly_root_causes.append(cause)
    
    # Cost forecast summary
    predicted = billing.get("predicted_cost", 0)
    confidence = billing.get("confidence", 0)
    cost_forecast_summary = f"Predicted monthly cost: ${predicted:.2f} (confidence: {confidence:.0%})"
    
    # Recommended actions
    recommended_actions = []
    if idle_count > 0:
        recommended_actions.append(f"Terminate or downsize {idle_count} idle instances")
    if anomaly_count > 0:
        recommended_actions.append(f"Investigate {anomaly_count} service anomalies")
    if predicted > 1500:
        recommended_actions.append("Review cost optimization opportunities")
    recommended_actions.append("Enable auto-scaling for variable workloads")
    recommended_actions.append("Set up alerting for anomaly detection")
    
    return {
        "generated_at": datetime.now().isoformat(),
        "infra_health": infra_health,
        "idle_waste_summary": idle_waste_summary,
        "anomaly_root_causes": anomaly_root_causes,
        "cost_forecast_summary": cost_forecast_summary,
        "recommended_actions": recommended_actions,
        "full_narrative": narrative,
        "sponsor_integrations_used": _integrations_used.copy(),
        "provider": provider
    }


def generate_short_explanation(prompt: str) -> str:
    """Generate short explanation via SambaNova, HF, or fallback simulation."""
    sambanova_key = os.getenv("SAMBANOVA_API_KEY")
    hf_key = os.getenv("HF_API_KEY")

    if sambanova_key:
        return _call_sambanova_explanation(prompt)
    elif hf_key:
        return _call_hf_explanation(prompt)
    else:
        return _simulate_explanation(prompt)


def _call_sambanova_ops_report(context: dict) -> Tuple[str, str]:
    """Call SambaNova for operations report. Returns (narrative, provider)."""
    try:
        sambanova_key = os.getenv("SAMBANOVA_API_KEY")
        endpoint = os.getenv("SAMBANOVA_ENDPOINT", "https://api.sambanova.ai/v1")

        instances = context.get("instances", [])
        services = context.get("services", [])
        idle_instances = context.get("idle_instances", [])
        anomalies = context.get("anomalies", [])
        billing = context.get("billing_forecast", {})

        prompt = f"""Generate a concise cloud operations report based on this infrastructure data:

Infrastructure Summary:
- Total instances: {len(instances)}
- Idle instances: {len(idle_instances)}
- Total services: {len(services)}
- Anomalies detected: {sum(1 for a in anomalies if a.get('has_anomaly', False))}

Cost Forecast:
- Predicted cost: ${billing.get('predicted_cost', 0):.2f}
- Confidence: {billing.get('confidence', 0):.0%}

Provide:
1. Executive summary (2-3 sentences)
2. Critical issues requiring attention
3. Cost optimization recommendations
4. Prioritized action items"""

        headers = {
            "Authorization": f"Bearer {sambanova_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "Meta-Llama-3.1-8B-Instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 800,
            "temperature": 0.3
        }

        response = requests.post(
            f"{endpoint}/chat/completions",
            json=payload,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"], "sambanova"

    except Exception as e:
        # Fallback to simulation on error
        return _simulate_ops_report(context)


def _call_hf_ops_report(context: dict) -> Tuple[str, str]:
    """Call Hugging Face for operations report. Returns (narrative, provider)."""
    try:
        hf_key = os.getenv("HF_API_KEY")
        model = os.getenv("HF_MODEL", "microsoft/DialoGPT-medium")

        instances = context.get("instances", [])
        idle_instances = context.get("idle_instances", [])
        anomalies = context.get("anomalies", [])
        billing = context.get("billing_forecast", {})

        prompt = f"""Cloud Ops Report:
Instances: {len(instances)}, Idle: {len(idle_instances)}
Anomalies: {sum(1 for a in anomalies if a.get('has_anomaly', False))}
Cost: ${billing.get('predicted_cost', 0):.2f}

Generate operations summary:"""

        headers = {
            "Authorization": f"Bearer {hf_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": prompt,
            "parameters": {"max_length": 400, "temperature": 0.7}
        }

        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()

        result = response.json()
        text = result[0]["generated_text"] if result else "Report generated."
        return text, "huggingface"

    except Exception:
        return _simulate_ops_report(context)


def _simulate_ops_report(context: dict) -> Tuple[str, str]:
    """Generate simulated operations report. Returns (narrative, provider)."""
    instances = context.get("instances", [])
    services = context.get("services", [])
    idle_instances = context.get("idle_instances", [])
    anomalies = context.get("anomalies", [])
    billing = context.get("billing_forecast", {})
    
    anomaly_count = sum(1 for a in anomalies if a.get("has_anomaly", False))
    predicted_cost = billing.get("predicted_cost", 0)

    narrative = f"""Cloud Operations Report - {datetime.now().strftime("%Y-%m-%d %H:%M")}

EXECUTIVE SUMMARY
Monitoring {len(instances)} instances across {len(services)} services. {len(idle_instances)} idle instances identified for potential cost savings. {anomaly_count} anomalies detected requiring attention. Predicted monthly cost: ${predicted_cost:.2f}.

INFRASTRUCTURE HEALTH
• Active instances: {len(instances) - len(idle_instances)}
• Idle instances: {len(idle_instances)} (candidates for termination)
• Services monitored: {len(services)}
• Anomalies detected: {anomaly_count}

COST ANALYSIS
• Current forecast: ${predicted_cost:.2f}/month
• Potential savings from idle instances: ${len(idle_instances) * 72:.2f}/month
• Confidence level: {billing.get('confidence', 0.75):.0%}

RECOMMENDATIONS
1. Review and terminate idle instances to reduce costs
2. Investigate detected anomalies for root cause analysis
3. Implement auto-scaling policies for variable workloads
4. Set up proactive alerting for performance thresholds
5. Schedule regular cost optimization reviews

ACTION ITEMS
• [HIGH] Address {anomaly_count} service anomalies
• [MEDIUM] Evaluate {len(idle_instances)} idle instances for termination
• [LOW] Review and update monitoring thresholds

Generated via simulation mode (no LLM API keys configured)."""

    return narrative, "simulation"


def _call_sambanova_explanation(prompt: str) -> str:
    """Call SambaNova for short explanation."""
    try:
        sambanova_key = os.getenv("SAMBANOVA_API_KEY")
        endpoint = os.getenv("SAMBANOVA_ENDPOINT", "https://api.sambanova.ai/v1")

        headers = {
            "Authorization": f"Bearer {sambanova_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "Meta-Llama-3.1-8B-Instruct",
            "messages": [{"role": "user", "content": f"Explain briefly: {prompt}"}],
            "max_tokens": 150,
            "temperature": 0.3
        }

        response = requests.post(f"{endpoint}/chat/completions", json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    except Exception:
        return _simulate_explanation(prompt)


def _call_hf_explanation(prompt: str) -> str:
    """Call Hugging Face for short explanation."""
    try:
        hf_key = os.getenv("HF_API_KEY")
        model = os.getenv("HF_MODEL", "microsoft/DialoGPT-medium")

        headers = {"Authorization": f"Bearer {hf_key}", "Content-Type": "application/json"}
        payload = {"inputs": f"Brief explanation: {prompt}", "parameters": {"max_length": 100, "temperature": 0.7}}

        response = requests.post(f"https://api-inference.huggingface.co/models/{model}", json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result[0]["generated_text"] if result else "Explanation provided."

    except Exception:
        return _simulate_explanation(prompt)


def _simulate_explanation(prompt: str) -> str:
    """Generate simulated short explanation."""
    return f"Explanation for '{prompt}': This is a simulated response. Configure SAMBANOVA_API_KEY or HF_API_KEY for LLM-powered explanations."
