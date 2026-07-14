# HomeInspectionRipper

Extracts structured data from home inspection PDF reports using the Grok vision API. Designed to work as the backend extraction service for the [InspectionSF](https://github.com/Berry-rock-code/InspectionSF) Salesforce package.

## How It Fits Together

```
Salesforce Opportunity
        │
        │  Agent checks "Inspection Received" checkbox
        ▼
InspectionReceivedTrigger  (Apex)
        │
        │  Finds PDF files uploaded within ±2 min of checkbox
        ▼
InspectionDocumentProcessor  (Apex Queueable)
        │
        │  POST /process  {files, instance_url, access_token, opportunity_id}
        ▼
HomeInspectionRipper  (this service — Python / Cloud Run)
        │
        │  Downloads PDFs from Salesforce using the session token
        │  Converts pages to images (pdftoppm)
        │  Runs demographics + damage agents in parallel against Grok API
        ▼
        │  Returns InspectionFindings JSON
        │
        ▼
InspectionDocumentProcessor  (Apex — stores results)
        │
        ├── Inspection_Findings__c  (property address, overall condition)
        └── Inspection_Issue__c     (one record per damage item)
```

## What Gets Extracted

From each PDF the service returns:

**Property info** — address, bedrooms, bathrooms, square footage, year built, overall condition

**Damage findings** organized by category, each with a severity (`critical` / `high` / `medium` / `low`), a 1–2 sentence description, the page number it appears on, and a flag if a specialist sub-report is called for:

| Category | Examples |
|----------|---------|
| Foundation | Cracks, settling, crawlspace issues, support columns |
| Roof | Shingles, flashing, gutters, drainage |
| HVAC | Heating, cooling, ductwork, ventilation |
| Electrical | Panel, wiring, outlets, GFCI, grounding |
| Plumbing | Pipes, fixtures, water heater, drainage |
| Other | Moisture, mold, windows, siding, pest, unpermitted work |

## Local Setup

**Prerequisites**

```bash
# Ubuntu / WSL
sudo apt-get install -y poppler-utils

# macOS
brew install poppler
```

**Install**

```bash
git clone https://github.com/Berry-rock-code/HomeInspectionRipper-py.git
cd HomeInspectionRipper-py
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set GROK_API_KEY=xai-your-key-here
```

**Run**

```bash
# Extract a single PDF
python main.py extract --pdf path/to/report.pdf

# Start the HTTP server (port 8080)
python main.py server

# Analyze past extraction logs
python main.py analyze
```

## API

### `POST /process`

Called by Salesforce. Downloads PDFs via the Salesforce Content API, runs extraction, returns findings.

**Request**
```json
{
  "files": [
    {"content_version_id": "068XXXXXXXXXXXX", "filename": "report.pdf"}
  ],
  "instance_url": "https://yourorg.my.salesforce.com",
  "access_token": "00DXXX...",
  "opportunity_id": "006XXXXXXXXXXXX"
}
```

**Response**
```json
{
  "success": true,
  "processing_time_ms": 14200,
  "findings": {
    "property": {
      "address": "123 Main St",
      "bedrooms": 3,
      "bathrooms": 2,
      "square_footage": 1800,
      "year_built": 1992
    },
    "overall_condition": "fair",
    "foundation": [],
    "roof": [
      {
        "category": "roof",
        "severity": "high",
        "description": "Missing shingles on north slope with exposed underlayment.",
        "page_number": 12,
        "requires_sub_report": false
      }
    ],
    "hvac": [], "electrical": [], "plumbing": [], "other": []
  }
}
```

### `GET /health`

Returns `{"status": "ok"}`. Used by Cloud Run health checks.

## Salesforce Setup

After deploying to Cloud Run:

1. In Salesforce, go to **Setup → Custom Metadata Types → Inspection Config → Manage Records → Default**
2. Set `Server_URL__c` to your Cloud Run service URL + `/process`
   ```
   https://inspection-server-xxxxx-uc.a.run.app/process
   ```
3. Make sure the Cloud Run URL is in your org's **Remote Site Settings** (already included in the InspectionSF package as `InspectionServer`)

## Deployment

Deployments are manual — trigger the **Deploy to Cloud Run** workflow from the **Actions** tab. It runs the full test suite first and will not deploy if tests fail.

**Required GitHub secrets:**

| Secret | Description |
|--------|-------------|
| `GROK_API_KEY` | Your x.ai API key |
| `GCP_PROJECT_ID` | Google Cloud project ID |
| `GCP_SA_KEY` | GCP service account JSON key |

## Related

- [InspectionSF](https://github.com/Berry-rock-code/InspectionSF) — Salesforce package (Apex trigger, LWC, custom objects)
- [Docs site](https://berry-rock-code.github.io/HomeInspectionRipper-py/)
