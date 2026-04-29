"""
👖 BLUE JEANS WUXIA ENGINE v2.0 — engine_validator.py
═══════════════════════════════════════════════════════════
회차 자가 검수 · 재료 활용 검증 · 전환점 자동 감지

핵심 함수:
- validate_planning_to_writing_mapping() — 기획 재료가 본문에 반영됐는가
- compute_episode_validation_score()     — 5축 종합 점수
- detect_transition_episodes()            — 마음 흐름 단계 전환점 자동 감지
- generate_material_usage_report()        — 작가용 가시화 리포트
- get_validation_mode_for_episode()       — 회차별 검수 모드 결정
- summarize_cumulative_25()               — 25화 모니터링 누적 대시보드

5축 검수 (무협 가중치):
1. MATERIAL_USAGE        — 무공·문파 재료 활용 (30%)
2. CHARACTER_CONSISTENCY — 12종 인물 역할 차별화 (20%)
3. CLIFFHANGER_STRENGTH  — 9유형 클리프행어 적용 (15%)
4. MISE_EN_SCENE         — 무공 시전·전투 묘사 (20%) ⭐
5. MARKET_VIABILITY      — 시장 트리거 충족도 (15%)

원칙:
- 본 모듈은 LLM 호출 없이 텍스트 패턴 매칭으로 1차 검수 (빠름·무비용)
- 깊은 검수가 필요하면 prompt.py의 build_validation_prompt()로 LLM 호출
- 회차별 단독 점수 + 누적 점수 분리 제공

© 2026 BLUE JEANS PICTURES
"""

from typing import List, Dict, Optional, Tuple

# Wuxia Engine 데이터 모듈 import
try:
    from prompt import (
        WUXIA_FORMULAS,
        PROTAGONIST_TYPES,
        NARRATIVE_MOTIFS,
        WUXIA_CHARACTER_ROLES,
        WUXIA_HERO_MIND_FLOW,
        WUXIA_VALIDATION_WEIGHTS,
        WUXIA_MARKET_DATA,
        VALIDATION_THRESHOLDS,
        get_stage_for_episode,
        detect_transition_episodes as _detect_transitions_from_prompt,
        detect_wuxia_work_orientation,
    )
    _PROMPT_OK = True
except ImportError as e:
    print(f"[engine_validator] prompt.py import 실패: {e}")
    WUXIA_FORMULAS = {}
    PROTAGONIST_TYPES = {}
    NARRATIVE_MOTIFS = {}
    WUXIA_CHARACTER_ROLES = {}
    WUXIA_HERO_MIND_FLOW = {"stages": []}
    WUXIA_VALIDATION_WEIGHTS = {
        "MATERIAL_USAGE": 0.30,
        "CHARACTER_CONSISTENCY": 0.20,
        "CLIFFHANGER_STRENGTH": 0.15,
        "MISE_EN_SCENE": 0.20,
        "MARKET_VIABILITY": 0.15,
    }
    WUXIA_MARKET_DATA = {}
    VALIDATION_THRESHOLDS = {
        "episode_pass": 75,
        "episode_warn": 65,
        "episode_redo": 55,
        "cumulative_pass": 78,
    }
    _PROMPT_OK = False


# ============================================================================
# 검수 모드 정의
# ============================================================================
VALIDATION_MODES = {
    "auto_until_25": {
        "name": "1~25화 자동 + 26화부터 결정",
        "description": "초기 정착기는 자동 검수, 25화 모니터링 후 작가가 결정",
        "default": True,
    },
    "transition_only": {
        "name": "전환점 회차만 자동 검수",
        "description": "마음 흐름 단계가 바뀌는 회차만 자동, 나머지는 수동",
        "default": False,
    },
    "all_auto": {
        "name": "모든 회차 자동 검수",
        "description": "비용 부담 있으나 가장 안전",
        "default": False,
    },
    "all_manual": {
        "name": "수동 검수만",
        "description": "작가가 버튼을 누를 때만 검수 실행",
        "default": False,
    },
}


# ============================================================================
# 1. validate_planning_to_writing_mapping
# ============================================================================
def validate_planning_to_writing_mapping(
    concept: dict,
    character_bible,
    written_text: str,
    ep_number: int = 0,
    total_eps: int = 50,
) -> dict:
    """기획 재료가 본문에 반영됐는지 검증.

    Returns:
        {
            "used": [...],       # 활용된 재료
            "weak": [...],       # 약하게 활용된 재료
            "missing": [...],    # 누락된 재료
            "score": int,        # 0~100 점수
            "critical_missing": [...],  # 치명적 누락
        }
    """
    text_lower = written_text.lower()
    used = []
    weak = []
    missing = []
    critical_missing = []

    # === 1. 메인 공식 검증 ===
    formula_main = concept.get("wuxia_formula_main", concept.get("formula_main", ""))
    if formula_main and formula_main in WUXIA_FORMULAS:
        f = WUXIA_FORMULAS[formula_main]
        keywords = f.get("keywords", [])
        if keywords:
            hits = _count_keyword_partial_hits(keywords, text_lower)
            label = f.get("label", formula_main)
            if hits >= 2:
                used.append(f"메인 공식 [{label}] 키워드 {hits}개 활용")
            elif hits == 1:
                weak.append(f"메인 공식 [{label}] 키워드 1개만 활용 (3개 이상 권장)")
            else:
                missing.append(f"메인 공식 [{label}] 키워드 미활용")
                critical_missing.append(f"formula_main_{formula_main}")

    # === 2. 1차 모티프 검증 ===
    motifs_obj = concept.get("narrative_motifs", {})
    primary_motif = ""
    if isinstance(motifs_obj, dict):
        primary_motif = motifs_obj.get("primary", "")
    elif isinstance(motifs_obj, list) and motifs_obj:
        primary_motif = motifs_obj[0]

    if primary_motif and primary_motif in NARRATIVE_MOTIFS:
        motif_data = NARRATIVE_MOTIFS[primary_motif]
        # 한자 빼고 한글만 추출
        motif_korean = primary_motif.split("(")[0].strip()
        if motif_korean.lower() in text_lower:
            used.append(f"1차 모티프 [{primary_motif}] 직접 등장")
        else:
            # 의미적 활용 확인 (motif desc의 키워드)
            desc = motif_data.get("desc", "").lower()
            desc_keywords = [w for w in desc.split() if len(w) >= 2][:3]
            if any(kw in text_lower for kw in desc_keywords):
                weak.append(f"1차 모티프 [{primary_motif}] 의미적 활용만")
            else:
                missing.append(f"1차 모티프 [{primary_motif}] 누락")
                critical_missing.append(f"primary_motif_{primary_motif}")

    # === 3. 주인공 이름·정체성 ===
    protagonist = concept.get("protagonist", {})
    if isinstance(protagonist, dict):
        name = protagonist.get("name", "")
        if name and name in written_text:
            used.append(f"주인공 [{name}] 등장")
        elif name:
            missing.append(f"주인공 [{name}] 미등장")
            critical_missing.append("protagonist_absent")

    # === 4. 주인공 유형 특수 요소 ===
    p_type = concept.get("protagonist_type", "")
    if p_type and p_type in PROTAGONIST_TYPES:
        ptype_data = PROTAGONIST_TYPES[p_type]
        # 회귀자라면 "회귀·전생·과거" 같은 키워드
        if p_type == "회귀자":
            keys = ["회귀", "전생", "과거", "다시", "기억"]
            if any(k in text_lower for k in keys):
                used.append("회귀자 정체성 본문 반영")
            else:
                weak.append("회귀자 정체성이 본문에 약함")
        elif p_type == "전생자_이세계":
            keys = ["현대", "전생", "이세계", "지구", "21세기"]
            if any(k in text_lower for k in keys):
                used.append("이세계 전생자 정체성 본문 반영")
            else:
                weak.append("이세계 전생자 정체성이 본문에 약함")
        elif p_type == "시스템_보유자":
            keys = ["시스템", "상태창", "레벨", "퀘스트", "스킬"]
            if any(k in text_lower for k in keys):
                used.append("시스템 보유자 정체성 본문 반영")
            else:
                weak.append("시스템 정체성이 본문에 약함")

    # === 5. 캐릭터 바이블 — 조연 등장 ===
    cb_chars = _normalize_character_data(character_bible)
    char_appearances = 0
    for char in cb_chars:
        if not isinstance(char, dict):
            continue
        cname = char.get("name", char.get("이름", ""))
        if cname and cname in written_text:
            char_appearances += 1

    if char_appearances >= 2:
        used.append(f"캐릭터 바이블 인물 {char_appearances}명 등장")
    elif char_appearances == 1:
        weak.append("캐릭터 바이블 인물 1명만 등장 (다중 인물 권장)")
    else:
        missing.append("캐릭터 바이블 인물 미등장")

    # === 6. 마음 흐름 단계 키워드 ===
    if ep_number > 0:
        stage = get_stage_for_episode(ep_number, total_eps)
        if stage:
            inner_kws = stage.get("inner_state_keywords", [])
            inner_hits = sum(1 for kw in inner_kws if kw in text_lower)
            if inner_hits >= 2:
                used.append(f"단계 {stage['stage']} 내면 키워드 {inner_hits}개 활용")
            elif inner_hits == 0:
                weak.append(f"단계 {stage['stage']} 내면 상태가 본문에 미약함")

    # === 점수 계산 ===
    total_items = len(used) + len(weak) + len(missing)
    if total_items == 0:
        score = 0
    else:
        score = int((len(used) * 100 + len(weak) * 50) / total_items)

    return {
        "used": used,
        "weak": weak,
        "missing": missing,
        "score": score,
        "critical_missing": critical_missing,
    }


def _normalize_character_data(character_bible):
    """캐릭터 바이블을 일관된 list of dict 형태로 정규화."""
    if character_bible is None:
        return []
    if isinstance(character_bible, list):
        return character_bible
    if isinstance(character_bible, dict):
        # v2.6.4 형식: {"protagonist": {...}, "supporting_characters": [...]}
        flattened = []
        if "protagonist" in character_bible and isinstance(character_bible["protagonist"], dict):
            flattened.append(character_bible["protagonist"])
        if "supporting_characters" in character_bible:
            sc = character_bible["supporting_characters"]
            if isinstance(sc, list):
                flattened.extend([c for c in sc if isinstance(c, dict)])
        if "antagonist" in character_bible and isinstance(character_bible["antagonist"], dict):
            flattened.append(character_bible["antagonist"])
        # 평면화에 실패하면 원본을 단일 인물로 처리
        if not flattened:
            return [character_bible]
        return flattened
    return []


def _count_keyword_partial_hits(keywords: list, text: str) -> int:
    """키워드 부분 매칭 카운트.
    한자 병기 표현(예: '회귀(回歸)')은 한글 부분만 추출해 매칭."""
    if not keywords:
        return 0
    text_lower = text.lower() if text else ""
    hits = 0
    seen = set()
    for kw in keywords:
        if not kw or not isinstance(kw, str):
            continue
        # 한자·괄호 제거
        kw_clean = kw.split("(")[0].strip().lower()
        if kw_clean and kw_clean not in seen:
            if kw_clean in text_lower:
                hits += 1
                seen.add(kw_clean)
    return hits


# ============================================================================
# 2. compute_episode_validation_score — 5축 종합 점수
# ============================================================================
def compute_episode_validation_score(
    concept: dict,
    character_bible,
    written_text: str,
    ep_number: int = 0,
    total_eps: int = 50,
    cliffhanger_type: Optional[str] = None,
) -> dict:
    """5축 종합 점수.

    Returns:
        {
            "axes": {...},       # 각 축별 점수와 세부
            "overall": int,      # 가중 종합 점수
            "grade": str,        # A+ / A / B+ / B / C / D / F
            "verdict": str,      # PASS / WARN / REDO
        }
    """
    axes = {}

    # === 1. MATERIAL_USAGE ===
    material_result = validate_planning_to_writing_mapping(
        concept, character_bible, written_text, ep_number, total_eps,
    )
    axes["MATERIAL_USAGE"] = {
        "score": material_result["score"],
        "details": material_result,
    }

    # === 2. CHARACTER_CONSISTENCY ===
    char_score = _score_character_consistency(character_bible, written_text)
    axes["CHARACTER_CONSISTENCY"] = char_score

    # === 3. CLIFFHANGER_STRENGTH ===
    cliff_score = _score_cliffhanger_strength(written_text, cliffhanger_type)
    axes["CLIFFHANGER_STRENGTH"] = cliff_score

    # === 4. MISE_EN_SCENE ===
    mise_score = _score_mise_en_scene(written_text)
    axes["MISE_EN_SCENE"] = mise_score

    # === 5. MARKET_VIABILITY ===
    market_score = _score_market_viability_episode(concept, written_text, ep_number, total_eps)
    axes["MARKET_VIABILITY"] = market_score

    # === 종합 계산 ===
    weights = WUXIA_VALIDATION_WEIGHTS
    overall = 0.0
    for axis_name, axis_data in axes.items():
        score = axis_data.get("score", 0)
        weight = weights.get(axis_name, 0)
        overall += score * weight

    overall = int(round(overall))

    # 등급
    if overall >= 90:
        grade = "A+"
    elif overall >= 85:
        grade = "A"
    elif overall >= 80:
        grade = "B+"
    elif overall >= 75:
        grade = "B"
    elif overall >= 65:
        grade = "C"
    elif overall >= 55:
        grade = "D"
    else:
        grade = "F"

    # 판정
    if overall >= VALIDATION_THRESHOLDS["episode_pass"]:
        verdict_short = "PASS"
    elif overall >= VALIDATION_THRESHOLDS["episode_warn"]:
        verdict_short = "WARN"
    else:
        verdict_short = "REDO"

    verdict_full = _generate_verdict(grade, axes, overall)

    return {
        "axes": axes,
        "overall": overall,
        "grade": grade,
        "verdict": verdict_short,
        "verdict_text": verdict_full,
    }


def _score_character_consistency(character_bible, text: str) -> dict:
    """인물 일관성 검증."""
    chars = _normalize_character_data(character_bible)
    if not chars:
        return {"score": 50, "issues": ["캐릭터 바이블이 없음"], "evidence": []}

    appeared_count = 0
    role_diversity = set()
    issues = []
    evidence = []

    for char in chars:
        if not isinstance(char, dict):
            continue
        name = char.get("name", char.get("이름", ""))
        role = char.get("narrative_role", char.get("서사적_역할", ""))

        if name and name in text:
            appeared_count += 1
            evidence.append(f"{name} 등장")
            if role:
                role_diversity.add(role)

    # 점수 계산
    if appeared_count == 0:
        score = 30
        issues.append("바이블 인물 미등장")
    elif appeared_count == 1:
        score = 60
        issues.append("주인공만 등장 (조연 부족)")
    elif appeared_count >= 3:
        score = 90
        if len(role_diversity) >= 2:
            score = 95
            evidence.append(f"인물 역할 다양성 {len(role_diversity)}종")
    else:
        score = 75

    # 평면화 검증 — 너무 짧은 인용/대사만 있으면 감점
    if appeared_count > 0 and len(text) > 1000:
        for char in chars:
            if not isinstance(char, dict):
                continue
            name = char.get("name", char.get("이름", ""))
            if name and text.count(name) == 1 and len(text) > 2000:
                # 등장은 했으나 1회 호출만
                issues.append(f"{name} 단순 1회 언급 (평면화 우려)")
                score = max(50, score - 5)

    return {
        "score": score,
        "issues": issues,
        "evidence": evidence,
        "appeared_count": appeared_count,
        "role_diversity": list(role_diversity),
    }


def _score_cliffhanger_strength(text: str, cliff_type: Optional[str] = None) -> dict:
    """클리프행어 강도 검증."""
    if not text or len(text) < 200:
        return {"score": 30, "issues": ["본문이 너무 짧음"], "evidence": []}

    last_300 = text[-300:].lower()
    issues = []
    evidence = []

    # 클리프행어 패턴 키워드 (9유형 무협 특화)
    cliff_patterns = {
        "Slap": ["손바닥", "뺨", "충격", "소리", "쿵"],
        "Reveal": ["사실은", "정체", "진실", "알고 보니", "그러나"],
        "Reversal": ["하지만", "그러나", "갑자기", "예상 밖", "역전"],
        "Arrival": ["나타났다", "도착했다", "등장", "문이 열렸"],
        "Choice": ["선택", "결정", "둘 중", "어느"],
        "Threat": ["위협", "죽음", "위기", "공격", "무기"],
        "Tears": ["눈물", "울었", "흐느", "슬픔"],
        "Challenge": ["비무", "결투", "도전", "대결"],  # 무협 특화
        "Breakthrough": ["깨달음", "각성", "돌파", "초절정", "단전이"],  # 무협 특화
    }

    detected_types = []
    for ptype, keywords in cliff_patterns.items():
        if any(kw in last_300 for kw in keywords):
            detected_types.append(ptype)

    # 점수
    if not detected_types:
        score = 50
        issues.append("마지막 300자에 클리프행어 패턴 미검출")
    elif len(detected_types) == 1:
        score = 75
        evidence.append(f"{detected_types[0]} 패턴 감지")
    else:
        score = 85
        evidence.append(f"복합 패턴 {detected_types[:2]}")

    # 마지막 문장의 임팩트 — 짧은 문장으로 끝나면 +5
    last_lines = [l.strip() for l in text.split("\n") if l.strip()][-3:]
    if last_lines and len(last_lines[-1]) <= 30:
        score = min(100, score + 5)
        evidence.append("짧은 임팩트 문장으로 마무리")

    # 명시된 cliffhanger_type과 일치 여부
    if cliff_type and cliff_type not in detected_types and len(detected_types) > 0:
        issues.append(f"의도한 {cliff_type} 패턴과 다른 패턴 감지")

    return {
        "score": score,
        "issues": issues,
        "evidence": evidence,
        "detected_types": detected_types,
    }


def _score_mise_en_scene(text: str) -> dict:
    """장면·묘사 강도 검증 (무협 가중)."""
    if not text:
        return {"score": 0, "issues": ["본문 없음"], "evidence": []}

    issues = []
    evidence = []
    score = 60  # 기본값

    # 무공 시전 묘사 키워드
    martial_keywords = [
        "검을", "검이", "도가", "도를", "권법", "장법", "내공", "기운",
        "휘둘렀", "내리쳤", "찔러", "베었", "튕겨", "솟구", "치솟",
        "발산", "폭발", "흩어", "꿰뚫", "베어",
    ]
    martial_hits = sum(1 for kw in martial_keywords if kw in text)
    if martial_hits >= 5:
        score += 15
        evidence.append(f"무공 시전 묘사 풍부 ({martial_hits}회)")
    elif martial_hits >= 2:
        score += 8
        evidence.append(f"무공 묘사 적정 ({martial_hits}회)")
    else:
        issues.append("무공 시전 묘사 부족 (전투 회차라면 보강 필요)")

    # 시각적 디테일 (의복·표정·자세)
    visual_keywords = [
        "표정", "눈빛", "미소", "찡그", "노려", "응시",
        "자세", "포즈", "몸짓", "흩날리", "휘날리",
        "검은", "붉은", "푸른", "흰", "옷자락",
    ]
    visual_hits = sum(1 for kw in visual_keywords if kw in text)
    if visual_hits >= 5:
        score += 10
        evidence.append(f"시각적 묘사 충분 ({visual_hits}회)")
    elif visual_hits >= 2:
        score += 5

    # 청각·후각 등 비시각 감각
    sensory_keywords = ["냄새", "향기", "소리가", "울림", "외침", "비명"]
    sensory_hits = sum(1 for kw in sensory_keywords if kw in text)
    if sensory_hits >= 2:
        score += 5
        evidence.append("다감각 묘사 포함")

    # 한자 병기 과다 검출 (글로벌 친화 위반)
    import re
    chinese_count = len(re.findall(r'\([\u4e00-\u9fff]+\)', text))
    if chinese_count > 8:
        score -= 10
        issues.append(f"한자 병기 과다 ({chinese_count}회) — 글로벌 영문 친화 위반")
    elif chinese_count > 4:
        score -= 3
        issues.append(f"한자 병기 약간 많음 ({chinese_count}회)")

    score = max(0, min(100, score))

    return {
        "score": score,
        "issues": issues,
        "evidence": evidence,
        "martial_hits": martial_hits,
        "visual_hits": visual_hits,
        "chinese_brackets": chinese_count,
    }


def _score_market_viability_episode(
    concept: dict,
    text: str,
    ep_number: int = 0,
    total_eps: int = 50,
) -> dict:
    """시장성 검증 — 트리거·훅·명대사."""
    issues = []
    evidence = []
    score = 60

    # 1. 첫 200자 훅
    if len(text) >= 200:
        first_200 = text[:200]
        hook_keywords = ["죽었다", "눈을 떴", "회귀", "전생", "각성", "...!", "?", "검", "피"]
        hook_hits = sum(1 for kw in hook_keywords if kw in first_200)
        if hook_hits >= 2:
            score += 15
            evidence.append("첫 200자 강력한 훅")
        elif hook_hits == 0:
            score -= 5
            issues.append("첫 200자 훅 부족")

    # 2. 명대사 (큰따옴표 짧은 대사)
    import re
    quoted_lines = re.findall(r'["""]([^"""\n]{5,30})["""]', text)
    if len(quoted_lines) >= 3:
        score += 10
        evidence.append(f"임팩트 대사 {len(quoted_lines)}개")
    elif len(quoted_lines) >= 1:
        score += 3

    # 3. 분량 (플랫폼 표준 4500~5500자)
    text_len = len(text)
    if 4000 <= text_len <= 6000:
        score += 5
        evidence.append(f"분량 적정 ({text_len}자)")
    elif text_len < 3000:
        score -= 10
        issues.append(f"분량 부족 ({text_len}자)")
    elif text_len > 7000:
        score -= 3
        issues.append(f"분량 과다 ({text_len}자)")

    # 4. 한자·고어체 검출 (10대 친화)
    archaic = ["재하", "소생", "본좌", "귀공", "시주", "이외다", "이오이다", "하나이다"]
    archaic_hits = sum(text.count(a) for a in archaic)
    if archaic_hits > 3:
        score -= 8
        issues.append(f"고어체 과다 ({archaic_hits}회) — 10대·글로벌 친화 위반")

    # 5. 회차 위치 적합성
    if ep_number > 0 and ep_number <= 5:
        # 초반은 훅이 더 중요
        if "?" in text[:500] or "!" in text[:500]:
            score += 3

    score = max(0, min(100, score))

    return {
        "score": score,
        "issues": issues,
        "evidence": evidence,
        "text_length": text_len,
        "quoted_lines_count": len(quoted_lines),
    }


def _generate_verdict(grade: str, axes: dict, overall: int) -> str:
    """종합 판정 텍스트 생성."""
    if overall >= 85:
        return f"우수 ({grade}). 발행 권장."
    elif overall >= VALIDATION_THRESHOLDS["episode_pass"]:
        return f"합격 ({grade}). 약점 보완 후 발행 가능."
    elif overall >= VALIDATION_THRESHOLDS["episode_warn"]:
        weak_axes = [n for n, d in axes.items() if d.get("score", 100) < 70]
        return f"경고 ({grade}). 약점 축: {', '.join(weak_axes)}. 보완 권장."
    else:
        return f"재집필 권장 ({grade}). 종합 점수 {overall} — 핵심 약점 다수."


# ============================================================================
# 3. detect_transition_episodes — 전환점 자동 감지
# ============================================================================
def detect_transition_episodes(concept: dict, total_eps: int = 50) -> List[int]:
    """단계 전환점 회차 자동 추출.
    무협(남성향 3단계)이면 보통 [3, 5, 30, 35] 같은 패턴."""
    if _PROMPT_OK:
        return _detect_transitions_from_prompt(total_eps)

    # 폴백
    s2_start = max(2, int(total_eps * 0.10))
    s2_full = max(s2_start + 2, int(total_eps * 0.20))
    s3_start = max(s2_full + 2, int(total_eps * 0.65))
    s3_full = max(s3_start + 1, int(total_eps * 0.70))
    return sorted(set([s2_start, s2_full, s3_start, s3_full]))


# ============================================================================
# 4. get_validation_mode_for_episode
# ============================================================================
def get_validation_mode_for_episode(
    ep_number: int,
    mode: str,
    concept: dict,
    total_eps: int = 50,
) -> dict:
    """현재 회차에서 자동 검수 실행할지 결정.

    Returns:
        {
            "should_auto": bool,    # 자동 실행 여부
            "reason": str,          # 결정 이유
            "is_transition": bool,  # 전환점 회차 여부
        }
    """
    transitions = detect_transition_episodes(concept, total_eps)
    is_transition = ep_number in transitions

    if mode == "all_auto":
        return {
            "should_auto": True,
            "reason": "전체 자동 검수 모드",
            "is_transition": is_transition,
        }

    if mode == "all_manual":
        return {
            "should_auto": False,
            "reason": "수동 검수 모드 — 작가가 버튼으로 실행",
            "is_transition": is_transition,
        }

    if mode == "transition_only":
        if is_transition:
            return {
                "should_auto": True,
                "reason": f"전환점 회차 (전환 회차 목록: {transitions})",
                "is_transition": True,
            }
        return {
            "should_auto": False,
            "reason": "일반 회차 — 전환점 모드에서는 수동만",
            "is_transition": False,
        }

    if mode == "auto_until_25":
        if ep_number <= 25:
            return {
                "should_auto": True,
                "reason": f"1~25화 자동 모니터링 구간 (현재 EP{ep_number})",
                "is_transition": is_transition,
            }
        return {
            "should_auto": False,
            "reason": "26화 이후 — 작가 결정 필요",
            "is_transition": is_transition,
        }

    return {
        "should_auto": False,
        "reason": f"알 수 없는 모드: {mode}",
        "is_transition": is_transition,
    }


# ============================================================================
# 5. generate_material_usage_report — 작가용 마크다운 리포트
# ============================================================================
def generate_material_usage_report(validation_result: dict, ep_number: int = 0) -> str:
    """검수 결과를 마크다운 리포트로 생성."""
    if not validation_result:
        return "검수 결과가 없습니다."

    overall = validation_result.get("overall", 0)
    grade = validation_result.get("grade", "?")
    verdict = validation_result.get("verdict", "?")
    verdict_text = validation_result.get("verdict_text", "")
    axes = validation_result.get("axes", {})

    lines = []
    lines.append(f"## 📊 EP{ep_number} 자가 검수 리포트")
    lines.append(f"\n**종합 점수**: {overall}점 · **등급**: {grade} · **판정**: {verdict}")
    lines.append(f"\n{verdict_text}")

    lines.append("\n---\n### 5축 세부 점수")
    for axis_name, axis_data in axes.items():
        if not isinstance(axis_data, dict):
            continue
        score = axis_data.get("score", 0)
        weight = WUXIA_VALIDATION_WEIGHTS.get(axis_name, 0)
        emoji = "🟢" if score >= 75 else ("🟡" if score >= 60 else "🔴")
        lines.append(f"\n#### {emoji} {axis_name} — {score}점 (가중치 {int(weight*100)}%)")

        evidence = axis_data.get("evidence", []) or axis_data.get("details", {}).get("used", [])
        if evidence:
            lines.append("**근거**:")
            for e in evidence[:3]:
                lines.append(f"- {e}")

        issues = axis_data.get("issues", []) or axis_data.get("details", {}).get("missing", [])
        if issues:
            lines.append("**문제점**:")
            for i in issues[:3]:
                lines.append(f"- ⚠️ {i}")

    # 핵심 누락
    material = axes.get("MATERIAL_USAGE", {}).get("details", {})
    critical = material.get("critical_missing", [])
    if critical:
        lines.append("\n---\n### ⛔ 치명적 누락")
        for c in critical:
            lines.append(f"- {c}")

    return "\n".join(lines)


# ============================================================================
# 6. summarize_cumulative_25 — 25화 누적 대시보드
# ============================================================================
def summarize_cumulative_25(
    validation_history: List[dict],
    cliffhanger_counts: Optional[Dict[str, int]] = None,
    total_eps: int = 50,
) -> dict:
    """1~25화 누적 대시보드 데이터.

    Returns:
        {
            "n_episodes": int,
            "avg_overall": float,
            "axis_avgs": dict,
            "weakest_episodes": list,
            "strongest_episodes": list,
            "frequent_missing": list,
            "cliffhanger_balance": dict,
            "recommendation": str,
        }
    """
    if not validation_history:
        return {
            "n_episodes": 0,
            "avg_overall": 0,
            "axis_avgs": {},
            "weakest_episodes": [],
            "strongest_episodes": [],
            "frequent_missing": [],
            "cliffhanger_balance": {},
            "recommendation": "검수 이력이 없습니다.",
        }

    n = len(validation_history)
    overalls = [v.get("overall", 0) for v in validation_history]
    avg_overall = sum(overalls) / n if n > 0 else 0

    # 축별 평균
    axis_sums = {axis: 0 for axis in WUXIA_VALIDATION_WEIGHTS.keys()}
    for v in validation_history:
        for axis_name, axis_data in v.get("axes", {}).items():
            if axis_name in axis_sums and isinstance(axis_data, dict):
                axis_sums[axis_name] += axis_data.get("score", 0)
    axis_avgs = {axis: round(total / n, 1) if n > 0 else 0 for axis, total in axis_sums.items()}

    # 약점/강점 회차
    indexed = [(i + 1, o) for i, o in enumerate(overalls)]
    indexed.sort(key=lambda x: x[1])
    weakest = indexed[:3]
    strongest = sorted(indexed, key=lambda x: x[1], reverse=True)[:3]

    # 자주 누락되는 재료
    missing_counter = {}
    for v in validation_history:
        material = v.get("axes", {}).get("MATERIAL_USAGE", {}).get("details", {})
        for m in material.get("missing", []):
            missing_counter[m] = missing_counter.get(m, 0) + 1
    frequent_missing = sorted(missing_counter.items(), key=lambda x: -x[1])[:5]

    # 클리프행어 분포
    if not cliffhanger_counts:
        cliffhanger_counts = {}
        for v in validation_history:
            detected = v.get("axes", {}).get("CLIFFHANGER_STRENGTH", {}).get("detected_types", [])
            for t in detected:
                cliffhanger_counts[t] = cliffhanger_counts.get(t, 0) + 1

    # 권장 모드
    recommendation = _recommend_next_mode(avg_overall, axis_avgs, weakest)

    return {
        "n_episodes": n,
        "avg_overall": round(avg_overall, 1),
        "axis_avgs": axis_avgs,
        "weakest_episodes": weakest,
        "strongest_episodes": strongest,
        "frequent_missing": frequent_missing,
        "cliffhanger_balance": cliffhanger_counts,
        "recommendation": recommendation,
    }


def _recommend_next_mode(avg_overall: float, axis_avgs: dict, weakest: list) -> str:
    """누적 대시보드 기반 26화 이후 모드 권장."""
    if avg_overall >= VALIDATION_THRESHOLDS["cumulative_pass"]:
        return (
            f"누적 평균 {avg_overall:.1f}점 — 우수. **transition_only 모드** 권장.\n"
            f"전환점 회차만 자동 검수해도 품질 유지 가능."
        )

    weak_axes_low = [n for n, s in axis_avgs.items() if s < 65]
    if len(weak_axes_low) >= 2:
        return (
            f"누적 평균 {avg_overall:.1f}점 — 약점 축 {len(weak_axes_low)}개 ({', '.join(weak_axes_low)}). "
            f"**all_auto 모드** 권장. 전체 자동 검수로 안전하게."
        )

    if avg_overall >= 70:
        return (
            f"누적 평균 {avg_overall:.1f}점 — 양호. **transition_only** 또는 **all_manual** 중 선택.\n"
            f"작가 신뢰도 따라 결정."
        )

    return (
        f"누적 평균 {avg_overall:.1f}점 — 미흡. **all_auto 모드** 강력 권장.\n"
        f"가장 약한 회차: {weakest[:2]}"
    )


# ============================================================================
# 자가 테스트
# ============================================================================
def _self_test():
    """모듈 자체 검증."""
    print("=== engine_validator.py 자가 테스트 ===")

    # 1. 검수 함수 호출
    sample_concept = {
        "title": "테스트 작품",
        "wuxia_formula_main": "F1_회귀_먼치킨_문파재건",
        "protagonist_type": "회귀자",
        "narrative_motifs": {"primary": "회귀(回歸)"},
        "protagonist": {"name": "장무극"},
    }
    sample_text = (
        "장무극은 눈을 떴다. 다시 과거로 돌아온 것이다.\n"
        "전생의 기억이 선명했다. 회귀였다.\n"
        "검을 들고 그는 휘둘렀다. 검기가 솟구쳤다.\n"
        "사부 청명 도장이 그를 응시했다.\n"
        "\"무극아, 너는 누구냐?\"\n"
        "장무극은 미소지었다. \"제자입니다, 사부님.\"\n"
    )
    sample_bible = [{"name": "장무극", "narrative_role": "주인공"}, {"name": "청명", "narrative_role": "사부_정신적_스승"}]

    result = compute_episode_validation_score(
        sample_concept, sample_bible, sample_text, ep_number=1, total_eps=50,
    )
    print(f"\n종합 점수: {result['overall']}점 ({result['grade']})")
    print(f"판정: {result['verdict']}")
    print(f"5축:")
    for axis, data in result['axes'].items():
        print(f"  - {axis}: {data['score']}점")

    # 2. 전환점 자동 감지
    transitions = detect_transition_episodes({}, 50)
    print(f"\n50화 전환점: {transitions}")

    # 3. 검수 모드
    for mode in ["auto_until_25", "transition_only", "all_auto"]:
        decision = get_validation_mode_for_episode(5, mode, sample_concept, 50)
        print(f"\nEP5 {mode}: should_auto={decision['should_auto']}, reason={decision['reason'][:40]}")

    # 4. 마크다운 리포트
    report = generate_material_usage_report(result, ep_number=1)
    print(f"\n리포트 길이: {len(report)}자")

    print("\n✅ 자가 테스트 통과")


if __name__ == "__main__":
    _self_test()
