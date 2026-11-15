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


class JinaEmbeddings(Embeddings):
    """Generate retrieval embeddings with Jina's OpenAI-compatible API."""

    def __init__(self, model_name: str, api_key: str) -> None:
        import httpx

        self._model_name = model_name
        self._client = httpx.Client(
            base_url="https://api.jina.ai/v1",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0,
        )

    def _embed(self, texts: list[str], task: str) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), 64):
            batch = texts[start : start + 64]
            response = self._client.post(
                "/embeddings",
                json={"model": self._model_name, "input": batch, "task": task},
            )
            response.raise_for_status()
            data = response.json()["data"]
            data.sort(key=lambda item: item["index"])
            vectors.extend(item["embedding"] for item in data)
        return vectors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts, "retrieval.passage")

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "retrieval.query")[0]


@lru_cache(maxsize=2)
def _load_jina_model(model_name: str, api_key: str) -> JinaEmbeddings:
    return JinaEmbeddings(model_name, api_key)


def create_embedding_model(settings: Settings) -> Embeddings:
    provider = settings.embedding_provider.strip().lower()
    if not settings.embedding_model.strip():
        raise EmbeddingConfigurationError("Set EMBEDDING_MODEL in the environment")

    if provider == "fastembed":
        return FastEmbedEmbeddings(settings.embedding_model)

    if provider == "jina":
        if not settings.jina_api_key:
            raise EmbeddingConfigurationError("Set JINA_API_KEY to enable Jina embeddings")
        return _load_jina_model(settings.embedding_model, settings.jina_api_key)

    if provider != "openai":
        raise EmbeddingConfigurationError(
            "Unsupported EMBEDDING_PROVIDER. Supported values are 'fastembed', 'jina', and 'openai'."
        )
    if not settings.openai_api_key:
        raise EmbeddingConfigurationError("Set OPENAI_API_KEY to enable document embeddings")

    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )
