import json
import os

from models import dictionary

CACHE_DIR_PATH = ".cache/translations"


def _create_dirs_if_not_exist() -> None:
    if not os.path.exists(CACHE_DIR_PATH):
        os.makedirs(CACHE_DIR_PATH)


def _get_file_cache_path(name: str) -> str:
    return os.path.join(CACHE_DIR_PATH, f"{name}.json")


class FileCacheDictionaryDataSource:

    def __init__(self) -> None:
        _create_dirs_if_not_exist()

    def get_dictionary_entry(self, text: str, dict_name: str) -> dictionary.DictionaryEntry:
        try:
            return self._try_to_find_dict_entry(text, dict_name)
        except FileNotFoundError:
            return dictionary.DictionaryEntry()

    def add_dictionary_entry(self, entry: dictionary.DictionaryEntry) -> None:
        with open(_get_file_cache_path(entry.lookup_text), mode="a") as cache_file:
            cache_file.write(json.dumps(dictionary.map_dictionary_entry_to_dict(entry)))
            cache_file.write("\n")

    def _try_to_find_dict_entry(self, text: str, dict_name: str) -> dictionary.DictionaryEntry:
        result = dictionary.DictionaryEntry()
        with open(_get_file_cache_path(text)) as cache_file:
            for line in cache_file.readlines():
                entry: dictionary.DictionaryEntry = json.loads(
                    line,
                    object_hook=dictionary.map_dict_to_dictionary_entry
                )
                if entry.dictionary_name == dict_name:
                    result = entry

        return result
