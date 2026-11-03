from abc import ABC, abstractmethod

class CancellationToken(ABC):
    @property
    @abstractmethod
    def is_cancelled(self) -> bool:
        pass

    @abstractmethod
    def raise_if_cancelled(self) -> None:
        pass
