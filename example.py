import getpass
import os
import asyncio
from typing import Annotated
from random import random
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END

from lib.llm_scheduler import LLMScheduler


async def main():
    os.environ["GROQ_API_KEY"] = getpass.getpass("GROQ_API_KEY: ").strip()

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

        # await asyncio.sleep(1 + 9 * random())  # 1s - 10s delay.
        await asyncio.sleep(0.5 + 1.5 * random())  # 0.5s - 2s delay.
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
        for i in range(3):
            tasks.append(tg.create_task(user_thread(names[i])))

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
