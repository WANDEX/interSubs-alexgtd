from typing import Callable

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLayout

from ui.custom_label import HighlightableLabel, HoverableLabel


def create_frame(style_sheet: str) -> QFrame:
    frame = QFrame()
    frame.setAttribute(Qt.WA_TranslucentBackground)
    frame.setWindowFlags(Qt.X11BypassWindowManagerHint)
    frame.setStyleSheet(style_sheet)
    return frame


def clear_layout(layout: QLayout) -> None:
    layout.parentWidget().hide()

    while not layout.isEmpty():
        item = layout.takeAt(0)
        if not item:
            return

        widget = item.widget()
        if widget:
            widget.deleteLater()


def get_label_factory(config) -> Callable[[str], HoverableLabel]:
    if config.is_subs_outlined:
        label_factory = lambda string: HighlightableLabel(string, config)
    else:
        label_factory = HoverableLabel
    return label_factory