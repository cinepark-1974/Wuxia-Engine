"""
👖 BLUE JEANS WUXIA ENGINE v2.7.2 — engine_validator.py
═══════════════════════════════════════════════════════════
회차 자가 검수 · 재료 활용 검증 · 전환점 자동 감지 · 문체 정적 스캐너
· 초식 일관성 정적 검사 · 장르 밀도 정적 검사

[변경 이력]
v2.7.2 (2026-07-28) — A32 문장 선두 기호 검출
  · scan_prose_style()에 A32 검출 2종 추가
    — 대사·문장 선두 말줄임표 ("……네." / …그러니까)
    — 문단 선두 대시 (——그런데 몸이 …)
  · 장면 구분선(*** / ··· 등 기호 전용 줄)은 검출 대상에서 제외
  · 아미고 EP002 실측: 선두 말줄임표 11건 / 선두 대시 3건
  · 설계 원칙 K 유지 — 검출만 하고 본문은 수정하지 않는다

v2.6.0 (2026-07-26) — Genre Density Scanner + 감점 방향 반전
  · [사고 패턴 N — 검수기가 정답을 오답으로 판정] 아미고 실측:
      작가 원고 EP2 (초식 9종·병기 16회) → MISE_EN_SCENE 80점
                                          + "글로벌 친화 위반" 감점
      엔진 원고 EP2 (초식 0종·병기 0회)  → MISE_EN_SCENE 90점, 무지적
    검수기가 장르가 살아 있는 원고를 감점하고 장르가 죽은 원고에
    최고점을 줬다. 엔진이 잘못된 방향으로 최적화되고 있었다.
  · _score_mise_en_scene 한자 병기 감점 로직 **반전**
    — 기존: >8회 -10점 (과다 감점만 존재, 부재는 무벌점)
    — 신설: <4회 -12점(장르 신호 부족) / 6~16회 +8점(정상)
            >22회 -6점(반복 병기 의심)
  · _score_mise_en_scene에 초식 명명 가점 신설 — 이름 붙은 무공이
    본문에 몇 종 등장하는지를 직접 계측 (기존에는 동작 동사만 계측해
    이름 없는 격투도 만점을 받을 수 있었다)
  · scan_wuxia_density() 신설 — A29~A31 정량 검사.
    7개 쿼터(명명 초식 / 병기 / 3박자 / 문파 / 내공 / 의성어 / 경지)
    EP1~EP4는 강화 임계값 적용
  · format_wuxia_density_report() 신설 — 쿼터 달성표 + 미달 항목
  · _collect_bible_terms 오탐 수정 — 1~2자 용어("기", "도")가
    한글 음절 어디에나 걸려 art_mentions가 과대 계상되던 문제
    (엔진 EP2가 "기(氣)x31"로 잡혔으나 실제 병기는 0회였음)
  · 설계 원칙 K 유지 — 검출만 하고 본문은 수정하지 않는다

v2.5.0 (2026-07-25) — Martial Consistency Scanner
  · scan_martial_consistency() 신설 — A27(초식 일관성)·A28(작가 설정
    우선) 정적 검사. LLM 미사용, 재현성 100%
    — 바이블 초식 사용 현황 / 무협 관용명 침입(자하신공·태극혼원공류)
    — 바이블 외 초식 후보(즉흥 작명 의심) / 한자 병기 반복
  · format_martial_scan_report() 신설 — 작가용 리포트.
    UI 표시와 REDO 프롬프트 주입에 공용
  · v2.4.0이 그릇(초식 바이블)과 룰(A28)을 만들었으나 준수 여부를
    확인할 수단이 없었다. 아미고 EP1의 초식명 0개를 알아내는 데
    사람의 통독이 필요했던 문제를 해결
  · 설계 원칙 K 유지 — 검출만 하고 본문은 수정하지 않는다


v2.3.0 (2026-07-23) — Youth Target Diagnosis
  · diagnose_youth_target() 신설 — A25(1020 경량화)·A26(무협 액기스)
    정량 진단. 대사 비율·대사 밀도·묘사 연속·무공/격돌 표현 검출
  · format_youth_diagnosis_report() 신설 — 지표표 + 미달 항목 리포트
  · 주인공 대사 수는 의도적으로 측정하지 않음 — 단역이 바이블에
    없으면 화자 식별이 불가해 추정치가 항상 과대 계상되므로
    (사고 패턴 I). 대사 비율·밀도로 동일 문제를 포착

v2.2.0 (2026-07-23) — Prose Style Scanner
  · scan_prose_style() 신설 — A23(계측·리포트체)·A24(설정 재료 반복)
    정규식 기반 정적 검출. LLM 미사용 → 재현성 100% 보장
  · format_prose_scan_report() 신설 — UI 표시·REDO 프롬프트 주입 공용
  · 원칙: 검출만 한다. 자동 수정·삭제 없음 (본문은 작가의 영역)
  · 인물명은 별칭 매칭으로 반복 검출에서 제외 (사고 패턴 H 적용)

v2.1.0 (2026-05-19) — Quality Pack
  · _score_mise_en_scene: martial/visual/sensory 키워드 사전에 활용형 보강
    (WebNovel v3.3 사고 사례: "뜨거워"만 등록 → "뜨거웠다" 누락으로 거짓 저점)

v2.0 (2026-05) — 초기 자가 검수 엔진
  · 5축 검수 시스템
  · 마음 흐름 전환점 자동 감지
  · 25화 누적 대시보드

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

import re
from typing import List, Dict, Optional, Tuple

# ═══════════════════════════════════════════════════
# 장르 밀도 계측 상수 (A29~A31) — v2.6.0 신규
# 무협의 장르 신호는 "동작"이 아니라 "이름"이다.
# 기존 검수는 동작 동사만 계측해 이름 없는 현대 격투도
# 만점을 받을 수 있었다. 이 상수군이 그 구멍을 막는다.
# ═══════════════════════════════════════════════════

# 무공 이름 접미어 — 한글만 써도 무공으로 판정
_ART_NAME_TAILS = (
    "신공", "심법", "검법", "도법", "장법", "권법", "지법", "보법",
    "신법", "각법", "창법", "편법", "검술", "도술", "창술", "권술",
    "장풍", "진경", "대법", "절기", "초식", "검결", "검진", "진법",
    "경공술", "축지법", "조식", "연환격", "무술", "연검술",
)
_ART_TAIL_RE = re.compile(
    r"([가-힣]{2,8}(?:" + "|".join(_ART_NAME_TAILS) + r"))"
)

# 한자 병기형 고유명사 — 한글(한자 3자 이상)
_HANJA_PAIR_RE = re.compile(r"([가-힣]{2,10})\s*\(([\u4e00-\u9fff]{2,10})\)")

# 병기 고유명사 중 무공이 아닌 범주 (학교·사찰·문파·지명·대회)
# 주의: "도"는 화산장풍도 같은 무공명 꼬리이므로 제외 목록에 넣지 않는다.
_NON_ART_TAILS = (
    "고", "교", "사", "파", "원", "궁", "성", "산", "촌", "각",
    "회", "대전", "대회", "관", "루", "방", "맹", "부", "군",
)

# 내공·기 어휘 (A31)
_NEIGONG_WORDS = [
    "내공", "기맥", "단전", "운기", "진기", "기세", "살기", "검기",
    "도기", "장력", "축기", "호흡법", "기(氣)", "기운", "혈도",
    "주화입마", "운기조식", "심법", "기의 흐름",
]

# 경지·서열 어휘 (A31)
_REALM_WORDS = [
    "화경", "절정", "초절정", "현경", "생사경", "자연경", "무신경",
    "삼화취정", "등봉조극", "통맥", "기초경", "입문", "대성",
    "경지", "고수", "일류", "이류", "삼류", "절대고수", "화후",
]

# 문파·계보 (A31) — 바이블 문파와 합집합으로 사용
_GENERIC_FACTIONS = [
    "무당파", "화산파", "아미파", "소림", "곤륜", "개방", "점창",
    "종남", "청성", "공동", "해남", "장백", "마교", "천마신교",
    "구파일방", "오대세가", "남궁", "사파", "정파", "무림맹",
]

# 의성어 (A31) — 타격·풍압·검격
_ONOMATOPOEIA = [
    "휙", "휘릭", "휘잉", "획", "쏴아", "쏴", "쐐액", "쉬익", "쉭",
    "붕", "쩌렁", "쩌렁쩌렁", "쿵", "쾅", "퍽", "팍", "파앙", "챙",
    "캉", "따앙", "철컥", "우드득", "우웅", "웅", "쌩", "빵빵",
    "다다다닥", "후다다닥", "촥", "스윽", "탁", "툭",
]
# 인용부호로 감싼 짧은 한글 (의성어 후보)
_QUOTED_SHORT_RE = re.compile(r"[\u2018\u201c'\"]([가-힣]{1,6})[\u2019\u201d'\"]")

# A30 ③해설 신호어 — 무공의 원리·귀속·장단점을 설명하는 표현
_EXPLAIN_MARKERS = [
    "무공이었다", "무공이다", "무공으로", "특화", "핵심은", "핵심이",
    "원리", "계열", "계보", "자랑하는", "비롯", "단점", "장점",
    "약하", "강하", "대가", "한계", "이용해", "응용", "기반",
    "연구하여", "연구해", "만든", "본류", "갈래", "비법",
    "보법이었다", "권법이었다", "술이었다", "기술이다", "뜻이었다",
    "능력을", "경지", "따라", "덕분", "때문",
]


def _count_three_beat(text: str, named_arts: list) -> list:
    """A30 3박자(명명→시연→해설) 완주 무공을 판정 — v2.6.0 신규.

    무공명 첫 등장 지점 앞 200자·뒤 500자 창에서 해설 신호어를
    2개 이상 찾으면 완주로 본다. 휴리스틱이며 진단용이다.

    Returns:
        완주로 판정된 무공명(한글 표기) 리스트
    """
    out = []
    if not text or not named_arts:
        return out
    for art in named_arts:
        base = re.sub(r"\s*\([^)]*\)\s*", "", art).strip()
        if not base:
            continue
        idx = text.find(base)
        if idx < 0:
            continue
        window = text[max(0, idx - 200): idx + 500]
        hits = [k for k in _EXPLAIN_MARKERS if k in window]
        if len(hits) >= 2:
            out.append(base)
    return out


def _extract_named_arts(text: str, bible_arts: Optional[set] = None) -> list:
    """본문에서 '이름이 붙은 무공'을 추출 — v2.6.0 신규.

    세 경로의 합집합으로 판정한다.
      ① 초식 바이블에 등재된 무공명 (가장 신뢰도 높음)
      ② 무공 접미어형 (당랑연검술·청수유수권·축지법)
      ③ 한자 병기형 중 무공으로 보이는 것 (유수화풍(流水和風))
         — 학교·사찰·문파·대회 접미어는 제외

    휴리스틱이므로 소수의 오탐·미탐이 있다. 진단 지표이며
    최종 판단은 작가의 것이다 (설계 원칙 K).

    Returns:
        정렬된 무공명 리스트 (중복 제거, 한자 병기 표기 우선)
    """
    if not text or not isinstance(text, str):
        return []

    found = {}   # 한글 표기 → 표시용 표기

    def _put(kor, display=None):
        kor = (kor or "").strip()
        if len(kor) < 2:
            return
        prev = found.get(kor)
        if display and (not prev or len(display) > len(prev)):
            found[kor] = display
        else:
            found.setdefault(kor, display or kor)

    # ① 바이블 등재 무공
    for art in sorted(bible_arts or set(), key=len, reverse=True):
        base = re.sub(r"\s*\([^)]*\)\s*", "", art).strip()
        if len(base) < 2:
            continue
        if base in text or art in text:
            _put(base, art if "(" in art else None)

    # ② 무공 접미어형
    for m in _ART_TAIL_RE.findall(text):
        _put(m)

    # ③ 한자 병기형 (무공 아닌 범주 제외)
    for kor, han in _HANJA_PAIR_RE.findall(text):
        if len(kor) < 2:
            continue
        if kor.endswith(_NON_ART_TAILS):
            continue
        _put(kor, f"{kor}({han})")

    return sorted(found.values())

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
    """장면·묘사 강도 검증 (무협 가중).

    [v2.1.0 키워드 사전 보강]
    martial_keywords·visual_keywords·sensory_keywords 모두 어간 + 주요 활용형 등록.
    어간만 등록 시 작가가 자연스럽게 쓰는 활용형이 검출되지 않아 거짓 저점 발생.
    (WebNovel v3.3 사고 사례에서 발견된 패턴)

    [v2.6.0 장르 밀도 반영 — 사고 패턴 N]
    기존 배점은 동작 동사만 계측해 이름 없는 현대 격투도 고득점했다.
    실측: 초식 0종·병기 0회 원고가 90점, 초식 9종·병기 16회 작가 원고가
    80점. 방향이 반대였다. v2.6.0에서 세 요소를 추가·반전한다.
      · 이름 붙은 무공 종수 (A29)   — 0종이면 큰 감점
      · A30 3박자 해설 유무          — 무협 독자의 과금 지점
      · 한자 병기 감점 방향 반전     — 부재가 위반, 반복이 위반
    상단 포화를 막기 위해 기본 점수를 60 → 45로 낮췄다.
    """
    if not text:
        return {"score": 0, "issues": ["본문 없음"], "evidence": []}

    issues = []
    evidence = []
    score = 45  # 기본값 (v2.6.0: 장르 밀도 항목 신설로 하향)

    # 무공 시전 묘사 키워드 — v2.1.0 활용형 보강
    martial_keywords = [
        # 기본 무기·내공 (명사 + 조사)
        "검을", "검이", "검으로", "도가", "도를", "도로",
        "권법", "장법", "내공", "기운", "진기", "검기", "도기",

        # 동작 동사 — 어간 + 주요 활용형
        "휘둘렀", "휘둘렀다", "휘두르며", "휘두르는", "휘두르자",
        "내리쳤", "내리쳤다", "내리치는", "내리쳐",
        "찔러", "찔렀", "찔렀다", "찌르는", "찌르며", "찌르자",
        "베었", "베었다", "베는", "베어", "베어내", "베어냈다",
        "튕겨", "튕겼다", "튕겨졌다", "튕겨내",
        "솟구", "솟구쳤", "솟구쳤다", "솟구치는", "솟구쳐",
        "치솟", "치솟았", "치솟았다", "치솟는",
        "발산", "발산했", "발산했다", "발산하며",
        "폭발", "폭발했", "폭발했다", "폭발하며",
        "흩어", "흩어졌", "흩어졌다", "흩어진", "흩어지며",
        "꿰뚫", "꿰뚫었", "꿰뚫었다", "꿰뚫는", "꿰뚫고",
        "쏟아", "쏟아졌다", "쏟아붓",
        "내질", "내질렀다", "내지르는",
    ]
    martial_hits = sum(1 for kw in martial_keywords if kw in text)
    if martial_hits >= 5:
        score += 12
        evidence.append(f"무공 시전 묘사 풍부 ({martial_hits}회)")
    elif martial_hits >= 2:
        score += 6
        evidence.append(f"무공 묘사 적정 ({martial_hits}회)")
    else:
        issues.append("무공 시전 묘사 부족 (전투 회차라면 보강 필요)")

    # 시각적 디테일 (의복·표정·자세) — v2.1.0 활용형 보강
    visual_keywords = [
        # 표정·시선
        "표정", "눈빛", "미소", "찡그", "찡그렸", "찡그렸다", "찡그리며",
        "노려", "노려보", "노려보았다", "노려보는",
        "응시", "응시했다", "응시하는",
        "흘끗", "스치", "스쳤다",

        # 자세·움직임
        "자세", "포즈", "몸짓",
        "흩날리", "흩날렸다", "흩날리는",
        "휘날리", "휘날렸다", "휘날리는",
        "굳었", "굳었다", "굳어졌다",

        # 색·옷
        "검은", "붉은", "푸른", "흰", "옷자락", "소매", "도포",
    ]
    visual_hits = sum(1 for kw in visual_keywords if kw in text)
    if visual_hits >= 5:
        score += 8
        evidence.append(f"시각적 묘사 충분 ({visual_hits}회)")
    elif visual_hits >= 2:
        score += 4

    # 청각·후각 등 비시각 감각 — v2.1.0 활용형 보강
    sensory_keywords = [
        "냄새", "냄새가", "향기", "향기가",
        "소리", "소리가", "소리에", "울림", "울렸다", "울리는",
        "외침", "외쳤다", "외치는",
        "비명", "비명이",
        "메아리", "쩌렁",
        "촉감", "차가웠", "차가웠다", "뜨거웠", "뜨거웠다",
    ]
    sensory_hits = sum(1 for kw in sensory_keywords if kw in text)
    if sensory_hits >= 2:
        score += 5
        evidence.append("다감각 묘사 포함")

    # ── 이름이 붙은 무공 계측 (v2.6.0 신설) ──
    # [왜 필요한가] 기존에는 동작 동사(휘둘렀다·베었다)만 계측했다.
    # 그래서 "관절을 꺾고 명치를 눌렀다" 같은 현대 격투도 만점을 받았다.
    # 무협의 장르 신호는 동작이 아니라 **이름**이다.
    import re
    named_list = _extract_named_arts(text)
    named_arts = set(named_list)
    named_count = len(named_arts)
    if named_count >= 5:
        score += 18
        evidence.append(f"이름 붙은 무공 {named_count}종 — 장르 신호 충분")
    elif named_count >= 3:
        score += 10
        evidence.append(f"이름 붙은 무공 {named_count}종")
    elif named_count >= 1:
        score += 3
        issues.append(f"이름 붙은 무공 {named_count}종 — 장르 밀도 부족 (A29: 3종 이상)")
    else:
        score -= 15
        issues.append(
            "이름 붙은 무공 0종 — A29 위반. 무공 장면이 이름 없는 격투로 "
            "처리됐을 가능성이 큽니다."
        )

    # ── A30 3박자 해설 (v2.6.0 신설) ──
    # 무협 독자가 지갑을 여는 지점은 ③해설(원리·문파 귀속·장단점)이다.
    # 엔진 원고에서 가장 자주 통째로 빠지는 요소다.
    three_beat = _count_three_beat(text, named_list)
    if len(three_beat) >= 2:
        score += 10
        evidence.append(f"A30 3박자 완주 {len(three_beat)}회")
    elif len(three_beat) == 1:
        score += 4
        evidence.append("A30 3박자 완주 1회")
    else:
        score -= 10
        issues.append(
            "A30 위반 — 3박자 완주 0회. 무공의 원리·문파 귀속·장단점 해설이 "
            "없습니다."
        )

    # ── 한자 병기 (v2.6.0 감점 방향 반전) ──
    # 기존 로직은 과다만 감점하고 부재는 무벌점이었다. 그 결과
    # 병기 0회 원고가 병기 16회 작가 원고보다 높은 점수를 받았다.
    # 무협에서 고유명사 병기는 억제 대상이 아니라 장르 필수 신호다.
    # 줄여야 할 것은 총량이 아니라 같은 용어의 반복 병기다 (A15).
    chinese_count = len(re.findall(r'\([\u4e00-\u9fff]+\)', text))
    if chinese_count < 4:
        score -= 12
        issues.append(
            f"한자 병기 {chinese_count}회 — A15·A29 위반. 고유명사 병기가 "
            f"부족해 무협으로 읽히지 않습니다 (정상 8~15회)."
        )
    elif chinese_count <= 16:
        score += 8
        evidence.append(f"한자 병기 {chinese_count}회 — 정상 밀도")
    elif chinese_count <= 22:
        evidence.append(f"한자 병기 {chinese_count}회 — 상한 근접")
    else:
        score -= 6
        issues.append(
            f"한자 병기 {chinese_count}회 — 과다. 같은 용어의 반복 병기 여부를 "
            f"확인해 주십시오 (재등장 시 한글만)."
        )

    score = max(0, min(100, score))

    return {
        "score": score,
        "issues": issues,
        "evidence": evidence,
        "martial_hits": martial_hits,
        "visual_hits": visual_hits,
        "chinese_brackets": chinese_count,
        "named_arts": sorted(named_arts),
        "named_art_count": named_count,
        "three_beat_arts": three_beat,
        "three_beat_count": len(three_beat),
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
# ═══════════════════════════════════════════════════
# 문체 정적 스캐너 (A23·A24) — v2.2.0 신규
# LLM 없이 정규식·카운팅으로 검출 → 같은 본문이면 항상 같은 결과
# 원칙: 검출만 한다. 자동 수정·삭제는 하지 않는다 (본문은 작가의 영역).
# ═══════════════════════════════════════════════════

# 반복 어절 검출에서 제외할 일반 서술어·기능어 어간
_PROSE_SCAN_STOPWORDS = {
    "있었", "없었", "것이", "그것", "그리", "하지", "않았", "않은", "않는",
    "했다", "한다", "하는", "하고", "하며", "해서", "위해", "때문", "그러",
    "이었", "아니", "같았", "같은", "같이", "보였", "보다", "보고", "듯이",
    "듯했", "채로", "쪽으", "앞에", "뒤에", "위에", "아래", "안에", "밖으",
    "속에", "사이", "순간", "지금", "다시", "이제", "아직", "함께", "모두",
    "자신", "그녀", "소리", "시선", "얼굴", "고개", "손을", "눈을", "몸을",
    "말을", "말이", "말했", "물었", "대답", "생각", "잠깐", "잠시", "자기",
    "소년", "소녀", "남자", "여자", "사람", "그대", "천천", "조용", "가만",
}

# 초 단위 계측 패턴 (아라비아 숫자 + 한글 수사)
_MEASURE_TIME_RE = re.compile(
    r"(\d+(?:\.\d+)?\s*초)"
    r"|(초당\s*[가-힣\d]+)"
    r"|((?:일|이|삼|사|오|육|칠|팔|구|십)\s*초(?:쯤|간|만에)?)"
)

# 인지 부정 부연 패턴
_COGNITION_DENIAL_RE = re.compile(
    r"(?:본인|자신|스스로)[은는이가도]?\s*[^\n。.]{0,25}?"
    r"(?:의식하지 못|느끼지 못|인지하지 못|알지 못한 채|눈치채지 못)"
)

# 정밀 관찰 부사 (회차당 2회 이상이면 검출)
_PRECISION_ADVERBS = ["미세하게", "미묘하게"]

# 계측 명사 (회차당 2회 이상이면 검출)
_MEASURE_NOUNS = ["각도", "궤적", "좌표", "어깨선"]


# ── A32 (v2.7.2): 문장 선두 기호 검출용 ──
# 여는 따옴표 직후 또는 줄 맨 앞의 말줄임표
_LEAD_ELLIPSIS_RE = re.compile(r'(?:^|["“”\'‘’「『(\[])\s*(?:…+|\.{2,})')
# 줄 맨 앞의 대시 (뒤에 글자가 이어지는 경우만 — 구분선은 제외)
_LEAD_DASH_RE = re.compile(r'^\s*(?:[—–―]{1,3}|-{2,})\s*(?=\S)')
# 장면 구분선 문자 (검출에서 제외)
_SEPARATOR_CHARS = set("*＊·•◦・∙※◇◆◈○●□■△▲—–―-~=＝#§†✦✧")


def _find_lines_with(text: str, needle: str) -> List[str]:
    """needle이 포함된 줄을 발췌 (앞뒤 여백 정리, 최대 60자)."""
    out = []
    for line in text.split("\n"):
        if needle in line:
            s = line.strip()
            out.append(s[:60] + ("…" if len(s) > 60 else ""))
    return out


def scan_prose_style(text: str, character_bible: dict = None) -> dict:
    """
    A23(계측·리포트체) + A24(설정 재료 반복) 정적 스캐너.

    LLM을 쓰지 않으므로 재현성이 100% 보장된다.
    검출 결과는 위반 문장 발췌와 함께 반환하며, 수정은 하지 않는다.

    Args:
        text: 회차 본문
        character_bible: 캐릭터 바이블 (인물명을 반복 검출에서 제외하는 용도)

    Returns:
        {
          "violations": [ {"rule", "label", "count", "samples": [...]} ],
          "repeated_stems": [ {"stem", "count"} ],   # A24 참고용
          "total_flags": int,
          "clean": bool,
        }
    """
    if not text or not isinstance(text, str):
        return {"violations": [], "repeated_stems": [], "total_flags": 0, "clean": True}

    violations = []

    # ── A23-1. 초 단위 계측 ──
    time_hits = _MEASURE_TIME_RE.findall(text)
    time_matches = ["".join(t) for t in time_hits]
    if time_matches:
        samples = []
        for m in dict.fromkeys(time_matches):  # 중복 제거, 순서 유지
            samples.extend(_find_lines_with(text, m)[:2])
        violations.append({
            "rule": "A23",
            "label": "초 단위 계측 서술",
            "count": len(time_matches),
            "samples": samples[:5],
        })

    # ── A23-2. 인지 부정 부연 ──
    denial_hits = _COGNITION_DENIAL_RE.findall(text)
    if denial_hits:
        samples = []
        for m in dict.fromkeys(denial_hits):
            samples.extend(_find_lines_with(text, m)[:2])
        violations.append({
            "rule": "A23",
            "label": "인지 부정 부연 (서술자의 계측 보고)",
            "count": len(denial_hits),
            "samples": samples[:5],
        })

    # ── A23-3. 정밀 관찰 부사 (2회 이상) ──
    for adv in _PRECISION_ADVERBS:
        cnt = text.count(adv)
        if cnt >= 2:
            violations.append({
                "rule": "A23",
                "label": f'정밀 관찰 부사 "{adv}" 남용',
                "count": cnt,
                "samples": _find_lines_with(text, adv)[:3],
            })

    # ── A23-4. 계측 명사 (2회 이상) ──
    for noun in _MEASURE_NOUNS:
        cnt = text.count(noun)
        if cnt >= 2:
            violations.append({
                "rule": "A23",
                "label": f'계측 명사 "{noun}" 반복',
                "count": cnt,
                "samples": _find_lines_with(text, noun)[:3],
            })

    # ── A10 보조. "~하는 것이었다" (3회 이상) ──
    cnt = text.count("는 것이었다")
    if cnt >= 3:
        violations.append({
            "rule": "A10",
            "label": '"~하는 것이었다" 구문 남용',
            "count": cnt,
            "samples": _find_lines_with(text, "는 것이었다")[:3],
        })

    # ── A32. 문장 선두 기호 (v2.7.2 신규) ──
    # 대사 선두 말줄임표 / 문단 선두 대시. 한국 독자가 AI 문체를
    # 식별하는 1순위 단서이므로 1건이라도 잡아 보고한다.
    lead_dots, lead_dash = [], []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        # 기호로만 이루어진 짧은 줄(장면 구분선)은 제외
        if len(s) <= 12 and all(ch in _SEPARATOR_CHARS for ch in s.replace(" ", "")):
            continue
        if _LEAD_ELLIPSIS_RE.search(s):
            lead_dots.append(s[:60] + ("…" if len(s) > 60 else ""))
        if _LEAD_DASH_RE.match(s):
            lead_dash.append(s[:60] + ("…" if len(s) > 60 else ""))

    if lead_dots:
        violations.append({
            "rule": "A32",
            "label": "문장·대사 선두 말줄임표 (“……네.” 형태)",
            "count": len(lead_dots),
            "samples": lead_dots[:5],
        })
    if lead_dash:
        violations.append({
            "rule": "A32",
            "label": "문단 선두 대시 (——그런데 … 형태)",
            "count": len(lead_dash),
            "samples": lead_dash[:5],
        })

    # ── A24. 반복 어간 검출 (버릇·습관·소품 과잉 반복 감지) ──
    # 인물명은 정당한 반복이므로 제외 (별칭 매칭: 사고 패턴 H)
    name_stems = set()
    if isinstance(character_bible, dict):
        def _collect_names(node):
            if isinstance(node, dict):
                nm = node.get("name", "")
                if isinstance(nm, str) and nm:
                    # "서지훈 (徐志勳)" → "서지훈" + "지훈" (성 제외 별칭)
                    base = nm.split("(")[0].strip()
                    if base:
                        name_stems.add(base[:2])
                        name_stems.add(base)
                        if len(base) >= 3:
                            name_stems.add(base[1:])  # 이름만 (성 제외)
                for v in node.values():
                    _collect_names(v)
            elif isinstance(node, list):
                for v in node:
                    _collect_names(v)
        _collect_names(character_bible)

    # 어절 → 조사·어미 제거한 어간 카운트
    _josa_re = re.compile(
        r"(을|를|이|가|은|는|의|에|에서|으로|로|와|과|도|만|까지|부터|처럼|보다"
        r"|했다|한다|하는|하고|하며|해서|했고|하지|하던|합니다"
        r"|았다|었다|였다|이다|이었다|겠다|런지|든지)$"
    )
    stem_counts = {}
    for token in re.findall(r"[가-힣]{2,}", text):
        stem = _josa_re.sub("", token)
        if len(stem) < 2:
            continue
        if stem in _PROSE_SCAN_STOPWORDS:
            continue
        if any(stem.startswith(n) or n.startswith(stem) for n in name_stems if n):
            continue
        stem_counts[stem] = stem_counts.get(stem, 0) + 1

    repeated = [
        {"stem": s, "count": c}
        for s, c in sorted(stem_counts.items(), key=lambda x: -x[1])
        if c >= 8
    ][:10]

    total_flags = sum(v["count"] for v in violations)
    return {
        "violations": violations,
        "repeated_stems": repeated,
        "total_flags": total_flags,
        "clean": (not violations and not repeated),
    }


def format_prose_scan_report(scan_result: dict, ep_number: int = 0) -> str:
    """스캐너 결과를 작가용 마크다운 리포트로 변환.

    UI 표시와 REDO 프롬프트 주입에 공용으로 쓴다.
    """
    if not scan_result or scan_result.get("clean"):
        return "✅ 문체 스캐너: 검출 없음 (A23·A24 기준 통과)"

    lines = [f"### 🧹 문체 스캐너 검출 결과" + (f" (EP{ep_number})" if ep_number else "")]

    for v in scan_result.get("violations", []):
        lines.append(f"\n**[{v['rule']}] {v['label']}** — {v['count']}회")
        for s in v.get("samples", []):
            lines.append(f"- `{s}`")

    repeated = scan_result.get("repeated_stems", [])
    if repeated:
        lines.append("\n**[A24 참고] 고빈도 반복 어간** (버릇·소품 과잉 반복 의심 — 작가 판단 필요)")
        for r in repeated:
            lines.append(f"- \"{r['stem']}\" × {r['count']}회")

    lines.append("\n> 스캐너는 검출만 합니다. 수정 여부와 방식은 작가의 판단입니다.")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════
# 1020 타깃·장르 정량 진단 (A25·A26) — v2.3.0 신규
# LLM 미사용. 대사 비율·주인공 대사 수·무공 시전 유무를 카운팅으로 검출.
# ═══════════════════════════════════════════════════

# 무공 시전 감지 키워드 (초식·시전 동작)
_MARTIAL_ACTION_WORDS = [
    "초식", "심법", "내공", "진기", "단전", "혈도", "경지", "기경", "화경",
    "절정", "현경", "삼류", "이류", "일류", "갑자", "운기", "호신강기",
    "검기", "검강", "장법", "권법", "지법", "신법", "보법", "검법", "도법",
]
# 격돌·타격 감지 키워드
_CLASH_WORDS = [
    "부딪", "맞부딪", "튕겨", "튕기", "베었", "베어", "찔러", "찔렀",
    "꿰뚫", "내리쳤", "휘둘렀", "때렸", "쳤다", "박혔", "꺾었", "걷어",
    "날아갔", "쓰러졌", "피가", "충격파", "격돌",
]

# 관찰·묘사 문단 판정에서 대사로 취급할 시작 문자
_DIALOG_OPENERS = ('"', '“', "'", "‘", "「", "『")


def diagnose_youth_target(text: str, character_bible: dict = None,
                          is_youth: bool = True, ep_number: int = 0) -> dict:
    """
    A25(1020 경량화) + A26(무협 액기스) 정량 진단.

    LLM 미사용 → 재현성 100%. 검출만 하고 수정하지 않는다.

    Args:
        text: 회차 본문
        character_bible: 주인공 이름 추출용
        is_youth: 1020 타깃 공식 여부 (A25 기준 적용 여부)
        ep_number: 회차 번호 (1~2화면 A26 강하게 적용)

    Returns:
        {"metrics": {...}, "issues": [{"rule","label","detail"}], "clean": bool}
    """
    if not text or not isinstance(text, str):
        return {"metrics": {}, "issues": [], "clean": True}

    paras = [p.strip() for p in text.split("\n") if p.strip()]
    if not paras:
        return {"metrics": {}, "issues": [], "clean": True}

    # 회차 제목 줄 제외
    body_paras = [p for p in paras if not re.match(r"^\*?\*?EP\s*\d+", p)]

    dialog_paras = [p for p in body_paras if p.startswith(_DIALOG_OPENERS)]
    body_chars = sum(len(p) for p in body_paras) or 1
    dialog_chars = sum(len(p) for p in dialog_paras)
    dialog_ratio = round(100.0 * dialog_chars / body_chars, 1)

    # 주인공 대사 수는 측정하지 않는다.
    # 단역이 바이블에 없으면 화자 식별이 불가능해 추정치가 항상 과대 계상된다
    # (사고 패턴 I: 측정 불가한 값을 숫자로 표시하면 그 자체가 거짓 신호).
    # 대신 신뢰 계산이 가능한 대사 비율·대사 밀도로 같은 문제를 포착한다.
    # A25의 "주인공 대사 12마디" 기준은 집필 프롬프트의 생성 지시로만 사용한다.

    # 대사 밀도 (1,000자당 대사 문단 수) — 추정 없이 계산되는 신뢰 지표
    dialog_density = round(1000.0 * len(dialog_paras) / body_chars, 1)

    # 관찰·묘사 연속 문단 최대 길이
    max_narration_run = 0
    run = 0
    for p in body_paras:
        if p.startswith(_DIALOG_OPENERS) or p == "*":
            run = 0
        else:
            run += 1
            max_narration_run = max(max_narration_run, run)

    # 무공 시전·격돌 검출
    martial_hits = [w for w in _MARTIAL_ACTION_WORDS if w in text]
    clash_hits = [w for w in _CLASH_WORDS if w in text]

    metrics = {
        "dialog_ratio": dialog_ratio,
        "dialog_paragraphs": len(dialog_paras),
        "dialog_density": dialog_density,
        "max_narration_run": max_narration_run,
        "martial_keywords": len(martial_hits),
        "clash_keywords": len(clash_hits),
        "total_chars": body_chars,
    }

    issues = []

    if is_youth:
        if dialog_ratio < 30:
            issues.append({
                "rule": "A25",
                "label": "대사 비율 미달",
                "detail": f"대사 글자 비율 {dialog_ratio}% (기준 30% 이상). "
                          f"묘사 편중으로 1020 타깃 이탈 위험.",
            })
        if dialog_density < 8:
            issues.append({
                "rule": "A25",
                "label": "대사 밀도 부족",
                "detail": f"1,000자당 대사 문단 {dialog_density}개 (기준 8개 이상). "
                          f"인물이 말하지 않고 서술자만 관찰하는 구조.",
            })
        if max_narration_run >= 4:
            issues.append({
                "rule": "A25",
                "label": "관찰·묘사 문단 연속",
                "detail": f"묘사 문단 최대 {max_narration_run}개 연속 "
                          f"(기준 3개 미만). 대사·행동을 끼울 것.",
            })

    if len(martial_hits) < 2:
        issues.append({
            "rule": "A26",
            "label": "무협 액기스 부족",
            "detail": f"무공·경지·내공 관련 표현 {len(martial_hits)}종 검출 "
                      f"(기준 2종 이상). 초식명 명시 시전이 필요.",
        })
    if not clash_hits and ep_number in (1, 2):
        issues.append({
            "rule": "A26",
            "label": "격돌·타격 부재",
            "detail": "무기 격돌 또는 실제 타격 묘사가 검출되지 않음. "
                      "검이 뽑히고 부딪히지 않는 1화는 장르 계약 위반.",
        })

    return {"metrics": metrics, "issues": issues, "clean": not issues}


def format_youth_diagnosis_report(diag: dict, ep_number: int = 0) -> str:
    """1020 타깃·장르 진단 결과를 작가용 마크다운으로 변환."""
    if not diag or not diag.get("metrics"):
        return "진단 대상 본문이 없습니다."

    m = diag["metrics"]
    lines = [f"### 🎯 1020 타깃·장르 진단" + (f" (EP{ep_number})" if ep_number else "")]
    lines.append("")
    lines.append("| 지표 | 측정값 | 기준 |")
    lines.append("|---|---|---|")
    lines.append(f"| 대사 글자 비율 | {m['dialog_ratio']}% | 30% 이상 |")
    lines.append(f"| 대사 밀도 (1,000자당) | {m['dialog_density']}개 | 8개 이상 |")
    lines.append(f"| 묘사 문단 최대 연속 | {m['max_narration_run']}개 | 3개 미만 |")
    lines.append(f"| 무공·경지 표현 | {m['martial_keywords']}종 | 2종 이상 |")
    lines.append(f"| 격돌·타격 표현 | {m['clash_keywords']}종 | 1종 이상 |")

    if diag.get("clean"):
        lines.append("\n✅ A25·A26 기준 통과")
        return "\n".join(lines)

    lines.append("")
    for it in diag.get("issues", []):
        lines.append(f"**[{it['rule']}] {it['label']}**")
        lines.append(f"- {it['detail']}")

    lines.append("\n> 진단은 검출만 합니다. 수정 여부와 방식은 작가의 판단입니다.")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════
# 초식 일관성 정적 검사 (A27·A28) — v2.5.0 신규
# LLM 미사용. 초식 바이블과 본문을 대조해 검출만 한다.
# 수정은 작가 영역이다 (설계 원칙 K).
# ═══════════════════════════════════════════════════

# 무협 관용 초식명 — 작가 설정 자리에 끼어들면 A28 위반
# (아미고 사고: 화산장풍·당랑연검술 자리에 자하신공·태극혼원공이
#  들어와 작품의 한자 차별화 장치가 지워졌다)
_GENERIC_ART_NAMES = [
    "자하신공", "태극혼원공", "구양신공", "구음진경", "건곤대나이",
    "능파미보", "일양지", "항룡십팔장", "타구봉법", "육맥신검",
    "북명신공", "선천공", "천마신공", "흡성대법", "이화접목",
    "벽사검법", "매화검법", "천화난사", "홍련참", "혈마공",
]

# 초식명 후보 추출 — 한글 2~6자 + 무공 접미어
_ART_SUFFIXES = (
    "신공", "심법", "검법", "도법", "장법", "권법", "지법", "보법",
    "신법", "각법", "창법", "편법", "검술", "도술", "창술", "장풍",
    "진경", "비급", "대법", "절기", "초식", "검결", "검진", "진법",
)
_ART_CANDIDATE_RE = re.compile(
    r"([가-힣]{2,6}(?:" + "|".join(_ART_SUFFIXES) + r"))"
)
# 한자 병기 초식명 — 한글(한자) 형태
_ART_WITH_HANJA_RE = re.compile(r"([가-힣]{2,8})\s*\(([\u4e00-\u9fff]{2,8})\)")


def _collect_bible_terms(martial_bible: dict) -> dict:
    """초식 바이블에서 용어를 종류별로 수집.

    Returns:
        {"arts": set, "artifacts": set, "weapons": set,
         "locked": set, "all": set, "display": {정규화형: 원문}}
    """
    out = {"arts": set(), "artifacts": set(), "weapons": set(),
           "context": set(),
           "locked": set(), "all": set(), "display": {}}
    if not isinstance(martial_bible, dict):
        return out

    def _add(bucket, raw):
        if not raw or not isinstance(raw, str):
            return
        raw = raw.strip()
        if not raw:
            return
        out[bucket].add(raw)
        out["all"].add(raw)
        # 한자 병기를 떼어낸 한글 표기도 별칭으로 등록
        # v2.6.0: 1자 별칭은 등록하지 않는다.
        #   "기(氣)"의 base "기"가 기운·기세·경기 등 모든 음절에 걸려
        #   art_mentions가 과대 계상됐다 (엔진 EP2가 실제 병기 0회인데
        #   "기(氣)x31"로 잡힌 거짓 신호 — 사고 패턴 I 계열)
        base = re.sub(r"\s*\([^)]*\)\s*", "", raw).strip()
        if base and base != raw and len(base) >= 2:
            out[bucket].add(base)
            out["all"].add(base)
            out["display"][base] = raw
        out["display"].setdefault(raw, raw)

    for item in martial_bible.get("power_taxonomy") or []:
        if isinstance(item, dict):
            _add("arts", item.get("name"))
    for grp in martial_bible.get("faction_arts") or []:
        if not isinstance(grp, dict):
            continue
        # v2.7.0: signature·training은 서술 필드다. 초식명 버킷에
        #   넣으면 문장이 초식으로 등록돼 art_mentions가 과대 계상되고
        #   A28 철자 고정 목록 40칸을 잡아먹는다. (실측 오염 8건)
        #   초식명 형식을 통과한 것만 등록하고, 나머지는 context로 보낸다.
        for _fld in ("signature", "training"):
            _v = grp.get(_fld)
            if _is_valid_art_name(_v):
                _add("arts", _v)
            elif isinstance(_v, str) and _v.strip():
                out["context"].add(_v.strip())
        for art in grp.get("arts") or []:
            if isinstance(art, dict):
                _add("arts", art.get("name"))
    for item in martial_bible.get("artifacts") or []:
        if isinstance(item, dict):
            _add("artifacts", item.get("name"))
    for item in martial_bible.get("weapons") or []:
        if isinstance(item, dict):
            _add("weapons", item.get("name"))
    for item in martial_bible.get("forbidden") or []:
        if isinstance(item, dict):
            # v2.7.0: forbidden.name도 서술구가 들어온다 ("심각한 부상 유발")
            if _is_valid_art_name(item.get("name")):
                _add("arts", item.get("name"))
    for t in martial_bible.get("author_locked_terms") or []:
        _add("locked", t if isinstance(t, str) else "")
    return out


def scan_martial_consistency(text: str, martial_bible: dict = None,
                             ep_number: int = 0) -> dict:
    """A27(초식 일관성) + A28(작가 설정 우선) 정적 검사 — v2.5.0 신규.

    LLM을 쓰지 않으므로 재현성이 100%다. 검출만 하고 수정하지 않는다.

    [왜 필요한가]
    v2.4.0이 초식 바이블과 A28 룰을 만들었지만, 룰을 지켰는지
    확인하는 수단이 없었다. 아미고 EP1은 초식명 0개·무공 시전
    0회였는데 이를 알아내는 데 사람의 통독이 필요했다.

    Args:
        text: 회차 본문
        martial_bible: 초식 바이블 (없으면 관용명 검출만 수행)
        ep_number: 회차 번호 (리포트 표기용)

    Returns:
        {
          "has_bible": bool,
          "bible_used": [{"term","count"}],      # 바이블 초식 사용 현황
          "bible_unused": [str],                 # 이 회차에 안 쓰인 바이블 초식
          "generic_hits": [{"term","count","samples"}],   # A28 관용명 위반
          "unknown_arts": [{"term","count","samples"}],   # 바이블 외 초식 후보
          "hanja_pairs": [{"term","count"}],     # 한자 병기 (첫 등장 초과 검출)
          "locked_missing": [str],               # 고정 용어 중 미등장
          "art_mentions": int,                   # 초식 언급 총량
          "flags": [str],                        # 요약 경보
          "clean": bool,
        }
    """
    result = {
        "has_bible": bool(martial_bible),
        "bible_used": [], "bible_unused": [],
        "generic_hits": [], "unknown_arts": [],
        "hanja_pairs": [], "locked_missing": [],
        "art_mentions": 0, "flags": [], "clean": True,
    }
    if not text or not isinstance(text, str):
        return result

    terms = _collect_bible_terms(martial_bible or {})

    # ── 1) 바이블 초식 사용 현황 ──
    used, unused = [], []
    for t in sorted(terms["arts"], key=len, reverse=True):
        # v2.6.0: 1자 용어는 음절 단위 오탐을 만들므로 계측 제외
        if len(t) < 2:
            continue
        c = text.count(t)
        if c > 0:
            used.append({"term": terms["display"].get(t, t), "count": c})
        else:
            unused.append(terms["display"].get(t, t))
    # 별칭 중복 정리 (한자 병기형과 한글형이 함께 잡힌 경우)
    seen = set()
    dedup_used = []
    for u in sorted(used, key=lambda x: -x["count"]):
        base = re.sub(r"\s*\([^)]*\)\s*", "", u["term"]).strip()
        if base in seen:
            continue
        seen.add(base)
        dedup_used.append(u)
    result["bible_used"] = dedup_used
    result["bible_unused"] = [
        u for u in unused
        if re.sub(r"\s*\([^)]*\)\s*", "", u).strip() not in seen
    ][:20]
    result["art_mentions"] = sum(u["count"] for u in dedup_used)

    # ── 2) A28 관용 초식명 검출 ──
    for g in _GENERIC_ART_NAMES:
        c = text.count(g)
        if c > 0 and g not in terms["all"]:
            result["generic_hits"].append({
                "term": g, "count": c,
                "samples": _find_lines_with(text, g)[:2],
            })

    # ── 3) 바이블에 없는 초식 후보 검출 ──
    cand_counts = {}
    for m in _ART_CANDIDATE_RE.findall(text):
        cand_counts[m] = cand_counts.get(m, 0) + 1
    for cand, c in sorted(cand_counts.items(), key=lambda x: -x[1]):
        if cand in terms["all"]:
            continue
        if any(cand in t or t in cand for t in terms["all"]):
            continue  # 바이블 용어의 부분 문자열
        if cand in [g["term"] for g in result["generic_hits"]]:
            continue  # 관용명으로 이미 보고
        result["unknown_arts"].append({
            "term": cand, "count": c,
            "samples": _find_lines_with(text, cand)[:2],
        })
    result["unknown_arts"] = result["unknown_arts"][:12]

    # ── 4) 한자 병기 과다 (A10 글로벌 친화 — 첫 등장만 허용) ──
    hanja = {}
    for kor, han in _ART_WITH_HANJA_RE.findall(text):
        key = f"{kor}({han})"
        hanja[key] = hanja.get(key, 0) + 1
    total_hanja = sum(hanja.values())
    result["hanja_pairs"] = [
        {"term": k, "count": v} for k, v in sorted(hanja.items(), key=lambda x: -x[1])
        if v > 1
    ][:10]

    # ── 5) 고정 용어 중 미등장 (참고용 — 위반이 아님) ──
    if terms["locked"]:
        result["locked_missing"] = [
            t for t in sorted(terms["locked"])
            if text.count(t) == 0
            and text.count(re.sub(r"\s*\([^)]*\)\s*", "", t).strip()) == 0
        ][:20]

    # ── 6) 요약 경보 ──
    if result["generic_hits"]:
        result["flags"].append(
            "A28 위반 — 무협 관용 초식명이 등장합니다. 작가 설정 초식으로 교체가 필요합니다."
        )
    if result["has_bible"] and result["art_mentions"] == 0:
        result["flags"].append(
            "A26·A28 경보 — 바이블 초식이 한 번도 등장하지 않습니다. 무공 장면이 추상 묘사로 처리됐을 가능성이 큽니다."
        )
    if len(result["unknown_arts"]) >= 3:
        result["flags"].append(
            f"A27 주의 — 바이블에 없는 초식 후보가 {len(result['unknown_arts'])}종 검출됐습니다. 즉흥 작명 여부를 확인해 주십시오."
        )
    if total_hanja < 4:
        result["flags"].append(
            f"A15·A29 경보 — 한자 병기 {total_hanja}회. 고유명사 병기가 부족해 "
            f"무협 장르로 읽히지 않을 위험이 있습니다 (정상 8~15회)."
        )
    elif total_hanja > 22:
        result["flags"].append(
            f"한자 병기 {total_hanja}회 — 총량 과다. 같은 용어의 반복 병기 여부를 "
            f"확인해 주십시오 (재등장 시 한글만)."
        )
    if not result["has_bible"]:
        result["flags"].append(
            "초식 바이블이 없습니다. STEP 1에서 추출하면 일관성 검사가 정밀해집니다."
        )

    result["clean"] = not result["generic_hits"] and not result["flags"]
    return result


def format_martial_scan_report(scan: dict, ep_number: int = 0) -> str:
    """초식 일관성 검사 결과를 작가용 마크다운 리포트로 변환.

    UI 표시와 REDO 프롬프트 주입에 공용으로 쓴다.
    """
    if not scan:
        return ""
    if scan.get("clean"):
        return "✅ 초식 일관성: 검출 없음 (A27·A28 기준 통과)"

    lines = ["### ⚔️ 초식 일관성 검사" + (f" (EP{ep_number})" if ep_number else "")]

    for f in scan.get("flags", []):
        lines.append(f"\n- {f}")

    gh = scan.get("generic_hits") or []
    if gh:
        lines.append("\n**[A28] 무협 관용 초식명 검출** — 작가 설정 초식으로 교체 필요")
        for g in gh:
            lines.append(f"- \"{g['term']}\" × {g['count']}회")
            for s in g.get("samples", []):
                lines.append(f"    · `{s}`")

    used = scan.get("bible_used") or []
    if used:
        lines.append("\n**바이블 초식 사용 현황**")
        lines.append(", ".join(f"{u['term']} ×{u['count']}" for u in used[:12]))

    ua = scan.get("unknown_arts") or []
    if ua:
        lines.append("\n**[A27] 바이블에 없는 초식 후보** (즉흥 작명 의심 — 작가 판단 필요)")
        for u in ua:
            lines.append(f"- \"{u['term']}\" × {u['count']}회")
            for s in u.get("samples", []):
                lines.append(f"    · `{s}`")

    hp = scan.get("hanja_pairs") or []
    if hp:
        lines.append("\n**한자 병기 반복** (첫 등장만 병기 원칙)")
        for h in hp:
            lines.append(f"- {h['term']} × {h['count']}회")

    lines.append("\n> 검사는 검출만 합니다. 수정 여부와 방식은 작가의 판단입니다.")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════
# 장르 밀도 정적 검사 (A29·A30·A31) — v2.6.0 신규
#
# [왜 필요한가]
# 아미고 EP1·EP2에서 문장·감정·대사가 모두 우수한데 무협으로
# 읽히지 않는 사고가 발생했다. 원인은 무공 명명 0종·한자 병기
# 0회·기 어휘 0회였다. 그런데 기존 5축 검수는 그 회차에
# MISE_EN_SCENE 90점을 줬다. 장르 소실을 탐지할 수단이 없었다.
#
# 이 스캐너는 A29 쿼터표를 그대로 계측한다. LLM 미사용,
# 재현성 100%. 검출만 하고 본문은 수정하지 않는다 (설계 원칙 K).
# ═══════════════════════════════════════════════════

# A29 쿼터 임계값 — (EP1~EP4 강화값, EP5 이후 기본값)
WUXIA_DENSITY_QUOTAS = [
    ("named_arts",  "이름 붙은 무공·초식", 5, 3),
    ("hanja",       "고유명사 한자 병기",   8, 6),
    ("three_beat",  "3박자 완주 (명명→시연→해설)", 2, 1),
    ("factions",    "문파·계보 귀속",       3, 2),
    ("neigong",     "내공·기 가시화",       4, 3),
    ("onomatopoeia", "타격·풍압 의성어",     3, 2),
    ("realms",      "경지·서열 노출",       2, 1),
]

# 명명 회피 관용구 — A29 절대 금지 항목
_NAMING_EVASION_PATTERNS = [
    "초식이라 부를 것도", "초식이라고 할 것도", "이름을 붙일 것도",
    "이름이 없었다", "이름도 없었다", "그냥 됐다", "그냥 잡혔",
    "그냥 되는", "무공이라 할 수도", "이름 없는",
]


def scan_wuxia_density(text: str, ep_number: int = 0,
                       martial_bible: dict = None) -> dict:
    """A29~A31 장르 밀도 정량 검사 — v2.6.0 신규.

    Args:
        text: 회차 본문
        ep_number: 회차 번호. 1~4면 도입부 강화 임계값을 적용한다.
        martial_bible: 초식 바이블 (있으면 무공·문파 판정 정확도 상승)

    Returns:
        {
          "ep_number": int,
          "is_opening": bool,             # EP1~EP4 여부
          "metrics": {키: 값},
          "quotas": [{"key","label","value","target","ok"}],
          "achieved": int,                # 충족 쿼터 수 (0~7)
          "total": 7,
          "grade": "PASS" | "WARN" | "FAIL",
          "named_arts": [str],            # 검출된 무공명
          "evasion_hits": [{"phrase","samples"}],   # 명명 회피 관용구
          "flags": [str],
        }
    """
    result = {
        "ep_number": ep_number,
        "is_opening": bool(1 <= ep_number <= 4),
        "metrics": {}, "quotas": [], "achieved": 0,
        "total": len(WUXIA_DENSITY_QUOTAS),
        "grade": "FAIL", "named_arts": [], "evasion_hits": [], "flags": [],
    }
    if not text or not isinstance(text, str):
        return result

    terms = _collect_bible_terms(martial_bible or {})

    # ── ① 이름 붙은 무공 ──
    named = _extract_named_arts(text, terms.get("arts"))
    result["named_arts"] = named
    m_named = len(named)

    # ── ② 고유명사 한자 병기 (총 출현 수) ──
    hanja_all = _HANJA_PAIR_RE.findall(text)
    m_hanja = len(hanja_all)
    # 반복 병기 계측 (A15 — 줄여야 할 것은 총량이 아니라 반복이다)
    pair_counts = {}
    for kor, han in hanja_all:
        pair_counts[f"{kor}({han})"] = pair_counts.get(f"{kor}({han})", 0) + 1
    repeated = {k: v for k, v in pair_counts.items() if v > 1}

    # ── ③ A30 3박자 완주 ──
    beat_detail = _count_three_beat(text, named)
    m_three = len(beat_detail)

    # ── ④ 문파·계보 귀속 ──
    faction_pool = set(_GENERIC_FACTIONS)
    for grp in (martial_bible or {}).get("faction_arts") or []:
        if isinstance(grp, dict) and grp.get("faction"):
            for piece in re.split(r"[/·,]", str(grp["faction"])):
                piece = re.sub(r"\s*\([^)]*\)\s*", "", piece).strip()
                if len(piece) >= 2:
                    faction_pool.add(piece)
    factions_found = sorted({f for f in faction_pool if f in text})
    m_factions = len(factions_found)

    # ── ⑤ 내공·기 가시화 ──
    m_neigong = sum(text.count(w) for w in _NEIGONG_WORDS)

    # ── ⑥ 의성어 ──
    onom = 0
    for w in _ONOMATOPOEIA:
        onom += len(re.findall(r"(?<![가-힣])" + re.escape(w) + r"(?![가-힣])", text))
    quoted = [q for q in _QUOTED_SHORT_RE.findall(text)
              if not q.endswith(("다", "요", "까", "네", "죠", "야", "군"))]
    m_onom = max(onom, len(quoted)) if quoted else onom

    # ── ⑦ 경지·서열 ──
    realm_found = sorted({w for w in _REALM_WORDS if w in text})
    m_realms = sum(text.count(w) for w in realm_found)

    result["metrics"] = {
        "named_arts": m_named, "hanja": m_hanja, "three_beat": m_three,
        "factions": m_factions, "neigong": m_neigong,
        "onomatopoeia": m_onom, "realms": m_realms,
        "hanja_repeated": repeated,
        "factions_found": factions_found,
        "three_beat_arts": beat_detail,
        "realm_words": realm_found,
    }

    # ── 쿼터 판정 ──
    for key, label, open_t, base_t in WUXIA_DENSITY_QUOTAS:
        target = open_t if result["is_opening"] else base_t
        value = result["metrics"].get(key, 0)
        ok = value >= target
        result["quotas"].append({
            "key": key, "label": label, "value": value,
            "target": target, "ok": ok,
        })
        if ok:
            result["achieved"] += 1

    # ── 명명 회피 관용구 검출 ──
    for p in _NAMING_EVASION_PATTERNS:
        if p in text:
            result["evasion_hits"].append({
                "phrase": p, "samples": _find_lines_with(text, p)[:2],
            })

    # ── 등급 ──
    total = result["total"]
    ach = result["achieved"]
    if ach >= total - 1:
        result["grade"] = "PASS"
    elif ach >= total - 3:
        result["grade"] = "WARN"
    else:
        result["grade"] = "FAIL"

    # 이름 붙은 무공 0종은 다른 지표와 무관하게 FAIL
    if m_named == 0:
        result["grade"] = "FAIL"

    # ── 경보 ──
    if m_named == 0:
        result["flags"].append(
            "A29 치명 위반 — 이름 붙은 무공이 0종입니다. 무공 장면이 "
            "이름 없는 격투로 처리됐습니다. 이 회차는 무협으로 읽히지 않습니다."
        )
    elif result["is_opening"] and m_named < 5:
        result["flags"].append(
            f"A29 위반 — 도입 4화 구간인데 이름 붙은 무공이 {m_named}종입니다 "
            f"(목표 5종). 독자는 1~4화에서 장르를 판정합니다."
        )
    if m_hanja < 4:
        result["flags"].append(
            f"A15·A29 위반 — 한자 병기 {m_hanja}회. 고유명사 병기가 부족합니다 "
            f"(정상 8~15회)."
        )
    if m_three == 0:
        result["flags"].append(
            "A30 위반 — 3박자 완주 0회. 무공의 원리·문파 귀속·장단점을 "
            "설명하는 해설이 없습니다. 무협 독자의 과금 지점이 비어 있습니다."
        )
    if result["evasion_hits"]:
        result["flags"].append(
            "A29 금지 표현 — 명명 회피 관용구가 검출됐습니다. 무공에 이름을 "
            "붙이거나, 다른 인물이 이름을 붙여주는 대사를 넣어 주십시오."
        )
    if repeated:
        top = ", ".join(f"{k}×{v}" for k, v in
                        sorted(repeated.items(), key=lambda x: -x[1])[:5])
        result["flags"].append(
            f"A15 반복 병기 — 재등장 시에는 한글만 씁니다: {top}"
        )
    if m_factions <= 1:
        result["flags"].append(
            f"A31 주의 — 문파·계보 언급이 {m_factions}곳입니다. 우리 편만 "
            f"나오면 강호가 좁아집니다."
        )

    return result


def format_wuxia_density_report(scan: dict, ep_number: int = 0) -> str:
    """장르 밀도 검사 결과를 작가용 마크다운 리포트로 변환.

    UI 표시와 REDO 프롬프트 주입에 공용으로 쓴다.
    """
    if not scan:
        return ""

    ep = scan.get("ep_number") or ep_number
    grade = scan.get("grade", "?")
    icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "🚨"}.get(grade, "•")
    scope = "도입 4화 강화 기준" if scan.get("is_opening") else "일반 회차 기준"

    lines = [
        f"### {icon} 무협 장르 밀도 (A29~A31)" + (f" — EP{ep}" if ep else ""),
        f"**{grade}** · 쿼터 {scan.get('achieved', 0)}/{scan.get('total', 7)} 충족 · {scope}",
        "",
        "| 항목 | 실측 | 목표 | 판정 |",
        "|---|---|---|---|",
    ]
    for q in scan.get("quotas", []):
        mark = "○" if q["ok"] else "**✗**"
        lines.append(f"| {q['label']} | {q['value']} | {q['target']} | {mark} |")

    for f in scan.get("flags", []):
        lines.append(f"\n- {f}")

    named = scan.get("named_arts") or []
    if named:
        lines.append(f"\n**검출된 무공명 ({len(named)}종)**")
        lines.append(", ".join(named[:15]))
    else:
        lines.append("\n**검출된 무공명** — 없음")

    m = scan.get("metrics") or {}
    if m.get("three_beat_arts"):
        lines.append("\n**3박자 완주로 판정된 무공**")
        lines.append(", ".join(m["three_beat_arts"][:10]))
    if m.get("factions_found"):
        lines.append("\n**언급된 문파·계보**")
        lines.append(", ".join(m["factions_found"][:12]))

    ev = scan.get("evasion_hits") or []
    if ev:
        lines.append("\n**명명 회피 관용구 검출**")
        for e in ev:
            lines.append(f"- \"{e['phrase']}\"")
            for s in e.get("samples", []):
                lines.append(f"    · `{s}`")

    lines.append("\n> 검사는 검출만 합니다. 수정 여부와 방식은 작가의 판단입니다.")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════
# 무공 대전 (Martial Codex) 게이트 — v2.7.0 신규
#
# 성장하는 사전은 오염되면 50화가 전부 오염된다. 등록 게이트 7종으로
# 막는다. 자동 등록은 없다 — 전부 작가 승인 후 병합이다.
# ═══════════════════════════════════════════════════

# 게이트 1 — 무협 관용명 차단 목록 (작품 고유성 보호)
_CODEX_BANNED_NAMES = set(_GENERIC_ART_NAMES) | {
    "구음백골조", "금강불괴", "역근경", "세수경", "소요유", "능공허도",
    "천산절맥", "만천화우", "낙영신검", "천외비선", "무영각", "철사장",
    "십단금", "대력금강지", "혼원벽력수", "칠상권", "낙화장",
}

# 게이트 3 — 등록 필수 필드
_CODEX_REQUIRED_FIELDS = ("name", "faction", "tier", "principle", "cost")

# 무공명 형식 — 조사·서술어가 붙은 문장은 초식명이 아니다
_SENTENCE_MARKERS = (
    "한다.", "했다.", "이다.", "된다.", "있다.", "없다.", "된 ", "하는 ",
    "에서", "에게", "으로", "를 ", "을 ", "이 ", "가 ", "는 ", "와 ", "과 ",
)


def _codex_name_parts(name: str) -> tuple:
    """무공명을 (한글, 한자)로 분해."""
    if not name:
        return "", ""
    m = re.match(r"\s*([^()（）]+)[\(（]?([\u4e00-\u9fff]*)[\)）]?\s*$", str(name))
    if not m:
        return str(name).strip(), ""
    return m.group(1).strip(), (m.group(2) or "").strip()


def _is_valid_art_name(name: str) -> bool:
    """초식명 형식 판정 — 문장·설명문 배제."""
    if not name or not isinstance(name, str):
        return False
    kor, _han = _codex_name_parts(name)
    if not (2 <= len(kor) <= 12):
        return False
    if any(mk in name for mk in _SENTENCE_MARKERS):
        return False
    if re.search(r"[.,!?·…]", kor):
        return False
    # 초식명에는 공백이 없다. "심각한 부상 유발" 같은 서술구를 배제한다.
    if " " in kor and not re.fullmatch(r"[A-Za-z0-9\s]+", kor):
        return False
    return bool(re.fullmatch(r"[가-힣A-Za-z0-9\s]+", kor))


def _jamo_similarity(a: str, b: str) -> float:
    """두 무공명의 유사도 (0.0~1.0). 게이트 2용."""
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    return inter / max(len(sa), len(sb))


def sanitize_martial_bible(martial_bible: dict) -> dict:
    """바이블 정화 — 문장형 오염 항목 격리 (v2.7.0 신규).

    [왜 필요한가]
    기획서 추출 과정에서 서술 문장이 초식명으로 등재됐다.
    아미고 실측: "유정이 두 가문의 비법을 총망라한 약을 조제했다.",
    "장웨이가 소림무술을 지도한다.", "심각한 부상 유발" 등 7~8건.
    이 항목들이 A28 철자 고정 목록 40칸을 잡아먹고 프롬프트에 실렸다.

    삭제하지 않고 _rejected로 격리한다. 작가가 되돌릴 수 있어야 한다.

    Returns:
        {"bible": 정화된 바이블, "rejected": [격리 항목], "report": str}
    """
    if not isinstance(martial_bible, dict):
        return {"bible": {}, "rejected": [], "report": "바이블 없음"}

    import copy
    mb = copy.deepcopy(martial_bible)
    rejected = []

    # power_taxonomy 정화
    tax = mb.get("power_taxonomy")
    if isinstance(tax, list):
        keep = []
        for it in tax:
            nm = (it or {}).get("name", "") if isinstance(it, dict) else ""
            if _is_valid_art_name(nm):
                keep.append(it)
            else:
                rejected.append({"where": "power_taxonomy", "name": nm, "item": it})
        mb["power_taxonomy"] = keep

    # faction_arts.arts 정화
    fa = mb.get("faction_arts")
    if isinstance(fa, list):
        for grp in fa:
            if not isinstance(grp, dict):
                continue
            arts = grp.get("arts")
            if not isinstance(arts, list):
                continue
            keep = []
            for it in arts:
                nm = (it or {}).get("name", "") if isinstance(it, dict) else ""
                if _is_valid_art_name(nm):
                    keep.append(it)
                else:
                    rejected.append({
                        "where": f"faction_arts/{grp.get('faction', '?')}",
                        "name": nm, "item": it,
                    })
            grp["arts"] = keep

    # author_locked_terms 정화
    locked = mb.get("author_locked_terms")
    if isinstance(locked, list):
        keep = []
        for t in locked:
            if _is_valid_art_name(str(t)):
                keep.append(t)
            else:
                rejected.append({"where": "author_locked_terms",
                                 "name": str(t), "item": t})
        mb["author_locked_terms"] = keep

    mb.setdefault("_rejected", [])
    mb["_rejected"].extend(rejected)

    lines = [f"### 🧹 바이블 정화 — {len(rejected)}건 격리"]
    if rejected:
        lines.append("초식명 형식이 아닌 항목을 `_rejected`로 옮겼습니다. 삭제하지 않았습니다.")
        lines.append("")
        for r in rejected[:15]:
            nm = (r["name"] or "")[:60]
            lines.append(f"- `{r['where']}` — {nm}")
    else:
        lines.append("오염 항목이 없습니다.")

    return {"bible": mb, "rejected": rejected, "report": "\n".join(lines)}


def _collect_codex_names(martial_bible: dict) -> dict:
    """현재 바이블의 무공명 색인 — {한글: 전체표기}."""
    idx = {}
    if not isinstance(martial_bible, dict):
        return idx
    for it in martial_bible.get("power_taxonomy") or []:
        if isinstance(it, dict) and it.get("name"):
            kor, _ = _codex_name_parts(it["name"])
            if kor:
                idx[kor] = it["name"]
    for grp in martial_bible.get("faction_arts") or []:
        if not isinstance(grp, dict):
            continue
        for it in grp.get("arts") or []:
            if isinstance(it, dict) and it.get("name"):
                kor, _ = _codex_name_parts(it["name"])
                if kor:
                    idx[kor] = it["name"]
    return idx


def validate_codex_entry(entry: dict, martial_bible: dict = None,
                         tier_counts: dict = None) -> dict:
    """무공 대전 항목 등록 게이트 7종 (v2.7.0 신규).

    Returns:
        {"ok": bool, "level": "PASS"|"WARN"|"BLOCK",
         "reasons": [str], "entry": 정규화된 항목}
    """
    reasons = []
    level = "PASS"
    if not isinstance(entry, dict):
        return {"ok": False, "level": "BLOCK", "reasons": ["항목 형식 오류"], "entry": {}}

    name = str(entry.get("name") or "").strip()
    kor, han = _codex_name_parts(name)
    idx = _collect_codex_names(martial_bible or {})

    # 게이트 1 — 무협 관용명 차단
    if kor in _CODEX_BANNED_NAMES:
        reasons.append(f"게이트1 관용명 — '{kor}'는 기존 무협 작품의 무공명입니다. 작품 고유성이 훼손됩니다.")
        level = "BLOCK"

    # 게이트 2 — 중복·유사 이름
    if kor and kor in idx:
        reasons.append(f"게이트2 중복 — '{kor}'는 이미 등재돼 있습니다 ({idx[kor]}).")
        level = "BLOCK"
    else:
        for ex_kor, ex_full in idx.items():
            if not ex_kor or ex_kor == kor:
                continue
            if kor and (kor in ex_kor or ex_kor in kor):
                reasons.append(f"게이트2 포함관계 — 기존 '{ex_full}'와 이름이 겹칩니다.")
                level = "BLOCK" if level != "BLOCK" else level
                break
            if _jamo_similarity(kor, ex_kor) >= 0.85:
                reasons.append(f"게이트2 유사 — 기존 '{ex_full}'와 매우 비슷합니다. 혼동 위험.")
                level = "WARN" if level == "PASS" else level
                break

    # 게이트 3 — 필수 필드
    missing = [f for f in _CODEX_REQUIRED_FIELDS
               if not str(entry.get(f) or "").strip()]
    if missing:
        label = {"name": "무공명", "faction": "문파", "tier": "등급",
                 "principle": "원리", "cost": "대가"}
        reasons.append(
            "게이트3 필수 필드 누락 — "
            + ", ".join(label.get(m, m) for m in missing)
            + ". 원리·대가가 없으면 A30 3박자 해설을 쓸 수 없습니다."
        )
        level = "BLOCK"

    # 게이트 4 — 한자 철자 충돌
    if kor and han:
        for ex_kor, ex_full in idx.items():
            if ex_kor != kor:
                continue
            _, ex_han = _codex_name_parts(ex_full)
            if ex_han and ex_han != han:
                reasons.append(
                    f"게이트4 한자 충돌 — 같은 '{kor}'인데 한자가 다릅니다: "
                    f"기존 {ex_han} / 신규 {han}"
                )
                level = "BLOCK"

    # 게이트 5 — 등급 정원
    tier = str(entry.get("tier") or "").strip()
    faction = str(entry.get("faction") or "").strip()
    if tier and tier_counts is not None:
        try:
            from prompt import MARTIAL_CODEX_TIERS
            quota = MARTIAL_CODEX_TIERS.get(tier, {}).get("quota_per_faction")
        except Exception:
            quota = None
        if quota:
            used = (tier_counts.get(faction, {}) or {}).get(tier, 0)
            if used >= quota:
                reasons.append(
                    f"게이트5 정원 초과 — {faction} {tier} 등급이 이미 {used}종입니다 "
                    f"(정원 {quota}). 무공의 무게는 희소성에서 나옵니다."
                )
                level = "WARN" if level == "PASS" else level

    # 게이트 6 — 이름 형식
    if not _is_valid_art_name(name):
        reasons.append(f"게이트6 이름 형식 — '{name[:40]}'는 초식명 형식이 아닙니다.")
        level = "BLOCK"

    # 게이트 7 — 출처 태그 (자동 부여)
    norm = dict(entry)
    norm.setdefault("source", "expansion")
    norm.setdefault("origin_ep", 0)
    norm["name"] = name

    return {"ok": level != "BLOCK", "level": level,
            "reasons": reasons, "entry": norm}


def merge_martial_codex(martial_bible: dict, new_entries: list,
                        faction: str = "", snapshot: bool = True) -> dict:
    """검증 통과 항목을 바이블에 병합 (v2.7.0 신규).

    병합 직전 바이블 스냅샷을 _snapshots에 보존한다 (보안책 6 — 롤백).
    자동 호출 금지. 작가가 승인한 항목만 넘긴다 (코드 작업 규칙 7).
    """
    import copy
    from datetime import datetime

    if not isinstance(martial_bible, dict):
        martial_bible = {}
    mb = copy.deepcopy(martial_bible)

    if snapshot:
        snaps = mb.get("_snapshots") or []
        lean = {k: v for k, v in martial_bible.items() if not k.startswith("_")}
        snaps.append({
            "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note": f"{faction} 확장 병합 전",
            "bible": lean,
        })
        mb["_snapshots"] = snaps[-5:]   # 최근 5개만 보존

    # 등급 정원 현황 집계
    tier_counts = {}
    for grp in mb.get("faction_arts") or []:
        if not isinstance(grp, dict):
            continue
        fac = str(grp.get("faction") or "").strip()
        tier_counts.setdefault(fac, {})
        for a in grp.get("arts") or []:
            if isinstance(a, dict):
                t = str(a.get("tier") or "").strip()
                if t:
                    tier_counts[fac][t] = tier_counts[fac].get(t, 0) + 1

    accepted, blocked, warned = [], [], []
    for e in new_entries or []:
        v = validate_codex_entry(e, mb, tier_counts)
        if not v["ok"]:
            blocked.append({"entry": e, "reasons": v["reasons"]})
            continue
        if v["level"] == "WARN":
            warned.append({"entry": v["entry"], "reasons": v["reasons"]})
        accepted.append(v["entry"])

        # 즉시 색인 반영 — 같은 배치 내 중복도 잡는다
        fac = str(v["entry"].get("faction") or faction).strip()
        tier = str(v["entry"].get("tier") or "").strip()
        tier_counts.setdefault(fac, {})
        if tier:
            tier_counts[fac][tier] = tier_counts[fac].get(tier, 0) + 1
        grp = None
        for g in mb.setdefault("faction_arts", []):
            if isinstance(g, dict) and str(g.get("faction", "")).strip() == fac:
                grp = g
                break
        if grp is None:
            grp = {"faction": fac, "signature": "", "training": "", "arts": []}
            mb["faction_arts"].append(grp)
        grp.setdefault("arts", []).append(v["entry"])

        # A28 철자 고정 목록에 등록
        locked = mb.setdefault("author_locked_terms", [])
        if v["entry"]["name"] not in locked:
            locked.append(v["entry"]["name"])

    return {
        "bible": mb, "accepted": accepted,
        "blocked": blocked, "warned": warned,
        "tier_counts": tier_counts,
    }


def format_codex_merge_report(result: dict, faction: str = "") -> str:
    """병합 결과를 작가용 마크다운 리포트로 변환."""
    if not result:
        return ""
    acc = result.get("accepted") or []
    blk = result.get("blocked") or []
    wrn = result.get("warned") or []

    lines = [f"### ⚔️ 무공 대전 병합 결과" + (f" — {faction}" if faction else "")]
    lines.append(f"등록 **{len(acc)}종** · 경고 {len(wrn)}종 · 차단 {len(blk)}종")

    if acc:
        lines.append("\n**등록된 무공**")
        lines.append("| 무공명 | 영문 | 등급 | 분류 | 대가 |")
        lines.append("|---|---|---|---|---|")
        for e in acc[:30]:
            lines.append(
                f"| {e.get('name','')} | {e.get('name_en','')} | "
                f"{e.get('tier','')} | {e.get('category','')} | "
                f"{str(e.get('cost',''))[:40]} |"
            )
    if wrn:
        lines.append("\n**경고 (등록됨 — 확인 권장)**")
        for w in wrn[:10]:
            lines.append(f"- {w['entry'].get('name','')}")
            for r in w["reasons"]:
                lines.append(f"    · {r}")
    if blk:
        lines.append("\n**차단 (등록 안 됨)**")
        for b in blk[:15]:
            nm = (b["entry"] or {}).get("name", "?")
            lines.append(f"- {nm}")
            for r in b["reasons"]:
                lines.append(f"    · {r}")

    lines.append("\n> 병합 직전 바이블은 `_snapshots`에 보존됐습니다. 되돌릴 수 있습니다.")
    return "\n".join(lines)


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

    # 5. 장르 밀도 스캐너 (v2.6.0) — 방향성 회귀 검증
    #    장르 신호가 있는 원고가 없는 원고보다 반드시 높아야 한다.
    dense = (
        "\"무당파의 당랑연검술(螳螂軟劍術)!\"\n"
        "장무극의 검이 사마귀 앞발처럼 파고들었다. '챙' 하고 쇳소리가 울렸다.\n"
        "당랑연검술은 사마귀의 움직임을 연구해 만든 연검술이다. 정면으로 맞서지 않고 "
        "상대의 힘을 흘려보낸 뒤 되돌려주는 것이 핵심이었다. 다만 단단한 방어를 뚫는 데는 약하다.\n"
        "화산파의 화산장풍도(花山掌風道)가 뒤이어 터졌다. 단전에서 끌어올린 내공이 "
        "손끝에 실렸다. 절정의 경지였다. '붕' 하는 소리와 함께 기운이 뻗었다.\n"
        "축지법(縮地法). 땅을 접는 보법이다. 소림의 제자가 눈을 크게 떴다.\n"
        "청수유수권(淸水流手拳)은 방어에 특화된 권법이었다. 아미파가 자랑하는 절기다.\n"
        "운기조식(運氣調息)으로 기맥을 다스렸다. 살기가 가셨다.\n"
    )
    thin = (
        "그는 팔꿈치로 명치를 눌렀다. 상대의 무릎이 꺾였다.\n"
        "초식이라 부를 것도 없었다. 그냥, 잡았다.\n"
        "\"어어, 힘 좀 빼요.\"\n"
        "\"…\"\n"
        "\"손목 이러면 밥 어떻게 먹어요.\"\n"
        "그는 이름이 없었다. 배운 적도 없었다. 그냥 됐다.\n"
    )
    d_dense = scan_wuxia_density(dense, ep_number=1)
    d_thin = scan_wuxia_density(thin, ep_number=1)
    m_dense = _score_mise_en_scene(dense)["score"]
    m_thin = _score_mise_en_scene(thin)["score"]
    print(f"\n장르 밀도 — 무협형: {d_dense['grade']} "
          f"{d_dense['achieved']}/7 (MISE {m_dense})")
    print(f"장르 밀도 — 격투형: {d_thin['grade']} "
          f"{d_thin['achieved']}/7 (MISE {m_thin})")
    assert d_dense["achieved"] > d_thin["achieved"], "밀도 판정 방향 역전"
    assert m_dense > m_thin, "MISE 점수 방향 역전 (사고 패턴 N 재발)"
    assert d_thin["evasion_hits"], "명명 회피 관용구 미검출"
    print("장르 밀도 방향성 검증 통과 (사고 패턴 N 회귀 방지)")

    print("\n✅ 자가 테스트 통과")


if __name__ == "__main__":
    _self_test()
