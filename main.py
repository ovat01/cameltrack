import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QComboBox, QTableWidget,
                             QTableWidgetItem, QPushButton, QHeaderView,
                             QFileDialog, QProgressBar, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from db import DatabaseManager
from analyzer import AudioAnalyzer
from harmonic import get_compatible_keys
from camelot_widget import CamelotWheelWidget

class AnalysisThread(QThread):
    progress = pyqtSignal(int)
    result = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, files, db, target_lufs):
        super().__init__()
        self.files = files
        self.db = db
        self.analyzer = AudioAnalyzer()
        self.target_lufs = target_lufs

    def run(self):
        total = len(self.files)
        for i, file_path in enumerate(self.files):
            file_hash = self.db.generate_hash(file_path)

            # Incremental check
            existing = self.db.get_track_by_hash(file_hash)
            if existing:
                self.result.emit(existing)
            else:
                data = self.analyzer.analyze(file_path, self.target_lufs)
                if data:
                    data['file_hash'] = file_hash
                    data['file_path'] = file_path
                    data['file_name'] = os.path.basename(file_path)

                    self.db.insert_track(data)
                    self.result.emit(data)

            self.progress.emit(int(((i + 1) / total) * 100))

        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DJ CamelTrack")
        self.setGeometry(100, 100, 1280, 720)

        self.db = DatabaseManager()
        self.target_lufs = -9.0 # Default to Club

        self.init_ui()
        self.load_library()

    def init_ui(self):
        # Dark Theme Palette
        self.setStyleSheet("""
            QMainWindow { background-color: #0f1015; color: #ffffff; }
            QWidget { background-color: #0f1015; color: #ffffff; }
            QLabel { color: #ffffff; }
            QTableWidget { background-color: #1a1c23; color: #ffffff; border: 1px solid #00f0ff; gridline-color: #2a2c33; }
            QTableWidget::item:selected { background-color: #3b2e5a; }
            QHeaderView::section { background-color: #2a2c33; color: #00f0ff; padding: 4px; border: 1px solid #1a1c23; }
            QPushButton { background-color: #7b2cbf; color: white; border-radius: 5px; padding: 5px 15px; font-weight: bold; }
            QPushButton:hover { background-color: #9d4edd; }
            QComboBox { background-color: #2a2c33; color: white; border: 1px solid #00f0ff; border-radius: 3px; padding: 2px; }
            QProgressBar { text-align: center; color: white; background-color: #2a2c33; border: 1px solid #00f0ff; border-radius: 5px; }
            QProgressBar::chunk { background-color: #00f0ff; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Left Panel ---
        left_panel = QVBoxLayout()

        logo_label = QLabel("<b>DJ Harmonic Studio v3.0</b>")
        logo_label.setStyleSheet("color: #00f0ff; font-size: 16px;")
        left_panel.addWidget(logo_label)

        # Settings
        self.loudness_cb = QCheckBox("Igualar Volumen")
        left_panel.addWidget(self.loudness_cb)

        self.club_btn = QPushButton("Club (-9 LUFS)")
        self.club_btn.clicked.connect(lambda: self.set_lufs(-9.0))
        left_panel.addWidget(self.club_btn)

        self.stream_btn = QPushButton("Redes (-14 LUFS)")
        self.stream_btn.clicked.connect(lambda: self.set_lufs(-14.0))
        left_panel.addWidget(self.stream_btn)

        # Camelot Wheel
        self.wheel_widget = CamelotWheelWidget()
        self.wheel_widget.keySelected.connect(self.on_wheel_key_selected)
        left_panel.addWidget(self.wheel_widget)

        left_panel.addStretch()

        # Add files/folders buttons
        add_file_btn = QPushButton("+ ARCHIVO")
        add_file_btn.clicked.connect(self.add_files)
        left_panel.addWidget(add_file_btn)

        main_layout.addLayout(left_panel, 1)

        # --- Right Panel (Main Area) ---
        right_panel = QVBoxLayout()

        # Top bar
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Notación:"))
        self.notation_combo = QComboBox()
        self.notation_combo.addItems(["Camelot", "Musical Key", "Open Key"])
        top_bar.addWidget(self.notation_combo)

        top_bar.addWidget(QLabel("Carpetas:"))
        self.folder_combo = QComboBox()
        self.folder_combo.addItems(["Energía", "Género", "Género > Energía", "Ninguna"])
        top_bar.addWidget(self.folder_combo)
        top_bar.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        top_bar.addWidget(self.progress_bar)

        right_panel.addLayout(top_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "TÍTULO", "ARTISTA", "BPM", "TONO",
            "ENERGÍA", "GÉNERO", "LUFS", "RMS", "PEAK", "RUTA"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.on_table_selection)

        right_panel.addWidget(self.table)

        main_layout.addLayout(right_panel, 4)

    def set_lufs(self, val):
        self.target_lufs = val
        print(f"Target LUFS set to {val}")

    def on_wheel_key_selected(self, key):
        print(f"Wheel selected: {key}")
        comp = get_compatible_keys(key)
        self.wheel_widget.setActiveKeys(comp)

    def on_table_selection(self):
        items = self.table.selectedItems()
        if not items: return
        row = items[0].row()
        key_item = self.table.item(row, 4)
        if key_item:
            key = key_item.text()
            comp = get_compatible_keys(key)
            self.wheel_widget.setActiveKeys(comp)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Audio Files", "", "Audio Files (*.mp3 *.wav *.flac *.aiff)")
        if files:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            self.thread = AnalysisThread(files, self.db, self.target_lufs)
            self.thread.progress.connect(self.progress_bar.setValue)
            self.thread.result.connect(self.add_track_to_table)
            self.thread.finished.connect(self.on_analysis_finished)
            self.thread.start()

    def on_analysis_finished(self):
        self.progress_bar.setVisible(False)

    def load_library(self):
        tracks = self.db.get_all_tracks()
        self.table.setRowCount(0)
        for t in tracks:
            self.add_track_to_table(t)

    def add_track_to_table(self, t):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Color code Camelot key
        key_color = self.wheel_widget.colors.get(t.get('camelot_key', ''), "#ffffff")

        items = [
            str(t.get('id', '')),
            str(t.get('title', '')),
            str(t.get('artist', '')),
            str(t.get('bpm', '')),
            str(t.get('camelot_key', '')),
            str(t.get('energy', '')),
            str(t.get('genre', '')),
            str(t.get('lufs', '')),
            str(t.get('rms', '')),
            str(t.get('peak', '')),
            str(t.get('file_path', ''))
        ]

        for col, text in enumerate(items):
            item = QTableWidgetItem(text)
            # Make not editable
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            # Apply color to key column
            if col == 4:
                item.setBackground(QColor(key_color))
                item.setForeground(QColor("black"))

            self.table.setItem(row, col, item)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
