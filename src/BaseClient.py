from abc import ABC, abstractmethod
from typing import Any


class BaseClient(ABC):
    @abstractmethod
    def set_controller(self, controller: Any):
        ...
