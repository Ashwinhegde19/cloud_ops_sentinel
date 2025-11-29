#!/usr/bin/env python3
"""
Cloud Ops Sentinel MCP Server
Exposes 6 core cloud operations tools via Model Context Protocol
"""

import os
import sys
from typing import Dict, Any
from datetime import datetime
import json

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import app modules
from app.infra_simulation import (
    generate_fake_infra, compute_idle_instances, generate_fake_metrics,
    compute_infra_summary, estimate_monthly_cost, INSTANCE_COSTS
)
from app.modal_client import restart_service_via_modal
from app.blaxel_client import restart_service_via_blaxel
from app.hyperbolic_client import detect_anomaly_from_metrics
from app.llm_client import generate_ops_report, get_integrations_used
from app.models import CostForecast, AnomalyResult

# Create MCP server
server = Server("cloud-ops-sentinel")


def serialize_datetime(obj):
    """Helper function to serialize datetime objects for JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def tool_list_idle_instances() -> Dict[str, Any]:
    """Get list of idle instances with monthly savings calculation (Requirements 1.1, 1.5)"""
    instances, services = generate_fake_infra()
    idle_instances = compute_idle_instances(instances)
    
    # Calculate monthly savings for each idle instance
    idle_data = []
    total_savings = 0.0
    for inst in idle_instances:
        tier = inst.tags.get("tier", "worker")
        hourly_cost = INSTANCE_COSTS.get(tier, 0.10)
        monthly_savings = hourly_cost * 24 * 30
        total_savings += monthly_savings
        
        inst_dict = json.loads(json.dumps(inst.model_dump(), default=serialize_datetime))
        inst_dict["monthly_savings"] = round(monthly_savings, 2)
        inst_dict["hourly_cost"] = hourly_cost
        idle_data.append(inst_dict)
    
    return {
        "idle_instances": idle_data,
        "total_idle_count": len(idle_instances),
        "total_monthly_savings": round(total_savings, 2)
    }


def tool_get_billing_forecast(month: str) -> Dict[str, Any]:
    """Generate billing forecast with breakdown and narrative (Requirements 2.1, 2.4, 2.5)"""
    instances, services = generate_fake_infra()
    
    # Get detailed cost breakdown
    cost_data = estimate_monthly_cost(instances, days=30)
    
    # Calculate confidence based on data quality
    confidence = 0.75 if len(instances) >= 5 else 0.55
    
    # Build risk factors if confidence is low
    risk_factors = []
    if confidence < 0.6:
        risk_factors.append("Limited historical data available")
        risk_factors.append("High variance in usage patterns")
    if cost_data.get("idle_instance_count", 0) > 2:
        risk_factors.append(f"{cost_data['idle_instance_count']} idle instances may be terminated")
    
    # Generate narrative
    narrative = f"Forecast for {month}: Predicted cost ${cost_data['total_monthly_cost']:.2f} with {confidence:.0%} confidence. "
    if cost_data.get("potential_savings", 0) > 0:
        narrative += f"Potential savings of ${cost_data['potential_savings']:.2f} from idle resources."
    
    forecast = CostForecast(
        month=month,
        predicted_cost=cost_data["total_monthly_cost"],
        confidence=confidence,
        narrative=narrative,
        breakdown=cost_data.get("cost_by_tier", {}),
        risk_factors=risk_factors
    )
    
    result = forecast.model_dump()
    result["cost_by_region"] = cost_data.get("cost_by_region", {})
    result["potential_savings"] = cost_data.get("potential_savings", 0)
    return result


def tool_get_metrics(service_id: str) -> Dict[str, Any]:
    """Get metrics for specified service"""
    metrics = generate_fake_metrics(service_id)
    return {
        "service_id": service_id,
        "metrics": [json.loads(json.dumps(m.model_dump(), default=serialize_datetime)) for m in metrics]
    }


def tool_detect_anomaly(service_id: str) -> Dict[str, Any]:
    """Detect anomalies for specified service"""
    metrics = generate_fake_metrics(service_id)
    anomaly_result = detect_anomaly_from_metrics(service_id, metrics)
    return anomaly_result.model_dump()


def tool_restart_service(service_id: str) -> Dict[str, Any]:
    """Restart service via Modal or Blaxel with RestartResult structure (Requirements 5.1)"""
    use_blaxel = os.getenv("USE_BLAXEL", "").lower() == "true"
    if use_blaxel:
        result = restart_service_via_blaxel(service_id)
    else:
        result = restart_service_via_modal(service_id)
    
    # Return RestartResult-compatible structure
    return {
        "service_id": result.get("service_id", service_id),
        "restart_status": result.get("restart_status", "success"),
        "time_taken_ms": result.get("time_taken_ms", 0),
        "post_restart_health": result.get("post_restart_health"),
        "via": result.get("via", "unknown"),
        "timestamp": result.get("timestamp", datetime.now().isoformat())
    }


def tool_summarize_infra() -> Dict[str, Any]:
    """Generate infrastructure summary with enhanced OpsReport (Requirements 6.1, 6.2, 6.5)"""
    instances, services = generate_fake_infra()
    idle_instances = compute_idle_instances(instances)
    current_month = datetime.now().strftime("%Y-%m")
    billing_forecast = tool_get_billing_forecast(current_month)
    
    # Get anomalies for all services
    anomalies = [tool_detect_anomaly(svc.service_id) for svc in services]
    
    # Compute infrastructure summary
    infra_summary = compute_infra_summary(instances, services)
    
    # Prepare context for LLM report
    context = {
        "instances": [json.loads(json.dumps(i.model_dump(), default=serialize_datetime)) for i in instances],
        "services": [json.loads(json.dumps(s.model_dump(), default=serialize_datetime)) for s in services],
        "idle_instances": [json.loads(json.dumps(i.model_dump(), default=serialize_datetime)) for i in idle_instances],
        "billing_forecast": billing_forecast,
        "anomalies": anomalies
    }
    
    # Generate structured ops report
    report = generate_ops_report(context)
    
    return {
        "report": report,
        "summary": json.loads(json.dumps(infra_summary.model_dump(), default=serialize_datetime)),
        "summary_data": context,
        "sponsor_integrations_used": report.get("sponsor_integrations_used", get_integrations_used())
    }


# Register MCP tools
@server.list_tools()
async def list_tools():
    """List available MCP tools"""
    return [
        Tool(
            name="list_idle_instances",
            description="Detect idle compute instances based on CPU, RAM, and network activity. Returns instances with low utilization that could be terminated for cost savings.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="get_billing_forecast",
            description="Forecast cloud costs for a specific month based on historical usage patterns.",
            inputSchema={
                "type": "object",
                "properties": {"month": {"type": "string", "description": "Month in YYYY-MM format"}},
                "required": ["month"]
            }
        ),
        Tool(
            name="get_metrics",
            description="Get performance metrics (CPU, RAM, latency, error rate) for a specific service.",
            inputSchema={
                "type": "object",
                "properties": {"service_id": {"type": "string", "description": "Service ID (e.g., svc_web, svc_api)"}},
                "required": ["service_id"]
            }
        ),
        Tool(
            name="detect_anomaly",
            description="Detect anomalies in service behavior using metrics analysis.",
            inputSchema={
                "type": "object",
                "properties": {"service_id": {"type": "string", "description": "Service ID to analyze"}},
                "required": ["service_id"]
            }
        ),
        Tool(
            name="restart_service",
            description="Restart a service via Modal or Blaxel compute backend.",
            inputSchema={
                "type": "object",
                "properties": {"service_id": {"type": "string", "description": "Service ID to restart"}},
                "required": ["service_id"]
            }
        ),
        Tool(
            name="summarize_infra",
            description="Generate comprehensive infrastructure summary with LLM-powered ops report including health status, cost analysis, and recommendations.",
            inputSchema={"type": "object", "properties": {}, "required": []}
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls"""
    try:
        if name == "list_idle_instances":
            result = tool_list_idle_instances()
        elif name == "get_billing_forecast":
            month = arguments.get("month", datetime.now().strftime("%Y-%m"))
            result = tool_get_billing_forecast(month)
        elif name == "get_metrics":
            service_id = arguments.get("service_id", "svc_web")
            result = tool_get_metrics(service_id)
        elif name == "detect_anomaly":
            service_id = arguments.get("service_id", "svc_web")
            result = tool_detect_anomaly(service_id)
        elif name == "restart_service":
            service_id = arguments.get("service_id", "svc_web")
            result = tool_restart_service(service_id)
        elif name == "summarize_infra":
            result = tool_summarize_infra()
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=serialize_datetime))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
