from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

LABELS = ["CURRENT", "STALE", "CONTRADICTED", "UNSUPPORTED", "CONFLICTING", "STABLE"]


def score(gold: dict[str, str], records: list[dict[str, Any]]) -> dict[str, Any]:
    predictions = {item["id"]: item for item in records if item.get("id") in gold}
    evaluated = [(gold[key], predictions.get(key, {}).get("verdict")) for key in gold]
    if not evaluated:
        return {"count": 0, "coverage": 0.0, "accuracy": None, "macro_f1": None, "average_latency_ms": None, "average_cost_usd": None, "per_class": {}}
    correct = sum(actual == predicted for actual, predicted in evaluated)
    per_class = {}
    for label in LABELS:
        tp = sum(actual == label and predicted == label for actual, predicted in evaluated)
        fp = sum(actual != label and predicted == label for actual, predicted in evaluated)
        fn = sum(actual == label and predicted != label for actual, predicted in evaluated)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}
    used = [predictions[key] for key in gold if key in predictions]
    latencies = [float(item["latency_ms"]) for item in used if item.get("latency_ms") is not None]
    costs = [float(item["cost_usd"]) for item in used if item.get("cost_usd") is not None]
    return {
        "count": len(evaluated),
        "coverage": round(len(used) / len(gold), 4),
        "accuracy": round(correct / len(evaluated), 4),
        "macro_f1": round(mean(item["f1"] for item in per_class.values()), 4),
        "average_latency_ms": round(mean(latencies), 2) if latencies else None,
        "average_cost_usd": round(mean(costs), 6) if costs else None,
        "per_class": per_class,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Score Verity predictions against the labelled benchmark.")
    parser.add_argument("--predictions", required=True, help="JSON array with id, verdict, latency_ms and optional cost_usd")
    parser.add_argument("--baseline", help="Optional prediction JSON array for an LLM-only baseline")
    args = parser.parse_args()
    benchmark = json.loads(Path("evaluation/benchmark.json").read_text())
    gold = {item["id"]: item["expected_verdict"] for item in benchmark}
    predictions = json.loads(Path(args.predictions).read_text())
    output = {"verity": score(gold, predictions)}
    if args.baseline:
        output["baseline"] = score(gold, json.loads(Path(args.baseline).read_text()))
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
