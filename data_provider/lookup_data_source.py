import threading
import time

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import QApplication

import config


class thread_translations(QObject):
    get_translations = pyqtSignal(str, int, bool)

    @pyqtSlot()
    def main(self):
        while 1:
            to_new_word = False

            try:
                word, globalX = config.queue_to_translate.get(False)
            except:
                time.sleep(config.update_time)
                continue

            # changing cursor to hourglass during translation
            QApplication.setOverrideCursor(Qt.WaitCursor)

            threads = []
            for translation_function_name in config.translation_function_names:
                threads.append(threading.Thread(target=globals()[translation_function_name], args=(word,)))
            for x in threads:
                x.start()
            while any(thread.is_alive() for thread in threads):
                if config.queue_to_translate.qsize():
                    to_new_word = True
                    break
                time.sleep(config.update_time)

            QApplication.restoreOverrideCursor()

            if to_new_word:
                continue

            if config.block_popup:
                continue

            self.get_translations.emit(word, globalX, False)
