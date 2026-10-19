import json
import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from .models import DirectorProgram


class ProgramRepository:
    def __init__(self, path: str = "football_director.db"):
        self.path = path
        self._lock = threading.Lock()
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS programs (
                id TEXT PRIMARY KEY, version INTEGER NOT NULL, status TEXT NOT NULL,
                original_instruction TEXT NOT NULL, program_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")

    def create(self, instruction: str, program: DirectorProgram) -> Dict:
        record_id = f"prog_{uuid4().hex[:12]}"
        with self._lock, self._connect() as db:
            db.execute(
                "INSERT INTO programs (id,version,status,original_instruction,program_json) VALUES (?,?,?,?,?)",
                (record_id, 1, "active", instruction, program.model_dump_json()),
            )
        return self.get(record_id)

    def list(self) -> List[Dict]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM programs ORDER BY created_at DESC").fetchall()
        return [self._row(row) for row in rows]

    def get(self, record_id: str) -> Optional[Dict]:
        with self._connect() as db:
            row = db.execute("SELECT * FROM programs WHERE id=?", (record_id,)).fetchone()
        return self._row(row) if row else None

    def set_status(self, record_id: str, status: str) -> Optional[Dict]:
        with self._lock, self._connect() as db:
            cursor = db.execute(
                "UPDATE programs SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, record_id)
            )
            if not cursor.rowcount:
                return None
        return self.get(record_id)

    @staticmethod
    def _row(row):
        result = dict(row)
        result["program"] = json.loads(result.pop("program_json"))
        return result
