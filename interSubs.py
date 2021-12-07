#! /usr/bin/env python
import logging
import os

import ui

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


def main():
    os.chdir(os.path.dirname(__file__))

    init_logger()
    ui.run()


if __name__ == "__main__":
    main()
