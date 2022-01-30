from typing import Protocol

from PyQt5 import QtCore

from models import dictionary


class RemoteDictionaryDataSource(Protocol):
    DICT_NAME: str

    def lookup(self, text: str) -> dictionary.DictionaryEntry:
        ...


class LocalDictionaryDataSource(Protocol):
    def get_dictionary_entry(self, text: str, dict_name: str) -> dictionary.DictionaryEntry:
        ...

    def add_dictionary_entry(self, entry: dictionary.DictionaryEntry) -> None:
        ...


class DictionaryRepositoryWorkerThread(QtCore.QThread):
    on_success = QtCore.pyqtSignal(dictionary.DictionaryEntry)
    on_error = QtCore.pyqtSignal(Exception)

    def __init__(
            self,
            remote_dict: RemoteDictionaryDataSource,
            local_dict: LocalDictionaryDataSource,
            text: str
    ) -> None:
        super().__init__()
        self._remote = remote_dict
        self._local = local_dict
        self._text = text

    def run(self) -> None:
        try:
            self._try_to_lookup()
        except Exception as e:
            self.on_error.emit(e)

    def _try_to_lookup(self) -> None:
        entry = self._local.get_dictionary_entry(self._text, self._remote.DICT_NAME)
        if entry.is_empty:
            entry = self._remote.lookup(self._text)
            self._local.add_dictionary_entry(entry)

        self.on_success.emit(entry)
