from langchain_core.embeddings import Embeddings

from app.core.config import Settings


class EmbeddingConfigurationError(RuntimeError):
    """Raised when the configured embedding provider is not ready to use."""


def create_embedding_model(settings: Settings) -> Embeddings:
    provider = settings.embedding_provider.strip().lower()
    if not settings.embedding_model.strip():
        raise EmbeddingConfigurationError("Set EMBEDDING_MODEL in the environment")

    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(
            model=settings.embedding_model,
            base_url=settings.ollama_base_url,
        )

    if provider != "openai":
        raise EmbeddingConfigurationError(
            "Unsupported EMBEDDING_PROVIDER. Supported values are 'openai' and 'ollama'."
        )
    if not settings.openai_api_key:
        raise EmbeddingConfigurationError("Set OPENAI_API_KEY to enable document embeddings")

    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )
