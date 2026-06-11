#!/usr/bin/env python3
"""Generate CSV and JSON from principle-classification-table.md

Writes:
- trading_os_v1/docs/engine-mapping/principles.csv
- trading_os_v1/docs/engine-mapping/principles.json

Usage: python3 trading_os_v1/scripts/generate_principle_csv.py
"""
from pathlib import Path
import re
import csv
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / 'docs' / 'engine-mapping' / 'principle-classification-table.md'
CSV_OUT = ROOT / 'docs' / 'engine-mapping' / 'principles.csv'
JSON_OUT = ROOT / 'docs' / 'engine-mapping' / 'principles.json'


def parse_markdown_table(text: str):
    lines = [ln.strip() for ln in text.splitlines()]
    # Find header
    header_idx = None
    for i, ln in enumerate(lines):
        if re.search(r'principle\s*\|\s*source module', ln, re.I):
            header_idx = i
            break
    if header_idx is None:
        # Fallback: find first line with at least 5 pipes
        for i, ln in enumerate(lines):
            if ln.count('|') >= 5:
                header_idx = i
                break
    if header_idx is None:
        raise SystemExit('Could not find markdown table header in {}'.format(MD))

    # Find the table block demarcated by '---'
    start = None
    for i in range(header_idx+1, len(lines)):
        if lines[i].strip().startswith('---'):
            start = i
            break
    if start is None:
        # assume rows start immediately after header
        start = header_idx

    # find next '---' after start
    end = None
    for i in range(start+1, len(lines)):
        if lines[i].strip().startswith('---'):
            end = i
            break
    if end is None:
        end = len(lines)

    rows = []
    for i in range(start+1, end):
        ln = lines[i]
        if not ln or ln.lower().startswith('notes'):
            continue
        if '|' not in ln:
            continue
        parts = [p.strip() for p in re.split(r'\s*\|\s*', ln)]
        # remove empty trailing parts
        if parts and parts[-1] == '':
            parts = parts[:-1]
        # Ensure 6 columns
        if len(parts) < 6:
            parts = parts + [''] * (6 - len(parts))
        rows.append(parts[:6])
    return rows


def write_csv(rows):
    header = ['principle', 'source_module', 'category', 'engine', 'v1_status', 'notes']
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def write_json(rows):
    objs = []
    for r in rows:
        objs.append({
            'principle': r[0],
            'source_module': r[1],
            'category': r[2],
            'engine': r[3],
            'v1_status': r[4],
            'notes': r[5],
        })
    with JSON_OUT.open('w', encoding='utf-8') as f:
        json.dump(objs, f, indent=2, ensure_ascii=False)


def main():
    if not MD.exists():
        print('Missing file:', MD, file=sys.stderr)
        raise SystemExit(2)
    text = MD.read_text(encoding='utf-8')
    rows = parse_markdown_table(text)
    if not rows:
        print('No rows parsed from', MD, file=sys.stderr)
        raise SystemExit(3)
    write_csv(rows)
    write_json(rows)
    print('Wrote:', CSV_OUT)
    print('Wrote:', JSON_OUT)


if __name__ == '__main__':
    main()
