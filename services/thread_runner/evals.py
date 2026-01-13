"""
Thread Runner Evals (Rubrics)
=============================
Defines success/fail logic for threads.
"""

from typing import List

from .models import Thread, ValidationRecord


class Rubric:
    @staticmethod
    def evaluate_thread(thread: Thread) -> List[ValidationRecord]:
        """Runs all applicable checks on a thread."""
        validations = []

        # Check 1: Goal Completion (Heuristic)
        # Did the model explicitly say it's done?
        # (In a real implementation, we'd check the final turn content)
        if thread.final_summary:
            validations.append(ValidationRecord(
                check="has_summary",
                status="pass"
            ))
        else:
            validations.append(ValidationRecord(
                check="has_summary",
                status="fail",
                evidence_ref="Missing final summary"
            ))

        # Check 2: Tool Usage Health
        # Did any tools fail?
        failed_tools = [t for t in thread.tool_trajectory if t.status == "error"]
        if failed_tools:
            validations.append(ValidationRecord(
                check="no_tool_failures",
                status="fail",
                evidence_ref=f"{len(failed_tools)} tools failed"
            ))
        else:
            validations.append(ValidationRecord(
                check="no_tool_failures",
                status="pass"
            ))

        # Check 3: Latency (Soft Eval)
        # Is it too slow?
        if thread.metrics.get("latency_ms", 0) > 30000:  # 30s limit
            validations.append(ValidationRecord(
                check="latency_sla",
                status="fail",
                evidence_ref=f"Latency {thread.metrics['latency_ms']}ms > 30s"
            ))
        else:
            validations.append(ValidationRecord(
                check="latency_sla",
                status="pass"
            ))

        return validations
