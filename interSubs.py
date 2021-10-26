#! /usr/bin/env python

import sys
import threading
import time

from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication

import config
from data_provider.subtitles_data_source import SubtitlesDataSourceWorker
from mpv import Mpv
from ui.popup_view import PopupView
from ui.subtitles_view import SubtitlesView


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
				threads.append(threading.Thread(target = globals()[translation_function_name], args = (word,)))
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


def main():
	print("[python] Starting interSubs ...")

	mpv_socket_path = sys.argv[1]
	mpv = Mpv(mpv_socket_path)
	subs_file_path = sys.argv[2]

	app = QApplication(sys.argv)

	cfg = config
	cfg.screen_width = app.primaryScreen().size().width()
	cfg.screen_height = app.primaryScreen().size().height()

	subs_view = SubtitlesView(cfg)
	popup_view = PopupView(cfg)
	subs_view.register_text_hover_event_handler(popup_view.pop)

	subs_data_source_worker = SubtitlesDataSourceWorker(subs_file_path)
	subs_data_source_worker.on_subtitles_changed.connect(popup_view.hide)
	subs_data_source_worker.on_subtitles_changed.connect(subs_view.submit_subs)
	subs_data_source_worker.start()

	app.exec_()


if __name__ == "__main__":
	main()
