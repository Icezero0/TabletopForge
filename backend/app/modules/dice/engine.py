from __future__ import annotations

import re
import secrets
from collections.abc import Callable
from dataclasses import dataclass


TERM_RE = re.compile(r"([+-]?)(?:(\d*)d(\d*)(?:k([hl])(\d+))?|(\d+))", re.IGNORECASE)
SUPPORTED_FORMULA_RE = re.compile(r"[0-9d+\-khl]+")
CHINESE_KEEP_RE = re.compile(r"(\d*)d(优势|劣势)(\d*)")
ROLL_REPEAT_RE = re.compile(r"^(?:r)?(?:(\d+)#)?(.+)$", re.IGNORECASE)


class DiceFormulaError(ValueError):
    pass


@dataclass(frozen=True)
class RollEval:
    formula: str
    total: int
    detail: dict


RandomInt = Callable[[int], int]


def _replace_chinese_keep(match: re.Match[str]) -> str:
    count_raw, keep_raw, faces_raw = match.group(1, 2, 3)
    base_count = int(count_raw or "1")
    roll_count = base_count * 2
    keep = "kh" if keep_raw == "优势" else "kl"
    faces = faces_raw or "20"
    return f"{roll_count}d{faces}{keep}{base_count}"


def normalize_formula(formula: str) -> str:
    normalized = re.sub(r"\s+", "", formula).lower()
    repeat_match = ROLL_REPEAT_RE.fullmatch(normalized)
    if repeat_match:
        repeat_raw, body = repeat_match.group(1, 2)
        if repeat_raw is not None and int(repeat_raw) < 1:
            raise DiceFormulaError("Dice formula is out of range")
        normalized = body
    return CHINESE_KEEP_RE.sub(_replace_chinese_keep, normalized)


def evaluate_formula(formula: str, *, random_int: RandomInt | None = None) -> RollEval:
    normalized = normalize_formula(formula)
    if not normalized:
        raise DiceFormulaError("Dice formula is empty")
    if not SUPPORTED_FORMULA_RE.fullmatch(normalized):
        raise DiceFormulaError("Unsupported dice formula")

    roll_int = random_int or (lambda faces: secrets.randbelow(faces) + 1)
    pos = 0
    total = 0
    terms = []
    for match in TERM_RE.finditer(normalized):
        if match.start() != pos:
            raise DiceFormulaError("Unsupported dice formula")
        pos = match.end()
        sign = -1 if match.group(1) == "-" else 1
        dice_count_raw, faces_raw, keep_kind, keep_count_raw, flat_raw = match.group(2, 3, 4, 5, 6)
        if flat_raw is not None:
            value = sign * int(flat_raw)
            total += value
            terms.append({"type": "modifier", "sign": sign, "value": int(flat_raw), "total": value})
            continue

        count = int(dice_count_raw or "1")
        faces = int(faces_raw or "20")
        keep_count = int(keep_count_raw) if keep_count_raw is not None else count
        if count < 1 or count > 100 or faces < 2 or faces > 1000 or keep_count < 1 or keep_count > count:
            raise DiceFormulaError("Dice formula is out of range")
        rolls = [roll_int(faces) for _ in range(count)]
        if any(value < 1 or value > faces for value in rolls):
            raise DiceFormulaError("Dice roller returned out-of-range value")

        kept_indexes = set(range(count))
        if keep_kind is not None:
            ordered = sorted(range(count), key=lambda idx: rolls[idx], reverse=keep_kind == "h")
            kept_indexes = set(ordered[:keep_count])
        dice = [
            {"value": value, "kept": index in kept_indexes}
            for index, value in enumerate(rolls)
        ]
        subtotal = sign * sum(rolls[index] for index in kept_indexes)
        total += subtotal
        terms.append({
            "type": "dice",
            "sign": sign,
            "count": count,
            "faces": faces,
            "keep": f"k{keep_kind}{keep_count}" if keep_kind is not None else None,
            "rolls": dice,
            "subtotal": subtotal,
        })

    if pos != len(normalized) or not terms:
        raise DiceFormulaError("Unsupported dice formula")

    return RollEval(formula=normalized, total=total, detail={"terms": terms})
