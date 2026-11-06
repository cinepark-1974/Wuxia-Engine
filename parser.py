"""
👖 BLUE JEANS WUXIA ENGINE v2.11.0 — parser.py
기획서 파일 파싱 모듈 (DOCX / HWP / PDF / TXT / MD)
© 2026 BLUE JEANS PICTURES

[변경 이력]
v2.11.0 (2026-11-07) — DOCX를 문서 순서대로 읽기 (단락·표 섞인 순서 보존).
  이전에는 표를 문서 끝에 몰아 붙여 표로 된 섹션 제목이 모두 끝으로 밀렸다.
  아미고 v1.0 기획서에서 실측: '개요 | INFORMATION' 등 7개 제목이 맨 뒤에 위치.
v2.8.1 (2026-11-06) — 헤더 정정만. 이식 당시의 'WEB NOVEL ENGINE v2.0' 표기를
  WUXIA ENGINE으로 바로잡았다. 파싱 코드 · 의존성(olefile·pypdf) 변경 없음
"""

import io
import struct


def parse_docx(file_bytes):
    """DOCX 파일에서 텍스트 추출."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        # v2.11.0: 문서에 나온 순서대로 단락과 표를 읽는다.
        #   이전에는 단락을 모두 읽은 뒤 표를 맨 끝에 붙였다. 섹션 제목을 표로
        #   만드는 블루진 기획서 양식에서는 '개요 | INFORMATION' 같은 제목이
        #   전부 문서 끝으로 밀려나 섹션 인식이 통째로 실패했다.
        from docx.table import Table
        from docx.text.paragraph import Paragraph
        parts = []
        for child in doc.element.body.iterchildren():
            tag = child.tag.rsplit("}", 1)[-1]
            if tag == "p":
                t = Paragraph(child, doc).text
                if t.strip():
                    parts.append(t)
            elif tag == "tbl":
                for row in Table(child, doc).rows:
                    cells = []
                    for cell in row.cells:
                        ct = cell.text.strip()
                        if ct and (not cells or cells[-1] != ct):   # 병합 셀 중복 제거
                            cells.append(ct)
                    if cells:
                        parts.append(" | ".join(cells))
        return "\n".join(parts)
    except Exception as e:
        return f"[DOCX 파싱 실패: {e}]"


def parse_hwp(file_bytes):
    """HWP 파일(구버전 5.0)에서 텍스트 추출. olefile + PrvText 스트림 활용."""
    try:
        import olefile
        import zlib

        ole = olefile.OleFileIO(io.BytesIO(file_bytes))

        # 1차: PrvText 스트림 (미리보기 텍스트)
        prvtext = ""
        if ole.exists("PrvText"):
            try:
                raw = ole.openstream("PrvText").read()
                prvtext = raw.decode("utf-16-le", errors="replace")
            except Exception:
                prvtext = ""

        # 2차: BodyText/Section0 스트림 (본문 텍스트)
        body_parts = []
        if ole.exists(["BodyText", "Section0"]):
            try:
                # FileHeader에서 압축 여부 확인
                is_compressed = False
                if ole.exists("FileHeader"):
                    header = ole.openstream("FileHeader").read()
                    flags = struct.unpack_from("<I", header, 36)[0]
                    is_compressed = bool(flags & 1)

                data = ole.openstream(["BodyText", "Section0"]).read()
                if is_compressed:
                    data = zlib.decompress(data, -15)

                i = 0
                while i < len(data):
                    if i + 4 > len(data):
                        break
                    h = struct.unpack_from("<I", data, i)[0]
                    tag_id = h & 0x3FF
                    size = (h >> 20) & 0xFFF
                    if size == 0xFFF:
                        if i + 8 > len(data):
                            break
                        size = struct.unpack_from("<I", data, i + 4)[0]
                        i += 8
                    else:
                        i += 4

                    if tag_id == 67:  # HWPTAG_PARA_TEXT
                        txt = ""
                        j = 0
                        while j < size:
                            if j + 2 > size:
                                break
                            ch = struct.unpack_from("<H", data, i + j)[0]
                            if ch >= 32:
                                txt += chr(ch)
                            elif ch in (13, 10):
                                txt += "\n"
                            j += 2
                        if txt.strip():
                            body_parts.append(txt.strip())
                    i += size
            except Exception:
                pass

        ole.close()

        body_text = "\n".join(body_parts)
        # body_text가 충분하면 사용, 아니면 PrvText fallback
        if len(body_text) >= len(prvtext):
            return body_text
        return prvtext
    except Exception as e:
        return f"[HWP 파싱 실패: {e}]"


def parse_pdf(file_bytes):
    """PDF 파일에서 텍스트 추출. pypdf 또는 pdfplumber."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                parts.append(text)
        return "\n".join(parts)
    except ImportError:
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text and text.strip():
                    parts.append(text)
            return "\n".join(parts)
        except Exception as e:
            return f"[PDF 파싱 실패: pypdf/PyPDF2 필요 — {e}]"
    except Exception as e:
        return f"[PDF 파싱 실패: {e}]"


def parse_txt(file_bytes):
    """TXT 파일에서 텍스트 추출 (UTF-8, CP949 자동 시도)."""
    for encoding in ["utf-8", "cp949", "euc-kr", "utf-16"]:
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return file_bytes.decode("utf-8", errors="replace")


def parse_brief(uploaded_file):
    """
    Streamlit UploadedFile 객체를 받아 텍스트 추출.
    파일 확장자에 따라 적절한 파서 호출.
    """
    if uploaded_file is None:
        return ""

    filename = uploaded_file.name.lower()
    file_bytes = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()

    if filename.endswith(".docx"):
        return parse_docx(file_bytes)
    elif filename.endswith(".hwp"):
        return parse_hwp(file_bytes)
    elif filename.endswith(".pdf"):
        return parse_pdf(file_bytes)
    elif filename.endswith(".txt") or filename.endswith(".md"):
        return parse_txt(file_bytes)
    else:
        return f"[지원하지 않는 파일 형식: {filename}]"
