from __future__ import annotations

import os
from urllib.parse import urlparse

import httpx
from pydantic import HttpUrl, TypeAdapter

from app.models.schemas import EvidenceSource

TAVILY_BASE = "https://api.tavily.com"
_URL = TypeAdapter(HttpUrl)


class TavilyError(RuntimeError):
    pass


async def search_claim(query: str, claim_id: str) -> list[EvidenceSource]:
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        raise TavilyError("Tavily is not configured. Add TAVILY_API_KEY in project settings.")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30, connect=10)) as client:
            response = await client.post(
                f"{TAVILY_BASE}/search",
                json={"api_key": key, "query": query, "search_depth": "advanced", "max_results": 3, "include_answer": False},
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            sources: list[EvidenceSource] = []
            for i, item in enumerate(results, start=1):
                raw_url = item.get("url")
                if not isinstance(raw_url, str) or not raw_url.startswith("https://"):
                    continue
                try:
                    url = _URL.validate_python(raw_url)
                except ValueError:
                    continue
                domain = urlparse(str(url)).netloc
                sources.append(EvidenceSource(
                    source_id=f"{claim_id}-S{i:02d}",
                    title=str(item.get("title") or domain)[:300],
                    url=url,
                    domain=domain,
                    excerpt=str(item.get("content") or "")[:2200],
                    relevance=max(0, min(1, float(item.get("score") or 0))),
                    published_date=item.get("published_date") or item.get("publishedDate"),
                    updated_date=item.get("updated_date") or item.get("updatedDate"),
                ))
            # Enrich the strongest available sources through Tavily Extract. Search snippets stay
            # available if Extract is unavailable; no guessed dates or URLs are added.
            extract_urls = [str(source.url) for source in sources[:1]]
            if extract_urls:
                try:
                    extracted = await client.post(
                        f"{TAVILY_BASE}/extract",
                        json={"api_key": key, "urls": extract_urls, "query": query},
                    )
                    if extracted.is_success:
                        by_url = {str(source.url): source for source in sources}
                        for item in extracted.json().get("results", []):
                            source = by_url.get(item.get("url"))
                            raw = item.get("raw_content") or item.get("content")
                            if source and isinstance(raw, str) and raw.strip():
                                source.excerpt = raw.strip()[:4200]
                except (httpx.HTTPError, ValueError):
                    pass
            return sources
    except httpx.HTTPStatusError as exc:
        raise TavilyError(f"Tavily returned HTTP {exc.response.status_code}; check the key, quota and search configuration.") from exc
    except httpx.HTTPError as exc:
        raise TavilyError(f"Tavily search failed: {type(exc).__name__}.") from exc
