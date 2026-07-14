# Architecture Decisions

## Python over Go

The original implementation was in Go. Switched to Python for faster iteration on prompt engineering and easier data wrangling with Pydantic. The bottleneck is always the Grok API round-trip, not language overhead.

## Grok (x.ai) as the Vision Model

Inspection reports are image-heavy. Grok supports multimodal input (images + text in one request) and has a large context window suitable for multi-page PDFs. The API is OpenAI-compatible, making it straightforward to swap models if needed.

## Two Parallel Agents instead of One

A single prompt asking for everything produced inconsistent output — demographics fields would crowd out damage detail or vice versa. Splitting into two focused agents (demographics, damage) and running them concurrently improves accuracy and keeps latency the same as a single call.

## pdftoppm (via pdf2image) for PDF Conversion

pdftoppm is a battle-tested CLI tool that produces clean JPEG output. pdf2image wraps it with a clean Python API. Alternatives like PyMuPDF or pdfplumber were considered but pdftoppm produced better image quality at low DPI for vision model input.

## FastAPI for the HTTP Server

FastAPI gives automatic request/response validation via Pydantic (same models used everywhere else), auto-generated OpenAPI docs at `/docs`, and async support if needed later. Flask was considered but FastAPI's native Pydantic integration removes a whole layer of manual parsing.

## Salesforce ContentVersion Download in the Server

Rather than requiring the caller to upload PDFs directly, the server downloads them from Salesforce using the caller's access token. This keeps the payload small (just IDs) and avoids storing PDFs anywhere permanently.

## Append-only JSONL Log

Each extraction is a single JSON line in `logs/extractions.jsonl`. This is easy to tail, grep, and parse with the analyzer. No database dependency needed for the current scale.
