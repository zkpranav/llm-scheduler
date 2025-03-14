import getpass
import os
import asyncio
from collections import deque
from typing import Deque, Tuple, Annotated
from random import random
import uuid
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END

from langchain.chat_models import init_chat_model


class BatchedQueueAsync:
    def __init__(self, n=1):
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


class LLMScheduler:
    def __init__(self):
        self.queue = BatchedQueueAsync(n=2)
        self.results: dict[uuid.UUID, asyncio.Future] = {}

        self.model = init_chat_model("llama3-8b-8192", model_provider="groq")

        asyncio.create_task(self.worker())

    async def __call__(self, messages: list):
        job_id = str(uuid.uuid4())
        result = asyncio.Future()
        self.results[job_id] = result

        await self.queue.add((job_id, messages))

        return await result

    async def worker(self):
        while True:
            batch = await self.queue.retrieve()
            # print(f"Processing jobs: {", ".join([str(b[0]) for b in batch])}")

            res = await self.model.abatch([b[1] for b in batch])

            for i in range(len(batch)):
                self.results[batch[i][0]].set_result(res[i])
                del self.results[batch[i][0]]


async def main():
    os.environ["GROQ_API_KEY"] = getpass.getpass("GROQ_API_KEY: ")

    llm_scheduler = LLMScheduler()

    class GraphState(TypedDict):
        messages: Annotated[list, add_messages]

    async def chatbot(state: GraphState):
        return {"messages": await llm_scheduler(state["messages"])}

    async def user_thread(name: str):
        graph_builder = StateGraph(GraphState)
        graph_builder.add_node("add", chatbot)
        graph_builder.add_edge(START, "add")
        graph_builder.add_edge("add", END)
        graph = graph_builder.compile()

        await asyncio.sleep(1 + 9 * random())  # 1s - 10s delay.
        print(f"{name} queried.")
        res = await graph.ainvoke(
            {"messages": [{"role": "user", "content": f"Hello, I am {name}."}]}
        )
        print(f"For {name}: {res["messages"][-1].content}")

    async with asyncio.TaskGroup() as tg:
        names = [
            "Luke Skywalker",
            "Darth Vader",
            "Princess Leia",
            "Han Solo",
            "Obi-Wan Kenobi",
            "Yoda",
            "Emperor Palpatine",
            "Boba Fett",
            "Ahsoka Tano",
            "Mace Windu",
            "R2D2",
            "C3PO",
        ]

        tasks = []
        for i in range(4):
            tasks.append(tg.create_task(user_thread(names[i])))

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
