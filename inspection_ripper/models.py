from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class PropertyInfo(BaseModel):
    address: str = ""
    bedrooms: int = 0
    bathrooms: int = 0
    square_footage: int = 0
    year_built: int = 0


class DamageCategory(BaseModel):
    category: str = ""   # foundation | roof | hvac | electrical | plumbing | other
    severity: str = ""   # critical | high | medium | low
    description: str = ""
    page_number: int = 0
    requires_sub_report: bool = False


class PhotoReference(BaseModel):
    page_number: int = 0
    description: str = ""


class InspectionFindings(BaseModel):
    property: PropertyInfo = Field(default_factory=PropertyInfo)
    foundation: list[DamageCategory] = Field(default_factory=list)
    roof: list[DamageCategory] = Field(default_factory=list)
    hvac: list[DamageCategory] = Field(default_factory=list)
    electrical: list[DamageCategory] = Field(default_factory=list)
    plumbing: list[DamageCategory] = Field(default_factory=list)
    other: list[DamageCategory] = Field(default_factory=list)
    photo_references: list[PhotoReference] = Field(default_factory=list)
    overall_condition: str = ""   # good | fair | poor | critical
    notes: str = ""


class AgentResult(BaseModel):
    agent_name: str = ""
    success: bool = False
    error_message: str = ""
    result: Any = None
    tokens_used: dict[str, int] = Field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})
    execution_time_ms: float = 0.0
    retried: bool = False
    succeeded_on_retry: bool = False


class ExtractionLog(BaseModel):
    id: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    input_file: str = ""
    file_size_bytes: int = 0
    model: str = "grok"
    agent_results: list[AgentResult] = Field(default_factory=list)
    combined_findings: InspectionFindings | None = None
    overall_success: bool = False
    total_tokens_used: dict[str, int] = Field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})
    total_execution_time_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentExtractor(BaseModel):
    name: str       # demographics | damage
    prompt: str
    timeout: int = 120   # seconds


class FieldCompleteness(BaseModel):
    address_found: bool = False
    bedrooms_found: bool = False
    bathrooms_found: bool = False
    square_footage_found: bool = False
    year_built_found: bool = False
    foundation_found: bool = False
    roof_found: bool = False
    hvac_found: bool = False
    electrical_found: bool = False
    plumbing_found: bool = False
    other_found: bool = False
    photos_referenced: bool = False
    overall_condition_found: bool = False


def get_field_completeness(findings: InspectionFindings) -> FieldCompleteness:
    return FieldCompleteness(
        address_found=bool(findings.property.address),
        bedrooms_found=findings.property.bedrooms > 0,
        bathrooms_found=findings.property.bathrooms > 0,
        square_footage_found=findings.property.square_footage > 0,
        year_built_found=findings.property.year_built > 0,
        foundation_found=len(findings.foundation) > 0,
        roof_found=len(findings.roof) > 0,
        hvac_found=len(findings.hvac) > 0,
        electrical_found=len(findings.electrical) > 0,
        plumbing_found=len(findings.plumbing) > 0,
        other_found=len(findings.other) > 0,
        photos_referenced=len(findings.photo_references) > 0,
        overall_condition_found=bool(findings.overall_condition),
    )
