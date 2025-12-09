"""
Base Agent class that all specialized agents inherit from.
Provides common functionality for agent initialization, execution, and error handling.
"""

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logger import get_logger


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.

    Attributes:
        name: Agent name
        llm: Language model instance
        logger: Logger instance
        max_retries: Maximum number of retry attempts
        system_prompt: System prompt template
    """

    def __init__(
        self,
        name: str,
        llm: BaseChatModel,
        system_prompt: str | None = None,
        max_retries: int | None = None,
    ):
        """
        Initialize the base agent.

        Args:
            name: Agent name
            llm: Language model instance
            system_prompt: System prompt template (optional)
            max_retries: Maximum retry attempts (optional, uses config default)
        """
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.max_retries = max_retries or settings.agent_max_retries
        self.logger = get_logger(f"agent.{name}")

        self.logger.info(f"Agent '{name}' initialized")

    @abstractmethod
    def _default_system_prompt(self) -> str:
        """
        Define the default system prompt for this agent.

        Returns:
            str: System prompt template
        """
        pass

    @abstractmethod
    async def execute(self, input_data: Any) -> Any:
        """
        Execute the agent's main task.

        Args:
            input_data: Input data for the agent

        Returns:
            Any: Agent's output

        Raises:
            Exception: If execution fails
        """
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def invoke_llm(
        self,
        messages: list[BaseMessage] | str,
        **kwargs: Any,
    ) -> str:
        """
        Invoke the LLM with retry logic.

        Args:
            messages: List of messages or a single string message
            **kwargs: Additional arguments for LLM invocation

        Returns:
            str: LLM response content

        Raises:
            Exception: If all retry attempts fail
        """
        try:
            # Convert string to messages if needed
            if isinstance(messages, str):
                messages = [
                    SystemMessage(content=self.system_prompt),
                    HumanMessage(content=messages),
                ]

            self.logger.debug(f"Invoking LLM for agent '{self.name}'")

            # Invoke LLM
            response = await self.llm.ainvoke(messages, **kwargs)

            self.logger.debug(f"LLM response received for agent '{self.name}'")

            return response.content

        except Exception as e:
            self.logger.error(f"LLM invocation failed for agent '{self.name}': {str(e)}")
            raise

    def create_messages(self, user_message: str, context: dict | None = None) -> list[BaseMessage]:
        """
        Create a list of messages for LLM invocation.

        Args:
            user_message: User's message content
            context: Additional context to include in system prompt

        Returns:
            list[BaseMessage]: List of formatted messages
        """
        # Format system prompt with context if provided
        system_content = self.system_prompt
        if context:
            system_content = system_content.format(**context)

        return [
            SystemMessage(content=system_content),
            HumanMessage(content=user_message),
        ]

    async def validate_input(self, input_data: Any) -> bool:
        """
        Validate input data before execution.

        Args:
            input_data: Input data to validate

        Returns:
            bool: True if valid, False otherwise
        """
        # Default implementation - can be overridden by subclasses
        return True

    async def validate_output(self, output_data: Any) -> bool:
        """
        Validate output data after execution.

        Args:
            output_data: Output data to validate

        Returns:
            bool: True if valid, False otherwise
        """
        # Default implementation - can be overridden by subclasses
        return True

    def log_execution_start(self, input_data: Any) -> None:
        """Log the start of agent execution."""
        self.logger.info(f"Agent '{self.name}' execution started")
        if settings.debug:
            self.logger.debug(f"Input data: {input_data}")

    def log_execution_end(self, output_data: Any) -> None:
        """Log the end of agent execution."""
        self.logger.info(f"Agent '{self.name}' execution completed")
        if settings.debug:
            self.logger.debug(f"Output data: {output_data}")

    def log_error(self, error: Exception) -> None:
        """Log an error during agent execution."""
        self.logger.error(f"Agent '{self.name}' execution failed: {str(error)}", exc_info=True)

    async def run(self, input_data: Any) -> Any:
        """
        Main entry point for agent execution with logging and validation.

        Args:
            input_data: Input data for the agent

        Returns:
            Any: Agent's output

        Raises:
            ValueError: If input validation fails
            Exception: If execution fails
        """
        try:
            # Log start
            self.log_execution_start(input_data)

            # Validate input
            if not await self.validate_input(input_data):
                raise ValueError(f"Invalid input data for agent '{self.name}'")

            # Execute agent logic
            output_data = await self.execute(input_data)

            # Validate output
            if not await self.validate_output(output_data):
                raise ValueError(f"Invalid output data from agent '{self.name}'")

            # Log end
            self.log_execution_end(output_data)

            return output_data

        except Exception as e:
            self.log_error(e)
            raise
