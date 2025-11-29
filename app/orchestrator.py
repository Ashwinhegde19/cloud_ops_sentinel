from typing import Dict, Any, List
from .mcp_server import MCP_TOOLS
from .llm_client import llm_client

class Orchestrator:
    def __init__(self):
        self.tools = MCP_TOOLS
        self.llm = llm_client

    def execute_workflow(self, workflow_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a predefined workflow using available tools"""
        if workflow_type == "cost_optimization":
            return self._cost_optimization_workflow(params)
        elif workflow_type == "health_check":
            return self._health_check_workflow(params)
        elif workflow_type == "full_analysis":
            return self._full_analysis_workflow(params)
        else:
            return {"success": False, "error": f"Unknown workflow: {workflow_type}"}

    def _cost_optimization_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run cost optimization analysis"""
        results = {}

        # Step 1: Get idle instances
        idle_result = self.tools["list_idle_instances"]()
        results["idle_instances"] = idle_result

        # Step 2: Get billing forecast
        billing_result = self.tools["get_billing_forecast"]()
        results["billing_forecast"] = billing_result

        # Step 3: Calculate potential savings
        idle_instances = idle_result.get("idle_instances", [])
        potential_savings = sum(inst.get("estimated_monthly_cost", 0) for inst in idle_instances)

        results["analysis"] = {
            "idle_count": len(idle_instances),
            "potential_monthly_savings": potential_savings,
            "recommendations": [
                "Consider terminating or downsizing idle instances",
                "Implement auto-scaling policies",
                "Review reserved instance usage"
            ]
        }

        return {
            "success": True,
            "workflow": "cost_optimization",
            "results": results
        }

    def _health_check_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run service health analysis"""
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
        anomalies = anomaly_result.get("anomalies", [])
        health_status = "healthy" if len(anomalies) == 0 else "degraded"

        results["health_summary"] = {
            "service_id": service_id,
            "status": health_status,
            "anomaly_count": len(anomalies),
            "recommendations": [
                "Monitor service performance closely" if health_status == "degraded" else "Service is operating normally"
            ]
        }

        return {
            "success": True,
            "workflow": "health_check",
            "results": results
        }

    def _full_analysis_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete infrastructure analysis"""
        results = {}

        # Step 1: Get infrastructure summary
        summary_result = self.tools["summarize_infra"]()
        results["summary"] = summary_result

        # Step 2: Get idle instances for cost analysis
        idle_result = self.tools["list_idle_instances"]()
        results["idle_analysis"] = idle_result

        # Step 3: Run cost optimization
        cost_workflow = self._cost_optimization_workflow({})
        results["cost_analysis"] = cost_workflow

        # Step 4: Generate comprehensive report using LLM
        analysis_data = {
            "summary": summary_result.get("summary_data", {}),
            "cost_savings": cost_workflow.get("results", {}),
            "idle_instances": idle_result.get("idle_instances", [])
        }

        llm_report = self.llm.generate_ops_report(analysis_data)
        results["llm_report"] = llm_report

        return {
            "success": True,
            "workflow": "full_analysis",
            "results": results,
            "executive_summary": llm_report.get("report", "")
        }

# Global orchestrator instance
orchestrator = Orchestrator()