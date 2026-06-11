from abc import ABC, abstractmethod
from typing import List
from .models import MappingEntry


class BaseEngine(ABC):
    def __init__(self, name: str, mappings: List[MappingEntry]):
        self.name = name
        self._mappings = mappings

    @property
    def mappings(self) -> List[MappingEntry]:
        return self._mappings

    @abstractmethod
    def validate(self):
        """Engine-specific validation or initialization."""
        raise NotImplementedError
