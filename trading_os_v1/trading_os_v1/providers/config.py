from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderErrorClassification:
    disposition: str
    error_code: str
    retryable: bool
    terminal: bool


def normalize_provider_config(
    *,
    explicit: dict[str, Any],
    env_map: dict[str, str | tuple[str, ...]] | None = None,
    defaults: dict[str, Any] | None = None,
    required: tuple[str, ...] = (),
) -> dict[str, Any]:
    resolved = dict(explicit)

    for field_name, env_keys in (env_map or {}).items():
        value = resolved.get(field_name)
        if value not in (None, ""):
            continue
        keys = env_keys if isinstance(env_keys, tuple) else (env_keys,)
        for env_key in keys:
            env_value = os.getenv(env_key)
            if env_value not in (None, ""):
                resolved[field_name] = env_value
                break

    for field_name, default_value in (defaults or {}).items():
        if resolved.get(field_name) in (None, ""):
            resolved[field_name] = default_value

    for field_name in required:
        if resolved.get(field_name) in (None, ""):
            raise ValueError(f"missing required config value: {field_name}")

    return resolved


def classify_provider_error(
    *,
    http_status: int | None = None,
    error_code: str | None = None,
    message: str | None = None,
    payload: Any | None = None,
    error: Exception | None = None,
) -> ProviderErrorClassification:
    payload_text = ""
    if isinstance(payload, dict):
        payload_text = " ".join(str(payload.get(key) or "") for key in ("message", "error", "reason", "status", "code"))
    code_text = str(error_code or "").upper()
    status_text = str(http_status) if http_status is not None else ""
    error_text = str(type(error).__name__ if error is not None else "")
    combined = " ".join([code_text, status_text, str(message or ""), payload_text, error_text]).lower()

    terminal_tokens = ("auth", "unauthorized", "forbidden", "entitlement")
    retryable_tokens = ("timeout", "rate limit", "rate_limit", "server", "tempor", "unavailable")

    if http_status in {401, 403} or any(token in combined for token in terminal_tokens):
        return ProviderErrorClassification(
            disposition="terminal_auth",
            error_code="AUTH",
            retryable=False,
            terminal=True,
        )

    if http_status in {408, 409, 425, 429, 500, 502, 503, 504} or any(token in combined for token in retryable_tokens) or isinstance(error, TimeoutError):
        normalized_code = code_text or (status_text if status_text else "RETRYABLE")
        return ProviderErrorClassification(
            disposition="retryable",
            error_code=normalized_code,
            retryable=True,
            terminal=False,
        )

    normalized_code = code_text or (status_text if status_text else (error_text.upper() if error_text else "PROVIDER_ERROR"))
    return ProviderErrorClassification(
        disposition="provider_error",
        error_code=normalized_code,
        retryable=False,
        terminal=False,
    )