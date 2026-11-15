from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import Settings


class LLMConfigurationError(RuntimeError):
    """Raised when the selected LLM provider is missing configuration."""


def create_chat_model(settings: Settings) -> BaseChatModel:
    provider = settings.llm_provider.strip().lower()
    model_name = settings.llm_model.strip()
    if not model_name:
        raise LLMConfigurationError("Set LLM_MODEL in the environment")

    if provider == "openai":
        if not settings.openai_api_key:
            raise LLMConfigurationError("Set OPENAI_API_KEY to use the OpenAI chat provider")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model_name, api_key=settings.openai_api_key)

    if provider == "groq":
        if not settings.groq_api_key:
            raise LLMConfigurationError("Set GROQ_API_KEY to use the Groq chat provider")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name,
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise LLMConfigurationError(
                "Set ANTHROPIC_API_KEY to use the Anthropic chat provider"
            )
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model_name, anthropic_api_key=settings.anthropic_api_key)

    raise LLMConfigurationError(
        "Unsupported LLM_PROVIDER. Supported values are 'openai', 'anthropic', and 'groq'."
    )
