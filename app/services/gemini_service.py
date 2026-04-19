import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, status
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_google_genai._common import GoogleGenerativeAIError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class GeminiClients:
    chat: Optional[ChatGoogleGenerativeAI] = None
    embeddings: Optional[GoogleGenerativeAIEmbeddings] = None
    chat_model_name: Optional[str] = None
    embedding_model_name: Optional[str] = None


class GeminiService:
    def __init__(self):
        if not settings.google_api_key:
            logger.warning("GOOGLE_API_KEY is not configured; Gemini calls will fail until it is set.")
        self.clients = GeminiClients()

    def _ensure_api_key(self) -> None:
        if not settings.google_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GOOGLE_API_KEY is not configured.",
            )

    def _build_chat_client(self, model_name: str | None = None) -> ChatGoogleGenerativeAI:
        self._ensure_api_key()
        return ChatGoogleGenerativeAI(
            model=model_name or settings.gemini_chat_model,
            google_api_key=settings.google_api_key,
            temperature=settings.llm_temperature,
            timeout=settings.gemini_timeout_seconds,
            max_output_tokens=settings.llm_max_output_tokens,
        )

    def _build_embedding_client(self, model_name: str | None = None) -> GoogleGenerativeAIEmbeddings:
        self._ensure_api_key()
        return GoogleGenerativeAIEmbeddings(
            model=model_name or settings.gemini_embedding_model,
            google_api_key=settings.google_api_key,
        )

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(settings.gemini_max_retries))
    def get_embedding_client(self) -> GoogleGenerativeAIEmbeddings:
        if self.clients.embeddings is None:
            self.clients.embeddings = self._build_embedding_client()
            self.clients.embedding_model_name = settings.gemini_embedding_model
        return self.clients.embeddings

    def get_embedding_client_for_model(self, model_name: str) -> GoogleGenerativeAIEmbeddings:
        if self.clients.embeddings is not None and self.clients.embedding_model_name == model_name:
            return self.clients.embeddings

        embedding_client = self._build_embedding_client(model_name)
        self.clients.embeddings = embedding_client
        self.clients.embedding_model_name = model_name
        return embedding_client

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(settings.gemini_max_retries))
    def get_chat_client(self) -> ChatGoogleGenerativeAI:
        if self.clients.chat is None:
            self.clients.chat = self._build_chat_client()
            self.clients.chat_model_name = settings.gemini_chat_model
        return self.clients.chat

    def get_chat_client_for_model(self, model_name: str) -> ChatGoogleGenerativeAI:
        if self.clients.chat is not None and self.clients.chat_model_name == model_name:
            return self.clients.chat

        chat_client = self._build_chat_client(model_name)
        self.clients.chat = chat_client
        self.clients.chat_model_name = model_name
        return chat_client

    async def generate_answer(self, prompt: str) -> str:
        last_exception: Exception | None = None

        for model_name in settings.gemini_chat_candidate_models:
            try:
                response = await self.get_chat_client_for_model(model_name).ainvoke(prompt)
                return response.content if isinstance(response.content, str) else str(response.content)
            except Exception as exc:
                last_exception = exc
                logger.warning("Chat generation failed for model %s: %s", model_name, exc)

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "LLM provider error while generating response. "
                f"Attempted chat models: {', '.join(settings.gemini_chat_candidate_models)}"
            ),
        ) from last_exception

    def build_embedding_exception(self, last_exception: Exception | None) -> HTTPException:
        exception = HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Embedding provider error. Verify GOOGLE_API_KEY and GEMINI_EMBEDDING_MODEL. "
                f"Attempted models: {', '.join(settings.gemini_embedding_candidate_models)}"
            ),
        )
        if last_exception is not None:
            exception.__cause__ = last_exception
        return exception
