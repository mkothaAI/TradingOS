from dataclasses import dataclass
from typing import Optional


@dataclass
class MappingEntry:
    principle: str
    source: Optional[str]
    status: Optional[str]
    notes: Optional[str]
