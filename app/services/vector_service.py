import json
import logging
import os
import time
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.config.settings import get_settings
from langchain_google_genai._common import GoogleGenerativeAIError

from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorService:
    def __init__(self, gemini_service: GeminiService):
        self.gemini_service = gemini_service
        Path(settings.faiss_index_dir).mkdir(parents=True, exist_ok=True)

    def _split_documents(self, documents: list[Document]) -> list[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        return splitter.split_documents(documents)

    def _dataset_index_path(self, dataset_id: UUID) -> str:
        return os.path.join(settings.faiss_index_dir, str(dataset_id))

    async def _embed_documents_in_batches(self, documents: list[Document]):
        text_embeddings: list[tuple[str, list[float]]] = []
        selected_model_name: str | None = None
        selected_embedding_client = None

        for start in range(0, len(documents), settings.batch_embedding_size):
            batch = documents[start : start + settings.batch_embedding_size]
            texts = [document.page_content for document in batch]
            vectors = None
            last_exception: Exception | None = None

            for model_name in settings.gemini_embedding_candidate_models:
                try:
                    embedding_client = self.gemini_service.get_embedding_client_for_model(model_name)
                    vectors = await run_in_threadpool(embedding_client.embed_documents, texts)
                    selected_model_name = model_name
                    selected_embedding_client = embedding_client
                    break
                except GoogleGenerativeAIError as exc:
                    last_exception = exc
                    logger.warning("Embedding failed for model %s: %s", model_name, exc)
                except Exception as exc:
                    last_exception = exc
                    logger.exception("Unexpected embedding error for model %s", model_name, exc_info=exc)

            if vectors is None or selected_embedding_client is None or selected_model_name is None:
                raise self.gemini_service.build_embedding_exception(last_exception)

            text_embeddings.extend(zip(texts, vectors))

        return selected_embedding_client, text_embeddings, selected_model_name

    async def create_index(self, dataset_id: UUID, documents: list[Document]) -> tuple[str, int, int, float, str]:
        chunked_documents = self._split_documents(documents)
        start = time.perf_counter()
        embeddings, text_embeddings, model_name = await self._embed_documents_in_batches(chunked_documents)
        vector_store = await run_in_threadpool(
            FAISS.from_embeddings,
            text_embeddings,
            embeddings,
            [document.metadata for document in chunked_documents],
        )
        index_path = self._dataset_index_path(dataset_id)
        await run_in_threadpool(vector_store.save_local, index_path)
        processing_time_ms = (time.perf_counter() - start) * 1000

        metadata_path = os.path.join(index_path, "chunks.json")
        Path(index_path).mkdir(parents=True, exist_ok=True)
        with open(metadata_path, "w", encoding="utf-8") as file_pointer:
            json.dump(
                [
                    {
                        "page_content": document.page_content,
                        "metadata": document.metadata,
                    }
                    for document in chunked_documents
                ],
                file_pointer,
                ensure_ascii=True,
                indent=2,
            )

        query_vector = await run_in_threadpool(embeddings.embed_query, "dimension-check")
        embedding_dimension = len(query_vector)
        return index_path, len(chunked_documents), embedding_dimension, processing_time_ms, model_name

    async def retrieve(self, dataset_id: UUID, query: str, top_k: int | None = None) -> list[Document]:
        index_path = self._dataset_index_path(dataset_id)
        if not os.path.exists(index_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vector index not found for dataset.",
            )

        embeddings = self.gemini_service.get_embedding_client()
        vector_store = await run_in_threadpool(
            FAISS.load_local,
            index_path,
            embeddings,
            allow_dangerous_deserialization=True,
        )
        docs = await run_in_threadpool(
            vector_store.similarity_search,
            query,
            top_k or settings.retrieval_top_k,
        )
        return docs
