import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Dict

import structlog

from normal_os.core.models import Task, TaskStatus
from normal_os.persistence.task_store import TaskStore

logger = structlog.get_logger(__name__)


class TaskExecutor:
    """Explicit async task executor with retry, cancellation and resource budgeting."""

    def __init__(
        self,
        max_concurrent: int = 8,
        default_timeout: int = 300,
        max_retries: int = 3,
    ):
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self.store = TaskStore()

    async def submit(
        self,
        task_type: str,
        payload: dict[str, Any],
        priority: int = 5,
        timeout: int | None = None,
    ) -> str:
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            type=task_type,
            payload=payload,
            priority=priority,
        )
        await self.store.save(task)
        logger.info("task_submitted", task_id=task_id, type=task_type)
        return task_id

    async def run_task(self, task: Task, handler: Callable) -> None:
        async with self._semaphore:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            await self.store.save(task)

            for attempt in range(self.max_retries + 1):
                try:
                    result = await asyncio.wait_for(
                        handler(task),
                        timeout=task.payload.get("timeout", self.default_timeout),
                    )
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    task.completed_at = datetime.utcnow()
                    await self.store.save(task)
                    logger.info("task_completed", task_id=task.id)
                    return
                except asyncio.TimeoutError:
                    logger.warning("task_timeout", task_id=task.id, attempt=attempt)
                    if attempt == self.max_retries:
                        task.status = TaskStatus.FAILED
                        task.error = "Timeout after retries"
                        await self.store.save(task)
                        return
                except Exception as e:
                    logger.error("task_error", task_id=task.id, error=str(e), attempt=attempt)
                    if attempt == self.max_retries:
                        task.status = TaskStatus.FAILED
                        task.error = str(e)
                        await self.store.save(task)
                        return
                    await asyncio.sleep(2 ** attempt)  # exponential backoff

    async def cancel(self, task_id: str) -> bool:
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            logger.info("task_cancelled", task_id=task_id)
            return True
        return False

    async def get_status(self, task_id: str) -> Task | None:
        return await self.store.get(task_id)