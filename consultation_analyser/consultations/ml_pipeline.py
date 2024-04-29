from typing import Dict, List, Union
from uuid import UUID

import numpy as np
import pandas as pd

from consultation_analyser.consultations import models

RANDOM_STATE = 12  # For reproducibility


def get_embeddings_for_question(
    answers_list: List[Dict[str, Union[UUID, str]]], embedding_model_name: str = "thenlper/gte-small"
) -> List[Dict[str, Union[UUID, str, np.ndarray]]]:
    from sentence_transformers import SentenceTransformer

    free_text_responses = [answer["free_text"] for answer in answers_list]
    embedding_model = SentenceTransformer(embedding_model_name)
    embeddings = embedding_model.encode(free_text_responses)
    z = zip(answers_list, embeddings)
    answers_list_with_embeddings = [dict(list(d.items()) + [("embedding", embedding)]) for d, embedding in z]
    return answers_list_with_embeddings


def get_topic_model(answers_list_with_embeddings: List[Dict[str, Union[UUID, str, np.ndarray]]]):
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
        n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", n_jobs=1, random_state=RANDOM_STATE
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=3, metric="euclidean", cluster_selection_method="eom", prediction_data=True
    )
    vectorizer_model = CountVectorizer(stop_words="english")
    ctfidf_model = ClassTfidfTransformer()
    topic_model = BERTopic(
        umap_model=umap_model, hdbscan_model=hdbscan_model, vectorizer_model=vectorizer_model, ctfidf_model=ctfidf_model
    )
    topic_model.fit_transform(free_text_responses_list, embeddings=embeddings)
    return topic_model


def get_answers_and_topics(topic_model, answers_list: List[Dict[str, Union[UUID, str]]]) -> pd.DataFrame:
    # Answers free text/IDs need to be in the same order
    free_text_responses = [answer["free_text"] for answer in answers_list]
    answers_id_list = [answer["id"] for answer in answers_list]
    # Assign topics to answers
    answers_df = topic_model.get_document_info(free_text_responses)
    answers_df["id"] = answers_id_list
    answers_df = answers_df[["id", "Name"]]
    return answers_df


def save_themes_to_answers(answers_topics_df: pd.DataFrame) -> None:
    for row in answers_topics_df.itertuples():
        answer = models.Answer.objects.get(id=row.id)
        theme_label = row.Name
        answer.save_theme_to_answer(theme_label=theme_label)


def save_themes_for_question(question: models.Question) -> None:
    # Order must remain the same - so convert to list
    answers_qs = models.Answer.objects.filter(question=question).order_by("created_at")
    answers_list = list(answers_qs.values("id", "free_text"))
    answers_list_with_embeddings = get_embeddings_for_question(answers_list)
    topic_model = get_topic_model(answers_list_with_embeddings)
    answers_topics_df = get_answers_and_topics(topic_model, answers_list_with_embeddings)
    save_themes_to_answers(answers_topics_df)


def save_themes_for_consultation(consultation_id: UUID) -> None:
    questions = models.Question.objects.filter(section__consultation__id=consultation_id, has_free_text=True)
    for question in questions:
        save_themes_for_question(question)
