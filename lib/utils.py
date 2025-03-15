from groq import AsyncClient
from langchain_core.messages import HumanMessage, AIMessage


async def groq_generate(client: AsyncClient, messages: list) -> str:
    try:
        # Rather ugly casting, but it will suffice.
        _messages = []
        for i in range(len(messages)):
            if isinstance(messages[i], HumanMessage):
                _messages.append({"role": "user", "content": messages[i].content})
            elif isinstance(messages[i], AIMessage):
                _messages.append({"role": "assistant", "content": messages[i].content})

        res = await client.chat.completions.create(
            messages=_messages,
            model="llama3-8b-8192",
        )

        return {"role": "assistant", "content": res.choices[0].message.content}
    except Exception as err:
        print(err)
