from umap import UMAP
from sentence_transformers import SentenceTransformer
from hdbscan import HDBSCAN
from bertopic import BERTopic
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn import CountVectorizer
import pandas as pd

from consultation_analyser.consultations import models


def get_answers_text_for_question(question_id):
	answers = models.Answer.objects.filter(question__id=question_id).sort_by("created_at").values_list(["id", "free_text"])
	return answers


def get_free_text_responses_from_answers(answers):
    free_text_responses = [answer["free_text"] for answer in answers]
    return free_text_responses


def get_answers_text_df(answers):
    df = pd.DataFrame(answers)
    return df


def get_embeddings_for_question(free_text_responses, embedding_model_name="thenlper/gte-small"):
    embedding_model = SentenceTransformer(embedding_model_name)
    embeddings = embedding_model.encode(free_text_responses)
    return embeddings


def get_topics(free_text_responses_list, embeddings):
    umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric='cosine', random_state=12)
    hdbscan_model = HDBSCAN(min_cluster_size=3, metric='euclidean', cluster_selection_method='eom', prediction_data=True)
    vectorizer_model = CountVectorizer(stop_words="english")
    ctfidf_model = ClassTfidfTransformer()
    topic_model = BERTopic(umap_model=umap_model, hdbscan_model=hdbscan_model, vectorizer_model=vectorizer_model, ctfidf_model=ctfidf_model)
    topic_model.fit_transform(free_text_responses_list, embeddings=embeddings)
    return topic_model


# TODO: Do we need this? What is this for?
def get_2d_embeddings(embeddings):
    umap_embeddings = UMAP(n_neighbors=15, n_components=2, min_dist=0.0, metric='cosine', random_state=12).fit_transform(embeddings)
    return umap_embeddings


def save_themes(topic_model):
    # TODO - add question_id to Theme model (maybe)
    topic_df = topic_model.get_topic_info()
    topic_id_lookup = {} # Mapping topic_id from model to UUID in DB
    for row in topic_df.itertuples():
        theme = models.Theme(keywords=row[??], label=[??]) #TODO - what are field names
        theme.save()
        topic_id_lookup[row["ID"]] = theme.id
        # TODO - update with the correc t
        # save each topic to theme model
        # add column to df with theme ID

    return topic_id_lookup


def save_themes_for_answers(topic_model, topic_id_lookup, answers):
    answers_df = get_answers_text_df(answers)
    free_text_responses = get_free_text_responses_from_answers(answers)
    answers_topics_df = topic_model.get_document_info(free_text_responses)
    # then just select the columns we care about
    # join answers_topics_df with answers_df to get original IDs
    # Replace topic ID with the theme ID from database (topic_id_lookup)

    for row in answers_df.itertuples():
        row.id (for example)



