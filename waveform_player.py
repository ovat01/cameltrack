import sys
import numpy as np
import librosa
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QRect, QThread
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class WaveformLoaderThread(QThread):
    waveform_ready = pyqtSignal(list)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            # Load audio quickly, resample to 22050
            y, sr = librosa.load(self.file_path, sr=22050, mono=True)
            # Create ~200 bins
            bins = 200
            samples_per_bin = len(y) // bins

            waveform_data = []
            for i in range(bins):
                start = i * samples_per_bin
                end = start + samples_per_bin
                # Extract max absolute amplitude in the bin
                if len(y[start:end]) > 0:
                    val = np.max(np.abs(y[start:end]))
                    waveform_data.append(float(val))
                else:
                    waveform_data.append(0.0)

            # Normalize
            max_val = max(waveform_data) if waveform_data else 1.0
            if max_val > 0:
                waveform_data = [v / max_val for v in waveform_data]

            self.waveform_ready.emit(waveform_data)
        except Exception as e:
            print(f"Error loading waveform: {e}")
            self.waveform_ready.emit([])


class WaveformWidget(QWidget):
    seek_requested = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self.progress = 0.0
        self.is_playing = False
        self.waveform_data = []
        self.bw_mode = False

    def set_bw_mode(self, enabled):
        self.bw_mode = enabled
        self.update()

    def set_waveform_data(self, data):
        self.waveform_data = data
        self.update()

    def clear_waveform(self):
        self.waveform_data = []
        self.update()

    def set_progress(self, progress):
        self.progress = max(0.0, min(1.0, progress))
        self.update()


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._handle_mouse(event.position().x())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._handle_mouse(event.position().x())

    def _handle_mouse(self, x_pos):
        if self.width() > 0:
            progress = x_pos / self.width()
            progress = max(0.0, min(1.0, progress))
            self.seek_requested.emit(progress)

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        width = rect.width()
        height = rect.height()

        # Draw background

        if self.bw_mode:
            painter.fillRect(rect, QColor("#ffffff"))
        else:
            painter.fillRect(rect, QColor("#1e1e2e"))


        if not self.waveform_data:
            return

        num_bars = len(self.waveform_data)
        bar_width = width / num_bars

        # Calculate split index based on progress
        split_idx = int(self.progress * num_bars)

        for i, val in enumerate(self.waveform_data):
            # Scale height
            bar_h = val * (height - 10)
            if bar_h < 2:
                bar_h = 2

            x = i * bar_width
            y = (height - bar_h) / 2

            # Color logic based on playing progress
            if self.bw_mode:
                if i < split_idx:
                    color = QColor(80, 80, 80)
                else:
                    color = QColor(180, 180, 180)
            else:
                if i < split_idx:
                    # Played portion: gradient feel
                    color = QColor(138, 43, 226) if i % 2 == 0 else QColor(0, 191, 255)
                else:
                    # Unplayed portion
                    color = QColor(100, 100, 120)

            painter.fillRect(QRect(int(x), int(y), int(bar_width - 1) or 1, int(bar_h)), color)


class PlayerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.waveform = WaveformWidget()
        self.layout.addWidget(self.waveform)

        self.controls_layout = QHBoxLayout()

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setStyleSheet("border-radius: 20px; background-color: #3b82f6; color: white; font-weight: bold;")
        self.play_btn.clicked.connect(self.toggle_play)

        self.time_label = QLabel("00:00 / 00:00")

        self.controls_layout.addWidget(self.play_btn)
        self.controls_layout.addWidget(self.time_label)
        self.controls_layout.addStretch()

        self.layout.addLayout(self.controls_layout)

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.7)

        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.playbackStateChanged.connect(self.on_state_changed)
        self.waveform.seek_requested.connect(self.seek_audio)

        self.current_duration = 0
        self.loader_thread = None


    def seek_audio(self, progress):
        if self.current_duration > 0:
            new_position = int(progress * self.current_duration)
            self.player.setPosition(new_position)

    def load_track(self, file_path):

        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(file_path))

        self.waveform.clear_waveform()
        self.waveform.set_progress(0)
        self.time_label.setText("00:00 / 00:00")

        # Load real waveform in background thread to not block GUI
        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.terminate()

        self.loader_thread = WaveformLoaderThread(file_path)
        self.loader_thread.waveform_ready.connect(self.waveform.set_waveform_data)
        self.loader_thread.start()

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def on_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setText("⏸")
        else:
            self.play_btn.setText("▶")

    def on_position_changed(self, position):
        if self.current_duration > 0:
            progress = position / self.current_duration
            self.waveform.set_progress(progress)

            # Update time label
            pos_sec = position // 1000
            dur_sec = self.current_duration // 1000

            p_m, p_s = divmod(pos_sec, 60)
            d_m, d_s = divmod(dur_sec, 60)

            self.time_label.setText(f"{p_m:02d}:{p_s:02d} / {d_m:02d}:{d_s:02d}")

    def on_duration_changed(self, duration):
        self.current_duration = duration
