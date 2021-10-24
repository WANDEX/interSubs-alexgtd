from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLayout


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
