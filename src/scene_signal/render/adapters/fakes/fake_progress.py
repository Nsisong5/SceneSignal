from scene_signal.render.ports.progress import ProgressReporterPort

class FakeProgressReporter(ProgressReporterPort):
    def __init__(self) -> None:
        self.reports: list[tuple[str, float, str]] = []

    def report(self, phase: str, fraction: float, message: str) -> None:
        self.reports.append((phase, fraction, message))
