from functools import lru_cache

from langchain_core.embeddings import Embeddings

from app.core.config import Settings


class EmbeddingConfigurationError(RuntimeError):
    """Raised when the configured embedding provider is not ready to use."""


@lru_cache(maxsize=4)
def _load_fastembed_model(model_name: str):
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=model_name)


class FastEmbedEmbeddings(Embeddings):
    """Generate embeddings locally with FastEmbed (no hosted API key needed)."""

    def __init__(self, model_name: str) -> None:
        self._model = _load_fastembed_model(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._model.passage_embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return next(self._model.query_embed(text)).tolist()


def create_embedding_model(settings: Settings) -> Embeddings:
    provider = settings.embedding_provider.strip().lower()
    if not settings.embedding_model.strip():
        raise EmbeddingConfigurationError("Set EMBEDDING_MODEL in the environment")

    if provider == "fastembed":
        return FastEmbedEmbeddings(settings.embedding_model)

    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(
            model=settings.embedding_model,
            base_url=settings.ollama_base_url,
        )

    if provider != "openai":
        raise EmbeddingConfigurationError(
            "Unsupported EMBEDDING_PROVIDER. Supported values are 'fastembed', 'openai', and 'ollama'."
        )
    if not settings.openai_api_key:
        raise EmbeddingConfigurationError("Set OPENAI_API_KEY to enable document embeddings")

    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )
