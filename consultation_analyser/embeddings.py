import random

from django.conf import settings
from openai import AzureOpenAI

from consultation_analyser.hosting_environment import HostingEnvironment

hosting_environment = HostingEnvironment()


def _uniform_vector(txt):
    seed = hash(txt) % (2**32)  # Ensure positive 32-bit integer
    random.seed(seed)
    return [random.uniform(-1, 1) for _ in range(settings.EMBEDDING_DIMENSION)]


if hosting_environment.is_deployed():
    client = AzureOpenAI()

    def embed_text(text: str | list[str]) -> list[float] | list[list[float]]:
        response = client.embeddings.create(
            input=text, model="text-embedding-3-small", dimensions=settings.EMBEDDING_DIMENSION
        )
        return response.data[0].embedding

else:

    def embed_text(text: str | list[str]) -> list[float] | list[list[float]]:
        if isinstance(text, str):
            return _uniform_vector(text)
        if isinstance(text, list):
            return list(map(_uniform_vector, text))
        raise ValueError(f"expected str or list[str] not {type(text)}")
