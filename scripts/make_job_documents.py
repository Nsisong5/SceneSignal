"""Script to generate test job documents for fixtures."""

import json
from pathlib import Path


def generate_job_documents() -> None:
    out_dir = Path("tests/fixtures/jobs")
    out_dir.mkdir(parents=True, exist_ok=True)

    fixtures = [
        "clip_5s_landscape_audio.mp4",
        "multishot_12s.mp4",
        "clip_30s_continuous.mp4",
        "black_transition_9s.mp4",
        "clip_portrait_5s.mp4",
    ]

    source_kinds = ["generated", "user_upload", "imported"]

    for fix in fixtures:
        base_name = Path(fix).stem
        for sk in source_kinds:
            job = {
                "contract_version": "1.0",
                "job_id": f"job-{base_name}-{sk[:3]}",
                "asset_id": f"asset-{base_name}",
                "source_kind": sk,
                "asset_ref": {"scheme": "file", "uri": fix},
                "extraction_profile": "standard",
                "source_prompt": f"Synthetic test video {fix}",
            }
            p = out_dir / f"{base_name}.{sk}.json"
            p.write_text(json.dumps(job, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("Job documents generated successfully under tests/fixtures/jobs/.")


if __name__ == "__main__":
    generate_job_documents()
