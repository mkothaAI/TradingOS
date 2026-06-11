import re
from pathlib import Path
from typing import Dict, List

from .models import MappingEntry


class MappingLoader:
    """Simple loader to parse the engine mapping markdown created from Varsity extractions."""

    def __init__(self, mapping_md_path: str):
        self.path = Path(mapping_md_path)

    def load(self) -> Dict[str, List[MappingEntry]]:
        if not self.path.exists():
            raise FileNotFoundError(f"Mapping file not found: {self.path}")

        text = self.path.read_text(encoding="utf-8")
        sections = self._split_sections(text)
        result: Dict[str, List[MappingEntry]] = {}
        for title, body in sections.items():
            entries = self._parse_section(body)
            result[title] = entries
        return result

    def _split_sections(self, text: str) -> Dict[str, str]:
        # Find headings like '## Universe Engine (Security Selection)'
        pattern = re.compile(r"^##\s+(.*)$", re.MULTILINE)
        matches = list(pattern.finditer(text))
        sections = {}
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            title = m.group(1).strip()
            body = text[start:end].strip()
            sections[title] = body
        return sections

    def _parse_section(self, body: str) -> List[MappingEntry]:
        entries: List[MappingEntry] = []
        # Look for lines starting with '- Principle:'
        for line in body.splitlines():
            line = line.strip()
            if not line.startswith('- Principle:'):
                continue
            # Remove leading '- Principle: '
            content = line[len('- Principle:'):].strip()
            # The file uses em-dash separators ' — '
            parts = [p.strip() for p in content.split('—')]
            # parts typically: ['"Text"', 'Source: Module X', 'Status: ...', 'Notes: ...']
            principle = parts[0].strip(' "') if parts else ''
            source = None
            status = None
            notes = None
            for p in parts[1:]:
                if p.lower().startswith('source:'):
                    source = p.split(':', 1)[1].strip()
                elif p.lower().startswith('status:'):
                    status = p.split(':', 1)[1].strip()
                elif p.lower().startswith('notes:'):
                    notes = p.split(':', 1)[1].strip()
                else:
                    # catch-all: if contains 'Source' or 'Status' keywords
                    if 'module' in p.lower() and source is None:
                        source = p
                    elif ('direct' in p.lower() or 'optional' in p.lower() or 'not suitable' in p.lower() or 'explanation' in p.lower()) and status is None:
                        status = p
                    elif notes is None:
                        notes = p

            entries.append(MappingEntry(principle=principle, source=source, status=status, notes=notes))
        return entries
