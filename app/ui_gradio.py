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


# ============== MAIN LAUNCH FUNCTION ==============

def launch():
    """Launch the attractive Gradio UI."""
    
    with gr.Blocks(title="Cloud Ops Sentinel") as demo:
        
        # Header
        gr.HTML("""
        <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.1) 100%); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 20px; padding: 32px; margin-bottom: 24px; text-align: center;">
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
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    launch()
