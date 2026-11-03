from abc import ABC, abstractmethod

class ProgressReporterPort(ABC):
    @abstractmethod
    def report(self, phase: str, fraction: float, message: str) -> None:
        pass
