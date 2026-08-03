"""Auto-discovery helper for 9router and OpenAI-compatible API gateways."""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from strix.config.settings import Settings

logger = logging.getLogger(__name__)


def fetch_router_models(
    api_base: str, api_key: str | None = None, timeout: float = 5.0
) -> list[str]:
    """Fetch model IDs from a 9router or OpenAI-compatible /v1/models endpoint."""
    if not api_base:
        return []

    base_url = api_base.rstrip("/")
    urls_to_try = [f"{base_url}/models"]
    if not base_url.endswith("/v1"):
        urls_to_try.append(f"{base_url}/v1/models")

    for url in urls_to_try:
        try:
            req = urllib.request.Request(url)
            if api_key:
                req.add_header("Authorization", f"Bearer {api_key}")
            req.add_header("User-Agent", "Strix/1.4.1")

            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    data: dict[str, Any] = json.loads(response.read().decode("utf-8"))
                    models_list = data.get("data", [])
                    if isinstance(models_list, list):
                        ids = [
                            item.get("id")
                            for item in models_list
                            if isinstance(item, dict) and item.get("id")
                        ]
                        if ids:
                            logger.info("Successfully discovered %d models from %url", len(ids), url)
                            return ids
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            logger.debug("Failed to fetch models from %s: %s", url, exc)
            continue

    return []


def select_best_model(models: list[str]) -> str | None:
    """Select the best default model from a list of discovered model IDs based on capability priority."""
    if not models:
        return None

    # Priority rules for model selection (prefer non-throttled ag/ models over free-tier gh/ models)
    priority_keywords = [
        "claude-opus",
        "claude-sonnet",
        "gemini-3",
        "gemini-pro",
        "gpt-4o",
        "gpt-4.1",
        "gpt-5",
        "claude-haiku",
        "gpt-4",
        "deepseek",
        "qwen",
    ]

    # Skip mini/micro/dated-utility models in first choice if larger clean models are available
    for kw in priority_keywords:
        for model in models:
            model_lower = model.lower()
            if (
                kw in model_lower
                and "mini" not in model_lower
                and "micro" not in model_lower
                and "-2024" not in model_lower
            ):
                return model

    # Second pass: allow mini models
    for kw in priority_keywords:
        for model in models:
            if kw in model.lower():
                return model

    return models[0]


def auto_discover_and_select_model(settings: Settings) -> str | None:
    """If STRIX_LLM is not set, auto-discover models from LLM_API_BASE and select the best one."""
    llm = settings.llm
    if not llm.api_base:
        return llm.model

    discovered_ids = fetch_router_models(llm.api_base, llm.api_key)
    if not discovered_ids:
        return llm.model

    # If STRIX_LLM is not set or empty, select the best model automatically
    if not llm.model:
        best_id = select_best_model(discovered_ids)
        if best_id:
            # All discovered models go through the OpenAI-compatible proxy at
            # LLM_API_BASE.  The SDK's OpenAI Chat Completions client strips the
            # "openai/" prefix and sends the remainder as the `model` field, so
            # "openai/gh/gpt-4o-..." sends model="gh/gpt-4o-..." to the proxy,
            # which is exactly what it advertised.
            formatted_model = best_id if best_id.startswith("openai/") else f"openai/{best_id}"
            llm.model = formatted_model
            os.environ["STRIX_LLM"] = formatted_model
            logger.info("Auto-selected model '%s' from 9router (%s)", formatted_model, llm.api_base)
            print(f"\n✨ [9router] Auto-discovered {len(discovered_ids)} models. Selected: {formatted_model}\n")
            return formatted_model

    return llm.model
