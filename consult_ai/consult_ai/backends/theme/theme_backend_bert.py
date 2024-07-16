import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from uuid import UUID

import numpy as np
import pandas as pd

from consult_ai.models.public_schema import Question, Answer, Theme
from consult_ai.backends.theme.theme_backend_base import ThemeBackendBase

logger = logging.getLogger("pipeline")


class ThemeBackendBert(ThemeBackendBase):
    def __init__(
        self,
        embedding_model: Optional[str] = None,
        persistence_path: Optional[Path] = None,
        device: Optional[str] = "cpu",
    ):
        # if not embedding_model:
        #     embedding_model = settings.BERTOPIC_DEFAULT_EMBEDDING_MODEL

        logger.info(f"BERTopic using embedding_model: {embedding_model}")

        self.embedding_model = embedding_model
        self.random_state = 12  # For reproducibility
        self.topic_model = None
        self.persistence_path = persistence_path
        self.device = device
        self.n_neighbors = 15

    def get_themes(
        self, question: Question, answers: List[Answer]
    ) -> tuple[List[Theme], List[Answer]]:

        answers_list = answers

        logger.info("BERTopic embedding")
        answers_list_with_embeddings = self.__get_embeddings_for_question(answers_list)

        logger.info("BERTopic topic model generation")
        topic_model = self.__get_topic_model(answers_list_with_embeddings)
        self.topic_model = topic_model

        topics = topic_model.topics_

        # Get the theme keywords for unique topics
        themes = []
        mapping = {}
        for topic_id in list(set(topics)):
            key_words = topic_model.get_topic(topic_id)
            # Drop the proportions
            key_words = [x[0] for x in key_words]

            theme = Theme(
                topic_id=topic_id,
                topic_keywords=key_words,
            )
            mapping[topic_id] = theme.id

            themes.append(theme)

        # Set the theme_id of the answer objects
        for answer, topic_id in zip(answers, topics):
            theme_id = mapping[topic_id]
            answer.theme_id = theme_id

        return (themes, answers)

    def __persist(self, subpath: str, answers_list_with_embeddings):
        # satisfy mypy
        if not self.persistence_path:
            return

        output_dir = Path(self.persistence_path) / subpath
        os.makedirs(output_dir, exist_ok=True)

        if not self.topic_model:
            raise Exception(
                "You cannot persist the topic model until you have run get_topics"
            )

        self.topic_model.save(
            output_dir,
            serialization="safetensors",
            save_ctfidf=True,
            save_embedding_model=self.embedding_model,
        )

        logger.info(f"BERTopic model persisted to {output_dir}")

    def __get_embeddings_for_question(self, answers_list: List[Answer]) -> List[Answer]:
        from sentence_transformers import SentenceTransformer
        from umap.umap_ import UMAP

        free_text_responses = [answer.free_text for answer in answers_list]
        embedding_model = SentenceTransformer(self.embedding_model)
        embeddings = embedding_model.encode(free_text_responses)
        two_dim_embeddings = UMAP(
            n_neighbors=self.n_neighbors,
            n_components=2,
            min_dist=0.0,
            metric="cosine",
            random_state=self.random_state,
        ).fit_transform(embeddings)
        z = zip(answers_list, embeddings, two_dim_embeddings)

        output_answer_list = []
        for answer, embedding, two_dim_embedding in z:
            answer.embedding = embedding
            answer.two_dim_embedding = two_dim_embedding
            output_answer_list.append(answer)

        return output_answer_list

    def __get_topic_model(self, answers_list_with_embeddings: List[Answer]):
        from bertopic import BERTopic
        from bertopic.vectorizers import ClassTfidfTransformer
        from hdbscan import HDBSCAN
        from sklearn.feature_extraction.text import CountVectorizer
        from umap.umap_ import UMAP

        free_text_responses_list = [
            answer.free_text for answer in answers_list_with_embeddings
        ]
        embeddings_list = [answer.embedding for answer in answers_list_with_embeddings]
        embeddings = np.array(embeddings_list)
        umap_model = UMAP(
            n_neighbors=self.n_neighbors,
            n_components=5,
            min_dist=0.0,
            metric="cosine",
            n_jobs=1,
            random_state=self.random_state,
        )
        hdbscan_model = HDBSCAN(
            min_cluster_size=3,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=True,
        )
        vectorizer_model = CountVectorizer(stop_words="english", ngram_range=(1, 2))
        ctfidf_model = ClassTfidfTransformer()
        topic_model = BERTopic(
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=vectorizer_model,
            ctfidf_model=ctfidf_model,
        )
        topic_model.fit_transform(free_text_responses_list, embeddings=embeddings)
        return topic_model


if __name__ == "__main__":
    backend = ThemeBackendBert(
        embedding_model="sentence-transformers-testing/stsb-bert-tiny-safetensors"
    )
    question = Question(id="1", text="Questiom text", has_free_text=True)
    answers = [Answer(question_id="1", free_text=f"My answer {i}") for i in range(10)]

    test = backend.get_themes(question, answers)
    print(test)
