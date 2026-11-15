from langchain_core.documents import Document

from app.core.config import Settings
from app.rag.ingestion.embeddings import create_embedding_model


def get_chroma_collection(settings: Settings):
    """Return the configured remote Chroma collection."""
    import chromadb

    client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
    return client.get_or_create_collection(
        name=settings.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )


def store_chunks(chunks: list[Document], settings: Settings) -> None:
    """Embed chunks and persist vectors and metadata in the Chroma server."""
    embedding_model = create_embedding_model(settings)
    vectors = embedding_model.embed_documents([chunk.page_content for chunk in chunks])

    collection = get_chroma_collection(settings)
    collection.add(
        ids=[str(chunk.id) for chunk in chunks],
        documents=[chunk.page_content for chunk in chunks],
        embeddings=vectors,
        metadatas=[chunk.metadata for chunk in chunks],
    )
