import sqlite3
import os
import hashlib
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="cameltrack.db"):
        import os
        import sys

        # Store in AppData for Windows
        if sys.platform == 'win32':
            app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
            base_dir = os.path.join(app_data, 'DJ_CamelTrack')
        else:
            base_dir = os.path.join(os.path.expanduser('~'), '.dj_cameltrack')

        os.makedirs(base_dir, exist_ok=True)
        self.db_path = os.path.join(base_dir, db_name)
        self.init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_hash TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    artist TEXT,
                    title TEXT,
                    bpm REAL,
                    musical_key TEXT,
                    camelot_key TEXT,
                    open_key TEXT,
                    major_minor TEXT,
                    genre TEXT,
                    energy REAL,
                    duration REAL,
                    lufs REAL,
                    rms REAL,
                    peak REAL,
                    dynamic_range REAL,
                    confidence REAL,
                    last_scanned TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def generate_hash(self, file_path):
        # Generates a simple hash based on file modification time and path for fast incremental checking
        try:
            mtime = os.path.getmtime(file_path)
            size = os.path.getsize(file_path)
            hash_str = f"{file_path}_{mtime}_{size}"
            return hashlib.md5(hash_str.encode()).hexdigest()
        except FileNotFoundError:
            return None

    def insert_track(self, track_data):
        # track_data is a dictionary
        conn = self._get_conn()
        try:
            cursor = conn.cursor()

            columns = ', '.join(track_data.keys())
            placeholders = ', '.join(['?' for _ in track_data])

            sql = f'''
                INSERT INTO tracks ({columns}, last_scanned)
                VALUES ({placeholders}, ?)
                ON CONFLICT(file_hash) DO UPDATE SET
                    file_path=excluded.file_path,
                    file_name=excluded.file_name,
                    artist=excluded.artist,
                    title=excluded.title,
                    bpm=excluded.bpm,
                    musical_key=excluded.musical_key,
                    camelot_key=excluded.camelot_key,
                    open_key=excluded.open_key,
                    major_minor=excluded.major_minor,
                    genre=excluded.genre,
                    energy=excluded.energy,
                    duration=excluded.duration,
                    lufs=excluded.lufs,
                    rms=excluded.rms,
                    peak=excluded.peak,
                    dynamic_range=excluded.dynamic_range,
                    confidence=excluded.confidence,
                    last_scanned=excluded.last_scanned
            '''

            values = list(track_data.values())
            values.append(datetime.now())

            cursor.execute(sql, values)
            conn.commit()
        finally:
            conn.close()

    def get_track_by_hash(self, file_hash):
        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tracks WHERE file_hash = ?", (file_hash,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def clear_all(self):
        conn = self._get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tracks')
            conn.commit()
        finally:
            conn.close()

    def get_all_tracks(self):
        conn = self._get_conn()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tracks")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
