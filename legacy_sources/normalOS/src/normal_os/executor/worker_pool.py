"""
WorkerPool for normalOS

Expanded with better resource budgeting, cancellation support,
and priority handling.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class WorkerTask:
    id: str
    coro: Callable
    priority: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)
    cancelled: bool = False


class WorkerPool:
    """Async worker pool with resource limits and cancellation."""

    def __init__(self, max_workers: int = 8, max_memory_mb: int = 2048):
        self.max_workers = max_workers
        self.max_memory_mb = max_memory_mb
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._workers: List[asyncio.Task] = []
        self._running = False

    async def start(self):
        self._running = True
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_loop(i))
            self._workers.append(worker)

    async def submit(self, coro: Callable, priority: int = 5, metadata: Optional[Dict] = None):
        task = WorkerTask(
            id=str(asyncio.current_task().get_name() if asyncio.current_task() else "unknown"),
            coro=coro,
            priority=priority,
            metadata=metadata or {}
        )
        await self._queue.put((priority, task))

    async def _worker_loop(self, worker_id: int):
        while self._running:
            try:
                priority, task = await self._queue.get()
                if task.cancelled:
                    continue
                await task.coro()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")

    async def cancel_all(self):
        for w in self._workers:
            w.cancel()
        self._workers.clear()
        self._running = False
