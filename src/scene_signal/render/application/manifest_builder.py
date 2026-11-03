from typing import Any
from scene_signal.render.contracts.manifest import RenderManifest
from scene_signal.render.contracts.render_request import RenderRequest
from scene_signal.render.domain.execution_plan import RenderExecutionPlan
from scene_signal.render.contracts.canonical import plan_fingerprint, request_hash

class ManifestBuilder:
    @staticmethod
    def build(
        request: RenderRequest,
        execution_plan: RenderExecutionPlan,
        outcome: Literal["succeeded", "failed", "cancelled"] if False else str,
        phase_reached: str,
        renderer_meta: dict[str, Any],
        sources: list[dict[str, Any]],
        postconditions: list[Any],
        warnings: list[Any],
        error: Any | None = None,
        commands: list[dict[str, Any]] = None,
    ) -> RenderManifest:
        pf = plan_fingerprint(request.plan.model_dump())
        rh = request_hash(request.model_dump())

        segments_data = [s.model_dump() for s in execution_plan.segments]
        transitions_data = [t.model_dump() for t in request.plan.timeline.transitions]

        return RenderManifest(
            render_job_id=request.render_job_id,
            plan_id=request.plan.plan_id,
            plan_fingerprint=pf,
            request_hash=rh,
            production_id=request.plan.production_id,
            outcome=outcome,
            phase_reached=phase_reached,
            profile=request.plan.output_profile.model_dump(),
            renderer=renderer_meta,
            strategy="normalize_then_assemble",
            limits_applied={},
            sources=sources,
            segments=segments_data,
            transitions=transitions_data,
            postconditions=postconditions,
            warnings=warnings,
            error=error,
            commands=commands or [],
        )
