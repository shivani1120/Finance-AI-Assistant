from typing import Any

from app.core.config import Settings
from app.rag.ingestion.embeddings import EmbeddingConfigurationError, create_embedding_model
from app.rag.ingestion.vector_store import get_chroma_collection
from app.schemas.retrieval import RetrievalFilters, RetrievedChunk


class RetrievalServiceError(RuntimeError):
    """Raised when the vector search dependency cannot complete a search."""


def retrieve_chunks(
    question: str,
    *,
    filters: RetrievalFilters,
    user_id: str,
    top_k: int,
    settings: Settings,
) -> list[RetrievedChunk]:
    """Embed a question and fetch its nearest matching chunks from Chroma."""
    try:
        collection = get_chroma_collection(settings)
        if collection.count() == 0:
            return []

        query_embedding = create_embedding_model(settings).embed_query(question)
        query_options: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        where = filters.to_chroma_where()
        ownership_filter = {"user_id": user_id}
        if where and "$and" in where:
            query_options["where"] = {"$and": [ownership_filter, *where["$and"]]}
        elif where:
            query_options["where"] = {"$and": [ownership_filter, where]}
        else:
            query_options["where"] = ownership_filter

        result = collection.query(**query_options)
    except EmbeddingConfigurationError:
        raise
    except Exception as exc:
        raise RetrievalServiceError("Vector search could not be completed") from exc

    ids = (result.get("ids") or [[]])[0] or []
    documents = (result.get("documents") or [[]])[0] or []
    metadatas = (result.get("metadatas") or [[]])[0] or []
    distances = (result.get("distances") or [[]])[0] or []

    retrieved: list[RetrievedChunk] = []
    for chunk_id, content, metadata, distance in zip(
        ids, documents, metadatas, distances, strict=False
    ):
        if content is None or metadata is None or distance is None:
            continue
        numeric_distance = float(distance)
        retrieved.append(
            RetrievedChunk(
                chunk_id=str(metadata.get("chunk_id", chunk_id)),
                document_id=str(metadata.get("document_id", "")),
                filename=str(metadata.get("filename", "")),
                company=str(metadata.get("company", "")),
                reporting_year=metadata.get("reporting_year"),
                document_type=str(metadata.get("document_type", "other")),
                page_number=metadata.get("page_number"),
                content=content,
                distance=numeric_distance,
                similarity_score=1.0 - numeric_distance,
            )
        )
    return retrieved
