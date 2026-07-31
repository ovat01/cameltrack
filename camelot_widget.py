from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QPointF
import math

class CamelotWheelWidget(QWidget):
    keySelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self.active_keys = []

        # Camelot Colors based on the image roughly
        self.colors = {
            "1A": "#87d6cf", "1B": "#b7f2e4",
            "2A": "#62c4b5", "2B": "#8cdcd0",
            "3A": "#72e5a4", "3B": "#9af5c4",
            "4A": "#a4e287", "4B": "#c6f2ad",
            "5A": "#dfda6b", "5B": "#ede896",
            "6A": "#e5b66d", "6B": "#f5d19a",
            "7A": "#eb8b6a", "7B": "#f5af95",
            "8A": "#ed6b87", "8B": "#f59aa5",
            "9A": "#e278b8", "9B": "#f2a8d3",
            "10A": "#bc72d1", "10B": "#d49eeb",
            "11A": "#8d7ae6", "11B": "#a998f5",
            "12A": "#6195e3", "12B": "#8cbaef",
        }

    def setActiveKeys(self, keys):
        self.active_keys = keys
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Simple hit detection could be done with polar coordinates
            w = self.width()
            h = self.height()
            center_x = w / 2
            center_y = h / 2

            dx = event.pos().x() - center_x
            dy = event.pos().y() - center_y

            dist = math.sqrt(dx**2 + dy**2)
            angle = math.degrees(math.atan2(dy, dx))
            # Adjust angle so top is 12
            angle = (angle + 90) % 360

            # Divide into 12 segments
            segment = int(((angle + 15) % 360) / 30)
            number = (segment + 1) if (segment + 1) <= 12 else 1

            # Assuming outer ring is Minor (A), inner is Major (B) or vice versa depending on mapping
            # Let's say outer is A, inner is B
            outer_radius = min(w, h) / 2 * 0.9
            inner_radius = min(w, h) / 2 * 0.5
            core_radius = min(w, h) / 2 * 0.2

            if core_radius < dist <= inner_radius:
                self.keySelected.emit(f"{number}B")
            elif inner_radius < dist <= outer_radius:
                self.keySelected.emit(f"{number}A")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        center_x = w / 2
        center_y = h / 2
        radius = min(w, h) / 2 * 0.9

        # Outer Ring (Minor A)
        for i in range(12):
            number = (i + 1)
            key = f"{number}A"
            angle = i * 30 - 15 - 90

            rect = QRectF(center_x - radius, center_y - radius, radius*2, radius*2)

            if key in self.active_keys:
                color = QColor(self.colors.get(key, "#555555")).lighter(120)
            else:
                color = QColor(self.colors.get(key, "#333333"))

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))

            # QPainter.drawPie takes angles in 1/16ths of a degree
            painter.drawPie(rect, int(-angle * 16), int(-30 * 16))

        # Inner Ring (Major B)
        inner_radius = radius * 0.6
        for i in range(12):
            number = (i + 1)
            key = f"{number}B"
            angle = i * 30 - 15 - 90

            rect = QRectF(center_x - inner_radius, center_y - inner_radius, inner_radius*2, inner_radius*2)

            if key in self.active_keys:
                color = QColor(self.colors.get(key, "#555555")).lighter(120)
            else:
                color = QColor(self.colors.get(key, "#444444"))

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.drawPie(rect, int(-angle * 16), int(-30 * 16))

        # Center Hole
        core_radius = inner_radius * 0.4
        rect = QRectF(center_x - core_radius, center_y - core_radius, core_radius*2, core_radius*2)
        painter.setBrush(QBrush(QColor("#1e1e1e"))) # Dark background matching UI
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawEllipse(rect)

        # Draw Text overlays
        painter.setPen(QPen(Qt.GlobalColor.black))
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)

        for i in range(12):
            number = i + 1
            # Text position calc
            angle_rad = math.radians(i * 30 - 90)

            # Outer text
            out_r = radius * 0.8
            tx = center_x + out_r * math.cos(angle_rad)
            ty = center_y + out_r * math.sin(angle_rad)
            painter.drawText(QRectF(tx-15, ty-10, 30, 20), Qt.AlignmentFlag.AlignCenter, f"{number}A")

            # Inner text
            in_r = inner_radius * 0.7
            tx = center_x + in_r * math.cos(angle_rad)
            ty = center_y + in_r * math.sin(angle_rad)
            painter.drawText(QRectF(tx-15, ty-10, 30, 20), Qt.AlignmentFlag.AlignCenter, f"{number}B")
