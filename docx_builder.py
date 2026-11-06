"""
👖 BLUE JEANS WUXIA ENGINE — docx_builder.py
DOCX 출력 모듈
- 회차별 DOCX (수정 편의)
- 시즌 전체 DOCX (피칭/보관용)
- 기획서 DOCX (컨셉 + 캐릭터 + 아크)
- 무공 대전 DOCX (별첨 제출용 설정집) ★ v2.7.0 신규
© 2026 BLUE JEANS PICTURES

[변경 이력]
v2.8.1 (2026-11-06) — 원고 서식 재복구 (사고 패턴 F 재발 대응)
  · [사고 원인] 2026-07-27 v2.8.0(둥근 따옴표·함초롬바탕·여백 2.0cm)이
    완성됐지만, 2026-07-28 v2.7.2(A32·구분선 정렬) 패치가 v2.8.0이 아닌
    v2.7.1 파일 위에 얹혀 커밋되면서 v2.8.0 전체가 다시 소실됐다.
    같은 서식 기능의 소실은 v2.2.0에 이어 두 번째다.
  · 재적용 범위 — v2.7.2의 _is_scene_break()·_add_scene_break()는 보존
    — to_smart_quotes(): 곧은 따옴표 → 둥근 따옴표. 줄 단위 열림/닫힘,
      영문 아포스트로피(don't) 예외, 멱등. DOCX 출력 경로 전용이며
      session_state의 회차 본문은 수정하지 않는다 (코드 작업 규칙 7)
    — MANUSCRIPT_FONT = "함초롬바탕": 회차·시즌 DOCX의 제목·본문·구분선
      (기획서·무공 대전은 맑은 고딕 유지)
    — PAGE_MARGIN_CM = 2.0 + _setup_page(): DOCX 4종 A4·여백 통일
  · 재발 방지: 패치 기준 파일은 항상 GitHub 최신 커밋에서 직접 받는다

v2.7.2 (2026-07-28) — 장면 구분선 가운데 정렬
  · _is_scene_break() 신설 — 기호로만 이루어진 짧은 줄을 장면 구분선으로
    판정 (*** / * * * / ··· / ※ / ◇ 등)
  · build_episode_docx()·build_season_docx() 본문 루프에 구분선 분기 추가
    — 가운데 정렬 + 위아래 여백 10pt (기존 본문 줄 서식은 그대로)
  · 작가 원고 메모 반영: 아미고 EP002의 *** 3건이 좌측 정렬로 나오던 문제
  · 본문 문자열 자체는 건드리지 않는다 (코드 작업 규칙 7 — 본문은 작가 영역)

v2.7.0 (2026-07-26) — 무공 대전 별첨 문서
  · build_martial_codex_docx() 신설
    원고 완료 후 작품 제안서에 별첨으로 제출하는 완성 설정집.
    표지 / 무공 체계 개관 / 경지 서열 / 문파별 장 / 무공 개별 항목 /
    기보·무기 / 금기 / 용어 색인(한글·한자·영문) 구성.
  · 용어 색인은 한글·한자·영문 3단. 라인웹툰 영문 동시 출시 시
    번역 대조표로 그대로 쓴다 (한자 처리 글로벌 친화 원칙).

v2.1.8 (2026-07-23) — 원고 서식 정비
  · 회차 DOCX 상단 메타 정보 라인(장르·분량·수위·플랫폼) 제거
  · 본문 빈 단락 제거 (이중 간격 방지) — 회차·시즌 공통
  · 행간 1.6 → 1.5 (전남편 검토용 원고의 지문 서식 기준)
  · (기존 헤더의 'WEB NOVEL ENGINE v2.6' 표기는 이식 당시
    잔재로, WUXIA ENGINE 표기로 정정)
"""

import io
from datetime import datetime

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ══════════════════════════════════════════════
# 디자인 상수
# ══════════════════════════════════════════════
NAVY = RGBColor(0x19, 0x19, 0x70)
YELLOW = RGBColor(0xFF, 0xCB, 0x05)
DARK = RGBColor(0x1A, 0x1A, 0x2E)
DIM = RGBColor(0x8E, 0x8E, 0x99)
LIGHT_BG = "EEEEF6"
YELLOW_BG = "FFCB05"

BODY_FONT = "맑은 고딕"  # 범용. 나눔고딕으로도 변경 가능
HEADING_FONT = "맑은 고딕"

# v2.8.1: 원고 서식 (회차·시즌 DOCX 전용)
MANUSCRIPT_FONT = "함초롬바탕"   # 원고 본문·제목. 곧은 따옴표·맑은 고딕은 AI 원고 신호
PAGE_MARGIN_CM = 2.0            # DOCX 4종 공통 상·하·좌·우 여백
SMART_QUOTES = True             # 출력 시 둥근 따옴표 변환 on/off


# ══════════════════════════════════════════════
# 공통 유틸
# ══════════════════════════════════════════════
# ── v2.8.1: 둥근 따옴표 · 페이지 설정 ──
def _is_latin_letter(ch):
    return bool(ch) and (("a" <= ch.lower() <= "z") or ch.isdigit())


def _smart_quotes_line(line):
    """한 줄 안에서 곧은 따옴표를 열림/닫힘 교대로 둥근 따옴표로 바꾼다."""
    out = []
    dq_open = False
    sq_open = False
    n = len(line)
    # 짝 없는 작은따옴표(홀수 개)의 마지막 하나는 닫는 모양으로 둔다
    # 예) "…….'" → “…….’” (엔진 원문 실측 사례)
    sq_total = line.count("'")
    sq_seen = 0
    for i, ch in enumerate(line):
        if ch == "\u201c":
            dq_open = True
        elif ch == "\u201d":
            dq_open = False
        elif ch == "\u2018":
            sq_open = True
        elif ch == "\u2019":
            sq_open = False

        if ch == '"':
            out.append("\u201d" if dq_open else "\u201c")
            dq_open = not dq_open
        elif ch == "'":
            prev = line[i - 1] if i > 0 else ""
            nxt = line[i + 1] if i + 1 < n else ""
            sq_seen += 1
            if _is_latin_letter(prev) and _is_latin_letter(nxt):
                out.append("\u2019")          # 영문 아포스트로피 (don't)
            elif sq_total % 2 == 1 and sq_seen == sq_total and not sq_open:
                out.append("\u2019")          # 짝 없는 마지막 하나
            else:
                out.append("\u2019" if sq_open else "\u2018")
                sq_open = not sq_open
        else:
            out.append(ch)
    return "".join(out)


def to_smart_quotes(text):
    """곧은 따옴표 → 둥근 따옴표 (v2.8.1 재적용).

    - 곧은 따옴표는 편집자·심사자에게 AI 생성 원고 신호로 읽힌다.
    - 단락(줄) 단위로 열림/닫힘을 판정한다. 한국 원고의 대사는
      한 줄에서 열고 닫는 것이 표준이므로 줄 경계에서 상태를 초기화한다.
    - 이미 둥근 따옴표인 문자는 건드리지 않는다 (멱등).
    - 원본 문자열을 수정하지 않고 새 문자열을 반환한다.
    """
    if not SMART_QUOTES or not isinstance(text, str) or not text:
        return text
    if '"' not in text and "'" not in text:
        return text
    return "\n".join(_smart_quotes_line(ln) for ln in text.split("\n"))


def _setup_page(doc):
    """A4 + 상·하·좌·우 PAGE_MARGIN_CM 여백 (v2.8.1)."""
    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.top_margin = Cm(PAGE_MARGIN_CM)
    section.bottom_margin = Cm(PAGE_MARGIN_CM)
    section.left_margin = Cm(PAGE_MARGIN_CM)
    section.right_margin = Cm(PAGE_MARGIN_CM)
    return section


# ── v2.7.2: 장면 구분선 ──
# 기호로만 이루어진 짧은 줄을 장면 구분선으로 본다.
# 예) ***  / * * *  / ＊＊＊ / ··· / ※ / ◇ / ---
_SCENE_BREAK_CHARS = set("*＊·•◦・∙※◇◆◈○●□■△▲—–―-~=＝#§†✦✧")


def _is_scene_break(line):
    """장면 구분선 여부 판정.

    기호 문자로만 이루어져 있고 12자 이하인 줄만 구분선으로 인정한다.
    '——20년 전.' 처럼 글자가 섞인 줄은 일반 본문으로 남는다.
    """
    s = (line or "").strip()
    if not s or len(s) > 12:
        return False
    core = s.replace(" ", "")
    if not core:
        return False
    return all(ch in _SCENE_BREAK_CHARS for ch in core)


def _add_scene_break(doc, text):
    """장면 구분선 단락 추가 — 가운데 정렬 + 위아래 여백."""
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_before = Pt(10)
    para.paragraph_format.space_after = Pt(10)
    para.paragraph_format.line_spacing = 1.5
    _add_run(para, text.strip(), font=MANUSCRIPT_FONT, size=11, color=DARK)
    return para


def _set_cell_bg(cell, color_hex):
    """셀 배경색 설정."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tc_pr.append(shd)


def _add_run(paragraph, text, font=BODY_FONT, size=11, bold=False,
             color=None, italic=False):
    """스타일링된 run 추가."""
    run = paragraph.add_run(text)
    run.font.name = font
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = color
    # 한글 폰트 설정
    r = run._element
    rpr = r.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr")
        r.insert(0, rpr)
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), font)
    return run


def _section_header_yellow(doc, ko_text, en_text=""):
    """노란색 섹션 헤더 (블루진 스타일)."""
    table = doc.add_table(rows=1, cols=1)
    cell = table.rows[0].cells[0]
    _set_cell_bg(cell, YELLOW_BG)
    para = cell.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _add_run(para, ko_text, font=HEADING_FONT, size=12, bold=True, color=NAVY)
    if en_text:
        _add_run(para, f"   {en_text}", font=HEADING_FONT, size=9, bold=False, color=NAVY)


def _horizontal_rule(doc):
    """수평선."""
    para = doc.add_paragraph()
    pPr = para._element.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "191970")
    pBdr.append(bottom)
    pPr.append(pBdr)


def _meta_line(doc, label, value):
    """메타 정보 한 줄 (라벨 + 값)."""
    para = doc.add_paragraph()
    _add_run(para, f"{label}: ", size=9, bold=True, color=DIM)
    _add_run(para, str(value), size=9, color=DARK)


# ══════════════════════════════════════════════
# 1. 회차별 DOCX (수정 편의)
# ══════════════════════════════════════════════
def build_episode_docx(episode_text, episode_number, concept=None,
                       plot=None, rating="19", platform="카카오페이지"):
    """
    단일 회차 DOCX 생성 — 수정 편의 중심.
    
    Args:
        episode_text: 본문 (첫 줄에 제목 포함)
        episode_number: 회차 번호
        concept: 컨셉 카드 (optional)
        plot: 회차 플롯 (optional)
        rating: '19' or '15'
        platform: 플랫폼명
    
    Returns:
        bytes — DOCX 파일 바이너리
    """
    doc = Document()

    # 페이지 설정 — v2.8.1: A4 + 여백 2.0cm (_setup_page 통합)
    _setup_page(doc)

    # v2.8.1: 곧은 따옴표 → 둥근 따옴표 (출력 경로 전용, 원본 미변경)
    episode_text = to_smart_quotes(episode_text or "")

    # 본문 첫 줄에서 제목 추출
    lines = episode_text.strip().split("\n")
    if lines and lines[0].strip():
        title_line = lines[0].strip()
        body_start = 1
        # 빈 줄 건너뛰기
        while body_start < len(lines) and not lines[body_start].strip():
            body_start += 1
        body = "\n".join(lines[body_start:])
    else:
        title_line = f"EP{episode_number}"
        body = episode_text

    # ── 제목 ──
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _add_run(title_para, title_line, font=MANUSCRIPT_FONT, size=20, bold=True, color=NAVY)

    # v2.1.8: 메타 정보 라인(장르·분량·수위·플랫폼) 제거 — 원고에는 제목과 본문만
    _horizontal_rule(doc)

    # ── 본문 ──
    # v2.1.8: 빈 줄은 단락으로 만들지 않음 (이중 간격 방지),
    #         행간 1.6 → 1.5 (전남편 검토용 지문 서식 기준)
    # v2.7.2: *** 등 장면 구분선은 가운데 정렬
    for line in body.split("\n"):
        if not line.strip():
            continue
        if _is_scene_break(line):
            _add_scene_break(doc, line)
            continue
        para = doc.add_paragraph()
        para.paragraph_format.space_after = Pt(6)
        para.paragraph_format.line_spacing = 1.5
        _add_run(para, line, font=MANUSCRIPT_FONT, size=11, color=DARK)

    # ── 푸터 (플롯 정보가 있으면) ──
    if plot:
        doc.add_page_break()
        _section_header_yellow(doc, "회차 메타", "EPISODE META")

        opening = plot.get("opening", {})
        if opening:
            _meta_line(doc, "첫 문장", opening.get("hook_line", ""))
            _meta_line(doc, "리캡 방식", opening.get("recap_method", ""))
            _meta_line(doc, "독자 질문", opening.get("question", ""))

        cliff = plot.get("cliffhanger", {})
        if cliff:
            _meta_line(doc, "클리프행어 유형", cliff.get("type", ""))
            _meta_line(doc, "클리프행어 내용", cliff.get("content", ""))
            _meta_line(doc, "다음 회차 연결", cliff.get("next_ep_connection", ""))

    # 저장
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ══════════════════════════════════════════════
# 2. 시즌 전체 DOCX
# ══════════════════════════════════════════════
def build_season_docx(episodes_dict, concept, rating="19", platform="카카오페이지"):
    """
    시즌 전체 DOCX 생성 — 피칭/보관용.
    
    Args:
        episodes_dict: {ep_num: episode_text, ...}
        concept: 컨셉 카드
        rating: '19' or '15'
    
    Returns:
        bytes
    """
    # v2.8.1: 곧은 따옴표 → 둥근 따옴표 (출력 경로 전용, 원본 미변경)
    episodes_dict = {
        k: to_smart_quotes(v or "")
        for k, v in (episodes_dict or {}).items()
    }

    doc = Document()

    # v2.8.1: A4 + 여백 2.0cm (_setup_page 통합)
    _setup_page(doc)

    # ── 커버 페이지 ──
    for _ in range(3):
        doc.add_paragraph()

    tagline = doc.add_paragraph()
    tagline.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(tagline, "BLUE JEANS PICTURES", font=HEADING_FONT, size=10, bold=True, color=NAVY)

    for _ in range(2):
        doc.add_paragraph()

    cover_title = doc.add_paragraph()
    cover_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(cover_title, concept.get("title", ""), font=HEADING_FONT, size=32, bold=True, color=NAVY)

    for _ in range(2):
        doc.add_paragraph()

    logline_para = doc.add_paragraph()
    logline_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(logline_para, to_smart_quotes(concept.get("logline", "")),
             size=12, italic=True, color=DARK)

    for _ in range(5):
        doc.add_paragraph()

    meta_para = doc.add_paragraph()
    meta_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(meta_para, concept.get("genre", ""), size=11, color=NAVY)
    _add_run(meta_para, "   |   ", size=11, color=DIM)
    _add_run(meta_para, f"{len(episodes_dict)}화 · {rating}금", size=11, color=NAVY)

    date_para = doc.add_paragraph()
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(date_para, datetime.now().strftime("%Y.%m.%d"), size=10, color=DIM)

    doc.add_page_break()

    # ── 목차 ──
    _section_header_yellow(doc, "목차", "CONTENTS")
    doc.add_paragraph()

    for ep_num in sorted(episodes_dict.keys()):
        text = episodes_dict[ep_num]
        first_line = text.strip().split("\n")[0] if text.strip() else f"EP{ep_num}"
        toc_para = doc.add_paragraph()
        _add_run(toc_para, f"EP{ep_num:03d}", size=10, bold=True, color=NAVY)
        _add_run(toc_para, f"   {first_line}", size=10, color=DARK)

    doc.add_page_break()

    # ── 본문 ──
    for ep_num in sorted(episodes_dict.keys()):
        text = episodes_dict[ep_num]
        lines = text.strip().split("\n")

        if lines and lines[0].strip():
            title_line = lines[0].strip()
            body_start = 1
            while body_start < len(lines) and not lines[body_start].strip():
                body_start += 1
            body = "\n".join(lines[body_start:])
        else:
            title_line = f"EP{ep_num}"
            body = text

        # 회차 제목
        title_para = doc.add_paragraph()
        title_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
        _add_run(title_para, title_line, font=MANUSCRIPT_FONT, size=18, bold=True, color=NAVY)

        # 본문 — v2.1.8: 빈 단락 제거 + 행간 1.5 (회차 DOCX와 동일 서식)
        # v2.7.2: *** 등 장면 구분선은 가운데 정렬
        for line in body.split("\n"):
            if not line.strip():
                continue
            if _is_scene_break(line):
                _add_scene_break(doc, line)
                continue
            para = doc.add_paragraph()
            para.paragraph_format.space_after = Pt(6)
            para.paragraph_format.line_spacing = 1.5
            _add_run(para, line, font=MANUSCRIPT_FONT, size=11, color=DARK)

        # 회차 구분
        doc.add_page_break()

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ══════════════════════════════════════════════
# 3. 기획서 DOCX (컨셉 + 캐릭터 + 아크)
# ══════════════════════════════════════════════
def build_proposal_docx(concept, character_bible=None, core_arc=None,
                        plant_map=None):
    """
    기획서 DOCX 생성 — 투자 피칭용.
    """
    doc = Document()

    # v2.8.1: A4 + 여백 2.0cm (_setup_page 통합)
    _setup_page(doc)

    # ── 커버 ──
    for _ in range(3):
        doc.add_paragraph()

    company = doc.add_paragraph()
    company.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(company, "BLUE JEANS PICTURES", font=HEADING_FONT, size=10, bold=True, color=NAVY)

    for _ in range(2):
        doc.add_paragraph()

    cover_title = doc.add_paragraph()
    cover_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(cover_title, concept.get("title", ""), font=HEADING_FONT, size=36, bold=True, color=NAVY)

    doc.add_paragraph()

    sub_title = doc.add_paragraph()
    sub_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(sub_title, "작품 기획서", font=HEADING_FONT, size=14, color=DIM)

    for _ in range(3):
        doc.add_paragraph()

    logline_para = doc.add_paragraph()
    logline_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(logline_para, concept.get("logline", ""), size=12, italic=True, color=DARK)

    doc.add_page_break()

    # ── 개요 ──
    _section_header_yellow(doc, "개요", "OVERVIEW")

    _meta_line(doc, "제목", concept.get("title", ""))
    _meta_line(doc, "장르", concept.get("genre", ""))
    _meta_line(doc, "형식", "웹소설")
    tags = concept.get("formula_tags", [])
    if tags:
        _meta_line(doc, "태그", " · ".join(tags))
    config = concept.get("serial_config", {})
    if config:
        _meta_line(doc, "Core Arc", f"{config.get('core_eps', 50)}화")
        _meta_line(doc, "수위", config.get("rating_mode", ""))
        _meta_line(doc, "과금 전환", f"EP{config.get('paywall_ep', 25)}")

    doc.add_paragraph()

    # ── 로그라인 ──
    _section_header_yellow(doc, "로그라인", "LOGLINE")
    para = doc.add_paragraph()
    _add_run(para, concept.get("logline", ""), size=11, color=DARK)

    doc.add_paragraph()

    # ── 시놉시스 ──
    _section_header_yellow(doc, "시놉시스", "SYNOPSIS")
    for para_text in concept.get("synopsis", "").split("\n"):
        if para_text.strip():
            para = doc.add_paragraph()
            para.paragraph_format.space_after = Pt(6)
            _add_run(para, para_text, size=11, color=DARK)

    doc.add_paragraph()

    # ── 시즌 질문 ──
    _section_header_yellow(doc, "시즌 질문", "SEASON QUESTIONS")
    sq = concept.get("season_questions", {})
    _meta_line(doc, "로맨스 축", sq.get("romance", ""))
    _meta_line(doc, "미스터리 축", sq.get("mystery", ""))

    doc.add_paragraph()

    # ── 세계관 ──
    _section_header_yellow(doc, "세계관", "WORLD")
    para = doc.add_paragraph()
    _add_run(para, concept.get("world", ""), size=11, color=DARK)

    doc.add_paragraph()

    # ── 캐릭터 ──
    _section_header_yellow(doc, "캐릭터", "CHARACTERS")

    # 주인공
    p = concept.get("protagonist", {})
    if p.get("name"):
        para = doc.add_paragraph()
        _add_run(para, "▶ 주인공 ", font=HEADING_FONT, size=12, bold=True, color=NAVY)
        _add_run(para, p.get("name", ""), font=HEADING_FONT, size=12, bold=True, color=DARK)
        _meta_line(doc, "Goal", p.get("goal", ""))
        _meta_line(doc, "Need", p.get("need", ""))
        _meta_line(doc, "Fatal Flaw", p.get("fatal_flaw", ""))
        doc.add_paragraph()

    # 상대역
    for i, li in enumerate(concept.get("love_interests", []), 1):
        para = doc.add_paragraph()
        _add_run(para, f"▶ 상대역 {i} ", font=HEADING_FONT, size=12, bold=True, color=NAVY)
        _add_run(para, f"{li.get('name', '')} ({li.get('role', '')})",
                 font=HEADING_FONT, size=12, bold=True, color=DARK)
        _meta_line(doc, "매력", li.get("appeal", ""))
        _meta_line(doc, "갈등", li.get("conflict", ""))
        doc.add_paragraph()

    # 빌런
    v = concept.get("villain", {})
    if v.get("name"):
        para = doc.add_paragraph()
        _add_run(para, "▶ 빌런 ", font=HEADING_FONT, size=12, bold=True, color=NAVY)
        _add_run(para, f"{v.get('name', '')} ({v.get('role', '')})",
                 font=HEADING_FONT, size=12, bold=True, color=DARK)
        _meta_line(doc, "Wants", v.get("wants", ""))
        _meta_line(doc, "Justification", v.get("justification", ""))
        _meta_line(doc, "Limits", v.get("limits", ""))
        _meta_line(doc, "Win Rate", v.get("win_rate", ""))
        doc.add_paragraph()

    # ── Core Arc 요약 ──
    if core_arc:
        doc.add_page_break()
        _section_header_yellow(doc, "Core Arc", "STRUCTURE")

        for block in core_arc:
            para = doc.add_paragraph()
            _add_run(para, f"[블록 {block.get('block_no', '')}] ",
                     font=HEADING_FONT, size=11, bold=True, color=NAVY)
            _add_run(para, f"{block.get('ep_range', '')} · {block.get('phase', '')}",
                     size=11, bold=True, color=DARK)

            theme_para = doc.add_paragraph()
            _add_run(theme_para, block.get("theme", ""), size=10, color=DIM)

            for ep in block.get("episodes", []):
                ep_para = doc.add_paragraph()
                _add_run(ep_para, f"  EP{ep.get('ep', ''):03d}. ",
                         size=10, bold=True, color=NAVY)
                _add_run(ep_para, ep.get("title", ""),
                         size=10, bold=True, color=DARK)
                _add_run(ep_para, f"  — {ep.get('summary', '')}",
                         size=10, color=DARK)
                _add_run(ep_para, f"  [{ep.get('cliffhanger_type', '')}]",
                         size=9, italic=True, color=DIM)
            doc.add_paragraph()

    # ── 떡밥 맵 ──
    if plant_map and plant_map.get("plants"):
        doc.add_page_break()
        _section_header_yellow(doc, "떡밥 맵", "PLANT & PAYOFF")

        for p in plant_map["plants"]:
            para = doc.add_paragraph()
            _add_run(para, f"🌱 {p.get('name', '')} ",
                     font=HEADING_FONT, size=11, bold=True, color=NAVY)
            _add_run(para, f"({p.get('type', '')})",
                     size=9, italic=True, color=DIM)

            _meta_line(doc, "설명", p.get("description", ""))
            _meta_line(doc, "심기", f"EP{p.get('plant_ep', '')}")
            hints = p.get("hints", [])
            if hints:
                _meta_line(doc, "힌트", ", ".join([f"EP{h}" for h in hints]))
            _meta_line(doc, "회수", f"EP{p.get('payoff_ep', '')}")
            doc.add_paragraph()

    # ── 푸터 ──
    doc.add_page_break()
    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(footer, "© 2026 BLUE JEANS PICTURES", size=9, color=DIM)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ══════════════════════════════════════════════
# 4. 무공 대전 DOCX (별첨 제출용 설정집) — v2.7.0 신규
#
# 원고 완료 후 작품 제안서에 별첨으로 제출하는 완성 문서.
# 집필 보조 자료가 아니라 그 자체로 읽히는 세계관 설정집이다.
# 그래서 항목마다 원리·계보·대가·상성·습득 조건까지 싣는다.
# ══════════════════════════════════════════════
_TIER_ORDER = ["비전", "절기", "중급", "기초"]
_TIER_HANJA = {"비전": "祕傳", "절기": "絕技", "중급": "中級", "기초": "基礎"}


def _codex_split_name(name):
    """'청수유수권(淸水流手拳)' → ('청수유수권', '淸水流手拳')."""
    import re as _re
    if not name:
        return "", ""
    m = _re.match(r"\s*([^()（）]+)[\(（]?([\u4e00-\u9fff]*)[\)）]?\s*$", str(name))
    if not m:
        return str(name).strip(), ""
    return m.group(1).strip(), (m.group(2) or "").strip()


def _codex_field_table(doc, entry):
    """무공 1종의 상세 표."""
    rows = [
        ("전승 계보", entry.get("lineage", "")),
        ("원리", entry.get("principle", "")),
        ("시연", entry.get("visual", "")),
        ("강점", entry.get("strength", "")),
        ("대가·한계", entry.get("cost", "")),
        ("상성", entry.get("counter", "")),
        ("습득 조건", entry.get("acquisition", "")),
    ]
    users = entry.get("users") or []
    if isinstance(users, list) and users:
        rows.append(("사용자", ", ".join(str(u) for u in users[:6])))
    if entry.get("planned_episodes"):
        rows.append(("등장", str(entry["planned_episodes"])))

    rows = [(lb, str(v).strip()) for lb, v in rows if str(v or "").strip()]
    if not rows:
        return

    table = doc.add_table(rows=len(rows), cols=2)
    table.autofit = True
    for i, (label, value) in enumerate(rows):
        c0, c1 = table.rows[i].cells
        _set_cell_bg(c0, LIGHT_BG)
        p0 = c0.paragraphs[0]
        _add_run(p0, label, size=9, bold=True, color=NAVY)
        p1 = c1.paragraphs[0]
        _add_run(p1, value, size=9.5, color=DARK)


def build_martial_codex_docx(martial_bible, concept=None, title_suffix="무공 대전"):
    """무공 대전 별첨 문서 DOCX 생성 (v2.7.0 신규).

    Args:
        martial_bible: 무공 대전 (확장 병합된 바이블)
        concept: 컨셉 카드 (제목·로그라인)
        title_suffix: 표지 부제

    Returns:
        DOCX 바이트열
    """
    concept = concept or {}
    martial_bible = martial_bible or {}
    doc = Document()

    # v2.8.1: A4 + 여백 2.0cm (_setup_page 통합)
    _setup_page(doc)

    work_title = concept.get("title") or "무제"

    # ── 표지 ──
    for _ in range(5):
        doc.add_paragraph()
    tp = doc.add_paragraph()
    tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(tp, work_title, font=HEADING_FONT, size=28, bold=True, color=NAVY)

    sp = doc.add_paragraph()
    sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(sp, title_suffix, font=HEADING_FONT, size=16, bold=True, color=DARK)

    sp2 = doc.add_paragraph()
    sp2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(sp2, "武功大全 · MARTIAL CODEX", font=HEADING_FONT, size=11, color=DIM)

    if concept.get("logline"):
        doc.add_paragraph()
        lp = doc.add_paragraph()
        lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _add_run(lp, str(concept["logline"]), size=10.5, italic=True, color=DARK)

    for _ in range(6):
        doc.add_paragraph()
    dp = doc.add_paragraph()
    dp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(dp, datetime.now().strftime("%Y. %m. %d."), size=10, color=DIM)
    bp = doc.add_paragraph()
    bp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(bp, "BLUE JEANS PICTURES", size=10, bold=True, color=NAVY)

    # ── 통계 집계 ──
    fa = [g for g in (martial_bible.get("faction_arts") or [])
          if isinstance(g, dict)]
    all_arts = []
    for g in fa:
        for a in (g.get("arts") or []):
            if isinstance(a, dict) and a.get("name"):
                a = dict(a)
                a.setdefault("faction", g.get("faction", ""))
                all_arts.append(a)

    # ── 개관 ──
    doc.add_page_break()
    _section_header_yellow(doc, "무공 체계 개관", "OVERVIEW")
    doc.add_paragraph()
    _meta_line(doc, "수록 무공", f"{len(all_arts)}종")
    _meta_line(doc, "수록 문파", f"{len(fa)}문파")
    tier_stat = {}
    for a in all_arts:
        t = str(a.get("tier") or "미분류").strip()
        tier_stat[t] = tier_stat.get(t, 0) + 1
    if tier_stat:
        order = [t for t in _TIER_ORDER if t in tier_stat] + \
                [t for t in tier_stat if t not in _TIER_ORDER]
        _meta_line(doc, "등급 분포",
                   " · ".join(f"{t} {tier_stat[t]}종" for t in order))

    mls = (martial_bible.get("martial_level_system") or "").strip()
    if mls:
        doc.add_paragraph()
        _section_header_yellow(doc, "경지·서열 체계", "REALMS")
        doc.add_paragraph()
        para = doc.add_paragraph()
        para.paragraph_format.line_spacing = 1.5
        _add_run(para, mls, size=10.5, color=DARK)

    # 등급 정의
    doc.add_paragraph()
    _section_header_yellow(doc, "무공 등급", "TIERS")
    doc.add_paragraph()
    tier_desc = {
        "비전": "문파 최고 절기. 장문인·계승자에게만 전수된다.",
        "절기": "문파를 상징하는 대표 무공. 상급 제자와 교사가 구사한다.",
        "중급": "제자 수련 과정의 실전 무공. 대련과 시합의 주력이다.",
        "기초": "입문 단계의 기본기. 경공·운기·보법 계열이 여기 속한다.",
    }
    tt = doc.add_table(rows=len(_TIER_ORDER) + 1, cols=3)
    hdr = tt.rows[0].cells
    for i, h in enumerate(["등급", "한자", "정의"]):
        _set_cell_bg(hdr[i], YELLOW_BG)
        _add_run(hdr[i].paragraphs[0], h, size=9, bold=True, color=NAVY)
    for i, t in enumerate(_TIER_ORDER, start=1):
        cells = tt.rows[i].cells
        _add_run(cells[0].paragraphs[0], t, size=9.5, bold=True, color=NAVY)
        _add_run(cells[1].paragraphs[0], _TIER_HANJA.get(t, ""), size=9.5, color=DIM)
        _add_run(cells[2].paragraphs[0], tier_desc.get(t, ""), size=9.5, color=DARK)

    # ── 문파별 장 ──
    for grp in fa:
        fac = str(grp.get("faction") or "").strip()
        arts = [a for a in (grp.get("arts") or [])
                if isinstance(a, dict) and a.get("name")]
        if not fac or not arts:
            continue

        doc.add_page_break()
        _section_header_yellow(doc, fac, "FACTION")
        doc.add_paragraph()

        if grp.get("faction_philosophy"):
            fp = doc.add_paragraph()
            fp.paragraph_format.line_spacing = 1.5
            _add_run(fp, str(grp["faction_philosophy"]), size=10.5,
                     italic=True, color=NAVY)
        if grp.get("signature"):
            _meta_line(doc, "대표 무공", grp["signature"])
        if grp.get("training"):
            _meta_line(doc, "수련 방식", grp["training"])
        _meta_line(doc, "수록", f"{len(arts)}종")

        def _tk(a):
            t = str(a.get("tier") or "")
            return _TIER_ORDER.index(t) if t in _TIER_ORDER else 99
        arts.sort(key=_tk)

        cur_tier = None
        for art in arts:
            tier = str(art.get("tier") or "미분류").strip()
            if tier != cur_tier:
                cur_tier = tier
                doc.add_paragraph()
                th = doc.add_paragraph()
                _add_run(th, f"— {tier}({_TIER_HANJA.get(tier, '')}) —",
                         font=HEADING_FONT, size=11, bold=True, color=NAVY)

            kor, han = _codex_split_name(art.get("name"))
            np_ = doc.add_paragraph()
            _add_run(np_, kor, font=HEADING_FONT, size=12.5, bold=True, color=DARK)
            if han:
                _add_run(np_, f"  {han}", font=HEADING_FONT, size=10.5, color=DIM)
            if art.get("name_en"):
                _add_run(np_, f"   {art['name_en']}", size=9, italic=True, color=DIM)
            if art.get("category"):
                _add_run(np_, f"   [{art['category']}]", size=9, color=DIM)

            _codex_field_table(doc, art)
            doc.add_paragraph()

    # ── 기보·무기·금기 ──
    def _simple_section(header, items, fields):
        rows = [it for it in (items or []) if isinstance(it, dict) and it.get("name")]
        if not rows:
            return
        doc.add_page_break()
        _section_header_yellow(doc, header, "")
        doc.add_paragraph()
        for it in rows:
            kor, han = _codex_split_name(it.get("name"))
            p = doc.add_paragraph()
            _add_run(p, kor, font=HEADING_FONT, size=11.5, bold=True, color=DARK)
            if han:
                _add_run(p, f"  {han}", size=10, color=DIM)
            for key, label in fields:
                v = str(it.get(key) or "").strip()
                if v:
                    _meta_line(doc, label, v)
            doc.add_paragraph()

    _simple_section("기보·영물", martial_bible.get("artifacts"),
                    [("type", "종류"), ("owner", "소유"), ("power", "능력"),
                     ("visual", "형상"), ("cost", "대가"),
                     ("reveal_timing", "공개 시점")])
    _simple_section("무기", martial_bible.get("weapons"),
                    [("faction", "문파"), ("form", "형태"), ("visual", "형상")])
    _simple_section("금기·부작용", martial_bible.get("forbidden"),
                    [("trigger", "발동 조건"), ("consequence", "결과")])

    # ── 용어 색인 (한글 · 한자 · 영문) ──
    index_rows = []
    for a in all_arts:
        kor, han = _codex_split_name(a.get("name"))
        if kor:
            index_rows.append((kor, han, str(a.get("name_en") or ""),
                               str(a.get("faction") or "")))
    for key in ("artifacts", "weapons"):
        for it in (martial_bible.get(key) or []):
            if isinstance(it, dict) and it.get("name"):
                kor, han = _codex_split_name(it["name"])
                if kor:
                    index_rows.append((kor, han, str(it.get("name_en") or ""), ""))
    index_rows = sorted(set(index_rows), key=lambda r: r[0])

    if index_rows:
        doc.add_page_break()
        _section_header_yellow(doc, "용어 색인", "GLOSSARY")
        p = doc.add_paragraph()
        _add_run(p, "영문 표기는 글로벌 동시 출시 시 번역 대조표로 사용합니다.",
                 size=9, italic=True, color=DIM)
        doc.add_paragraph()

        tb = doc.add_table(rows=len(index_rows) + 1, cols=4)
        hdr = tb.rows[0].cells
        for i, h in enumerate(["한글", "한자", "영문", "문파"]):
            _set_cell_bg(hdr[i], YELLOW_BG)
            _add_run(hdr[i].paragraphs[0], h, size=9, bold=True, color=NAVY)
        for i, row in enumerate(index_rows, start=1):
            cells = tb.rows[i].cells
            _add_run(cells[0].paragraphs[0], row[0], size=9, color=DARK)
            _add_run(cells[1].paragraphs[0], row[1], size=9, color=DIM)
            _add_run(cells[2].paragraphs[0], row[2], size=9, color=DARK)
            _add_run(cells[3].paragraphs[0], row[3], size=9, color=DIM)

    # ── 푸터 ──
    doc.add_page_break()
    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(footer, f"{work_title} · {title_suffix}", size=9, color=DIM)
    footer2 = doc.add_paragraph()
    footer2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(footer2, "© 2026 BLUE JEANS PICTURES", size=9, color=DIM)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
