#!/usr/bin/env python3
"""
Cloud Ops Sentinel - Gradio 6 UI
Enterprise-grade cloud operations dashboard
"""

import gradio as gr
import json
import sys
import os
from typing import Dict, Any
from datetime import datetime

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


def format_idle_instances(result: Dict[str, Any]) -> str:
    """Format idle instances with savings calculation (Requirements 7.3)."""
    instances = result.get("idle_instances", [])
    total_savings = result.get("total_monthly_savings", 0)
    
    if not instances:
        return "✅ No idle instances found. All resources are being utilized efficiently."

    output = f"🚫 **{len(instances)} Idle Instances Detected**\n"
    output += f"💰 **Total Potential Monthly Savings: ${total_savings:.2f}**\n\n"
    
    for i, inst in enumerate(instances, 1):
        cpu_list = inst.get('cpu_usage', [])
        ram_list = inst.get('ram_usage', [])
        avg_cpu = sum(cpu_list) / len(cpu_list) if cpu_list else 0
        avg_ram = sum(ram_list) / len(ram_list) if ram_list else 0
        
        output += f"**{i}. {inst.get('instance_id', 'N/A')}**\n"
        output += f"   • Region: {inst.get('tags', {}).get('region', 'N/A')}\n"
        output += f"   • Tier: {inst.get('tags', {}).get('tier', 'N/A')}\n"
        output += f"   • CPU: {avg_cpu:.1f}% | RAM: {avg_ram:.1f}%\n"
        output += f"   • Monthly Savings: ${inst.get('monthly_savings', 0):.2f}\n\n"

    return output


def format_billing_forecast(result: Dict[str, Any]) -> str:
    """Format billing forecast with breakdown (Requirements 7.1)."""
    output = f"📊 **Cost Forecast for {result.get('month', 'N/A')}**\n\n"
    output += f"💵 **Predicted Cost:** ${result.get('predicted_cost', 0):.2f}\n"
    output += f"📈 **Confidence:** {result.get('confidence', 0):.0%}\n"
    output += f"💰 **Potential Savings:** ${result.get('potential_savings', 0):.2f}\n\n"
    
    # Breakdown by tier
    breakdown = result.get("breakdown", {})
    if breakdown:
        output += "**Cost by Tier:**\n"
        for tier, cost in breakdown.items():
            output += f"   • {tier}: ${cost:.2f}\n"
    
    # Risk factors
    risk_factors = result.get("risk_factors", [])
    if risk_factors:
        output += "\n⚠️ **Risk Factors:**\n"
        for risk in risk_factors:
            output += f"   • {risk}\n"
    
    # Narrative
    narrative = result.get("narrative", "")
    if narrative:
        output += f"\n📝 {narrative}"
    
    return output


def format_metrics_and_anomalies(metrics_result: Dict[str, Any], anomaly_result: Dict[str, Any]) -> str:
    """Format metrics and anomalies with baseline comparison (Requirements 7.4)."""
    output = f"📊 **Service Metrics: {metrics_result.get('service_id', 'N/A')}**\n\n"
    
    metrics = metrics_result.get("metrics", [])
    if metrics:
        # Calculate averages
        avg_cpu = sum(m.get('cpu', 0) for m in metrics) / len(metrics)
        avg_ram = sum(m.get('ram', 0) for m in metrics) / len(metrics)
        avg_latency = sum(m.get('latency_ms', 0) for m in metrics) / len(metrics)
        avg_error = sum(m.get('error_rate', 0) for m in metrics) / len(metrics)
        
        output += f"**Metrics Summary ({len(metrics)} samples):**\n"
        output += f"   • Avg CPU: {avg_cpu:.1f}%\n"
        output += f"   • Avg RAM: {avg_ram:.1f}%\n"
        output += f"   • Avg Latency: {avg_latency:.1f}ms\n"
        output += f"   • Avg Error Rate: {avg_error:.2%}\n\n"
    
    # Anomaly detection results
    has_anomaly = anomaly_result.get("has_anomaly", False)
    severity = anomaly_result.get("severity", "none")
    
    severity_emoji = {"none": "✅", "low": "🟡", "medium": "🟠", "high": "🔴", "critical": "🚨"}
    output += f"**Anomaly Detection:**\n"
    output += f"   • Status: {severity_emoji.get(severity, '❓')} {severity.upper()}\n"
    output += f"   • Anomaly Detected: {'Yes' if has_anomaly else 'No'}\n"
    
    if has_anomaly:
        output += f"   • Type: {anomaly_result.get('anomaly_type', 'Unknown')}\n"
        output += f"   • Reason: {anomaly_result.get('reason', 'N/A')}\n"
        output += f"\n💡 **Recommended Action:** {anomaly_result.get('recommended_action', 'N/A')}\n"
    
    # Evidence
    evidence = anomaly_result.get("evidence", [])
    if evidence:
        output += "\n**Evidence:**\n"
        for e in evidence[:5]:
            output += f"   • {e}\n"
    
    return output


def format_restart_result(result: Dict[str, Any]) -> str:
    """Format restart result with health check."""
    status = result.get("restart_status", "unknown")
    status_emoji = "✅" if status == "success" else "❌"
    
    output = f"{status_emoji} **Service Restart: {result.get('service_id', 'N/A')}**\n\n"
    output += f"   • Status: {status.upper()}\n"
    output += f"   • Time Taken: {result.get('time_taken_ms', 0):.2f}ms\n"
    output += f"   • Backend: {result.get('via', 'unknown')}\n"
    
    health = result.get("post_restart_health")
    if health:
        health_emoji = "🟢" if health >= 90 else "🟡" if health >= 70 else "🔴"
        output += f"   • Post-Restart Health: {health_emoji} {health:.1f}%\n"
    
    output += f"   • Timestamp: {result.get('timestamp', 'N/A')}\n"
    
    return output


def format_ops_report(result: Dict[str, Any]) -> str:
    """Format ops report with all sections (Requirements 7.1)."""
    report = result.get("report", {})
    summary = result.get("summary", {})
    
    output = f"📋 **Cloud Operations Report**\n"
    output += f"Generated: {report.get('generated_at', datetime.now().isoformat())}\n\n"
    
    # Infrastructure Health
    health = report.get("infra_health", "Unknown")
    health_emoji = {"Healthy": "🟢", "Degraded": "🟡", "Critical": "🔴"}.get(health, "❓")
    output += f"**Infrastructure Health:** {health_emoji} {health}\n\n"
    
    # Summary stats
    if summary:
        output += "**Summary:**\n"
        output += f"   • Total Instances: {summary.get('total_instances', 0)}\n"
        output += f"   • Running: {summary.get('running_instances', 0)}\n"
        output += f"   • Idle: {summary.get('idle_instances', 0)}\n"
        output += f"   • Health Score: {summary.get('health_score', 0):.1f}%\n"
        output += f"   • Daily Cost: ${summary.get('total_daily_cost', 0):.2f}\n\n"
    
    # Idle waste summary
    idle_summary = report.get("idle_waste_summary", "")
    if idle_summary:
        output += f"**💰 Cost Optimization:**\n{idle_summary}\n\n"
    
    # Anomaly root causes
    anomalies = report.get("anomaly_root_causes", [])
    if anomalies:
        output += "**⚠️ Anomaly Root Causes:**\n"
        for a in anomalies[:5]:
            output += f"   • {a}\n"
        output += "\n"
    
    # Recommended actions
    actions = report.get("recommended_actions", [])
    if actions:
        output += "**📝 Recommended Actions:**\n"
        for i, action in enumerate(actions[:5], 1):
            output += f"   {i}. {action}\n"
        output += "\n"
    
    # Sponsor integrations
    integrations = result.get("sponsor_integrations_used", [])
    if integrations:
        output += f"**🔌 Integrations Used:** {', '.join(integrations)}\n\n"
    
    # Full narrative
    narrative = report.get("full_narrative", "")
    if narrative:
        output += "---\n**Full Report:**\n"
        output += narrative[:2000]  # Limit length
    
    return output


def format_infra_summary(result: Dict[str, Any]) -> str:
    """Format infrastructure summary (Requirements 7.1)."""
    summary = result.get("summary", {})
    
    output = "📈 **Infrastructure Overview**\n\n"
    
    # Health score
    health_score = summary.get("health_score", 0)
    if health_score >= 90:
        health_emoji = "🟢"
    elif health_score >= 70:
        health_emoji = "🟡"
    else:
        health_emoji = "🔴"
    
    output += f"**Health Score:** {health_emoji} {health_score:.1f}%\n\n"
    
    output += "**Instances:**\n"
    output += f"   • Total: {summary.get('total_instances', 0)}\n"
    output += f"   • Running: {summary.get('running_instances', 0)}\n"
    output += f"   • Idle: {summary.get('idle_instances', 0)}\n"
    output += f"   • Error: {summary.get('error_instances', 0)}\n\n"
    
    output += "**Services:**\n"
    output += f"   • Total: {summary.get('total_services', 0)}\n"
    output += f"   • Healthy: {summary.get('healthy_services', 0)}\n"
    output += f"   • Degraded: {summary.get('degraded_services', 0)}\n\n"
    
    output += f"**Daily Cost:** ${summary.get('total_daily_cost', 0):.2f}\n"
    output += f"**Regions:** {', '.join(summary.get('regions', []))}\n"
    
    return output


def launch():
    """Launch the Gradio UI with all sections (Requirements 7.1)."""
    
    with gr.Blocks(
        title="Cloud Ops Sentinel",
        theme=gr.themes.Soft()
    ) as demo:
        gr.Markdown("""
        # ☁️ Cloud Ops Sentinel
        **Enterprise Cloud Operations Assistant**
        
        AI-powered infrastructure monitoring, anomaly detection, cost optimization, and automated remediation.
        
        ---
        """)
        
        with gr.Tabs():
            # Tab 1: Infrastructure Summary
            with gr.Tab("📈 Infrastructure Summary"):
                gr.Markdown("### Overall Infrastructure Health")
                refresh_summary_btn = gr.Button("🔄 Refresh Summary", variant="primary")
                summary_output = gr.Markdown(label="Infrastructure Summary")
                
                refresh_summary_btn.click(
                    fn=lambda: format_infra_summary(tool_summarize_infra()),
                    outputs=[summary_output]
                )
            
            # Tab 2: Idle Instances
            with gr.Tab("🚫 Idle Instances"):
                gr.Markdown("### Detect Idle Resources for Cost Savings")
                list_idle_btn = gr.Button("🔍 Scan for Idle Instances", variant="primary")
                idle_output = gr.Markdown(label="Idle Instances")
                
                list_idle_btn.click(
                    fn=lambda: format_idle_instances(tool_list_idle_instances()),
                    outputs=[idle_output]
                )
            
            # Tab 3: Cost Forecast
            with gr.Tab("💰 Cost Forecast"):
                gr.Markdown("### Cloud Cost Analysis and Forecasting")
                with gr.Row():
                    month_input = gr.Textbox(
                        label="Month (YYYY-MM)",
                        value=datetime.now().strftime("%Y-%m"),
                        placeholder="2025-12"
                    )
                    forecast_btn = gr.Button("📊 Generate Forecast", variant="primary")
                forecast_output = gr.Markdown(label="Billing Forecast")
                
                forecast_btn.click(
                    fn=lambda m: format_billing_forecast(tool_get_billing_forecast(m)),
                    inputs=[month_input],
                    outputs=[forecast_output]
                )
            
            # Tab 4: Service Metrics & Anomalies
            with gr.Tab("📊 Metrics & Anomalies"):
                gr.Markdown("### Service Performance Analysis")
                with gr.Row():
                    service_id_input = gr.Textbox(
                        label="Service ID",
                        value="svc_web",
                        placeholder="e.g., svc_web, svc_api, svc_db"
                    )
                    analyze_btn = gr.Button("🔬 Analyze Service", variant="primary")
                metrics_output = gr.Markdown(label="Metrics & Anomalies")
                
                analyze_btn.click(
                    fn=lambda sid: format_metrics_and_anomalies(
                        tool_get_metrics(sid),
                        tool_detect_anomaly(sid)
                    ),
                    inputs=[service_id_input],
                    outputs=[metrics_output]
                )
            
            # Tab 5: Service Control
            with gr.Tab("🔄 Service Control"):
                gr.Markdown("### Restart Services")
                with gr.Row():
                    restart_service_id = gr.Textbox(
                        label="Service ID to Restart",
                        value="svc_web",
                        placeholder="e.g., svc_web"
                    )
                    restart_btn = gr.Button("🔄 Restart Service", variant="stop")
                restart_output = gr.Markdown(label="Restart Status")
                
                restart_btn.click(
                    fn=lambda sid: format_restart_result(tool_restart_service(sid)),
                    inputs=[restart_service_id],
                    outputs=[restart_output]
                )
            
            # Tab 6: Full Ops Report
            with gr.Tab("📋 Ops Report"):
                gr.Markdown("### Comprehensive Operations Report")
                report_btn = gr.Button("📝 Generate Full Report", variant="primary")
                report_output = gr.Markdown(label="Operations Report")
                
                report_btn.click(
                    fn=lambda: format_ops_report(tool_summarize_infra()),
                    outputs=[report_output]
                )
        
        gr.Markdown("""
        ---
        
        **Powered by:** Modal • Hyperbolic • Blaxel • Hugging Face • SambaNova • LangChain • MCP
        
        *Cloud Ops Sentinel - Enterprise MCP Agent for DevOps Automation*
        """)
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    launch()
