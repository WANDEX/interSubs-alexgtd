from dataclasses import dataclass, field, asdict
from typing import List, Tuple


@dataclass
class DictionaryEntry:
    dictionary_name: str = ""
    lookup_text: str = ""
    examples: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        if self.lookup_text:
            return False
        return True


def map_dict_to_dictionary_entry(dict_: dict) -> DictionaryEntry:
    dict_name = "dictionary_name"
    lookup_text = "lookup_text"
    examples = "examples"
    if dict_name and lookup_text and examples in dict_:
        return DictionaryEntry(dict_[dict_name], dict_[lookup_text], dict_[examples])
    raise AttributeError(f"Couldn't map {dict_} to DictionaryEntry model")


def map_dictionary_entry_to_dict(entry: DictionaryEntry) -> dict:
    return asdict(entry)
