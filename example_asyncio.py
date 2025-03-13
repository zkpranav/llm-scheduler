import asyncio
from collections import deque
from typing import Deque
from random import random


class BatchedQueueAsync:
    def __init__(self, n=2):
        self.n = n
        self.queue: Deque[int] = deque()
        self.cond_var = asyncio.Condition()

    async def add(self, item: int) -> None:
        async with self.cond_var:
            self.queue.append(item)
            if len(self.queue) >= self.n:
                self.cond_var.notify()

    async def retrieve(self) -> list[int]:
        async with self.cond_var:
            while len(self.queue) < self.n:
                await self.cond_var.wait()

            batch = [self.queue.popleft() for _ in range(0, self.n, 1)]
            return batch


async def worker(queue: BatchedQueueAsync) -> None:
    while True:
        batch = await queue.retrieve()
        print(f"Processing jobs: {", ".join([str(i) for i in batch])}")
        await asyncio.sleep(0.5)  # simulate processing

        # Dummy exit
        if 14 in batch:
            break


async def main():
    queue = BatchedQueueAsync(n=3)

    worker_task = asyncio.create_task(worker(queue))

    for i in range(0, 15, 1):
        asyncio.sleep(0.5 + 1.5 * random())
        await queue.add(i)

    await asyncio.gather(worker_task)


if __name__ == "__main__":
    asyncio.run(main())
