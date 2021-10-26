#! /usr/bin/env python

import sys
import threading
import time

from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPaintEvent, QPainter, QFontMetrics, QColor, QPen, QBrush
from PyQt5.QtWidgets import QApplication, QLabel

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


class HighlightableLabel(QLabel):
	def __init__(self, text: str, config):
		super().__init__(text)
		self.setMouseTracking(True)
		self.cfg = config
		self.word = text
		self.is_highlighting = False

		self.setStyleSheet('background: transparent; color: transparent;')

	def highlight(self, color, underline_width):
		color = QColor(color)
		color = QColor(color.red(), color.green(), color.blue(), 200)
		painter = QPainter(self)

		if self.cfg.is_hover_underline:
			font_metrics = QFontMetrics(self.font())
			text_width = font_metrics.width(self.word)
			text_height = font_metrics.height()

			brush = QBrush(color)
			pen = QPen(brush, underline_width, Qt.SolidLine, Qt.RoundCap)
			painter.setPen(pen)
			painter.drawLine(0, text_height - underline_width, text_width, text_height - underline_width)

		if self.cfg.is_hover_highlight:
			x = y = 0
			y += self.fontMetrics().ascent()

			painter.setPen(color)
			painter.drawText(x, y + self.cfg.outline_top_padding - self.cfg.outline_bottom_padding, self.word)

	def paintEvent(self, evt: QPaintEvent):
		if self.is_highlighting:
			self.highlight(self.cfg.hover_color, self.cfg.hover_underline_thickness)

	def resizeEvent(self, event):
		text_height = self.fontMetrics().height()
		text_width = self.fontMetrics().width(self.word)

		self.setFixedSize(text_width, text_height + self.cfg.outline_bottom_padding + self.cfg.outline_top_padding)

	def enterEvent(self, event):
		self.is_highlighting = True
		self.repaint()

	def leaveEvent(self, event):
		self.is_highlighting = False
		self.repaint()


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
