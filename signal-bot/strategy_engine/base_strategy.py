from abc import ABC, abstractmethod
from collections import deque
from loguru import logger


class BaseStrategy(ABC):
    name: str = ""
    game: str = ""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.max_gale: int = self.config.get("max_gale", 2)
        self._history: deque = deque(maxlen=50)
        self._pending_gale: int | None = None  # nível de gale atual se entrada aberta

    @abstractmethod
    def should_enter(self, history: list) -> tuple[bool, str]:
        """
        Analisa o histórico e decide se deve entrar.
        Retorna (deve_entrar, o_que_apostar).
        """
        ...

    @abstractmethod
    def resolve(self, result: dict, entry: str) -> str:
        """
        Dado o resultado e a entrada feita, retorna 'win' ou 'loss'.
        """
        ...

    def add_to_history(self, result: dict):
        self._history.append(result)

    def get_history(self) -> list:
        return list(self._history)

    def streak(self, history: list, key: str, value) -> int:
        """Conta quantos resultados consecutivos iguais no final do histórico."""
        count = 0
        for item in reversed(history):
            if item.get(key) == value:
                count += 1
            else:
                break
        return count
