#! /usr/bin/env python

import sys

from PyQt5.QtWidgets import QApplication

import config
from data_provider.subtitles_data_source import SubtitlesDataSourceWorker
from mpv import Mpv
from ui.popup_view import PopupView
from ui.subtitles_view import SubtitlesView


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
