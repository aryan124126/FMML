from abc import ABC, abstractmethod
from typing import List

from ..models import Listing


class Source(ABC):
    name: str

    @abstractmethod
    def fetch(self, keywords: List[str]) -> List[Listing]:
        """Return listings relevant to the given keywords. Must not raise on
        network/parsing errors it can reasonably anticipate — log and return
        whatever was gathered, or an empty list."""
        raise NotImplementedError
