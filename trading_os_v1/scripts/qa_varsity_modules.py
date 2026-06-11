#!/usr/bin/env python3
from pathlib import Path
import re
import pdfplumber
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'source' / 'Varsity'
OUT = ROOT / 'docs' / 'varsity-extraction'
OUT.mkdir(parents=True, exist_ok=True)

CHAP_RE = re.compile(r'(^|\n)\s*(CHAPTER\s+\d+[:\-\s]?|Chapter\s+\d+[:\-\s]?|CHAPTER\s+[A-Z]+)', re.I)
EXCEL_KEYWORDS = ['excel', 'solver', 'sheet', 'frequency', 'pivot', 'table', 'chart', 'graph', 'workbook']

def analyze_pdf(pdf_path: Path):
    chapters = []
    pages_with_images = []
    pages_with_excel_mentions = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ''
            # detect chapter markers on this page
            if CHAP_RE.search(text):
                # take first line as excerpt
                first = next((ln.strip() for ln in text.splitlines() if ln.strip()), '')
                chapters.append({'page': i, 'excerpt': first[:240]})
            # detect images
            imgs = getattr(page, 'images', []) or []
            if imgs and len(imgs) > 0:
                pages_with_images.append(i)
            # heuristic: excel/table mentions
            lowered = text.lower()
            if any(k in lowered for k in EXCEL_KEYWORDS):
                pages_with_excel_mentions.append(i)
    return {
        'chapters': chapters,
        'pages_with_images': pages_with_images,
        'pages_with_excel_mentions': pages_with_excel_mentions,
    }

def find_md_for_pdf(pdf_path: Path):
    # search for md files that contain the module number or stem
    stem = pdf_path.stem.lower()
    candidates = list(OUT.glob('*.md'))
    for c in candidates:
        name = c.stem.lower()
        if stem in name or any(part in name for part in stem.split('_')):
            return c
    # fallback: return a new QA md path
    slug = re.sub(r'[^a-z0-9]+','-', stem.lower()).strip('-')
    return OUT / f"qa-{slug}.md"

def append_qa_to_md(md_path: Path, pdf_path: Path, analysis: dict):
    header = f"\n\n## QA: Chapters & Images (automated)\n- source_pdf: {pdf_path.relative_to(ROOT)}\n- qa_date: {datetime.utcnow().isoformat()}Z\n"
    lines = [header]
    if analysis['chapters']:
        lines.append('\n### Detected chapter markers:')
        for c in analysis['chapters']:
            lines.append(f"- page {c['page']}: {c['excerpt']}")
    else:
        lines.append('\n- No explicit chapter markers detected in text extraction.')

    if analysis['pages_with_images']:
        lines.append('\n### Pages with embedded images detected:')
        lines.append(', '.join(str(p) for p in analysis['pages_with_images']))
    else:
        lines.append('\n- No embedded images detected by pdfplumber.')

    if analysis['pages_with_excel_mentions']:
        lines.append('\n### Pages referencing Excel/tables/solver:')
        lines.append(', '.join(str(p) for p in analysis['pages_with_excel_mentions']))

    # write to md (append)
    with md_path.open('a', encoding='utf8') as f:
        f.write('\n'.join(lines))

def main():
    pdfs = sorted(SRC.rglob('*.pdf'))
    if not pdfs:
        print('No PDFs found under', SRC)
        return
    aggregate = []
    for p in pdfs:
        print('Analyzing', p)
        analysis = analyze_pdf(p)
        md = find_md_for_pdf(p)
        append_qa_to_md(md, p, analysis)
        aggregate.append({'pdf': str(p.relative_to(ROOT)), 'md': str(md.relative_to(ROOT)), 'chapters': analysis['chapters'], 'images': analysis['pages_with_images'], 'excel_pages': analysis['pages_with_excel_mentions']})

    # write aggregate summary
    agg_path = OUT / 'qa-summary.md'
    with agg_path.open('w', encoding='utf8') as f:
        f.write('# QA Summary\n')
        f.write(f'- generated: {datetime.utcnow().isoformat()}Z\n\n')
        for a in aggregate:
            f.write(f"## {a['pdf']} -> {a['md']}\n")
            if a['chapters']:
                f.write('Detected chapters:\n')
                for c in a['chapters']:
                    f.write(f"- page {c['page']}: {c['excerpt']}\n")
            else:
                f.write('- No chapter markers detected\n')
            if a['images']:
                f.write(f"- Pages with images: {', '.join(map(str,a['images']))}\n")
            else:
                f.write('- No embedded images detected\n')
            if a['excel_pages']:
                f.write(f"- Pages mentioning Excel/tables/solver: {', '.join(map(str,a['excel_pages']))}\n")
            f.write('\n')

    print('QA complete. Summary written to', agg_path)

if __name__ == '__main__':
    main()
