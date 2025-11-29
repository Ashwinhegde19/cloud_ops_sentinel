"""
PDF Report Generator
Generates downloadable PDF/Markdown reports with SambaNova narratives.
"""

import io
from datetime import datetime
from typing import Dict, List, Optional, Any

from .models import (
    ReportData, HygieneScore, Instance, AnomalyResult, CostForecast
)
from .mcp_server import (
    tool_list_idle_instances,
    tool_summarize_infra,
    tool_get_billing_forecast
)
from .hygiene_score import calculate_hygiene_score
from .llm_client import generate_short_explanation


def build_report_data() -> ReportData:
    """
    Aggregate all data needed for the report.
    
    Returns:
        ReportData with all sections populated
    """
    # Get infrastructure summary
    summary_result = tool_summarize_infra()
    report = summary_result.get("report", {})
    summary = summary_result.get("summary", {})
    
    # Get idle instances
    idle_result = tool_list_idle_instances()
    idle_instances = []
    for inst in idle_result.get("idle_instances", []):
        if isinstance(inst, dict):
            idle_instances.append(Instance(**inst))
        elif isinstance(inst, Instance):
            idle_instances.append(inst)
    
    # Get billing forecast
    month = datetime.now().strftime("%Y-%m")
    forecast_result = tool_get_billing_forecast(month)
    cost_forecast = CostForecast(**forecast_result) if forecast_result else None
    
    # Get anomalies from summary
    anomalies = []
    for a in summary_result.get("anomalies", []):
        if isinstance(a, dict):
            anomalies.append(AnomalyResult(**a))
        elif isinstance(a, AnomalyResult):
            anomalies.append(a)
    
    # Calculate hygiene score
    total_instances = summary.get("total_instances", 10)
    hygiene = calculate_hygiene_score(
        total_instances=total_instances,
        idle_instances=len(idle_instances),
        anomalies=anomalies,
        cost_forecast=cost_forecast
    )
    
    # Build executive summary
    exec_summary = _build_executive_summary(summary, idle_instances, anomalies, hygiene)
    
    # Build recommendations
    recommendations = report.get("recommended_actions", [])
    if not recommendations:
        recommendations = hygiene.suggestions
    
    return ReportData(
        generated_at=datetime.now(),
        report_period="Last 24 hours",
        executive_summary=exec_summary,
        hygiene_score=hygiene,
        idle_instances=idle_instances,
        anomalies=anomalies,
        cost_forecast=cost_forecast,
        recommendations=recommendations
    )


def _build_executive_summary(
    summary: Dict,
    idle_instances: List[Instance],
    anomalies: List[AnomalyResult],
    hygiene: HygieneScore
) -> str:
    """Build executive summary text."""
    total = summary.get("total_instances", 0)
    running = summary.get("running_instances", 0)
    idle_count = len(idle_instances)
    anomaly_count = len([a for a in anomalies if a.has_anomaly])
    
    return f"""Infrastructure Overview: Monitoring {total} instances with {running} actively running. 
{idle_count} idle instances identified for potential cost optimization. 
{anomaly_count} service anomalies detected requiring attention.
Overall Infrastructure Hygiene Score: {hygiene.score:.0f}/100 ({hygiene.status})."""


def create_section_narrative(section: str, data: Dict) -> str:
    """
    Generate LLM-powered narrative for a report section.
    
    Args:
        section: Section name
        data: Section data
    
    Returns:
        Narrative text for the section
    """
    try:
        prompt = f"Write a brief 2-3 sentence summary for the {section} section of a cloud operations report. Data: {str(data)[:500]}"
        return generate_short_explanation(prompt)
    except Exception:
        return _get_template_narrative(section, data)


def _get_template_narrative(section: str, data: Dict) -> str:
    """Fallback template-based narrative."""
    templates = {
        "idle_instances": "Idle instances represent underutilized resources that could be terminated or downsized to reduce costs.",
        "anomalies": "Service anomalies indicate potential issues that require investigation and remediation.",
        "cost_forecast": "Cost forecasting helps plan budgets and identify optimization opportunities.",
        "hygiene_score": "The hygiene score provides a quick assessment of overall infrastructure health.",
        "recommendations": "Following these recommendations will improve infrastructure efficiency and reduce costs."
    }
    return templates.get(section, f"This section covers {section} information.")


def generate_pdf_report() -> bytes:
    """
    Generate PDF report document.
    
    Returns:
        PDF file as bytes
    """
    try:
        from fpdf import FPDF
    except ImportError:
        # If fpdf not available, return markdown as bytes
        markdown = generate_markdown_report()
        return markdown.encode('utf-8')
    
    report_data = build_report_data()
    
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "Cloud Ops Sentinel Report", new_x="LMARGIN", new_y="NEXT", align="C")
    
    # Metadata
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Generated: {report_data.generated_at.strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 6, f"Report Period: {report_data.report_period}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(8)
    
    # Executive Summary
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Executive Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, report_data.executive_summary)
    pdf.ln(4)
    
    # Hygiene Score
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Infrastructure Hygiene Score", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    if report_data.hygiene_score:
        score = report_data.hygiene_score
        pdf.cell(0, 6, f"Score: {score.score:.0f}/100 - Status: {score.status.upper()}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    # Idle Instances
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Idle Instances", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    if report_data.idle_instances:
        pdf.cell(0, 5, f"Found {len(report_data.idle_instances)} idle instances", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 5, "No idle instances detected.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    # Anomalies
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Anomalies Detected", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    active_anomalies = [a for a in report_data.anomalies if a.has_anomaly]
    if active_anomalies:
        pdf.cell(0, 5, f"Found {len(active_anomalies)} anomalies", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 5, "No anomalies detected.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    # Cost Forecast
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Cost Forecast", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    if report_data.cost_forecast:
        cf = report_data.cost_forecast
        pdf.cell(0, 5, f"Predicted Cost: ${cf.predicted_cost:.2f} (Confidence: {cf.confidence:.0%})", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    # Recommendations
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Recommendations", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for i, rec in enumerate(report_data.recommendations[:5], 1):
        rec_text = rec[:80] if len(rec) > 80 else rec
        pdf.cell(0, 5, f"{i}. {rec_text}", new_x="LMARGIN", new_y="NEXT")
    
    return pdf.output()


def generate_markdown_report() -> str:
    """
    Generate Markdown report as fallback.
    
    Returns:
        Markdown formatted report string
    """
    report_data = build_report_data()
    
    lines = [
        "# Cloud Ops Sentinel Report",
        "",
        f"**Generated:** {report_data.generated_at.strftime('%Y-%m-%d %H:%M')}",
        f"**Report Period:** {report_data.report_period}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        report_data.executive_summary,
        "",
        "---",
        "",
        "## Infrastructure Hygiene Score",
        ""
    ]
    
    if report_data.hygiene_score:
        score = report_data.hygiene_score
        lines.extend([
            f"**Score:** {score.score:.0f}/100",
            f"**Status:** {score.status.upper()}",
            "",
            "### Breakdown",
            ""
        ])
        for factor, value in score.breakdown.items():
            if not factor.endswith("_count") and not factor.endswith("_rate") and not factor.endswith("_percentage"):
                lines.append(f"- {factor}: {value:.1f}")
    
    lines.extend([
        "",
        "---",
        "",
        "## Idle Instances",
        ""
    ])
    
    if report_data.idle_instances:
        lines.append(f"Found **{len(report_data.idle_instances)}** idle instances:")
        lines.append("")
        lines.append("| Instance ID | Avg CPU | Region |")
        lines.append("|-------------|---------|--------|")
        for inst in report_data.idle_instances[:10]:
            avg_cpu = sum(inst.cpu_usage) / len(inst.cpu_usage) if inst.cpu_usage else 0
            region = inst.tags.get("region", "N/A")
            lines.append(f"| {inst.instance_id} | {avg_cpu:.1f}% | {region} |")
    else:
        lines.append("✅ No idle instances detected.")
    
    lines.extend([
        "",
        "---",
        "",
        "## Anomalies Detected",
        ""
    ])
    
    active_anomalies = [a for a in report_data.anomalies if a.has_anomaly]
    if active_anomalies:
        lines.append(f"Found **{len(active_anomalies)}** anomalies:")
        lines.append("")
        for anomaly in active_anomalies[:10]:
            lines.append(f"- **{anomaly.service_id}** ({anomaly.severity}): {anomaly.reason}")
    else:
        lines.append("✅ No anomalies detected.")
    
    lines.extend([
        "",
        "---",
        "",
        "## Cost Forecast",
        ""
    ])
    
    if report_data.cost_forecast:
        cf = report_data.cost_forecast
        lines.extend([
            f"**Predicted Cost:** ${cf.predicted_cost:.2f}",
            f"**Confidence:** {cf.confidence:.0%}",
            ""
        ])
        if cf.breakdown:
            lines.append("### Breakdown by Tier")
            lines.append("")
            for tier, cost in cf.breakdown.items():
                lines.append(f"- {tier}: ${cost:.2f}")
    
    lines.extend([
        "",
        "---",
        "",
        "## Recommendations",
        ""
    ])
    
    for i, rec in enumerate(report_data.recommendations, 1):
        lines.append(f"{i}. {rec}")
    
    lines.extend([
        "",
        "---",
        "",
        "*Report generated by Cloud Ops Sentinel*"
    ])
    
    return "\n".join(lines)
