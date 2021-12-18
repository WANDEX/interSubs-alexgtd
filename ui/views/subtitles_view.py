from typing import Callable, Tuple

from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QVBoxLayout, QBoxLayout

from ui.util import create_frame, clear_layout, get_label_factory
from ui.views.view import View


def create_vertical_linear_layout(parent: QWidget, spacing: int) -> QVBoxLayout:
    vertical_linear_layout = QVBoxLayout(parent)
    vertical_linear_layout.setSpacing(spacing)
    vertical_linear_layout.setContentsMargins(0, 0, 0, 0)
    return vertical_linear_layout


def create_horizontal_linear_layout() -> QHBoxLayout:
    horizontal_linear_layout = QHBoxLayout()
    horizontal_linear_layout.setContentsMargins(0, 0, 0, 0)
    horizontal_linear_layout.setSpacing(20)
    return horizontal_linear_layout


def split_string_by_words_limit(text: str, limit: int) -> Tuple[str, str]:
    result = text, ""
    words_list = text.split()
    words_to_split = int(len(words_list) / 2)

    if len(words_list) > limit:
        first_line = " ".join(words_list[0:words_to_split])
        second_line = " ".join(words_list[words_to_split:len(words_list)])
        result = first_line, second_line

    return result


class SubtitlesLine:
    def __init__(self, parent_layout: QBoxLayout, config) -> None:
        self._cfg = config
        self._line_layout = create_horizontal_linear_layout()
        parent_layout.addLayout(self._line_layout)

        # default empty function to avoid null checking
        self.on_text_hover_enter: Callable[[str, QEvent], None] = lambda text, event: None

    def set_text(self, text: str) -> None:
        clear_layout(self._line_layout)
        if text:
            self._populate_layout_with_widgets(text)

    def _populate_layout_with_widgets(self, text: str) -> None:
        label_factory = get_label_factory(self._cfg)
        self._line_layout.addStretch()

        for word in text.split():
            label = label_factory(word)
            label.setMouseTracking(True)
            label.on_hover_enter.connect(self._enclose_text_into_on_hover_enter_event(word))
            self._line_layout.addWidget(label)

        self._line_layout.addStretch()

    def _enclose_text_into_on_hover_enter_event(self, text: str) -> Callable[[QEvent], None]:
        def on_hover_enter(e: QEvent) -> None:
            self.on_text_hover_enter(text, e)

        return on_hover_enter


class SubtitlesView(View):
    def __init__(self, config) -> None:
        super().__init__()
        self._cfg = config
        self._frame = create_frame(self._cfg.style_subs)
        self._layout = create_vertical_linear_layout(self._frame, self._cfg.subs_padding_between_lines)

        self._first_subs_line = SubtitlesLine(self._layout, self._cfg)
        self._second_subs_line = SubtitlesLine(self._layout, self._cfg)
        self._first_subs_line.on_text_hover_enter = self.on_text_hover_enter
        self._second_subs_line.on_text_hover_enter = self.on_text_hover_enter

    def submit_subs(self, subs_text: str) -> None:
        first_line, second_line = split_string_by_words_limit(subs_text, 5)

        self._first_subs_line.set_text(first_line)
        self._second_subs_line.set_text(second_line)

        self.set_subs_frames_x_y_axis()
        self.show()

    def on_text_hover_enter(self, text: str, event: QEvent) -> None:
        self.presenter.on_text_hover_enter(text, event)

    def show(self) -> None:
        self._frame.show()

    def set_subs_frames_x_y_axis(self) -> None:
        self._frame.adjustSize()

        w = self._frame.geometry().width()
        h = self._frame.height = self._frame.geometry().height()
        x = (self._cfg.screen_width / 2) - (w / 2)

        if self._cfg.subs_top_placement_B:
            y = self._cfg.subs_screen_edge_padding
        else:
            y = self._cfg.screen_height - self._cfg.subs_screen_edge_padding - h

        self._frame.setGeometry(int(x), int(y), 0, 0)
