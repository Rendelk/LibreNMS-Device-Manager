import sqlite3
from pathlib import Path
from datetime import datetime


DB_DIR = Path("data")
DB_FILE = DB_DIR / "history.db"


class HistoryDatabase:
    def __init__(self):
        DB_DIR.mkdir(exist_ok=True)
        self.init_db()

    def init_db(self):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT NOT NULL,
                    username TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    device_ip TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    exit_code INTEGER,
                    stdout TEXT,
                    stderr TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id)
                )
            """)

    def create_session(self, action: str, target: str, username: str = "") -> int:
        created_at = datetime.now().strftime("%H:%M:%S %d:%m:%Y")
        title = f"Проведено дію в {created_at}"

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute(
                """
                INSERT INTO sessions (title, action, target, username, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, action, target, username, created_at),
            )
            return cursor.lastrowid

    def add_item(self, session_id, device_ip, status, message, exit_code=None, stdout="", stderr=""):
        created_at = datetime.now().strftime("%H:%M:%S %d:%m:%Y")

        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                """
                INSERT INTO session_items (
                    session_id, device_ip, status, message,
                    exit_code, stdout, stderr, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, device_ip, status, message, exit_code, stdout, stderr, created_at),
            )