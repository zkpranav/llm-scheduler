import os
import json
import asyncio

from groq import AsyncClient
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage
import requests

_GROQ_CHAT_COMPLETION_URL = "/v1/chat/completions"
_GROQ_FILE_URL = "https://api.groq.com/openai/v1/files"


class GroqInputsBatched:
    job_id: str
    messages: list[AnyMessage]


def _convert_lg_msg_to_groq(messages: list[AnyMessage]):
    # Rather ugly casting, but it will suffice.
    _messages = []
    for i in range(len(messages)):
        if isinstance(messages[i], HumanMessage):
            _messages.append({"role": "user", "content": messages[i].content})
        elif isinstance(messages[i], AIMessage):
            _messages.append({"role": "assistant", "content": messages[i].content})

    return _messages


def _groq_create_batch(inputs: list[GroqInputsBatched]):
    batch = []
    for input in inputs:
        batch.append(
            {
                "custom_id": input["job_id"],
                "method": "POST",
                "url": _GROQ_CHAT_COMPLETION_URL,
                "body": {
                    "model": "llama-3.1-8b-instant",
                    "messages": _convert_lg_msg_to_groq(input["messages"]),
                },
            }
        )

    return bytes(json.dumps(batch), encoding="utf-8")


def _groq_upload_batch(batch):
    res = requests.post(
        url=_GROQ_FILE_URL,
        headers={"Authorization": f"Bearer {os.environ.get("GROQ_API_KEY")}"},
        files={"file": ("batch_file.jsonl", batch)},
        data={"purpose": "batch"},
    )

    return res.json()


async def groq_generate(client: AsyncClient, messages: list[AnyMessage]) -> str:
    res = await client.chat.completions.create(
        messages=_convert_lg_msg_to_groq(messages),
        model="llama3-8b-8192",
    )

    return AIMessage(content=res.choices[0].message.content)


async def groq_generate_batch_fake(client: AsyncClient, batch):
    return await asyncio.gather(*[groq_generate(client, b[1]) for b in batch])


async def groq_generate_batch(inputs: list[GroqInputsBatched]): ...
