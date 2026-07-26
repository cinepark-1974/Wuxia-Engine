"""
👖 BLUE JEANS WUXIA ENGINE — docx_builder.py
DOCX 출력 모듈
- 회차별 DOCX (수정 편의)
- 시즌 전체 DOCX (피칭/보관용)
- 기획서 DOCX (컨셉 + 캐릭터 + 아크)
© 2026 BLUE JEANS PICTURES

[변경 이력]
v2.2.1 (2026-07-26) — 페이지 여백 조정
  · A4 여백 2.5cm → 2.0cm (상·하·좌·우 동일)
  · PAGE_MARGIN_CM 상수로 분리 — 회차·시즌·기획서 DOCX 공통 적용

v2.2.0 (2026-07-26) — 함초롬바탕 스타일 체계 + 둥근 따옴표
  · [핵심] 원고 서식을 '스타일 기반'으로 전환
    — 문서 기본값(docDefaults)과 Normal 스타일에 함초롬바탕 주입
    — 명명 스타일 2종 신설: '에피소드 제목' / '웹소설본문'
    — 본문 run에 폰트를 직접 박지 않음 → 워드에서 스타일 하나만
      고치면 전체 원고 서식이 한 번에 바뀜 (작가 교정중 파일 방식)
  · [핵심] 곧은 따옴표 → 둥근 따옴표 자동 변환 (to_smart_quotes)
    — " → “ ” / ' → ‘ ’ 문맥 판정
    — 영문 축약형(don't)은 ’ 로 처리, 이미 둥근 따옴표는 보존
    — 「」『』 등 낫표는 손대지 않음
  · 머리말·꼬리말 신설 — 머리말 우측 〈작품 제목〉, 꼬리말 가운데
    페이지 번호 (교정중 파일과 동일)
  · [수정] 제목 오인식 버그 — 본문 첫 문장이 제목으로 승격되고
    본문에서 사라지던 문제. 제목 판별 규칙 신설
    (EP n / 제n화 / # 로 시작하거나, 30자 이하 + 종결부호 없음)
    미검출 시 'EP 01.' 형태를 자동 생성하고 본문은 손대지 않음
  · 본문 서식 교정중 파일 기준으로 재조정
    — 10.5pt / 행간 1.15 / 문단 뒤 간격 0 + 같은 스타일 간 간격 무시
  · 제목 아래 수평선 제거 (작가가 교정 단계에서 삭제한 요소)

v2.1.8 (2026-07-23) — 원고 서식 정비
  · 회차 DOCX 상단 메타 정보 라인(장르·분량·수위·플랫폼) 제거
  · 본문 빈 단락 제거 (이중 간격 방지) — 회차·시즌 공통
  · 행간 1.6 → 1.5 (전남편 검토용 원고의 지문 서식 기준)
  · (기존 헤더의 'WEB NOVEL ENGINE v2.6' 표기는 이식 당시
    잔재로, WUXIA ENGINE 표기로 정정)
"""

import io
import re
from datetime import datetime

from docx import Document
from docx.shared import Pt, Cm, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.style import WD_STYLE_TYPE
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

# ── 원고 기본 폰트 ────────────────────────────
# 작가 교정중 파일 기준. 이 한 줄만 바꾸면 전체 문서 서식이 따라옵니다.
# (한/글 계열 폰트. 워드 영문 등록명은 "HCR Batang")
MANUSCRIPT_FONT = "함초롬바탕"

BODY_FONT = MANUSCRIPT_FONT      # 본문
HEADING_FONT = MANUSCRIPT_FONT   # 제목·섹션 헤더

# ── 원고 서식 수치 (교정중 파일 실측값) ────────
TITLE_SIZE_PT = 18.0        # 에피소드 제목
BODY_SIZE_PT = 10.5         # 본문
BODY_LINE_SPACING = 1.15    # 행간
BODY_SPACE_AFTER_PT = 0.0   # 문단 뒤 간격 (contextualSpacing 병행)

# ── 페이지 설정 ────────────────────────────────
PAGE_MARGIN_CM = 2.0        # A4 상·하·좌·우 여백 (cm)

# ── 스타일 이름 ────────────────────────────────
STYLE_TITLE = "에피소드 제목"
STYLE_BODY = "웹소설본문"


# ══════════════════════════════════════════════
# 0. 따옴표 정규화 (곧은 따옴표 → 둥근 따옴표)
# ══════════════════════════════════════════════
# 여는 따옴표로 판정할 직전 문자
# (쉼표·말줄임표·콜론은 제외 — "대사," / "…" 처럼 닫는 자리가 더 흔함)
_OPENING_PREV = set(" \t\r\n\u00a0([{<«‘“「『《〈【〔—–―·")


def _is_opening_context(prev_char: str) -> bool:
    """직전 문자를 보고 '여는 따옴표' 자리인지 판정."""
    if prev_char == "":
        return True
    return prev_char in _OPENING_PREV


def _convert_line(line):
    """
    한 줄 변환 (1차: 문맥 판정).

    Returns:
        (chars, dq_index_list) — 문자 리스트와 큰따옴표가 놓인 위치
    """
    chars = []
    dq_idx = []
    prev = ""
    for ch in line:
        if ch == '"':
            dq_idx.append(len(chars))
            chars.append("“" if _is_opening_context(prev) else "”")
        elif ch == "'":
            chars.append("‘" if _is_opening_context(prev) else "’")
        else:
            chars.append(ch)
        prev = ch
    return chars, dq_idx


def to_smart_quotes(text):
    """
    곧은 따옴표를 둥근 따옴표로 변환.

      "대사"      → “대사”
      '독백'      → ‘독백’
      don't       → don’t   (영문 축약형은 닫는 형태 = 어퍼스트로피)

    이미 둥근 따옴표(“ ” ‘ ’)이거나 낫표(「」『』)면 그대로 둡니다.

    판정 방식
      1차 — '직전 문자' 문맥으로 여닫이 결정
      2차 — 한 줄 안의 큰따옴표 개수가 짝수인데 여닫이가 안 맞으면
            그 줄만 교대(여-닫-여-닫) 방식으로 다시 변환

    줄 단위로 처리하므로 따옴표 짝이 어긋난 원고에서도
    뒤 문단까지 연쇄로 망가지지 않습니다.
    """
    if not text or ('"' not in text and "'" not in text):
        return text

    result = []
    for line in text.split("\n"):
        chars, dq_idx = _convert_line(line)

        # 2차 보정 — 짝수 개인데 여닫이 불균형이면 교대 방식으로 덮어씀
        if dq_idx and len(dq_idx) % 2 == 0:
            opens = sum(1 for i in dq_idx if chars[i] == "“")
            if opens * 2 != len(dq_idx):
                for order, i in enumerate(dq_idx):
                    chars[i] = "“" if order % 2 == 0 else "”"

        result.append("".join(chars))
    return "\n".join(result)


def _t(text, smart=True):
    """출력 직전 텍스트 정규화."""
    if text is None:
        return ""
    text = str(text)
    return to_smart_quotes(text) if smart else text


# ══════════════════════════════════════════════
# 1. 스타일 장치 (함초롬바탕 기반)
# ══════════════════════════════════════════════
def _apply_font_to_rpr(rpr, font_name):
    """rPr 요소에 4가지 폰트 슬롯(ascii/hAnsi/eastAsia/cs)을 모두 지정."""
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for slot in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(slot), font_name)
    # 테마 폰트 참조가 남아 있으면 직접 지정이 무시되므로 제거
    for theme_slot in ("w:asciiTheme", "w:hAnsiTheme",
                       "w:eastAsiaTheme", "w:cstheme"):
        if rfonts.get(qn(theme_slot)) is not None:
            del rfonts.attrib[qn(theme_slot)]


def _set_doc_defaults(doc, font_name=MANUSCRIPT_FONT,
                      size_pt=BODY_SIZE_PT,
                      line_spacing=BODY_LINE_SPACING):
    """
    문서 기본값(docDefaults) 자체에 폰트를 심습니다.
    표·머리말·꼬리말처럼 스타일을 따로 안 먹인 요소까지 전부 따라옵니다.
    """
    styles_el = doc.styles.element

    dd = styles_el.find(qn("w:docDefaults"))
    if dd is None:
        dd = OxmlElement("w:docDefaults")
        styles_el.insert(0, dd)

    # run 기본값
    rpr_default = dd.find(qn("w:rPrDefault"))
    if rpr_default is None:
        rpr_default = OxmlElement("w:rPrDefault")
        dd.append(rpr_default)
    rpr = rpr_default.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr")
        rpr_default.append(rpr)
    _apply_font_to_rpr(rpr, font_name)

    half = str(int(round(size_pt * 2)))
    for tag in ("w:sz", "w:szCs"):
        el = rpr.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            rpr.append(el)
        el.set(qn("w:val"), half)

    # 문단 기본값
    ppr_default = dd.find(qn("w:pPrDefault"))
    if ppr_default is None:
        ppr_default = OxmlElement("w:pPrDefault")
        dd.append(ppr_default)
    ppr = ppr_default.find(qn("w:pPr"))
    if ppr is None:
        ppr = OxmlElement("w:pPr")
        ppr_default.append(ppr)
    spacing = ppr.find(qn("w:spacing"))
    if spacing is None:
        spacing = OxmlElement("w:spacing")
        ppr.append(spacing)
    spacing.set(qn("w:after"), "0")
    spacing.set(qn("w:line"), str(int(round(line_spacing * 240))))
    spacing.set(qn("w:lineRule"), "auto")


def _style_font(style, font_name=MANUSCRIPT_FONT):
    """스타일 정의 자체에 폰트 지정 (run에 직접 박지 않음)."""
    rpr = style.element.get_or_add_rPr()
    _apply_font_to_rpr(rpr, font_name)


def _style_contextual_spacing(style):
    """같은 스타일 문단끼리는 간격을 주지 않음 (교정중 파일 설정)."""
    ppr = style.element.get_or_add_pPr()
    if ppr.find(qn("w:contextualSpacing")) is None:
        ppr.append(OxmlElement("w:contextualSpacing"))


def _get_or_add_style(doc, name, style_type=WD_STYLE_TYPE.PARAGRAPH):
    try:
        return doc.styles[name]
    except KeyError:
        return doc.styles.add_style(name, style_type)


def setup_manuscript_styles(doc, font_name=MANUSCRIPT_FONT):
    """
    원고용 스타일 체계를 문서에 심습니다.

      Normal          — 함초롬바탕 10.5pt, 행간 1.15  (모든 스타일의 뿌리)
      에피소드 제목    — Normal 기반, 18pt 굵게
      웹소설본문       — Normal 기반, 10.5pt, 문단 뒤 간격 0

    작가는 워드에서 '웹소설본문' 스타일 하나만 수정하면
    원고 전체 서식이 한 번에 바뀝니다.
    """
    _set_doc_defaults(doc, font_name)

    # ── Normal (뿌리 스타일) ──
    normal = doc.styles["Normal"]
    normal.font.name = font_name
    normal.font.size = Pt(BODY_SIZE_PT)
    normal.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    _style_font(normal, font_name)
    npf = normal.paragraph_format
    npf.line_spacing = BODY_LINE_SPACING
    npf.space_before = Pt(0)
    npf.space_after = Pt(0)

    # ── 에피소드 제목 ──
    title_style = _get_or_add_style(doc, STYLE_TITLE)
    title_style.base_style = normal
    title_style.font.size = Pt(TITLE_SIZE_PT)
    title_style.font.bold = True
    title_style.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    _style_font(title_style, font_name)
    tpf = title_style.paragraph_format
    tpf.space_before = Pt(0)
    tpf.space_after = Pt(10)
    tpf.line_spacing = BODY_LINE_SPACING
    tpf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title_style.quick_style = True

    # ── 웹소설본문 ──
    body_style = _get_or_add_style(doc, STYLE_BODY)
    body_style.base_style = normal
    body_style.font.size = Pt(BODY_SIZE_PT)
    body_style.font.bold = False
    body_style.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    _style_font(body_style, font_name)
    bpf = body_style.paragraph_format
    bpf.space_before = Pt(0)
    bpf.space_after = Pt(BODY_SPACE_AFTER_PT)
    bpf.line_spacing = BODY_LINE_SPACING
    _style_contextual_spacing(body_style)
    body_style.quick_style = True

    return doc


# ══════════════════════════════════════════════
# 공통 유틸
# ══════════════════════════════════════════════
def _set_cell_bg(cell, color_hex):
    """셀 배경색 설정."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tc_pr.append(shd)


def _add_run(paragraph, text, font=None, size=None, bold=None,
             color=None, italic=None, smart=True):
    """
    run 추가.

    font=None / size=None / color=None 이면 폰트·크기·색을 run에 박지 않고
    문단 스타일에서 상속받습니다 (= 스타일 기반 서식).
    직접 지정이 필요한 곳(기획서 헤더 등)만 값을 넘깁니다.
    """
    run = paragraph.add_run(_t(text, smart))
    if font:
        run.font.name = font
        rpr = run._element.get_or_add_rPr()
        _apply_font_to_rpr(rpr, font)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color is not None:
        run.font.color.rgb = color
    return run


def _add_page_number_field(paragraph):
    """꼬리말 페이지 번호 필드."""
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(instr)
    run._r.append(end)
    return run


def _setup_header_footer(doc, header_text=""):
    """머리말(우측 작품명) + 꼬리말(가운데 페이지 번호). 교정중 파일 기준."""
    section = doc.sections[0]

    header_para = section.header.paragraphs[0]
    header_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if header_text:
        _add_run(header_para, f"〈{header_text}〉", size=9, color=DIM,
                 smart=False)

    footer_para = section.footer.paragraphs[0]
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_page_number_field(footer_para)


def _setup_page(doc):
    """A4 + 여백 2.0cm (상하좌우 동일)."""
    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.top_margin = Cm(PAGE_MARGIN_CM)
    section.bottom_margin = Cm(PAGE_MARGIN_CM)
    section.left_margin = Cm(PAGE_MARGIN_CM)
    section.right_margin = Cm(PAGE_MARGIN_CM)
    return section


def _new_manuscript_doc(header_text=""):
    """원고용 문서 초기화 — 페이지 + 스타일 + 머리말/꼬리말."""
    doc = Document()
    _setup_page(doc)
    setup_manuscript_styles(doc)
    _setup_header_footer(doc, header_text)
    return doc


def _section_header_yellow(doc, ko_text, en_text=""):
    """노란색 섹션 헤더 (블루진 스타일)."""
    table = doc.add_table(rows=1, cols=1)
    cell = table.rows[0].cells[0]
    _set_cell_bg(cell, YELLOW_BG)
    para = cell.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    _add_run(para, ko_text, font=HEADING_FONT, size=12, bold=True, color=NAVY)
    if en_text:
        _add_run(para, f"   {en_text}", font=HEADING_FONT, size=9,
                 bold=False, color=NAVY, smart=False)


def _horizontal_rule(doc):
    """수평선. (v2.2.0 원고에서는 미사용 — 기획서용으로만 유지)"""
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
    _add_run(para, f"{label}: ", size=9, bold=True, color=DIM, smart=False)
    _add_run(para, str(value), size=9, color=DARK)


# ══════════════════════════════════════════════
# 제목 / 본문 분리
# ══════════════════════════════════════════════
_TITLE_HEAD = re.compile(
    r"^\s*(?:#+\s*)?(?:EP\s*\.?\s*\d+|EPISODE\s*\d+|제?\s*\d+\s*화|\d+\s*화)\b",
    re.IGNORECASE,
)
_SENTENCE_END = ("。", ".", "!", "?", "…", ",", "”", "’", '"', "'", "」", "』")
_DIALOGUE_HEAD = ('"', "'", "“", "‘", "「", "『", "-", "—")


def _looks_like_title(line):
    """
    첫 줄이 '회차 제목'인지 판정.

    v2.2.0 이전에는 첫 줄을 무조건 제목으로 올려서,
    LLM이 제목 없이 본문부터 출력하면 첫 문장이 제목으로 승격되고
    본문에서 사라졌습니다 (아미고 EP001 사례).
    """
    s = (line or "").strip()
    if not s:
        return False
    if _TITLE_HEAD.match(s):
        return True
    if s.startswith("#"):
        return True
    if s.startswith(_DIALOGUE_HEAD):
        return False
    if len(s) <= 30 and not s.endswith(_SENTENCE_END):
        return True
    return False


def _clean_title(line):
    """마크다운 머리표(#) 제거."""
    return re.sub(r"^\s*#+\s*", "", (line or "").strip()).strip()


def _split_title_and_body(text, episode_number, title_override=None):
    """
    본문 텍스트에서 (제목, 본문)을 분리.

    Returns:
        (title_line, body_text)
    """
    text = (text or "").strip()
    lines = text.split("\n")

    if title_override:
        title = _clean_title(title_override)
        body = text
        if lines and _looks_like_title(lines[0]):
            body = "\n".join(lines[1:]).lstrip("\n")
        if not _TITLE_HEAD.match(title):
            title = f"EP {episode_number:02d}. {title}"
        return title, body

    if lines and _looks_like_title(lines[0]):
        title = _clean_title(lines[0])
        start = 1
        while start < len(lines) and not lines[start].strip():
            start += 1
        body = "\n".join(lines[start:])
        if not _TITLE_HEAD.match(title):
            title = f"EP {episode_number:02d}. {title}"
        return title, body

    # 제목 없음 — 본문은 그대로 두고 제목만 생성
    return f"EP {episode_number:02d}.", text


def _write_body(doc, body_text):
    """본문 단락 작성 — 스타일 기반 (run에 서식 직접 지정 안 함)."""
    for line in (body_text or "").split("\n"):
        if not line.strip():
            continue
        para = doc.add_paragraph(style=STYLE_BODY)
        _add_run(para, line.strip())


# ══════════════════════════════════════════════
# 1. 회차별 DOCX (수정 편의)
# ══════════════════════════════════════════════
def build_episode_docx(episode_text, episode_number, concept=None,
                       plot=None, rating="19", platform="카카오페이지",
                       title_override=None):
    """
    단일 회차 DOCX 생성 — 수정 편의 중심.

    Args:
        episode_text: 본문 (첫 줄에 제목이 있을 수도, 없을 수도 있음)
        episode_number: 회차 번호
        concept: 컨셉 카드 (optional) — 머리말 작품명에 사용
        plot: 회차 플롯 (optional) — 마지막 장 회차 메타에 사용
        rating: '19' or '15'
        platform: 플랫폼명
        title_override: 제목 직접 지정 (optional)

    Returns:
        bytes — DOCX 파일 바이너리
    """
    work_title = (concept or {}).get("title", "")
    doc = _new_manuscript_doc(header_text=work_title)

    title_line, body = _split_title_and_body(
        episode_text, int(episode_number), title_override
    )

    # ── 제목 ──
    title_para = doc.add_paragraph(style=STYLE_TITLE)
    _add_run(title_para, title_line)

    # ── 본문 ──
    _write_body(doc, body)

    # ── 회차 메타 (플롯 정보가 있으면) ──
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
    concept = concept or {}
    work_title = concept.get("title", "")
    doc = _new_manuscript_doc(header_text=work_title)

    # ── 커버 페이지 ──
    for _ in range(3):
        doc.add_paragraph()

    tagline = doc.add_paragraph()
    tagline.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(tagline, "BLUE JEANS PICTURES", font=HEADING_FONT, size=10,
             bold=True, color=NAVY, smart=False)

    for _ in range(2):
        doc.add_paragraph()

    cover_title = doc.add_paragraph()
    cover_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(cover_title, work_title, font=HEADING_FONT, size=32,
             bold=True, color=NAVY)

    for _ in range(2):
        doc.add_paragraph()

    logline_para = doc.add_paragraph()
    logline_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(logline_para, concept.get("logline", ""), size=12,
             italic=True, color=DARK)

    for _ in range(5):
        doc.add_paragraph()

    meta_para = doc.add_paragraph()
    meta_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(meta_para, f"{len(episodes_dict)}화 · {rating}금", size=11,
             color=NAVY, smart=False)

    date_para = doc.add_paragraph()
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(date_para, datetime.now().strftime("%Y.%m.%d"), size=10,
             color=DIM, smart=False)

    doc.add_page_break()

    # ── 목차 ──
    _section_header_yellow(doc, "목차", "CONTENTS")
    doc.add_paragraph()

    for ep_num in sorted(episodes_dict.keys(), key=lambda k: int(k)):
        t, _body = _split_title_and_body(episodes_dict[ep_num], int(ep_num))
        toc_para = doc.add_paragraph()
        _add_run(toc_para, f"EP{int(ep_num):03d}", size=10, bold=True,
                 color=NAVY, smart=False)
        _add_run(toc_para, f"   {t}", size=10, color=DARK)

    doc.add_page_break()

    # ── 본문 ──
    for ep_num in sorted(episodes_dict.keys(), key=lambda k: int(k)):
        title_line, body = _split_title_and_body(
            episodes_dict[ep_num], int(ep_num)
        )

        title_para = doc.add_paragraph(style=STYLE_TITLE)
        _add_run(title_para, title_line)

        _write_body(doc, body)

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
    concept = concept or {}
    doc = Document()
    _setup_page(doc)
    setup_manuscript_styles(doc)

    # ── 커버 ──
    for _ in range(3):
        doc.add_paragraph()

    company = doc.add_paragraph()
    company.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(company, "BLUE JEANS PICTURES", font=HEADING_FONT, size=10,
             bold=True, color=NAVY, smart=False)

    for _ in range(2):
        doc.add_paragraph()

    cover_title = doc.add_paragraph()
    cover_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(cover_title, concept.get("title", ""), font=HEADING_FONT,
             size=36, bold=True, color=NAVY)

    doc.add_paragraph()

    sub_title = doc.add_paragraph()
    sub_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(sub_title, "작품 기획서", font=HEADING_FONT, size=14, color=DIM)

    for _ in range(3):
        doc.add_paragraph()

    logline_para = doc.add_paragraph()
    logline_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _add_run(logline_para, concept.get("logline", ""), size=12,
             italic=True, color=DARK)

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
        _add_run(para, "▶ 주인공 ", font=HEADING_FONT, size=12, bold=True,
                 color=NAVY, smart=False)
        _add_run(para, p.get("name", ""), font=HEADING_FONT, size=12,
                 bold=True, color=DARK)
        _meta_line(doc, "Goal", p.get("goal", ""))
        _meta_line(doc, "Need", p.get("need", ""))
        _meta_line(doc, "Fatal Flaw", p.get("fatal_flaw", ""))
        doc.add_paragraph()

    # 상대역
    for i, li in enumerate(concept.get("love_interests", []), 1):
        para = doc.add_paragraph()
        _add_run(para, f"▶ 상대역 {i} ", font=HEADING_FONT, size=12,
                 bold=True, color=NAVY, smart=False)
        _add_run(para, f"{li.get('name', '')} ({li.get('role', '')})",
                 font=HEADING_FONT, size=12, bold=True, color=DARK)
        _meta_line(doc, "매력", li.get("appeal", ""))
        _meta_line(doc, "갈등", li.get("conflict", ""))
        doc.add_paragraph()

    # 빌런
    v = concept.get("villain", {})
    if v.get("name"):
        para = doc.add_paragraph()
        _add_run(para, "▶ 빌런 ", font=HEADING_FONT, size=12, bold=True,
                 color=NAVY, smart=False)
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
                     font=HEADING_FONT, size=11, bold=True, color=NAVY,
                     smart=False)
            _add_run(para, f"{block.get('ep_range', '')} · {block.get('phase', '')}",
                     size=11, bold=True, color=DARK)

            theme_para = doc.add_paragraph()
            _add_run(theme_para, block.get("theme", ""), size=10, color=DIM)

            for ep in block.get("episodes", []):
                ep_para = doc.add_paragraph()
                _add_run(ep_para, f"  EP{int(ep.get('ep', 0) or 0):03d}. ",
                         size=10, bold=True, color=NAVY, smart=False)
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
    _add_run(footer, "© 2026 BLUE JEANS PICTURES", size=9, color=DIM,
             smart=False)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
