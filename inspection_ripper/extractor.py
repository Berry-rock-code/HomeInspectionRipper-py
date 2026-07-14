from __future__ import annotations

import base64
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .agents import AgentExtractor, build_agents
from .client import GrokClient
from .models import (
    AgentResult,
    DamageCategory,
    InspectionFindings,
    PropertyInfo,
)


def pdf_to_base64_images(pdf_path: str | Path, dpi: int = 72) -> list[str]:
    from io import BytesIO
    from pdf2image import convert_from_path

    pages = convert_from_path(str(pdf_path), dpi=dpi, fmt="jpeg")
    images = []
    for page in pages:
        buf = BytesIO()
        page.save(buf, format="JPEG")          # fix: was pages.save (wrong var)
        images.append(base64.b64encode(buf.getvalue()).decode("utf-8"))  # fix: getValue → getvalue
    return images


class Extractor:
    def __init__(self, client: GrokClient) -> None:
        self.client = client

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def extract_from_pdf(
        self, pdf_path: str | Path
    ) -> tuple[list[AgentResult], InspectionFindings, dict[str, int]]:
        """Extract findings from a single PDF."""
        images = pdf_to_base64_images(pdf_path)
        return self._run_agents(images)

    def extract_from_multiple_pdfs(
        self, pdf_paths: list[str | Path]
    ) -> tuple[list[AgentResult], InspectionFindings, dict[str, int]]:
        """Concatenate all pages from multiple PDFs, then run agents once."""
        all_images: list[str] = []
        for path in pdf_paths:
            all_images.extend(pdf_to_base64_images(path))
        if not all_images:
            raise ValueError(f"No pages extracted from {len(pdf_paths)} PDF(s)")
        return self._run_agents(all_images)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_agents(
        self, page_images: list[str]
    ) -> tuple[list[AgentResult], InspectionFindings, dict[str, int]]:
        agents = build_agents()
        results = []
        total_tokens = {"input_tokens": 0, "output_tokens": 0}

        with ThreadPoolExecutor(max_workers=len(agents)) as pool:
            futures = {
                pool.submit(self._extract_with_retry, agent, page_images): agent
                for agent in agents
            }
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                total_tokens["input_tokens"] += result.tokens_used["input_tokens"]
                total_tokens["output_tokens"] += result.tokens_used["output_tokens"]

        findings = self._combine_results(results)
        return results, findings, total_tokens

    def _extract_with_retry(
        self, agent: AgentExtractor, page_images: list[str]
    ) -> AgentResult:
        start = time.time()

        for attempt in range(2):
            try:
                text, tokens = self.client.call_api(
                    page_images, agent.prompt, timeout=agent.timeout
                )
                return AgentResult(
                    agent_name=agent.name,
                    success=True,                                    # fix: was sucess
                    result=text,
                    tokens_used=tokens,
                    execution_time_ms=(time.time() - start) * 1000, # fix: was execution_time
                    retried=attempt > 0,
                    succeeded_on_retry=attempt > 0,
                )
            except Exception as exc:
                last_error = str(exc)

        return AgentResult(
            agent_name=agent.name,
            success=False,                                           # fix: was sucess
            error_message=last_error,
            tokens_used={"input_tokens": 0, "output_tokens": 0},
            execution_time_ms=(time.time() - start) * 1000,         # fix: was execution_time
            retried=True,
        )

    # ------------------------------------------------------------------
    # Result parsing
    # ------------------------------------------------------------------

    def _combine_results(self, results: list[AgentResult]) -> InspectionFindings:
        findings = InspectionFindings()
        for result in results:
            if not result.success:
                continue
            try:
                data = json.loads(result.result) if isinstance(result.result, str) else result.result
            except (json.JSONDecodeError, TypeError):
                continue

            if result.agent_name == "demographics":
                self._extract_demographics(data, findings)
            elif result.agent_name == "damage":
                self._extract_damage(data, findings)
        return findings

    def _extract_demographics(self, data: dict, findings: InspectionFindings) -> None:
        prop = data.get("property", {})
        findings.property.address = prop.get("address", "")
        findings.property.bedrooms = int(prop.get("bedrooms", 0))
        findings.property.bathrooms = int(prop.get("bathrooms", 0))
        findings.property.square_footage = int(prop.get("square_footage", 0))
        findings.property.year_built = int(prop.get("year_built", 0))
        findings.overall_condition = data.get("overall_condition", "")
        findings.notes = data.get("notes", "")

    def _extract_damage(self, data: dict, findings: InspectionFindings) -> None:
        category_map = {
            "foundation": findings.foundation,
            "roof": findings.roof,
            "hvac": findings.hvac,
            "electrical": findings.electrical,
            "plumbing": findings.plumbing,
            "other": findings.other,
        }
        for category, target_list in category_map.items():
            for item in data.get(category, []):
                target_list.append(DamageCategory(
                    category=category,
                    severity=item.get("severity", ""),
                    description=item.get("description", ""),
                    page_number=int(item.get("page_number", 0)),
                    requires_sub_report=bool(item.get("requires_sub_report", False)),
                ))
