from typing import Callable, Tuple

from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QVBoxLayout, QBoxLayout

from ui.util import create_frame, clear_layout, get_label_factory


def create_vertical_linear_layout(parent: QWidget, spacing: int) -> QVBoxLayout:
    vertical_linear_layout = QVBoxLayout(parent)
    vertical_linear_layout.setSpacing(spacing)
    vertical_linear_layout.setContentsMargins(0, 0, 0, 0)
    return vertical_linear_layout


def create_horizontal_linear_layout() -> QHBoxLayout:
    horizontal_linear_layout = QHBoxLayout()
    horizontal_linear_layout.setContentsMargins(0, 0, 0, 0)
    horizontal_linear_layout.setSpacing(20)
    horizontal_linear_layout.addStretch()
    return horizontal_linear_layout


def split_string_by_words_limit(text: str, limit: int) -> Tuple[str, str]:
    result = text, ""
    words_count_to_split = 4
    words_list = text.split()

    if len(words_list) > limit:
        first_line = " ".join(words_list[0:words_count_to_split])
        second_line = " ".join(words_list[words_count_to_split:len(words_list)])
        result = first_line, second_line

    return result


class SubtitlesLine:
    def __init__(self, parent_layout: QBoxLayout, config):
        self.cfg = config
        self.line_layout = create_horizontal_linear_layout()
        parent_layout.addLayout(self.line_layout)

        self.mouse_enter_event_handler: Callable[[str, QEvent], None] = lambda text, event: None

    def set_text(self, text: str) -> None:
        clear_layout(self.line_layout)
        label_factory = get_label_factory(self.cfg)
        for word in text.split():
            label = label_factory(word)
            label.setMouseTracking(True)
            label.on_enter.connect(self.enclose_text_into_mouse_enter_event_handler(word))
            self.line_layout.addWidget(label)

    def enclose_text_into_mouse_enter_event_handler(self, text: str) -> Callable[[QEvent], None]:
        def enter_event(event: QEvent):
            self.mouse_enter_event_handler(text, event)

        return enter_event

    def register_mouse_enter_event_handler(self, handler: Callable[[str, QEvent], None]) -> None:
        self.mouse_enter_event_handler = handler


class SubtitlesView:
    def __init__(self, config):
        self.cfg = config
        self.frame = create_frame(self.cfg.style_subs)
        self.outer_layout = create_vertical_linear_layout(self.frame, self.cfg.subs_padding_between_lines)

        self.first_subs_line = SubtitlesLine(self.outer_layout, self.cfg)
        self.second_subs_line = SubtitlesLine(self.outer_layout, self.cfg)

    def submit_subs(self, subs_text: str) -> None:
        subs_lines = split_string_by_words_limit(subs_text, 5)

        self.first_subs_line.set_text(subs_lines[0])
        self.second_subs_line.set_text(subs_lines[1])

        self.set_subs_frames_x_y_axis()
        self.show()

    def register_text_hover_event_handler(self, handler: Callable[[str, QEvent], None]) -> None:
        self.first_subs_line.register_mouse_enter_event_handler(handler)
        self.second_subs_line.register_mouse_enter_event_handler(handler)

    def show(self) -> None:
        self.frame.show()

    def hide(self) -> None:
        self.frame.hide()

    def set_subs_frames_x_y_axis(self) -> None:
        self.frame.adjustSize()

        w = self.frame.geometry().width()
        h = self.frame.height = self.frame.geometry().height()
        x = (self.cfg.screen_width / 2) - (w / 2)

        if self.cfg.subs_top_placement_B:
            y = self.cfg.subs_screen_edge_padding
        else:
            y = self.cfg.screen_height - self.cfg.subs_screen_edge_padding - h

        self.frame.setGeometry(int(x), int(y), 0, 0)
