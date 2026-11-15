"""Stage 1 record validation and an explicit, untrained recommendation baseline."""
from __future__ import annotations

import math
import re
from datetime import datetime
from statistics import median

LEVEL_NAMES = {1: "기초", 2: "보통", 3: "도전"}
BASE_SECONDS = {1: 40, 2: 35, 3: 30}
EXPERIENCE_LEVEL = {"new": 1, "sometimes": 2, "often": 3, "unspecified": 1}
N_QUESTIONS = 6


def initial_level(experience: str) -> int:
    return EXPERIENCE_LEVEL.get(experience, 1)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _number(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_record(record: dict) -> dict:
    """Whitelist exported data, reject inconsistent records, and recompute scores.

    Local JSON can be edited; these checks validate consistency, not authenticity.
    No names, phone numbers, free text, or arbitrary fields are retained.
    """
    _require(isinstance(record, dict), "JSON 최상위는 객체여야 합니다.")
    _require(record.get("schema_version") == "1.0", "지원하지 않는 기록 버전입니다.")
    _require(record.get("stage") == 1, "1라운드 기록만 분석할 수 있습니다.")
    out = {"schema_version": "1.0", "stage": 1}
    for key in ("participant_id", "round_id"):
        value = record.get(key)
        _require(isinstance(value, str) and re.fullmatch(r"[a-zA-Z0-9_-]{8,64}", value), f"{key}가 올바르지 않습니다.")
        out[key] = value
    stamp = record.get("completed_at")
    _require(isinstance(stamp, str) and len(stamp) < 40, "완료 시각이 올바르지 않습니다.")
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        _require(parsed.tzinfo is not None, "완료 시각에는 시간대가 필요합니다.")
    except (ValueError, TypeError):
        raise ValueError("완료 시각이 올바르지 않습니다.") from None
    out["completed_at"] = stamp
    _require(record.get("recording_consent") is True, "기록 이용 동의가 없는 파일입니다.")
    out["recording_consent"] = True
    profile = record.get("profile")
    _require(isinstance(profile, dict), "프로필이 없습니다.")
    enums = {
        "experience": set(EXPERIENCE_LEVEL),
        "age_group": {"unspecified", "under40", "40to64", "65plus"},
        "disability": {"unspecified", "yes", "no"},
    }
    clean_profile = {}
    for key, choices in enums.items():
        _require(profile.get(key) in choices, f"{key} 값이 올바르지 않습니다.")
        clean_profile[key] = profile[key]
    for key in ("extra_time", "large_text"):
        _require(type(profile.get(key)) is bool, f"{key}는 참 또는 거짓이어야 합니다.")
        clean_profile[key] = profile[key]
    _require(profile.get("demographic_consent") is True or
             (profile["age_group"] == "unspecified" and profile["disability"] == "unspecified"),
             "선택 정보 동의와 입력 내용이 일치하지 않습니다.")
    clean_profile["demographic_consent"] = profile.get("demographic_consent") is True
    out["profile"] = clean_profile
    level = record.get("initial_level")
    _require(type(level) is int and level == initial_level(profile["experience"]), "초기 수준이 게임 경험과 일치하지 않습니다.")
    out["initial_level"] = level
    retry = record.get("retry_count")
    _require(type(retry) is int and 0 <= retry <= 10000, "재도전 횟수가 올바르지 않습니다.")
    out["retry_count"] = retry
    rows = record.get("questions")
    _require(isinstance(rows, list) and len(rows) == N_QUESTIONS, "완료된 6문항 기록이 필요합니다.")
    limit = BASE_SECONDS[level] * (1.5 if profile["extra_time"] else 1)
    clean_rows = []
    for index, row in enumerate(rows, 1):
        _require(isinstance(row, dict) and row.get("question_index") == index, "문항 순서가 올바르지 않습니다.")
        _require(row.get("level") == level, "문항 수준이 일치하지 않습니다.")
        cycle = row.get("cycle")
        _require(isinstance(cycle, list) and len(cycle) in (2, 3) and
                 all(type(x) is int and 0 <= x <= 3 for x in cycle), "도형 규칙이 올바르지 않습니다.")
        if level == 1:
            valid = len(cycle) == 2 and len(set(cycle)) == 2
        elif level == 2:
            valid = len(cycle) == 3 and len(set(cycle)) == 3
        else:
            valid = len(cycle) == 3 and len(set(cycle)) == 2 and (cycle[0] == cycle[1] or cycle[1] == cycle[2])
        _require(valid, "난이도와 도형 규칙이 일치하지 않습니다.")
        sequence = row.get("sequence")
        _require(isinstance(sequence, list) and len(cycle) * 2 <= len(sequence) < len(cycle) * 3 and
                 all(type(x) is int for x in sequence) and
                 sequence == [cycle[i % len(cycle)] for i in range(len(sequence))], "문제 배열이 올바르지 않습니다.")
        choice = row.get("selected")
        outcome = row.get("outcome")
        _require(outcome in ("answer", "timeout", "skip"), "응답 유형이 올바르지 않습니다.")
        _require((outcome == "answer" and type(choice) is int and 0 <= choice <= 3) or
                 (outcome != "answer" and choice is None), "선택 값이 응답 유형과 일치하지 않습니다.")
        elapsed = row.get("response_ms")
        _require(_number(elapsed) and 0 <= elapsed <= limit * 1000, "응답 시간이 범위를 벗어났습니다.")
        _require(row.get("limit_ms") == limit * 1000, "제한 시간이 지원 설정과 일치하지 않습니다.")
        _require(outcome != "timeout" or elapsed == limit * 1000, "시간 초과 기록이 일치하지 않습니다.")
        _require(outcome != "answer" or elapsed < limit * 1000, "제한 시간을 지난 답변입니다.")
        _require(type(row.get("hint_used")) is bool, "힌트 사용 값이 올바르지 않습니다.")
        expected = cycle[len(sequence) % len(cycle)]
        correct = outcome == "answer" and choice == expected
        clean_rows.append({"question_index": index, "level": level, "cycle": cycle,
                           "sequence": sequence, "selected": choice, "correct_answer": expected,
                           "correct": correct, "outcome": outcome,
                           "response_ms": elapsed, "limit_ms": limit * 1000,
                           "hint_used": row["hint_used"]})
    out["questions"] = clean_rows
    return out


def summarize(record: dict) -> dict:
    record = validate_record(record)
    rows = record["questions"]
    correct = sum(q["correct"] for q in rows)
    return {
        "correct_count": correct, "accuracy": correct / N_QUESTIONS,
        "median_seconds": median(q["response_ms"] for q in rows) / 1000,
        "median_time_ratio": median(q["response_ms"] / q["limit_ms"] for q in rows),
        "hint_count": sum(q["hint_used"] for q in rows),
        "timeout_count": sum(q["outcome"] == "timeout" for q in rows),
        "skip_count": sum(q["outcome"] == "skip" for q in rows),
        "stage_success": correct >= 4,
    }


def recommend(record: dict) -> dict:
    record = validate_record(record)
    metrics = summarize(record)
    old = record["initial_level"]
    if metrics["accuracy"] < .5 or metrics["timeout_count"] >= 2:
        proposed = old - 1
        reason = "정답이 3개 미만이거나 시간 초과가 2회 이상이어서 한 단계 조정을 제안합니다."
    elif (metrics["correct_count"] >= 5 and metrics["median_time_ratio"] <= .6
          and metrics["hint_count"] <= 1):
        proposed = old + 1
        reason = "정답 5개 이상, 중앙 응답 시간 비율 60% 이하, 힌트 1회 이하를 충족했습니다."
    else:
        proposed = old
        reason = "상향·하향 기준에 해당하지 않아 현재 수준을 유지합니다."
    new = max(1, min(3, proposed))
    if new != proposed:
        reason += " 사용 가능한 난이도 범위의 경계이므로 현재 수준을 유지합니다."
    return {"method": "rule_baseline_v1", "is_trained_ai": False,
            "initial_level": old, "next_level": new, "reason": reason,
            "next_base_seconds": BASE_SECONDS[new],
            "next_seconds": BASE_SECONDS[new] * (1.5 if record["profile"]["extra_time"] else 1),
            "support_preserved": True, "metrics": metrics}
