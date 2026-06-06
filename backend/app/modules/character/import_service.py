from __future__ import annotations

import json
import logging
import time
from copy import deepcopy
from typing import Any

from openai import OpenAI
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError, BadRequestError
from app.core.logging import log_extra
from app.modules.character.constants import CharacterKind
from app.modules.character.import_defaults import (
    DND5E_CLASSES,
    default_attributes,
    default_equipment,
    default_extras,
    default_features,
    default_flavor,
    default_identity,
    default_spells,
)
from app.modules.character.import_prompt import (
    build_import_prompt,
    build_import_system_message,
)
from app.modules.character.schemas import CharacterCreate, CharacterImportPreviewResponse

logger = logging.getLogger("app.llm")


def _text_preview(text: str, limit: int = 400) -> str:
    compact = text.replace("\r\n", "\n")
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit]}… [truncated, total={len(text)} chars]"


def _llm_log(settings: Settings, event: str, message: str, **fields: Any) -> None:
    if not settings.llm_log_verbose:
        return
    logger.info(message, **log_extra(event, **fields))


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def call_llm(raw_text: str, settings: Settings) -> str:
    if not settings.llm_api_key:
        logger.warning(
            "LLM API key missing",
            **log_extra("llm.call.skipped", reason="llm_not_configured"),
        )
        raise AppError(
            "LLM API key is not configured. Set LLM_API_KEY or DASHSCOPE_API_KEY in .env",
            code="service_unavailable",
            status_code=503,
            reason="llm_not_configured",
        )

    prompt = build_import_prompt(raw_text)
    _llm_log(
        settings,
        "llm.call.start",
        "LLM request starting",
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        api_key_set=True,
        raw_text_chars=len(raw_text),
        raw_text_preview=_text_preview(raw_text),
        prompt_chars=len(prompt),
        prompt_preview=_text_preview(prompt, limit=600),
    )

    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    started = time.monotonic()
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": build_import_system_message()},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
    except Exception as exc:
        elapsed_ms = round((time.monotonic() - started) * 1000)
        logger.error(
            "LLM request failed",
            **log_extra(
                "llm.call.error",
                model=settings.llm_model,
                base_url=settings.llm_base_url,
                elapsed_ms=elapsed_ms,
                error_type=type(exc).__name__,
                error=str(exc),
            ),
        )
        raise

    elapsed_ms = round((time.monotonic() - started) * 1000)
    usage = getattr(response, "usage", None)
    content = response.choices[0].message.content
    finish_reason = response.choices[0].finish_reason

    _llm_log(
        settings,
        "llm.call.done",
        "LLM request completed",
        model=settings.llm_model,
        elapsed_ms=elapsed_ms,
        finish_reason=finish_reason,
        response_chars=len(content or ""),
        response_preview=_text_preview(content or "", limit=800),
        prompt_tokens=getattr(usage, "prompt_tokens", None),
        completion_tokens=getattr(usage, "completion_tokens", None),
        total_tokens=getattr(usage, "total_tokens", None),
    )

    if not content:
        logger.warning(
            "LLM returned empty content",
            **log_extra("llm.call.empty", model=settings.llm_model, elapsed_ms=elapsed_ms),
        )
        raise BadRequestError(
            "LLM returned empty response",
            reason="llm_empty_response",
        )
    return content


def _normalize_classes(classes: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in classes:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip().lower()
        if name not in DND5E_CLASSES:
            continue
        level = item.get("level", 1)
        try:
            level_int = max(1, min(20, int(level)))
        except (TypeError, ValueError):
            level_int = 1
        normalized.append(
            {
                "name": name,
                "level": level_int,
                "subclass": str(item.get("subclass") or ""),
            }
        )
    return normalized


def _clamp_ability_scores(scores: dict[str, Any]) -> dict[str, int]:
    keys = (
        "strength",
        "dexterity",
        "constitution",
        "intelligence",
        "wisdom",
        "charisma",
    )
    result: dict[str, int] = {}
    for key in keys:
        raw = scores.get(key, 10)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = 10
        result[key] = max(1, min(30, value))
    return result


def parse_and_normalize(
    raw_json: str,
    *,
    settings: Settings | None = None,
) -> CharacterImportPreviewResponse:
    active_settings = settings or get_settings()
    _llm_log(
        active_settings,
        "llm.parse.start",
        "Parsing LLM JSON response",
        response_chars=len(raw_json),
        response_preview=_text_preview(raw_json, limit=800),
    )

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        logger.warning(
            "Failed to parse LLM JSON",
            **log_extra(
                "llm.parse.invalid_json",
                error=str(exc),
                response_preview=_text_preview(raw_json, limit=400),
            ),
        )
        raise BadRequestError(
            "Failed to parse LLM JSON response",
            reason="llm_invalid_json",
            details={"error": str(exc)},
        ) from exc

    if not isinstance(data, dict):
        logger.warning(
            "LLM response is not a JSON object",
            **log_extra("llm.parse.invalid_shape", response_type=type(data).__name__),
        )
        raise BadRequestError(
            "LLM response must be a JSON object",
            reason="llm_invalid_shape",
        )

    identity_raw = data.get("identity")
    identity = _deep_merge(
        default_identity(),
        identity_raw if isinstance(identity_raw, dict) else {},
    )
    if isinstance(identity.get("classes"), list):
        identity["classes"] = _normalize_classes(identity["classes"])

    attributes_raw = data.get("attributes")
    attributes = _deep_merge(
        default_attributes(),
        attributes_raw if isinstance(attributes_raw, dict) else {},
    )
    if isinstance(attributes.get("ability_scores"), dict):
        attributes["ability_scores"] = _clamp_ability_scores(
            attributes["ability_scores"]
        )

    flavor = _deep_merge(default_flavor(), data.get("flavor") or {})
    features = _deep_merge(default_features(), data.get("features") or {})
    equipment = _deep_merge(default_equipment(), data.get("equipment") or {})
    extras = _deep_merge(default_extras(), data.get("extras") or {})

    spells = data.get("spells")
    if spells is not None:
        spells = _deep_merge(default_spells(), spells if isinstance(spells, dict) else {})

    name = str(data.get("name") or identity.get("name") or "").strip()
    if not name:
        name = "未命名角色"

    identity["name"] = str(identity.get("name") or name).strip() or name

    payload = {
        "name": name,
        "player_name": str(data.get("player_name") or ""),
        "kind": CharacterKind.PC_MAIN,
        "system": "dnd5e",
        "identity": identity,
        "flavor": flavor,
        "attributes": attributes,
        "features": features,
        "spells": spells,
        "equipment": equipment,
        "extras": extras,
        "state": data.get("state"),
    }

    try:
        validated = CharacterCreate.model_validate(payload)
    except ValidationError as exc:
        logger.warning(
            "LLM output failed schema validation",
            **log_extra(
                "llm.parse.schema_mismatch",
                character_name=name,
                error_count=len(exc.errors()),
            ),
        )
        raise BadRequestError(
            "LLM output does not match character schema",
            reason="llm_schema_mismatch",
            details={"errors": exc.errors()},
        ) from exc

    result = CharacterImportPreviewResponse.model_validate(validated.model_dump())
    classes = result.identity.get("classes") if isinstance(result.identity, dict) else []
    _llm_log(
        active_settings,
        "llm.parse.done",
        "LLM JSON normalized",
        character_name=result.name,
        player_name=result.player_name,
        class_count=len(classes) if isinstance(classes, list) else 0,
        has_spells=result.spells is not None,
        equipment_items=len(
            (result.equipment or {}).get("items", [])
            if isinstance(result.equipment, dict)
            else []
        ),
    )
    return result


def import_preview(raw_text: str, settings: Settings | None = None) -> CharacterImportPreviewResponse:
    active_settings = settings or get_settings()
    started = time.monotonic()
    _llm_log(
        active_settings,
        "llm.import.start",
        "Character import preview started",
        raw_text_chars=len(raw_text),
        raw_text_preview=_text_preview(raw_text),
    )

    try:
        raw_response = call_llm(raw_text, active_settings)
    except AppError:
        raise
    except Exception as exc:
        elapsed_ms = round((time.monotonic() - started) * 1000)
        logger.error(
            "Character import LLM call failed",
            **log_extra(
                "llm.import.error",
                elapsed_ms=elapsed_ms,
                error_type=type(exc).__name__,
                error=str(exc),
            ),
        )
        raise AppError(
            "LLM request failed",
            code="service_unavailable",
            status_code=503,
            reason="llm_request_failed",
            details={"error": str(exc)},
        ) from exc

    result = parse_and_normalize(raw_response, settings=active_settings)
    _llm_log(
        active_settings,
        "llm.import.done",
        "Character import preview completed",
        elapsed_ms=round((time.monotonic() - started) * 1000),
        character_name=result.name,
    )
    return result
