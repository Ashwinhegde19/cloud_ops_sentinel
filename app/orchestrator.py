"""
Cloud Ops Sentinel Orchestrator
LangChain-style workflow orchestration for multi-step operations
"""

from typing import Dict, Any, List
from datetime import datetime

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


# Tool registry for orchestration
MCP_TOOLS = {
    "list_idle_instances": tool_list_idle_instances,
    "get_billing_forecast": tool_get_billing_forecast,
    "get_metrics": tool_get_metrics,
    "detect_anomaly": tool_detect_anomaly,
    "restart_service": tool_restart_service,
    "summarize_infra": tool_summarize_infra
}


class Orchestrator:
    """Orchestrates multi-step cloud operations workflows."""
    
    def __init__(self):
        self.tools = MCP_TOOLS
        self.workflow_history: List[Dict[str, Any]] = []

    def execute_workflow(self, workflow_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a predefined workflow using available tools.
        
        Supported workflows:
        - cost_optimization: Analyze idle instances and billing forecast
        - health_check: Get metrics and detect anomalies for a service
        - full_analysis: Complete infrastructure analysis with LLM report
        """
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
        """Run cost optimization analysis (Requirements 8.2)."""
        results = {}
        
        # Step 1: Get idle instances
        idle_result = self.tools["list_idle_instances"]()
        results["idle_instances"] = idle_result
        
        # Step 2: Get billing forecast
        month = params.get("month", datetime.now().strftime("%Y-%m"))
        billing_result = self.tools["get_billing_forecast"](month)
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
                "Implement auto-scaling policies for variable workloads",
                "Review reserved instance usage for additional savings",
                "Set up cost alerts for budget monitoring"
            ]
        }
        
        self.workflow_history.append({
            "workflow": "cost_optimization",
            "timestamp": datetime.now().isoformat(),
            "results": results
        })
        
        return {
            "success": True,
            "workflow": "cost_optimization",
            "results": results
        }


    def _health_check_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run service health analysis (Requirements 8.2)."""
        service_id = params.get("service_id")
        if not service_id:
            return {"success": False, "error": "service_id required"}
        
        results = {}
        
        # Step 1: Get metrics
        metrics_result = self.tools["get_metrics"](service_id)
        results["metrics"] = metrics_result
        
        # Step 2: Detect anomalies
        anomaly_result = self.tools["detect_anomaly"](service_id)
        results["anomalies"] = anomaly_result
        
        # Step 3: Generate health summary
        has_anomaly = anomaly_result.get("has_anomaly", False)
        severity = anomaly_result.get("severity", "none")
        
        if severity in ["critical", "high"]:
            health_status = "critical"
        elif severity == "medium" or has_anomaly:
            health_status = "degraded"
        else:
            health_status = "healthy"
        
        results["health_summary"] = {
            "service_id": service_id,
            "status": health_status,
            "has_anomaly": has_anomaly,
            "severity": severity,
            "anomaly_type": anomaly_result.get("anomaly_type"),
            "recommended_action": anomaly_result.get("recommended_action", "Continue monitoring"),
            "metrics_count": len(metrics_result.get("metrics", [])),
            "recommendations": [
                anomaly_result.get("recommended_action", "Continue monitoring"),
                "Set up alerting for this service" if has_anomaly else "Service is operating normally"
            ]
        }
        
        self.workflow_history.append({
            "workflow": "health_check",
            "timestamp": datetime.now().isoformat(),
            "service_id": service_id,
            "results": results
        })
        
        return {
            "success": True,
            "workflow": "health_check",
            "results": results
        }

    def _full_analysis_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete infrastructure analysis (Requirements 8.2, 8.4)."""
        results = {}
        
        # Step 1: Get infrastructure summary (includes LLM report)
        summary_result = self.tools["summarize_infra"]()
        results["summary"] = summary_result
        
        # Step 2: Get idle instances for cost analysis
        idle_result = self.tools["list_idle_instances"]()
        results["idle_analysis"] = idle_result
        
        # Step 3: Run cost optimization workflow
        cost_workflow = self._cost_optimization_workflow(params)
        results["cost_analysis"] = cost_workflow.get("results", {})
        
        # Step 4: Aggregate all results
        report = summary_result.get("report", {})
        
        results["executive_summary"] = {
            "infra_health": report.get("infra_health", "Unknown"),
            "total_instances": summary_result.get("summary", {}).get("total_instances", 0),
            "idle_instances": len(idle_result.get("idle_instances", [])),
            "potential_savings": idle_result.get("total_monthly_savings", 0),
            "anomaly_count": len([a for a in summary_result.get("summary_data", {}).get("anomalies", []) if a.get("has_anomaly")]),
            "recommended_actions": report.get("recommended_actions", []),
            "sponsor_integrations_used": summary_result.get("sponsor_integrations_used", [])
        }
        
        self.workflow_history.append({
            "workflow": "full_analysis",
            "timestamp": datetime.now().isoformat(),
            "results": results
        })
        
        return {
            "success": True,
            "workflow": "full_analysis",
            "results": results,
            "executive_summary": results["executive_summary"]
        }

    def get_workflow_history(self) -> List[Dict[str, Any]]:
        """Return history of executed workflows."""
        return self.workflow_history.copy()

    def clear_history(self):
        """Clear workflow history."""
        self.workflow_history = []


# Global orchestrator instance
orchestrator = Orchestrator()
