"""
LLM Factory for creating and managing different LLM providers.
Supports OpenAI, Anthropic, and Google LLMs.
"""

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.core.config import settings


class LLMFactory:
    """Factory class for creating LLM instances."""

    @staticmethod
    def create_llm(
        provider: str,
        model: str | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> BaseChatModel:
        """
        Create an LLM instance based on the provider.

        Args:
            provider: LLM provider name (openai, anthropic, google)
            model: Model name (optional, uses default from config)
            temperature: Temperature setting (optional, uses default from config)
            **kwargs: Additional arguments to pass to the LLM

        Returns:
            BaseChatModel: Configured LLM instance

        Raises:
            ValueError: If provider is not supported
        """
        config = settings.get_llm_config(provider)

        # Override with provided values
        if model:
            config["model"] = model
        if temperature is not None:
            config["temperature"] = temperature

        # Merge additional kwargs
        config.update(kwargs)

        if provider == "openai":
            return ChatOpenAI(
                api_key=config["api_key"],
                model=config["model"],
                temperature=config["temperature"],
                max_tokens=config.get("max_tokens"),
                request_timeout=settings.agent_timeout,
            )

        elif provider == "anthropic":
            return ChatAnthropic(
                api_key=config["api_key"],
                model=config["model"],
                temperature=config["temperature"],
                max_tokens=config.get("max_tokens"),
                timeout=settings.agent_timeout,
            )

        elif provider == "google":
            return ChatGoogleGenerativeAI(
                google_api_key=config["api_key"],
                model=config["model"],
                temperature=config["temperature"],
                timeout=settings.agent_timeout,
            )

        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    @staticmethod
    def create_agent_llms() -> dict[str, BaseChatModel]:
        """
        Create LLM instances for all agents based on configuration.

        Returns:
            dict: Dictionary mapping agent names to their LLM instances
        """
        return {
            "orchestrator": LLMFactory.create_llm(
                provider=settings.orchestrator_llm_provider,
                model=settings.orchestrator_model,
            ),
            "schema_validator": LLMFactory.create_llm(
                provider=settings.schema_validator_llm_provider,
                model=settings.schema_validator_model,
            ),
            "architect": LLMFactory.create_llm(
                provider=settings.architect_llm_provider,
                model=settings.architect_model,
            ),
            "code_generator": LLMFactory.create_llm(
                provider=settings.code_generator_llm_provider,
                model=settings.code_generator_model,
            ),
            "validator": LLMFactory.create_llm(
                provider=settings.validator_llm_provider,
                model=settings.validator_model,
            ),
        }

    @staticmethod
    def create_default_llm() -> BaseChatModel:
        """
        Create a default LLM instance.

        Returns:
            BaseChatModel: Default LLM configured from settings
        """
        return LLMFactory.create_llm(
            provider=settings.default_llm_provider,
        )
