"""LLM abstraction layer for themefinder.

Provides a Protocol-based interface for LLM calls with structured output support,
and an OpenAI implementation. Designed for easy extension to other providers.
"""

import asyncio
import concurrent.futures
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np
import openai
from pydantic import BaseModel


@dataclass
class LLMResponse:
    """Wraps an LLM call result."""

    parsed: BaseModel | str


@runtime_checkable
class LLM(Protocol):
    """Protocol defining the LLM interface for themefinder."""

    async def ainvoke(
        self, prompt: str, output_model: type[BaseModel] | None = None
    ) -> LLMResponse: ...

    def invoke(
        self, prompt: str, output_model: type[BaseModel] | None = None
    ) -> LLMResponse: ...


class OpenAILLM:
    """OpenAI SDK implementation of the LLM protocol."""

    def __init__(
        self,
        model,
        request_kwargs: dict | None = None,
        **client_kwargs,
    ):
        self.model = model
        self.request_kwargs = request_kwargs or {}
        self.client = openai.AsyncOpenAI(**client_kwargs)

    async def ainvoke(
        self, prompt: str, output_model: type[BaseModel] | None = None
    ) -> LLMResponse:
        kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            **self.request_kwargs,
        }
        if output_model:
            kwargs["response_format"] = output_model
            response = await self.client.chat.completions.parse(**kwargs)
            return LLMResponse(parsed=response.choices[0].message.parsed)
        else:
            response = await self.client.chat.completions.create(**kwargs)
            return LLMResponse(parsed=response.choices[0].message.content)

    def invoke(
        self, prompt: str, output_model: type[BaseModel] | None = None
    ) -> LLMResponse:
        """Synchronous wrapper around ainvoke."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    asyncio.run, self.ainvoke(prompt, output_model)
                ).result()
        return asyncio.run(self.ainvoke(prompt, output_model))


@runtime_checkable
class Embedder(Protocol):
    """Protocol for text embedding, kept separate from LLM so each can be swapped alone."""

    async def aembed(self, texts: list[str]) -> np.ndarray:
        """Return an array of shape (len(texts), dim), one row per text in order."""
        ...


class OpenAIEmbedder:
    """OpenAI SDK implementation of the Embedder protocol."""

    def __init__(
        self,
        model: str = "text-embedding-3-large",
        batch_size: int = 256,
        concurrency: int = 5,
        **client_kwargs,
    ):
        self.model = model
        self.batch_size = batch_size
        self.concurrency = concurrency
        self.client = openai.AsyncOpenAI(**client_kwargs)

    async def aembed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 0), dtype=np.float32)

        semaphore = asyncio.Semaphore(self.concurrency)

        async def embed_batch(batch: list[str]) -> list[list[float]]:
            async with semaphore:
                response = await self.client.embeddings.create(
                    input=batch, model=self.model
                )
            return [item.embedding for item in response.data]

        batches = [
            texts[i : i + self.batch_size]
            for i in range(0, len(texts), self.batch_size)
        ]
        results = await asyncio.gather(*[embed_batch(batch) for batch in batches])
        return np.asarray(
            [vector for batch in results for vector in batch], dtype=np.float32
        )
