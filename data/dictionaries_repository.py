from typing import Callable, MutableSet, Collection

from PyQt5 import QtCore

from data.dictionary_data_source import DictionaryRepositoryWorkerThread
from data.file_cache_dictionary_data_source import FileCacheDictionaryDataSource
from models.dictionary import DictionaryEntry


class DictionariesRepository(QtCore.QObject):
    on_success = QtCore.pyqtSignal(DictionaryEntry)
    on_error = QtCore.pyqtSignal(Exception)

    def __init__(self, dictionary_data_sources: Collection) -> None:
        super().__init__()

        self._remote_dicts = dictionary_data_sources
        self._local_dict = FileCacheDictionaryDataSource()
        self._threads: MutableSet[QtCore.QThread] = set()

    def get_dictionary_entries(self, text: str) -> None:
        self._init_and_start_dictionary_threads(text)

    def _init_and_start_dictionary_threads(self, text: str) -> None:
        for remote_dict in self._remote_dicts:
            t = DictionaryRepositoryWorkerThread(remote_dict, self._local_dict, text)
            t.on_success.connect(self._do_on_success)
            t.on_error.connect(self._do_on_error)
            t.finished.connect(self._enclose_thread_in_on_finish_event(t))
            t.start()
            self._threads.add(t)

    def _do_on_success(self, entry: DictionaryEntry) -> None:
        self.on_success.emit(entry)

    def _do_on_error(self, error: Exception) -> None:
        self.on_error.emit(error)

    def _enclose_thread_in_on_finish_event(self, thread: QtCore.QThread) -> Callable[[None], None]:
        def clear_threads() -> None:
            self._threads.remove(thread)

        return clear_threads
