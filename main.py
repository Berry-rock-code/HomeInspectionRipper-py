"""CLI entry points for HomeInspectionRipper.

Usage:
  # Extract a single PDF
  python main.py extract --pdf path/to/report.pdf

  # Start the HTTP server
  python main.py server

  # Analyze extraction logs
  python main.py analyze
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def cmd_extract(args: argparse.Namespace) -> None:
    """Run multi-agent extraction on a PDF and write results to output/.

    Steps:
    1. Read GROK_API_KEY from env (or --key flag).
    2. Build GrokClient, Extractor, Logger.
    3. Call extractor.extract_from_pdf(args.pdf).
    4. Write JSON output to args.output_dir / <stem>.json.
    5. Call logger.log_multi_agent(...).
    6. Print summary table to stdout.
    """
    from inspection_ripper import Extractor, GrokClient, Logger
    from inspection_ripper.models import get_field_completeness

    api_key = args.key or os.getenv("GROK_API_KEY", "")
    if not api_key:
        sys.exit("Error: GROK_API_KEY not set. Use --key or set the env var.")

    client = GrokClient(api_key=api_key)
    extractor = Extractor(client=client)
    logger = Logger(log_dir=args.log_dir)

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        sys.exit(f"Error: file not found: {pdf_path}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Extracting: {pdf_path}")
    import time
    start = time.time()
    agent_results, findings, total_tokens = extractor.extract_from_pdf(pdf_path)
    elapsed = (time.time() - start) * 1000

    output_path = output_dir / (pdf_path.stem + ".json")
    output_path.write_text(findings.model_dump_json(indent=2))

    logger.log_multi_agent(
        input_file=str(pdf_path),
        file_size_bytes=pdf_path.stat().st_size,
        agent_results=agent_results,
        findings=findings,
        total_tokens=total_tokens,
        total_execution_time_ms=elapsed,
        metadata={"field_completeness": get_field_completeness(findings).model_dump()},
    )

    print(f"\n{'=' * 52}")
    print(f"Output:       {output_path}")
    print(f"Total time:   {elapsed:.0f} ms")
    print(f"Tokens:       in={total_tokens['input_tokens']}  out={total_tokens['output_tokens']}")
    print(f"\n--- Agent results ---")
    for r in agent_results:
        status = "OK" if r.success else "FAIL"
        retry = " (retried)" if r.retried else ""
        print(f"  [{status}] {r.agent_name:<15} {r.execution_time_ms:>6.0f} ms{retry}")
    print(f"\n--- Property ---")
    print(f"  Address:    {findings.property.address}")
    print(f"  Beds/Baths: {findings.property.bedrooms} / {findings.property.bathrooms}")
    print(f"  Sq ft:      {findings.property.square_footage}")
    print(f"  Year built: {findings.property.year_built}")
    print(f"  Condition:  {findings.overall_condition}")
    print(f"\n--- Damage ---")
    print(f"  Foundation: {len(findings.foundation)}")
    print(f"  Roof:       {len(findings.roof)}")
    print(f"  HVAC:       {len(findings.hvac)}")
    print(f"  Electrical: {len(findings.electrical)}")
    print(f"  Plumbing:   {len(findings.plumbing)}")
    print(f"  Other:      {len(findings.other)}")
    print(f"{'=' * 52}\n")


def cmd_server(args: argparse.Namespace) -> None:
    """Start the FastAPI server with uvicorn."""
    import uvicorn
    from inspection_ripper.server import create_app

    api_key = os.getenv("GROK_API_KEY", "")
    if not api_key:
        sys.exit("Error: GROK_API_KEY not set.")

    port = int(os.getenv("PORT", "8080"))
    app = create_app(api_key)
    uvicorn.run(app, host="0.0.0.0", port=port)


def cmd_analyze(args: argparse.Namespace) -> None:
    """Load extraction logs and print the analysis report."""
    from inspection_ripper.analyzer import Analyzer
    from inspection_ripper.logger import Logger

    logger = Logger(log_dir=args.log_dir)
    analyzer = Analyzer(logger)
    report = analyzer.run()
    analyzer.print_report(report)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="home-inspection-ripper")
    sub = parser.add_subparsers(dest="command", required=True)

    # extract
    p_extract = sub.add_parser("extract", help="Extract data from a PDF inspection report")
    p_extract.add_argument("--pdf", required=True, help="Path to PDF file")
    p_extract.add_argument("--key", default="", help="Grok API key (or set GROK_API_KEY)")
    p_extract.add_argument("--output-dir", default="./output", help="Where to write JSON output")
    p_extract.add_argument("--log-dir", default="./logs", help="Where to write JSONL logs")
    p_extract.add_argument("--verbose", action="store_true")
    p_extract.set_defaults(func=cmd_extract)

    # server
    p_server = sub.add_parser("server", help="Start the HTTP server")
    p_server.set_defaults(func=cmd_server)

    # analyze
    p_analyze = sub.add_parser("analyze", help="Analyze extraction logs")
    p_analyze.add_argument("--log-dir", default="./logs")
    p_analyze.set_defaults(func=cmd_analyze)

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
