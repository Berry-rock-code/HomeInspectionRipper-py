from __future__ import annotations

from dataclasses import dataclass, field

from .logger import Logger
from .models import ExtractionLog, get_field_completeness


@dataclass
class AgentStats:
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    avg_exec_time_ms: float = 0.0
    total_tokens: int = 0
    retries_needed: int = 0
    succeeded_on_retry: int = 0


@dataclass
class DamageStats:
    foundation: int = 0
    roof: int = 0
    hvac: int = 0
    electrical: int = 0
    plumbing: int = 0
    other: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


@dataclass
class AnalysisReport:
    total: int = 0
    successful: int = 0
    failed: int = 0
    overall_success_rate: float = 0.0
    avg_exec_time_ms: float = 0.0
    token_stats: dict[str, int] = field(default_factory=dict)
    field_completion_rate: dict[str, float] = field(default_factory=dict)
    agent_performance: dict[str, AgentStats] = field(default_factory=dict)
    damage_stats: DamageStats = field(default_factory=DamageStats)
    insights: list[str] = field(default_factory=list)


class Analyzer:
    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    def run(self) -> AnalysisReport:
        logs = self.logger.load_all()
        report = AnalysisReport(total=len(logs))
        if not logs:
            return report

        total_exec_time = 0.0
        field_counts: dict[str, int] = {}
        agent_times: dict[str, list[float]] = {}

        for entry in logs:
            if entry.overall_success:
                report.successful += 1
                self._tally_damage(entry, report.damage_stats)
                if entry.combined_findings:
                    self._tally_fields(entry, field_counts)
            else:
                report.failed += 1

            for ar in entry.agent_results:
                stats = report.agent_performance.setdefault(ar.agent_name, AgentStats())
                if ar.success:
                    stats.success_count += 1
                    stats.total_tokens += ar.tokens_used.get("input_tokens", 0) + ar.tokens_used.get("output_tokens", 0)
                    agent_times.setdefault(ar.agent_name, []).append(ar.execution_time_ms)
                    if ar.succeeded_on_retry:
                        stats.succeeded_on_retry += 1
                else:
                    stats.failure_count += 1
                if ar.retried:
                    stats.retries_needed += 1

            for k, v in entry.total_tokens_used.items():
                report.token_stats[k] = report.token_stats.get(k, 0) + v

            total_exec_time += entry.total_execution_time_ms

        report.overall_success_rate = report.successful / report.total * 100
        report.avg_exec_time_ms = total_exec_time / report.total

        for name, stats in report.agent_performance.items():
            total = stats.success_count + stats.failure_count
            if total:
                stats.success_rate = stats.success_count / total * 100
            times = agent_times.get(name, [])
            if times:
                stats.avg_exec_time_ms = sum(times) / len(times)

        if report.successful:
            report.field_completion_rate = {
                f: count / report.successful * 100
                for f, count in field_counts.items()
            }

        report.insights = self._generate_insights(report)
        return report

    def _tally_damage(self, entry: ExtractionLog, stats: DamageStats) -> None:
        if not entry.combined_findings:
            return
        f = entry.combined_findings
        stats.foundation += len(f.foundation)
        stats.roof += len(f.roof)
        stats.hvac += len(f.hvac)
        stats.electrical += len(f.electrical)
        stats.plumbing += len(f.plumbing)
        stats.other += len(f.other)
        for damages in [f.foundation, f.roof, f.hvac, f.electrical, f.plumbing, f.other]:
            for d in damages:
                if d.severity == "critical":
                    stats.critical += 1
                elif d.severity == "high":
                    stats.high += 1
                elif d.severity == "medium":
                    stats.medium += 1
                elif d.severity == "low":
                    stats.low += 1

    def _tally_fields(self, entry: ExtractionLog, field_counts: dict[str, int]) -> None:
        c = get_field_completeness(entry.combined_findings)
        for name, found in c.model_dump().items():
            if found:
                field_counts[name] = field_counts.get(name, 0) + 1

    def _generate_insights(self, report: AnalysisReport) -> list[str]:
        insights = []
        insights.append(
            f"Overall success rate: {report.overall_success_rate:.1f}% "
            f"({report.successful}/{report.total} extractions)"
        )

        if report.agent_performance:
            weakest = min(report.agent_performance.items(), key=lambda x: x[1].success_rate)
            strongest = max(report.agent_performance.items(), key=lambda x: x[1].success_rate)
            if weakest[1].success_rate < 100:
                insights.append(f"Weakest agent: '{weakest[0]}' ({weakest[1].success_rate:.1f}% success)")
            insights.append(f"Strongest agent: '{strongest[0]}' ({strongest[1].success_rate:.1f}% success)")

        damage_map = {
            "foundation": report.damage_stats.foundation,
            "roof": report.damage_stats.roof,
            "hvac": report.damage_stats.hvac,
            "electrical": report.damage_stats.electrical,
            "plumbing": report.damage_stats.plumbing,
            "other": report.damage_stats.other,
        }
        most_common = max(damage_map.items(), key=lambda x: x[1])
        if most_common[1] > 0:
            insights.append(f"Most common damage type: '{most_common[0]}' ({most_common[1]} issues)")

        if report.damage_stats.critical > 0:
            insights.append(f"Critical severity damage found: {report.damage_stats.critical} issues")

        insights.append(f"Average extraction time: {report.avg_exec_time_ms:.0f} ms per report")
        return insights

    def print_report(self, report: AnalysisReport) -> None:
        w = 54
        print(f"\n{'=' * w}")
        print("  MULTI-AGENT EXTRACTION ANALYSIS")
        print(f"{'=' * w}")
        print(f"  Total:        {report.total}")
        print(f"  Successful:   {report.successful}")
        print(f"  Failed:       {report.failed}")
        print(f"  Success rate: {report.overall_success_rate:.1f}%")
        print(f"  Avg time:     {report.avg_exec_time_ms:.0f} ms")

        print(f"\n--- Agent Performance ---")
        for name, stats in sorted(report.agent_performance.items(), key=lambda x: -x[1].success_rate):
            retry = f" ({stats.retries_needed} retries)" if stats.retries_needed else ""
            print(f"  {name:<15} {stats.success_rate:5.1f}%  {stats.avg_exec_time_ms:>6.0f} ms  {stats.total_tokens} tokens{retry}")

        print(f"\n--- Field Completion ---")
        for name, rate in sorted(report.field_completion_rate.items(), key=lambda x: -x[1]):
            print(f"  {name:<30} {rate:.1f}%")

        print(f"\n--- Damage Summary ---")
        d = report.damage_stats
        print(f"  Foundation: {d.foundation}  Roof: {d.roof}  HVAC: {d.hvac}")
        print(f"  Electrical: {d.electrical}  Plumbing: {d.plumbing}  Other: {d.other}")
        print(f"\n--- Severity ---")
        print(f"  Critical: {d.critical}  High: {d.high}  Medium: {d.medium}  Low: {d.low}")

        print(f"\n--- Token Usage ---")
        print(f"  Input:  {report.token_stats.get('input_tokens', 0)}")
        print(f"  Output: {report.token_stats.get('output_tokens', 0)}")

        print(f"\n--- Insights ---")
        for i, insight in enumerate(report.insights, 1):
            print(f"  {i}. {insight}")
        print(f"{'=' * w}\n")
