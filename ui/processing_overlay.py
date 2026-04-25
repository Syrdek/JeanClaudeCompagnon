import math
import sys

from PySide6.QtGui import QPaintEvent, QIcon
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QApplication, QWidget


def _mix_colors(color1: QColor, color2: QColor, ratio: float) -> QColor:
    ratio = max(0.0, min(1.0, ratio))
    inv = 1.0 - ratio
    return QColor(
        int(color1.red() * inv + color2.red() * ratio),
        int(color1.green() * inv + color2.green() * ratio),
        int(color1.blue() * inv + color2.blue() * ratio),
        int(color1.alpha() * inv + color2.alpha() * ratio),
    )


class ProcessingOverlay(QWidget):
    """
    A small always-on-top overlay displayed at the top of the screen
    showing an indeterminate processing animation.
    """

    def __init__(self, width: int = 200, height: int = 20, bar_color: QColor | list[int] | tuple[int, int, int] | tuple[int, int, int, int] = (0, 140, 255, 220)):
        """
        Initialize the processing overlay.

        :param width: The width of the overlay in pixels.
        :param height: The height of the overlay bar in pixels.
        :param bar_color: The color of the bar overlay.
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

        self.setWindowIcon(QIcon("icon.png"))

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
        self._bar_color = self._normalize_color(bar_color)

        self.paintAnimation = None
        self.set_waiting()

    def set_loading(self):
        """
        Set the overlay animation to loading mode.
        """
        self.paintAnimation = self.__paint_comet

    def set_waiting(self):
        """
        Set the overlay animation to waiting mode.
        """
        self.paintAnimation = self.__paint_pulse

    def set_playing(self):
        """
        Set the overlay animation to playing mode.
        """
        self.paintAnimation = self.__paint_multi_sonogram

    @property
    def bar_color(self) -> QColor:
        return QColor(self._bar_color)

    @bar_color.setter
    def bar_color(self, value: QColor | tuple[int, int, int] | tuple[int, int, int, int]) -> None:
        self._bar_color = self._normalize_color(value)
        self.update()

    def _normalize_color(self, value: QColor | list[int] | tuple[int, int, int] | tuple[int, int, int, int]) -> QColor:
        """
        Normalize a color value to a QColor object.

        Supports QColor, list, or tuple with 3 (RGB) or 4 (RGBA) components.

        :param value: The color value to normalize.
        :return: A valid QColor object.
        :raises ValueError: If the tuple length is invalid or the color is not valid.
        :raises TypeError: If the value type is unsupported.
        """
        if isinstance(value, list):
            return self._normalize_color(tuple(value))
        if isinstance(value, QColor):
            color = QColor(value)
        elif isinstance(value, tuple):
            if len(value) == 3:
                color = QColor(*value, 220)
            elif len(value) == 4:
                color = QColor(*value)
            else:
                raise ValueError("bar_color tuple must contain 3 (RGB) or 4 (RGBA) integers")
        else:
            raise TypeError("bar_color must be a QColor or an RGB/RGBA tuple")

        if not color.isValid():
            raise ValueError("Invalid bar_color value")
        return color

    def _bar_color_variant(self, brightness_factor: float = 1.0, alpha_factor: float = 1.0) -> QColor:
        """
        Generate a variant of the bar color with adjusted brightness and alpha.

        :param brightness_factor: Factor to lighten (>1.0) or darken (<1.0) the color.
        :param alpha_factor: Factor to scale the alpha channel.
        :return: A new QColor with the modified properties.
        """
        color = QColor(self._bar_color)
        if brightness_factor >= 1.0:
            color = color.lighter(int(brightness_factor * 100))
        else:
            color = color.darker(max(1, int(100 / brightness_factor)))
        color.setAlpha(max(0, min(255, int(self._bar_color.alpha() * alpha_factor))))
        return color

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Paint the overlay background and the active animation.

        :param event: The Qt paint event.
        """
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

        base_color = self._bar_color_variant(brightness_factor=1.0, alpha_factor=1.0)
        peak_color = self._bar_color_variant(brightness_factor=1.45, alpha_factor=1.12)

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
            mixed_color = _mix_colors(base_color, peak_color, color_mix)

            painter.fillRect(
                int(center_x - self.bar_width / 2),
                y,
                self.bar_width,
                int(bar_height),
                mixed_color,
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

        color = self._bar_color_variant(brightness_factor=1.08, alpha_factor=1.05)

        for index in range(bar_count):
            x = index * step
            dist = abs(index - center) / max(1.0, center)

            # The phase propagates outward
            propagation = self._phase * 2 * math.pi * 2.0 - dist * 7.0
            pulse = 0.5 + 0.5 * math.sin(propagation)

            # Contrast enhancement
            pulse = pulse ** 2.2

            level = (1.0 - dist * 0.55) * (0.15 + 0.85 * pulse)
            level = max(0.05, min(1.0, level))

            min_h = max(2, int(height * 0.10))
            max_h = height - 2
            bar_height = min_h + level * (max_h - min_h)
            y = int((height - bar_height) / 2)

            alpha = int(120 + 120 * level)
            pulse_color = QColor(color)
            pulse_color.setAlpha(max(0, min(255, alpha)))

            painter.fillRect(
                x,
                y,
                self.bar_width,
                int(bar_height),
                pulse_color,
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

            # Head + exponential tail
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
            comet_base = self._bar_color_variant(brightness_factor=0.85, alpha_factor=0.35)
            comet_head = self._bar_color_variant(brightness_factor=1.35, alpha_factor=1.0)
            comet_color = _mix_colors(comet_base, comet_head, intensity)
            comet_color.setAlpha(max(0, min(255, alpha)))

            painter.fillRect(
                x,
                y,
                self.bar_width,
                int(bar_height),
                comet_color,
            )

        painter.end()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = ProcessingOverlay()
    overlay.bar_color = (250, 250, 250)
    overlay.set_waiting()
    overlay.show()
    sys.exit(app.exec())
