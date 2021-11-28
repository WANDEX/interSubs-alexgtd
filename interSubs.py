#! /usr/bin/env python
import argparse
import logging
import os
import sys

from PyQt5.QtWidgets import QApplication

import config
from data.subtitles_data_source import SubtitlesDataSourceWorker
from ui.popup_view import PopupView
from ui.subtitles_view import SubtitlesView

log = logging.getLogger()


def init_logger() -> None:
    log.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)

    script_name = os.path.splitext(os.path.basename(__file__))[0]

    file_handler = logging.FileHandler(f"{script_name}.log")
    file_handler.setLevel(logging.INFO)

    basic_info = "%(name)s %(levelname)s: %(message)s"
    console_handler.setFormatter(logging.Formatter(f"[{script_name}-python] {basic_info}"))
    file_handler.setFormatter(logging.Formatter(f"%(asctime)s {basic_info}"))

    log.addHandler(file_handler)
    log.addHandler(console_handler)


def parse_command_line_arguments() -> argparse.Namespace:
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("-i", "--ipc-file-path", required=True)
    args_parser.add_argument("-s", "--subs-file-path", required=True)
    args = args_parser.parse_args()
    return args


def main():
    os.chdir(os.path.dirname(__file__))
    init_logger()
    log.info("Start.")

    args = parse_command_line_arguments()
    app = QApplication(sys.argv)

    cfg = config
    cfg.screen_width = app.primaryScreen().size().width()
    cfg.screen_height = app.primaryScreen().size().height()

    subs_view = SubtitlesView(cfg)
    popup_view = PopupView(cfg)
    subs_view.register_text_hover_event_handler(popup_view.pop)

    subs_data_source = SubtitlesDataSourceWorker(args.subs_file_path)
    subs_data_source.on_subtitles_change.connect(popup_view.hide)
    subs_data_source.on_subtitles_change.connect(subs_view.submit_subs)
    subs_data_source.on_error.connect(
        lambda e: log.error("Exception occurred while watching the subtitles file.", exc_info=e)
    )
    subs_data_source.start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
