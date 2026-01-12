"""
Thread Runner Training Module
=============================
Handles the curation of Thread execution history into training datasets
and triggering of Vertex AI tuning jobs.
"""

import json
import logging
from typing import List, Dict, Any
from .models import Thread, ThreadStatus

logger = logging.getLogger("thread_runner.training")

class TrainingManager:
    def __init__(self):
        pass

    def extract_training_examples(self, threads: List[Thread]) -> List[Dict[str, Any]]:
        """
        Converts successful threads into Gemini SFT examples.
        Format: {"messages": [{"role": "user", "content": ...}, {"role": "model", "content": ...}]}
        """
        dataset = []
        for thread in threads:
            # Filter for high-quality data
            if thread.status != ThreadStatus.COMPLETED and thread.status != ThreadStatus.WAITING_FOR_REVIEW:
                continue

            # Check validations (only train on passing threads)
            if any(v.status == "fail" for v in thread.validations):
                continue

            # Construct SFT Example
            # Input: The Goal & Context
            user_msg = f"Goal: {thread.goal}\nContext Refs: {thread.context_refs}"

            # Output: The Tool Trajectory key steps or Final Summary
            # For strict tool-use training, we'd format the tool calls.
            # For simple instruction tuning, we use the final summary or correct plan execution.
            model_msg = thread.final_summary or "Execution completed."

            example = {
                "messages": [
                    {"role": "user", "content": user_msg},
                    {"role": "model", "content": model_msg}
                ]
            }
            dataset.append(example)

        return dataset

    def save_dataset_jsonl(self, dataset: List[Dict[str, Any]], filepath: str):
        """Saves dataset to JSONL for Vertex AI."""
        with open(filepath, "w", encoding="utf-8") as f:
            for example in dataset:
                f.write(json.dumps(example) + "\n")
        logger.info(f"Saved {len(dataset)} examples to {filepath}")

    def trigger_tuning_job(self, dataset_gcs_uri: str, base_model: str = "gemini-1.5-pro-002"):
        """
        Triggers a Vertex AI Supervised Fine-Tuning job.
        (Placeholder for actual Vertex AI Pipeline call)
        """
        logger.info(f"🚀 Triggering Tuning Job on {base_model}")
        logger.info(f"Dataset: {dataset_gcs_uri}")
        return "job-id-placeholder-123"

# Singleton
training_manager = TrainingManager()
