from umap import UMAP
from sentence_transformers import SentenceTransformer

from consultation_analyser.consultations import models



def get_embeddings_for_question(question_id, embedding_model_name="thenlper/gte-small"):
	relevant_answers = models.Answer.objects.filter(question__id=question_id).values_list("free_text", flat=True)
	relevant_answers = list(relevant_answers)
    embedding_model = SentenceTransformer(embedding_model_name)
    embeddings = embedding_model.encode(relevant_answers)
    # Reduce to 2D embeddings
    umap_embeddings = UMAP(n_neighbors=15, n_components=2, min_dist=0.0, metric='cosine', random_state=12).fit_transform(embeddings)
    return umap_embeddings

