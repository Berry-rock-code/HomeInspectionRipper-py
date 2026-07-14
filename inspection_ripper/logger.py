from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from .models import AgentResult, ExtractionLog, InspectionFindings


class Logger:
    def __init__(self, log_dir: str | Path = "./logs") -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self.log_dir / "extractions.jsonl"

    def log_extraction(self, entry: ExtractionLog) -> None:
        """Append one ExtractionLog as a JSON line to extractions.jsonl."""
        if not entry.timestamp:
            entry.timestamp = datetime.utcnow()
        if not entry.id:
            entry.id = str(int(time.time_ns()))

        with self._log_file.open("a", encoding="utf-8") as f:
            f.write(entry.model_dump_json() + "\n")

    def log_multi_agent(
        self,
        input_file: str,
        file_size_bytes: int,
        agent_results: list[AgentResult],
        findings: InspectionFindings | None,
        total_tokens: dict[str, int],
        total_execution_time_ms: float,
        metadata: dict | None = None,
    ) -> None:
        """Convenience wrapper: build an ExtractionLog and write it."""
        overall_success = any(r.success for r in agent_results)
        entry = ExtractionLog(
            input_file=input_file,
            file_size_bytes=file_size_bytes,
            agent_results=agent_results,
            combined_findings=findings,
            overall_success=overall_success,
            total_tokens_used=total_tokens,
            total_execution_time_ms=total_execution_time_ms,
            metadata=metadata or {},
        )
        self.log_extraction(entry)

    def load_all(self) -> list[ExtractionLog]:
        """Read every line from extractions.jsonl and return parsed logs."""
        if not self._log_file.exists():
            return []
        logs: list[ExtractionLog] = []
        for line in self._log_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    logs.append(ExtractionLog.model_validate_json(line))
                except Exception:
                    pass
        return logs
