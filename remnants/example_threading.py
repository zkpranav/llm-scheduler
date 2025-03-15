from collections import deque
from typing import Deque
from threading import Condition, Thread
from time import sleep
from random import random


class BatchedQueue:
    def __init__(self, n=2):
        self.n = n
        self.queue: Deque[int] = deque()
        self.cond_var = Condition()

    def add(self, item: int) -> None:
        with self.cond_var:
            self.queue.append(item)
            if len(self.queue) >= self.n:
                self.cond_var.notify()

    def retrieve(self) -> list[int]:
        with self.cond_var:
            while len(self.queue) < self.n:
                self.cond_var.wait()

            batch = [self.queue.popleft() for _ in range(0, self.n, 1)]
            return batch


def worker(queue: BatchedQueue) -> None:
    while True:
        batch = queue.retrieve()
        print(f"Processing jobs: {", ".join([str(i) for i in batch])}")
        sleep(0.5)  # simulate processing

        # Dummy exit
        if 14 in batch:
            break


def main():
    queue = BatchedQueue(n=3)

    w_thread = Thread(target=worker, kwargs={"queue": queue}, daemon=False)
    w_thread.start()

    for i in range(0, 15, 1):
        sleep(0.5 + 1.5 * random())
        queue.add(i)

    w_thread.join()


if __name__ == "__main__":
    main()
