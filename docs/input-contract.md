# SceneSignal — Input Contract (`ExtractionJob`)

The `ExtractionJob` contract specifies how an extraction job is requested. It requires:
- `contract_version`: `"1.0"`
- `job_id`: string matching `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`
- `asset_id`: string
- `source_kind`: `generated` | `user_upload` | `imported`
- `asset_ref`: object with `scheme`, `uri`, and optional sha256 `checksum`
- `extraction_profile`: `quick` | `standard` | `thorough`

No technical metadata (duration, resolution, codecs) is accepted in the input contract because SceneSignal inspects the media itself.
