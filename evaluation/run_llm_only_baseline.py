from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from app.services.groq_client import groq_json

LABELS = {"CURRENT", "STALE", "CONTRADICTED", "UNSUPPORTED", "CONFLICTING", "STABLE"}


async def main() -> None:
    benchmark = json.loads(Path("evaluation/benchmark.json").read_text())
    output = []
    for item in benchmark:
        started = time.perf_counter()
        result = await groq_json(
            "You are an LLM-only factuality baseline. Do not search the web and do not use external evidence. Using only your pretrained knowledge, classify the supplied claim as CURRENT, STALE, CONTRADICTED, UNSUPPORTED, CONFLICTING, or STABLE as of 2026-11-13. Return JSON with a single field verdict containing exactly one allowed label. Treat uncertainty as UNSUPPORTED. Do not infer conflicting sources without evidence.",
            item["claim"],
        )
        verdict = str(result.get("verdict", "")).upper()
        if verdict not in LABELS:
            raise ValueError(f"Baseline returned an invalid verdict for {item['id']}.")
        output.append({"id": item["id"], "verdict": verdict, "latency_ms": round((time.perf_counter() - started) * 1000, 2)})
    Path("evaluation/llm-only-predictions.json").write_text(json.dumps(output, indent=2) + "\n")
    print(f"Wrote {len(output)} LLM-only baseline predictions to evaluation/llm-only-predictions.json")
    print("Provider cost was not estimated; add a measured cost_usd field per record if available.")


if __name__ == "__main__":
    asyncio.run(main())
