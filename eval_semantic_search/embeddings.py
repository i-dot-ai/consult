"""
Embedding generation for semantic search evaluation.
"""

import os
import time
from typing import List, Union

from openai import AzureOpenAI
import logging

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings using OpenAI models"""

    def __init__(self):
        # Hardcoded to text-embedding-3-small with 1024 dimensions
        self.model = "text-embedding-3-small"
        self.dimensions = 1024

        # Get Azure OpenAI settings from environment
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )

    def embed_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings using OpenAI API with retry logic"""
        max_retries = 5
        base_delay = 2  # Azure suggests 2 seconds
        
        for attempt in range(max_retries):
            try:
                response = self.client.embeddings.create(
                    input=text, model=self.model, dimensions=self.dimensions
                )
                
                if isinstance(text, str):
                    return response.data[0].embedding
                return [item.embedding for item in response.data]
                
            except Exception as e:
                if hasattr(e, 'status_code') and e.status_code == 429:
                    # Rate limit error
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Rate limit hit, waiting {delay} seconds (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    # Other errors, re-raise
                    raise
        
        # If we've exhausted all retries
        raise Exception(f"Failed to generate embeddings after {max_retries} attempts")
