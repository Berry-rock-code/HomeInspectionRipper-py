# Setup

## Prerequisites

- Python 3.12+
- `poppler-utils` (provides `pdftoppm` for PDF conversion)

### Install poppler

```bash
# Ubuntu / WSL
sudo apt-get install -y poppler-utils

# macOS
brew install poppler
```

## Local Development

```bash
# 1. Clone the repo
git clone <repo-url>
cd HomeInspectionRipper-py

# 2. Create and activate the virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows WSL: same command

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt   # for tests and linting

# 4. Configure environment
cp .env.example .env
# Edit .env and set GROK_API_KEY=xai-your-key-here
```

## Running

```bash
# Extract a single PDF
python main.py extract --pdf path/to/report.pdf

# Start the HTTP server (default port 8080)
python main.py server

# Analyze extraction logs
python main.py analyze
```

## Running Tests

```bash
pytest tests/ -v
```

## GitHub Actions Secrets (for CI/CD)

Add these in your repo's Settings → Secrets → Actions:

| Secret | Description |
|--------|-------------|
| `GROK_API_KEY` | Your x.ai API key |
| `GCP_PROJECT_ID` | Google Cloud project ID |
| `GCP_SA_KEY` | GCP service account JSON key (for Cloud Run deploy) |

The deploy workflow is `workflow_dispatch` only — trigger it manually from the Actions tab.
