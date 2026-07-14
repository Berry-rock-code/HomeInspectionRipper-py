from __future__ import annotations

import tempfile
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .client import GrokClient
from .extractor import Extractor
from .models import InspectionFindings

app = FastAPI(title="HomeInspectionRipper")


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
# Routes
# ------------------------------------------------------------------

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/process", response_model=ProcessResponse)
def process(req: ProcessRequest, client: GrokClient = None) -> ProcessResponse:
    """Download PDFs from Salesforce, run multi-agent extraction, return findings.

    Steps:
    1. Validate req.files is non-empty and credentials are present.
    2. Create a temp directory.
    3. Call _download_sf_file for each file ref; skip failures (log them).
    4. Raise 400 if no files downloaded.
    5. Run extractor.extract_from_multiple_pdfs on the local paths.
    6. Return ProcessResponse with findings and timing.
    """
    import time

    if not req.files:
        raise HTTPException(status_code=400, detail="No files provided.")
    if not req.instance_url or not req.access_token:
        raise HTTPException(status_code=400, detail="No instance URL or access_token are provided.")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        pdf_paths = []
        for file_ref in req.files:
            try:
                pdf_paths.append(_download_sf_file(req.instance_url, req.access_token, file_ref, tmp_path))
            except Exception as exc:
                print(f"skipping {file_ref.filename}: {exc}")

        if not pdf_paths:
            raise HTTPException(status_code=400, detail="No pdf files provided from Salesforce.")

        extractor = Extractor(client=client)
        start = time.time()
        _, findings, _ = extractor.extract_from_multiple_pdfs(pdf_paths)
        elapsed = (time.time() - start) * 1000

    return ProcessResponse(success=True, findings=findings, processing_time_ms=elapsed)


def _download_sf_file(
    instance_url: str,
    access_token: str,
    file_ref: SalesforceFileRef,
    dest_dir: Path,
) -> Path:
    """Download a Salesforce ContentVersion file and save it to dest_dir.

    URL pattern:
      {instance_url}/services/data/v59.0/sobjects/ContentVersion/{id}/VersionData
    Auth header: Bearer {access_token}
    Timeout: 60 s
    Raise httpx.HTTPStatusError on non-200.
    Return the local Path where the file was saved.
    """
    url = (
            instance_url.rstrip("/")
            + "/services/data/v59.0/sobjects/ContentVersion"
            + f"/{file_ref.content_version_id}/VersionData"
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


# ------------------------------------------------------------------
# App factory (used by main.py / uvicorn)
# ------------------------------------------------------------------

def create_app(api_key: str) -> FastAPI:
    """Wire a GrokClient into the app via dependency injection."""
    client = GrokClient(api_key=api_key)

    @app.post("/process", response_model=ProcessResponse, include_in_schema=False)
    def _process(req: ProcessRequest) -> ProcessResponse:
        return process(req, client=client)

    return app
