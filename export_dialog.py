from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QCheckBox, QFrame, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class ExportDialog(QDialog):
    def __init__(self, track_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CONFIRMAR EXPORTACIÓN")
        self.setFixedSize(450, 500)

        # Dark Theme Palette to match main window
        self.setStyleSheet("""
            QDialog { background-color: #0f1015; color: #ffffff; }
            QLabel { color: #ffffff; }
            QPushButton { border-radius: 5px; padding: 10px; font-weight: bold; }
            QPushButton#btn_cancel { background-color: #3b2e5a; color: #ff6b6b; }
            QPushButton#btn_cancel:hover { background-color: #4a3b70; }
            QPushButton#btn_export { background-color: #20c997; color: white; }
            QPushButton#btn_export:hover { background-color: #28a745; }
            QFrame#summary_frame { background-color: #1a1c23; border-radius: 5px; }
            QRadioButton { color: #a998f5; font-weight: bold; }
            QRadioButton::indicator { width: 15px; height: 15px; border-radius: 2px; border: 1px solid #a998f5; background-color: #1a1c23; }
            QRadioButton::indicator:checked { background-color: #20c997; border: 1px solid #20c997; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QLabel("RESUMEN DE EXPORTACIÓN")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(header)

        # Summary Frame
        summary_frame = QFrame()
        summary_frame.setObjectName("summary_frame")
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setSpacing(10)

        lbl_tracks = QLabel(f"• {track_count} Tracks")
        lbl_tracks.setStyleSheet("color: #a998f5;")

        lbl_format = QLabel("• Formato: <span style='color:#a998f5;'>[Key]</span> Artist - Title")
        lbl_folders = QLabel("• Carpetas: Energía")

        chk_detected = QCheckBox("Tonalidades Detectadas")
        chk_detected.setChecked(True)
        chk_detected.setStyleSheet("color: #20c997;")
        chk_detected.setEnabled(False) # Just visual for now

        summary_layout.addWidget(lbl_tracks)
        summary_layout.addWidget(lbl_format)
        summary_layout.addWidget(lbl_folders)

        chk_layout = QHBoxLayout()
        lbl_dot = QLabel("•")
        lbl_dot.setStyleSheet("color: #20c997;")
        chk_layout.addWidget(lbl_dot)
        chk_layout.addWidget(chk_detected)
        chk_layout.addStretch()
        summary_layout.addLayout(chk_layout)

        layout.addWidget(summary_frame)

        # Mode Section
        mode_header = QLabel("MODO DE EXPORTACIÓN")
        mode_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mode_header.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        mode_header.setStyleSheet("color: #7b8396; margin-top: 10px;")
        layout.addWidget(mode_header)

        self.radio_group = QButtonGroup(self)

        # Rename original
        self.rb_rename = QRadioButton("Renombrar originales")
        self.rb_rename.setChecked(True)
        lbl_rename_desc = QLabel("Los archivos serán renombrados.\nNo se crean duplicados.")
        lbl_rename_desc.setStyleSheet("color: #7b8396; margin-left: 25px;")

        self.radio_group.addButton(self.rb_rename, 1)

        layout.addWidget(self.rb_rename)
        layout.addWidget(lbl_rename_desc)

        # Copy original
        self.rb_copy = QRadioButton("Hacer copias renombradas")
        lbl_copy_desc = QLabel("Se mantienen los originales.\n⚠️ Ocupa el doble de espacio.")
        lbl_copy_desc.setStyleSheet("color: #7b8396; margin-left: 25px;")

        self.radio_group.addButton(self.rb_copy, 2)

        layout.addWidget(self.rb_copy)
        layout.addWidget(lbl_copy_desc)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)

        self.btn_cancel = QPushButton("CANCELAR")
        self.btn_cancel.setObjectName("btn_cancel")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_export = QPushButton("EXPORTAR")
        self.btn_export.setObjectName("btn_export")
        self.btn_export.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_export)

        layout.addLayout(btn_layout)

    def get_export_mode(self):
        # 1 for rename, 2 for copy
        return self.radio_group.checkedId()
