import asyncio
import uuid

from langchain.chat_models import init_chat_model

from lib.batched_queue import BatchedQueueAsync


class LLMScheduler:
    """A scheduler for batching and processing LLM requests asynchronously.

    This scheduler collects LLM requests into batches for efficient processing.
    It uses a batched queue to collect requests and processes them when either
    the batch size is reached or a timeout occurs.
    """

    def __init__(self):
        self.queue = BatchedQueueAsync(n=2, timeout=3.0)
        self.results: dict[uuid.UUID, asyncio.Future] = {}

        self.model = init_chat_model("llama3-8b-8192", model_provider="groq")

        self.worker_task = asyncio.create_task(self._worker())

    async def __call__(self, messages: list):
        """Process a single LLM request.

        Args:
            messages (list): The messages to be processed by the LLM.

        Returns:
            The result of LLM processing.
        """
        job_id = str(uuid.uuid4())
        result = asyncio.Future()
        self.results[job_id] = result

        await self.queue.add((job_id, messages))

        return await result

    async def _worker(self):
        """Background worker that processes batches of LLM requests.

        Continuously retrieves batches from the queue and processes them
        using the LLM model. Results are stored in the futures dictionary
        and made available to the waiting callers.
        """
        while True:
            batch = await self.queue.retrieve()
            print(f"Processing jobs: {", ".join([str(b[0]) for b in batch])}")

            res = await self.model.abatch([b[1] for b in batch])

            for i in range(len(batch)):
                self.results[batch[i][0]].set_result(res[i])
                del self.results[batch[i][0]]
