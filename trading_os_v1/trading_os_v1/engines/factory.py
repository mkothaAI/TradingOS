from typing import Dict

from .base import BaseEngine
from .loader import MappingLoader
from .models import MappingEntry


class SimpleEngine(BaseEngine):
    def validate(self):
        # Basic validation: ensure mappings exist
        if not self.mappings:
            raise ValueError(f"Engine {self.name} has no mappings")


def load_all_engines(mapping_md_path: str) -> Dict[str, SimpleEngine]:
    loader = MappingLoader(mapping_md_path)
    mapping_dict = loader.load()
    engines: Dict[str, SimpleEngine] = {}
    for title, entries in mapping_dict.items():
        engines[title] = SimpleEngine(title, entries)
    return engines
