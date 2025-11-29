"""
Ops Chat Agent - Natural Language Interface for Cloud Operations
LangChain-powered conversational agent with MCP tool-calling and SambaNova LLM.
"""

import os
import re
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any

from .models import Intent, ChatResponse
from .mcp_server import (
    tool_list_idle_instances,
    tool_get_billing_forecast,
    tool_get_metrics,
    tool_detect_anomaly,
    tool_restart_service,
    tool_summarize_infra
)
from .hygiene_score import calculate_hygiene_score


# Tool definitions for LLM
TOOL_DEFINITIONS = [
    {
        "name": "list_idle_instances",
        "description": "Detect idle compute instances based on CPU, RAM, and network activity. Returns instances with low utilization that could be terminated for cost savings.",
        "parameters": {}
    },
    {
        "name": "get_billing_forecast",
        "description": "Forecast cloud costs for a specific month based on historical usage patterns.",
        "parameters": {"month": "Month in YYYY-MM format (optional, defaults to current month)"}
    },
    {
        "name": "get_metrics",
        "description": "Get performance metrics (CPU, RAM, latency, error rate) for a specific service.",
        "parameters": {"service_id": "Service ID (e.g., svc_web, svc_api, svc_db, svc_cache, svc_worker, svc_auth)"}
    },
    {
        "name": "detect_anomaly",
        "description": "Detect anomalies in service behavior using metrics analysis.",
        "parameters": {"service_id": "Service ID to analyze"}
    },
    {
        "name": "restart_service",
        "description": "Restart a service via Modal or Blaxel compute backend.",
        "parameters": {"service_id": "Service ID to restart"}
    },
    {
        "name": "summarize_infra",
        "description": "Generate comprehensive infrastructure summary with health status, cost analysis, and recommendations.",
        "parameters": {}
    },
    {
        "name": "get_hygiene_score",
        "description": "Calculate the infrastructure hygiene score (0-100) measuring overall health based on idle instances, anomalies, cost risk, and restart failures.",
        "parameters": {}
    }
]

# Known service names for entity extraction
KNOWN_SERVICES = ["svc_web", "svc_api", "svc_db", "svc_cache", "svc_worker", "svc_auth"]


def _execute_hygiene_score(params: Dict) -> Dict:
    """Execute hygiene score calculation."""
    from .models import AnomalyResult, CostForecast
    
    summary = tool_summarize_infra()
    idle_result = tool_list_idle_instances()
    
    anomalies = summary.get("anomalies", [])
    cost_forecast = summary.get("billing_forecast", {})
    
    anomaly_objects = []
    for a in anomalies:
        if isinstance(a, dict):
            anomaly_objects.append(AnomalyResult(**a))
        elif isinstance(a, AnomalyResult):
            anomaly_objects.append(a)
    
    forecast_obj = None
    if cost_forecast:
        if isinstance(cost_forecast, dict):
            forecast_obj = CostForecast(**cost_forecast)
        elif isinstance(cost_forecast, CostForecast):
            forecast_obj = cost_forecast
    
    total_instances = summary.get("summary", {}).get("total_instances", 10)
    idle_count = len(idle_result.get("idle_instances", []))
    
    hygiene = calculate_hygiene_score(
        total_instances=total_instances,
        idle_instances=idle_count,
        anomalies=anomaly_objects,
        cost_forecast=forecast_obj
    )
    data = hygiene.model_dump()
    data["calculated_at"] = data["calculated_at"].isoformat()
    return data


# Tool function mapping (defined after _execute_hygiene_score)
TOOL_FUNCTIONS = {
    "list_idle_instances": lambda params: tool_list_idle_instances(),
    "get_billing_forecast": lambda params: tool_get_billing_forecast(params.get("month", datetime.now().strftime("%Y-%m"))),
    "get_metrics": lambda params: tool_get_metrics(params.get("service_id", "svc_web")),
    "detect_anomaly": lambda params: tool_detect_anomaly(params.get("service_id", "svc_web")),
    "restart_service": lambda params: tool_restart_service(params.get("service_id")),
    "summarize_infra": lambda params: tool_summarize_infra(),
    "get_hygiene_score": _execute_hygiene_score
}


def _build_system_prompt() -> str:
    """Build the system prompt for the LLM agent."""
    tools_desc = "\n".join([
        f"- {t['name']}: {t['description']}" 
        for t in TOOL_DEFINITIONS
    ])
    
    return f"""You are Cloud Ops Sentinel, an AI-powered cloud operations assistant. You help DevOps engineers manage their infrastructure through natural language.

Available tools:
{tools_desc}

Available services: svc_web, svc_api, svc_db, svc_cache, svc_worker, svc_auth

When the user asks a question:
1. Determine which tool(s) to call based on their request
2. Extract any parameters needed (like service_id or month)
3. Respond with a JSON object containing your tool calls

Response format (MUST be valid JSON):
{{
    "thought": "Brief explanation of what you're doing",
    "tool_calls": [
        {{"tool": "tool_name", "params": {{"param": "value"}}}}
    ],
    "clarification": null
}}

If the query is ambiguous or you need more information:
{{
    "thought": "Why clarification is needed",
    "tool_calls": [],
    "clarification": "Your question to the user"
}}

Examples:
- "show idle instances" -> {{"thought": "User wants to see idle instances", "tool_calls": [{{"tool": "list_idle_instances", "params": {{}}}}], "clarification": null}}
- "restart the web service" -> {{"thought": "User wants to restart svc_web", "tool_calls": [{{"tool": "restart_service", "params": {{"service_id": "svc_web"}}}}], "clarification": null}}
- "what's wrong with api?" -> {{"thought": "User asking about svc_api issues", "tool_calls": [{{"tool": "get_metrics", "params": {{"service_id": "svc_api"}}}}, {{"tool": "detect_anomaly", "params": {{"service_id": "svc_api"}}}}], "clarification": null}}
- "give me a full analysis" -> {{"thought": "User wants comprehensive overview", "tool_calls": [{{"tool": "summarize_infra", "params": {{}}}}, {{"tool": "list_idle_instances", "params": {{}}}}, {{"tool": "get_hygiene_score", "params": {{}}}}], "clarification": null}}

Be helpful and proactive. If a user mentions a service name like "web", "api", "db", map it to the correct service_id (svc_web, svc_api, svc_db, etc.)."""


def _call_llm_for_intent(message: str, history: List[Dict]) -> Dict:
    """Call SambaNova LLM to determine intent and tool calls."""
    sambanova_key = os.getenv("SAMBANOVA_API_KEY", "")
    endpoint = os.getenv("SAMBANOVA_ENDPOINT", "https://api.sambanova.ai/v1")
    
    # Check if key is valid
    if not sambanova_key or "your_" in sambanova_key.lower() or len(sambanova_key) < 10:
        # Fall back to regex-based parsing
        return _fallback_intent_parsing(message)
    
    try:
        # Build conversation context
        messages = [{"role": "system", "content": _build_system_prompt()}]
        
        # Add recent history for context (last 3 exchanges)
        for h in history[-3:]:
            messages.append({"role": "user", "content": h.get("user", "")})
            messages.append({"role": "assistant", "content": h.get("assistant", "")})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        headers = {
            "Authorization": f"Bearer {sambanova_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "Meta-Llama-3.1-8B-Instruct",
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.1  # Low temperature for consistent tool selection
        }
        
        response = requests.post(
            f"{endpoint}/chat/completions",
            json=payload,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Parse JSON response from LLM
        return _parse_llm_response(content)
        
    except Exception as e:
        # Fall back to regex-based parsing on any error
        print(f"LLM call failed: {e}, falling back to regex parsing")
        return _fallback_intent_parsing(message)


def _parse_llm_response(content: str) -> Dict:
    """Parse the LLM's JSON response."""
    try:
        # Try to extract JSON from the response
        # Sometimes LLM wraps JSON in markdown code blocks
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group())
        return {"thought": "Could not parse response", "tool_calls": [], "clarification": "I didn't understand that. Could you rephrase?"}
    except json.JSONDecodeError:
        return {"thought": "Invalid JSON", "tool_calls": [], "clarification": "I had trouble understanding. Please try again."}


def _fallback_intent_parsing(message: str) -> Dict:
    """Fallback regex-based intent parsing when LLM is unavailable."""
    message_lower = message.lower().strip()
    
    # Intent patterns with typo tolerance
    patterns = {
        "list_idle_instances": [r"\bidle\b", r"\bidel\b", r"\bunused\b", r"\binactive\b", r"\bwasted?\b"],
        "get_metrics": [r"\bmetrics?\b", r"\bperformance\b", r"\bcpu\b", r"\bram\b", r"\blatency\b", r"\bstats?\b"],
        "get_billing_forecast": [r"\bforecast\b", r"\bcost\b", r"\bbilling\b", r"\bbudget\b", r"\bspending\b", r"\bmoney\b"],
        "detect_anomaly": [r"\banomaly\b", r"\banomalies\b", r"\bissues?\b", r"\bproblems?\b", r"\balerts?\b", r"\bdetect\b"],
        "restart_service": [r"\brestart\b", r"\breboot\b", r"\breset\b", r"\brecycle\b"],
        "summarize_infra": [r"\bsummary\b", r"\boverview\b", r"\breport\b", r"\bstatus\b", r"\binfra\w*\b", r"\bdashboard\b"],
        "get_hygiene_score": [r"\bhygiene\b", r"\bscore\b", r"\bhealth\b", r"\bgrade\b", r"\brating\b"]
    }
    
    # Find matching intent
    best_tool = None
    best_score = 0
    
    for tool, tool_patterns in patterns.items():
        score = sum(1 for p in tool_patterns if re.search(p, message_lower))
        if score > best_score:
            best_score = score
            best_tool = tool
    
    if best_score == 0:
        return {
            "thought": "Could not determine intent",
            "tool_calls": [],
            "clarification": _generate_help_message()
        }
    
    # Extract service_id if needed
    params = {}
    if best_tool in ["get_metrics", "detect_anomaly", "restart_service"]:
        service_id = _extract_service_id(message_lower)
        if service_id:
            params["service_id"] = service_id
        elif best_tool == "restart_service":
            return {
                "thought": "Need service ID for restart",
                "tool_calls": [],
                "clarification": "Which service would you like to restart? Available: svc_web, svc_api, svc_db, svc_cache, svc_worker, svc_auth"
            }
    
    # Extract month for forecast
    if best_tool == "get_billing_forecast":
        month_match = re.search(r'\b(\d{4}-\d{2})\b', message)
        if month_match:
            params["month"] = month_match.group(1)
    
    return {
        "thought": f"Using fallback parsing, detected {best_tool}",
        "tool_calls": [{"tool": best_tool, "params": params}],
        "clarification": None
    }


def _extract_service_id(text: str) -> Optional[str]:
    """Extract service ID from text with fuzzy matching."""
    # Direct match
    for svc in KNOWN_SERVICES:
        if svc in text:
            return svc
    
    # Fuzzy match common names
    name_map = {
        "web": "svc_web", "api": "svc_api", "db": "svc_db",
        "database": "svc_db", "cache": "svc_cache", "worker": "svc_worker", "auth": "svc_auth"
    }
    
    for name, svc_id in name_map.items():
        if re.search(rf'\b{name}\b', text):
            return svc_id
    
    return None


def _generate_help_message() -> str:
    """Generate help message for ambiguous queries."""
    return """I didn't quite understand that. Here's what I can help with:

• "Show idle instances" - Find underutilized resources
• "Get metrics for svc_web" - Check service performance
• "What's the cost forecast?" - Predict cloud spending
• "Check for anomalies in api" - Detect service issues
• "Restart svc_api" - Restart a service
• "Show summary" - Get infrastructure overview
• "What's the hygiene score?" - Check overall health

Please try rephrasing your question."""


def _execute_tools(tool_calls: List[Dict]) -> Dict[str, Any]:
    """Execute the requested tools and collect results."""
    results = {}
    tools_called = []
    errors = []
    
    for call in tool_calls:
        tool_name = call.get("tool")
        params = call.get("params", {})
        
        if tool_name not in TOOL_FUNCTIONS:
            errors.append(f"Unknown tool: {tool_name}")
            continue
        
        try:
            result = TOOL_FUNCTIONS[tool_name](params)
            results[tool_name] = result
            tools_called.append(tool_name)
        except Exception as e:
            errors.append(f"Error executing {tool_name}: {str(e)}")
    
    return {
        "results": results,
        "tools_called": tools_called,
        "errors": errors
    }


def _generate_response(results: Dict[str, Any], thought: str) -> str:
    """Generate natural language response from tool results using LLM."""
    sambanova_key = os.getenv("SAMBANOVA_API_KEY", "")
    endpoint = os.getenv("SAMBANOVA_ENDPOINT", "https://api.sambanova.ai/v1")
    
    # Check if key is valid
    if not sambanova_key or "your_" in sambanova_key.lower() or len(sambanova_key) < 10:
        return _format_results_fallback(results)
    
    try:
        # Prepare results summary for LLM
        results_summary = json.dumps(results, indent=2, default=str)[:3000]  # Limit size
        
        prompt = f"""Based on these tool results, provide a helpful, concise response to the user.
Be conversational and highlight the most important information.

Tool Results:
{results_summary}

Provide a natural language summary (2-4 sentences) with key insights. Use bullet points for lists if needed."""

        headers = {
            "Authorization": f"Bearer {sambanova_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "Meta-Llama-3.1-8B-Instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
            "temperature": 0.3
        }
        
        response = requests.post(
            f"{endpoint}/chat/completions",
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        return response.json()["choices"][0]["message"]["content"]
        
    except Exception:
        return _format_results_fallback(results)


def _format_results_fallback(results: Dict[str, Any]) -> str:
    """Format results without LLM (fallback)."""
    tool_results = results.get("results", {})
    
    if not tool_results:
        return "I processed your request but didn't get any results. Please try again."
    
    responses = []
    
    if "list_idle_instances" in tool_results:
        data = tool_results["list_idle_instances"]
        instances = data.get("idle_instances", [])
        savings = data.get("total_monthly_savings", 0)
        if instances:
            responses.append(f"Found {len(instances)} idle instances. Potential monthly savings: ${savings:.2f}.")
        else:
            responses.append("No idle instances detected. Resources are being utilized efficiently.")
    
    if "get_metrics" in tool_results:
        data = tool_results["get_metrics"]
        service_id = data.get("service_id", "unknown")
        metrics = data.get("metrics", [])
        if metrics:
            avg_cpu = sum(m.get("cpu", 0) for m in metrics) / len(metrics)
            avg_latency = sum(m.get("latency_ms", 0) for m in metrics) / len(metrics)
            responses.append(f"Service {service_id}: CPU {avg_cpu:.1f}%, Latency {avg_latency:.0f}ms.")
    
    if "get_billing_forecast" in tool_results:
        data = tool_results["get_billing_forecast"]
        cost = data.get("predicted_cost", 0)
        confidence = data.get("confidence", 0)
        responses.append(f"Predicted cost: ${cost:.2f} (confidence: {confidence:.0%}).")
    
    if "detect_anomaly" in tool_results:
        data = tool_results["detect_anomaly"]
        if data.get("has_anomaly"):
            severity = data.get("severity", "unknown")
            reason = data.get("reason", "Unknown issue")
            responses.append(f"⚠️ Anomaly detected! Severity: {severity}. {reason}")
        else:
            responses.append("✅ No anomalies detected. Service is operating normally.")
    
    if "restart_service" in tool_results:
        data = tool_results["restart_service"]
        status = data.get("restart_status", "unknown")
        service_id = data.get("service_id", "unknown")
        health = data.get("post_restart_health", 0)
        if status == "success":
            responses.append(f"✅ Service {service_id} restarted successfully. Health: {health:.0f}%")
        else:
            responses.append(f"❌ Restart failed for {service_id}. Status: {status}")
    
    if "summarize_infra" in tool_results:
        data = tool_results["summarize_infra"]
        report = data.get("report", {})
        summary = data.get("summary", {})
        health = report.get("infra_health", "Unknown")
        total = summary.get("total_instances", 0)
        idle = summary.get("idle_instances", 0)
        responses.append(f"Infrastructure: {health}. {total} instances, {idle} idle.")
    
    if "get_hygiene_score" in tool_results:
        data = tool_results["get_hygiene_score"]
        score = data.get("score", 0)
        status = data.get("status", "unknown")
        suggestions = data.get("suggestions", [])
        suggestion = suggestions[0] if suggestions else "Continue monitoring."
        responses.append(f"Hygiene Score: {score:.0f}/100 ({status}). {suggestion}")
    
    return " ".join(responses) if responses else "Request processed. Check the results for details."


def process_chat_message(message: str, history: List[Dict] = None) -> ChatResponse:
    """
    Main entry point for processing chat messages.
    Uses LangChain-style agentic loop with SambaNova LLM.
    
    Args:
        message: User's natural language query
        history: Conversation history
    
    Returns:
        ChatResponse with message, tools called, and results
    """
    history = history or []
    
    if not message.strip():
        return ChatResponse(
            message="Please enter a question or command.",
            tools_called=[],
            results={},
            clarification_needed=False,
            timestamp=datetime.now()
        )
    
    # Step 1: Call LLM to determine intent and tool calls (agentic decision)
    llm_response = _call_llm_for_intent(message, history)
    
    # Step 2: Check if clarification is needed
    if llm_response.get("clarification"):
        return ChatResponse(
            message=llm_response["clarification"],
            tools_called=[],
            results={},
            clarification_needed=True,
            timestamp=datetime.now()
        )
    
    # Step 3: Execute the tool chain
    tool_calls = llm_response.get("tool_calls", [])
    
    if not tool_calls:
        return ChatResponse(
            message=_generate_help_message(),
            tools_called=[],
            results={},
            clarification_needed=True,
            timestamp=datetime.now()
        )
    
    try:
        execution_result = _execute_tools(tool_calls)
        
        # Check for errors
        if execution_result.get("errors") and not execution_result.get("results"):
            error_msg = execution_result["errors"][0]
            return ChatResponse(
                message=f"I encountered an issue: {error_msg}. Please try again.",
                tools_called=execution_result.get("tools_called", []),
                results={},
                clarification_needed=False,
                timestamp=datetime.now()
            )
        
        # Step 4: Generate natural language response using LLM
        response_text = _generate_response(
            execution_result,
            llm_response.get("thought", "")
        )
        
        return ChatResponse(
            message=response_text,
            tools_called=execution_result["tools_called"],
            results=execution_result["results"],
            clarification_needed=False,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        return ChatResponse(
            message=f"Sorry, I encountered an error: {str(e)}. Please try a different query.",
            tools_called=[],
            results={},
            clarification_needed=False,
            timestamp=datetime.now()
        )


# Expose parse_intent for backward compatibility
def parse_intent(message: str) -> Intent:
    """Parse user message to extract intent (backward compatibility)."""
    result = _fallback_intent_parsing(message)
    
    tool_calls = result.get("tool_calls", [])
    if tool_calls:
        tool = tool_calls[0]
        intent_type = tool.get("tool", "ambiguous").replace("_", "_")
        # Map tool names to intent types
        type_map = {
            "list_idle_instances": "query_idle",
            "get_metrics": "query_metrics",
            "get_billing_forecast": "query_forecast",
            "detect_anomaly": "query_anomaly",
            "restart_service": "action_restart",
            "summarize_infra": "query_summary",
            "get_hygiene_score": "query_hygiene"
        }
        intent_type = type_map.get(tool.get("tool"), "ambiguous")
        return Intent(
            type=intent_type,
            entities=tool.get("params", {}),
            confidence=0.8
        )
    
    return Intent(type="ambiguous", entities={}, confidence=0.0)
