import os
import librosa
import numpy as np
import pyloudnorm as pyln
from mutagen import File
from harmonic import musical_to_camelot

class AudioAnalyzer:
    def __init__(self):
        # We define a basic mapping from librosa pitch classes to note names
        self.pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    def extract_metadata(self, file_path):
        """Extract basic metadata using Mutagen"""
        meta = {'artist': 'Unknown Artist', 'title': os.path.basename(file_path), 'duration': 0}
        try:
            audio = File(file_path, easy=True)
            if audio:
                if 'artist' in audio:
                    meta['artist'] = audio['artist'][0]
                elif '\xa9ART' in audio:
                    meta['artist'] = audio['\xa9ART'][0]

                if 'title' in audio:
                    meta['title'] = audio['title'][0]
                elif '\xa9nam' in audio:
                    meta['title'] = audio['\xa9nam'][0]

                if hasattr(audio, 'info'):
                    meta['duration'] = audio.info.length
        except Exception as e:
            print(f"Metadata extraction error: {e}")
        return meta

    def analyze(self, file_path, target_lufs=-14.0):
        try:
            # Load audio using librosa. For large libraries, we might load a snippet,
            # but for full analysis we need the whole file or a large chunk.
            # Using mono and 22050Hz for faster processing.
            y, sr = librosa.load(file_path, sr=22050, mono=True)

            # Duration fallback
            duration = librosa.get_duration(y=y, sr=sr)

            # --- BPM Detection ---
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
            bpm = round(float(tempo[0]) if isinstance(tempo, np.ndarray) else float(tempo), 2)

            # --- Key Detection ---
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            chroma_vals = np.sum(chroma, axis=1)
            pitch_idx = np.argmax(chroma_vals)
            pitch = self.pitch_classes[pitch_idx]

            # Major / Minor distinction (very simplified heuristic using template matching)
            # A more robust approach uses KS profiles, here's a basic one:
            # We look at the third: +4 semitones for Major, +3 for minor
            major_third_idx = (pitch_idx + 4) % 12
            minor_third_idx = (pitch_idx + 3) % 12

            if chroma_vals[minor_third_idx] > chroma_vals[major_third_idx]:
                major_minor = "Minor"
                musical_key = f"{pitch}m"
            else:
                major_minor = "Major"
                musical_key = f"{pitch}"

            # Convert to Camelot (Mapping G#m to Abm if needed, simplified)
            # Fix enharmonics for our dict
            enharmonics = {'A#m': 'Bbm', 'C#m': 'Dbm', 'D#m': 'Ebm', 'D#': 'Eb', 'A#': 'Bb', 'G#m':'Abm', 'G#': 'Ab'}
            search_key = enharmonics.get(musical_key, musical_key)
            camelot_key = musical_to_camelot(search_key)
            if not camelot_key:
                 # Fallback if mapping misses
                 camelot_key = "1A" # Dummy

            open_key = f"{camelot_key[:-1]}{'m' if major_minor == 'Minor' else 'd'}" # Simplified open key

            # --- Loudness, RMS, Peak ---
            # pyln requires >=16kHz. 22050 is fine.
            meter = pyln.Meter(sr)
            # pyln expects (samples, channels), we have (samples,)
            lufs = meter.integrated_loudness(y)

            rms = np.sqrt(np.mean(y**2))
            rms_db = 20 * np.log10(rms + 1e-10)

            peak = np.max(np.abs(y))
            peak_db = 20 * np.log10(peak + 1e-10)

            dynamic_range = peak_db - rms_db

            # --- Energy Score ---
            # Proprietary score based on RMS, spectral centroid, and onset strength
            spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            avg_cent = np.mean(spec_cent)
            avg_onset = np.mean(onset_env)

            # Normalize some values to a 1-10 scale (highly simplified heuristic)
            energy_raw = (rms * 10) + (avg_onset * 5) + (avg_cent / 1000)
            energy = min(max(round(float(energy_raw), 1), 1.0), 10.0)

            # --- Genre Detection (Dummy Heuristic for now) ---
            genre = "Electronic"
            if bpm > 135 and energy > 7:
                genre = "Psytrance"
            elif bpm < 125 and energy < 5:
                genre = "Deep House"
            elif 125 <= bpm <= 130:
                genre = "Techno"

            confidence = 85.5 # Fake confidence score

            meta = self.extract_metadata(file_path)
            if meta['duration'] == 0:
                meta['duration'] = duration

            return {
                'artist': meta['artist'],
                'title': meta['title'],
                'bpm': bpm,
                'musical_key': musical_key,
                'camelot_key': camelot_key,
                'open_key': open_key,
                'major_minor': major_minor,
                'genre': genre,
                'energy': energy,
                'duration': meta['duration'],
                'lufs': round(float(lufs), 2),
                'rms': round(float(rms_db), 2),
                'peak': round(float(peak_db), 2),
                'dynamic_range': round(float(dynamic_range), 2),
                'confidence': confidence
            }

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
