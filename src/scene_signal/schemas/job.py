"""ExtractionJob input contract and parsing."""

from typing import List, Literal, Optional, Union

from pydantic import Field, ValidationError, field_validator

from scene_signal.domain.errors import InvalidJobContractError, UnsupportedContractVersionError
from scene_signal.schemas.common import (
    ID_REGEX,
    VERSION_REGEX,
    AssetRef,
    ChannelContext,
    RelatedAsset,
    SourceTimeline,
    StrictModel,
)
from scene_signal.schemas.versions import check_contract_version


class ExtractionJob(StrictModel):
    contract_version: str = Field(..., pattern=VERSION_REGEX)
    job_id: str = Field(..., pattern=ID_REGEX)
    asset_id: str = Field(..., pattern=ID_REGEX)
    source_kind: Literal["generated", "user_upload", "imported"]
    asset_ref: AssetRef
    extraction_profile: Literal["quick", "standard", "thorough"]
    production_id: Optional[str] = Field(default=None, pattern=ID_REGEX)
    scene_id: Optional[str] = Field(default=None, pattern=ID_REGEX)
    order_index: Optional[int] = Field(default=None, ge=0)
    source_prompt: Optional[str] = Field(default=None, max_length=8000)
    global_prompt: Optional[str] = Field(default=None, max_length=8000)
    channel_context: Optional[ChannelContext] = None
    language: Optional[str] = None
    transcript_ref: Optional[AssetRef] = None
    related_assets: List[RelatedAsset] = Field(default_factory=list)
    source_timeline: Optional[SourceTimeline] = None
    user_preferences_ref: Optional[str] = None
    requested_capabilities: List[str] = Field(default_factory=list)
    provider_config_ref: Optional[str] = None
    rerun_of: Optional[str] = Field(default=None, pattern=ID_REGEX)
    correlation_id: Optional[str] = Field(default=None, pattern=ID_REGEX)

    @field_validator("contract_version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        check_contract_version(v)
        return v


def parse_extraction_job(raw: Union[str, bytes, dict]) -> ExtractionJob:
    try:
        if isinstance(raw, (str, bytes)):
            import json
            data = json.loads(raw)
        else:
            data = raw
        return ExtractionJob.model_validate(data)
    except ValidationError as e:
        fields = {}
        for err in e.errors():
            loc = ".".join(str(l) for l in err["loc"])
            fields[loc] = err["msg"]
        raise InvalidJobContractError(
            message=f"Invalid extraction job contract: {e}",
            details={"fields": fields},
        )
    except UnsupportedContractVersionError:
        raise
    except Exception as e:
        raise InvalidJobContractError(
            message=f"Failed to parse extraction job contract: {e}",
            details={"error": str(e)},
        )
