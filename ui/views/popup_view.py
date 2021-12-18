from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QVBoxLayout, QLabel

from ui.views.view import View
from ui.util import create_frame, clear_layout


class PopupView(View):
    def __init__(self, config) -> None:
        super().__init__()
        self.config = config
        self.frame = create_frame(self.config.style_popup)
        self.layout = QVBoxLayout(self.frame)

    def pop(self, string: str, event: QMouseEvent) -> None:
        clear_layout(self.layout)
        self.set_text(string)
        self.set_x_y_axis(event)
        self.show()

    def set_text(self, text: str) -> None:
        label = QLabel(text)
        self.layout.addWidget(label)

    def show(self) -> None:
        self.frame.show()

    def hide(self) -> None:
        self.frame.hide()

    def set_x_y_axis(self, event: QMouseEvent) -> None:
        x_cursor_pos = event.globalX()
        self.frame.adjustSize()

        w = self.frame.geometry().width()
        h = self.frame.geometry().height()

        if w > self.config.screen_width:
            w = self.config.screen_width - 20

        if x_cursor_pos == -1:
            x = (self.config.screen_width / 2) - (w / 2)
        else:
            x = x_cursor_pos - w / 5
            if x + w > self.config.screen_width:
                x = self.config.screen_width - w

        if self.config.subs_top_placement_B:
            y = self.first_subs_frame.height + self.config.subs_screen_edge_padding
        else:
            y = self.config.screen_height - self.config.subs_screen_edge_padding - h - 120

        self.frame.setGeometry(int(x), int(y), int(w), 0)
