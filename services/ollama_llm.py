from typing import List, Dict, Any, Iterator

from ollama import Client, ChatResponse


class OllamaClient(object):
    history: List[Dict[str, Any]]

    def __init__(self, url: str = "http://localhost:11434",
                 api_key: str = "",
                 system_prompt: str = None,
                 max_history: int = 10):
        kwargs = {}
        if api_key:
            kwargs["headers"]={'Authorization': 'Bearer ' + api_key}

        self.client = Client(host=url, **kwargs)
        self.history = []

        self.system_prompt = system_prompt
        self.max_history = max_history


    def history_add(self, content: str, role: str="assistant", **kwargs):
        msg = {"role": role, "content": content}
        msg.update(kwargs)
        self.history.append(msg)

    def request(self, model: str, message:str = None, **kwargs) -> ChatResponse:
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