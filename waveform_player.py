import sys
import numpy as np
import librosa
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QApplication, QSlider
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QRect, QThread, QSize
from PyQt6.QtGui import QPainter, QColor
try:
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    HAS_MULTIMEDIA = True
except ImportError:
    HAS_MULTIMEDIA = False

class WaveformLoaderThread(QThread):
    waveform_ready = pyqtSignal(list)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            # Load audio quickly, resample to 22050
            y, sr = librosa.load(self.file_path, sr=22050, mono=True)
            if self._is_cancelled: return

            # Create ~200 bins
            bins = 200
            samples_per_bin = max(1, len(y) // bins)

            S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
            freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)

            low_idx = np.where(freqs < 250)[0]
            mid_idx = np.where((freqs >= 250) & (freqs < 4000))[0]
            high_idx = np.where(freqs >= 4000)[0]

            frames_per_bin = max(1, S.shape[1] // bins)
            waveform_data = []

            for i in range(bins):
                if self._is_cancelled: return
                start_samp = i * samples_per_bin
                end_samp = start_samp + samples_per_bin

                amp = float(np.max(np.abs(y[start_samp:end_samp]))) if len(y[start_samp:end_samp]) > 0 else 0.0

                start_frame = i * frames_per_bin
                end_frame = start_frame + frames_per_bin

                if end_frame <= S.shape[1] and start_frame < S.shape[1]:
                    S_bin = S[:, start_frame:end_frame]
                    low_energy = np.mean(S_bin[low_idx, :])
                    mid_energy = np.mean(S_bin[mid_idx, :])
                    high_energy = np.mean(S_bin[high_idx, :])

                    total = low_energy + mid_energy + high_energy
                    if total > 0:
                        r = int(min(255, (high_energy / total) * 255 * 1.5))
                        g = int(min(255, (mid_energy / total) * 255 * 1.2))
                        b = int(min(255, (low_energy / total) * 255 * 1.2))
                    else:
                        r, g, b = 100, 100, 100
                else:
                    r, g, b = 100, 100, 100

                waveform_data.append({"amp": amp, "rgb": [r, g, b]})

            if self._is_cancelled: return

            # Normalize
            max_val = max([item["amp"] for item in waveform_data]) if waveform_data else 1.0
            if max_val > 0:
                for item in waveform_data:
                    item["amp"] = round(item["amp"] / max_val, 3)

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
        self.zoom_level = 1.0

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        self.zoom_level = min(5.0, self.zoom_level + 0.5)
        self.update()

    def zoom_out(self):
        self.zoom_level = max(1.0, self.zoom_level - 0.5)
        self.update()

    def zoom_fit(self):
        self.zoom_level = 1.0
        self.update()

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

        # Adjust calculations based on zoom level
        virtual_width = width * self.zoom_level
        num_bars = len(self.waveform_data)
        bar_width = virtual_width / num_bars

        # Calculate offset to keep current progress centered if zoomed
        offset_x = 0
        if self.zoom_level > 1.0:
            playhead_x = virtual_width * self.progress
            offset_x = playhead_x - (width / 2)
            offset_x = max(0, min(offset_x, virtual_width - width))

        # Calculate split index based on progress
        split_idx = int(self.progress * num_bars)

        for i, data_point in enumerate(self.waveform_data):
            # Support both new dict RGB format and old float format
            if isinstance(data_point, dict) and "amp" in data_point and "rgb" in data_point:
                val = data_point["amp"]
                r, g, b = data_point["rgb"]
                base_color = QColor(r, g, b)
            else:
                val = float(data_point)
                base_color = QColor(138, 43, 226) if i % 2 == 0 else QColor(0, 191, 255) # Old gradient

            # Scale height
            bar_h = val * (height - 10)
            if bar_h < 2:
                bar_h = 2

            x = (i * bar_width) - offset_x
            if x + bar_width < 0 or x > width:
                continue # Outside visible area

            y = (height - bar_h) / 2

            # Color logic based on playing progress
            if self.bw_mode:
                if i < split_idx:
                    color = QColor(80, 80, 80)
                else:
                    color = QColor(180, 180, 180)
            else:
                if i < split_idx:
                    # Played portion: use RGB base color
                    color = base_color
                else:
                    # Unplayed portion: dim the base color
                    color = QColor(int(base_color.red() * 0.4),
                                   int(base_color.green() * 0.4),
                                   int(base_color.blue() * 0.4))

            painter.fillRect(QRect(int(x), int(y), int(bar_width - 1) or 1, int(bar_h)), color)


class PlayerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Track Info Panel (Left)
        self.info_layout = QVBoxLayout()
        self.art_label = QLabel("[Art]")
        self.art_label.setFixedSize(60, 60)
        self.art_label.setStyleSheet("background-color: #222; border: 1px solid #d4af37;")
        self.art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel("No track selected")
        self.title_label.setStyleSheet("font-weight: bold; color: white;")
        self.artist_label = QLabel("Unknown Artist")
        self.artist_label.setStyleSheet("color: #aaa;")

        self.meta_label = QLabel("Key: -- | Genre: -- | Energy: --")
        self.meta_label.setStyleSheet("color: #d4af37; font-size: 10px;")

        info_text_layout = QVBoxLayout()
        info_text_layout.addWidget(self.title_label)
        info_text_layout.addWidget(self.artist_label)
        info_text_layout.addWidget(self.meta_label)

        track_info_h = QHBoxLayout()
        track_info_h.addWidget(self.art_label)
        track_info_h.addLayout(info_text_layout)

        self.info_layout.addLayout(track_info_h)
        self.layout.addLayout(self.info_layout, 1)

        # Player Controls and Waveform (Center/Right)
        self.player_layout = QVBoxLayout()

        self.waveform = WaveformWidget()
        self.player_layout.addWidget(self.waveform)

        self.controls_layout = QHBoxLayout()

        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setStyleSheet("border-radius: 20px; background-color: #d4af37; color: black; font-weight: bold;")
        self.play_btn.clicked.connect(self.toggle_play)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: white;")

        self.controls_layout.addWidget(self.play_btn)
        self.controls_layout.addWidget(self.time_label)
        self.controls_layout.addStretch()

        self.player_layout.addLayout(self.controls_layout)

        self.layout.addLayout(self.player_layout, 4)

        self.current_duration = 0
        self.loader_thread = None

        if HAS_MULTIMEDIA:
            self.player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.player.setAudioOutput(self.audio_output)
            self.audio_output.setVolume(0.7)

            self.player.positionChanged.connect(self.on_position_changed)
            self.player.durationChanged.connect(self.on_duration_changed)
            self.player.playbackStateChanged.connect(self.on_state_changed)
            self.waveform.seek_requested.connect(self.seek_audio)
        else:
            self.player = None
            self.audio_output = None
            self.play_btn.setEnabled(False)
            self.play_btn.setToolTip("PyQt6-Multimedia not installed. Playback disabled.")


    def seek_audio(self, progress):
        if self.current_duration > 0:
            new_position = int(progress * self.current_duration)
            self.player.setPosition(new_position)

    def load_track(self, file_path, title="Unknown", artist="Unknown", key="--", genre="--", energy="--", cover_pixmap=None, waveform_data="[]"):

        self.title_label.setText(title)
        self.artist_label.setText(artist)
        self.meta_label.setText(f"Key: {key} | Genre: {genre} | Energy: {energy}")

        if hasattr(self, 'art_label'):
            if cover_pixmap and not cover_pixmap.isNull():
                self.art_label.setPixmap(cover_pixmap)
            else:
                self.art_label.clear()
                self.art_label.setText("No Art")

        if HAS_MULTIMEDIA and self.player:
            self.player.stop()
            self.player.setSource(QUrl.fromLocalFile(file_path))

        self.waveform.clear_waveform()
        self.waveform.set_progress(0)
        self.time_label.setText("00:00 / 00:00")

        # Load real waveform in background thread to not block GUI
        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.cancel()
            self.loader_thread.wait() # Safely wait for thread to finish

        self.loader_thread = WaveformLoaderThread(file_path)
        self.loader_thread.waveform_ready.connect(self.waveform.set_waveform_data)
        self.loader_thread.start()

    def toggle_play(self):
        if HAS_MULTIMEDIA and self.player:
            if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.player.pause()
            else:
                self.player.play()

    def on_state_changed(self, state):
        if HAS_MULTIMEDIA:
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
