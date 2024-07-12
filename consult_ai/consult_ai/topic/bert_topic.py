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
answers_list_with_embeddings = [
    AnswerWithEmbeddings(answer.id, answer.free_text, embedding, two_dim_embedding)
    for answer, embedding, two_dim_embedding in z
]