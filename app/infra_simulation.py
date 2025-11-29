import random
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

# Add parent directory to path for imports when running as script
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Import models - handle both module and script execution
try:
    from .models import Instance, Service, MetricPoint, InfraSummary
except ImportError:
    from app.models import Instance, Service, MetricPoint, InfraSummary


# Cost per hour by instance type (simulated)
INSTANCE_COSTS = {
    "frontend": 0.15,
    "api": 0.25,
    "database": 0.45,
    "cache": 0.12,
    "worker": 0.08,
}


def generate_fake_infra() -> Tuple[List[Instance], List[Service]]:
    """Generate fake infrastructure with realistic patterns for demo."""
    instances = []
    services = []

    instance_configs = [
        ("web-server-1", ["us-east-1"], {"env": "prod", "tier": "frontend"}),
        ("web-server-2", ["us-east-1"], {"env": "prod", "tier": "frontend"}),
        ("api-server-1", ["us-west-2"], {"env": "prod", "tier": "api"}),
        ("api-server-2", ["us-west-2"], {"env": "prod", "tier": "api"}),
        ("db-server-1", ["us-east-1"], {"env": "prod", "tier": "database"}),
        ("db-replica-1", ["eu-west-1"], {"env": "prod", "tier": "database"}),
        ("cache-server-1", ["us-east-1"], {"env": "prod", "tier": "cache"}),
        ("worker-1", ["eu-west-1"], {"env": "staging", "tier": "worker"}),
        ("worker-2", ["ap-southeast-1"], {"env": "dev", "tier": "worker"}),
        ("analytics-1", ["us-east-1"], {"env": "prod", "tier": "worker"}),
    ]

    for name, regions, tags in instance_configs:
        tier = tags.get("tier", "worker")
        env = tags.get("env", "prod")
        
        # Determine instance behavior based on environment and tier
        if env in ["staging", "dev"] or "worker" in name:
            # Idle instances: very low CPU/memory, no recent requests
            cpu_usage = [random.uniform(0.1, 3.0) for _ in range(24)]
            ram_usage = [random.uniform(5, 12) for _ in range(24)]
            last_request = datetime.now() - timedelta(hours=random.randint(25, 168))
            network_activity = random.uniform(0.01, 0.5)
            idle_state = True
        elif "db" in name:
            # Database instances: moderate steady usage
            cpu_usage = [random.uniform(20, 50) for _ in range(24)]
            ram_usage = [random.uniform(60, 85) for _ in range(24)]
            last_request = datetime.now() - timedelta(minutes=random.randint(1, 30))
            network_activity = random.uniform(5, 20)
            idle_state = False
        else:
            # Active instances: variable usage patterns
            cpu_usage = [random.uniform(15, 75) for _ in range(24)]
            ram_usage = [random.uniform(30, 70) for _ in range(24)]
            last_request = datetime.now() - timedelta(minutes=random.randint(1, 60))
            network_activity = random.uniform(10, 100)
            idle_state = False

        instance = Instance(
            instance_id=f"inst_{name}",
            cpu_usage=cpu_usage,
            ram_usage=ram_usage,
            last_request=last_request,
            tags={"name": name, "region": regions[0], **tags},
            idle_state=idle_state,
            network_activity=network_activity
        )
        instances.append(instance)

    # Generate services mapped to instances
    service_configs = [
        ("svc_web", instances[0].instance_id, "web-frontend", "healthy", 98.5),
        ("svc_web_alt", instances[1].instance_id, "web-frontend-alt", "healthy", 97.2),
        ("svc_api", instances[2].instance_id, "api-gateway", "degraded", 72.0),
        ("svc_api_2", instances[3].instance_id, "api-service", "healthy", 95.0),
        ("svc_db", instances[4].instance_id, "primary-database", "healthy", 99.1),
        ("svc_db_replica", instances[5].instance_id, "db-replica", "healthy", 98.8),
        ("svc_cache", instances[6].instance_id, "redis-cache", "healthy", 99.5),
        ("svc_worker", instances[7].instance_id, "background-worker", "stopped", 0.0),
        ("svc_worker_dev", instances[8].instance_id, "dev-worker", "stopped", 0.0),
        ("svc_analytics", instances[9].instance_id, "analytics-engine", "healthy", 88.0),
    ]

    for service_id, instance_id, name, status, health_score in service_configs:
        service = Service(
            service_id=service_id,
            instance_id=instance_id,
            name=name,
            status=status,
            last_restart=datetime.now() - timedelta(hours=random.randint(1, 168)),
            health_score=health_score
        )
        services.append(service)

    return instances, services


def generate_fake_metrics(service_id: str, hours: int = 24) -> List[MetricPoint]:
    """Generate realistic time-series metrics for a service."""
    metrics = []
    base_time = datetime.now() - timedelta(hours=hours)

    # Determine service behavior pattern
    is_api = "api" in service_id.lower()
    is_db = "db" in service_id.lower()
    is_worker = "worker" in service_id.lower()

    for hour in range(hours + 1):
        timestamp = base_time + timedelta(hours=hour)
        
        # Time-based patterns (higher load during business hours)
        hour_of_day = timestamp.hour
        is_peak = 9 <= hour_of_day <= 17
        load_multiplier = 1.5 if is_peak else 0.7

        if is_worker:
            cpu = random.uniform(1, 5)
            ram = random.uniform(5, 15)
            latency_ms = random.uniform(50, 200)
            error_rate = random.uniform(0, 0.02)
        elif is_db:
            cpu = random.uniform(25, 55) * load_multiplier
            ram = random.uniform(60, 85)
            latency_ms = random.uniform(5, 50)
            error_rate = random.uniform(0, 0.01)
        elif is_api:
            cpu = random.uniform(20, 70) * load_multiplier
            ram = random.uniform(40, 75)
            latency_ms = random.uniform(50, 300) * load_multiplier
            error_rate = random.uniform(0.01, 0.08)
        else:
            cpu = random.uniform(15, 60) * load_multiplier
            ram = random.uniform(30, 65)
            latency_ms = random.uniform(100, 400)
            error_rate = random.uniform(0, 0.05)

        # Clamp values
        cpu = min(100, max(0, cpu))
        ram = min(100, max(0, ram))

        metric_point = MetricPoint(
            timestamp=timestamp,
            cpu=round(cpu, 2),
            ram=round(ram, 2),
            latency_ms=round(latency_ms, 2),
            error_rate=round(error_rate, 4),
            network_in=round(random.uniform(1, 50), 2),
            network_out=round(random.uniform(0.5, 30), 2)
        )
        metrics.append(metric_point)

    return metrics


def compute_idle_instances(instances: List[Instance]) -> List[Instance]:
    """Identify idle instances based on CPU, RAM, and network activity."""
    idle_instances = []
    N_HOURS = 24  # threshold hours

    for instance in instances:
        avg_cpu = sum(instance.cpu_usage) / len(instance.cpu_usage) if instance.cpu_usage else 0
        avg_ram = sum(instance.ram_usage) / len(instance.ram_usage) if instance.ram_usage else 0
        hours_since_request = (datetime.now() - instance.last_request).total_seconds() / 3600
        network = instance.network_activity or 0

        # Idle criteria: low CPU (<5%), low memory (<20%), low network (<1), no recent requests (>24h)
        if avg_cpu < 5.0 and avg_ram < 20.0 and network < 1.0 and hours_since_request > N_HOURS:
            instance.idle_state = True
            idle_instances.append(instance)

    return idle_instances


def compute_infra_summary(instances: List[Instance], services: List[Service]) -> InfraSummary:
    """Compute overall infrastructure summary."""
    running = [i for i in instances if not i.idle_state]
    idle = [i for i in instances if i.idle_state]
    error_instances = [i for i in instances if any(
        s.status in ["error", "degraded"] for s in services if s.instance_id == i.instance_id
    )]
    
    healthy_services = [s for s in services if s.status == "healthy"]
    degraded_services = [s for s in services if s.status in ["degraded", "error", "stopped"]]
    
    # Calculate costs
    total_daily_cost = 0.0
    for inst in instances:
        tier = inst.tags.get("tier", "worker")
        hourly_cost = INSTANCE_COSTS.get(tier, 0.10)
        total_daily_cost += hourly_cost * 24
    
    # Calculate health score
    if services:
        health_score = sum(s.health_score or 0 for s in services) / len(services)
    else:
        health_score = 100.0
    
    regions = list(set(inst.tags.get("region", "unknown") for inst in instances))
    
    return InfraSummary(
        total_instances=len(instances),
        running_instances=len(running),
        idle_instances=len(idle),
        error_instances=len(error_instances),
        total_services=len(services),
        healthy_services=len(healthy_services),
        degraded_services=len(degraded_services),
        total_daily_cost=round(total_daily_cost, 2),
        health_score=round(health_score, 1),
        regions=regions,
        last_updated=datetime.now()
    )


def estimate_monthly_cost(instances: List[Instance], days: int = 30) -> Dict[str, Any]:
    """Estimate monthly cloud costs with breakdown."""
    cost_by_tier = {}
    cost_by_region = {}
    total_cost = 0.0
    
    for inst in instances:
        tier = inst.tags.get("tier", "worker")
        region = inst.tags.get("region", "unknown")
        hourly_cost = INSTANCE_COSTS.get(tier, 0.10)
        monthly_cost = hourly_cost * 24 * days
        
        cost_by_tier[tier] = cost_by_tier.get(tier, 0) + monthly_cost
        cost_by_region[region] = cost_by_region.get(region, 0) + monthly_cost
        total_cost += monthly_cost
    
    # Calculate potential savings from idle instances
    idle = compute_idle_instances(instances)
    potential_savings = 0.0
    for inst in idle:
        tier = inst.tags.get("tier", "worker")
        hourly_cost = INSTANCE_COSTS.get(tier, 0.10)
        potential_savings += hourly_cost * 24 * days
    
    return {
        "total_monthly_cost": round(total_cost, 2),
        "cost_by_tier": {k: round(v, 2) for k, v in cost_by_tier.items()},
        "cost_by_region": {k: round(v, 2) for k, v in cost_by_region.items()},
        "potential_savings": round(potential_savings, 2),
        "idle_instance_count": len(idle)
    }