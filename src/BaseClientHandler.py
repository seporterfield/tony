from abc import ABC, abstractmethod
from typing import Any, List

from src.BaseClient import BaseClient
from src.ServerMsg import ServerMsg


class BaseClientHandler(ABC):
    def __init__(
        self,
        client: BaseClient,
        typing_time: int,
    ) -> None:
        self.client: BaseClient = client
        self.typing_time = typing_time
        self.chat_history: List[Any] = []

    def set_controller(self, controller: Any):
        self.client.set_controller(controller)

    @abstractmethod
    def on_ready(self):
        ...

    @abstractmethod
    def on_resumed(self, chat_history: List[ServerMsg]) -> Any:
        ...

    @abstractmethod
    def on_message(self, message: Any) -> Any:
        ...

    @abstractmethod
    async def get_chat_history(self, message: Any) -> List[ServerMsg]:
        ...

    @abstractmethod
    def get_message_channel(self, message: Any) -> Any:
        ...

    @abstractmethod
    def message_channel(self, message_text: str, channel: Any = None):
        ...

    @abstractmethod
    def connect(self, token: str | None = None):
        ...

    @abstractmethod
    def should_reply_to_msg(self, message):
        ...
