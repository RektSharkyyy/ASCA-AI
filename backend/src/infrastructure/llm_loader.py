from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from src.infrastructure.config import config
from src.infrastructure.logging import logger

def get_llm(provider: Optional[str] = None, model_name: Optional[str] = None, temperature: float = 0.1):
    provider = provider or config.env.DEFAULT_LLM_PROVIDER
    provider = provider.lower()

    if provider == "openrouter":
        model = model_name or config.models.get("llm_providers", {}).get("openrouter", {}).get("default_model", "google/gemini-2.5-flash")
        api_key = config.env.OPENROUTER_API_KEY
        if not api_key:
            logger.warning("OPENROUTER_API_KEY is not set in environment!")
        logger.info(f"Loading OpenRouter LLM: {model}")
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=temperature,
            max_tokens=600,
            request_timeout=25.0,
        )

    elif provider == "openai":
        model = model_name or config.models.get("llm_providers", {}).get("openai", {}).get("default_model", "gpt-4o-mini")
        api_key = config.env.OPENAI_API_KEY
        if not api_key:
            logger.warning("OPENAI_API_KEY is not set in environment!")
        logger.info(f"Loading OpenAI LLM: {model}")
        return ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=temperature,
        )

    elif provider == "google":
        model = model_name or config.models.get("llm_providers", {}).get("google", {}).get("default_model", "gemini-2.5-flash")
        api_key = config.env.GOOGLE_API_KEY
        if not api_key:
            logger.warning("GOOGLE_API_KEY is not set in environment!")
        logger.info(f"Loading Google Gemini LLM: {model}")
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
        )

    else:
        raise ValueError(f"Unsupported LLM Provider: {provider}")
