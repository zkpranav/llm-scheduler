import asyncio
from collections import deque


class BatchedQueueAsync:
    """An asynchronous queue that batches items and supports timeout-based retrieval.

    This queue collects items until either the batch size is reached or a timeout occurs.
    Items are then retrieved as a batch.

    Args:
        n (int, optional): The maximum batch size. Defaults to 1.
        timeout (float, optional): The timeout duration in seconds. Defaults to 5.0.
    """

    def __init__(self, n=1, timeout=5.0):
        self.n = n
        self.timeout = timeout
        self.queue = deque()
        self.cond_var = asyncio.Condition()

        self.timeout_task = None

    async def _timeout_handler(self):
        try:
            await asyncio.sleep(self.timeout)

            async with self.cond_var:
                if len(self.queue) > 0:
                    self.cond_var.notify()
        except asyncio.CancelledError:
            pass

    async def add(self, item):
        """Add an item to the queue.

        If the batch size is reached, notifies waiting consumers.
        If not, starts a timeout task if one isn't already running.

        Args:
            item: The item to add to the queue.
        """
        async with self.cond_var:
            self.queue.append(item)
            if len(self.queue) >= self.n:
                self.cond_var.notify()
            elif self.timeout_task is None:
                self.timeout_task = asyncio.create_task(self._timeout_handler())

    async def retrieve(self):
        """Retrieve a batch of items from the queue.

        Waits until either the batch size is reached or timeout occurs.
        Cancels any pending timeout task when items are retrieved.

        Returns:
            list: A batch of items from the queue, up to the maximum batch size.
        """
        async with self.cond_var:
            while len(self.queue) < self.n:
                await self.cond_var.wait()

                if len(self.queue) != 0:
                    break  # Either timeout hit or queue has enough items.

            if self.timeout_task is not None:
                self.timeout_task.cancel()
                self.timeout_task = None

            batch_size = min(len(self.queue), self.n)
            batch = [self.queue.popleft() for _ in range(0, batch_size, 1)]

            if len(self.queue) > 0:
                self.timeout_task = asyncio.create_task(self._timeout_handler())

            return batch
