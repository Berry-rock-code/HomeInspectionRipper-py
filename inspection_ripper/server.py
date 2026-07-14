from __future__ import annotations

import tempfile
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .client import GrokClient
from .extractor import Extractor
from .models import InspectionFindings


# ------------------------------------------------------------------
# Request / Response schemas
# ------------------------------------------------------------------

class SalesforceFileRef(BaseModel):
    content_version_id: str
    filename: str = ""


class ProcessRequest(BaseModel):
    files: list[SalesforceFileRef]
    instance_url: str
    access_token: str
    opportunity_id: str = ""


class ProcessResponse(BaseModel):
    success: bool
    findings: InspectionFindings | None = None
    processing_time_ms: float | None = None
    error: str | None = None


# ------------------------------------------------------------------
# App factory (used by main.py / uvicorn)
# ------------------------------------------------------------------

def create_app(api_key: str) -> FastAPI:
    app = FastAPI(title="HomeInspectionRipper")
    client = GrokClient(api_key=api_key)
    extractor = Extractor(client=client)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/process", response_model=ProcessResponse)
    def process(req: ProcessRequest) -> ProcessResponse:
        if not req.files:
            raise HTTPException(status_code=400, detail="files must not be empty")
        if not req.instance_url or not req.access_token:
            raise HTTPException(status_code=400, detail="instance_url and access_token are required")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pdf_paths = []
            for file_ref in req.files:
                try:
                    pdf_paths.append(_download_sf_file(req.instance_url, req.access_token, file_ref, tmp_path))
                except Exception as exc:
                    print(f"skipping {file_ref.filename}: {exc}", flush=True)

            if not pdf_paths:
                raise HTTPException(status_code=400, detail="no files could be downloaded from Salesforce")

            start = time.time()
            _, findings, _ = extractor.extract_from_multiple_pdfs(pdf_paths)
            elapsed = (time.time() - start) * 1000

        return ProcessResponse(success=True, findings=findings, processing_time_ms=elapsed)

    return app


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _download_sf_file(
    instance_url: str,
    access_token: str,
    file_ref: SalesforceFileRef,
    dest_dir: Path,
) -> Path:
    url = (
        instance_url.rstrip("/")
        + f"/services/data/v59.0/sobjects/ContentVersion/{file_ref.content_version_id}/VersionData"
    )
    response = httpx.get(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=60,
        follow_redirects=True,
    )
    response.raise_for_status()

    filename = file_ref.filename or f"{file_ref.content_version_id}.pdf"
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"

    local_path = dest_dir / filename
    local_path.write_bytes(response.content)
    return local_path
