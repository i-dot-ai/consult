from typing import Optional

from langchain_community.llms import FakeListLLM

from .langchain_llm_backend import LangchainLLMBackend


class DummyLLMBackend(LangchainLLMBackend):
    def __init__(self, responses: Optional[list[str]] = None):
        resp = '{ "short_description": "Example short description", "summary": "Example summary" }'
        if not responses:
            responses = [resp]
        llm = FakeListLLM(responses=responses)
        super().__init__(llm)
