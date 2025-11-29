"""
Cloud Ops Sentinel Orchestrator
LangChain-powered workflow orchestration for multi-step operations
"""

from typing import Dict, Any, List, Callable
from datetime import datetime

# LangChain imports for tool-calling pipeline
from langchain_core.tools import Tool, StructuredTool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Import tool functions
from .mcp_server import (
    tool_list_idle_instances,
    tool_get_billing_forecast,
    tool_get_metrics,
    tool_detect_anomaly,
    tool_restart_service,
    tool_summarize_infra
)
from .llm_client import generate_ops_report, get_integrations_used


def _create_langchain_tools() -> List[Tool]:
    """Create LangChain Tool wrappers for MCP tools."""
    return [
        Tool(
            name="list_idle_instances",
            description="Detect idle compute instances based on CPU, RAM, and network activity",
            func=lambda _: tool_list_idle_instances()
        ),
        Tool(
            name="get_billing_forecast",
            description="Forecast cloud costs for a specific month",
            func=lambda month: tool_get_billing_forecast(month if month else datetime.now().strftime("%Y-%m"))
        ),
        Tool(
            name="get_metrics",
            description="Get performance metrics for a specific service",
            func=lambda service_id: tool_get_metrics(service_id if service_id else "svc_web")
        ),
        Tool(
            name="detect_anomaly",
            description="Detect anomalies in service behavior",
            func=lambda service_id: tool_detect_anomaly(service_id if service_id else "svc_web")
        ),
        Tool(
            name="restart_service",
            description="Restart a service via Modal or Blaxel",
            func=lambda service_id: tool_restart_service(service_id if service_id else "svc_web")
        ),
        Tool(
            name="summarize_infra",
            description="Generate infrastructure summary with LLM-powered ops report",
            func=lambda _: tool_summarize_infra()
        )
    ]


# Tool registry for direct access
MCP_TOOLS = {
    "list_idle_instances": tool_list_idle_instances,
    "get_billing_forecast": tool_get_billing_forecast,
    "get_metrics": tool_get_metrics,
    "detect_anomaly": tool_detect_anomaly,
    "restart_service": tool_restart_service,
    "summarize_infra": tool_summarize_infra
}


class LangChainOrchestrator:
    """LangChain-powered orchestrator for cloud operations workflows."""
    
    def __init__(self):
        self.tools = MCP_TOOLS
        self.langchain_tools = _create_langchain_tools()
        self.workflow_history: List[Dict[str, Any]] = []
        self._integrations_used = ["LangChain", "MCP"]

    def get_tools(self) -> List[Tool]:
        """Get LangChain tool wrappers."""
        return self.langchain_tools

    def execute_tool(self, tool_name: str, params: Any = None) -> Dict[str, Any]:
        """Execute a tool via LangChain tool wrapper."""
        for tool in self.langchain_tools:
            if tool.name == tool_name:
                result = tool.func(params)
                self._integrations_used.append(f"Tool:{tool_name}")
                return result
        return {"error": f"Tool not found: {tool_name}"}

    def execute_workflow(self, workflow_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a predefined workflow using LangChain tools."""
        params = params or {}
        
        if workflow_type == "cost_optimization":
            return self._cost_optimization_workflow(params)
        elif workflow_type == "health_check":
            return self._health_check_workflow(params)
        elif workflow_type == "full_analysis":
            return self._full_analysis_workflow(params)
        else:
            return {"success": False, "error": f"Unknown workflow: {workflow_type}"}

    def _cost_optimization_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run cost optimization analysis using LangChain tools."""
        results = {}
        
        # Step 1: Get idle instances via LangChain tool
        idle_result = self.execute_tool("list_idle_instances")
        results["idle_instances"] = idle_result
        
        # Step 2: Get billing forecast
        month = params.get("month", datetime.now().strftime("%Y-%m"))
        billing_result = self.execute_tool("get_billing_forecast", month)
        results["billing_forecast"] = billing_result
        
        # Step 3: Calculate potential savings
        idle_instances = idle_result.get("idle_instances", [])
        total_savings = idle_result.get("total_monthly_savings", 0)
        
        results["analysis"] = {
            "idle_count": len(idle_instances),
            "potential_monthly_savings": total_savings,
            "predicted_cost": billing_result.get("predicted_cost", 0),
            "optimized_cost": billing_result.get("predicted_cost", 0) - total_savings,
            "recommendations": [
                f"Terminate {len(idle_instances)} idle instances to save ${total_savings:.2f}/month",
                "Implement auto-scaling policies",
                "Review reserved instance usage"
            ]
        }
        
        self.workflow_history.append({
            "workflow": "cost_optimization",
            "timestamp": datetime.now().isoformat(),
            "integrations": self._integrations_used.copy()
        })
        
        return {"success": True, "workflow": "cost_optimization", "results": results, "integrations": self._integrations_used}


    def _health_check_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run service health analysis using LangChain tools."""
        service_id = params.get("service_id")
        if not service_id:
            return {"success": False, "error": "service_id required"}
        
        results = {}
        
        # Step 1: Get metrics via LangChain tool
        metrics_result = self.execute_tool("get_metrics", service_id)
        results["metrics"] = metrics_result
        
        # Step 2: Detect anomalies
        anomaly_result = self.execute_tool("detect_anomaly", service_id)
        results["anomalies"] = anomaly_result
        
        # Step 3: Generate health summary
        has_anomaly = anomaly_result.get("has_anomaly", False)
        severity = anomaly_result.get("severity", "none")
        
        health_status = "critical" if severity in ["critical", "high"] else "degraded" if has_anomaly else "healthy"
        
        results["health_summary"] = {
            "service_id": service_id,
            "status": health_status,
            "has_anomaly": has_anomaly,
            "severity": severity,
            "recommended_action": anomaly_result.get("recommended_action", "Continue monitoring")
        }
        
        self.workflow_history.append({
            "workflow": "health_check",
            "timestamp": datetime.now().isoformat(),
            "service_id": service_id,
            "integrations": self._integrations_used.copy()
        })
        
        return {"success": True, "workflow": "health_check", "results": results, "integrations": self._integrations_used}

    def _full_analysis_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete infrastructure analysis using LangChain tools."""
        results = {}
        
        # Step 1: Get infrastructure summary
        summary_result = self.execute_tool("summarize_infra")
        results["summary"] = summary_result
        
        # Step 2: Get idle instances
        idle_result = self.execute_tool("list_idle_instances")
        results["idle_analysis"] = idle_result
        
        # Step 3: Run cost optimization
        cost_workflow = self._cost_optimization_workflow(params)
        results["cost_analysis"] = cost_workflow.get("results", {})
        
        # Step 4: Aggregate results
        report = summary_result.get("report", {})
        
        results["executive_summary"] = {
            "infra_health": report.get("infra_health", "Unknown"),
            "total_instances": summary_result.get("summary", {}).get("total_instances", 0),
            "idle_instances": len(idle_result.get("idle_instances", [])),
            "potential_savings": idle_result.get("total_monthly_savings", 0),
            "recommended_actions": report.get("recommended_actions", []),
            "integrations_used": self._integrations_used
        }
        
        self.workflow_history.append({
            "workflow": "full_analysis",
            "timestamp": datetime.now().isoformat(),
            "integrations": self._integrations_used.copy()
        })
        
        return {"success": True, "workflow": "full_analysis", "results": results, "integrations": self._integrations_used}

    def get_workflow_history(self) -> List[Dict[str, Any]]:
        """Return history of executed workflows."""
        return self.workflow_history.copy()


# Global orchestrator instance with LangChain
orchestrator = LangChainOrchestrator()
