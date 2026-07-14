# HomeInspectionRipper

A Python tool that extracts structured data from home inspection PDF reports using the Grok vision API. Runs parallel AI agents to pull out property demographics and categorized damage findings, then returns clean JSON.

## Documentation

- [Architecture](ARCHITECTURE.md) — how the system is structured and how data flows through it
- [Data Model](DATA_MODEL.md) — all Pydantic models and their fields
- [Setup](SETUP.md) — installation, configuration, and running locally
- [Runbook](RUNBOOK.md) — operating the service, debugging, and Cloud Run logs
- [Decisions](DECISIONS.md) — why key technical choices were made

## Quick Start

```bash
git clone <repo-url>
cd HomeInspectionRipper-py
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your GROK_API_KEY
python main.py extract --pdf path/to/report.pdf
```

## Commands

```bash
python main.py extract --pdf report.pdf   # extract a single PDF
python main.py server                     # start the HTTP server on :8080
python main.py analyze                    # summarize extraction logs
```
