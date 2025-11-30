#!/usr/bin/env python3
"""
Cloud Ops Sentinel - Gradio 6 UI
Enterprise-grade cloud operations dashboard with modern styling and charts
"""

import gradio as gr
import json
import sys
import os
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import random

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()


def markdown_to_html(text: str) -> str:
    """Convert markdown formatting to HTML for display."""
    if not text:
        return ""
    # Convert **bold** to <strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color: #e2e8f0;">\1</strong>', text)
    # Convert *italic* to <em>
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Convert numbered lists (1. item)
    text = re.sub(r'^(\d+)\.\s+(.+)$', r'<div style="margin: 8px 0; padding-left: 20px;"><span style="color: #6366f1; font-weight: 600;">\1.</span> \2</div>', text, flags=re.MULTILINE)
    # Convert bullet points
    text = re.sub(r'^[-•]\s+(.+)$', r'<div style="margin: 4px 0; padding-left: 20px;">• \1</div>', text, flags=re.MULTILINE)
    # Convert newlines to <br> for proper spacing
    text = text.replace('\n\n', '</p><p style="margin: 12px 0;">')
    text = text.replace('\n', '<br>')
    return f'<p style="margin: 12px 0;">{text}</p>'

# Add parent directory to path for imports when running as script
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Import tool functions
try:
    from .mcp_server import (
        tool_list_idle_instances,
        tool_get_billing_forecast,
        tool_get_metrics,
        tool_detect_anomaly,
        tool_restart_service,
        tool_summarize_infra
    )
except ImportError:
    from app.mcp_server import (
        tool_list_idle_instances,
        tool_get_billing_forecast,
        tool_get_metrics,
        tool_detect_anomaly,
        tool_restart_service,
        tool_summarize_infra
    )


# ============== CUSTOM CSS FOR ATTRACTIVE UI ==============
CUSTOM_CSS = """
/* Global Styles */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0d1b2a 100%) !important;
    min-height: 100vh;
}

/* Header Styling */
.header-container {
    background: linear-gradient(90deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    backdrop-filter: blur(10px);
}

/* Card Styling */
.metric-card {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 12px;
    padding: 20px;
    margin: 8px 0;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.metric-card:hover {
    border-color: rgba(99, 102, 241, 0.5);
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(99, 102, 241, 0.2);
}

/* Status Badges */
.status-healthy {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 12px;
}

.status-warning {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 12px;
}

.status-critical {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 12px;
}

/* Button Styling */
.primary-btn {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4) !important;
}

.primary-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6) !important;
}

/* Tab Styling */
.tabs {
    background: transparent !important;
}

.tab-nav {
    background: rgba(30, 41, 59, 0.5) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
}

.tab-nav button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}

.tab-nav button.selected {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
}

/* Output Styling */
.output-markdown {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    color: #e2e8f0 !important;
}

/* Sponsor Badge */
.sponsor-badge {
    display: inline-flex;
    align-items: center;
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 8px;
    padding: 6px 12px;
    margin: 4px;
    font-size: 13px;
    color: #a5b4fc;
}

/* Glow Effects */
.glow-text {
    text-shadow: 0 0 20px rgba(99, 102, 241, 0.5);
}

/* Stats Grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin: 16px 0;
}

.stat-item {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}

.stat-value {
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.stat-label {
    font-size: 12px;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}
"""


# ============== FORMATTING FUNCTIONS ==============

def format_idle_instances(result: Dict[str, Any]) -> str:
    """Format idle instances with attractive styling."""
    instances = result.get("idle_instances", [])
    total_savings = result.get("total_monthly_savings", 0)
    
    if not instances:
        return """
<div style="text-align: center; padding: 40px;">
    <div style="font-size: 64px; margin-bottom: 16px;">✅</div>
    <h2 style="color: #10b981; margin-bottom: 8px;">All Clear!</h2>
    <p style="color: #94a3b8;">No idle instances found. Your resources are being utilized efficiently.</p>
</div>
"""

    output = f"""
<div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.05) 100%); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 16px; padding: 24px; margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
        <div>
            <h2 style="color: #fca5a5; margin: 0; font-size: 24px;">🚫 {len(instances)} Idle Instances Detected</h2>
            <p style="color: #94a3b8; margin: 8px 0 0 0;">Resources with low utilization that could be terminated</p>
        </div>
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 16px 24px; border-radius: 12px; text-align: center;">
            <div style="font-size: 28px; font-weight: 700; color: white;">${total_savings:.2f}</div>
            <div style="font-size: 12px; color: rgba(255,255,255,0.8); text-transform: uppercase;">Monthly Savings</div>
        </div>
    </div>
</div>

<div style="display: grid; gap: 16px;">
"""
    
    for i, inst in enumerate(instances, 1):
        cpu_list = inst.get('cpu_usage', [])
        ram_list = inst.get('ram_usage', [])
        avg_cpu = sum(cpu_list) / len(cpu_list) if cpu_list else 0
        avg_ram = sum(ram_list) / len(ram_list) if ram_list else 0
        region = inst.get('tags', {}).get('region', 'N/A')
        tier = inst.get('tags', {}).get('tier', 'N/A')
        savings = inst.get('monthly_savings', 0)
        
        tier_color = {"production": "#ef4444", "staging": "#f59e0b", "development": "#10b981"}.get(tier, "#6366f1")
        
        output += f"""
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 12px; padding: 20px; transition: all 0.3s ease;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
            <div>
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <span style="font-size: 20px;">🖥️</span>
                    <span style="font-size: 18px; font-weight: 600; color: #e2e8f0;">{inst.get('instance_id', 'N/A')}</span>
                    <span style="background: {tier_color}; color: white; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase;">{tier}</span>
                </div>
                <div style="display: flex; gap: 24px; flex-wrap: wrap;">
                    <div style="color: #94a3b8;">
                        <span style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Region</span>
                        <div style="color: #e2e8f0; font-weight: 500;">{region}</div>
                    </div>
                    <div style="color: #94a3b8;">
                        <span style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">CPU Usage</span>
                        <div style="color: #fca5a5; font-weight: 500;">{avg_cpu:.1f}%</div>
                    </div>
                    <div style="color: #94a3b8;">
                        <span style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">RAM Usage</span>
                        <div style="color: #fca5a5; font-weight: 500;">{avg_ram:.1f}%</div>
                    </div>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 24px; font-weight: 700; color: #10b981;">${savings:.2f}</div>
                <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">Potential Savings</div>
            </div>
        </div>
    </div>
"""
    
    output += "</div>"
    return output


def format_billing_forecast(result: Dict[str, Any]) -> str:
    """Format billing forecast with attractive styling."""
    predicted = result.get('predicted_cost', 0)
    confidence = result.get('confidence', 0)
    savings = result.get('potential_savings', 0)
    breakdown = result.get("breakdown", {})
    risk_factors = result.get("risk_factors", [])
    narrative = result.get("narrative", "")
    
    confidence_color = "#10b981" if confidence >= 0.8 else "#f59e0b" if confidence >= 0.6 else "#ef4444"
    
    output = f"""
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;">
    <div style="background: linear-gradient(145deg, rgba(99, 102, 241, 0.2) 0%, rgba(99, 102, 241, 0.05) 100%); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 16px; padding: 24px; text-align: center;">
        <div style="font-size: 36px; font-weight: 700; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">${predicted:.2f}</div>
        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">Predicted Cost</div>
    </div>
    <div style="background: linear-gradient(145deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.05) 100%); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 16px; padding: 24px; text-align: center;">
        <div style="font-size: 36px; font-weight: 700; color: #10b981;">${savings:.2f}</div>
        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">Potential Savings</div>
    </div>
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 24px; text-align: center;">
        <div style="font-size: 36px; font-weight: 700; color: {confidence_color};">{confidence:.0%}</div>
        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">Confidence</div>
    </div>
</div>
"""
    
    if breakdown:
        output += """
<div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 24px; margin-bottom: 16px;">
    <h3 style="color: #e2e8f0; margin: 0 0 16px 0; font-size: 16px;">💳 Cost Breakdown by Tier</h3>
    <div style="display: grid; gap: 12px;">
"""
        tier_colors = {"production": "#ef4444", "staging": "#f59e0b", "development": "#10b981"}
        total = sum(breakdown.values()) or 1
        
        for tier, cost in breakdown.items():
            pct = (cost / total) * 100
            color = tier_colors.get(tier, "#6366f1")
            output += f"""
        <div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="color: #e2e8f0; font-weight: 500; text-transform: capitalize;">{tier}</span>
                <span style="color: #94a3b8;">${cost:.2f} ({pct:.0f}%)</span>
            </div>
            <div style="background: rgba(99, 102, 241, 0.1); border-radius: 4px; height: 8px; overflow: hidden;">
                <div style="background: {color}; height: 100%; width: {pct}%; border-radius: 4px;"></div>
            </div>
        </div>
"""
        output += "</div></div>"
    
    if risk_factors:
        output += """
<div style="background: linear-gradient(145deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 16px; padding: 24px; margin-bottom: 16px;">
    <h3 style="color: #fbbf24; margin: 0 0 12px 0; font-size: 16px;">⚠️ Risk Factors</h3>
    <ul style="margin: 0; padding-left: 20px; color: #fcd34d;">
"""
        for risk in risk_factors:
            output += f'<li style="margin-bottom: 8px;">{risk}</li>'
        output += "</ul></div>"
    
    if narrative:
        output += f"""
<div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 24px;">
    <h3 style="color: #e2e8f0; margin: 0 0 12px 0; font-size: 16px;">📝 Analysis</h3>
    <p style="color: #94a3b8; margin: 0; line-height: 1.6;">{narrative}</p>
</div>
"""
    
    return output


def format_metrics_and_anomalies(metrics_result: Dict[str, Any], anomaly_result: Dict[str, Any]) -> str:
    """Format metrics and anomalies with attractive styling."""
    service_id = metrics_result.get('service_id', 'N/A')
    metrics = metrics_result.get("metrics", [])
    has_anomaly = anomaly_result.get("has_anomaly", False)
    severity = anomaly_result.get("severity", "none")
    
    # Calculate averages
    if metrics:
        avg_cpu = sum(m.get('cpu', 0) for m in metrics) / len(metrics)
        avg_ram = sum(m.get('ram', 0) for m in metrics) / len(metrics)
        avg_latency = sum(m.get('latency_ms', 0) for m in metrics) / len(metrics)
        avg_error = sum(m.get('error_rate', 0) for m in metrics) / len(metrics) * 100
    else:
        avg_cpu = avg_ram = avg_latency = avg_error = 0
    
    severity_config = {
        "none": {"color": "#10b981", "bg": "rgba(16, 185, 129, 0.1)", "border": "rgba(16, 185, 129, 0.3)", "icon": "✅", "label": "Healthy"},
        "low": {"color": "#fbbf24", "bg": "rgba(251, 191, 36, 0.1)", "border": "rgba(251, 191, 36, 0.3)", "icon": "🟡", "label": "Low"},
        "medium": {"color": "#f97316", "bg": "rgba(249, 115, 22, 0.1)", "border": "rgba(249, 115, 22, 0.3)", "icon": "🟠", "label": "Medium"},
        "high": {"color": "#ef4444", "bg": "rgba(239, 68, 68, 0.1)", "border": "rgba(239, 68, 68, 0.3)", "icon": "🔴", "label": "High"},
        "critical": {"color": "#dc2626", "bg": "rgba(220, 38, 38, 0.1)", "border": "rgba(220, 38, 38, 0.3)", "icon": "🚨", "label": "Critical"}
    }
    
    sev = severity_config.get(severity, severity_config["none"])
    
    # CPU/RAM color based on value
    cpu_color = "#10b981" if avg_cpu < 60 else "#f59e0b" if avg_cpu < 80 else "#ef4444"
    ram_color = "#10b981" if avg_ram < 60 else "#f59e0b" if avg_ram < 80 else "#ef4444"
    latency_color = "#10b981" if avg_latency < 200 else "#f59e0b" if avg_latency < 500 else "#ef4444"
    error_color = "#10b981" if avg_error < 1 else "#f59e0b" if avg_error < 5 else "#ef4444"
    
    output = f"""
<div style="background: linear-gradient(135deg, {sev['bg']} 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid {sev['border']}; border-radius: 16px; padding: 24px; margin-bottom: 24px;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
        <div>
            <h2 style="color: #e2e8f0; margin: 0; font-size: 24px;">📊 {service_id}</h2>
            <p style="color: #94a3b8; margin: 8px 0 0 0;">{len(metrics)} metric samples analyzed</p>
        </div>
        <div style="background: {sev['bg']}; border: 1px solid {sev['border']}; padding: 12px 20px; border-radius: 12px; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 24px;">{sev['icon']}</span>
            <div>
                <div style="font-size: 14px; font-weight: 600; color: {sev['color']};">{sev['label']}</div>
                <div style="font-size: 11px; color: #94a3b8;">Anomaly Status</div>
            </div>
        </div>
    </div>
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px;">
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 20px; text-align: center;">
        <div style="font-size: 32px; font-weight: 700; color: {cpu_color};">{avg_cpu:.1f}%</div>
        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">CPU Usage</div>
        <div style="background: rgba(99, 102, 241, 0.1); border-radius: 4px; height: 6px; margin-top: 12px; overflow: hidden;">
            <div style="background: {cpu_color}; height: 100%; width: {min(avg_cpu, 100)}%; border-radius: 4px;"></div>
        </div>
    </div>
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 20px; text-align: center;">
        <div style="font-size: 32px; font-weight: 700; color: {ram_color};">{avg_ram:.1f}%</div>
        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">RAM Usage</div>
        <div style="background: rgba(99, 102, 241, 0.1); border-radius: 4px; height: 6px; margin-top: 12px; overflow: hidden;">
            <div style="background: {ram_color}; height: 100%; width: {min(avg_ram, 100)}%; border-radius: 4px;"></div>
        </div>
    </div>
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 20px; text-align: center;">
        <div style="font-size: 32px; font-weight: 700; color: {latency_color};">{avg_latency:.0f}ms</div>
        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">Avg Latency</div>
    </div>
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 20px; text-align: center;">
        <div style="font-size: 32px; font-weight: 700; color: {error_color};">{avg_error:.2f}%</div>
        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">Error Rate</div>
    </div>
</div>
"""
    
    if has_anomaly:
        anomaly_type = anomaly_result.get('anomaly_type', 'Unknown')
        reason = anomaly_result.get('reason', 'N/A')
        action = anomaly_result.get('recommended_action', 'N/A')
        evidence = anomaly_result.get("evidence", [])
        
        output += f"""
<div style="background: linear-gradient(145deg, {sev['bg']} 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid {sev['border']}; border-radius: 16px; padding: 24px; margin-bottom: 16px;">
    <h3 style="color: {sev['color']}; margin: 0 0 16px 0; font-size: 18px;">⚠️ Anomaly Detected</h3>
    <div style="display: grid; gap: 12px;">
        <div style="display: flex; gap: 8px;">
            <span style="color: #94a3b8; min-width: 80px;">Type:</span>
            <span style="color: #e2e8f0; font-weight: 500;">{anomaly_type}</span>
        </div>
        <div style="display: flex; gap: 8px;">
            <span style="color: #94a3b8; min-width: 80px;">Reason:</span>
            <span style="color: #e2e8f0;">{reason}</span>
        </div>
    </div>
</div>

<div style="background: linear-gradient(145deg, rgba(16, 185, 129, 0.1) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 16px; padding: 24px;">
    <h3 style="color: #10b981; margin: 0 0 12px 0; font-size: 18px;">💡 Recommended Action</h3>
    <p style="color: #e2e8f0; margin: 0; line-height: 1.6;">{action}</p>
</div>
"""
        
        if evidence:
            output += """
<div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 24px; margin-top: 16px;">
    <h3 style="color: #e2e8f0; margin: 0 0 12px 0; font-size: 16px;">📋 Evidence</h3>
    <ul style="margin: 0; padding-left: 20px; color: #94a3b8;">
"""
            for e in evidence[:5]:
                output += f'<li style="margin-bottom: 6px;">{e}</li>'
            output += "</ul></div>"
    
    return output


def format_restart_result(result: Dict[str, Any]) -> str:
    """Format restart result with attractive styling."""
    status = result.get("restart_status", "unknown")
    service_id = result.get('service_id', 'N/A')
    time_taken = result.get('time_taken_ms', 0)
    backend = result.get('via', 'unknown')
    health = result.get("post_restart_health", 0)
    timestamp = result.get('timestamp', 'N/A')
    
    is_success = status == "success"
    status_color = "#10b981" if is_success else "#ef4444"
    status_bg = "rgba(16, 185, 129, 0.1)" if is_success else "rgba(239, 68, 68, 0.1)"
    status_border = "rgba(16, 185, 129, 0.3)" if is_success else "rgba(239, 68, 68, 0.3)"
    status_icon = "✅" if is_success else "❌"
    
    health_color = "#10b981" if health >= 90 else "#f59e0b" if health >= 70 else "#ef4444"
    
    return f"""
<div style="background: linear-gradient(135deg, {status_bg} 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid {status_border}; border-radius: 16px; padding: 32px; text-align: center; margin-bottom: 24px;">
    <div style="font-size: 64px; margin-bottom: 16px;">{status_icon}</div>
    <h2 style="color: {status_color}; margin: 0 0 8px 0; font-size: 28px;">Service {status.title()}</h2>
    <p style="color: #94a3b8; margin: 0;">{service_id} has been restarted</p>
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 20px; text-align: center;">
        <div style="font-size: 28px; font-weight: 700; color: #6366f1;">{time_taken:.0f}ms</div>
        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">Time Taken</div>
    </div>
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 20px; text-align: center;">
        <div style="font-size: 28px; font-weight: 700; color: {health_color};">{health:.0f}%</div>
        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">Post-Restart Health</div>
    </div>
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 20px; text-align: center;">
        <div style="font-size: 20px; font-weight: 600; color: #a855f7; text-transform: capitalize;">{backend}</div>
        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">Backend Used</div>
    </div>
</div>

<div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 16px; margin-top: 16px; text-align: center;">
    <span style="color: #94a3b8; font-size: 13px;">🕐 Completed at {timestamp}</span>
</div>
"""


def format_ops_report(result: Dict[str, Any]) -> str:
    """Format ops report with attractive styling."""
    report = result.get("report", {})
    summary = result.get("summary", {})
    
    health = report.get("infra_health", "Unknown")
    health_config = {
        "Healthy": {"color": "#10b981", "bg": "rgba(16, 185, 129, 0.1)", "border": "rgba(16, 185, 129, 0.3)", "icon": "🟢"},
        "Degraded": {"color": "#f59e0b", "bg": "rgba(245, 158, 11, 0.1)", "border": "rgba(245, 158, 11, 0.3)", "icon": "🟡"},
        "Critical": {"color": "#ef4444", "bg": "rgba(239, 68, 68, 0.1)", "border": "rgba(239, 68, 68, 0.3)", "icon": "🔴"}
    }
    h = health_config.get(health, {"color": "#94a3b8", "bg": "rgba(148, 163, 184, 0.1)", "border": "rgba(148, 163, 184, 0.3)", "icon": "❓"})
    
    generated_at = report.get('generated_at', datetime.now().isoformat())
    
    output = f"""
<div style="background: linear-gradient(135deg, {h['bg']} 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid {h['border']}; border-radius: 20px; padding: 32px; margin-bottom: 24px; text-align: center;">
    <div style="font-size: 48px; margin-bottom: 12px;">{h['icon']}</div>
    <h1 style="color: #e2e8f0; margin: 0 0 8px 0; font-size: 32px;">Infrastructure {health}</h1>
    <p style="color: #94a3b8; margin: 0; font-size: 14px;">Report generated at {generated_at[:19]}</p>
</div>
"""
    
    if summary:
        total = summary.get('total_instances', 0)
        running = summary.get('running_instances', 0)
        idle = summary.get('idle_instances', 0)
        health_score = summary.get('health_score', 0)
        daily_cost = summary.get('total_daily_cost', 0)
        
        score_color = "#10b981" if health_score >= 90 else "#f59e0b" if health_score >= 70 else "#ef4444"
        
        output += f"""
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-bottom: 24px;">
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 20px; text-align: center;">
        <div style="font-size: 36px; font-weight: 700; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{total}</div>
        <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">Total Instances</div>
    </div>
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 20px; text-align: center;">
        <div style="font-size: 36px; font-weight: 700; color: #10b981;">{running}</div>
        <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">Running</div>
    </div>
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 20px; text-align: center;">
        <div style="font-size: 36px; font-weight: 700; color: #f59e0b;">{idle}</div>
        <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">Idle</div>
    </div>
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 20px; text-align: center;">
        <div style="font-size: 36px; font-weight: 700; color: {score_color};">{health_score:.0f}%</div>
        <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">Health Score</div>
    </div>
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 20px; text-align: center;">
        <div style="font-size: 36px; font-weight: 700; color: #6366f1;">${daily_cost:.0f}</div>
        <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">Daily Cost</div>
    </div>
</div>
"""
    
    # Idle waste summary
    idle_summary = report.get("idle_waste_summary", "")
    if idle_summary:
        output += f"""
<div style="background: linear-gradient(145deg, rgba(16, 185, 129, 0.1) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 16px; padding: 24px; margin-bottom: 16px;">
    <h3 style="color: #10b981; margin: 0 0 12px 0; font-size: 18px;">💰 Cost Optimization Opportunity</h3>
    <p style="color: #e2e8f0; margin: 0; line-height: 1.6;">{idle_summary}</p>
</div>
"""
    
    # Anomaly root causes
    anomalies = report.get("anomaly_root_causes", [])
    if anomalies:
        output += """
<div style="background: linear-gradient(145deg, rgba(245, 158, 11, 0.1) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 16px; padding: 24px; margin-bottom: 16px;">
    <h3 style="color: #fbbf24; margin: 0 0 16px 0; font-size: 18px;">⚠️ Anomaly Root Causes</h3>
    <div style="display: grid; gap: 8px;">
"""
        for a in anomalies[:5]:
            output += f'<div style="background: rgba(245, 158, 11, 0.1); border-radius: 8px; padding: 12px; color: #fcd34d;">• {a}</div>'
        output += "</div></div>"
    
    # Recommended actions
    actions = report.get("recommended_actions", [])
    if actions:
        output += """
<div style="background: linear-gradient(145deg, rgba(99, 102, 241, 0.1) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 16px; padding: 24px; margin-bottom: 16px;">
    <h3 style="color: #a5b4fc; margin: 0 0 16px 0; font-size: 18px;">📝 Recommended Actions</h3>
    <div style="display: grid; gap: 8px;">
"""
        for i, action in enumerate(actions[:5], 1):
            output += f"""
        <div style="background: rgba(99, 102, 241, 0.1); border-radius: 8px; padding: 12px; display: flex; align-items: center; gap: 12px;">
            <span style="background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600;">{i}</span>
            <span style="color: #e2e8f0;">{action}</span>
        </div>
"""
        output += "</div></div>"
    
    # Sponsor integrations
    integrations = result.get("sponsor_integrations_used", [])
    if integrations:
        output += """
<div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 24px;">
    <h3 style="color: #e2e8f0; margin: 0 0 16px 0; font-size: 16px;">🔌 Integrations Used</h3>
    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
"""
        for integration in integrations:
            output += f'<span style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 20px; padding: 6px 14px; color: #a5b4fc; font-size: 13px;">{integration}</span>'
        output += "</div></div>"
    
    # Full narrative - convert markdown to HTML
    narrative = report.get("full_narrative", "")
    if narrative:
        formatted_narrative = markdown_to_html(narrative[:2500])
        output += f"""
<div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 24px; margin-top: 16px;">
    <h3 style="color: #e2e8f0; margin: 0 0 16px 0; font-size: 16px;">📄 Full Report</h3>
    <div style="color: #94a3b8; line-height: 1.8;">{formatted_narrative}</div>
</div>
"""
    
    return output


def format_infra_summary(result: Dict[str, Any]) -> str:
    """Format infrastructure summary with attractive styling."""
    summary = result.get("summary", {})
    
    health_score = summary.get("health_score", 0)
    score_color = "#10b981" if health_score >= 90 else "#f59e0b" if health_score >= 70 else "#ef4444"
    score_icon = "🟢" if health_score >= 90 else "🟡" if health_score >= 70 else "🔴"
    
    total = summary.get('total_instances', 0)
    running = summary.get('running_instances', 0)
    idle = summary.get('idle_instances', 0)
    error = summary.get('error_instances', 0)
    total_services = summary.get('total_services', 0)
    healthy_services = summary.get('healthy_services', 0)
    degraded_services = summary.get('degraded_services', 0)
    daily_cost = summary.get('total_daily_cost', 0)
    regions = summary.get('regions', [])
    
    return f"""
<div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.1) 100%); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 20px; padding: 32px; margin-bottom: 24px; text-align: center;">
    <div style="font-size: 72px; font-weight: 800; color: {score_color}; line-height: 1;">{health_score:.0f}%</div>
    <div style="font-size: 16px; color: #94a3b8; margin-top: 8px;">{score_icon} Infrastructure Health Score</div>
</div>

<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; margin-bottom: 24px;">
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 24px;">
        <h3 style="color: #e2e8f0; margin: 0 0 20px 0; font-size: 16px; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px;">🖥️</span> Instances
        </h3>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;">
            <div style="text-align: center;">
                <div style="font-size: 32px; font-weight: 700; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{total}</div>
                <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">Total</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 32px; font-weight: 700; color: #10b981;">{running}</div>
                <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">Running</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 32px; font-weight: 700; color: #f59e0b;">{idle}</div>
                <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">Idle</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 32px; font-weight: 700; color: #ef4444;">{error}</div>
                <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">Error</div>
            </div>
        </div>
    </div>
    
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 24px;">
        <h3 style="color: #e2e8f0; margin: 0 0 20px 0; font-size: 16px; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px;">⚙️</span> Services
        </h3>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
            <div style="text-align: center;">
                <div style="font-size: 32px; font-weight: 700; background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{total_services}</div>
                <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">Total</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 32px; font-weight: 700; color: #10b981;">{healthy_services}</div>
                <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">Healthy</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 32px; font-weight: 700; color: #f59e0b;">{degraded_services}</div>
                <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase;">Degraded</div>
            </div>
        </div>
    </div>
</div>

<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px;">
    <div style="background: linear-gradient(145deg, rgba(16, 185, 129, 0.1) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 16px; padding: 24px; text-align: center;">
        <div style="font-size: 36px; font-weight: 700; color: #10b981;">${daily_cost:.2f}</div>
        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px;">Daily Cost</div>
    </div>
    <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 24px;">
        <div style="font-size: 14px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">Active Regions</div>
        <div style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;">
            {"".join([f'<span style="background: rgba(99, 102, 241, 0.2); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 8px; padding: 6px 12px; color: #a5b4fc; font-size: 13px;">{r}</span>' for r in regions])}
        </div>
    </div>
</div>
"""


# ============== NEW FEATURE IMPORTS ==============
try:
    from .ops_chat import process_chat_message
    from .auto_remediate import (
        is_enabled, enable_remediation, disable_remediation,
        get_event_log, start_remediation_loop, stop_remediation_loop
    )
    from .hygiene_score import calculate_hygiene_score
    from .pdf_report import generate_markdown_report, build_report_data
except ImportError:
    from app.ops_chat import process_chat_message
    from app.auto_remediate import (
        is_enabled, enable_remediation, disable_remediation,
        get_event_log, start_remediation_loop, stop_remediation_loop
    )
    from app.hygiene_score import calculate_hygiene_score
    from app.pdf_report import generate_markdown_report, build_report_data


# ============== NEW FEATURE FORMATTING ==============

def format_chat_response(message: str, history: list) -> Tuple[str, list]:
    """Process chat message and return formatted response with full conversation history."""
    if not message.strip():
        return _build_conversation_html(history), history
    
    response = process_chat_message(message, history)
    
    # Update history with new exchange
    new_history = history + [{"user": message, "assistant": response.message, "tools": response.tools_called}]
    
    # Build full conversation HTML
    return _build_conversation_html(new_history), new_history


def _build_conversation_html(history: list) -> str:
    """Build HTML for the full conversation history with auto-scroll to bottom."""
    if not history:
        return '''<div style="min-height: 150px; display: flex; align-items: center; justify-content: center; background: linear-gradient(145deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.7) 100%); border: 1px dashed rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 24px;">
            <div style="text-align: center;">
                <div style="font-size: 32px; margin-bottom: 8px;">💬</div>
                <p style="color: #64748b; margin: 0;">Ask me anything about your infrastructure!</p>
                <p style="color: #475569; font-size: 12px; margin-top: 4px;">Try the quick actions above or type your own question</p>
            </div>
        </div>'''
    
    # Use flex column-reverse to auto-scroll to bottom (newest messages visible)
    # Outer container with reverse flex, inner container with normal order
    conversation_html = '''<div style="display: flex; flex-direction: column-reverse; max-height: 500px; overflow-y: auto; background: linear-gradient(145deg, rgba(30, 41, 59, 0.3) 0%, rgba(15, 23, 42, 0.5) 100%); border-radius: 12px;">
<div style="padding: 16px;">'''
    
    for i, exchange in enumerate(history):
        user_msg = exchange.get("user", "")
        assistant_msg = exchange.get("assistant", "")
        tools = exchange.get("tools", [])
        
        # Format assistant message with line breaks
        formatted_msg = assistant_msg.replace('• ', '<br>• ').replace('\n\n', '<br><br>').replace('\n', '<br>')
        if formatted_msg.startswith('<br>'):
            formatted_msg = formatted_msg[4:]
        
        # Tool badges
        tools_html = ""
        if tools:
            tools_html = '<div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px;">'
            for t in tools:
                tools_html += f'<span style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(139, 92, 246, 0.3) 100%); color: #a5b4fc; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 500;">🔧 {t}</span>'
            tools_html += '</div>'
        
        # Add separator between exchanges (except first)
        if i > 0:
            conversation_html += '<div style="border-top: 1px solid rgba(99, 102, 241, 0.1); margin: 16px 0;"></div>'
        
        conversation_html += f'''
    <!-- Exchange {i+1} -->
    <div style="margin-bottom: 16px;">
        <!-- User Question -->
        <div style="margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px;">👤</span>
                <span style="color: #94a3b8; font-size: 12px; font-weight: 500;">You:</span>
            </div>
            <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 12px 16px; margin-left: 36px;">
                <div style="color: #e2e8f0; font-size: 14px; font-weight: 500;">{user_msg}</div>
            </div>
        </div>
        
        <!-- Assistant Response -->
        <div>
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px;">🤖</span>
                <span style="color: #94a3b8; font-size: 12px; font-weight: 500;">Sentinel:</span>
            </div>
            <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 16px 20px; margin-left: 36px;">
                <div style="color: #e2e8f0; font-size: 14px; line-height: 1.8;">{formatted_msg}</div>
                {tools_html}
            </div>
        </div>
    </div>
'''
    
    # Close both inner and outer divs
    conversation_html += '</div></div>'
    return conversation_html


def format_hygiene_score() -> str:
    """Get and format the hygiene score."""
    try:
        report_data = build_report_data()
        score = report_data.hygiene_score
        
        if not score:
            return "<p>Unable to calculate hygiene score</p>"
        
        # Color based on status
        status_colors = {
            "healthy": {"color": "#10b981", "bg": "rgba(16, 185, 129, 0.15)", "border": "rgba(16, 185, 129, 0.5)", "icon": "🟢", "glow": "0 0 30px rgba(16, 185, 129, 0.4)"},
            "needs_attention": {"color": "#f59e0b", "bg": "rgba(245, 158, 11, 0.15)", "border": "rgba(245, 158, 11, 0.5)", "icon": "🟡", "glow": "0 0 30px rgba(245, 158, 11, 0.4)"},
            "critical": {"color": "#ef4444", "bg": "rgba(239, 68, 68, 0.15)", "border": "rgba(239, 68, 68, 0.5)", "icon": "🔴", "glow": "0 0 30px rgba(239, 68, 68, 0.4)"}
        }
        s = status_colors.get(score.status, status_colors["needs_attention"])
        
        # Build breakdown HTML with icons
        factor_icons = {"idle": "💤", "anomaly": "⚠️", "cost_risk": "💰", "restart": "🔄"}
        breakdown_html = ""
        for factor, value in score.breakdown.items():
            if factor.endswith("_score"):
                key = factor.replace("_score", "")
                label = key.replace("_", " ").title()
                icon = factor_icons.get(key, "📊")
                bar_color = "#10b981" if value >= 80 else "#f59e0b" if value >= 50 else "#ef4444"
                breakdown_html += f"""
                <div style="margin: 12px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="color: #e2e8f0; font-size: 13px;">{icon} {label}</span>
                        <span style="color: {bar_color}; font-size: 14px; font-weight: 600;">{value:.0f}</span>
                    </div>
                    <div style="background: rgba(99, 102, 241, 0.1); border-radius: 6px; height: 10px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, {bar_color} 0%, {bar_color}dd 100%); height: 100%; width: {value}%; border-radius: 6px; transition: width 0.5s ease;"></div>
                    </div>
                </div>
                """
        
        # Build suggestions HTML
        suggestions_html = ""
        for i, sug in enumerate(score.suggestions[:3], 1):
            suggestions_html += f'<div style="display: flex; align-items: flex-start; margin: 10px 0;"><span style="color: #6366f1; font-weight: 600; margin-right: 10px;">{i}.</span><span style="color: #cbd5e1; line-height: 1.5;">{sug}</span></div>'
        
        return f"""
<div style="text-align: center; margin-bottom: 32px; padding: 24px;">
    <div style="background: {s['bg']}; border: 3px solid {s['border']}; border-radius: 50%; width: 180px; height: 180px; margin: 0 auto; display: flex; flex-direction: column; justify-content: center; align-items: center; box-shadow: {s['glow']};">
        <div style="font-size: 56px; font-weight: 800; color: {s['color']}; text-shadow: 0 2px 10px rgba(0,0,0,0.3);">{score.score:.0f}</div>
        <div style="font-size: 16px; color: #94a3b8; font-weight: 500;">/ 100</div>
    </div>
    <div style="margin-top: 20px;">
        <span style="font-size: 32px;">{s['icon']}</span>
        <div style="color: {s['color']}; font-size: 22px; font-weight: 700; margin-top: 8px; text-transform: uppercase; letter-spacing: 2px;">{score.status.replace('_', ' ')}</div>
    </div>
</div>

<div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 16px; padding: 20px; margin-bottom: 20px;">
    <h4 style="color: #e2e8f0; margin: 0 0 16px 0; font-size: 16px; display: flex; align-items: center;">
        <span style="margin-right: 8px;">📊</span> Score Breakdown
    </h4>
    {breakdown_html}
</div>

<div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 16px; padding: 20px;">
    <h4 style="color: #e2e8f0; margin: 0 0 16px 0; font-size: 16px; display: flex; align-items: center;">
        <span style="margin-right: 8px;">💡</span> Recommendations
    </h4>
    {suggestions_html}
</div>
"""
    except Exception as e:
        return f"<p style='color: #ef4444;'>Error calculating score: {str(e)}</p>"


def format_remediation_status() -> str:
    """Format auto-remediation status and event log."""
    enabled = is_enabled()
    events = get_event_log()
    
    # Status card with animation effect
    status_color = "#10b981" if enabled else "#ef4444"
    status_bg = "rgba(16, 185, 129, 0.15)" if enabled else "rgba(239, 68, 68, 0.15)"
    status_border = "rgba(16, 185, 129, 0.4)" if enabled else "rgba(239, 68, 68, 0.4)"
    status_glow = "0 0 20px rgba(16, 185, 129, 0.3)" if enabled else "0 0 20px rgba(239, 68, 68, 0.3)"
    
    status_html = f"""
<div style="background: {status_bg}; border: 2px solid {status_border}; border-radius: 16px; padding: 24px; margin-bottom: 20px; text-align: center; box-shadow: {status_glow};">
    <div style="font-size: 48px; margin-bottom: 12px;">{'🤖' if enabled else '🔒'}</div>
    <div style="color: {status_color}; font-size: 24px; font-weight: 700; text-transform: uppercase; letter-spacing: 2px;">
        {'ACTIVE' if enabled else 'INACTIVE'}
    </div>
    <div style="color: #94a3b8; font-size: 13px; margin-top: 8px;">
        {'Monitoring all services for anomalies' if enabled else 'Click toggle to enable autonomous remediation'}
    </div>
</div>
"""
    
    # Stats row
    total_events = len(events)
    restarts = len([e for e in events if e.action_taken == "restart"])
    escalations = len([e for e in events if e.escalated])
    
    stats_html = f"""
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px;">
    <div style="background: linear-gradient(145deg, rgba(99, 102, 241, 0.15) 0%, rgba(99, 102, 241, 0.05) 100%); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 16px; text-align: center;">
        <div style="font-size: 28px; font-weight: 700; color: #6366f1;">{total_events}</div>
        <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;">Total Events</div>
    </div>
    <div style="background: linear-gradient(145deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 16px; text-align: center;">
        <div style="font-size: 28px; font-weight: 700; color: #10b981;">{restarts}</div>
        <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;">Restarts</div>
    </div>
    <div style="background: linear-gradient(145deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 16px; text-align: center;">
        <div style="font-size: 28px; font-weight: 700; color: #f59e0b;">{escalations}</div>
        <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;">Escalations</div>
    </div>
</div>
"""
    
    # Events log
    if events:
        events_html = "<h4 style='color: #e2e8f0; margin: 0 0 16px 0; font-size: 15px;'>📋 Recent Events</h4>"
        for event in reversed(events[-5:]):  # Last 5 events, newest first
            if event.action_taken == "restart":
                action_icon = "🔄"
                action_color = "#10b981"
            elif event.escalated:
                action_icon = "⚠️"
                action_color = "#f59e0b"
            else:
                action_icon = "👁️"
                action_color = "#94a3b8"
            
            health_display = f"{event.post_health:.0%}" if event.post_health else "N/A"
            health_color = "#10b981" if event.post_health and event.post_health >= 0.7 else "#f59e0b" if event.post_health else "#94a3b8"
            
            events_html += f"""
<div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(99, 102, 241, 0.15); border-radius: 10px; padding: 14px; margin: 10px 0;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 18px;">{action_icon}</span>
            <span style="color: #e2e8f0; font-weight: 600;">{event.service_id}</span>
        </div>
        <span style="background: {action_color}22; color: {action_color}; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase;">{event.action_taken}</span>
    </div>
    <div style="display: flex; justify-content: space-between; margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(99, 102, 241, 0.1);">
        <span style="color: #64748b; font-size: 12px;">🕐 {event.timestamp.strftime('%H:%M:%S')}</span>
        <span style="color: {health_color}; font-size: 12px; font-weight: 500;">Health: {health_display}</span>
    </div>
</div>
"""
    else:
        events_html = """
<div style="text-align: center; padding: 32px;">
    <div style="font-size: 48px; margin-bottom: 12px; opacity: 0.5;">📭</div>
    <p style="color: #64748b; margin: 0;">No remediation events yet</p>
    <p style="color: #475569; font-size: 12px; margin-top: 8px;">Events will appear here when anomalies are detected</p>
</div>
"""
    
    return status_html + stats_html + f"""
<div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 20px;">
    {events_html}
</div>
"""


def toggle_remediation(current_state: bool) -> Tuple[str, bool]:
    """Toggle auto-remediation on/off."""
    if current_state:
        stop_remediation_loop()
        return format_remediation_status(), False
    else:
        start_remediation_loop()
        return format_remediation_status(), True


# ============== SETTINGS HELPER FUNCTIONS ==============

def _render_profile_info() -> str:
    """Render profile info HTML."""
    return """
<div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 16px; padding: 24px;">
    <div style="display: grid; gap: 16px;">
        <div>
            <label style="color: #94a3b8; font-size: 12px; text-transform: uppercase;">Username</label>
            <div style="color: #e2e8f0; font-size: 16px; font-weight: 500;">admin</div>
        </div>
        <div>
            <label style="color: #94a3b8; font-size: 12px; text-transform: uppercase;">Role</label>
            <div style="color: #6366f1; font-size: 16px; font-weight: 500;">Admin</div>
        </div>
    </div>
</div>
"""


def _render_platforms_list() -> str:
    """Render platforms list HTML."""
    try:
        from app.platforms import list_platforms
    except ImportError:
        from .platforms import list_platforms
    
    platforms = list_platforms()
    
    if not platforms:
        return """
<div style="text-align: center; padding: 40px; background: linear-gradient(145deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.7) 100%); border-radius: 12px;">
    <div style="font-size: 48px; margin-bottom: 16px;">🌐</div>
    <p style="color: #94a3b8;">No platforms configured yet.</p>
</div>
"""
    
    html = '<div style="display: grid; gap: 12px;">'
    type_icons = {"aws": "☁️", "gcp": "🔷", "azure": "🔶", "custom": "⚙️"}
    
    for p in platforms:
        status_color = "#10b981" if p.connection_status == "connected" else "#ef4444" if p.connection_status == "failed" else "#f59e0b"
        icon = type_icons.get(p.type, "🌐")
        
        html += f"""
<div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 12px; padding: 16px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 24px;">{icon}</span>
            <div>
                <div style="color: #e2e8f0; font-weight: 600;">{p.name}</div>
                <div style="color: #64748b; font-size: 12px; text-transform: uppercase;">{p.type}</div>
            </div>
        </div>
        <span style="color: {status_color};">● {p.connection_status}</span>
    </div>
</div>
"""
    html += '</div>'
    return html


def _render_api_keys_list() -> str:
    """Render API keys list HTML."""
    try:
        from app.api_keys import list_keys
    except ImportError:
        from .api_keys import list_keys
    
    keys = list_keys()
    
    if not keys:
        return """
<div style="text-align: center; padding: 40px; background: linear-gradient(145deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.7) 100%); border-radius: 12px;">
    <div style="font-size: 48px; margin-bottom: 16px;">🔑</div>
    <p style="color: #94a3b8;">No API keys configured yet.</p>
</div>
"""
    
    html = '<div style="display: grid; gap: 12px;">'
    service_icons = {"sambanova": "🧠", "modal": "🚀", "hyperbolic": "🔮", "blaxel": "⚡", "huggingface": "🤗"}
    
    for k in keys:
        icon = service_icons.get(k.service, "🔑")
        html += f"""
<div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 12px; padding: 16px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 20px;">{icon}</span>
            <div>
                <div style="color: #e2e8f0; font-weight: 500;">{k.name}</div>
                <div style="color: #64748b; font-size: 12px; text-transform: uppercase;">{k.service}</div>
            </div>
        </div>
        <div style="font-family: monospace; color: #94a3b8; background: rgba(99, 102, 241, 0.1); padding: 4px 12px; border-radius: 6px;">
            {k.masked_value}
        </div>
    </div>
</div>
"""
    html += '</div>'
    return html


def _change_password(current: str, new: str, confirm: str) -> str:
    """Handle password change."""
    if not current or not new or not confirm:
        return '<p style="color: #ef4444;">❌ All fields are required</p>'
    if new != confirm:
        return '<p style="color: #ef4444;">❌ New passwords do not match</p>'
    if len(new) < 6:
        return '<p style="color: #ef4444;">❌ Password must be at least 6 characters</p>'
    return '<p style="color: #10b981;">✅ Password changed successfully</p>'


def _add_platform(name: str, ptype: str, creds: str) -> Tuple[str, str]:
    """Add a new platform."""
    import json
    try:
        from app.platforms import add_platform
        from app.models import PlatformConfig
    except ImportError:
        from .platforms import add_platform
        from .models import PlatformConfig
    
    if not name or not ptype:
        return '<p style="color: #ef4444;">❌ Name and type are required</p>', _render_platforms_list()
    
    try:
        credentials = json.loads(creds) if creds else {}
    except json.JSONDecodeError:
        return '<p style="color: #ef4444;">❌ Invalid JSON for credentials</p>', _render_platforms_list()
    
    config = PlatformConfig(name=name, type=ptype, credentials=credentials)
    add_platform(config)
    return f'<p style="color: #10b981;">✅ Platform "{name}" added</p>', _render_platforms_list()


def _add_api_key(name: str, service: str, value: str) -> Tuple[str, str]:
    """Add a new API key."""
    try:
        from app.api_keys import add_key
    except ImportError:
        from .api_keys import add_key
    
    if not name or not service or not value:
        return '<p style="color: #ef4444;">❌ All fields are required</p>', _render_api_keys_list()
    
    add_key(name, value, service)
    return f'<p style="color: #10b981;">✅ API key "{name}" added</p>', _render_api_keys_list()


# ============== MAIN LAUNCH FUNCTION ==============

def launch():
    """Launch the attractive Gradio UI."""
    
    # Sync API keys from database to environment on startup
    try:
        from app.api_keys import sync_keys_to_env
    except ImportError:
        from .api_keys import sync_keys_to_env
    sync_keys_to_env()
    
    with gr.Blocks(title="Cloud Ops Sentinel") as demo:
        
        # Header (logout button only shown when auth is enabled)
        auth_enabled = os.getenv("ENABLE_AUTH", "false").lower() == "true"
        logout_html = """
            <div style="position: absolute; top: 16px; right: 16px;">
                <a href="/logout" 
                   style="background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; padding: 8px 16px; color: #fca5a5; font-size: 12px; text-decoration: none; cursor: pointer;">
                    🚪 Logout
                </a>
            </div>
        """ if auth_enabled else ""
        
        gr.HTML(f"""
        <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.1) 100%); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 20px; padding: 32px; margin-bottom: 24px; position: relative;">
            {logout_html}
            <div style="text-align: center;">
                <div style="font-size: 48px; margin-bottom: 12px;">☁️</div>
                <h1 style="color: #e2e8f0; margin: 0 0 8px 0; font-size: 36px; font-weight: 700; background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Cloud Ops Sentinel</h1>
                <p style="color: #94a3b8; margin: 0 0 20px 0; font-size: 16px;">Enterprise Cloud Operations Assistant with AI-Powered Intelligence</p>
                <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 8px;">
                    <span style="background: rgba(99, 102, 241, 0.2); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 20px; padding: 6px 14px; color: #a5b4fc; font-size: 12px;">🚀 Modal</span>
                    <span style="background: rgba(168, 85, 247, 0.2); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 20px; padding: 6px 14px; color: #c4b5fd; font-size: 12px;">🔮 Hyperbolic</span>
                    <span style="background: rgba(236, 72, 153, 0.2); border: 1px solid rgba(236, 72, 153, 0.3); border-radius: 20px; padding: 6px 14px; color: #f9a8d4; font-size: 12px;">⚡ Blaxel</span>
                    <span style="background: rgba(251, 191, 36, 0.2); border: 1px solid rgba(251, 191, 36, 0.3); border-radius: 20px; padding: 6px 14px; color: #fcd34d; font-size: 12px;">🤗 Hugging Face</span>
                    <span style="background: rgba(16, 185, 129, 0.2); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 20px; padding: 6px 14px; color: #6ee7b7; font-size: 12px;">🧠 SambaNova</span>
                    <span style="background: rgba(59, 130, 246, 0.2); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 20px; padding: 6px 14px; color: #93c5fd; font-size: 12px;">🔗 LangChain</span>
                    <span style="background: rgba(239, 68, 68, 0.2); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 20px; padding: 6px 14px; color: #fca5a5; font-size: 12px;">🔌 MCP</span>
                </div>
            </div>
        </div>
        """)
        
        with gr.Tabs() as tabs:
            # Tab 1: Infrastructure Summary
            with gr.Tab("📈 Dashboard", id="dashboard"):
                gr.HTML('<h2 style="color: #e2e8f0; margin: 0 0 16px 0;">Infrastructure Overview</h2>')
                refresh_summary_btn = gr.Button("🔄 Refresh Dashboard", variant="primary", size="lg")
                summary_output = gr.HTML(label="Infrastructure Summary")
                
                refresh_summary_btn.click(
                    fn=lambda: format_infra_summary(tool_summarize_infra()),
                    outputs=[summary_output]
                )
            
            # Tab 2: Idle Instances
            with gr.Tab("🚫 Idle Resources", id="idle"):
                gr.HTML('<h2 style="color: #e2e8f0; margin: 0 0 8px 0;">Cost Optimization</h2>')
                gr.HTML('<p style="color: #94a3b8; margin: 0 0 16px 0;">Detect idle instances and calculate potential savings</p>')
                list_idle_btn = gr.Button("🔍 Scan for Idle Instances", variant="primary", size="lg")
                idle_output = gr.HTML(label="Idle Instances")
                
                list_idle_btn.click(
                    fn=lambda: format_idle_instances(tool_list_idle_instances()),
                    outputs=[idle_output]
                )
            
            # Tab 3: Cost Forecast
            with gr.Tab("💰 Cost Forecast", id="cost"):
                gr.HTML('<h2 style="color: #e2e8f0; margin: 0 0 8px 0;">Cloud Cost Analysis</h2>')
                gr.HTML('<p style="color: #94a3b8; margin: 0 0 16px 0;">Predict future costs and identify savings opportunities</p>')
                with gr.Row():
                    month_input = gr.Textbox(
                        label="Forecast Month",
                        value=datetime.now().strftime("%Y-%m"),
                        placeholder="YYYY-MM",
                        scale=2
                    )
                    forecast_btn = gr.Button("📊 Generate Forecast", variant="primary", size="lg", scale=1)
                forecast_output = gr.HTML(label="Billing Forecast")
                
                forecast_btn.click(
                    fn=lambda m: format_billing_forecast(tool_get_billing_forecast(m)),
                    inputs=[month_input],
                    outputs=[forecast_output]
                )
            
            # Tab 4: Service Metrics & Anomalies
            with gr.Tab("📊 Metrics & Anomalies", id="metrics"):
                gr.HTML('<h2 style="color: #e2e8f0; margin: 0 0 8px 0;">Service Performance Analysis</h2>')
                gr.HTML('<p style="color: #94a3b8; margin: 0 0 16px 0;">Monitor service health and detect anomalies with AI</p>')
                with gr.Row():
                    service_id_input = gr.Textbox(
                        label="Service ID",
                        value="svc_web",
                        placeholder="e.g., svc_web, svc_api, svc_db",
                        scale=2
                    )
                    analyze_btn = gr.Button("🔬 Analyze Service", variant="primary", size="lg", scale=1)
                metrics_output = gr.HTML(label="Metrics & Anomalies")
                
                analyze_btn.click(
                    fn=lambda sid: format_metrics_and_anomalies(
                        tool_get_metrics(sid),
                        tool_detect_anomaly(sid)
                    ),
                    inputs=[service_id_input],
                    outputs=[metrics_output]
                )
            
            # Tab 5: Service Control
            with gr.Tab("🔄 Service Control", id="control"):
                gr.HTML('<h2 style="color: #e2e8f0; margin: 0 0 8px 0;">Service Management</h2>')
                gr.HTML('<p style="color: #94a3b8; margin: 0 0 16px 0;">Restart services via Modal or Blaxel compute backends</p>')
                with gr.Row():
                    restart_service_id = gr.Textbox(
                        label="Service ID to Restart",
                        value="svc_web",
                        placeholder="e.g., svc_web",
                        scale=2
                    )
                    restart_btn = gr.Button("🔄 Restart Service", variant="stop", size="lg", scale=1)
                restart_output = gr.HTML(label="Restart Status")
                
                restart_btn.click(
                    fn=lambda sid: format_restart_result(tool_restart_service(sid)),
                    inputs=[restart_service_id],
                    outputs=[restart_output]
                )
            
            # Tab 6: Full Ops Report
            with gr.Tab("📋 Ops Report", id="report"):
                gr.HTML('<h2 style="color: #e2e8f0; margin: 0 0 8px 0;">Comprehensive Operations Report</h2>')
                gr.HTML('<p style="color: #94a3b8; margin: 0 0 16px 0;">AI-generated infrastructure analysis with actionable recommendations</p>')
                report_btn = gr.Button("📝 Generate Full Report", variant="primary", size="lg")
                report_output = gr.HTML(label="Operations Report")
                
                report_btn.click(
                    fn=lambda: format_ops_report(tool_summarize_infra()),
                    outputs=[report_output]
                )
            
            # Tab 7: Ops Chat (NEW)
            with gr.Tab("💬 Ops Chat", id="chat"):
                gr.HTML('<h2 style="color: #e2e8f0; margin: 0 0 8px 0;">AI Operations Assistant</h2>')
                gr.HTML('''<p style="color: #94a3b8; margin: 0 0 8px 0;">Ask questions in natural language - I'll call the right tools automatically</p>
                <p style="color: #64748b; font-size: 11px; margin: 0 0 16px 0;">
                    <span style="background: rgba(16, 185, 129, 0.2); color: #6ee7b7; padding: 2px 8px; border-radius: 4px; margin-right: 8px;">🧠 LangChain + SambaNova</span>
                    Powered by agentic AI with automatic tool selection
                </p>''')
                
                chat_history = gr.State([])
                
                # Quick action buttons
                gr.HTML("""
                <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px;">
                    <span style="color: #64748b; font-size: 12px; padding: 6px 0;">Quick actions:</span>
                </div>
                """)
                
                with gr.Row():
                    quick_idle = gr.Button("🚫 Idle Instances", size="sm", variant="secondary")
                    quick_metrics = gr.Button("📊 Metrics", size="sm", variant="secondary")
                    quick_forecast = gr.Button("💰 Cost Forecast", size="sm", variant="secondary")
                    quick_anomaly = gr.Button("⚠️ Anomalies", size="sm", variant="secondary")
                    quick_hygiene = gr.Button("🏥 Hygiene Score", size="sm", variant="secondary")
                    clear_chat_btn = gr.Button("🗑️ Clear", size="sm", variant="secondary")
                
                # Chat output area
                chat_output = gr.HTML(
                    value='''<div style="min-height: 150px; display: flex; align-items: center; justify-content: center; background: linear-gradient(145deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.7) 100%); border: 1px dashed rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 24px;">
                        <div style="text-align: center;">
                            <div style="font-size: 32px; margin-bottom: 8px;">💬</div>
                            <p style="color: #64748b; margin: 0;">Ask me anything about your infrastructure!</p>
                            <p style="color: #475569; font-size: 12px; margin-top: 4px;">Try the quick actions above or type your own question</p>
                        </div>
                    </div>''',
                    elem_id="chat-output"
                )
                
                # Input row
                with gr.Row(equal_height=True):
                    chat_input = gr.Textbox(
                        label="Your Question",
                        placeholder="e.g., 'Show me idle instances' or 'Restart svc_web'",
                        scale=5,
                        container=True
                    )
                    chat_btn = gr.Button("💬 Send", variant="primary", size="lg", scale=1, min_width=100)
                
                def process_and_clear(message, history):
                    if not message.strip():
                        return chat_output.value, history, ""
                    response_html, new_history = format_chat_response(message, history)
                    return response_html, new_history, ""
                
                def quick_action(query, history):
                    response_html, new_history = format_chat_response(query, history)
                    return response_html, new_history
                
                def clear_chat():
                    """Clear conversation history."""
                    return _build_conversation_html([]), []
                
                # Quick action handlers
                quick_idle.click(fn=lambda h: quick_action("Show me idle instances", h), inputs=[chat_history], outputs=[chat_output, chat_history])
                quick_metrics.click(fn=lambda h: quick_action("Show metrics for svc_web", h), inputs=[chat_history], outputs=[chat_output, chat_history])
                quick_forecast.click(fn=lambda h: quick_action("What's the cost forecast?", h), inputs=[chat_history], outputs=[chat_output, chat_history])
                quick_anomaly.click(fn=lambda h: quick_action("Check for anomalies", h), inputs=[chat_history], outputs=[chat_output, chat_history])
                quick_hygiene.click(fn=lambda h: quick_action("What's the hygiene score?", h), inputs=[chat_history], outputs=[chat_output, chat_history])
                clear_chat_btn.click(fn=clear_chat, outputs=[chat_output, chat_history])
                
                chat_btn.click(
                    fn=process_and_clear,
                    inputs=[chat_input, chat_history],
                    outputs=[chat_output, chat_history, chat_input]
                )
                chat_input.submit(
                    fn=process_and_clear,
                    inputs=[chat_input, chat_history],
                    outputs=[chat_output, chat_history, chat_input]
                )
            
            # Tab 8: Hygiene Score (NEW)
            with gr.Tab("🏥 Hygiene Score", id="hygiene"):
                gr.HTML('<h2 style="color: #e2e8f0; margin: 0 0 8px 0;">Infrastructure Hygiene Score</h2>')
                gr.HTML('<p style="color: #94a3b8; margin: 0 0 16px 0;">A single 0-100 score measuring overall infrastructure health</p>')
                
                hygiene_btn = gr.Button("📊 Calculate Hygiene Score", variant="primary", size="lg")
                hygiene_output = gr.HTML(label="Hygiene Score")
                
                hygiene_btn.click(
                    fn=format_hygiene_score,
                    outputs=[hygiene_output]
                )
            
            # Tab 9: Auto-Remediation (NEW)
            with gr.Tab("🤖 Auto-Remediation", id="remediation"):
                gr.HTML('<h2 style="color: #e2e8f0; margin: 0 0 8px 0;">Autonomous Remediation</h2>')
                gr.HTML('<p style="color: #94a3b8; margin: 0 0 16px 0;">Automatically detect and fix service anomalies</p>')
                
                remediation_state = gr.State(False)
                
                with gr.Row():
                    toggle_btn = gr.Button("🔄 Toggle Auto-Remediation", variant="primary", size="lg")
                    refresh_events_btn = gr.Button("🔄 Refresh Events", variant="secondary", size="lg")
                
                remediation_output = gr.HTML(value=format_remediation_status())
                
                toggle_btn.click(
                    fn=toggle_remediation,
                    inputs=[remediation_state],
                    outputs=[remediation_output, remediation_state]
                )
                refresh_events_btn.click(
                    fn=format_remediation_status,
                    outputs=[remediation_output]
                )
                
                gr.HTML("""
                <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 12px; margin-top: 16px;">
                    <p style="color: #fbbf24; margin: 0; font-size: 12px;"><strong>⚠️ How it works:</strong></p>
                    <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 11px;">
                        When enabled, the system monitors all services for anomalies. If a HIGH or CRITICAL severity anomaly is detected,
                        it automatically restarts the service and verifies health. If health remains below 70%, the service is escalated
                        and auto-restart is disabled for that service.
                    </p>
                </div>
                """)
            
            # Tab 10: Download Report (NEW)
            with gr.Tab("📥 Download Report", id="download"):
                gr.HTML('<h2 style="color: #e2e8f0; margin: 0 0 8px 0;">Export Operations Report</h2>')
                gr.HTML('<p style="color: #94a3b8; margin: 0 0 16px 0;">Download a comprehensive report for stakeholders</p>')
                
                with gr.Row():
                    generate_preview_btn = gr.Button("👁️ Preview Report", variant="secondary", size="lg")
                    generate_file_btn = gr.Button("📄 Generate Report File", variant="primary", size="lg")
                
                download_file = gr.File(label="📥 Click the download arrow (↓) on the right to save")
                download_output = gr.Markdown(label="Report Preview")
                
                def create_report_file():
                    """Generate markdown file for download."""
                    content = generate_markdown_report()
                    filepath = "/tmp/cloud_ops_sentinel_report.md"
                    with open(filepath, "w") as f:
                        f.write(content)
                    return filepath
                
                generate_preview_btn.click(
                    fn=generate_markdown_report,
                    outputs=[download_output]
                )
                generate_file_btn.click(
                    fn=create_report_file,
                    outputs=[download_file]
                )
            
            # Tab 11: Settings (Admin) - only show when auth is enabled
            if auth_enabled:
                with gr.Tab("⚙️ Settings", id="settings"):
                    gr.HTML('<h2 style="color: #e2e8f0; margin: 0 0 8px 0;">Settings & Configuration</h2>')
                    gr.HTML('<p style="color: #94a3b8; margin: 0 0 16px 0;">Manage platforms, API keys, and user settings</p>')
                    
                    with gr.Tabs():
                        # Profile tab
                        with gr.Tab("👤 Profile"):
                            profile_info = gr.HTML(value=_render_profile_info())
                            
                            gr.HTML('<h4 style="color: #e2e8f0; margin: 20px 0 12px 0;">Change Password</h4>')
                            with gr.Row():
                                current_pwd = gr.Textbox(label="Current Password", type="password", scale=1)
                                new_pwd = gr.Textbox(label="New Password", type="password", scale=1)
                                confirm_pwd = gr.Textbox(label="Confirm Password", type="password", scale=1)
                            
                            change_pwd_btn = gr.Button("🔒 Change Password", variant="primary")
                            pwd_result = gr.HTML()
                            
                            change_pwd_btn.click(
                                fn=_change_password,
                                inputs=[current_pwd, new_pwd, confirm_pwd],
                                outputs=[pwd_result]
                            )
                        
                        # Platforms tab
                        with gr.Tab("🌐 Platforms"):
                            platforms_list = gr.HTML(value=_render_platforms_list())
                            
                            gr.HTML('<h4 style="color: #e2e8f0; margin: 20px 0 12px 0;">Add New Platform</h4>')
                            with gr.Row():
                                platform_name = gr.Textbox(label="Platform Name", placeholder="My AWS Account")
                                platform_type = gr.Dropdown(label="Type", choices=["aws", "gcp", "azure", "custom"], value="aws")
                            
                            platform_creds = gr.Textbox(
                                label="Credentials (JSON)",
                                placeholder='{"access_key": "...", "secret_key": "...", "region": "us-east-1"}',
                                lines=3
                            )
                            
                            add_platform_btn = gr.Button("➕ Add Platform", variant="primary")
                            platform_result = gr.HTML()
                            
                            add_platform_btn.click(
                                fn=_add_platform,
                                inputs=[platform_name, platform_type, platform_creds],
                                outputs=[platform_result, platforms_list]
                            )
                        
                        # API Keys tab
                        with gr.Tab("🔑 API Keys"):
                            keys_list = gr.HTML(value=_render_api_keys_list())
                            
                            gr.HTML('<h4 style="color: #e2e8f0; margin: 20px 0 12px 0;">Add New API Key</h4>')
                            with gr.Row():
                                key_name = gr.Textbox(label="Key Name", placeholder="SambaNova Production")
                                key_service = gr.Dropdown(
                                    label="Service",
                                    choices=["sambanova", "modal", "hyperbolic", "blaxel", "huggingface", "openai", "custom"],
                                    value="sambanova"
                                )
                            
                            key_value = gr.Textbox(label="API Key Value", type="password", placeholder="sk-...")
                            
                            add_key_btn = gr.Button("➕ Add API Key", variant="primary")
                            key_result = gr.HTML()
                            
                            add_key_btn.click(
                                fn=_add_api_key,
                                inputs=[key_name, key_service, key_value],
                                outputs=[key_result, keys_list]
                            )
        
        # Footer
        gr.HTML("""
        <div style="background: linear-gradient(145deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.6) 100%); border: 1px solid rgba(99, 102, 241, 0.15); border-radius: 16px; padding: 24px; margin-top: 24px; text-align: center;">
            <p style="color: #64748b; margin: 0; font-size: 13px;">
                <strong style="color: #94a3b8;">Cloud Ops Sentinel</strong> — Enterprise MCP Agent for DevOps Automation
            </p>
            <p style="color: #475569; margin: 8px 0 0 0; font-size: 12px;">
                Built with ❤️ for the AI Hackathon
            </p>
        </div>
        """)
    
    # Return demo for external launch or launch directly
    return demo


def launch_app():
    """Create and return the Gradio app."""
    # Sync API keys from database to environment on startup
    try:
        from app.api_keys import sync_keys_to_env
    except ImportError:
        from .api_keys import sync_keys_to_env
    sync_keys_to_env()
    
    demo = launch()
    return demo


def launch_with_auth():
    """Launch with authentication enabled."""
    os.environ["ENABLE_AUTH"] = "true"
    launch()


if __name__ == "__main__":
    # Check if running with gradio reload
    import os
    if os.environ.get("GRADIO_WATCH_DIRS"):
        # Running with hot reload via gradio CLI
        import gradio as gr
        gr.close_all()
    launch()
