"""Contract and schema version checking."""

from scene_signal.domain.errors import UnsupportedContractVersionError

SUPPORTED_CONTRACT_VERSION = "1.0"
SUPPORTED_SCHEMA_VERSION = "1.0"


def check_contract_version(version: str) -> None:
    if version != SUPPORTED_CONTRACT_VERSION:
        raise UnsupportedContractVersionError(
            f"Unsupported contract version '{version}'. Supported version is '{SUPPORTED_CONTRACT_VERSION}'.",
            details={"version": version, "supported": SUPPORTED_CONTRACT_VERSION},
        )


def check_schema_version(version: str) -> None:
    if version != SUPPORTED_SCHEMA_VERSION:
        raise UnsupportedContractVersionError(
            f"Unsupported schema version '{version}'. Supported version is '{SUPPORTED_SCHEMA_VERSION}'.",
            details={"version": version, "supported": SUPPORTED_SCHEMA_VERSION},
        )
