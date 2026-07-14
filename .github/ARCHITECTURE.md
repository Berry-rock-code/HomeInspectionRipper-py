# Architecture

## Overview

HomeInspectionRipper takes one or more PDF inspection reports, converts them to images, and uses the Grok vision API to extract structured property and damage data via parallel AI agents.

## Request Flow

```
Caller (CLI or Salesforce)
        │
        ▼
  main.py / server.py
        │
        ▼
  Extractor.extract_from_pdf()
        │
        ├── pdf_to_base64_images()     # pdftoppm via pdf2image
        │
        └── _run_agents()              # ThreadPoolExecutor
              ├── demographics agent ──► GrokClient.call_api() ──► x.ai API
              └── damage agent      ──► GrokClient.call_api() ──► x.ai API
                        │
                        ▼
              _combine_results()
                        │
                        ▼
              InspectionFindings (JSON)
```

## Components

| File | Responsibility |
|------|---------------|
| `client.py` | Raw HTTP to the Grok (x.ai) chat completions endpoint |
| `extractor.py` | PDF → images, parallel agent dispatch, result parsing |
| `agents.py` | Prompt text for each agent |
| `models.py` | Pydantic data models shared across the whole package |
| `logger.py` | Append-only JSONL log of every extraction |
| `server.py` | FastAPI server — downloads PDFs from Salesforce, runs extraction |
| `analyzer.py` | Reads the JSONL log and produces a performance report |
| `main.py` | CLI entry point (`extract`, `server`, `analyze` subcommands) |

## Parallel Agent Pattern

Two agents run concurrently against the same set of page images:

- **demographics** — extracts property info (address, beds, baths, sq ft, year built, condition)
- **damage** — extracts categorized issues (foundation, roof, HVAC, electrical, plumbing, other)

Each agent gets one retry on failure. Results are merged into a single `InspectionFindings` object.

## Deployment

The server is deployed as a Docker container on Google Cloud Run. It is stateless — no database. Logs are written to the container filesystem (ephemeral); for production persistence, mount a Cloud Storage FUSE bucket or ship logs to Cloud Logging.
