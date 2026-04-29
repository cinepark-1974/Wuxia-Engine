"""
👖 BLUE JEANS WUXIA ENGINE v1.0 — main.py
무협 웹소설 집필 엔진 (Streamlit Cloud 배포용)
© 2026 BLUE JEANS PICTURES
"""
import streamlit as st
import anthropic
import json
import re
from datetime import datetime

from prompt import (
    SYSTEM_PROMPT,
    build_system_prompt,
    build_parse_brief_prompt,
    build_brief_to_seed_prompt,           # v2.0 신규
    build_brief_episode_extraction_prompt, # v2.0 신규
    build_generate_concept_prompt,
    build_augment_concept_prompt,
    build_core_arc_prompt,
    build_extension_arc_prompt,
    build_plant_payoff_prompt,
    build_character_bible_prompt,
    build_episode_plot_prompt,
    build_episode_write_prompt,
    build_rating_convert_prompt,
    build_alternative_scene_prompt,
    build_quality_check_prompt,
    build_episode_summary_prompt,
    build_reader_simulation_prompt,
    WUXIA_FORMULAS,
    PROTAGONIST_TYPES,
    NARRATIVE_TONE_PRESETS,
    READER_PERSONAS,
    NARRATIVE_MOTIFS,
    PLATFORM_LENGTH,
    match_formulas,
    get_platform_length,
    # v2.0 신규
    WUXIA_CHARACTER_ROLES,
    WUXIA_HERO_MIND_FLOW,
    WUXIA_VALIDATION_WEIGHTS,
    WUXIA_MARKET_DATA,
    VALIDATION_THRESHOLDS,
    get_protagonist_subtype_block,
    get_character_role_block,
    get_stage_for_episode,
    detect_wuxia_work_orientation,
    build_wuxia_formula_strategy_block,
    build_wuxia_motif_block,
    build_wuxia_character_role_block,
    build_wuxia_mind_flow_arc_block,
    build_wuxia_market_viability_block,
    build_wuxia_ideaseed_to_concept_prompt,
    build_validation_prompt,
    build_episode_redo_prompt,
)
from profession_pack import (
    PROFESSION_PACK,
    detect_profession_category,
    detect_protagonist_type,
    build_profession_block,
    build_multi_profession_block,
    build_protagonist_type_detail_block,
    auto_inject_profession_blocks,
)
from parser import parse_brief
from docx_builder import build_episode_docx, build_season_docx, build_proposal_docx
# v2.0 자가 검수 엔진
from engine_validator import (
    VALIDATION_MODES,
    compute_episode_validation_score,
    detect_transition_episodes,
    get_validation_mode_for_episode,
    generate_material_usage_report,
    summarize_cumulative_25,
)


# ══════════════════════════════════════════════
# Page Config
# ══════════════════════════════════════════════
st.set_page_config(
    page_title="BLUE JEANS · Wuxia Engine",
    page_icon="👖",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ══════════════════════════════════════════════
# CSS (블루진 디자인 시스템 완전 복제 from v2.6)
# ══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
@import url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@latest/Paperlogy.css');
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&display=swap');

:root {
    --navy: #191970;
    --y: #FFCB05;
    --bg: #F7F7F5;
    --card: #FFFFFF;
    --card-border: #E2E2E0;
    --t: #1A1A2E;
    --r: #D32F2F;
    --g: #2EC484;
    --dim: #8E8E99;
    --light-bg: #EEEEF6;
    --display: 'Playfair Display', 'Paperlogy', 'Georgia', serif;
    --heading: 'Paperlogy', 'Pretendard', sans-serif;
    --body: 'Pretendard', -apple-system, sans-serif;
}
html, body, [class*="css"] {
    font-family: var(--body) !important;
    color: var(--t);
}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"],
[data-testid="stMainBlockContainer"], [data-testid="stHeader"],
[data-testid="stBottom"], [data-testid="stSidebar"] {
    background-color: var(--bg) !important;
    color: var(--t) !important;
}
.brand-header {
    text-align: center;
    padding: 2rem 0 1.5rem;
    border-bottom: 2px solid var(--y);
    margin-bottom: 1.5rem;
}
.brand-header .company {
    font-family: var(--display);
    font-weight: 900; font-size: 0.85rem;
    letter-spacing: 0.35em; color: var(--navy);
    margin-bottom: 0.25rem;
}
.brand-header .engine {
    font-family: var(--heading);
    font-weight: 700; font-size: 1.6rem;
    letter-spacing: 0.5em; color: var(--navy);
    margin-bottom: 0.3rem;
}
.brand-header .tagline {
    font-family: var(--body);
    font-weight: 300; font-size: 0.7rem;
    letter-spacing: 0.3em; color: var(--dim);
}
.section-header {
    background: var(--y);
    padding: 8px 16px; border-radius: 4px;
    margin: 1.2rem 0 0.6rem; display: inline-block;
}
.section-header span {
    font-family: var(--heading);
    font-weight: 700; color: var(--navy);
    font-size: 0.85rem; letter-spacing: 0.05em;
}
.stButton > button {
    background: var(--navy) !important;
    color: #FFFFFF !important;
    border: none !important;
    font-family: var(--heading) !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.5rem !important;
}
.stButton > button:hover {
    background: var(--y) !important;
    color: var(--navy) !important;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 2px solid var(--card-border);
}
.stTabs [data-baseweb="tab"] {
    font-family: var(--heading) !important;
    font-weight: 600 !important;
    color: var(--dim) !important;
    font-size: 0.9rem !important;
    padding: 0.8rem 2rem !important;
}
.stTabs [aria-selected="true"] {
    color: var(--navy) !important;
    border-bottom: 3px solid var(--y) !important;
}
.stProgress > div > div {
    background-color: var(--y) !important;
}
textarea { font-family: var(--body) !important; font-size: 0.9rem !important; }
.rating-badge-19 {
    background: var(--r); color: white;
    padding: 2px 8px; border-radius: 4px;
    font-size: 0.75rem; font-weight: 700;
}
.rating-badge-15 {
    background: var(--g); color: white;
    padding: 2px 8px; border-radius: 4px;
    font-size: 0.75rem; font-weight: 700;
}
.seq {
    display: inline-block;
    background: var(--navy); color: #FFFFFF !important;
    padding: 2px 10px; border-radius: 12px;
    font-family: var(--heading);
    font-weight: 700; font-size: 0.75rem;
    letter-spacing: 0.03em; margin-right: 6px;
}
.sub-tab-header {
    font-family: var(--heading);
    font-weight: 700; color: var(--navy);
    font-size: 1rem; margin: 1rem 0 0.5rem;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid var(--card-border);
}
.mode-card {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
}
.version-badge {
    display: inline-block;
    background: var(--light-bg);
    color: var(--navy);
    padding: 3px 10px;
    border-radius: 12px;
    font-family: var(--heading);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# Brand Header
# ══════════════════════════════════════════════
st.markdown("""
<div class="brand-header">
    <div class="company">BLUE JEANS PICTURES</div>
    <div class="engine">WUXIA ENGINE</div>
    <div class="tagline">YOUNG · VINTAGE · FREE · INNOVATIVE</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# API Client & Model
# ══════════════════════════════════════════════
MODEL_OPUS = "claude-opus-4-7"      # v2.0 — 집필 (temperature/top_p/thinking 사용 금지)
MODEL_SONNET = "claude-sonnet-4-6"  # v2.0 — 구조 분석·자가 검수
MAX_TOKENS_ARC = 12000
MAX_TOKENS_EPISODE = 8000
MAX_TOKENS_STRUCTURE = 6000
MAX_TOKENS_ANALYSIS = 4000


@st.cache_resource
def get_client():
    return anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])


def call_claude(prompt, max_tokens=4096, model=None, system=None):
    if model is None:
        model = MODEL_SONNET
    if system is None:
        system = SYSTEM_PROMPT
    client = get_client()
    full = []
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            full.append(text)
    return "".join(full)


def call_claude_opus(prompt, max_tokens=8000, system=None):
    return call_claude(prompt, max_tokens=max_tokens, model=MODEL_OPUS, system=system)


def safe_json(raw, debug=False):
    """JSON 추출 & 파싱 — v2.0 강화판.

    3단계 폴백:
    1단계: 표준 JSON 추출 (마크다운 / trailing comma 처리)
    2단계: 한국어 가이드 문구 제거 (예: "등에서 선택", "중 하나")
    3단계: 잘린 JSON 자동 복구 (닫히지 않은 괄호 보강)

    Args:
        raw: LLM 원본 응답
        debug: True면 실패 시 (None, error_info) 튜플 반환

    Returns:
        파싱된 dict/list 또는 None (debug=True면 (result, info))
    """
    error_info = {"raw_length": len(raw) if raw else 0, "stage_failed": None, "error": None}

    if not raw:
        error_info["stage_failed"] = "empty_input"
        return (None, error_info) if debug else None

    # ── 0단계: 마크다운 코드 블록 제거 ──
    cleaned = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE).strip()

    # ── JSON 블록 추출 헬퍼 ──
    def extract_json_block(text):
        for open_c, close_c in [("{", "}"), ("[", "]")]:
            start = text.find(open_c)
            if start < 0:
                continue
            depth = 0
            in_string = False
            escape = False
            for i in range(start, len(text)):
                ch = text[i]
                if escape:
                    escape = False
                    continue
                if ch == "\\":
                    escape = True
                    continue
                if ch == '"' and not escape:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == open_c:
                    depth += 1
                elif ch == close_c:
                    depth -= 1
                    if depth == 0:
                        return text[start:i + 1]
        return None

    block = extract_json_block(cleaned)
    if block:
        cleaned = block

    # ── 제어 문자 제거 + trailing comma 정리 ──
    cleaned = "".join(ch for ch in cleaned if ch >= " " or ch in "\n\r\t")
    cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)

    # ── 1단계: 표준 파싱 시도 ──
    try:
        return (json.loads(cleaned), error_info) if debug else json.loads(cleaned)
    except json.JSONDecodeError as e1:
        error_info["stage_failed"] = "stage1_standard"
        error_info["error"] = str(e1)

    # ── 2단계: 한국어 가이드 문구 제거 후 재시도 ──
    # 예: "narrative_motifs": ["혈수", "기연" 등에서 선택]
    # → "narrative_motifs": ["혈수", "기연"]
    guide_patterns = [
        r'\s*등에서\s*선택',
        r'\s*중\s*하나',
        r'\s*중\s*1개',
        r'\s*중\s*1[~~-]\d+개',
        r'\s*등\s*가능',
        r'\s*해당되는?\s*것',
        r'\s*해당하는?\s*것',
        r'\s*없으면\s*빈\s*문자열',
        r'\s*없으면\s*[""]"]',
    ]
    cleaned_v2 = cleaned
    for pat in guide_patterns:
        cleaned_v2 = re.sub(pat, '', cleaned_v2)
    # trailing comma 다시 정리
    cleaned_v2 = re.sub(r",(\s*[}\]])", r"\1", cleaned_v2)

    try:
        return (json.loads(cleaned_v2), error_info) if debug else json.loads(cleaned_v2)
    except json.JSONDecodeError as e2:
        error_info["stage_failed"] = "stage2_guide_removal"
        error_info["error"] = str(e2)

    # ── 3단계: 잘린 JSON 자동 복구 (닫히지 않은 괄호 보강) ──
    # LLM 응답이 토큰 한도로 잘려서 끝부분이 손상된 경우
    cleaned_v3 = cleaned_v2

    # 마지막 정상 위치까지 자르기 (마지막 콜론·콤마 후로 잘려있으면 그 앞까지)
    # ", "key": ... <끝>" 같은 패턴 제거
    # 끝부분에서 마지막 닫는 괄호 위치 추적
    last_safe = -1
    depth_curly = 0
    depth_square = 0
    in_str = False
    esc = False
    for i, ch in enumerate(cleaned_v3):
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == '"' and not esc:
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            depth_curly += 1
        elif ch == "}":
            depth_curly -= 1
            if depth_curly == 0 and depth_square == 0:
                last_safe = i
        elif ch == "[":
            depth_square += 1
        elif ch == "]":
            depth_square -= 1
            if depth_curly == 0 and depth_square == 0:
                last_safe = i

    # 닫히지 않은 괄호 자동 보강
    if depth_curly > 0 or depth_square > 0:
        # 끝 부분의 ", "incomplete_key": ..." 같은 미완성 항목 제거
        # 마지막 정상적인 ", " 또는 "{" 또는 "[" 직후까지 자르기
        last_comma_or_open = max(
            cleaned_v3.rfind(","),
            cleaned_v3.rfind("{"),
            cleaned_v3.rfind("["),
        )
        if last_comma_or_open > 0:
            cleaned_v3 = cleaned_v3[:last_comma_or_open]
            # trailing comma 제거
            cleaned_v3 = cleaned_v3.rstrip().rstrip(",")

        # 여전히 닫히지 않은 괄호 보강
        depth_curly = cleaned_v3.count("{") - cleaned_v3.count("}")
        depth_square = cleaned_v3.count("[") - cleaned_v3.count("]")
        for _ in range(depth_square):
            cleaned_v3 += "]"
        for _ in range(depth_curly):
            cleaned_v3 += "}"

    try:
        return (json.loads(cleaned_v3), error_info) if debug else json.loads(cleaned_v3)
    except json.JSONDecodeError as e3:
        error_info["stage_failed"] = "stage3_truncation_recovery"
        error_info["error"] = str(e3)

    return (None, error_info) if debug else None


# ══════════════════════════════════════════════
# Session State
# ══════════════════════════════════════════════
defaults = {
    "concept_card": {},
    "core_arc": [],
    "core_arc_summaries": [],
    "extension_arc": [],
    "extension_mode": "bridge",
    "extension_eps": 50,
    "plant_map_core": {},
    "plant_map_extension": {},
    "character_bible": {},
    "episode_plots": {},
    "episodes_19": {},
    "episodes_15": {},
    "episode_summaries": {},
    "quality_reports": {},
    "producer_note": "",
    "style_dna": "",
    "style_strength": "중",
    "brief_text": "",
    # v2.0 자가 검수
    "validation_mode": "auto_until_25",
    "validation_results": {},      # {ep_number: validation_result_dict}
    "post_25_decided": False,      # 26화 이후 모드 결정 여부
    # v2.0 IdeaSeed
    "wuxia_idea_seed_data": None,  # 업로드된 IdeaSeed JSON dict
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════
# 프로듀서 노트 (전역)
# ══════════════════════════════════════════════
with st.expander("🎬 프로듀서 노트 (전역 적용)", expanded=False):
    st.session_state.producer_note = st.text_area(
        "세션 전체에 적용할 지시사항",
        value=st.session_state.producer_note,
        height=80,
        placeholder="예: 대사 짧고 건조하게. 전투는 초단문. 한자 병기 최소화.",
        label_visibility="collapsed",
    )


# ══════════════════════════════════════════════
# 프로젝트 Save / Load
# ══════════════════════════════════════════════
PROJECT_KEYS = [
    "concept_card", "core_arc", "core_arc_summaries",
    "extension_arc", "extension_mode", "extension_eps",
    "plant_map_core", "plant_map_extension", "character_bible",
    "episode_plots", "episodes_19", "episodes_15",
    "episode_summaries", "quality_reports",
    "producer_note", "style_dna", "style_strength", "brief_text",
]


def build_project_snapshot():
    snapshot = {"version": "wuxia-1.0", "saved_at": datetime.now().isoformat()}
    for k in PROJECT_KEYS:
        snapshot[k] = st.session_state.get(k)
    return snapshot


def restore_project_snapshot(data):
    if not isinstance(data, dict):
        return False
    for k in PROJECT_KEYS:
        if k in data:
            st.session_state[k] = data[k]
    return True


with st.expander("💾 프로젝트 저장 / 불러오기", expanded=False):
    col_a, col_b = st.columns(2)
    with col_a:
        snapshot = build_project_snapshot()
        snapshot_json = json.dumps(snapshot, ensure_ascii=False, indent=2)
        title = st.session_state.concept_card.get("title", "wuxia_project")
        safe_title = re.sub(r"[^\w\-]", "_", title)
        st.download_button(
            "📥 현재 프로젝트 저장 (.json)",
            data=snapshot_json.encode("utf-8"),
            file_name=f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )
    with col_b:
        uploaded_project = st.file_uploader(
            "📤 프로젝트 불러오기",
            type=["json"],
            key="project_upload",
            label_visibility="collapsed",
        )
        if uploaded_project is not None:
            try:
                loaded = json.loads(uploaded_project.read().decode("utf-8"))
                if restore_project_snapshot(loaded):
                    st.success("✅ 프로젝트 복원 완료")
                    st.rerun()
                else:
                    st.error("❌ 올바르지 않은 프로젝트 파일")
            except Exception as e:
                st.error(f"❌ 불러오기 실패: {e}")


# ══════════════════════════════════════════════
# 메인 탭 구조 (3단계 파이프라인)
# ══════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    "STEP 1 · CONCEPT",
    "STEP 2 · BUILD-UP",
    "STEP 3 · WRITING",
])


# ══════════════════════════════════════════════
# STEP 1: CONCEPT (컨셉 카드 생성) — v2.0 4탭 구조
# ══════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header"><span>CONCEPT · 작품 컨셉 설계</span></div>', unsafe_allow_html=True)

    sub_tabs_1 = st.tabs([
        "📄 기획서 업로드",
        "💡 아이디어 생성",
        "✏️ 직접 입력",
        "🌱 IdeaSeed JSON",  # v2.0 신규
    ])

    # ── 서브탭 1: 기획서 업로드 ──
    with sub_tabs_1[0]:
        st.caption("기획서 파일(DOCX/HWP/PDF/TXT/MD)을 업로드하면 컨셉 카드가 자동 생성됩니다.")
        uploaded = st.file_uploader(
            "기획서 파일을 올려주세요",
            type=["docx", "hwp", "pdf", "txt", "md"],
            key="brief_upload",
        )
        if uploaded is not None:
            try:
                brief_text = parse_brief(uploaded)
                st.session_state.brief_text = brief_text

                # 분량 정보 표시
                brief_len = len(brief_text)
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.metric("기획서 분량", f"{brief_len:,}자")
                with col_info2:
                    if brief_len > 12000:
                        st.warning(f"⚠️ 12,000자 초과 — 자동으로 앞·뒤 발췌하여 분석")
                    else:
                        st.success("✅ 분량 적정")

                with st.expander("파싱된 기획서 내용 확인", expanded=False):
                    st.text_area("내용", brief_text, height=200, label_visibility="collapsed")

                if st.button("🔍 기획서 분석 → 컨셉 카드 생성", use_container_width=True, key="brief_to_concept"):
                    with st.spinner("기획서 분석 중... (긴 기획서는 1~2분 소요)"):
                        raw = call_claude(
                            build_parse_brief_prompt(brief_text),
                            max_tokens=MAX_TOKENS_STRUCTURE,
                        )
                        # debug=True로 상세 진단 정보 받기
                        parsed, debug_info = safe_json(raw, debug=True)
                        if parsed:
                            st.session_state.concept_card = parsed
                            st.success("✅ 컨셉 카드 생성 완료")
                            st.rerun()
                        else:
                            st.error("❌ JSON 파싱 실패")
                            with st.expander("🔍 디버그 정보 (개발자용)", expanded=True):
                                st.write(f"**실패 단계**: {debug_info.get('stage_failed', '?')}")
                                st.write(f"**원본 길이**: {debug_info.get('raw_length', 0):,}자")
                                st.write(f"**오류 메시지**: {debug_info.get('error', '?')}")
                                st.markdown("**LLM 원본 응답 (앞 2000자)**")
                                st.code(raw[:2000] if raw else "(빈 응답)", language="json")
                                if raw and len(raw) > 2000:
                                    st.markdown("**LLM 원본 응답 (끝 1000자)**")
                                    st.code(raw[-1000:], language="json")
                            st.info(
                                "💡 해결 방법:\n"
                                "1. **기획서가 너무 긴 경우**: 핵심 부분만 별도 파일로 줄여서 업로드\n"
                                "2. **결말 정보 누락**: 위 응답이 중간에 잘렸다면 max_tokens 한도 초과 — 짧은 기획서로 재시도\n"
                                "3. **재시도**: 같은 파일 그대로 다시 버튼 클릭 (LLM 응답 변동성 있음)"
                            )
            except Exception as e:
                st.error(f"파일 읽기 실패: {e}")

    # ── 서브탭 2: 아이디어 생성 ──
    with sub_tabs_1[1]:
        st.caption("자유 형식의 아이디어를 입력하면 자동으로 컨셉 카드가 만들어집니다.")
        idea = st.text_area(
            "작품 아이디어 (자유 형식)",
            height=150,
            placeholder="예: 화산파 속가제자가 마교 호법의 배신으로 죽은 후 10년 전으로 회귀해 복수와 문파 재건을 시작한다. 여주는 당가의 독술 천재...",
            key="idea_input",
        )
        genre_hint = st.text_input(
            "장르 힌트 (선택)",
            placeholder="무협 / 판타지 무협 / 여성향 무협 등",
            key="genre_hint",
        )

        if st.button("💡 아이디어 → 컨셉 카드 생성", use_container_width=True,
                     disabled=not idea, key="idea_to_concept"):
            with st.spinner("컨셉 카드 설계 중..."):
                matches = match_formulas(idea, top_n=3)
                if matches:
                    with st.expander("공식 매칭 결과", expanded=False):
                        for k, score, label in matches:
                            st.write(f"  • {label} — 점수 {score:.1f}")

                raw = call_claude_opus(
                    build_generate_concept_prompt(idea, genre_hint),
                    max_tokens=MAX_TOKENS_STRUCTURE,
                )
                parsed = safe_json(raw)
                if parsed:
                    st.session_state.concept_card = parsed
                    st.success("✅ 컨셉 카드 생성 완료")
                    st.rerun()
                else:
                    st.error("❌ JSON 파싱 실패")
                    with st.expander("원본 응답"):
                        st.text(raw)

    # ── 서브탭 3: 직접 입력 (JSON 직접 편집) ──
    with sub_tabs_1[2]:
        st.caption("컨셉 카드 JSON을 직접 입력하거나 편집하세요.")
        existing_json = json.dumps(st.session_state.concept_card, ensure_ascii=False, indent=2) if st.session_state.concept_card else "{}"
        manual_json = st.text_area(
            "컨셉 카드 JSON",
            value=existing_json,
            height=400,
            key="manual_concept_json",
        )
        if st.button("💾 직접 입력한 JSON 저장", use_container_width=True, key="save_manual"):
            try:
                parsed = json.loads(manual_json)
                st.session_state.concept_card = parsed
                st.success("✅ 컨셉 카드 저장 완료")
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"JSON 파싱 오류: {e}")

    # ── 서브탭 4: IdeaSeed JSON (v2.0 신규) ──
    with sub_tabs_1[3]:
        st.caption(
            "Claude Max 무협 스킬에서 생성한 IdeaSeed JSON을 업로드하면 "
            "v2.0 콘셉트 카드로 자동 변환됩니다."
        )

        col_seed1, col_seed2 = st.columns([3, 1])

        with col_seed1:
            seed_upload = st.file_uploader(
                "IdeaSeed JSON 파일",
                type=["json"],
                key="ideaseed_upload",
            )

            seed_paste = st.text_area(
                "또는 IdeaSeed JSON 직접 붙여넣기",
                height=200,
                placeholder='{\n  "_idea_engine_meta": {...},\n  "title": "...",\n  "raw_idea": "...",\n  ...\n}',
                key="ideaseed_paste",
            )

        with col_seed2:
            st.markdown("**IdeaSeed 분석**")

            if seed_upload is not None:
                try:
                    seed_data = json.loads(seed_upload.read().decode("utf-8"))
                    st.session_state.wuxia_idea_seed_data = seed_data
                except Exception as e:
                    st.error(f"파일 읽기 실패: {e}")
            elif seed_paste.strip():
                try:
                    seed_data = json.loads(seed_paste)
                    st.session_state.wuxia_idea_seed_data = seed_data
                except json.JSONDecodeError:
                    st.warning("JSON 형식 확인 필요")

            seed_data = st.session_state.wuxia_idea_seed_data
            if seed_data:
                meta = seed_data.get("_idea_engine_meta", {})
                st.metric("Hook Score", meta.get("hook_score", "?"))
                st.metric("Verdict", meta.get("verdict", "?"))

                v3_class = seed_data.get("_v3_classification_wuxia", {})
                if v3_class:
                    st.markdown("**무협 분류**")
                    st.caption(f"공식: {v3_class.get('wuxia_formula_main', '?')}")
                    st.caption(f"주인공: {v3_class.get('protagonist_type', '?')}")
                    st.caption(f"톤: {v3_class.get('narrative_tone', '?')}")

        # 미결정 사항 처리
        seed_data = st.session_state.wuxia_idea_seed_data
        pending_resolved = {}
        if seed_data:
            pending = seed_data.get("pending_decisions", [])
            if pending:
                with st.expander(f"📌 작가 결정 필요 사항 ({len(pending)}개)", expanded=True):
                    st.caption("기획서 작성 시 결정되지 않은 사항입니다. 답변 후 변환하면 컨셉 카드에 반영됩니다.")
                    for i, q in enumerate(pending):
                        answer = st.text_input(
                            f"Q{i+1}: {q}",
                            key=f"pending_q_{i}",
                            placeholder="(공란이면 AI가 가장 합리적 기본값 적용)",
                        )
                        if answer:
                            pending_resolved[q] = answer

            # 변환 버튼
            if st.button(
                "🌱 IdeaSeed → 무협 컨셉 카드 변환",
                use_container_width=True,
                key="seed_to_concept",
                type="primary",
            ):
                with st.spinner("IdeaSeed → 컨셉 카드 변환 중..."):
                    seed_json_str = json.dumps(seed_data, ensure_ascii=False)
                    raw = call_claude_opus(
                        build_wuxia_ideaseed_to_concept_prompt(
                            seed_json_str,
                            pending_decisions_resolved=pending_resolved or None,
                        ),
                        max_tokens=MAX_TOKENS_STRUCTURE,
                    )
                    parsed = safe_json(raw)
                    if parsed:
                        st.session_state.concept_card = parsed
                        st.success("✅ IdeaSeed → 컨셉 카드 변환 완료")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ JSON 파싱 실패")
                        with st.expander("원본 응답"):
                            st.text(raw[:3000])
        else:
            st.info("위에서 IdeaSeed JSON을 업로드하거나 붙여넣으세요.")

    # ──── 컨셉 카드 표시 & 편집 ────
    if st.session_state.concept_card:
        st.markdown('<div class="sub-tab-header">📄 컨셉 카드</div>', unsafe_allow_html=True)

        cc = st.session_state.concept_card

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"### {cc.get('title', '(제목 없음)')}")
            st.markdown(f"**로그라인:** {cc.get('logline', '')}")
            st.markdown(f"**장르:** {cc.get('genre', '')}")

            formula_label = WUXIA_FORMULAS.get(cc.get('formula_key', ''), {}).get('label', '')
            ptype_label = PROTAGONIST_TYPES.get(cc.get('protagonist_type', ''), {}).get('label', '')
            st.markdown(f"**공식:** {formula_label}")
            st.markdown(f"**주인공 유형:** {ptype_label}")

        with col2:
            st.markdown(f"**타깃 플랫폼:** {cc.get('target_platform', '')}")
            st.markdown(f"**등급:** {cc.get('target_rating', '')}")
            motifs = cc.get("narrative_motifs", [])
            if motifs:
                st.markdown(f"**모티프:** {', '.join(motifs[:3])}")

        with st.expander("전체 JSON 보기 / 편집", expanded=False):
            edited = st.text_area(
                "컨셉 카드 JSON",
                value=json.dumps(cc, ensure_ascii=False, indent=2),
                height=400,
                label_visibility="collapsed",
            )
            if st.button("💾 편집 내용 저장"):
                try:
                    st.session_state.concept_card = json.loads(edited)
                    st.success("저장 완료")
                    st.rerun()
                except json.JSONDecodeError as e:
                    st.error(f"JSON 오류: {e}")

        # ──── 컨셉 증강 ────
        if st.button("✨ 빈 필드 자동 보강", use_container_width=True):
            with st.spinner("보강 중..."):
                raw = call_claude(
                    build_augment_concept_prompt(json.dumps(cc, ensure_ascii=False)),
                    max_tokens=MAX_TOKENS_STRUCTURE,
                )
                parsed = safe_json(raw)
                if parsed:
                    st.session_state.concept_card = parsed
                    st.success("보강 완료")
                    st.rerun()


# ══════════════════════════════════════════════
# STEP 2: BUILD-UP (Arc + Plant Map + Character Bible)
# ══════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header"><span>BUILD-UP · 서사 구조 설계</span></div>', unsafe_allow_html=True)

    if not st.session_state.concept_card:
        st.warning("먼저 STEP 1에서 컨셉 카드를 생성해주세요.")
    else:
        build_tab1, build_tab2, build_tab3, build_tab4 = st.tabs([
            "Core Arc (50화)",
            "Extension Arc",
            "Plant & Payoff Map",
            "Character Bible",
        ])

        # ──── Core Arc ────
        with build_tab1:
            st.markdown('<div class="sub-tab-header">Core Arc · 50화 비트 설계</div>', unsafe_allow_html=True)

            core_eps = st.number_input("Core Arc 회차 수", 30, 100, 50, 5)

            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.session_state.style_dna = st.text_area(
                    "작가 스타일 DNA (선택)",
                    value=st.session_state.style_dna,
                    height=80,
                    placeholder="예: 지문 건조, 대사 간결, 한자 병기 최소...",
                )
            with col_s2:
                st.session_state.style_strength = st.select_slider(
                    "스타일 반영 강도",
                    options=["약", "중", "강"],
                    value=st.session_state.style_strength,
                )

            if st.button("🎬 Core Arc 생성", use_container_width=True):
                with st.spinner(f"{core_eps}화 비트 설계 중... (Opus 사용, 1~2분 소요)"):
                    raw = call_claude_opus(
                        build_core_arc_prompt(
                            st.session_state.concept_card,
                            core_eps=core_eps,
                            producer_note=st.session_state.producer_note,
                            style_dna=st.session_state.style_dna,
                            style_strength=st.session_state.style_strength,
                        ),
                        max_tokens=MAX_TOKENS_ARC,
                    )
                    parsed = safe_json(raw)
                    if parsed and isinstance(parsed, list):
                        st.session_state.core_arc = parsed
                        st.success(f"✅ Core Arc {len(parsed)}화 생성 완료")
                    else:
                        st.error("❌ Arc 생성 실패")
                        with st.expander("원본"):
                            st.text(raw[:3000])

            if st.session_state.core_arc:
                st.markdown(f"**총 {len(st.session_state.core_arc)}화 설계 완료**")
                for ep_data in st.session_state.core_arc:
                    with st.expander(
                        f"EP {ep_data.get('ep', '?')} · {ep_data.get('title', '')}",
                        expanded=False,
                    ):
                        st.markdown(f"**비트:** {ep_data.get('beat_label', '')}")
                        st.markdown(f"**메인 씬:** {ep_data.get('main_scene', '')}")
                        st.markdown(f"**주인공 진행:** {ep_data.get('protagonist_beat', '')}")
                        st.markdown(f"**클리프행어:** {ep_data.get('cliffhanger', '')}")
                        plants = ep_data.get("plant_seeds", [])
                        if plants:
                            st.markdown(f"**떡밥 배치:** {', '.join(plants)}")
                        payoffs = ep_data.get("payoff_recall", [])
                        if payoffs:
                            st.markdown(f"**떡밥 회수:** {', '.join(payoffs)}")

        # ──── Extension Arc ────
        with build_tab2:
            st.markdown('<div class="sub-tab-header">Extension Arc · 확장 시즌</div>', unsafe_allow_html=True)

            if not st.session_state.core_arc:
                st.info("Core Arc 생성 후 이용 가능합니다.")
            else:
                st.session_state.extension_mode = st.radio(
                    "확장 모드",
                    ["bridge", "jump"],
                    format_func=lambda x: "Bridge (Core 직결 후속)" if x == "bridge" else "Jump (시간 점프)",
                    horizontal=True,
                )
                st.session_state.extension_eps = st.number_input(
                    "Extension 회차 수", 30, 100, st.session_state.extension_eps, 5,
                )

                if st.button("🌿 Extension Arc 생성", use_container_width=True):
                    core_arc_text = json.dumps(st.session_state.core_arc, ensure_ascii=False)
                    with st.spinner("Extension 설계 중..."):
                        raw = call_claude_opus(
                            build_extension_arc_prompt(
                                st.session_state.concept_card,
                                core_arc_text,
                                extension_mode=st.session_state.extension_mode,
                                extension_eps=st.session_state.extension_eps,
                                producer_note=st.session_state.producer_note,
                            ),
                            max_tokens=MAX_TOKENS_ARC,
                        )
                        parsed = safe_json(raw)
                        if parsed and isinstance(parsed, list):
                            st.session_state.extension_arc = parsed
                            st.success(f"✅ Extension {len(parsed)}화 생성 완료")
                        else:
                            st.error("❌ 생성 실패")

                if st.session_state.extension_arc:
                    st.markdown(f"**Extension {len(st.session_state.extension_arc)}화 생성됨**")
                    with st.expander("전체 보기"):
                        st.json(st.session_state.extension_arc)

        # ──── Plant & Payoff Map ────
        with build_tab3:
            st.markdown('<div class="sub-tab-header">Plant & Payoff Map · 떡밥 설계</div>', unsafe_allow_html=True)

            if not st.session_state.core_arc:
                st.info("Core Arc 생성 후 이용 가능합니다.")
            else:
                arc_choice = st.radio(
                    "대상 Arc",
                    ["Core Arc", "Extension Arc"],
                    horizontal=True,
                    disabled=not st.session_state.extension_arc,
                )

                if st.button("🌱 떡밥 맵 생성", use_container_width=True):
                    target_arc = st.session_state.core_arc if arc_choice == "Core Arc" else st.session_state.extension_arc
                    arc_type = "core" if arc_choice == "Core Arc" else "extension"
                    arc_text = json.dumps(target_arc, ensure_ascii=False)
                    chars = json.dumps(
                        st.session_state.character_bible or st.session_state.concept_card,
                        ensure_ascii=False,
                    )

                    with st.spinner("떡밥 맵 작성 중..."):
                        raw = call_claude(
                            build_plant_payoff_prompt(arc_text, chars, arc_type),
                            max_tokens=MAX_TOKENS_STRUCTURE,
                        )
                        parsed = safe_json(raw)
                        if parsed:
                            if arc_type == "core":
                                st.session_state.plant_map_core = parsed
                            else:
                                st.session_state.plant_map_extension = parsed
                            st.success("✅ 떡밥 맵 생성 완료")
                        else:
                            st.error("❌ 생성 실패")

                current_map = (
                    st.session_state.plant_map_core if arc_choice == "Core Arc"
                    else st.session_state.plant_map_extension
                )
                if current_map:
                    plants = current_map.get("plants", [])
                    payoffs = current_map.get("payoffs", [])
                    orphans = current_map.get("orphan_plants", [])

                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        st.markdown(f"**떡밥 {len(plants)}개**")
                        for p in plants[:10]:
                            st.markdown(f"  • [EP{p.get('ep')}] {p.get('description', '')[:50]}")
                    with col_p2:
                        st.markdown(f"**회수 {len(payoffs)}개**")
                        for y in payoffs[:10]:
                            st.markdown(f"  • [EP{y.get('ep')}] {y.get('description', '')[:50]}")

                    if orphans:
                        st.warning(f"⚠️ 회수 안 된 떡밥: {', '.join(orphans)}")

        # ──── Character Bible ────
        with build_tab4:
            st.markdown('<div class="sub-tab-header">Character Bible · 캐릭터 상세</div>', unsafe_allow_html=True)

            if st.button("👥 캐릭터 바이블 생성", use_container_width=True):
                with st.spinner("캐릭터 바이블 작성 중..."):
                    # 자동 직업 블록 주입
                    profession_blocks = auto_inject_profession_blocks(st.session_state.concept_card)

                    raw = call_claude_opus(
                        build_character_bible_prompt(
                            json.dumps(st.session_state.concept_card, ensure_ascii=False),
                            profession_blocks=profession_blocks,
                        ),
                        max_tokens=MAX_TOKENS_ARC,
                    )
                    parsed = safe_json(raw)
                    if parsed:
                        st.session_state.character_bible = parsed
                        st.success("✅ 캐릭터 바이블 생성 완료")
                    else:
                        st.error("❌ 생성 실패")

            if st.session_state.character_bible:
                cb = st.session_state.character_bible
                for role_key, role_data in cb.items():
                    if not role_data:
                        continue
                    if isinstance(role_data, list):
                        for i, c in enumerate(role_data):
                            with st.expander(f"{role_key} {i+1}: {c.get('이름', c.get('name', ''))}", expanded=False):
                                st.json(c)
                    else:
                        with st.expander(f"{role_key}: {role_data.get('이름', role_data.get('name', ''))}", expanded=False):
                            st.json(role_data)


# ══════════════════════════════════════════════
# STEP 3: WRITING (회차 집필)
# ══════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header"><span>WRITING · 회차 집필</span></div>', unsafe_allow_html=True)

    if not st.session_state.core_arc:
        st.warning("먼저 STEP 2에서 Core Arc를 생성해주세요.")
    else:
        arc_source = st.radio(
            "집필 대상 Arc",
            ["Core Arc", "Extension Arc"],
            horizontal=True,
            disabled=not st.session_state.extension_arc,
        )
        target_arc = (
            st.session_state.core_arc if arc_source == "Core Arc"
            else st.session_state.extension_arc
        )

        # 회차 선택
        ep_options = [ep.get("ep") for ep in target_arc if ep.get("ep")]
        if not ep_options:
            st.error("Arc에 회차 정보가 없습니다.")
        else:
            selected_ep = st.selectbox(
                "집필할 회차",
                ep_options,
                format_func=lambda e: f"EP {e}: " + next(
                    (ep.get("title", "") for ep in target_arc if ep.get("ep") == e), ""
                ),
            )

            platform = st.selectbox(
                "플랫폼",
                list(PLATFORM_LENGTH.keys()),
                index=list(PLATFORM_LENGTH.keys()).index(
                    st.session_state.concept_card.get("target_platform", "문피아")
                ) if st.session_state.concept_card.get("target_platform") in PLATFORM_LENGTH else 0,
            )
            rating = st.radio(
                "등급",
                ["15금", "19금"],
                horizontal=True,
                index=1 if st.session_state.concept_card.get("target_rating") == "19금" else 0,
            )

            # ──── 플롯 생성 ────
            col_w1, col_w2 = st.columns(2)
            with col_w1:
                if st.button(f"📐 EP{selected_ep} 플롯 생성", use_container_width=True):
                    with st.spinner("플롯 설계 중..."):
                        ep_arc = next(
                            (ep for ep in target_arc if ep.get("ep") == selected_ep), {}
                        )
                        plant_map = (
                            st.session_state.plant_map_core if arc_source == "Core Arc"
                            else st.session_state.plant_map_extension
                        )
                        prev_summaries = ""
                        for prev_ep in range(max(1, selected_ep - 3), selected_ep):
                            summ = st.session_state.episode_summaries.get(prev_ep, "")
                            if summ:
                                prev_summaries += f"\n[EP{prev_ep}] {summ}"

                        raw = call_claude(
                            build_episode_plot_prompt(
                                json.dumps(ep_arc, ensure_ascii=False),
                                json.dumps(plant_map, ensure_ascii=False),
                                selected_ep,
                                json.dumps(st.session_state.concept_card, ensure_ascii=False),
                                prev_summaries=prev_summaries,
                                producer_note=st.session_state.producer_note,
                            ),
                            max_tokens=MAX_TOKENS_STRUCTURE,
                        )
                        parsed = safe_json(raw)
                        if parsed:
                            st.session_state.episode_plots[selected_ep] = parsed
                            st.success(f"✅ EP{selected_ep} 플롯 완성")
                            st.rerun()
                        else:
                            st.error("❌ 플롯 생성 실패")

            with col_w2:
                plot_ready = selected_ep in st.session_state.episode_plots
                if st.button(
                    f"✍️ EP{selected_ep} 본문 집필",
                    use_container_width=True,
                    disabled=not plot_ready,
                ):
                    with st.spinner(f"EP{selected_ep} 집필 중... (Opus 사용)"):
                        profession_blocks = auto_inject_profession_blocks(st.session_state.concept_card)
                        episode_text = call_claude_opus(
                            build_episode_write_prompt(
                                json.dumps(st.session_state.episode_plots[selected_ep], ensure_ascii=False),
                                json.dumps(st.session_state.character_bible, ensure_ascii=False),
                                st.session_state.style_dna,
                                selected_ep,
                                rating=rating,
                                platform=platform,
                                producer_note=st.session_state.producer_note,
                                concept_card=st.session_state.concept_card,
                                profession_blocks=profession_blocks,
                            ),
                            max_tokens=MAX_TOKENS_EPISODE,
                        )
                        if rating == "19금":
                            st.session_state.episodes_19[selected_ep] = episode_text
                        else:
                            st.session_state.episodes_15[selected_ep] = episode_text
                        st.success(f"✅ EP{selected_ep} 본문 완성 ({len(episode_text)}자)")
                        st.rerun()

            # ──── 플롯 표시 ────
            if selected_ep in st.session_state.episode_plots:
                with st.expander(f"📐 EP{selected_ep} 플롯", expanded=False):
                    st.json(st.session_state.episode_plots[selected_ep])

            # ──── 본문 표시 ────
            ep19 = st.session_state.episodes_19.get(selected_ep)
            ep15 = st.session_state.episodes_15.get(selected_ep)
            current_ep = ep19 if rating == "19금" else ep15

            if current_ep:
                st.markdown(f'<div class="sub-tab-header">📖 EP{selected_ep} 본문 ({rating})</div>',
                            unsafe_allow_html=True)

                col_tool1, col_tool2, col_tool3, col_tool4 = st.columns(4)
                with col_tool1:
                    if rating == "19금" and st.button("🔄 15금 변환", use_container_width=True):
                        with st.spinner("변환 중..."):
                            converted = call_claude(
                                build_rating_convert_prompt(current_ep),
                                max_tokens=MAX_TOKENS_EPISODE,
                            )
                            st.session_state.episodes_15[selected_ep] = converted
                            st.success("✅ 15금 변환 완료")
                            st.rerun()

                with col_tool2:
                    if st.button("🔍 품질 체크", use_container_width=True):
                        with st.spinner("분석 중..."):
                            raw = call_claude(
                                build_quality_check_prompt(
                                    current_ep,
                                    selected_ep,
                                    json.dumps(st.session_state.character_bible, ensure_ascii=False),
                                    json.dumps(st.session_state.concept_card, ensure_ascii=False),
                                ),
                                max_tokens=MAX_TOKENS_ANALYSIS,
                            )
                            parsed = safe_json(raw)
                            if parsed:
                                st.session_state.quality_reports[selected_ep] = parsed
                                st.success("✅ 품질 체크 완료")
                                st.rerun()

                with col_tool3:
                    if st.button("📝 회차 요약", use_container_width=True):
                        with st.spinner("요약 중..."):
                            summary = call_claude(
                                build_episode_summary_prompt(current_ep, selected_ep),
                                max_tokens=1000,
                            )
                            st.session_state.episode_summaries[selected_ep] = summary
                            st.success("✅ 요약 완료")
                            st.rerun()

                with col_tool4:
                    # DOCX 다운로드
                    try:
                        # rating 파라미터: "19" / "15" 형식 (docx_builder 규약)
                        rating_code = "19" if rating == "19금" else "15"
                        docx_bytes = build_episode_docx(
                            current_ep,
                            selected_ep,
                            concept=st.session_state.concept_card,
                            rating=rating_code,
                            platform=platform,
                        )
                        title = st.session_state.concept_card.get("title", "wuxia")
                        safe_title = re.sub(r"[^\w\-]", "_", title)
                        st.download_button(
                            "📥 DOCX 다운로드",
                            data=docx_bytes,
                            file_name=f"{safe_title}_EP{selected_ep:03d}_{rating}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.caption(f"DOCX 생성 실패: {e}")

                # 본문 표시
                st.text_area(
                    "본문",
                    value=current_ep,
                    height=500,
                    label_visibility="collapsed",
                )

                # 품질 리포트
                if selected_ep in st.session_state.quality_reports:
                    with st.expander("🔍 품질 리포트", expanded=False):
                        qr = st.session_state.quality_reports[selected_ep]
                        score = qr.get("overall_score", 0)
                        st.metric("종합 점수", f"{score}/100")
                        for item in qr.get("items", []):
                            status = item.get("status", "")
                            emoji = {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(status, "•")
                            st.markdown(
                                f"{emoji} **{item.get('category')}** · {item.get('item')}: {item.get('issue', '')}"
                            )

                # ──── v2.0 자가 검수 시스템 ────
                st.markdown('<div class="sub-tab-header">🔬 v2.0 자가 검수 (5축 종합)</div>', unsafe_allow_html=True)

                # 검수 모드 결정
                col_v1, col_v2 = st.columns([2, 1])
                with col_v1:
                    val_mode = st.selectbox(
                        "검수 모드",
                        list(VALIDATION_MODES.keys()),
                        format_func=lambda k: VALIDATION_MODES[k]["name"],
                        index=list(VALIDATION_MODES.keys()).index(st.session_state.validation_mode)
                            if st.session_state.validation_mode in VALIDATION_MODES else 0,
                        key=f"val_mode_select_{selected_ep}",
                    )
                    if val_mode != st.session_state.validation_mode:
                        st.session_state.validation_mode = val_mode

                    st.caption(VALIDATION_MODES[val_mode]["description"])

                with col_v2:
                    transitions = detect_transition_episodes(
                        st.session_state.concept_card,
                        len(target_arc) if target_arc else 50,
                    )
                    st.markdown("**전환점 회차**")
                    st.caption(", ".join([f"EP{t}" for t in transitions]))

                # 현재 회차 자동 검수 여부
                mode_decision = get_validation_mode_for_episode(
                    selected_ep,
                    val_mode,
                    st.session_state.concept_card,
                    len(target_arc) if target_arc else 50,
                )
                if mode_decision["is_transition"]:
                    st.info(f"⚠️ EP{selected_ep}는 마음 흐름 전환점입니다. 자동 검수 권장.")
                if mode_decision["should_auto"]:
                    st.success(f"🤖 자동 검수 권장: {mode_decision['reason']}")
                else:
                    st.caption(f"ℹ️ {mode_decision['reason']}")

                # 검수 실행 버튼
                col_v3, col_v4 = st.columns(2)
                with col_v3:
                    if st.button(
                        "📐 규칙 기반 자가 검수 (즉시·무료)",
                        use_container_width=True,
                        key=f"rule_validate_{selected_ep}",
                    ):
                        with st.spinner("5축 규칙 기반 검수 중..."):
                            result = compute_episode_validation_score(
                                st.session_state.concept_card,
                                st.session_state.character_bible,
                                current_ep,
                                ep_number=selected_ep,
                                total_eps=len(target_arc) if target_arc else 50,
                            )
                            st.session_state.validation_results[selected_ep] = result
                            st.success(f"✅ 검수 완료: {result['overall']}점 ({result['grade']})")
                            st.rerun()

                with col_v4:
                    if st.button(
                        "🤖 LLM 깊이 검수 (Sonnet)",
                        use_container_width=True,
                        key=f"llm_validate_{selected_ep}",
                    ):
                        with st.spinner("LLM 깊이 검수 중... (1~2분)"):
                            # 먼저 규칙 기반 사전 검수
                            rule_result = compute_episode_validation_score(
                                st.session_state.concept_card,
                                st.session_state.character_bible,
                                current_ep,
                                ep_number=selected_ep,
                                total_eps=len(target_arc) if target_arc else 50,
                            )
                            # LLM 검수 호출
                            prev_summ = st.session_state.episode_summaries.get(selected_ep - 1, "")
                            raw = call_claude(
                                build_validation_prompt(
                                    current_ep,
                                    selected_ep,
                                    st.session_state.concept_card,
                                    json.dumps(st.session_state.character_bible, ensure_ascii=False),
                                    rule_validation_result=rule_result.get("axes", {}).get("MATERIAL_USAGE", {}).get("details"),
                                    total_eps=len(target_arc) if target_arc else 50,
                                    prev_summary=prev_summ,
                                ),
                                max_tokens=MAX_TOKENS_ANALYSIS,
                            )
                            llm_result = safe_json(raw)
                            if llm_result:
                                # 규칙 결과와 LLM 결과 병합 — LLM 결과를 우선
                                st.session_state.validation_results[selected_ep] = {
                                    "axes": llm_result.get("axes", rule_result.get("axes", {})),
                                    "overall": llm_result.get("weighted_overall", rule_result.get("overall", 0)),
                                    "grade": llm_result.get("grade", rule_result.get("grade", "?")),
                                    "verdict": llm_result.get("verdict", rule_result.get("verdict", "?")),
                                    "verdict_text": llm_result.get("verdict", ""),
                                    "key_strengths": llm_result.get("key_strengths", []),
                                    "key_weaknesses": llm_result.get("key_weaknesses", []),
                                    "concrete_fixes": llm_result.get("concrete_fixes", []),
                                    "transition_quality": llm_result.get("transition_quality", ""),
                                    "_source": "LLM",
                                }
                                st.success(f"✅ LLM 검수 완료: {llm_result.get('weighted_overall', '?')}점")
                                st.rerun()
                            else:
                                st.error("❌ LLM 검수 결과 파싱 실패")

                # 검수 결과 표시
                if selected_ep in st.session_state.validation_results:
                    val_result = st.session_state.validation_results[selected_ep]
                    overall = val_result.get("overall", 0)
                    verdict = val_result.get("verdict", "?")
                    grade = val_result.get("grade", "?")

                    # 메트릭
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        emoji = "🟢" if overall >= 75 else ("🟡" if overall >= 65 else "🔴")
                        st.metric(f"{emoji} 종합 점수", f"{overall}/100")
                    with col_m2:
                        st.metric("등급", grade)
                    with col_m3:
                        verdict_color = {"PASS": "🟢", "WARN": "🟡", "REDO": "🔴"}.get(verdict, "")
                        st.metric("판정", f"{verdict_color} {verdict}")

                    # 마크다운 리포트
                    with st.expander("📊 5축 세부 리포트", expanded=(verdict == "REDO")):
                        report = generate_material_usage_report(val_result, ep_number=selected_ep)
                        st.markdown(report)

                    # LLM 검수의 추가 정보
                    if val_result.get("_source") == "LLM":
                        if val_result.get("key_strengths"):
                            st.markdown("**💪 강점**")
                            for s in val_result["key_strengths"]:
                                st.markdown(f"- {s}")
                        if val_result.get("concrete_fixes"):
                            st.markdown("**🛠 구체적 수정 제안**")
                            for f in val_result["concrete_fixes"]:
                                st.markdown(f"- {f}")

                    # 재집필 버튼
                    if verdict == "REDO":
                        st.warning("⚠️ 재집필 권장 등급입니다.")
                        if st.button(
                            "🔄 약점 보완 재집필 실행",
                            use_container_width=True,
                            key=f"redo_{selected_ep}",
                            type="primary",
                        ):
                            with st.spinner("약점 보완 재집필 중... (Opus 사용)"):
                                redo_text = call_claude_opus(
                                    build_episode_redo_prompt(
                                        current_ep,
                                        selected_ep,
                                        val_result,
                                        st.session_state.concept_card,
                                        json.dumps(st.session_state.character_bible, ensure_ascii=False),
                                    ),
                                    max_tokens=MAX_TOKENS_EPISODE,
                                )
                                if rating == "19금":
                                    st.session_state.episodes_19[selected_ep] = redo_text
                                else:
                                    st.session_state.episodes_15[selected_ep] = redo_text
                                # 검수 결과 초기화 (재검수 유도)
                                if selected_ep in st.session_state.validation_results:
                                    del st.session_state.validation_results[selected_ep]
                                st.success(f"✅ EP{selected_ep} 재집필 완료 ({len(redo_text)}자)")
                                st.rerun()

                # 25화 누적 대시보드 (val_count >= 5 시점부터 표시)
                val_count = len(st.session_state.validation_results)
                if val_count >= 5:
                    with st.expander(
                        f"📈 누적 검수 대시보드 ({val_count}/25화)",
                        expanded=(val_count >= 25 and not st.session_state.post_25_decided),
                    ):
                        history = list(st.session_state.validation_results.values())
                        summary = summarize_cumulative_25(history, total_eps=len(target_arc) if target_arc else 50)

                        col_d1, col_d2, col_d3 = st.columns(3)
                        with col_d1:
                            st.metric("검수 회차 수", summary["n_episodes"])
                        with col_d2:
                            st.metric("평균 종합 점수", f"{summary['avg_overall']:.1f}")
                        with col_d3:
                            cum_pass = VALIDATION_THRESHOLDS["cumulative_pass"]
                            status = "✅ 통과" if summary["avg_overall"] >= cum_pass else "⚠️ 미달"
                            st.metric("누적 합격선", f"{cum_pass}/{status}")

                        st.markdown("**축별 평균 점수**")
                        for axis, avg in summary["axis_avgs"].items():
                            weight = WUXIA_VALIDATION_WEIGHTS.get(axis, 0)
                            emoji = "🟢" if avg >= 75 else ("🟡" if avg >= 65 else "🔴")
                            st.markdown(f"- {emoji} {axis} (가중치 {int(weight*100)}%): **{avg:.1f}점**")

                        if summary["frequent_missing"]:
                            st.markdown("**자주 누락되는 재료**")
                            for m, cnt in summary["frequent_missing"]:
                                st.caption(f"- {m} ({cnt}회 누락)")

                        st.markdown("**📋 권장 사항**")
                        st.info(summary["recommendation"])

                        # 26화 이후 모드 결정 (25화 도달 후)
                        if val_count >= 25 and not st.session_state.post_25_decided:
                            st.markdown("---")
                            st.markdown("### 🎯 26화 이후 검수 모드 결정")
                            col_post1, col_post2, col_post3 = st.columns(3)
                            with col_post1:
                                if st.button("🤖 전체 자동 모드", use_container_width=True, key="post25_auto"):
                                    st.session_state.validation_mode = "all_auto"
                                    st.session_state.post_25_decided = True
                                    st.success("✅ 전체 자동 검수 모드로 전환")
                                    st.rerun()
                            with col_post2:
                                if st.button("⚡ 전환점만 자동", use_container_width=True, key="post25_trans"):
                                    st.session_state.validation_mode = "transition_only"
                                    st.session_state.post_25_decided = True
                                    st.success("✅ 전환점 자동 검수 모드로 전환")
                                    st.rerun()
                            with col_post3:
                                if st.button("✋ 수동 검수만", use_container_width=True, key="post25_manual"):
                                    st.session_state.validation_mode = "all_manual"
                                    st.session_state.post_25_decided = True
                                    st.success("✅ 수동 검수 모드로 전환")
                                    st.rerun()

                # 독자 시뮬레이터
                with st.expander("👥 독자 시뮬레이터", expanded=False):
                    persona_choice = st.selectbox(
                        "페르소나",
                        list(READER_PERSONAS.keys()),
                        format_func=lambda k: READER_PERSONAS[k]["label"],
                    )
                    if st.button("독자 피드백 받기", key=f"sim_{selected_ep}"):
                        with st.spinner("독자 시뮬레이션 중..."):
                            feedback = call_claude(
                                build_reader_simulation_prompt(
                                    current_ep, persona_choice,
                                    st.session_state.concept_card.get("genre", ""),
                                ),
                                max_tokens=2000,
                            )
                            st.markdown(feedback)


# ══════════════════════════════════════════════
# Sidebar (버전 정보 + 통계)
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 👖 WUXIA ENGINE")
    st.markdown('<span class="version-badge">v2.0</span>', unsafe_allow_html=True)
    st.markdown("**Build:** 2026-04-29")
    st.markdown("---")

    st.markdown("#### 📊 작업 현황")
    if st.session_state.concept_card:
        st.markdown(f"✅ 컨셉: {st.session_state.concept_card.get('title', '')[:20]}")
    else:
        st.markdown("⬜ 컨셉 미생성")

    if st.session_state.core_arc:
        st.markdown(f"✅ Core Arc: {len(st.session_state.core_arc)}화")
    else:
        st.markdown("⬜ Core Arc 미생성")

    if st.session_state.character_bible:
        st.markdown(f"✅ 캐릭터 바이블")
    else:
        st.markdown("⬜ 캐릭터 미생성")

    ep19_count = len(st.session_state.episodes_19)
    ep15_count = len(st.session_state.episodes_15)
    st.markdown(f"✍️ 집필: 19금 {ep19_count}화 / 15금 {ep15_count}화")

    # v2.0 자가 검수 현황
    val_count = len(st.session_state.validation_results)
    if val_count > 0:
        avg = sum(v.get("overall", 0) for v in st.session_state.validation_results.values()) / val_count
        st.markdown(f"🔬 검수: {val_count}화 (평균 {avg:.1f}점)")

    if st.session_state.wuxia_idea_seed_data:
        st.markdown("🌱 IdeaSeed 로딩됨")

    st.markdown("---")
    st.markdown("#### ⚙️ v2.0 시스템")
    st.markdown(f"- 공식: {len(WUXIA_FORMULAS)}개")
    st.markdown(f"- 주인공 유형: {len(PROTAGONIST_TYPES)}개 (+ subtype)")
    st.markdown(f"- 인물 역할: {len(WUXIA_CHARACTER_ROLES)}개 ⭐ NEW")
    st.markdown(f"- 마음 흐름: {len(WUXIA_HERO_MIND_FLOW.get('stages', []))}단계 ⭐ NEW")
    st.markdown(f"- 직업 팩: {len(PROFESSION_PACK)}개")
    st.markdown(f"- 모티프: {len(NARRATIVE_MOTIFS)}개")
    st.markdown(f"- 독자 페르소나: {len(READER_PERSONAS)}개")

    st.markdown("---")
    st.markdown("#### 🔬 자가 검수 (5축)")
    for axis, weight in WUXIA_VALIDATION_WEIGHTS.items():
        st.caption(f"- {axis}: {int(weight*100)}%")

    st.markdown("---")
    st.caption("© 2026 BLUE JEANS PICTURES")
