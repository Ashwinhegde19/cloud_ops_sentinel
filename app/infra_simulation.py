import random
import sys
import os
from datetime import datetime, timedelta
from typing import List

# Add parent directory to path for imports when running as script
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Import models - handle both module and script execution
try:
    from .models import Instance, Service, MetricPoint
except ImportError:
    # Running as script - use absolute imports
    from app.models import Instance, Service, MetricPoint


def generate_fake_infra() -> tuple[List[Instance], List[Service]]:
    instances = []
    services = []

    # Generate fake instances
    instance_configs = [
        ("web-server-1", ["us-east-1"], {"env": "prod", "tier": "frontend"}),
        ("web-server-2", ["us-east-1"], {"env": "prod", "tier": "frontend"}),
        ("api-server-1", ["us-west-2"], {"env": "prod", "tier": "api"}),
        ("db-server-1", ["us-east-1"], {"env": "prod", "tier": "database"}),
        ("cache-server-1", ["us-east-1"], {"env": "prod", "tier": "cache"}),
        ("worker-1", ["eu-west-1"], {"env": "staging", "tier": "worker"}),
    ]

    for name, regions, tags in instance_configs:
        # Make some instances idle for demo purposes
        if "worker" in name or "staging" in tags.get("env", ""):
            # Idle instances: very low CPU/memory, no recent requests
            cpu_usage = [random.uniform(0.1, 2.0) for _ in range(24)]
            ram_usage = [random.uniform(5, 15) for _ in range(24)]
            last_request = datetime.now() - timedelta(hours=random.randint(25, 168))  # 1-7 days ago
        else:
            # Active instances: normal CPU/memory usage
            cpu_usage = [random.uniform(5, 80) for _ in range(24)]
            ram_usage = [random.uniform(10, 90) for _ in range(24)]
            last_request = datetime.now() - timedelta(hours=random.randint(1, 72))

        instance = Instance(
            instance_id=f"inst_{name}",
            cpu_usage=cpu_usage,
            ram_usage=ram_usage,
            last_request=last_request,
            tags={"name": name, "region": regions[0], **tags}
        )
        instances.append(instance)

    # Generate fake services
    service_configs = [
        ("svc_web", instances[0].instance_id, "web-service", "healthy"),
        ("svc_web_alt", instances[1].instance_id, "web-service-alt", "healthy"),
        ("svc_api", instances[2].instance_id, "api-service", "degraded"),
        ("svc_db", instances[3].instance_id, "database", "healthy"),
        ("svc_cache", instances[4].instance_id, "cache", "healthy"),
        ("svc_worker", instances[5].instance_id, "worker-service", "stopped"),
    ]

    for service_id, instance_id, name, status in service_configs:
        service = Service(
            service_id=service_id,
            instance_id=instance_id,
            name=name,
            status=status,
            last_restart=datetime.now() - timedelta(hours=random.randint(1, 168))
        )
        services.append(service)

    return instances, services


def generate_fake_metrics(service_id: str) -> List[MetricPoint]:
    metrics = []
    base_time = datetime.now() - timedelta(hours=24)

    for hour in range(25):
        timestamp = base_time + timedelta(hours=hour)

        # Generate realistic metrics with some variation
        cpu = random.uniform(5, 85)
        ram = random.uniform(15, 90)
        latency_ms = random.uniform(10, 500)
        error_rate = random.uniform(0, 0.1) if random.random() > 0.1 else random.uniform(0.1, 0.3)

        metric_point = MetricPoint(
            timestamp=timestamp,
            cpu=cpu,
            ram=ram,
            latency_ms=latency_ms,
            error_rate=error_rate
        )
        metrics.append(metric_point)

    return metrics


def compute_idle_instances(instances: List[Instance]) -> List[Instance]:
    idle_instances = []
    N_HOURS = 24  # threshold hours

    for instance in instances:
        avg_cpu = sum(instance.cpu_usage) / len(instance.cpu_usage) if instance.cpu_usage else 0
        avg_ram = sum(instance.ram_usage) / len(instance.ram_usage) if instance.ram_usage else 0
        hours_since_request = (datetime.now() - instance.last_request).total_seconds() / 3600

        # Check if instance is idle: low CPU (<5%), low memory (<15%), and no recent requests (>24h)
        if avg_cpu < 5.0 and avg_ram < 15.0 and hours_since_request > N_HOURS:
            idle_instances.append(instance)

    return idle_instances