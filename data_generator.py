"""
Simulated Cloud Infrastructure Data Generator
Generates realistic mock data for cloud services, instances, and metrics
"""

import random
import datetime
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ServiceType(Enum):
    WEB_SERVER = "web_server"
    DATABASE = "database"
    API_GATEWAY = "api_gateway"
    CACHE = "cache"
    QUEUE = "queue"
    STORAGE = "storage"


@dataclass
class CloudInstance:
    instance_id: str
    name: str
    service_type: ServiceType
    status: str  # "running", "stopped", "idle", "error"
    cpu_usage: float
    memory_usage: float
    cost_per_hour: float
    region: str
    uptime_hours: float
    last_restart: datetime.datetime
    created_at: datetime.datetime


@dataclass
class ServiceMetrics:
    service_id: str
    timestamp: datetime.datetime
    cpu_usage: float
    memory_usage: float
    network_in: float
    network_out: float
    disk_io: float
    request_rate: float
    error_rate: float
    response_time: float


class CloudDataGenerator:
    def __init__(self):
        self.regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
        self.service_names = [
            "frontend-app", "auth-service", "payment-api", "user-db",
            "session-cache", "notification-queue", "file-storage",
            "analytics-engine", "search-service", "chat-backend"
        ]
        self.instances = []
        self.metrics = []
        self._generate_instances()

    def _generate_instances(self):
        """Generate mock cloud instances"""
        for i, name in enumerate(self.service_names):
            service_type = ServiceType(random.choice([
                ServiceType.WEB_SERVER, ServiceType.DATABASE,
                ServiceType.API_GATEWAY, ServiceType.CACHE,
                ServiceType.QUEUE, ServiceType.STORAGE
            ]))

            status = random.choice(["running", "idle", "stopped", "error"])
            cost_per_hour = random.uniform(0.10, 2.50)

            instance = CloudInstance(
                instance_id=f"i-{random.randint(100000, 999999)}",
                name=name,
                service_type=service_type,
                status=status,
                cpu_usage=random.uniform(5.0, 95.0) if status == "running" else 0.0,
                memory_usage=random.uniform(10.0, 80.0) if status == "running" else 0.0,
                cost_per_hour=cost_per_hour,
                region=random.choice(self.regions),
                uptime_hours=random.uniform(1, 720),  # Up to 30 days
                last_restart=datetime.datetime.now() - datetime.timedelta(
                    hours=random.randint(1, 168)
                ),
                created_at=datetime.datetime.now() - datetime.timedelta(
                    days=random.randint(1, 365)
                )
            )
            self.instances.append(instance)

    def generate_metrics(self, service_id: str, hours_back: int = 24) -> List[ServiceMetrics]:
        """Generate historical metrics for a service"""
        metrics = []
        base_time = datetime.datetime.now() - datetime.timedelta(hours=hours_back)

        # Find the instance
        instance = next((i for i in self.instances if i.instance_id == service_id), None)
        if not instance:
            return metrics

        for i in range(hours_back):
            timestamp = base_time + datetime.timedelta(hours=i)

            # Generate realistic metrics with some variance
            cpu_usage = max(0, min(100, instance.cpu_usage + random.uniform(-10, 10)))
            memory_usage = max(0, min(100, instance.memory_usage + random.uniform(-5, 5)))

            metrics.append(ServiceMetrics(
                service_id=service_id,
                timestamp=timestamp,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                network_in=random.uniform(0.1, 50.0),
                network_out=random.uniform(0.1, 30.0),
                disk_io=random.uniform(0, 100.0),
                request_rate=random.uniform(10, 1000) if instance.status == "running" else 0,
                error_rate=random.uniform(0, 5.0),
                response_time=random.uniform(50, 500) if instance.status == "running" else 0
            ))

        return metrics

    def get_all_instances(self) -> List[CloudInstance]:
        """Return all instances"""
        return self.instances

    def get_idle_instances(self) -> List[CloudInstance]:
        """Return instances with low CPU usage"""
        return [i for i in self.instances if i.cpu_usage < 10.0 and i.status == "running"]

    def get_billing_forecast(self, days: int = 30) -> Dict[str, Any]:
        """Generate billing forecast"""
        total_daily_cost = sum(i.cost_per_hour * 24 for i in self.instances if i.status == "running")

        forecast = {
            "current_daily_cost": round(total_daily_cost, 2),
            "current_monthly_cost": round(total_daily_cost * 30, 2),
            "projected_monthly_cost": round(total_daily_cost * days, 2),
            "potential_savings": round(random.uniform(100, 1000), 2),
            "breakdown": {
                "running_instances": len([i for i in self.instances if i.status == "running"]),
                "idle_instances": len(self.get_idle_instances()),
                "stopped_instances": len([i for i in self.instances if i.status == "stopped"]),
                "error_instances": len([i for i in self.instances if i.status == "error"])
            }
        }
        return forecast

    def get_service_summary(self) -> Dict[str, Any]:
        """Get overall infrastructure summary"""
        total_instances = len(self.instances)
        running_instances = len([i for i in self.instances if i.status == "running"])
        idle_instances = len(self.get_idle_instances())
        error_instances = len([i for i in self.instances if i.status == "error"])

        total_cost = sum(i.cost_per_hour * 24 for i in self.instances if i.status == "running")
        avg_cpu = sum(i.cpu_usage for i in self.instances if i.status == "running") / max(running_instances, 1)
        avg_memory = sum(i.memory_usage for i in self.instances if i.status == "running") / max(running_instances, 1)

        return {
            "total_instances": total_instances,
            "running_instances": running_instances,
            "idle_instances": idle_instances,
            "error_instances": error_instances,
            "total_daily_cost": round(total_cost, 2),
            "average_cpu_usage": round(avg_cpu, 2),
            "average_memory_usage": round(avg_memory, 2),
            "regions": list(set(i.region for i in self.instances)),
            "services": list(set(i.name for i in self.instances))
        }


# Global instance for the data generator
cloud_data = CloudDataGenerator()