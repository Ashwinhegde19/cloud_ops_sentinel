"""
Cloud Ops Sentinel Gradio 6 UI
Web interface for cloud infrastructure monitoring and management
"""

import gradio as gr
import json
import asyncio
import pandas as pd
from typing import Dict, Any, List
from data_generator import cloud_data


class CloudOpsUI:
    def __init__(self):
        self.data_generator = cloud_data

        # UI initialized - Gradio 6.x compatible

    def create_idle_instances_tab(self):
        """Create tab for listing idle instances"""
        with gr.Tab("🚫 Idle Instances"):
            gr.Markdown("## Instances with Low CPU Utilization")

            refresh_btn = gr.Button("Refresh Idle Instances", variant="primary")
            idle_instances_table = gr.Dataframe(
                headers=["Instance ID", "Name", "Type", "CPU %", "Memory %", "Cost/Hr", "Region", "Monthly Savings"],
                label="Idle Instances",
                row_count=(0, "dynamic"),
                column_count=(8, "fixed"),
                wrap=True
            )

            total_savings_text = gr.Textbox(label="Potential Monthly Savings", value="")

            refresh_btn.click(
                self.get_idle_instances,
                outputs=[idle_instances_table, total_savings_text]
            )

    def create_billing_forecast_tab(self):
        """Create tab for billing forecasts"""
        with gr.Tab("💰 Billing Forecast"):
            gr.Markdown("## Cloud Cost Analysis and Forecasting")

            days_input = gr.Slider(1, 90, value=30, step=1, label="Forecast Period (Days)")
            forecast_btn = gr.Button("Generate Forecast", variant="primary")

            with gr.Row():
                with gr.Column():
                    current_daily = gr.Textbox(label="Current Daily Cost")
                    projected_monthly = gr.Textbox(label="Projected Monthly Cost")
                    potential_savings = gr.Textbox(label="Potential Savings")

                with gr.Column():
                    running_instances = gr.Textbox(label="Running Instances")
                    idle_instances_count = gr.Textbox(label="Idle Instances")
                    error_instances = gr.Textbox(label="Error Instances")

            recommendations = gr.JSON(label="Recommendations")

            forecast_btn.click(
                self.get_billing_forecast,
                inputs=[days_input],
                outputs=[current_daily, projected_monthly, potential_savings,
                        running_instances, idle_instances_count, error_instances, recommendations]
            )

    def create_metrics_tab(self):
        """Create tab for service metrics"""
        with gr.Tab("📊 Service Metrics"):
            gr.Markdown("## Performance Metrics Analysis")

            # Service selection
            instances = self.data_generator.get_all_instances()
            service_choices = [(f"{i.name} ({i.instance_id})", i.instance_id) for i in instances]

            service_dropdown = gr.Dropdown(
                choices=service_choices,
                label="Select Service",
                value=service_choices[0][1] if service_choices else None
            )

            hours_slider = gr.Slider(1, 168, value=24, step=1, label="Analysis Period (Hours)")
            get_metrics_btn = gr.Button("Get Metrics", variant="primary")

            with gr.Row():
                with gr.Column():
                    avg_cpu = gr.Textbox(label="Average CPU Usage")
                    max_cpu = gr.Textbox(label="Peak CPU Usage")
                    current_cpu = gr.Textbox(label="Current CPU Usage")

                with gr.Column():
                    avg_memory = gr.Textbox(label="Average Memory Usage")
                    max_memory = gr.Textbox(label="Peak Memory Usage")
                    current_memory = gr.Textbox(label="Current Memory Usage")

            with gr.Row():
                with gr.Column():
                    avg_response_time = gr.Textbox(label="Average Response Time (ms)")
                    avg_request_rate = gr.Textbox(label="Average Request Rate")

                with gr.Column():
                    current_response_time = gr.Textbox(label="Current Response Time (ms)")
                    current_request_rate = gr.Textbox(label="Current Request Rate")

            latest_data_json = gr.JSON(label="Latest Metrics Data")

            get_metrics_btn.click(
                self.get_service_metrics,
                inputs=[service_dropdown, hours_slider],
                outputs=[avg_cpu, max_cpu, current_cpu, avg_memory, max_memory, current_memory,
                        avg_response_time, avg_request_rate, current_response_time, current_request_rate, latest_data_json]
            )

    def create_anomaly_detection_tab(self):
        """Create tab for anomaly detection"""
        with gr.Tab("⚠️ Anomaly Detection"):
            gr.Markdown("## Performance Anomaly Analysis")

            instances = self.data_generator.get_all_instances()
            service_choices = [(f"{i.name} ({i.instance_id})", i.instance_id) for i in instances]

            service_dropdown = gr.Dropdown(
                choices=service_choices,
                label="Select Service to Analyze",
                value=service_choices[0][1] if service_choices else None
            )

            detect_btn = gr.Button("Detect Anomalies", variant="primary")

            with gr.Row():
                with gr.Column():
                    risk_level = gr.Textbox(label="Risk Level")
                    anomalies_count = gr.Textbox(label="Anomalies Detected")

                with gr.Column():
                    baseline_cpu = gr.Textbox(label="Baseline CPU %")
                    current_cpu = gr.Textbox(label="Current CPU %")

            anomalies_json = gr.JSON(label="Detected Anomalies")
            current_metrics_json = gr.JSON(label="Current vs Baseline Metrics")

            detect_btn.click(
                self.detect_anomalies,
                inputs=[service_dropdown],
                outputs=[risk_level, anomalies_count, baseline_cpu, current_cpu, anomalies_json, current_metrics_json]
            )

    def create_service_control_tab(self):
        """Create tab for service management"""
        with gr.Tab("🔄 Service Control"):
            gr.Markdown("## Cloud Service Management")

            instances = self.data_generator.get_all_instances()
            service_choices = [(f"{i.name} ({i.instance_id})", i.instance_id) for i in instances]

            service_dropdown = gr.Dropdown(
                choices=service_choices,
                label="Select Service",
                value=service_choices[0][1] if service_choices else None
            )

            restart_btn = gr.Button("Restart Service", variant="primary")

            restart_status = gr.Textbox(label="Restart Status")
            service_info = gr.JSON(label="Service Information")
            downtime = gr.Textbox(label="Estimated Downtime")

            restart_btn.click(
                self.restart_service,
                inputs=[service_dropdown],
                outputs=[restart_status, service_info, downtime]
            )

    def create_infrastructure_summary_tab(self):
        """Create tab for overall infrastructure summary"""
        with gr.Tab("📈 Infrastructure Overview"):
            gr.Markdown("## Cloud Infrastructure Health Dashboard")

            refresh_summary_btn = gr.Button("Refresh Summary", variant="primary")

            with gr.Row():
                with gr.Column():
                    total_instances = gr.Textbox(label="Total Instances")
                    running_instances = gr.Textbox(label="Running Instances")
                    idle_instances_count = gr.Textbox(label="Idle Instances")
                    error_instances = gr.Textbox(label="Error Instances")

                with gr.Column():
                    health_score = gr.Textbox(label="Health Score")
                    avg_cpu_usage = gr.Textbox(label="Average CPU Usage")
                    avg_memory_usage = gr.Textbox(label="Average Memory Usage")
                    total_daily_cost = gr.Textbox(label="Total Daily Cost")

            regions_list = gr.Textbox(label="Active Regions")
            services_list = gr.Textbox(label="Active Services")

            health_issues = gr.JSON(label="Health Issues")
            recommendations = gr.JSON(label="Recommendations")

            refresh_summary_btn.click(
                self.get_infrastructure_summary,
                outputs=[total_instances, running_instances, idle_instances_count, error_instances,
                        health_score, avg_cpu_usage, avg_memory_usage, total_daily_cost,
                        regions_list, services_list, health_issues, recommendations]
            )

    def get_idle_instances(self):
        """Get idle instances data"""
        idle_instances = self.data_generator.get_idle_instances()

        if not idle_instances:
            return pd.DataFrame(), "No idle instances found"

        data = []
        total_savings = 0

        for instance in idle_instances:
            monthly_savings = instance.cost_per_hour * 24 * 30
            total_savings += monthly_savings

            data.append([
                instance.instance_id,
                instance.name,
                instance.service_type.value,
                f"{instance.cpu_usage:.1f}%",
                f"{instance.memory_usage:.1f}%",
                f"${instance.cost_per_hour:.2f}",
                instance.region,
                f"${monthly_savings:.2f}"
            ])

        df = pd.DataFrame(data, columns=[
            "Instance ID", "Name", "Type", "CPU %", "Memory %", "Cost/Hr", "Region", "Monthly Savings"
        ])

        return df, f"${total_savings:.2f}"

    def get_billing_forecast(self, days):
        """Get billing forecast data"""
        forecast = self.data_generator.get_billing_forecast(days)

        return (
            f"${forecast['current_daily_cost']:.2f}",
            f"${forecast['projected_monthly_cost']:.2f}",
            f"${forecast['potential_savings']:.2f}",
            str(forecast['breakdown']['running_instances']),
            str(forecast['breakdown']['idle_instances']),
            str(forecast['breakdown']['error_instances']),
            forecast.get('recommendations', [])
        )

    def get_service_metrics(self, service_id, hours):
        """Get service metrics data"""
        metrics = self.data_generator.generate_metrics(service_id, hours)

        if not metrics:
            return "Service not found", "", "", "", "", "", "", "", "", "", {}

        cpu_values = [m.cpu_usage for m in metrics]
        memory_values = [m.memory_usage for m in metrics]
        response_times = [m.response_time for m in metrics]
        request_rates = [m.request_rate for m in metrics]

        latest = metrics[-1]

        return (
            f"{sum(cpu_values)/len(cpu_values):.1f}%",
            f"{max(cpu_values):.1f}%",
            f"{latest.cpu_usage:.1f}%",
            f"{sum(memory_values)/len(memory_values):.1f}%",
            f"{max(memory_values):.1f}%",
            f"{latest.memory_usage:.1f}%",
            f"{sum(response_times)/len(response_times):.1f}",
            f"{sum(request_rates)/len(request_rates):.1f}",
            f"{latest.response_time:.1f}",
            f"{latest.request_rate:.1f}",
            {
                "timestamp": latest.timestamp.isoformat(),
                "cpu_usage": latest.cpu_usage,
                "memory_usage": latest.memory_usage,
                "request_rate": latest.request_rate,
                "error_rate": latest.error_rate,
                "response_time": latest.response_time
            }
        )

    def detect_anomalies(self, service_id):
        """Detect anomalies in service"""
        metrics = self.data_generator.generate_metrics(service_id, 24)

        if not metrics:
            return "Service not found", "0", "0%", "0%", {}, {}

        cpu_values = [m.cpu_usage for m in metrics]
        memory_values = [m.memory_usage for m in metrics]
        error_rates = [m.error_rate for m in metrics]

        avg_cpu = sum(cpu_values) / len(cpu_values)
        avg_memory = sum(memory_values) / len(memory_values)
        avg_error_rate = sum(error_rates) / len(error_rates)

        current_cpu = cpu_values[-1]
        current_memory = memory_values[-1]
        current_error_rate = error_rates[-1]

        # Simple anomaly detection
        anomalies = []
        risk_level = "low"

        if current_cpu > avg_cpu * 2:
            risk_level = "high"
        elif current_cpu > avg_cpu * 1.5:
            risk_level = "medium"

        if current_memory > avg_memory * 1.5:
            risk_level = "high"

        if current_error_rate > avg_error_rate * 3:
            risk_level = "high"

        if current_cpu < 5:
            anomalies.append({
                "type": "low_utilization",
                "severity": "low",
                "description": f"CPU usage {current_cpu:.1f}% is very low"
            })

        return (
            risk_level,
            str(len(anomalies)),
            f"{avg_cpu:.1f}%",
            f"{current_cpu:.1f}%",
            anomalies,
            {
                "baseline_cpu": avg_cpu,
                "current_cpu": current_cpu,
                "baseline_memory": avg_memory,
                "current_memory": current_memory,
                "baseline_error_rate": avg_error_rate,
                "current_error_rate": current_error_rate
            }
        )

    def restart_service(self, service_id):
        """Restart a service"""
        instances = self.data_generator.get_all_instances()
        instance = next((i for i in instances if i.instance_id == service_id), None)

        if not instance:
            return "Service not found", {}, "0 minutes"

        # Simulate restart
        instance.status = "running"
        instance.last_restart = pd.Timestamp.now()

        downtime_minutes = round(2.5, 1)  # Simulated downtime

        return (
            "Successfully restarted",
            {
                "service_id": instance.instance_id,
                "name": instance.name,
                "type": instance.service_type.value,
                "region": instance.region,
                "status": instance.status
            },
            f"{downtime_minutes} minutes"
        )

    def get_infrastructure_summary(self):
        """Get infrastructure summary"""
        summary = self.data_generator.get_service_summary()

        # Calculate health score
        health_score = 100
        if summary["error_instances"] > 0:
            health_score -= summary["error_instances"] * 10
        if summary["idle_instances"] > 0:
            health_score -= summary["idle_instances"] * 5
        if summary["average_cpu_usage"] > 80:
            health_score -= 10
        if summary["average_memory_usage"] > 85:
            health_score -= 10

        health_score = max(0, health_score)

        return (
            str(summary["total_instances"]),
            str(summary["running_instances"]),
            str(summary["idle_instances"]),
            str(summary["error_instances"]),
            str(health_score),
            f"{summary['average_cpu_usage']:.1f}%",
            f"{summary['average_memory_usage']:.1f}%",
            f"${summary['total_daily_cost']:.2f}",
            ", ".join(summary["regions"]),
            ", ".join(summary["services"]),
            summary.get("health_analysis", {}).get("issues", []),
            summary.get("health_analysis", {}).get("recommendations", [])
        )

    def create_ui(self):
        """Create the complete Gradio UI"""
        with gr.Blocks(title="Cloud Ops Sentinel") as app:
            self._build_ui_content(app)
        return app

    def _build_ui_content(self, app):
        """Build the UI content inside the Blocks context"""
        gr.Markdown("""
        # ☁️ Cloud Ops Sentinel

        **Cloud Infrastructure Monitoring & Management Platform**

        ---

        Monitor your cloud infrastructure, detect anomalies, optimize costs, and manage services all in one place.
        """)

        self.create_idle_instances_tab()
        self.create_billing_forecast_tab()
        self.create_metrics_tab()
        self.create_anomaly_detection_tab()
        self.create_service_control_tab()
        self.create_infrastructure_summary_tab()

        gr.Markdown("""
        ---

        **Powered by:** Modal • Hyperbolic • Blaxel • Hugging Face • SambaNova • LangChain

        Built for the Cloud Ops Sentinel hackathon - MVP version with simulated data
        """)


def main():
    """Main entry point for the Gradio app"""
    ui = CloudOpsUI()
    app = ui.create_ui()

    # Launch the app
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True,
        quiet=False
    )


if __name__ == "__main__":
    main()