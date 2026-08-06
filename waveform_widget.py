import os
import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, pyqtSignal

class InteractiveWaveformWidget(QWidget):
    position_changed = pyqtSignal(int) # Emits position in ms when user interacts

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.waveform_data = None
        self.duration_ms = 0
        self.current_position_ms = 0

        self.zoom_level = 1.0
        self.offset_x = 0
        self.is_dragging = False

    def load_waveform(self, cache_path, duration_ms):
        self.duration_ms = duration_ms
        if os.path.exists(cache_path):
            try:
                self.waveform_data = np.load(cache_path)
            except Exception as e:
                print(f"Error loading waveform: {e}")
                self.waveform_data = None
        else:
            self.waveform_data = None

        self.zoom_level = 1.0
        self.offset_x = 0
        self.current_position_ms = 0
        self.update()

    def set_position(self, pos_ms):
        if not self.is_dragging:
            self.current_position_ms = pos_ms

            # Auto-scroll logic if zoomed in
            if self.waveform_data is not None and self.zoom_level > 1.0:
                playhead_x = self._ms_to_x(pos_ms)
                # If playhead goes beyond 80% of width, scroll
                visible_width = self.width()
                if playhead_x > visible_width * 0.8:
                    self.offset_x -= (playhead_x - visible_width * 0.5) # Center it

            self.update()

    def _ms_to_x(self, ms):
        if self.duration_ms == 0 or self.waveform_data is None: return 0
        ratio = ms / self.duration_ms
        total_width = self.width() * self.zoom_level
        return int(ratio * total_width) + self.offset_x

    def _x_to_ms(self, x):
        if self.waveform_data is None or self.width() == 0: return 0
        total_width = self.width() * self.zoom_level
        adj_x = x - self.offset_x
        ratio = adj_x / total_width
        return max(0, min(self.duration_ms, int(ratio * self.duration_ms)))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor("#0f1015"))

        if self.waveform_data is None:
            painter.setPen(QColor("#ffffff"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Waveform Not Available")
            return

        w = self.width()
        h = self.height()

        # Draw multi-band waveform
        # waveform_data shape is (N, 3) where channels are Lows(Red), Mids(Green), Highs(Blue)
        # N can be quite large, so we downsample visually based on width

        total_width = w * self.zoom_level
        N = len(self.waveform_data)

        # To avoid drawing thousands of lines, we step based on pixels
        # 1 pixel = how many samples?
        samples_per_pixel = max(1, N / total_width)

        start_x = max(0, -self.offset_x)
        end_x = min(total_width, start_x + w)

        painter.setPen(Qt.PenStyle.NoPen)

        for x in range(int(start_x), int(end_x)):
            # find corresponding sample index
            idx = int(x * samples_per_pixel)
            if idx >= N: break

            # Simple downsampling (max over the window)
            end_idx = int((x+1) * samples_per_pixel)
            if end_idx > N: end_idx = N

            if end_idx > idx:
                chunk = self.waveform_data[idx:end_idx]
                val = np.max(chunk, axis=0)
            else:
                val = self.waveform_data[idx]

            lows, mids, highs = val

            # Mix colors: Lows -> Red, Mids -> Green, Highs -> Blue
            r = int(lows * 255)
            g = int(mids * 255)
            b = int(highs * 255)

            # Transient/High Energy (Yellow) if lows and mids are high
            if r > 200 and g > 200:
                b = max(0, b - 50)

            color = QColor(min(255, r), min(255, g), min(255, b))

            # Draw a vertical line representing amplitude
            # Total amplitude = sum or max? Let's use max of bands
            amp = max(lows, mids, highs)
            line_h = int(amp * h)

            draw_x = int(x + self.offset_x)

            # Draw mirrored
            y1 = (h - line_h) // 2

            painter.fillRect(draw_x, y1, 1, line_h, color)

        # Draw Playhead
        playhead_x = self._ms_to_x(self.current_position_ms)
        if 0 <= playhead_x <= w:
            painter.setPen(QPen(QColor("#ffffff"), 2))
            painter.drawLine(playhead_x, 0, playhead_x, h)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            pos_ms = self._x_to_ms(event.pos().x())
            self.current_position_ms = pos_ms
            self.position_changed.emit(pos_ms)
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_dragging:
            pos_ms = self._x_to_ms(event.pos().x())
            self.current_position_ms = pos_ms
            self.position_changed.emit(pos_ms)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False

    def wheelEvent(self, event):
        # Zoom in / out
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_level = min(10.0, self.zoom_level * 1.2)
        else:
            self.zoom_level = max(1.0, self.zoom_level / 1.2)

        # Keep offset bounded
        if self.zoom_level == 1.0:
            self.offset_x = 0

        self.update()

class MiniatureWaveformWidget(QWidget):
    def __init__(self, cache_path, duration_ms, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(150)
        self.cache_path = cache_path
        self.duration_ms = duration_ms
        self.waveform_data = None
        if os.path.exists(cache_path):
            try:
                self.waveform_data = np.load(cache_path)
            except:
                pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#1a1c23"))

        if self.waveform_data is None:
            return

        w = self.width()
        h = self.height()
        N = len(self.waveform_data)
        if N == 0: return

        samples_per_pixel = max(1, N / w)
        painter.setPen(Qt.PenStyle.NoPen)

        for x in range(w):
            idx = int(x * samples_per_pixel)
            if idx >= N: break

            end_idx = int((x+1) * samples_per_pixel)
            if end_idx > N: end_idx = N

            if end_idx > idx:
                val = np.max(self.waveform_data[idx:end_idx], axis=0)
            else:
                val = self.waveform_data[idx]

            lows, mids, highs = val
            r, g, b = int(lows*255), int(mids*255), int(highs*255)
            if r > 200 and g > 200: b = max(0, b - 50)
            color = QColor(min(255, r), min(255, g), min(255, b))

            amp = max(lows, mids, highs)
            line_h = int(amp * h)
            y1 = (h - line_h) // 2

            painter.fillRect(x, y1, 1, line_h, color)
