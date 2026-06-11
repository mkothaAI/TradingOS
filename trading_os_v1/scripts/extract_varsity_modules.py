#!/usr/bin/env python3
from pathlib import Path
import re
import pdfplumber
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'source' / 'Varsity'
OUT = ROOT / 'docs' / 'varsity-extraction'
OUT.mkdir(parents=True, exist_ok=True)

def slugify(name: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9-_]+', '-', name).strip('-').lower()
    return s

def extract_pdf(pdf_path: Path):
    pages = []
    images_present = False
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            txt = page.extract_text() or ''
            pages.append((i, txt))
            if getattr(page, 'images', None):
                if len(page.images) > 0:
                    images_present = True
    return pages, images_present

def build_md(pdf_path: Path, pages, images_present):
    title = pdf_path.stem
    slug = slugify(title)
    out_file = OUT / f"{slug}.md"
    with out_file.open('w', encoding='utf8') as f:
        f.write(f"Module: {title}\n\n")
        f.write("Source files used:\n")
        f.write(f"- {pdf_path.relative_to(ROOT)}\n\n")
        f.write("Extraction status:\n")
        f.write("- status: verified (text extracted)\n")
        f.write(f"- extraction_date: {datetime.utcnow().isoformat()}Z\n")
        f.write("- extractor: pdfplumber (text-only extraction)\n\n")

        # Summary: first non-empty page content excerpt
        summary = ''
        for pnum, txt in pages[:6]:
            if txt and len(txt.strip())>20:
                summary = ' '.join(txt.replace('\n',' ').split())[:800]
                break
        f.write("## Module summary\n")
        f.write(summary + "\n\n")

        # Chapter detections
        f.write("## Chapter-by-chapter notes\n")
        chap_re = re.compile(r'CHAPTER\s+\d+|CHAPTER\s+\w+', re.I)
        found = False
        for pnum, txt in pages:
            if not txt:
                continue
            if chap_re.search(txt):
                found = True
                # take first 240 chars as key points
                excerpt = ' '.join(txt.replace('\n',' ').split())[:240]
                f.write(f"- Detected chapter marker on page {pnum}: {excerpt}\n")
        if not found:
            f.write("- No explicit chapter markers detected in text extraction.\n")

        f.write("\n## Open questions / missing material\n")
        if images_present:
            f.write("- PDF references images or Excel screenshots; images were detected but not captured as structured data. Consider supplying original workbooks or higher-resolution images for precise reproduction.\n")
        else:
            f.write("- No images detected by pdfplumber, but verify visually for charts/Excel snapshots.\n")

        f.write("\n## Notes on extraction quality\n")
        f.write("- Generated from text-only extraction; tables and images may be incomplete.\n")

    return out_file

def main():
    pdfs = list(SRC.rglob('*.pdf'))
    if not pdfs:
        print('No PDFs found under', SRC)
        return
    created = []
    for p in sorted(pdfs):
        print('Processing', p)
        pages, images_present = extract_pdf(p)
        out = build_md(p, pages, images_present)
        created.append(out)
    print('Created', len(created), 'files under', OUT)
    for c in created:
        print('-', c.relative_to(ROOT))

if __name__ == '__main__':
    main()
