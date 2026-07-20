"""Centralized AI provider (OpenAI-compatible: Groq, SambaNova, or OpenAI).

The client is constructed exactly once here so every service shares identical,
correct configuration instead of duplicating the bootstrap. Everything degrades
gracefully: with no API key, ``get_client()`` is ``None`` and ``chat()`` returns
``None``, so callers fall back to deterministic logic and the app remains fully
functional offline / on free tiers.

Provider resolution:
  * ``OPENAI_API_KEY`` — a SambaNova UUID-style key OR an OpenAI ``sk-`` key.
  * ``AI_BASE_URL`` / ``AI_MODEL`` — optional explicit overrides (else sensible
    provider defaults are chosen automatically).
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from openai import OpenAI
from config import settings

logger = logging.getLogger("hiringbuddy.ai")

# --- Provider resolution -------------------------------------------------
# All supported providers are OpenAI-compatible; only base_url + model differ.
_PROVIDER_DEFAULTS = {
    "groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "sambanova": ("https://api.sambanova.ai/v1", "Meta-Llama-3.3-70B-Instruct"),
    "openai": (None, "gpt-4o-mini"),
}

_provider = (getattr(settings, "AI_PROVIDER", "") or "").strip().lower()

# Pick the API key for the configured provider (env-only; never hardcoded).
if _provider == "groq":
    _api_key = getattr(settings, "GROQ_API_KEY", "")
elif _provider in ("sambanova", "openai"):
    _api_key = getattr(settings, "OPENAI_API_KEY", "")
else:
    # Auto: prefer an explicit Groq key, then the legacy OPENAI/SambaNova key.
    _api_key = getattr(settings, "GROQ_API_KEY", "") or getattr(settings, "OPENAI_API_KEY", "")
_api_key = (_api_key or "").strip()

AI_ENABLED = bool(_api_key) and _api_key != "dummy-key"

# Infer the provider from the key shape when it wasn't set explicitly.
if not _provider:
    if _api_key.startswith("gsk_"):
        _provider = "groq"
    elif _api_key.startswith("sk-"):
        _provider = "openai"
    elif _api_key:
        _provider = "sambanova"
    else:
        _provider = "groq"

AI_PROVIDER = _provider
_default_base, _default_model = _PROVIDER_DEFAULTS.get(_provider, (None, "llama-3.3-70b-versatile"))

# Explicit env overrides win; otherwise use provider-appropriate defaults.
AI_BASE_URL: Optional[str] = (getattr(settings, "AI_BASE_URL", "") or "").strip() or _default_base
AI_MODEL: str = (getattr(settings, "AI_MODEL", "") or "").strip() or _default_model

_client: Optional[OpenAI] = None
if AI_ENABLED:
    try:
        _client = OpenAI(api_key=_api_key, base_url=AI_BASE_URL)
        logger.info("AI provider ready (%s · model=%s · base_url=%s)",
                    AI_PROVIDER, AI_MODEL, AI_BASE_URL or "openai-default")
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("AI client init failed; running deterministic offline-only: %s", e)
        _client = None
else:
    logger.info("AI disabled (no API key) — deterministic offline mode")


def get_client() -> Optional[OpenAI]:
    """Return the shared OpenAI-compatible client, or ``None`` when AI is disabled."""
    return _client


def chat(prompt: str, *, system: Optional[str] = None, temperature: float = 0.1,
         max_tokens: Optional[int] = None) -> Optional[str]:
    """Single-turn completion. Returns response text, or ``None`` on any failure.

    Never raises — every caller must have a deterministic fallback.
    """
    if _client is None:
        return None
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    kwargs = {"model": AI_MODEL, "messages": messages, "temperature": temperature}
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    try:
        resp = _client.chat.completions.create(**kwargs)
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.warning("AI chat call failed: %s", e)
        return None


def extract_json(text: Optional[str]):
    """Best-effort parse of a JSON object/array from a model response.

    Strips ```json code fences and falls back to the first ``{...}`` / ``[...]``
    block. Returns the parsed value, or ``None`` on failure.
    """
    if not text:
        return None
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?", "", t, flags=re.I).strip()
        if t.endswith("```"):
            t = t[:-3].strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    m = re.search(r"(\{.*\}|\[.*\])", t, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            return None
    return None
