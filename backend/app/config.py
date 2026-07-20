import os
from dataclasses import dataclass

from dotenv import load_dotenv

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

load_dotenv(BASE_DIR / ".env", override=True)


def _resolve_backend_path(value: str) -> str:
    path = Path(value)
    return str(path if path.is_absolute() else BASE_DIR / path)


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


@dataclass(slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Draftly Backend")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "*")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_service_role_key: str | None = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    linkedin_client_id: str | None = os.getenv("LINKEDIN_CLIENT_ID")
    linkedin_client_secret: str | None = os.getenv("LINKEDIN_CLIENT_SECRET")
    linkedin_redirect_uri: str = os.getenv("LINKEDIN_REDIRECT_URI", "http://127.0.0.1:8001/api/linkedin/callback")
    linkedin_scope: str = os.getenv("LINKEDIN_SCOPE", "openid profile email w_member_social")
    linkedin_api_version: str = os.getenv("LINKEDIN_API_VERSION", "202605")
    linkedin_post_char_limit: int = int(os.getenv("LINKEDIN_POST_CHAR_LIMIT", "3000"))
    linkedin_article_preview_enabled: bool = _env_bool("LINKEDIN_ARTICLE_PREVIEW_ENABLED", "false")
    model_provider: str = os.getenv("MODEL_PROVIDER", "ollama").lower()
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    gemini_temperature: float = float(os.getenv("GEMINI_TEMPERATURE", os.getenv("OLLAMA_TEMPERATURE", "0.3")))
    gemini_max_output_tokens: int = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "2048"))
    gemini_draft_output_tokens: int = int(os.getenv("GEMINI_DRAFT_OUTPUT_TOKENS", "1400"))
    openrouter_api_key: str | None = os.getenv("OPENROUTER_API_KEY")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    openrouter_temperature: float = float(
        os.getenv("OPENROUTER_TEMPERATURE", os.getenv("GEMINI_TEMPERATURE", "0.3"))
    )
    openrouter_max_output_tokens: int = int(
        os.getenv("OPENROUTER_MAX_OUTPUT_TOKENS", os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "2048"))
    )
    openrouter_site_url: str = os.getenv("OPENROUTER_SITE_URL", os.getenv("FRONTEND_URL", "http://127.0.0.1:5173"))
    openrouter_app_name: str = os.getenv("OPENROUTER_APP_NAME", os.getenv("APP_NAME", "Draftly Backend"))
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_temperature: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.3"))
    ollama_num_ctx: int = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
    ollama_top_p: float = float(os.getenv("OLLAMA_TOP_P", "0.9"))
    ollama_top_k: int = int(os.getenv("OLLAMA_TOP_K", "40"))
    web_user_agent: str = os.getenv(
        "WEB_USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    )
    web_search_max_results: int = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "5"))
    web_fetch_max_sources: int = int(os.getenv("WEB_FETCH_MAX_SOURCES", "3"))
    web_extract_char_limit: int = int(os.getenv("WEB_EXTRACT_CHAR_LIMIT", "4000"))
    tavily_api_key: str | None = os.getenv("TAVILY_API_KEY")
    tavily_search_depth: str = os.getenv("TAVILY_SEARCH_DEPTH", "basic")
    rag_enabled: bool = _env_bool("RAG_ENABLED", os.getenv("AG_ENABLED", "false"))
    rag_debug: bool = _env_bool("RAG_DEBUG", "false")
    rag_provider: str = os.getenv("RAG_PROVIDER", "ollama").lower()
    rag_embed_model: str = os.getenv("RAG_EMBED_MODEL", "nomic-embed-text")
    rag_embedding_timeout_seconds: float = float(os.getenv("RAG_EMBEDDING_TIMEOUT_SECONDS", "8"))
    rag_top_k: int = _env_int("RAG_TOP_K", 2)
    rag_chunk_size: int = _env_int("RAG_CHUNK_SIZE", 420)
    rag_chunk_overlap: int = _env_int("RAG_CHUNK_OVERLAP", 80)
    rag_source_char_limit: int = _env_int("RAG_SOURCE_CHAR_LIMIT", 360)
    rag_quick_top_k: int = _env_int("RAG_QUICK_TOP_K", 1)
    rag_moderate_top_k: int = _env_int("RAG_MODERATE_TOP_K", rag_top_k)
    rag_deep_top_k: int = _env_int("RAG_DEEP_TOP_K", 3)
    rag_quick_chunk_size: int = _env_int("RAG_QUICK_CHUNK_SIZE", 320)
    rag_moderate_chunk_size: int = _env_int("RAG_MODERATE_CHUNK_SIZE", rag_chunk_size)
    rag_deep_chunk_size: int = _env_int("RAG_DEEP_CHUNK_SIZE", 520)
    rag_quick_chunk_overlap: int = _env_int("RAG_QUICK_CHUNK_OVERLAP", 40)
    rag_moderate_chunk_overlap: int = _env_int("RAG_MODERATE_CHUNK_OVERLAP", rag_chunk_overlap)
    rag_deep_chunk_overlap: int = _env_int("RAG_DEEP_CHUNK_OVERLAP", 100)
    rag_quick_source_char_limit: int = _env_int("RAG_QUICK_SOURCE_CHAR_LIMIT", 260)
    rag_moderate_source_char_limit: int = _env_int("RAG_MODERATE_SOURCE_CHAR_LIMIT", rag_source_char_limit)
    rag_deep_source_char_limit: int = _env_int("RAG_DEEP_SOURCE_CHAR_LIMIT", 520)
    rag_evaluation_log_path: str = _resolve_backend_path(
        os.getenv("RAG_EVALUATION_LOG_PATH", "data/rag_evaluation_log.txt")
    )
    gemini_image_api_key: str | None = (
        os.getenv("GEMINI_API_KEY_2")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )
    image_generation_provider: str = os.getenv("IMAGE_GENERATION_PROVIDER", "gemini").lower()
    openrouter_image_model: str = os.getenv("OPENROUTER_IMAGE_MODEL", "")
    openrouter_image_size: str = os.getenv("OPENROUTER_IMAGE_SIZE", "")
    openrouter_image_aspect_ratio: str = os.getenv("OPENROUTER_IMAGE_ASPECT_RATIO", "")
    gemini_image_model: str = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")
    gemini_image_aspect_ratio: str = os.getenv("GEMINI_IMAGE_ASPECT_RATIO", "16:9")
    gemini_image_size: str = os.getenv("GEMINI_IMAGE_SIZE", "1K")
    image_generation_timeout_seconds: float = float(os.getenv("IMAGE_GENERATION_TIMEOUT_SECONDS", "60"))
    chat_recent_messages_limit: int = int(os.getenv("CHAT_RECENT_MESSAGES_LIMIT", "3"))
    chat_summary_char_limit: int = int(os.getenv("CHAT_SUMMARY_CHAR_LIMIT", "350"))
    chat_message_context_char_limit: int = int(os.getenv("CHAT_MESSAGE_CONTEXT_CHAR_LIMIT", "160"))
    agent_plan_timeout_seconds: float = float(os.getenv("AGENT_PLAN_TIMEOUT_SECONDS", "25"))
    agent_search_query_timeout_seconds: float = float(os.getenv("AGENT_SEARCH_QUERY_TIMEOUT_SECONDS", "15"))
    agent_search_timeout_seconds: float = float(os.getenv("AGENT_SEARCH_TIMEOUT_SECONDS", "25"))
    agent_fetch_timeout_seconds: float = float(os.getenv("AGENT_FETCH_TIMEOUT_SECONDS", "20"))
    agent_source_context_timeout_seconds: float = float(
        os.getenv("AGENT_SOURCE_CONTEXT_TIMEOUT_SECONDS", os.getenv("AGENT_SOURCE_SUMMARY_TIMEOUT_SECONDS", "25"))
    )
    agent_response_chunk_timeout_seconds: float = float(os.getenv("AGENT_RESPONSE_CHUNK_TIMEOUT_SECONDS", "30"))
    agent_conversation_summary_timeout_seconds: float = float(
        os.getenv("AGENT_CONVERSATION_SUMMARY_TIMEOUT_SECONDS", "20")
    )


settings = Settings()
