import aiosqlite
import json
from datetime import datetime
from typing import Any, List, Optional

from normal_os.core.models import Task, TaskStatus


class TaskStore:
    """Explicit async persistence for tasks + context/history."""

    def __init__(self, db_path: str = "./data/normalos.db"):
        self.db_path = db_path

    async def _init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    type TEXT,
                    payload TEXT,
                    status TEXT,
                    created_at TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    result TEXT,
                    error TEXT,
                    priority INTEGER
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS task_context (
                    task_id TEXT,
                    key TEXT,
                    value TEXT,
                    PRIMARY KEY (task_id, key)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    event TEXT,
                    data TEXT,
                    ts TEXT
                )
            """)
            await db.commit()

    async def save(self, task: Task):
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO tasks
                (id, type, payload, status, created_at, started_at, completed_at, result, error, priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id, task.type, json.dumps(task.payload), task.status,
                task.created_at.isoformat(),
                task.started_at.isoformat() if task.started_at else None,
                task.completed_at.isoformat() if task.completed_at else None,
                json.dumps(task.result) if task.result else None,
                task.error, task.priority
            ))
            await db.commit()

    async def get(self, task_id: str) -> Optional[Task]:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = await cursor.fetchone()
            if row:
                return self._row_to_task(row)
            return None

    async def list_by_status(self, status: TaskStatus) -> List[Task]:
        await self._init_db()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT * FROM tasks WHERE status = ? ORDER BY priority DESC, created_at", (status,))
            rows = await cursor.fetchall()
            return [self._row_to_task(r) for r in rows]

    def _row_to_task(self, row) -> Task:
        return Task(
            id=row[0],
            type=row[1],
            payload=json.loads(row[2]) if row[2] else {},
            status=row[3],
            created_at=datetime.fromisoformat(row[4]),
            started_at=datetime.fromisoformat(row[5]) if row[5] else None,
            completed_at=datetime.fromisoformat(row[6]) if row[6] else None,
            result=json.loads(row[7]) if row[7] else None,
            error=row[8],
            priority=row[9],
        )