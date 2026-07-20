from __future__ import annotations

from langchain_ollama import ChatOllama

from ...config import settings

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:  # pragma: no cover - exercised before optional dependency install
    ChatGoogleGenerativeAI = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:  # pragma: no cover - exercised before optional dependency install
    ChatOpenAI = None


def create_chat_model(*, max_output_tokens: int | None = None) -> object:
    if settings.model_provider == "gemini":
        if ChatGoogleGenerativeAI is None:
            raise RuntimeError("langchain-google-genai is not installed. Run pip install -r requirements.txt.")
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required when MODEL_PROVIDER=gemini")
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            temperature=settings.gemini_temperature,
            max_output_tokens=max_output_tokens or settings.gemini_max_output_tokens,
        )
    if settings.model_provider == "openrouter":
        if ChatOpenAI is None:
            raise RuntimeError("langchain-openai is not installed. Run pip install -r requirements.txt.")
        if not settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required when MODEL_PROVIDER=openrouter")
        return ChatOpenAI(
            model=settings.openrouter_model,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            temperature=settings.openrouter_temperature,
            max_tokens=max_output_tokens or settings.openrouter_max_output_tokens,
            default_headers={
                "HTTP-Referer": settings.openrouter_site_url,
                "X-Title": settings.openrouter_app_name,
            },
        )
    if settings.model_provider != "ollama":
        raise RuntimeError(f"Unsupported MODEL_PROVIDER: {settings.model_provider}")
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=settings.ollama_temperature,
        num_ctx=settings.ollama_num_ctx,
        top_p=settings.ollama_top_p,
        top_k=settings.ollama_top_k,
    )
