"""Core data models."""

from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import datetime


class Task(BaseModel):
    """A task to be executed by the system."""
    id: str = Field(default_factory=lambda: f"task_{datetime.now().timestamp()}")
    description: str
    priority: int = Field(default=5, ge=1, le=10)
    estimated_duration_minutes: int = 30
    required_capabilities: list[str] = Field(default_factory=list)
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""
    provider: str
    model: str
    content: str
    tokens_used: int | None = None
    latency_ms: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OptimizationResult(BaseModel):
    """Result from QUBO optimization."""
    task_order: list[str]
    energy: float
    solver_time_ms: float
    metadata: dict[str, Any] = Field(default_factory=dict)