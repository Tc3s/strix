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


def check_model_health(
    api_base: str, api_key: str | None, model_id: str, timeout: float = 2.5
) -> bool:
    """Send a quick 1-token test request to verify if the model is responsive and has available quota."""
    if not api_base:
        return True
    try:
        clean_model = model_id.removeprefix("openai/")
        url = f"{api_base.rstrip('/')}/chat/completions"
        if not api_base.rstrip("/").endswith("/v1") and "/v1" not in url:
            url = f"{api_base.rstrip('/')}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": clean_model,
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 1,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        if e.code in (429, 403, 503):
            logger.warning(
                "Model '%s' failed health check (HTTP %d - Quota Exhausted/Throttled)",
                model_id,
                e.code,
            )
            return False
        return True
    except Exception as exc:
        logger.warning("Model '%s' health check timeout/error: %s", model_id, exc)
        return False


def select_best_model(
    models: list[str], api_base: str | None = None, api_key: str | None = None
) -> str | None:
    """Select the best healthy default model from a list of discovered model IDs based on capability priority."""
    if not models:
        return None

    # Priority rules for model selection (prefer active unthrottled models)
    priority_keywords = [
        "gemini-pro",
        "gpt-4.1",
        "gpt-4o",
        "gemini-3",
        "claude-opus",
        "claude-sonnet",
        "gpt-5",
        "claude-haiku",
        "gpt-4",
        "deepseek",
        "qwen",
    ]

    candidates: list[str] = []
    for kw in priority_keywords:
        for model in models:
            model_lower = model.lower()
            if (
                kw in model_lower
                and "mini" not in model_lower
                and "micro" not in model_lower
                and "-2024" not in model_lower
                and model not in candidates
            ):
                candidates.append(model)

    for m in models:
        if m not in candidates:
            candidates.append(m)

    if api_base:
        for candidate in candidates:
            if check_model_health(api_base, api_key, candidate):
                return candidate
        logger.warning("All candidate models failed health check, using first candidate as fallback.")

    return candidates[0] if candidates else models[0]


def auto_discover_and_select_model(settings: Settings) -> str | None:
    """Auto-discover models from LLM_API_BASE and select/verify the best healthy one."""
    llm = settings.llm
    if not llm.api_base:
        return llm.model

    discovered_ids = fetch_router_models(llm.api_base, llm.api_key)
    if not discovered_ids:
        return llm.model

    # If current llm.model is set, test its health. If it's quota-exhausted (429/timeout), trigger auto-fallback!
    if llm.model:
        if check_model_health(llm.api_base, llm.api_key, llm.model):
            return llm.model
        logger.warning("Configured model '%s' is quota-exhausted or hanging. Initiating auto-fallback...", llm.model)
        print(f"\n⚠️ [9router] Model '{llm.model}' is out of quota or hanging. Auto-switching to healthy candidate...\n")

    best_id = select_best_model(discovered_ids, api_base=llm.api_base, api_key=llm.api_key)
    if best_id:
        formatted_model = best_id if best_id.startswith("openai/") else f"openai/{best_id}"
        llm.model = formatted_model
        os.environ["STRIX_LLM"] = formatted_model
        logger.info("Auto-fallback selected healthy model '%s' from 9router (%s)", formatted_model, llm.api_base)
        print(f"✨ [9router] Active & healthy model selected: {formatted_model}\n")
        return formatted_model

    return llm.model
