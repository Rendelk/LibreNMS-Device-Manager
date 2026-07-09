from pathlib import Path
from datetime import datetime


REPORT_DIR = Path("reports")
REPORT_FILE = REPORT_DIR / "mikrotik_actions.txt"


class ReportWriter:
    def __init__(self):
        REPORT_DIR.mkdir(exist_ok=True)

    def start_session(self, action: str, username: str):
        now = datetime.now().strftime("%H:%M:%S %d:%m:%Y")

        with open(REPORT_FILE, "a", encoding="utf-8") as file:
            file.write("\n")
            file.write(f"Проведено дію в {now}\n")
            file.write(f"Дія: {action}\n")
            file.write(f"Користувач: {username}\n")
            file.write("\n")

    def add_line(self, text: str):
        with open(REPORT_FILE, "a", encoding="utf-8") as file:
            file.write(text + "\n")

    def end_session(self):
        with open(REPORT_FILE, "a", encoding="utf-8") as file:
            file.write("-" * 50 + "\n")