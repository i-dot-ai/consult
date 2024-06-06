from langchain_community.llms import Ollama

from .langchain_llm_backend import LangchainLLMBackend


class OllamaLLMBackend(LangchainLLMBackend):
    def __init__(self, model_name: str):
        llm = Ollama(model=model_name)
        super().__init__(llm)
