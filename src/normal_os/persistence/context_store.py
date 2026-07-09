"""
ContextStore for normalOS

Persistent context memory across sessions.
Expanded with better layering and metadata support.
"""

import aiosqlite
import json
from typing import Any, Dict, List, Optional


class ContextStore:
    """Persistent context / memory store with layer support."""

    def __init__(self, db_path: str = "./data/normalos.db"):
        self.db_path = db_path

    async def _ensure_table(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context_key TEXT,
                    value TEXT,
                    layer INTEGER DEFAULT 0,
                    metadata TEXT,
                    ts TEXT
                )
            """)
            await db.commit()

    async def save_context(self, key: str, value: Any, layer: int = 0, metadata: Optional[Dict] = None):
        await self._ensure_table()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO context (context_key, value, layer, metadata, ts)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (key, json.dumps(value), layer, json.dumps(metadata or {})))
            await db.commit()

    async def get_context(self, key: str, layer: Optional[int] = None) -> List[Dict]:
        await self._ensure_table()
        async with aiosqlite.connect(self.db_path) as db:
            if layer is not None:
                cursor = await db.execute(
                    "SELECT * FROM context WHERE context_key = ? AND layer = ? ORDER BY ts DESC",
                    (key, layer),
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM context WHERE context_key = ? ORDER BY ts DESC", (key,)
                )
            rows = await cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "key": r[1],
                    "value": json.loads(r[2]),
                    "layer": r[3],
                    "metadata": json.loads(r[4]) if r[4] else {},
                    "ts": r[5],
                }
                for r in rows
            ]
