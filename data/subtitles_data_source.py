import time

from PyQt5.QtCore import QThread, pyqtSignal


class SubtitlesDataSourceWorker(QThread):
    on_subtitles_changed = pyqtSignal(str)

    def __init__(self, subtitles_file_path: str):
        super().__init__()
        self.subs_file_path = subtitles_file_path

    def run(self):
        self.watch_subtitles()

    def watch_subtitles(self):
        previous_subs_text = ""
        while True:
            try:
                current_subs_text = open(self.subs_file_path).read()
                if current_subs_text != previous_subs_text:
                    self.on_subtitles_changed.emit(current_subs_text)
                    previous_subs_text = current_subs_text
            except Exception as ex:
                print("Error occurred during watching the subtitles file for a change.\n", ex)

            time.sleep(1)
