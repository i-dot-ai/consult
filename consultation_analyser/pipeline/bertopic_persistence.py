import os
from pathlib import Path


class BERTopicPersistence:
    def __init__(self, path: Path):
        self.path = path

    def persist(self, model, embedding_model, subpath):
        output_dir = self.path / subpath
        os.makedirs(output_dir, exist_ok=True)
        self.topic_model.save(
            output_dir,
            serialization="safetensors",
            save_ctfidf=True,
            save_embedding_model=self.embedding_model,
        )
