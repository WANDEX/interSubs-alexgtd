#! /usr/bin/env python

import os
import re
import sys
import threading
import time

from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPaintEvent, QPainter, QFontMetrics, QColor, QPen, QBrush
from PyQt5.QtWidgets import QApplication, QLabel

from data_provider.deepl import deepl
from data_provider.dict_cc import dict_cc
from data_provider.google_translate import google
from data_provider.leo import leo
from data_provider.linguee import linguee
from data_provider.morfix import morfix
from data_provider.offline_dictionary import tab_divided_dict
from data_provider.pons import pons
from data_provider.redensarten import redensarten
from data_provider.reverso import reverso
from data_provider.pronunciation import listen
from data_provider.subtitles_data_source import SubtitlesDataSourceWorker
from mpv import Mpv
from ui.popup_view import PopupView
from ui.subtitles_view import SubtitlesView

os.chdir(os.path.expanduser('~/.config/mpv/scripts/'))
import interSubs_config as config


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


class events_class(QLabel):
	mouseHover = pyqtSignal(str, int, bool)
	redraw = pyqtSignal(bool, bool)

	def __init__(self, word, subs, skip = False, parent=None):
		super().__init__(word)
		self.setMouseTracking(True)
		self.word = word
		self.subs = subs
		self.skip = skip
		self.is_highlighting = False

		self.setStyleSheet('background: transparent; color: transparent;')

	def highlight(self, color, underline_width):
		color = QColor(color)
		color = QColor(color.red(), color.green(), color.blue(), 200)
		painter = QPainter(self)

		if config.is_hover_underline:
			font_metrics = QFontMetrics(self.font())
			text_width = font_metrics.width(self.word)
			text_height = font_metrics.height()

			brush = QBrush(color)
			pen = QPen(brush, underline_width, Qt.SolidLine, Qt.RoundCap)
			painter.setPen(pen)
			if not self.skip:
				painter.drawLine(0, text_height - underline_width, text_width, text_height - underline_width)

		if config.is_hover_highlight:
			x = y = 0
			y += self.fontMetrics().ascent()

			painter.setPen(color)
			painter.drawText(x, y + config.outline_top_padding - config.outline_bottom_padding, self.word)

	if config.is_subs_outlined:
		def paintEvent(self, evt: QPaintEvent):
			if self.is_highlighting:
				self.highlight(config.hover_color, config.hover_underline_thickness)

	#####################################################

	def resizeEvent(self, event):
		text_height = self.fontMetrics().height()
		text_width = self.fontMetrics().width(self.word)

		self.setFixedSize(text_width, text_height + config.outline_bottom_padding + config.outline_top_padding)

	def enterEvent(self, event):
		if not self.skip:
			self.is_highlighting = True
			self.repaint()
			config.queue_to_translate.put((self.word, event.globalX()))

	@pyqtSlot()
	def leaveEvent(self, event):
		if not self.skip:
			self.is_highlighting = False
			self.repaint()

			config.scroll = {}
			self.mouseHover.emit('', 0, False)
			QApplication.restoreOverrideCursor()

	def wheel_scrolling(self, event):
		if event.y() > 0:
			return 'ScrollUp'
		if event.y():
			return 'ScrollDown'
		if event.x() > 0:
			return 'ScrollLeft'
		if event.x():
			return 'ScrollRight'

	def wheelEvent(self, event):
		for mouse_action in config.mouse_buttons:
			if self.wheel_scrolling(event.angleDelta()) == mouse_action[0]:
				if event.modifiers() == eval('Qt.%s' % mouse_action[1]):
					exec('self.%s(event)' % mouse_action[2])

	def mousePressEvent(self, event):
		for mouse_action in config.mouse_buttons:
			if 'Scroll' not in mouse_action[0]:
				if event.button() == eval('Qt.%s' % mouse_action[0]):
					if event.modifiers() == eval('Qt.%s' % mouse_action[1]):
						exec('self.%s(event)' % mouse_action[2])

	#####################################################

	def f_show_in_browser(self, event):
		config.avoid_resuming = True
		os.system(config.show_in_browser.replace('${word}', self.word))

	def f_auto_pause_options(self, event):
		if config.auto_pause == 2:
			config.auto_pause = 0
		else:
			config.auto_pause += 1
		mpv.show_text('auto_pause: %d' % config.auto_pause)

	def f_listen(self, event):
		listen(self.word, config.listen_via)

	@pyqtSlot()
	def f_subs_screen_edge_padding_decrease(self, event):
		config.subs_screen_edge_padding -= 5
		mpv.show_text('subs_screen_edge_padding: %d' % config.subs_screen_edge_padding)
		self.redraw.emit(False, True)

	@pyqtSlot()
	def f_subs_screen_edge_padding_increase(self, event):
		config.subs_screen_edge_padding += 5
		mpv.show_text('subs_screen_edge_padding: %d' % config.subs_screen_edge_padding)
		self.redraw.emit(False, True)

	@pyqtSlot()
	def f_font_size_decrease(self, event):
		config.style_subs = re.sub('font-size: (\d+)px;', lambda size: [ 'font-size: %dpx;' % ( int(size.group(1)) - 1 ), mpv.show_text('font: %s' % size.group(1))][0], config.style_subs, flags = re.I)
		self.redraw.emit(False, True)

	@pyqtSlot()
	def f_font_size_increase(self, event):
		config.style_subs = re.sub('font-size: (\d+)px;', lambda size: [ 'font-size: %dpx;' % ( int(size.group(1)) + 1 ), mpv.show_text('font: %s' % size.group(1))][0], config.style_subs, flags = re.I)
		self.redraw.emit(False, True)

	def f_auto_pause_min_words_decrease(self, event):
		config.auto_pause_min_words -= 1
		mpv.show_text('auto_pause_min_words: %d' % config.auto_pause_min_words)

	def f_auto_pause_min_words_increase(self, event):
		config.auto_pause_min_words += 1
		mpv.show_text('auto_pause_min_words: %d' % config.auto_pause_min_words)

	# f_deepl_translation -> f_translation_full_sentence
	@pyqtSlot()
	def f_deepl_translation(self, event):
		self.mouseHover.emit(self.subs , event.globalX(), True)
	
	@pyqtSlot()
	def f_translation_full_sentence(self, event):
		self.mouseHover.emit(self.subs , event.globalX(), True)

	def f_save_word_to_file(self, event):
		if ( os.path.isfile(os.path.expanduser(config.save_word_to_file_fname)) and self.word not in [ x.strip() for x in open(os.path.expanduser(config.save_word_to_file_fname)).readlines() ] ) or not os.path.isfile(os.path.expanduser(config.save_word_to_file_fname)):
			print(self.word, file = open(os.path.expanduser(config.save_word_to_file_fname), 'a'))

	@pyqtSlot()
	def f_scroll_translations_up(self, event):
		if self.word in config.scroll and config.scroll[self.word] > 0:
			config.scroll[self.word] = config.scroll[self.word] - 1
		else:
			config.scroll[self.word] = 0
		self.mouseHover.emit(self.word, event.globalX(), False)

	@pyqtSlot()
	def f_scroll_translations_down(self, event):
		if self.word in config.scroll:
			config.scroll[self.word] = config.scroll[self.word] + 1
		else:
			config.scroll[self.word] = 1
		self.mouseHover.emit(self.word, event.globalX(), False)


if __name__ == "__main__":
	print("[python] Starting interSubs ...")

	mpv_socket_path = sys.argv[1]
	mpv = Mpv(mpv_socket_path)
	subs_file_path = sys.argv[2]

	app = QApplication(sys.argv)

	config.screen_width = app.primaryScreen().size().width()
	config.screen_height = app.primaryScreen().size().height()

	subs_view = SubtitlesView(config)
	popup_view = PopupView(config)
	subs_view.register_text_hover_event_handler(popup_view.pop)

	subs_data_source_worker = SubtitlesDataSourceWorker(subs_file_path)
	subs_data_source_worker.on_subtitles_changed.connect(popup_view.hide)
	subs_data_source_worker.on_subtitles_changed.connect(subs_view.submit_subs)
	subs_data_source_worker.start()

	app.exec_()
