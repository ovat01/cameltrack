import sys
from waveform_player import PlayerWidget
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QComboBox, QTableWidget,
                             QTableWidgetItem, QPushButton, QHeaderView,
                             QFileDialog, QProgressBar, QCheckBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont

import shutil
from db import DatabaseManager
from analyzer import AudioAnalyzer
from harmonic import get_compatible_keys
from camelot_widget import CamelotWheelWidget
from export_dialog import ExportDialog

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
        self.setWindowTitle("CamelTrack")
        self.setGeometry(100, 100, 1280, 720)

        self.db = DatabaseManager()
        self.target_lufs = -9.0 # Default to Club

        self.init_ui()
        self.load_library()

    def init_ui(self):
        # Dark Theme Palette
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; color: #ffffff; }
            QWidget { background-color: #121212; color: #ffffff; }
            QLabel { color: #ffffff; }
            QTableWidget { background-color: #1e1e1e; color: #ffffff; border: 1px solid #d4af37; gridline-color: #333333; }
            QTableWidget::item:selected { background-color: #4a3d13; }
            QHeaderView::section { background-color: #252525; color: #d4af37; padding: 4px; border: 1px solid #1e1e1e; }
            QPushButton { background-color: #d4af37; color: black; border-radius: 5px; padding: 5px 15px; font-weight: bold; }
            QPushButton:hover { background-color: #f1c40f; }
            QComboBox { background-color: #252525; color: white; border: 1px solid #d4af37; border-radius: 3px; padding: 2px; }
            QProgressBar { text-align: center; color: white; background-color: #252525; border: 1px solid #d4af37; border-radius: 5px; }
            QProgressBar::chunk { background-color: #d4af37; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # Main layout is vertical now to hold split view on top and dock on bottom
        main_layout_v = QVBoxLayout(central_widget)
        main_layout_v.setContentsMargins(0, 0, 0, 0)
        main_layout_v.setSpacing(0)

        top_split_widget = QWidget()
        main_layout = QHBoxLayout(top_split_widget)

        # --- Left Panel ---
        left_panel = QVBoxLayout()

        logo_label = QLabel("<b>CamelTrack</b>")
        logo_label.setStyleSheet("color: #d4af37; font-size: 16px;")
        left_panel.addWidget(logo_label)

        # Camelot Wheel
        self.wheel_widget = CamelotWheelWidget()
        self.wheel_widget.keySelected.connect(self.on_wheel_key_selected)
        left_panel.addWidget(self.wheel_widget)

        left_panel.addStretch()

        # Add files/folders buttons
        btn_layout = QHBoxLayout()
        add_file_btn = QPushButton("+ ARCHIVO")
        add_file_btn.clicked.connect(self.add_files)
        btn_layout.addWidget(add_file_btn)

        self.clear_btn = QPushButton("LIMPIAR")
        self.clear_btn.setStyleSheet("background-color: #e63946; color: white;")
        self.clear_btn.clicked.connect(self.clear_library)
        btn_layout.addWidget(self.clear_btn)

        left_panel.addLayout(btn_layout)

        main_layout.addLayout(left_panel, 1)

        # --- Right Panel (Main Area) ---
        right_panel = QVBoxLayout()

        # Top bar
        top_bar = QHBoxLayout()

        top_bar.addWidget(QLabel("Ordenar por:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["", "Camelot", "Energía", "Género"])
        self.sort_combo.currentTextChanged.connect(self.on_sort_changed)
        top_bar.addWidget(self.sort_combo)
        top_bar.addStretch()

        from PyQt6.QtWidgets import QCheckBox
        self.bw_theme_cb = QCheckBox("B&W Theme")
        self.bw_theme_cb.stateChanged.connect(self.toggle_bw_theme)
        top_bar.addWidget(self.bw_theme_cb)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        top_bar.addWidget(self.progress_bar)

        right_panel.addLayout(top_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["WAVE", "ID", "TÍTULO", "BPM", "TONO", "ENERGÍA", "GÉNERO"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_table_selection)

        self.table.hideColumn(1) # Hide ID

        right_panel.addWidget(self.table)

        # Export Button Row
        export_row = QHBoxLayout()
        export_row.addStretch()

        self.export_btn = QPushButton("EXPORTAR")
        self.export_btn.setStyleSheet("background-color: #20c997; color: white; padding: 8px 25px; border-radius: 5px;")
        self.export_btn.clicked.connect(self.export_files)
        export_row.addWidget(self.export_btn)

        right_panel.addLayout(export_row)

        main_layout.addLayout(right_panel, 4)
        main_layout_v.addWidget(top_split_widget, 1)

        # --- Bottom Panel (Player) ---
        bottom_panel = QWidget()
        bottom_panel.setStyleSheet("background-color: #1a1a1a; border-top: 1px solid #d4af37;")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(10, 10, 10, 10)

        self.player_widget = PlayerWidget()
        bottom_layout.addWidget(self.player_widget)

        main_layout_v.addWidget(bottom_panel, 0)


    def toggle_bw_theme(self, state):
        from PyQt6.QtCore import Qt
        if state == Qt.CheckState.Checked.value:
            # Apply grayscale/B&W stylesheet
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #f0f0f0; color: #000000; }
                QTableWidget { background-color: #ffffff; color: #000000; gridline-color: #cccccc; }
                QHeaderView::section { background-color: #e0e0e0; color: #000000; border: 1px solid #cccccc; }
                QPushButton { background-color: #e0e0e0; color: #000000; border: 1px solid #aaaaaa; }
                QProgressBar { background-color: #e0e0e0; color: #000000; text-align: center; }
                QProgressBar::chunk { background-color: #888888; }
            """)
            self.player_widget.waveform.set_bw_mode(True)
        else:
            # Restore dark theme
            self.setStyleSheet("") # Clear to fallback or re-apply original
            self.player_widget.waveform.set_bw_mode(False)

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

        # Load track into player
        path_item = self.table.item(row, 0)
        title_item = self.table.item(row, 3)
        artist_item = self.table.item(row, 4)
        key_item = self.table.item(row, 6)
        energy_item = self.table.item(row, 7)
        genre_item = self.table.item(row, 8)

        if path_item:
            file_path = path_item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                title = title_item.text() if title_item else "Unknown"
                artist = artist_item.text() if artist_item else "Unknown"
                key = key_item.text() if key_item else "--"
                energy = energy_item.text() if energy_item else "--"
                genre = genre_item.text() if genre_item else "--"
                self.player_widget.load_track(file_path, title, artist, key, genre, energy)

        # Highlight Camelot
        key_item = self.table.item(row, 6)
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


    def clear_library(self):
        self.table.setRowCount(0)
        self.db.clear_all_tracks()
        self.wheel_widget.setActiveKeys([])

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

        # Energy stars calculation
        raw_energy = float(t.get('energy', 1.0))
        # Map 1-10 to 1-5 stars
        stars_count = int(round(raw_energy / 2))
        stars_count = max(1, min(5, stars_count))
        stars_str = "★" * stars_count

        bpm_val = t.get("bpm", 0.0)
        try:
            bpm_str = str(int(round(float(bpm_val))))
        except (ValueError, TypeError):
            bpm_str = "0"

        items = [
            "", # WAVE
            str(t.get("id", "")),
            str(t.get("title", "")),
            bpm_str,
            str(t.get("camelot_key", "")),
            stars_str,
            str(t.get("genre", ""))
        ]

        for col, text in enumerate(items):
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

            if col == 6: # Tono
                item.setBackground(QColor(key_color))
                item.setForeground(QColor("black"))
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            elif col == 7: # Energy stars
                item.setForeground(QColor("#f1c40f")) # Gold color for stars

            self.table.setItem(row, col, item)
            if col == 0:
                item.setData(Qt.ItemDataRole.UserRole, str(t.get("file_path", "")))


    def on_sort_changed(self, text):
        if text == "Camelot":
            self.smart_camelot_sort()
        elif text == "Energía":
            self.table.sortItems(5, Qt.SortOrder.DescendingOrder)
        elif text == "Género":
            self.table.sortItems(6, Qt.SortOrder.AscendingOrder)

    def smart_camelot_sort(self):
        # A smart DJ ordering algorithm
        # We want to traverse tracks such that the next track is harmonically compatible (e.g. +1/-1 or same key)
        track_count = self.table.rowCount()
        if track_count == 0:
            return

        # Extract rows
        rows = []
        for r in range(track_count):
            row_data = []
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                row_data.append((item.text(), item.data(Qt.ItemDataRole.UserRole), item.background(), item.foreground(), item.font(), item.textAlignment()))
            rows.append(row_data)

        # Sort logic: start with 1A, then 1B, 2B, 2A, 3A, 3B, 4B... traversing the wheel optimally.
        # For simplicity, we can do a mapped numeric sort to order them by DJ Camelot proximity
        def camelot_score(key_str):
            if not key_str or len(key_str) < 2: return 0
            val = int(key_str[:-1])
            letter = key_str[-1].upper()
            # Interleave A and B: 1A=1, 1B=2, 2B=3, 2A=4, 3A=5, 3B=6... to create a harmonic path
            # We can give a smooth path mapping:
            # Let's just group them logically:
            return val * 10 + (1 if letter == 'A' else 2)

        rows.sort(key=lambda x: camelot_score(x[4][0]))

        self.table.setRowCount(0)
        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, d in enumerate(row_data):
                text, user_data, bg, fg, font, align = d
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(align)
                if bg: item.setBackground(bg)
                if fg: item.setForeground(fg)
                if font: item.setFont(font)
                item.setData(Qt.ItemDataRole.UserRole, user_data)
                self.table.setItem(row, col, item)


    def export_files(self):
        track_count = self.table.rowCount()
        if track_count == 0:
            return

        dialog = ExportDialog(track_count, self)
        if dialog.exec():
            mode = dialog.get_export_mode()

            # Fetch all tracks from table data
            for row in range(track_count):
                title_item = self.table.item(row, 3)
                artist_item = self.table.item(row, 4)
                bpm_item = self.table.item(row, 5)
                key_item = self.table.item(row, 6)
                path_item = self.table.item(row, 0)

                if not (title_item and bpm_item and key_item and path_item):
                    continue

                title = title_item.text()
                artist = artist_item.text() if artist_item else "Unknown"
                if not artist:
                    artist = "Unknown"
                key = key_item.text()
                bpm = bpm_item.text()
                old_path = path_item.data(Qt.ItemDataRole.UserRole) if path_item else ""

                if not os.path.exists(old_path):
                    continue

                dir_name = os.path.dirname(old_path)
                ext = os.path.splitext(old_path)[1]

                # Format: [Key] Artist - Title
                # Handle cases where artist or title might be missing
                display_artist = artist if artist and artist != "Unknown Artist" else "Unknown"
                display_title = title if title else "Track"

                # Sanitize filenames
                safe_artist = "".join(c for c in display_artist if c.isalnum() or c in " -_").strip()
                safe_title = "".join(c for c in display_title if c.isalnum() or c in " -_").strip()

                new_filename = f"[{key}] {safe_artist} - {safe_title}{ext}"
                new_path = os.path.join(dir_name, new_filename)

                if old_path == new_path:
                    continue # Already correctly named

                try:
                    if mode == 1: # Rename
                        os.rename(old_path, new_path)
                        # Update table with new path (in a real app we'd update DB too)
                        path_item.setData(Qt.ItemDataRole.UserRole, new_path)
                    elif mode == 2: # Copy
                        shutil.copy2(old_path, new_path)
                except Exception as e:
                    print(f"Error exporting file {old_path}: {e}")

            # In a full implementation, we'd trigger a UI refresh or toast notification here.
            print("Export complete.")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
