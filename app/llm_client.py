import os
import requests
from datetime import datetime
from typing import Dict, Any
from .config import config


def generate_ops_report(context: dict) -> str:
    """Generate operations report via SambaNova, HF, or fallback simulation."""
    sambanova_key = os.getenv("SAMBANOVA_API_KEY")
    hf_key = os.getenv("HF_API_KEY")

    if sambanova_key:
        return _call_sambanova_ops_report(context)
    elif hf_key:
        return _call_hf_ops_report(context)
    else:
        return _simulate_ops_report(context)


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


def _call_sambanova_ops_report(context: dict) -> str:
    """Call SambaNova for operations report."""
    try:
        sambanova_key = os.getenv("SAMBANOVA_API_KEY")
        endpoint = os.getenv("SAMBANOVA_ENDPOINT", "https://api.sambanova.ai/v1")

        instances_summary = context.get("instances_summary", {})
        services_summary = context.get("services_summary", {})
        anomalies_summary = context.get("anomalies_summary", {})
        cost_forecast_summary = context.get("cost_forecast_summary", {})

        prompt = f"""Generate a concise operations report based on this data:

Instances: {instances_summary}
Services: {services_summary}
Anomalies: {anomalies_summary}
Cost Forecast: {cost_forecast_summary}

Provide executive summary, critical issues, cost optimization recommendations, and action items."""

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
            headers=headers
        )
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    except Exception:
        return _simulate_ops_report(context)


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

        response = requests.post(
            f"{endpoint}/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    except Exception:
        return _simulate_explanation(prompt)


def _call_hf_ops_report(context: dict) -> str:
    """Call Hugging Face for operations report."""
    try:
        hf_key = os.getenv("HF_API_KEY")
        model = os.getenv("HF_MODEL", "microsoft/DialoGPT-medium")

        instances_summary = context.get("instances_summary", {})
        services_summary = context.get("services_summary", {})
        anomalies_summary = context.get("anomalies_summary", {})
        cost_forecast_summary = context.get("cost_forecast_summary", {})

        prompt = f"""Cloud Ops Summary:

Instances: {instances_summary}
Services: {services_summary}
Anomalies: {anomalies_summary}
Cost Forecast: {cost_forecast_summary}

Provide operations report with recommendations:"""

        headers = {
            "Authorization": f"Bearer {hf_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 400,
                "temperature": 0.7
            }
        }

        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            json=payload,
            headers=headers
        )
        response.raise_for_status()

        result = response.json()
        return result[0]["generated_text"] if result else "Operations report generated successfully."

    except Exception:
        return _simulate_ops_report(context)


def _call_hf_explanation(prompt: str) -> str:
    """Call Hugging Face for short explanation."""
    try:
        hf_key = os.getenv("HF_API_KEY")
        model = os.getenv("HF_MODEL", "microsoft/DialoGPT-medium")

        headers = {
            "Authorization": f"Bearer {hf_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": f"Brief explanation: {prompt}",
            "parameters": {
                "max_length": 100,
                "temperature": 0.7
            }
        }

        response = requests.post(
            f"https://api-inference.huggingface.co/models/{model}",
            json=payload,
            headers=headers
        )
        response.raise_for_status()

        result = response.json()
        return result[0]["generated_text"] if result else "Brief explanation provided."

    except Exception:
        return _simulate_explanation(prompt)


def _simulate_ops_report(context: dict) -> str:
    """Generate simulated operations report."""
    instances_count = len(context.get("instances_summary", {}).get("instances", []))
    services_count = len(context.get("services_summary", {}).get("services", []))
    anomalies_count = len(context.get("anomalies_summary", {}).get("anomalies", []))
    avg_cost = context.get("cost_forecast_summary", {}).get("avg_monthly_cost", 0)

    return f"""Cloud Operations Report - {datetime.now().strftime("%Y-%m-%d %H:%M")}

Executive Summary:
• {instances_count} instances monitored across {services_count} services
• {anomalies_count} anomalies detected requiring attention
• Average monthly cost forecast: ${avg_cost:.2f}

Critical Issues:
• Service health monitoring active
• Performance thresholds configured
• Cost optimization opportunities identified

Recommendations:
• Review idle instances for cost savings
• Monitor services with high error rates
• Implement automated scaling policies
• Schedule maintenance for degraded services

Action Items:
• Optimize resource allocation based on usage patterns
• Update monitoring thresholds for better coverage
• Review and update alerting policies

Generated via simulation mode."""


def _simulate_explanation(prompt: str) -> str:
    """Generate simulated short explanation."""
    return f"Simulated explanation for '{prompt}': This is a simulated response indicating the system would process your query and provide a detailed explanation. The service is running in fallback mode due to missing API credentials."