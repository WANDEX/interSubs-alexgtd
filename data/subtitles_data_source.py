from typing import Optional, IO

from PyQt5.QtCore import QThread, pyqtSignal, QTimer


class SubtitlesDataSourceWorker(QThread):
    on_subtitles_change = pyqtSignal(str)
    on_error = pyqtSignal(OSError)

    def __init__(self, subtitles_file_path: str):
        super().__init__()
        self._subs_file_path = subtitles_file_path
        self._subs_file: Optional[IO] = None
        self._previous_subs_text = ""

    def run(self) -> None:
        try:
            self._subs_file = open(self._subs_file_path)
            timer = QTimer()
            timer.timeout.connect(self._check_for_subs_diff_and_emit_it)
            timer.start(15)
            self.exec_()
        except OSError as e:
            self.on_error.emit(e)
        finally:
            if self._subs_file:
                self._subs_file.close()

    def _check_for_subs_diff_and_emit_it(self) -> None:
        current_subs_text = self._subs_file.read()
        if current_subs_text != self._previous_subs_text:
            self.on_subtitles_change.emit(current_subs_text)
            self._previous_subs_text = current_subs_text

        self._subs_file.seek(0)
