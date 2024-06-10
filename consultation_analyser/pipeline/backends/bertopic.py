import os
from pathlib import Path
from typing import Dict, List, Optional, Union
from uuid import UUID

import numpy as np
import pandas as pd
from django.conf import settings

from consultation_analyser.consultations import models

from .topic_backend import TopicBackend
from .types import TopicAssignment


class BERTopicBackend(TopicBackend):
    def __init__(self, embedding_model: Optional[str] = None):
        if not embedding_model:
            embedding_model = settings.BERTOPIC_DEFAULT_EMBEDDING_MODEL

        self.embedding_model = embedding_model
        self.random_state = 12  # For reproducibility
        self.topic_model = None

    def get_topics(self, question: models.Question) -> list[TopicAssignment]:
        answers_qs = models.Answer.objects.filter(question=question).order_by("created_at")
        answers_list = list(answers_qs.values("id", "free_text"))
        answers_list_with_embeddings = self.__get_embeddings_for_question(answers_list)
        self.topic_model = self.__get_topic_model(answers_list_with_embeddings)
        answers_topics_df = self.__get_answers_and_topics(
            self.topic_model, answers_list_with_embeddings
        )

        assignments = []
        for row in answers_topics_df.itertuples():
            answer = models.Answer.objects.get(id=row.id)
            topic_keywords = row.Top_n_words.split(" - ")
            topic_id = row.Topic
            assignments.append(
                TopicAssignment(topic_id=topic_id, topic_keywords=topic_keywords, answer=answer)
            )

        return assignments

    def save_topic_model(self, output_dir) -> None:
        if not self.topic_model:
            raise Exception(
                "You cannot save the BERTopic topic model until you've called get_topics"
            )

        output_dir = Path(output_dir) / "bertopic"
        os.makedirs(output_dir, exist_ok=True)
        self.topic_model.save(
            output_dir,
            serialization="safetensors",
            save_ctfidf=True,
            save_embedding_model=self.embedding_model,
        )

    def __get_embeddings_for_question(
        self,
        answers_list: List[Dict[str, Union[UUID, str]]],
    ) -> List[Dict[str, Union[UUID, str, np.ndarray]]]:
        from sentence_transformers import SentenceTransformer

        free_text_responses = [answer["free_text"] for answer in answers_list]
        embedding_model = SentenceTransformer(self.embedding_model)
        embeddings = embedding_model.encode(free_text_responses)
        z = zip(answers_list, embeddings)
        answers_list_with_embeddings = [
            dict(list(d.items()) + [("embedding", embedding)]) for d, embedding in z
        ]
        return answers_list_with_embeddings

    def __get_topic_model(
        self, answers_list_with_embeddings: List[Dict[str, Union[UUID, str, np.ndarray]]]
    ):
        from bertopic import BERTopic
        from bertopic.vectorizers import ClassTfidfTransformer
        from hdbscan import HDBSCAN
        from sklearn.feature_extraction.text import CountVectorizer
        from umap.umap_ import UMAP

        free_text_responses_list = [answer["free_text"] for answer in answers_list_with_embeddings]
        embeddings_list = [answer["embedding"] for answer in answers_list_with_embeddings]
        embeddings = np.array(embeddings_list)
        # Set random_state so that we can reproduce the results
        umap_model = UMAP(
            n_neighbors=15,
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
        vectorizer_model = CountVectorizer(stop_words="english")
        ctfidf_model = ClassTfidfTransformer()
        topic_model = BERTopic(
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            vectorizer_model=vectorizer_model,
            ctfidf_model=ctfidf_model,
        )
        topic_model.fit_transform(free_text_responses_list, embeddings=embeddings)
        return topic_model

    def __get_answers_and_topics(
        self, topic_model, answers_list: List[Dict[str, Union[UUID, str]]]
    ) -> pd.DataFrame:
        # Answers free text/IDs need to be in the same order
        free_text_responses = [answer["free_text"] for answer in answers_list]
        answers_id_list = [answer["id"] for answer in answers_list]
        # Assign topics to answers
        answers_df = topic_model.get_document_info(free_text_responses)
        answers_df["id"] = answers_id_list
        answers_df = answers_df[["id", "Top_n_words", "Topic"]]
        return answers_df
