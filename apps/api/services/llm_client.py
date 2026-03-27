"""LLM client factory for multi-provider abstraction."""

from core.config import settings


def get_llm_client():
    """Return a LangChain-compatible chat model based on LLM_PROVIDER setting.

    Returns:
        A LangChain ChatModel instance compatible with the current provider.

    Raises:
        ValueError: If the provider is unknown or API key is missing.
    """
    provider = settings.llm_provider.lower()

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")
        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=0,
        )
    elif provider == "groq":
        from langchain_groq import ChatGroq

        if not settings.groq_api_key:
            raise ValueError("Groq API key not configured")
        return ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0,
        )
    elif provider == "siliconflow":
        from langchain_openai import ChatOpenAI

        if not settings.siliconflow_api_key:
            raise ValueError("SiliconFlow API key not configured")
        return ChatOpenAI(
            model=settings.siliconflow_model,
            api_key=settings.siliconflow_api_key,
            base_url=settings.siliconflow_base_url,
            temperature=0,
        )
    elif provider == "fireworks":
        from langchain_openai import ChatOpenAI

        if not settings.fireworks_api_key:
            raise ValueError("Fireworks API key not configured")
        return ChatOpenAI(
            model=settings.fireworks_model,
            api_key=settings.fireworks_api_key,
            base_url=settings.fireworks_base_url,
            temperature=0,
        )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


def get_direct_client():
    """Return a direct client for provider-specific APIs (used by LLM processor).

    Returns:
        A provider-specific client instance for direct API calls.

    Raises:
        ValueError: If the provider is unknown or API key is missing.
    """
    provider = settings.llm_provider.lower()

    if provider == "anthropic":
        from anthropic import Anthropic

        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")
        return Anthropic(api_key=settings.anthropic_api_key)
    elif provider == "groq":
        from groq import Groq

        if not settings.groq_api_key:
            raise ValueError("Groq API key not configured")
        return Groq(api_key=settings.groq_api_key)
    elif provider == "siliconflow":
        from openai import OpenAI

        if not settings.siliconflow_api_key:
            raise ValueError("SiliconFlow API key not configured")
        return OpenAI(
            api_key=settings.siliconflow_api_key,
            base_url=settings.siliconflow_base_url,
        )
    elif provider == "fireworks":
        from openai import OpenAI

        if not settings.fireworks_api_key:
            raise ValueError("Fireworks API key not configured")
        return OpenAI(
            api_key=settings.fireworks_api_key,
            base_url=settings.fireworks_base_url,
        )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
