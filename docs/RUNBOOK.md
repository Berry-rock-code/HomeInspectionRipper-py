# Runbook

## Extracting a Report Locally

```bash
source .venv/bin/activate
python main.py extract --pdf ./path/to/report.pdf --verbose
```

Output JSON lands in `./output/<filename>.json`. The extraction log is appended to `./logs/extractions.jsonl`.

## Starting the Server

```bash
source .venv/bin/activate
python main.py server
# Listening on http://0.0.0.0:8080
```

### POST /process

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

Returns `InspectionFindings` JSON on success.

### GET /health

Returns `{"status": "ok"}`. Used by Cloud Run health checks.

## Analyzing Logs

```bash
python main.py analyze
```

Prints agent success rates, field completion rates, damage distribution, and key insights from all past runs in `./logs/extractions.jsonl`.

## Deploying to Cloud Run

Trigger the **Deploy to Cloud Run** workflow manually from the GitHub Actions tab. It runs tests first and will not deploy if they fail.

## Debugging a Failed Extraction

1. Check `./logs/extractions.jsonl` — find the entry with `"overall_success": false`.
2. Look at `agent_results` — the failing agent will have `"success": false` and an `error_message`.
3. Common causes:
   - `GROK_API_KEY` not set or expired
   - PDF could not be converted (check `poppler-utils` is installed)
   - Grok returned malformed JSON — the agent prompt may need tuning
   - Salesforce access token expired (server mode only)

## Checking Cloud Run Logs

```bash
gcloud run services logs read inspection-server \
  --region=us-central1 \
  --project=YOUR_PROJECT_ID \
  --limit=50
```
