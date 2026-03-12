"""In-memory job store for background processing (replaces Celery + Redis)."""

from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class JobState:
    """Tracks state for a single background job."""

    status: str = "PENDING"  # PENDING | PROGRESS | SUCCESS | FAILURE
    progress: float = 0.0
    step: str = ""
    result: dict[str, Any] | None = None
    error: str | None = None


class JobStore:
    """Thread-safe in-memory job store."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobState] = {}
        self._lock = threading.Lock()

    def create(self, job_id: str) -> None:
        with self._lock:
            self._jobs[job_id] = JobState()

    def get(self, job_id: str) -> JobState | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update_progress(self, job_id: str, step: str, progress: float) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = "PROGRESS"
                job.step = step
                job.progress = progress

    def set_success(self, job_id: str, result: dict[str, Any]) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = "SUCCESS"
                job.progress = 1.0
                job.result = result

    def set_failure(self, job_id: str, error: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.status = "FAILURE"
                job.error = error

    def remove(self, job_id: str) -> None:
        with self._lock:
            self._jobs.pop(job_id, None)


# Singleton instance
job_store = JobStore()
