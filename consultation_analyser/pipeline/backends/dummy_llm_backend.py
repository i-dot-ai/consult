from langchain_community.llms import FakeListLLM

from .langchain_llm_backend import LangchainLLMBackend


class DummyLLMBackend(LangchainLLMBackend):
    def __init__(self, responses: list[str] = None):
        if not responses:
            responses = [
                '{"short description": "Example short description", "summary": "Example summary"}'
            ]
        llm = FakeListLLM(responses=responses)
        super().__init__(llm)
