import asyncio
from typing import List, Callable, Awaitable
from SPARDOWN.core.logging import logger
from SPARDOWN.models.models import JobStatus

class QueueManager:
    def __init__(self, concurrency: int = 3):
        self.queue = asyncio.Queue(maxsize=200)
        self.concurrency = concurrency
        self.workers = []
        self._shutdown_event = asyncio.Event()

    async def start(self, worker_func: Callable[[int], Awaitable[None]]):
        for i in range(self.concurrency):
            worker = asyncio.create_task(self._worker_loop(i, worker_func))
            self.workers.append(worker)
        logger.info(f"Started worker pool with {self.concurrency} workers")

    async def _worker_loop(self, worker_id: int, worker_func: Callable[[int], Awaitable[None]]):
        while not self._shutdown_event.is_set():
            try:
                # Use timeout to check shutdown event periodically
                job_id = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                try:
                    await worker_func(job_id)
                except Exception as e:
                    logger.error(f"Worker {worker_id} critical failure on job {job_id}: {e}")
                finally:
                    self.queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def add_job(self, job_id: int):
        if self.queue.full():
            raise RuntimeError("Queue is full")

        await self.queue.put(job_id)


    async def stop(self):
        logger.info("Shutting down worker pool...")
        self._shutdown_event.set()
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("Worker pool stopped.")
