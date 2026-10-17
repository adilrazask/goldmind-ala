import json
import sqlite3
from pathlib import Path
from typing import Any
from .models import ExperimentResult

class MemoryStore:
    """Small, persistent local memory for instructions and experiment experience."""
    def __init__(self, db_path: str = "data/ala_memory.sqlite3") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS instructions (id INTEGER PRIMARY KEY AUTOINCREMENT, instruction TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            conn.execute("CREATE TABLE IF NOT EXISTS experiments (experiment_id TEXT PRIMARY KEY, objective TEXT NOT NULL, hypothesis TEXT NOT NULL, result_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            conn.execute("CREATE TABLE IF NOT EXISTS examples (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, lesson TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            conn.execute("CREATE TABLE IF NOT EXISTS agent_state (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
            conn.execute("CREATE TABLE IF NOT EXISTS strategy_candidates (candidate_id TEXT PRIMARY KEY, family TEXT NOT NULL, spec_json TEXT NOT NULL, status TEXT NOT NULL, score REAL, result_json TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")

    def add_instruction(self, instruction: str) -> None:
        with self._connect() as conn:
            conn.execute("INSERT INTO instructions(instruction) VALUES (?)", (instruction,))

    def get_instructions(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT instruction FROM instructions ORDER BY id").fetchall()
        return [r["instruction"] for r in rows]

    def save_result(self, result: ExperimentResult) -> None:
        with self._connect() as conn:
            conn.execute("INSERT OR REPLACE INTO experiments(experiment_id, objective, hypothesis, result_json) VALUES (?, ?, ?, ?)", (result.experiment_id, result.objective, result.hypothesis, json.dumps(result.to_dict())))

    def recent_results(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT result_json, created_at FROM experiments ORDER BY created_at DESC, rowid DESC LIMIT ?", (limit,)).fetchall()
        results = []
        for row in rows:
            item = json.loads(row["result_json"])
            item["created_at"] = row["created_at"]
            results.append(item)
        return results

    def add_example(self, title: str, lesson: str) -> None:
        with self._connect() as conn:
            conn.execute("INSERT INTO examples(title, lesson) VALUES (?, ?)", (title, lesson))

    def get_examples(self) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT title, lesson, created_at FROM examples ORDER BY id").fetchall()
        return [dict(r) for r in rows]

    def experiment_count(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM experiments").fetchone()[0])

    def set_state(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute("INSERT INTO agent_state(key,value,updated_at) VALUES(?,?,CURRENT_TIMESTAMP) ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP", (key, value))

    def get_state(self, key: str, default: str | None = None) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM agent_state WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def save_candidate(self, candidate_id: str, family: str, spec: dict, status: str, score: float | None = None, result: dict | None = None) -> None:
        with self._connect() as conn:
            conn.execute("INSERT OR REPLACE INTO strategy_candidates(candidate_id,family,spec_json,status,score,result_json) VALUES(?,?,?,?,?,?)", (candidate_id, family, json.dumps(spec), status, score, json.dumps(result) if result is not None else None))

    def candidate_history(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM strategy_candidates ORDER BY created_at DESC,rowid DESC LIMIT ?", (limit,)).fetchall()
        out=[]
        for row in rows:
            item=dict(row); item["spec_json"]=json.loads(item["spec_json"]); item["result_json"]=json.loads(item["result_json"]) if item["result_json"] else None; out.append(item)
        return out
