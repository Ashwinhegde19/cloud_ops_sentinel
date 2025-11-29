---
inclusion: fileMatch
fileMatchPattern: "**/*test*.py"
---

# Testing Guidelines for Cloud Ops Sentinel

## Property-Based Testing with Hypothesis

### Test Annotation Format
```python
# **Feature: enterprise-cloud-ops, Property N: Property Name**
# **Validates: Requirements X.Y**
@given(...)
def test_property_name(...):
    ...
```

### Key Properties to Test
1. Idle Instance Classification - avg_cpu < 5%, avg_ram < 15%, network < 1, hours > 24
2. Cost Forecast Structure - month, predicted_cost > 0, 0 <= confidence <= 1
3. Metrics Time Series - at least 24 data points
4. Anomaly Severity - one of: none, low, medium, high, critical
5. Anomaly Thresholds - latency > 500ms OR error_rate > 0.1 triggers anomaly
6. Restart Result - via is one of: modal, blaxel, simulation
7. LLM Fallback - SambaNova → HuggingFace → Simulation

### Running Tests
```bash
source venv/bin/activate
pytest tests/ -v
pytest tests/ --hypothesis-show-statistics
```

## Unit Test Guidelines
- Test edge cases: empty inputs, boundary values
- Test error conditions
- Don't over-test - property tests cover many inputs
