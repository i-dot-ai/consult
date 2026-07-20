"""LLM abstraction layer for themefinder.

A single Pydantic AI-backed ``LLM`` class drives all chat/structured calls.
The model/provider is a single configurable value: pass a provider-prefixed
string (``"openai:gpt-4o"``, ``"anthropic:claude-..."``, ``"google:gemini-..."``)
for direct-to-provider routing, or a ``base_url``/``api_key`` pair to route through
an OpenAI-compatible gateway (the Consult LiteLLM proxy).
"""

from dataclasses import dataclass

from pydantic import BaseModel
from pydantic_ai import Agent, NativeOutput
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings


@dataclass
class LLMResponse:
    """Wraps an LLM call result."""

    parsed: BaseModel | str


def _resolve_model(
    model: str | Model,
    base_url: str | None,
    api_key: str | None,
) -> str | Model:
    """Resolve the ``model`` argument into something an ``Agent`` accepts.

    - ``model`` is already a ``Model`` instance -> use as-is (also the test seam),
      regardless of ``base_url``/``api_key``: a ready-made model carries its own
      provider, so there is nothing for the gateway args to configure.
    - ``base_url``/``api_key`` given (with a string ``model``) -> gateway mode:
      build an ``OpenAIChatModel`` over an ``OpenAIProvider`` pointed at the
      gateway. Here ``model`` is the gateway's model name (no ``provider:``
      prefix); the proxy does the routing.
    - otherwise -> pass the provider-prefixed string straight through to the
      ``Agent``, which resolves the provider from env API keys.
    """
    if not isinstance(model, str):
        return model
    if base_url is not None or api_key is not None:
        return OpenAIChatModel(
            model,
            provider=OpenAIProvider(base_url=base_url, api_key=api_key),
        )
    return model


class LLM:
    """Pydantic AI-backed implementation of the themefinder LLM interface."""

    def __init__(
        self,
        model: str | Model,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        temperature: float | None = None,
        model_settings: ModelSettings | None = None,
    ):
        self._model = _resolve_model(model, base_url, api_key)
        self._settings = model_settings or (
            ModelSettings(temperature=temperature) if temperature is not None else None
        )
        self._agent = Agent(self._model)

    @staticmethod
    def _output_type(output_model: type[BaseModel] | None):
        return NativeOutput(output_model) if output_model is not None else str

    async def ainvoke(
        self, prompt: str, output_model: type[BaseModel] | None = None
    ) -> LLMResponse:
        result = await self._agent.run(
            prompt,
            output_type=self._output_type(output_model),
            model_settings=self._settings,
        )
        return LLMResponse(parsed=result.output)

    def invoke(
        self, prompt: str, output_model: type[BaseModel] | None = None
    ) -> LLMResponse:
        result = self._agent.run_sync(
            prompt,
            output_type=self._output_type(output_model),
            model_settings=self._settings,
        )
        return LLMResponse(parsed=result.output)
