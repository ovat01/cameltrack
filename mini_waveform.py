import json
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt

def get_mini_waveform_pixmap_from_data(waveform_json, width=100, height=30):
    try:
        if not waveform_json:
            return QPixmap()
        waveform_data = json.loads(waveform_json)
        if not waveform_data:
            return QPixmap()

        img = QImage(width, height, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bins = width
        # Subsample or interpolate waveform_data to match bins
        # For simplicity, if we cached 200 bins and want 100 width:
        ratio = len(waveform_data) / bins

        for x in range(bins):
            idx = int(x * ratio)
            if idx < len(waveform_data):
                data_point = waveform_data[idx]
                if isinstance(data_point, dict) and "amp" in data_point and "rgb" in data_point:
                    val = data_point["amp"]
                    r, g, b = data_point["rgb"]
                    color = QColor(r, g, b)
                else:
                    val = float(data_point)
                    color = QColor("#d4af37") # Legacy fallback
            else:
                val = 0.0
                color = QColor("#d4af37")

            bar_h = max(2, val * height)
            y_pos = (height - bar_h) / 2
            painter.fillRect(int(x), int(y_pos), 1, int(bar_h), color)

        painter.end()
        return QPixmap.fromImage(img)

    except Exception as e:
        print(f"Error generating mini waveform from data: {e}")
    return QPixmap()
