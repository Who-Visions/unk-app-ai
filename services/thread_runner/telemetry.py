"""
Thread Runner Telemetry
=======================
Handles logging, metrics, and Notion dashboard integration.
"""

import logging
from typing import Any, Dict

# Lazy import NotionSkill to avoid circular dependency if needed
try:
    from skills.notion_skill import NotionSkill
except ImportError:
    NotionSkill = None

logger = logging.getLogger("thread_runner")


class Telemetry:
    def __init__(self):
        self.notion = NotionSkill() if NotionSkill else None

    def log_event(self, thread_id: str, event_type: str, details: Dict[str, Any]):
        """Logs a structural event (e.g., tool_call, validation)."""
        logger.info(f"[{thread_id}] {event_type}: {details}")
        # In future: Push to BigQuery or Firestore

    def record_metric(self, thread_id: str, metric_name: str, value: float):
        """Records a numerical metric (latency, tokens)."""
        logger.info(f"[{thread_id}] METRIC {metric_name}={value}")

        # Push to Notion Dashboard (AI Training Data DB)
        if self.notion:
            # We prefix with Thread ID for context
            model_name = "ThreadRunner"
            res = self.notion.log_training_metric(model_name, metric_name, value)
            if "Skipped" in res:
                logger.debug(f"Notion Log Skipped: {res}")
            elif "Failed" in res:
                logger.warning(f"Notion Log Failed: {res}")


telemetry = Telemetry()
