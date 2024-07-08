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
                "stop": ["###", "</s>"],
            },
        )
        super().__init__(llm)
