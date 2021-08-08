#! /usr/bin/env python

import os, subprocess, sys
import random, re, time
import threading, queue
import numpy

from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal, pyqtSlot, QSize
from PyQt5.QtWidgets import QApplication, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QWidget
from PyQt5.QtGui import QPalette, QPaintEvent, QPainter, QPainterPath, QFontMetrics, QColor, QPen, QBrush

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
from mpv import Mpv

os.chdir(os.path.expanduser('~/.config/mpv/scripts/'))
import interSubs_config as config


def stripsd2(phrase):
	return ''.join(e for e in phrase.strip().lower() if e == ' ' or (e.isalnum() and not e.isdigit())).strip()

def r2l(l):
	l2 = ''

	try:
		l2 = re.findall('(?!%)\W+$', l)[0][::-1]
	except:
		pass

	l2 += re.sub('^\W+|(?!%)\W+$', '', l)

	try:
		l2 += re.findall('^\W+', l)[0][::-1]
	except:
		pass
	
	return l2

def split_long_lines(line, chunks = 2, max_symbols_per_line = False):
	if max_symbols_per_line:
		chunks = 0
		while 1:
			chunks += 1
			new_lines = []
			for i in range(chunks):
				new_line = ' '.join(numpy.array_split(line.split(' '), chunks)[i])
				new_lines.append(new_line)

			if len(max(new_lines, key = len)) <= max_symbols_per_line:
				return '\n'.join(new_lines)
	else:
		new_lines = []
		for i in range(chunks):
			new_line = ' '.join(numpy.array_split(line.split(' '), chunks)[i])
			new_lines.append(new_line)

		return '\n'.join(new_lines)

def dir2(name):
	print('\n'.join(dir( name )))
	exit()

class thread_subtitles(QObject):
	update_subtitles = pyqtSignal(bool, bool)

	@pyqtSlot()
	def main(self):
		global subs

		was_hidden = 0
		inc = 0
		auto_pause_2_ind = 0
		last_updated = time.time()

		while 1:
			time.sleep(config.update_time)

			# hide subs when mpv isn't in focus or in fullscreen
			if inc * config.update_time > config.focus_checking_time - 0.0001:
				while 'mpv' not in subprocess.getoutput('xdotool getwindowfocus getwindowname') or (config.hide_when_not_fullscreen_B and not mpv.is_in_fullscreen()) or (os.path.exists(mpv_socket_path + '_hide')):
					if not was_hidden:
						self.update_subtitles.emit(True, False)
						was_hidden = 1
					else:
						time.sleep(config.focus_checking_time)
				inc = 0
			inc += 1

			if was_hidden:
				was_hidden = 0
				self.update_subtitles.emit(False, False)
				continue

			try:
				tmp_file_subs = open(sub_file).read()
			except:
				continue
			
			# tmp hack
			# if config.R2L_from_B:
			# 	tmp_file_subs = r2l(tmp_file_subs.strip())

			if config.extend_subs_duration2max_B and not len(tmp_file_subs):
				if not config.extend_subs_duration_limit_sec:
					continue
				if config.extend_subs_duration_limit_sec > time.time() - last_updated:
					continue

			last_updated = time.time()

			# automatically switch into Hebrew if it's detected
			if config.lang_from != 'he' and config.lang_from != 'iw' and any((c in set('קראטוןםפשדגכעיחלךףזסבהנמצתץ')) for c in tmp_file_subs):
				config.lang_from = 'he'

				frf = random.choice(config.he_fonts)
				config.style_subs = re.sub('font-family: ".*?";', lambda ff: 'font-family: "%s";' % frf, config.style_subs, flags = re.I)

				config.R2L_from_B = True
				config.translation_function_names = config.translation_function_names_2
				config.listen_via = 'forvo'

				os.system('notify-send -i none -t 1111 "He"')
				os.system('notify-send -i none -t 1111 "%s"' % str(frf))

				self.update_subtitles.emit(False, True)

			while tmp_file_subs != subs:
				if config.auto_pause == 2:
					if not auto_pause_2_ind and len(re.sub(' +', ' ', stripsd2(subs.replace('\n', ' '))).split(' ')) > config.auto_pause_min_words - 1 and not mpv.is_paused():
						mpv.pause()
						auto_pause_2_ind = 1

					if auto_pause_2_ind and mpv.is_paused():
						break

					auto_pause_2_ind = 0

				subs = tmp_file_subs

				if config.auto_pause == 1:
					if len(re.sub(' +', ' ', stripsd2(subs.replace('\n', ' '))).split(' ')) > config.auto_pause_min_words - 1:
						mpv.pause()

				self.update_subtitles.emit(False, False)

				break

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

# drawing layer
# because can't calculate outline with precision
class drawing_layer(QLabel):
	def __init__(self, line, subs, parent=None):
		super().__init__(None)
		self.line = line
		self.setStyleSheet(config.style_subs)
		self.psuedo_line = 0

	def draw_text_n_outline(self, painter: QPainter, x, y, outline_width, outline_blur, text):
		outline_color = QColor(config.outline_color)

		font = self.font()
		text_path = QPainterPath()
		if config.R2L_from_B:
			text_path.addText(x, y, font, ' ' + r2l(text.strip()) + ' ')
		else:
			text_path.addText(x, y, font, text)

		# draw blur
		range_width = range(outline_width, outline_width + outline_blur)
		# ~range_width = range(outline_width + outline_blur, outline_width, -1)

		for width in range_width:
			if width == min(range_width):
				alpha = 200
			else:
				alpha = (max(range_width) - width) / max(range_width) * 200
				alpha = int(alpha)

			blur_color = QColor(outline_color.red(), outline_color.green(), outline_color.blue(), alpha)
			blur_brush = QBrush(blur_color, Qt.SolidPattern)
			blur_pen = QPen(blur_brush, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

			painter.setPen(blur_pen)
			painter.drawPath(text_path)

		# draw outline
		outline_color = QColor(outline_color.red(), outline_color.green(), outline_color.blue(), 255)
		outline_brush = QBrush(outline_color, Qt.SolidPattern)
		outline_pen = QPen(outline_brush, outline_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

		painter.setPen(outline_pen)
		painter.drawPath(text_path)

		# draw text
		color = self.palette().color(QPalette.Text)
		painter.setPen(color)
		painter.drawText(x, y, text)

	if config.outline_B:
		def paintEvent(self, evt: QPaintEvent):
			if not self.psuedo_line:
				self.psuedo_line = 1
				return

			x = y = 0
			y += self.fontMetrics().ascent()
			painter = QPainter(self)

			self.draw_text_n_outline(
				painter,
				x,
				y + config.outline_top_padding - config.outline_bottom_padding,
				config.outline_thickness,
				config.outline_blur,
				text = self.line
				)

		def resizeEvent(self, *args):
			self.setFixedSize(
				self.fontMetrics().width(self.line),
				self.fontMetrics().height() +
					config.outline_bottom_padding +
					config.outline_top_padding
				)

		def sizeHint(self):
			return QSize(
				self.fontMetrics().width(self.line),
				self.fontMetrics().height()
				)

class events_class(QLabel):
	mouseHover = pyqtSignal(str, int, bool)
	redraw = pyqtSignal(bool, bool)

	def __init__(self, word, subs, skip = False, parent=None):
		super().__init__(word)
		self.setMouseTracking(True)
		self.word = word
		self.subs = subs
		self.skip = skip
		self.highlight = False

		self.setStyleSheet('background: transparent; color: transparent;')

	def highligting(self, color, underline_width):
		color = QColor(color)
		color = QColor(color.red(), color.green(), color.blue(), 200)
		painter = QPainter(self)

		if config.hover_underline:
			font_metrics = QFontMetrics(self.font())
			text_width = font_metrics.width(self.word)
			text_height = font_metrics.height()

			brush = QBrush(color)
			pen = QPen(brush, underline_width, Qt.SolidLine, Qt.RoundCap)
			painter.setPen(pen)
			if not self.skip:
				painter.drawLine(0, text_height - underline_width, text_width, text_height - underline_width)

		if config.hover_hightlight:
			x = y = 0
			y += self.fontMetrics().ascent()

			painter.setPen(color)
			painter.drawText(x, y + config.outline_top_padding - config.outline_bottom_padding, self.word)

	if config.outline_B:
		def paintEvent(self, evt: QPaintEvent):
			if self.highlight:
				self.highligting(config.hover_color, config.hover_underline_thickness)

	#####################################################

	def resizeEvent(self, event):
		text_height = self.fontMetrics().height()
		text_width = self.fontMetrics().width(self.word)

		self.setFixedSize(text_width, text_height + config.outline_bottom_padding + config.outline_top_padding)

	def enterEvent(self, event):
		if not self.skip:
			self.highlight = True
			self.repaint()
			config.queue_to_translate.put((self.word, event.globalX()))

	@pyqtSlot()
	def leaveEvent(self, event):
		if not self.skip:
			self.highlight = False
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

class main_class(QWidget):
	def __init__(self):
		super().__init__()

		self.thread_subs = QThread()
		self.obj = thread_subtitles()
		self.obj.update_subtitles.connect(self.render_subtitles)
		self.obj.moveToThread(self.thread_subs)
		self.thread_subs.started.connect(self.obj.main)
		self.thread_subs.start()

		self.thread_translations = QThread()
		self.obj2 = thread_translations()
		self.obj2.get_translations.connect(self.render_popup)
		self.obj2.moveToThread(self.thread_translations)
		self.thread_translations.started.connect(self.obj2.main)
		self.thread_translations.start()

		# start the forms
		self.subtitles_base()
		self.subtitles_base2()
		self.popup_base()

	def clearLayout(self, layout):
		if layout == 'subs':
			layout = self.subtitles_vbox
			self.subtitles.hide()
		elif layout == 'subs2':
			layout = self.subtitles_vbox2
			self.subtitles2.hide()
		elif layout == 'popup':
			layout = self.popup_vbox
			self.popup.hide()

		if layout is not None:
			while layout.count():
				item = layout.takeAt(0)
				widget = item.widget()

				if widget is not None:
					widget.deleteLater()
				else:
					self.clearLayout(item.layout())

	def subtitles_base(self):
		self.subtitles = QFrame()
		self.subtitles.setAttribute(Qt.WA_TranslucentBackground)
		self.subtitles.setWindowFlags(Qt.X11BypassWindowManagerHint)
		self.subtitles.setStyleSheet(config.style_subs)

		self.subtitles_vbox = QVBoxLayout(self.subtitles)
		self.subtitles_vbox.setSpacing(config.subs_padding_between_lines)
		self.subtitles_vbox.setContentsMargins(0, 0, 0, 0)

	def subtitles_base2(self):
		self.subtitles2 = QFrame()
		self.subtitles2.setAttribute(Qt.WA_TranslucentBackground)
		self.subtitles2.setWindowFlags(Qt.X11BypassWindowManagerHint)
		self.subtitles2.setStyleSheet(config.style_subs)

		self.subtitles_vbox2 = QVBoxLayout(self.subtitles2)
		self.subtitles_vbox2.setSpacing(config.subs_padding_between_lines)
		self.subtitles_vbox2.setContentsMargins(0, 0, 0, 0)

		if config.pause_during_translation_B:
			self.subtitles2.enterEvent = lambda event : [mpv.pause(), setattr(config, 'block_popup', False)][0]
			self.subtitles2.leaveEvent = lambda event : [mpv.resume(), setattr(config, 'block_popup', True)][0] if not config.avoid_resuming else [setattr(config, 'avoid_resuming', False), setattr(config, 'block_popup', True)][0]

	def popup_base(self):
		self.popup = QFrame()
		self.popup.setAttribute(Qt.WA_TranslucentBackground)
		self.popup.setWindowFlags(Qt.X11BypassWindowManagerHint)
		self.popup.setStyleSheet(config.style_popup)

		self.popup_inner = QFrame()
		outer_box = QVBoxLayout(self.popup)
		outer_box.addWidget(self.popup_inner)

		self.popup_vbox = QVBoxLayout(self.popup_inner)
		self.popup_vbox.setSpacing(0)

	def render_subtitles(self, hide = False, redraw = False):
		if hide or not len(subs):
			try:
				self.subtitles.hide()
				self.subtitles2.hide()
			finally:
				return

		if redraw:
			self.subtitles.setStyleSheet(config.style_subs)
			self.subtitles2.setStyleSheet(config.style_subs)
		else:
			self.clearLayout('subs')
			self.clearLayout('subs2')

			if hasattr(self, 'popup'):
				self.popup.hide()

			# if subtitle consists of one overly long line - split into two
			if config.split_long_lines_B and len(subs.split('\n')) == 1 and len(subs.split(' ')) > config.split_long_lines_words_min - 1:
				subs2 = split_long_lines(subs)
			else:
				subs2 = subs

			subs2 = re.sub(' +', ' ', subs2).strip()

			##############################

			for line in subs2.split('\n'):
				line2 = ' %s ' % line.strip()
				ll = drawing_layer(line2, subs2)

				hbox = QHBoxLayout()
				hbox.setContentsMargins(0, 0, 0, 0)
				hbox.setSpacing(0)
				hbox.addStretch()
				hbox.addWidget(ll)
				hbox.addStretch()
				self.subtitles_vbox.addLayout(hbox)

				####################################

				hbox = QHBoxLayout()
				hbox.setContentsMargins(0, 0, 0, 0)
				hbox.setSpacing(0)
				hbox.addStretch()

				if config.R2L_from_B:
					line2 = line2[::-1]

				line2 += '\00'
				word = ''
				for smbl in line2:
					if smbl.isalpha():
						word += smbl
					else:
						if len(word):
							if config.R2L_from_B:
								word = word[::-1]

							ll = events_class(word, subs2)
							ll.mouseHover.connect(self.render_popup)
							ll.redraw.connect(self.render_subtitles)

							hbox.addWidget(ll)
							word = ''

						if smbl != '\00':
							ll = events_class(smbl, subs2, skip = True)
							hbox.addWidget(ll)

				hbox.addStretch()
				self.subtitles_vbox2.addLayout(hbox)

		self.subtitles.adjustSize()
		self.subtitles2.adjustSize()

		w = self.subtitles.geometry().width()
		h = self.subtitles.height = self.subtitles.geometry().height()

		x = (config.screen_width/2) - (w/2)

		if config.subs_top_placement_B:
			y = config.subs_screen_edge_padding
		else:
			y = config.screen_height - config.subs_screen_edge_padding - h

		self.subtitles.setGeometry(int(x), int(y), 0, 0)
		self.subtitles.show()

		self.subtitles2.setGeometry(int(x), int(y), 0, 0)
		self.subtitles2.show()

	def render_popup(self, text, x_cursor_pos, is_line):
		if text == '':
			if hasattr(self, 'popup'):
				self.popup.hide()
			return

		self.clearLayout('popup')

		if is_line:
			QApplication.setOverrideCursor(Qt.WaitCursor)
			
			line = globals()[config.translation_function_name_full_sentence](text)
			if config.translation_function_name_full_sentence == 'google':
				try:
					line = line[0][0][0].strip()
				except:
					line = 'Google translation failed.'
			
			if config.split_long_lines_B and len(line.split('\n')) == 1 and len(line.split(' ')) > config.split_long_lines_words_min - 1:
				line = split_long_lines(line)

			ll = QLabel(line)
			ll.setObjectName("first_line")
			self.popup_vbox.addWidget(ll)
		else:
			word = text

			for translation_function_name_i, translation_function_name in enumerate(config.translation_function_names):
				pairs, word_descr = globals()[translation_function_name](word)

				if not len(pairs):
					pairs = [['', '[Not found]']]
					#return

				# ~pairs = [ [ str(i) + ' ' + pair[0], pair[1] ] for i, pair in enumerate(pairs) ]

				if word in config.scroll:
					if len(pairs[config.scroll[word]:]) > config.number_of_translations:
						pairs = pairs[config.scroll[word]:]
					else:
						pairs = pairs[-config.number_of_translations:]
						if len(config.translation_function_names) == 1:
							config.scroll[word] -= 1

				for i1, pair in enumerate(pairs):
					if i1 == config.number_of_translations:
						break

					if config.split_long_lines_in_popup_B:
						pair[0] = split_long_lines(pair[0], max_symbols_per_line = config.split_long_lines_in_popup_symbols_min)
						pair[1] = split_long_lines(pair[1], max_symbols_per_line = config.split_long_lines_in_popup_symbols_min)

					if pair[0] == '-':
						pair[0] = ''
					if pair[1] == '-':
						pair[1] = ''

					# ~if config.R2L_from_B:
						# ~pair[0] = pair[0][::-1]
					# ~if config.R2L_to_B:
						# ~pair[1] = pair[1][::-1]

					if pair[0] != '':
						# to emphasize the exact form of the word
						# to ignore case on input and match it on output
						chnks = re.split(word, pair[0], flags = re.I)
						exct_words = re.findall(word, pair[0], flags = re.I)

						hbox = QHBoxLayout()
						hbox.setContentsMargins(0, 0, 0, 0)

						for i2, chnk in enumerate(chnks):
							if len(chnk):
								ll = QLabel(chnk)
								ll.setObjectName("first_line")
								hbox.addWidget(ll)
							if i2 + 1 < len(chnks):
								ll = QLabel(exct_words[i2])
								ll.setObjectName("first_line_emphasize_word")
								hbox.addWidget(ll)

						# filling the rest of the line with empty bg
						ll = QLabel()
						ll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
						hbox.addWidget(ll)

						self.popup_vbox.addLayout(hbox)

					if pair[1] != '':
						ll = QLabel(pair[1])
						ll.setObjectName("second_line")
						self.popup_vbox.addWidget(ll)

						# padding
						ll = QLabel()
						ll.setStyleSheet("font-size: 6px;")
						self.popup_vbox.addWidget(ll)

				if len(word_descr[0]):
					ll = QLabel(word_descr[0])
					ll.setProperty("morphology", word_descr[1])
					ll.setAlignment(Qt.AlignRight)
					self.popup_vbox.addWidget(ll)

				# delimiter between dictionaries
				if translation_function_name_i + 1 < len(config.translation_function_names):
					ll = QLabel()
					ll.setObjectName("delimiter")
					self.popup_vbox.addWidget(ll)

		self.popup_inner.adjustSize()
		self.popup.adjustSize()

		w = self.popup.geometry().width()
		h = self.popup.geometry().height()

		if w > config.screen_width:
			w = config.screen_width - 20

		if not is_line:
			if w < config.screen_width / 3:
				w = config.screen_width / 3

		if x_cursor_pos == -1:
			x = (config.screen_width/2) - (w/2)
		else:
			x = x_cursor_pos - w/5
			if x+w > config.screen_width:
				x = config.screen_width - w

		if config.subs_top_placement_B:
			y = self.subtitles.height + config.subs_screen_edge_padding
		else:
			y = config.screen_height - config.subs_screen_edge_padding - self.subtitles.height - h

		self.popup.setGeometry(int(x), int(y), int(w), 0)
		self.popup.show()

		QApplication.restoreOverrideCursor()

if __name__ == "__main__":
	print('[py part] Starting interSubs ...')

	try:
		os.mkdir('urls')
	except:
		pass

	mpv_socket_path = sys.argv[1]
	mpv = Mpv(mpv_socket_path)
	sub_file = sys.argv[2]

	subs = ''

	app = QApplication(sys.argv)

	config.avoid_resuming = False
	config.block_popup = False
	config.scroll = {}
	config.queue_to_translate = queue.Queue()
	config.screen_width = app.primaryScreen().size().width()
	config.screen_height = app.primaryScreen().size().height()

	form = main_class()
	app.exec_()
