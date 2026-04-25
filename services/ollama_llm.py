from typing import List, Dict, Any, Iterator

from ollama import Client, ChatResponse


class OllamaClient(object):
    """
    Client for interacting with an Ollama-compatible chat API.
    """
    history: List[Dict[str, Any]]

    def __init__(self, url: str = "http://localhost:11434",
                 api_key: str = "",
                 system_prompt: str = None,
                 max_history: int = 10):
        """
        Construct an OllamaClient.

        :param url: Base URL of the Ollama API server.
        :param api_key: Optional API key for authentication.
        :param system_prompt: Optional system prompt to prepend to every request.
        :param max_history: Maximum number of messages to retain in the conversation history.
        """
        kwargs = {}
        if api_key:
            kwargs["headers"] = {"Authorization": "Bearer " + api_key}

        self.client = Client(host=url, **kwargs)
        self.history = []

        self.system_prompt = system_prompt
        self.max_history = max_history

    def history_add(self, content: str, role: str = "assistant", **kwargs):
        """
        Append a message to the conversation history.

        :param content: The text content of the message.
        :param role: The role of the message sender (e.g. "assistant", "user").
        """
        msg = {"role": role, "content": content}
        msg.update(kwargs)
        self.history.append(msg)

    def request(self, model: str, message: str = None, **kwargs) -> ChatResponse:
        """
        Send a chat request to the Ollama API.

        Automatically manages conversation history and optional system prompt.

        :param model: Name of the model to use for the chat.
        :param message: Optional user message to add before sending the request.
        :param kwargs: Additional keyword arguments forwarded to the underlying client.
        :return: The chat response returned by the API.
        """
        if message is not None:
            self.history_add(content=message, role="user")

        history = self.history
        if self.max_history and len(history) > self.max_history:
            history = history[: self.max_history]

        if self.system_prompt is not None:
            history = [{
                "role": "system",
                "content": self.system_prompt,
            }] + history

        response = self.client.chat(model=model, messages=history, **kwargs)
        response_message = response.message
        self.history_add(
            content=response_message.content,
            role=response_message.role
        )
        return response