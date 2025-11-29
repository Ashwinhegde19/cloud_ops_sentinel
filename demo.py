#!/usr/bin/env python3
"""
Cloud Ops Sentinel - Quick Demo Script

This script provides a simple command-line interface to test all MCP tools
without using the Gradio UI. Perfect for quick smoke tests and demonstrations.

Usage:
    python demo.py                    # Run all tests
    python demo.py --tool idle        # Test only idle instances
    python demo.py --tool forecast    # Test only billing forecast
    python demo.py --tool metrics     # Test only metrics & anomalies
    python demo.py --tool restart     # Test only restart service
    python demo.py --tool report      # Test only ops report
    python demo.py --all             # Run comprehensive test suite
"""

import argparse
import json
import sys
import os
from datetime import datetime

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import tool functions
try:
    from app.mcp_server import (
        tool_list_idle_instances,
        tool_get_billing_forecast,
        tool_get_metrics,
        tool_detect_anomaly,
        tool_restart_service,
        tool_summarize_infra
    )
except ImportError:
    # Fallback for direct execution
    from mcp_server import (
        tool_list_idle_instances,
        tool_get_billing_forecast,
        tool_get_metrics,
        tool_detect_anomaly,
        tool_restart_service,
        tool_summarize_infra
    )


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_idle_instances():
    """Test the list idle instances tool"""
    print("Testing: List Idle Instances")
    result = tool_list_idle_instances()

    instances = result.get("idle_instances", [])
    print(f"Found {len(instances)} idle instances:")

    for i, instance in enumerate(instances, 1):
        cpu_list = instance.get('cpu_usage', [])
        ram_list = instance.get('ram_usage', [])

        # Calculate averages for better display
        avg_cpu = sum(cpu_list) / len(cpu_list) if cpu_list else 0
        avg_ram = sum(ram_list) / len(ram_list) if ram_list else 0

        print(f"  {i}. {instance.get('instance_id', 'N/A')}")
        print(f"     Service: {instance.get('service_id', 'N/A')}")
        print(f"     CPU: {avg_cpu:.1f}% (avg of {len(cpu_list)} samples)")
        print(f"     Memory: {avg_ram:.1f}% (avg of {len(ram_list)} samples)")
        print(f"     Status: {instance.get('status', 'N/A')}")

    return len(instances) > 0


def test_billing_forecast():
    """Test the billing forecast tool"""
    print("Testing: Billing Forecast")
    month = datetime.now().strftime("%Y-%m")
    result = tool_get_billing_forecast(month)

    print(f"Month: {result.get('month', 'N/A')}")
    print(f"Predicted Cost: ${result.get('predicted_cost', 0):.2f}")
    print(f"Confidence: {result.get('confidence', 0):.2%}")

    return result.get('predicted_cost', 0) > 0


def test_metrics_and_anomalies(service_id="svc_web"):
    """Test metrics and anomaly detection"""
    print(f"Testing: Metrics & Anomaly Detection for {service_id}")

    # Get metrics
    metrics_result = tool_get_metrics(service_id)
    metrics = metrics_result.get("metrics", [])
    print(f"Retrieved {len(metrics)} metrics")

    # Detect anomalies
    anomaly_result = tool_detect_anomaly(service_id)
    is_anomaly = anomaly_result.get("is_anomaly", False)
    anomalies = anomaly_result.get("anomalies", [])

    print(f"Anomaly Detected: {is_anomaly}")
    print(f"Number of Anomalies: {len(anomalies)}")

    if anomalies:
        print("Anomaly Details:")
        for anomaly in anomalies:
            print(f"  - {anomaly}")

    return len(metrics) > 0


def test_restart_service(service_id="svc_web"):
    """Test service restart"""
    print(f"Testing: Restart Service {service_id}")
    result = tool_restart_service(service_id)

    status = result.get("status", "unknown")
    print(f"Restart Status: {status}")
    print(f"Service ID: {result.get('service_id', 'N/A')}")

    return status == "restarted"


def test_ops_report():
    """Test infrastructure summary and ops report"""
    print("Testing: Generate Ops Report")
    result = tool_summarize_infra()

    report = result.get("report", "")
    summary_data = result.get("summary_data", {})

    print(f"Report Length: {len(report)} characters")
    print(f"Summary Data Keys: {list(summary_data.keys())}")

    # Print first 200 characters of report
    print(f"Report Preview: {report[:200]}...")

    return len(report) > 0


def run_comprehensive_test():
    """Run all tests in sequence"""
    print_section("Cloud Ops Sentinel - Comprehensive Demo")
    print(f"Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        ("Idle Instances", test_idle_instances),
        ("Billing Forecast", test_billing_forecast),
        ("Metrics & Anomalies", test_metrics_and_anomalies),
        ("Restart Service", test_restart_service),
        ("Ops Report", test_ops_report)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            print_section(f"Running: {test_name}")
            success = test_func()
            results.append((test_name, success, None))
            print(f"✓ {test_name}: {'PASSED' if success else 'FAILED'}")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"✗ {test_name}: FAILED - {e}")

    # Summary
    print_section("Test Summary")
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for test_name, success, error in results:
        status = "PASS" if success else "FAIL"
        print(f"  {test_name}: {status}")
        if error:
            print(f"    Error: {error}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Cloud Ops Sentinel is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

    return passed == total


def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(description="Cloud Ops Sentinel Demo")
    parser.add_argument("--tool", choices=["idle", "forecast", "metrics", "restart", "report"],
                       help="Test specific tool")
    parser.add_argument("--service", default="svc_web", help="Service ID for tests")
    parser.add_argument("--all", action="store_true", help="Run comprehensive test suite")

    args = parser.parse_args()

    if args.all:
        return run_comprehensive_test()
    elif args.tool:
        tool_map = {
            "idle": test_idle_instances,
            "forecast": test_billing_forecast,
            "metrics": lambda: test_metrics_and_anomalies(args.service),
            "restart": lambda: test_restart_service(args.service),
            "report": test_ops_report
        }

        if args.tool in tool_map:
            print_section(f"Testing: {args.tool.title()}")
            success = tool_map[args.tool]()
            print(f"\nResult: {'PASSED' if success else 'FAILED'}")
        else:
            print(f"Unknown tool: {args.tool}")
            return False
    else:
        # Default: run comprehensive test
        return run_comprehensive_test()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)