from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Translation:
    service_name: str
    original_text: str
    translation_pairs: List[Tuple[str, str]]
