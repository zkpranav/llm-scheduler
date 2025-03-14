import asyncio
from collections import deque
from typing import Deque, Tuple
from random import random
import uuid


class BatchedQueueAsync:
    def __init__(self, n=2):
        self.n = n
        self.queue: Deque[Tuple[str, int]] = deque()
        self.cond_var = asyncio.Condition()

    async def add(self, item: Tuple[str, int]) -> None:
        async with self.cond_var:
            self.queue.append(item)
            if len(self.queue) >= self.n:
                self.cond_var.notify()

    async def retrieve(self) -> list[Tuple[str, int]]:
        async with self.cond_var:
            while len(self.queue) < self.n:
                await self.cond_var.wait()

            batch = [self.queue.popleft() for _ in range(0, self.n, 1)]
            return batch


class LLMNode:
    def __init__(self):
        self.queue = BatchedQueueAsync(n=3)
        self.results: dict[uuid.UUID, asyncio.Future] = {}

        asyncio.create_task(self.worker())

    async def __call__(self, job: int):
        job_id = str(uuid.uuid4())
        result = asyncio.Future()

        await self.queue.add((job_id, job))
        self.results[job_id] = result

        return await result

    async def worker(self):
        while True:
            batch = await self.queue.retrieve()
            print(f"Processing jobs: {", ".join([str(i[1]) for i in batch])}")
            await asyncio.sleep(0.5)  # simulate processing

            for b in batch:
                self.results[b[0]].set_result(b[1])
                del self.results[b[0]]


async def main():
    node = LLMNode()

    async with asyncio.TaskGroup() as tg:
        for i in range(15):
            print(f"Producing job: {i}")
            await asyncio.sleep(0.25 + 0.75 * random())
            tg.create_task(node(i))


if __name__ == "__main__":
    asyncio.run(main())
