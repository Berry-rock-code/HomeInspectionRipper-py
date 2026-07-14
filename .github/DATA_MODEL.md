# Data Model

All models live in `inspection_ripper/models.py` and are Pydantic `BaseModel` subclasses.

## PropertyInfo

Basic property details extracted by the demographics agent.

| Field | Type | Description |
|-------|------|-------------|
| `address` | `str` | Full property address |
| `bedrooms` | `int` | Number of bedrooms |
| `bathrooms` | `int` | Number of bathrooms |
| `square_footage` | `int` | Total square footage |
| `year_built` | `int` | Year the property was built |

## DamageCategory

A single grouped issue found in the report.

| Field | Type | Description |
|-------|------|-------------|
| `category` | `str` | `foundation` \| `roof` \| `hvac` \| `electrical` \| `plumbing` \| `other` |
| `severity` | `str` | `critical` \| `high` \| `medium` \| `low` |
| `description` | `str` | 1–2 sentence summary of the issue |
| `page_number` | `int` | Page where the issue first appears |
| `requires_sub_report` | `bool` | True if a specialist inspection is called for |

## InspectionFindings

The complete structured output of one extraction run.

| Field | Type | Description |
|-------|------|-------------|
| `property` | `PropertyInfo` | Property demographics |
| `foundation` | `list[DamageCategory]` | Foundation issues |
| `roof` | `list[DamageCategory]` | Roof issues |
| `hvac` | `list[DamageCategory]` | HVAC issues |
| `electrical` | `list[DamageCategory]` | Electrical issues |
| `plumbing` | `list[DamageCategory]` | Plumbing issues |
| `other` | `list[DamageCategory]` | All other issues |
| `photo_references` | `list[PhotoReference]` | Evidence page links |
| `overall_condition` | `str` | `good` \| `fair` \| `poor` \| `critical` |
| `notes` | `str` | General notes from the report |

## ExtractionLog

One record written to `logs/extractions.jsonl` per extraction run.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Nanosecond timestamp as string |
| `timestamp` | `datetime` | UTC time of extraction |
| `input_file` | `str` | Path to source PDF |
| `file_size_bytes` | `int` | PDF size |
| `model` | `str` | AI model used (default `grok`) |
| `agent_results` | `list[AgentResult]` | Per-agent output |
| `combined_findings` | `InspectionFindings` | Merged result |
| `overall_success` | `bool` | True if at least one agent succeeded |
| `total_tokens_used` | `dict` | `{input_tokens, output_tokens}` |
| `total_execution_time_ms` | `float` | Wall time for full extraction |
| `metadata` | `dict` | Field completeness and other extras |
