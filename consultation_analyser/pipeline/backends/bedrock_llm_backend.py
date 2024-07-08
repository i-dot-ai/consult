from django.conf import settings
from langchain_aws import BedrockLLM

from .langchain_llm_backend import LangchainLLMBackend


class BedrockLLMBackend(LangchainLLMBackend):
    def __init__(self):
        llm = BedrockLLM(
            # hardcoding this because the kwargs and model
            # are coupled - can generalise later
            model_id="mistral.mistral-large-2402-v1:0",
            region_name=settings.AWS_REGION,
            model_kwargs={
                "temperature": 0.8,
                "max_new_tokens": 2048,
                "repetition_penalty": 1.03,
                "stop": ["###", "</s>"],
                "return_full_text": False,
            },
        )
        super().__init__(llm)
