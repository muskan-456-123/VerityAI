from evaluate import score


def test_missing_predictions_count_as_misses_and_cost_stays_unknown():
    result = score(
        {"a": "CURRENT", "b": "STALE"},
        [{"id": "a", "verdict": "CURRENT", "latency_ms": 125}],
    )
    assert result["count"] == 2
    assert result["coverage"] == 0.5
    assert result["accuracy"] == 0.5
    assert result["average_latency_ms"] == 125.0
    assert result["average_cost_usd"] is None
    assert result["per_class"]["STALE"]["recall"] == 0.0
