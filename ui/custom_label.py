from PyQt5.QtCore import Qt, QEvent, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QBrush, QPen, QPalette, QPaintEvent, QFontMetrics
from PyQt5.QtWidgets import QLabel


class HoverableLabel(QLabel):
    on_hover_enter = pyqtSignal(QEvent)
    on_hover_leave = pyqtSignal(QEvent)

    def event(self, e: QEvent) -> bool:
        if e.type() == QEvent.Enter:
            self.on_hover_enter.emit(e)
            return super().event(e)
        elif e.type() == QEvent.Leave:
            self.on_hover_leave.emit(e)
            return super().event(e)
        else:
            return super().event(e)


class OutlinedLabel(HoverableLabel):
    def __init__(self, text: str, config):
        super().__init__(text)
        self._cfg = config

    def paintEvent(self, e: QPaintEvent) -> None:
        self._draw_text_and_outline()

    def _draw_text_and_outline(self) -> None:
        x = 0
        y = 0
        y += self.fontMetrics().ascent()
        y = y + self._cfg.outline_top_padding - self._cfg.outline_bottom_padding

        painter = QPainter(self)
        text_painter_path = self._get_text_painter_path(x, y)

        self._draw_blurred_outline(painter, text_painter_path)
        self._draw_outline(painter, text_painter_path, QColor(self._cfg.outline_color), self._cfg.outline_width)
        self._draw_text(painter, x, y)

    def _get_text_painter_path(self, x: int, y: int) -> QPainterPath:
        text_painter_path = QPainterPath()
        text_painter_path.addText(x, y, self.font(), self.text())
        return text_painter_path

    def _draw_blurred_outline(self, painter: QPainter, text_path: QPainterPath) -> None:
        blur_color = QColor(self._cfg.outline_color)
        range_width = range(self._cfg.outline_width, self._cfg.outline_width + self._cfg.outline_blur_width)

        for width in range_width:
            if width == min(range_width):
                alpha = 200
            else:
                alpha = (max(range_width) - width) / max(range_width) * 200
                alpha = int(alpha)

            blur_color.setAlpha(alpha)
            self._draw_outline(painter, text_path, blur_color, width)

    def _draw_outline(self, painter: QPainter, text_path: QPainterPath, color: QColor, pen_width: int) -> None:
        outline_brush = QBrush(color, Qt.SolidPattern)
        outline_pen = QPen(outline_brush, pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(outline_pen)
        painter.drawPath(text_path)

    def _draw_text(self, painter: QPainter, x: int, y: int) -> None:
        color = self.palette().color(QPalette.Text)
        painter.setPen(color)
        painter.drawText(x, y, self.text())


class HighlightableLabel(OutlinedLabel):
    def __init__(self, text: str, config):
        super().__init__(text, config)
        self.setMouseTracking(True)
        self._is_highlighting = False
        self.on_hover_enter.connect(self._highlight)
        self.on_hover_leave.connect(self._unhighlight)

    def paintEvent(self, e: QPaintEvent) -> None:
        super().paintEvent(e)
        if self._is_highlighting:
            self._draw_highlighting()

    def _draw_highlighting(self) -> None:
        color = QColor(self._cfg.highlighting_color)
        color.setAlpha(200)
        painter = QPainter(self)

        if self._cfg.is_hover_underline:
            underline_width = self._cfg.underlined_highlighting_width
            font_metrics = QFontMetrics(self.font())
            text_width = font_metrics.width(self.text())
            text_height = font_metrics.height()

            brush = QBrush(color)
            pen = QPen(brush, underline_width, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(0, text_height - underline_width, text_width, text_height - underline_width)

        if self._cfg.is_hover_highlight:
            x = y = 0
            y += self.fontMetrics().ascent()

            painter.setPen(color)
            painter.drawText(x, y + self._cfg.outline_top_padding - self._cfg.outline_bottom_padding, self.text())

    def _highlight(self) -> None:
        self._is_highlighting = True
        self.update()

    def _unhighlight(self) -> None:
        self._is_highlighting = False
        self.update()
