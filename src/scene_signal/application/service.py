"""Scene intelligence extraction service facade."""

from pathlib import Path
from typing import List, Optional, Union
from scene_signal.domain.policies import Settings
from scene_signal.schemas.job import ExtractionJob, parse_extraction_job
from scene_signal.schemas.result import JobResult
from scene_signal.application.pipeline import ExtractionPipeline, PipelinePorts


class SceneIntelligenceService:
    def __init__(self, ports: PipelinePorts, settings: Optional[Settings] = None, allowed_roots: Optional[List[Path]] = None):
        self.pipeline = ExtractionPipeline(ports=ports, settings=settings, allowed_roots=allowed_roots)

    def extract(self, job: Union[ExtractionJob, dict, str, bytes]) -> JobResult:
        if isinstance(job, ExtractionJob):
            extracted_job = job
        else:
            extracted_job = parse_extraction_job(job)
        return self.pipeline.run(extracted_job)
