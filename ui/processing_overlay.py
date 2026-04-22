import ctypes
import math
import platform
import sys
from math import sin, pi

import PySide6
from PyQt6.QtGui import QPaintEvent
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QLinearGradient
from PySide6.QtWidgets import QApplication, QWidget


class ProcessingOverlay(QWidget):
    """
    A small always-on-top overlay displayed at the top of the screen
    showing an indeterminate processing animation.
    """

    def __init__(self, width: int = 200, height: int = 20):
        """
        Initialize the processing overlay.

        :param height: The height of the overlay bar in pixels.
        """
        super().__init__()

        self._phase = 0.0
        self._speed = 0.01  # phase increment per tick

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        # No border and no margins
        self.setContentsMargins(0, 0, 0, 0)
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(int((screen.width() - width)/2), screen.y(), width, height)
        self.setFixedHeight(height)

        # Animation timer (~60 FPS)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(16)

        self.bar_width = 6
        self.bar_gap = 2

        self.paintAnimation = None
        self.set_waiting()

    def set_loading(self):
        self.paintAnimation = self.__paint_comet

    def set_waiting(self):
        self.paintAnimation = self.__paint_comet

    def set_playing(self):
        self.paintAnimation = self.__paint_multi_sonogram

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        if callable(self.paintAnimation):
            self.paintAnimation(event)

    def _on_tick(self) -> None:
        """
        Advance the animation phase and trigger a repaint.
        """
        self._phase += self._speed
        if self._phase > 1.0:
            self._phase -= 1.0
        self.update()

    def __paint_multi_sonogram(self, event: QPaintEvent) -> None:
        """
        Paint animated bars like a sonogram using multiple waves.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        step = self.bar_width + self.bar_gap
        bar_count = max(1, width // step)

        base_color = QColor(0, 140, 255, 220)
        peak_color = QColor(80, 220, 255, 245)

        for index in range(bar_count):
            x = index * step
            center_x = x + self.bar_width / 2
            xn = index / max(1, bar_count - 1)

            wave1 = 0.5 + 0.5 * math.sin((xn * 10.0) + self._phase * 2 * math.pi * 1.7)
            wave2 = 0.5 + 0.5 * math.sin((xn * 22.0) - self._phase * 2 * math.pi * 2.1)
            wave3 = 0.5 + 0.5 * math.sin((xn * 6.0) + self._phase * 2 * math.pi * 0.8)

            envelope = 0.6 + 0.4 * math.sin(self._phase * 2 * math.pi * 0.55)

            level = (0.5 * wave1 + 0.3 * wave2 + 0.2 * wave3) * envelope
            level = max(0.08, min(1.0, level))

            min_h = max(2, int(height * 0.12))
            max_h = height - 2
            bar_height = min_h + level * (max_h - min_h)
            y = int((height - bar_height) / 2)

            color_mix = min(1.0, level * 1.1)
            r = int(base_color.red() * (1 - color_mix) + peak_color.red() * color_mix)
            g = int(base_color.green() * (1 - color_mix) + peak_color.green() * color_mix)
            b = int(base_color.blue() * (1 - color_mix) + peak_color.blue() * color_mix)
            a = int(base_color.alpha() * (1 - color_mix) + peak_color.alpha() * color_mix)

            painter.fillRect(
                int(center_x - self.bar_width / 2),
                y,
                self.bar_width,
                int(bar_height),
                QColor(r, g, b, a),
            )

        painter.end()

    def __paint_pulse(self, event: QPaintEvent) -> None:
        """
        Paint bars pulsing from the center to the edges.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        step = self.bar_width + self.bar_gap
        bar_count = max(1, width // step)
        center = (bar_count - 1) / 2

        color = QColor(0, 150, 255, 230)

        for index in range(bar_count):
            x = index * step
            dist = abs(index - center) / max(1.0, center)

            # La phase se propage vers l'extérieur
            propagation = self._phase * 2 * math.pi * 2.0 - dist * 7.0
            pulse = 0.5 + 0.5 * math.sin(propagation)

            # Accentuation du contraste
            pulse = pulse ** 2.2

            level = (1.0 - dist * 0.55) * (0.15 + 0.85 * pulse)
            level = max(0.05, min(1.0, level))

            min_h = max(2, int(height * 0.10))
            max_h = height - 2
            bar_height = min_h + level * (max_h - min_h)
            y = int((height - bar_height) / 2)

            alpha = int(120 + 120 * level)
            painter.fillRect(
                x,
                y,
                self.bar_width,
                int(bar_height),
                QColor(color.red(), color.green(), color.blue(), alpha),
            )

        painter.end()

    def __paint_comet(self, event: QPaintEvent) -> None:
        """
        Paint a moving comet-like pulse with a smooth trailing effect.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        step = self.bar_width + self.bar_gap
        bar_count = max(1, width // step)

        head_pos = self._phase * (bar_count + 10) - 5

        for index in range(bar_count):
            x = index * step
            d = index - head_pos

            # Tête + traîne exponentielle
            if d < 0:
                intensity = math.exp(d / 4.0)
            else:
                intensity = math.exp(-d / 1.5)

            intensity = max(0.0, min(1.0, intensity))

            wave = 0.75 + 0.25 * math.sin(index * 0.9 + self._phase * 2 * math.pi * 3.0)
            level = max(0.05, min(1.0, intensity * wave))

            min_h = max(2, int(height * 0.15))
            max_h = height - 2
            bar_height = min_h + level * (max_h - min_h)
            y = int((height - bar_height) / 2)

            alpha = int(40 + 210 * intensity)
            blue = int(180 + 75 * intensity)

            painter.fillRect(
                x,
                y,
                self.bar_width,
                int(bar_height),
                QColor(0, 120, blue, alpha),
            )

        painter.end()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = ProcessingOverlay()
    overlay.show()
    sys.exit(app.exec())
