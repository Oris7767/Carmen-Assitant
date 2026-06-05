"""
pdf_generator.py — Generate horoscope PDFs with WeasyPrint.
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path

WEASYPRINT_OK = False
try:
    from weasyprint import HTML
    WEASYPRINT_OK = True
except ImportError:
    pass

BASE_DIR = Path(__file__).parent.parent


def _text_to_html(text: str) -> str:
    """Convert plain text section to HTML."""
    html = []
    in_list = False
    for line in text.split('\n'):
        s = line.strip()
        if not s:
            if in_list: html.append("</ul>"); in_list = False
            continue
        if s.startswith('###') or s.startswith('**') and s.endswith('**'):
            title = s.replace('**', '').lstrip('#').strip()
            if in_list: html.append("</ul>"); in_list = False
            if title:
                html.append(f'<h3>{title}</h3>')
        elif s.startswith('- ') or s.startswith('* '):
            if not in_list: html.append('<ul>'); in_list = True
            html.append(f'<li>{s[2:]}</li>')
        else:
            if in_list: html.append('</ul>'); in_list = False
            para = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
            html.append(f'<p>{para}</p>')
    if in_list: html.append('</ul>')
    return '\n'.join(html)


def _build_sections(text: str) -> str:
    """Split text into sections by ## headers OR numbered headers."""
    parts = []
    cur_title = ""
    cur_block = ""
    for line in text.split('\n'):
        s = line.strip()
        if not s:
            cur_block += line + '\n'
            continue
        
        is_header = False
        title = None
        
        # Pattern 1: ## [number]. Title  (legacy format)
        m = re.match(r'^##\s+(\d+[.、]?\s*.+)$', s)
        if m:
            is_header = True
            title = m.group(1).strip()
        
        # Pattern 2: Number. TITLE TEXT  (LLM output format with sections 1-12)
        if not is_header:
            m = re.match(r'^(\d+[.、])\s*([A-Z].+)$', s)
            if m:
                num = m.group(1).rstrip('.、')
                if num.isdigit() and 1 <= int(num) <= 12:
                    # BUG FIX (2026-06-04): LLM often repeats the section title inside its
                    # output (e.g. "2. PHAN TICH TUNG HANH TINH CHI TIET"). Pattern 2 would
                    # match this as a NEW header, resetting cur_block to empty before any
                    # content is collected → Section gets lost from PDF.
                    # Skip duplicate headers by checking if the number matches current section.
                    cur_num = ''
                    if cur_title:
                        cm = re.match(r'^(\d+)', cur_title)
                        if cm:
                            cur_num = cm.group(1)
                    # Skip the duplicate header line entirely
                    if num == cur_num:
                        continue
        
        # Pattern 3: ## Generic Title
        if not is_header:
            m = re.match(r'^##\s+(.+)$', s)
            if m:
                is_header = True
                title = m.group(1).strip()
        
        if is_header and title:
            if cur_title and cur_block.strip():
                parts.append(f'<h2>{cur_title}</h2>')
                parts.append(_text_to_html(cur_block))
            cur_title = title
            cur_block = ""
        else:
            cur_block += line + '\n'
    
    if cur_title and cur_block.strip():
        parts.append(f'<h2>{cur_title}</h2>')
        parts.append(_text_to_html(cur_block))
    
    return '\n'.join(parts)

def generate_pdf(full_text: str, chart_data: dict = None) -> bytes:
    """Generate PDF from FULL reading text. Returns PDF bytes."""
    if not WEASYPRINT_OK:
        raise RuntimeError("WeasyPrint chưa cài đặt")

    meta = (chart_data or {}).get('metadata', {})
    name = (chart_data or {}).get('name', '')

    body = _build_sections(full_text)

    template = (BASE_DIR / "data" / "pdf_template.html").read_text(encoding='utf-8')
    html = template\
        .replace('%%NAME%%', name or 'Không xác định')\
        .replace('%%DOB%%', meta.get('date', 'Không xác định'))\
        .replace('%%TOB%%', meta.get('time', 'Không xác định'))\
        .replace('%%POB%%', f"{meta.get('latitude','?')}, {meta.get('longitude','?')}" if meta.get('latitude') else 'Không xác định')\
        .replace('%%BODY%%', body)\
        .replace('%%DATE%%', datetime.now().strftime("%d tháng %m, %Y"))\
        .replace('%%CHARS%%', f'{len(full_text):,}')

    return HTML(string=html).write_pdf()


def save_pdf(full_text: str, chart_data: dict = None, output_path: str = None) -> str:
    """Generate PDF and save. Returns file path."""
    if output_path is None:
        d = BASE_DIR / "data" / "pdfs"
        d.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(d / f"reading_{ts}.pdf")
    pdf_bytes = generate_pdf(full_text, chart_data)
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    return output_path
