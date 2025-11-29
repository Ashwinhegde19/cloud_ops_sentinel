import gradio as gr
import json
import sys
import os
from typing import Dict, Any

# Add parent directory to path for imports when running as script
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Import tool functions - handle both module and script execution
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
    # Running as script - use absolute imports
    from app.mcp_server import (
        tool_list_idle_instances,
        tool_get_billing_forecast,
        tool_get_metrics,
        tool_detect_anomaly,
        tool_restart_service,
        tool_summarize_infra
    )


def format_idle_instances(result: Dict[str, Any]) -> str:
    """Format idle instances for display"""
    instances = result.get("idle_instances", [])
    if not instances:
        return "No idle instances found."

    formatted = "Idle Instances:\n\n"
    for instance in instances:
        cpu_list = instance.get('cpu_usage', [])
        ram_list = instance.get('ram_usage', [])

        # Calculate averages for better display
        avg_cpu = sum(cpu_list) / len(cpu_list) if cpu_list else 0
        avg_ram = sum(ram_list) / len(ram_list) if ram_list else 0

        formatted += f"- Instance ID: {instance.get('instance_id', 'N/A')}\n"
        formatted += f"  Service: {instance.get('service_id', 'N/A')}\n"
        formatted += f"  CPU Usage: {avg_cpu:.1f}% (avg of {len(cpu_list)} samples)\n"
        formatted += f"  Memory Usage: {avg_ram:.1f}% (avg of {len(ram_list)} samples)\n"
        formatted += f"  Status: {instance.get('status', 'N/A')}\n\n"

    return formatted


def format_metrics_and_anomalies(metrics_result: Dict[str, Any], anomaly_result: Dict[str, Any]) -> str:
    """Format metrics and anomalies for display"""
    output = "Service Metrics:\n\n"

    # Format metrics
    service_id = metrics_result.get("service_id", "N/A")
    metrics = metrics_result.get("metrics", [])
    output += f"Service ID: {service_id}\n"
    output += f"Number of metrics: {len(metrics)}\n\n"

    # Format anomalies
    output += "Anomaly Detection:\n\n"
    anomalies_found = anomaly_result.get("anomalies", [])
    is_anomaly = anomaly_result.get("is_anomaly", False)

    output += f"Anomaly Detected: {is_anomaly}\n"
    if anomalies_found:
        output += "Anomalies:\n"
        for anomaly in anomalies_found:
            output += f"  - {anomaly}\n"
    else:
        output += "No anomalies detected.\n"

    return output


def format_restart_result(result: Dict[str, Any]) -> str:
    """Format restart result for display"""
    status = result.get("status", "unknown")
    service_id = result.get("service_id", "N/A")

    return f"Service {service_id} restart: {status}"


def format_ops_report(result: Dict[str, Any]) -> str:
    """Format ops report for display"""
    report = result.get("report", "No report generated.")
    return report


def launch():
    """Launch the Gradio UI"""

    with gr.Blocks(title="Cloud Ops Sentinel") as demo:
        gr.Markdown("# Cloud Ops Sentinel")
        gr.Markdown("Simple MCP-based Cloud Operations Assistant")

        with gr.Row():
            # Column 1: Service selector and Action buttons
            with gr.Column():
                gr.Markdown("## Service Configuration")
                service_id = gr.Textbox(label="Service ID", placeholder="e.g., svc_web")
                gr.Markdown("## Actions")

                list_idle_btn = gr.Button("List Idle Instances", variant="secondary")
                forecast_btn = gr.Button("Get Billing Forecast", variant="secondary")
                metrics_anomaly_btn = gr.Button("Get Metrics & Detect Anomaly", variant="primary")
                restart_btn = gr.Button("Restart Service", variant="stop")
                ops_report_btn = gr.Button("Generate Ops Report", variant="primary")

            # Column 2: JSON/text outputs
            with gr.Column():
                gr.Markdown("## Results")
                idle_output = gr.Textbox(label="Idle Instances", lines=8)
                forecast_output = gr.JSON(label="Billing Forecast")
                metrics_anomaly_output = gr.Textbox(label="Metrics & Anomalies", lines=10)
                restart_output = gr.Textbox(label="Restart Status", lines=3)
                ops_report_output = gr.Textbox(label="Ops Report", lines=15)

        # Button click handlers
        list_idle_btn.click(
            fn=lambda: format_idle_instances(tool_list_idle_instances()),
            outputs=[idle_output]
        )

        forecast_btn.click(
            fn=lambda: tool_get_billing_forecast("2024-12"),
            outputs=[forecast_output]
        )

        metrics_anomaly_btn.click(
            fn=lambda service_id: format_metrics_and_anomalies(
                tool_get_metrics(service_id),
                tool_detect_anomaly(service_id)
            ),
            inputs=[service_id],
            outputs=[metrics_anomaly_output]
        )

        restart_btn.click(
            fn=lambda service_id: format_restart_result(tool_restart_service(service_id)),
            inputs=[service_id],
            outputs=[restart_output]
        )

        ops_report_btn.click(
            fn=lambda: format_ops_report(tool_summarize_infra()),
            outputs=[ops_report_output]
        )

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    launch()