import unittest

import json
from pathlib import Path

from inspection_ripper.logger import Logger
from inspection_ripper.models import AgentResult, ExtractionLog


def test_log_extraction_writes_jsonl(tmp_path):
    logger = Logger(log_dir=tmp_path)
    entry = ExtractionLog(input_file="report.pdf", overall_success=True)
    logger.log_extraction(entry)

    log_file = tmp_path / "extractions.jsonl"
    assert log_file.exists()
    lines = log_file.read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["input_file"] == "report.pdf"
    assert data["overall_success"] is True


def test_log_extraction_appends(tmp_path):
    logger = Logger(log_dir=tmp_path)
    for i in range(3):
        logger.log_extraction(ExtractionLog(input_file=f"report_{i}.pdf"))

    lines = (tmp_path / "extractions.jsonl").read_text().strip().splitlines()
    assert len(lines) == 3


def test_load_all_returns_entries(tmp_path):
    logger = Logger(log_dir=tmp_path)
    logger.log_extraction(ExtractionLog(input_file="a.pdf", overall_success=True))
    logger.log_extraction(ExtractionLog(input_file="b.pdf", overall_success=False))

    entries = logger.load_all()
    assert len(entries) == 2
    assert entries[0].input_file == "a.pdf"
    assert entries[1].overall_success is False


def test_load_all_empty(tmp_path):
    logger = Logger(log_dir=tmp_path)
    assert logger.load_all() == []


def test_log_multi_agent_sets_overall_success(tmp_path):
    logger = Logger(log_dir=tmp_path)
    results = [
        AgentResult(agent_name="demographics", success=True),
        AgentResult(agent_name="damage", success=False),
    ]
    logger.log_multi_agent(
        input_file="test.pdf",
        file_size_bytes=500,
        agent_results=results,
        findings=None,
        total_tokens={"input_tokens": 100, "output_tokens": 50},
        total_execution_time_ms=1234.5,
    )
    entries = logger.load_all()
    assert entries[0].overall_success is True


def test_log_sets_id_if_missing(tmp_path):
    logger = Logger(log_dir=tmp_path)
    logger.log_extraction(ExtractionLog())
    entries = logger.load_all()
    assert entries[0].id != ""


if __name__ == '__main__':
    unittest.main()
