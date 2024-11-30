from typing import Any, Dict, Iterator, List, Optional

import requests
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.messages.ai import UsageMetadata
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field


class ChatMistralNemo(BaseChatModel):
    """A custom chat model that interacts with the Mistral-Nemo API.

    Example:
        .. code-block:: python

            model = ChatMistralNemo(
                base_url="<completions endpoint>",
                api_key="<api key>",
                model_name="mistral-nemo-instruct-2407",
            )
            result = model.invoke([HumanMessage(content="Как дела?")])
            result = model.batch([[HumanMessage(content="Как дела?")],
                                 [HumanMessage(content="Что новенького?")]])
    """

    base_url: str
    """The base URL of the Mistral-Nemo API."""
    api_key: str
    """API key for authenticating with the Mistral-Nemo API."""
    model_name: Optional[str] = Field(
        alias="model", default="mistral-nemo-instruct-2407"
    )
    """The name of the model."""
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[int] = None
    stop: Optional[List[str]] = None

    classes_map: Dict[str, str] = {
        "system": "system",
        "human": "user",
        "ai": "assistant",
    }

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response from the model using the Mistral-Nemo API."""
        headers = {"Authorization": self.api_key}

        body = {
            "model": self.model_name,
            "messages": [
                *[
                    {"role": self.classes_map[message.type], "content": message.content}
                    for message in messages
                ],
            ],
            "max_tokens": self.max_tokens or 1000,
            "temperature": self.temperature or 0.3,
        }

        response = requests.post(
            f"{self.base_url}", headers=headers, json=body, timeout=self.timeout
        )

        if response.status_code != 200:
            raise ValueError(
                f"API call failed with status code {response.status_code}: {response.text}"
            )

        result = response.json()
        choice = result["choices"][0]
        content = choice["message"]["content"]

        usage = result.get("usage", {})
        response_metadata = {
            "provider": result.get("provider"),
            "model": result.get("model"),
            "request_id": result.get("request_id"),
            "response_id": result.get("response_id"),
        }

        usage_metadata = UsageMetadata(
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

        message = AIMessage(
            content=content,
            response_metadata=response_metadata,
            usage_metadata=usage_metadata,
        )

        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Stream responses from the model (not supported in this API)."""
        raise NotImplementedError("Streaming is not supported for this model.")

    @property
    def _llm_type(self) -> str:
        """Get the type of language model used by this chat model."""
        return "mistral-nemo-chat"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return a dictionary of identifying parameters."""
        return {
            "model_name": self.model_name,
            "base_url": self.base_url,
        }
