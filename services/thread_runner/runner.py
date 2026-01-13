"""

Thread Runner Service

=====================

Orchestrates the execution of Threads using Vertex AI Gemini.

"""


import asyncio
from datetime import datetime

from google import genai
from google.api_core.exceptions import (InternalServerError, ResourceExhausted,
                                        ServiceUnavailable)
from google.genai import types
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_exponential)

from services.thread_runner.evals import Rubric
from services.thread_runner.models import Thread, ThreadStatus
from services.thread_runner.persistence import store
from services.thread_runner.telemetry import telemetry
from services.thread_runner.tools import THREAD_TOOLS

# ... imports ...


class ThreadRunner:

    def __init__(self, project_id: str, location: str = "us-central1"):

        self.project_id = project_id

        self.location = location

        self.client = genai.Client(vertexai=True, project=project_id, location=location)

        self.model_id = "gemini-2.0-flash-001"

        # Initialize Skills

        from skills.slack_skill import SlackSkill

        self.slack = SlackSkill()

    @retry(

        retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable, InternalServerError)),

        stop=stop_after_attempt(3),

        wait=wait_exponential(multiplier=1, min=2, max=10)

    )
    async def _execute_turn_with_retry(self, chat, input_text):

        return await chat.send_message(input_text)

    async def run_thread(self, thread: Thread) -> Thread:
        """

        Executes a thread to completion or review gate.

        """

        print(f"🚀 Starting Thread {thread.thread_id}: {thread.goal}")

        telemetry.log_event(thread.thread_id, "THREAD_START", {"goal": thread.goal})

        self.slack.post_message(
            "C08678XJ66C", f"🧵 *Thread Started* `{thread.thread_id[:8]}`\n**Goal**: {thread.goal}")

        # Note: Channel ID should be env var or config, defaulting to general/notification channel

        start_time = datetime.utcnow()

        thread.status = ThreadStatus.RUNNING

        await store.save_thread(thread)  # PERSIST START

        # Hydrate system prompt with context

        system_prompt = f"""You are a Thread Runner Agent.

        Goal: {thread.goal}

        Context Refs: {thread.context_refs}



        Execute the necessary tools to achieve the goal.



        CRITICAL:

        1. REFLECT: Before every tool call, briefly think about *why* you are calling it.

        2. VERIFY: If a tool fails, analyze the error before retrying.

        3. MEMORY: Use `search_codebase_semantically` if you lack context.



        Think step-by-step. Update the plan if needed.

        """

        # Initialize Chat

        chat = self.client.aio.chats.create(

            model=self.model_id,

            config=types.GenerateContentConfig(

                system_instruction=system_prompt,

                tools=THREAD_TOOLS,

                temperature=0.0

            )

        )

        try:

            # Create map for execution

            tool_map = {func.__name__: func for func in THREAD_TOOLS}

            # Initialization

            turn_count = 0

            max_turns = 100

            final_response_text = ""

            # Initial Trigger

            response = await self._execute_turn_with_retry(chat, "Please start execution.")

            while turn_count < max_turns:

                turn_count += 1

                # Check for tool calls

                candidate = response.candidates[0]

                tool_calls = [
                    part.function_call for part in candidate.content.parts if part.function_call]

                if tool_calls:

                    print(
                        f"🛠️ Turn {turn_count}: Tool Calls detected: {[tc.name for tc in tool_calls]}")

                    # Execute all tools in this turn (parallel if possible, sequential for now)

                    tool_responses = []

                    for tool_call in tool_calls:

                        tool_name = tool_call.name

                        tool_args = tool_call.args

                        if tool_name in tool_map:

                            try:

                                print(f"  -> Executing {tool_name}({tool_args})")

                                # Execute Sync Tool

                                result = tool_map[tool_name](**tool_args)

                                # Construct Response

                                response_part = types.Part.from_function_response(

                                    name=tool_name,

                                    response={"result": result}

                                )

                                tool_responses.append(response_part)

                            except Exception as e:  # pylint: disable=W0718

                                print(f"  ❌ Error executing {tool_name}: {e}")

                                response_part = types.Part.from_function_response(

                                    name=tool_name,

                                    response={"error": str(e)}

                                )

                                tool_responses.append(response_part)

                        else:

                            print(f"  ❌ Unknown tool: {tool_name}")

                            response_part = types.Part.from_function_response(

                                name=tool_name,

                                response={"error": "Tool not found"}

                            )

                            tool_responses.append(response_part)

                    # Send results back to model

                    response = await self._execute_turn_with_retry(chat, tool_responses)

                    continue  # Loop back for next model output

                # If no tool calls, it's a text response (summary or question)

                final_response_text = candidate.content.parts[0].text if candidate.content.parts else "Reference: No content."

                # Check for explicit completion

                if "TASK_COMPLETE" in final_response_text:

                    break

                # If just text (reasoning), allow it to continue by prompting for next step

                print(
                    f"  💬 Text detected ({len(final_response_text)} chars). Prompting to proceed...")

                response = await self._execute_turn_with_retry(chat, "Proceed with the next step. If finished, say TASK_COMPLETE.")

            summary = final_response_text

            thread.final_summary = summary

            # --- EVALUATION LOOP ---

            # Calculate metrics

            end_time = datetime.utcnow()

            latency = (end_time - start_time).total_seconds() * 1000

            thread.metrics["latency_ms"] = latency

            thread.metrics["tool_calls"] = turn_count

            # Run Rubrics

            thread.validations = Rubric.evaluate_thread(thread)

            # Determine Status based on critical evals

            if any(v.status == "fail" and v.check == "no_tool_failures" for v in thread.validations):

                thread.status = ThreadStatus.FAILED

                icon = "❌"

            else:

                thread.status = ThreadStatus.WAITING_FOR_REVIEW

                icon = "✅"

            thread.updated_at = end_time

            await store.save_thread(thread)  # PERSIST END

            # Telemetry

            telemetry.record_metric(thread.thread_id, "latency_ms", latency)

            telemetry.log_event(thread.thread_id, "THREAD_COMPLETE", {"status": thread.status})

            msg = f"{icon} *Thread {thread.status}* `{thread.thread_id[:8]}`\n**Summary**: {summary[:100]}..."

            self.slack.post_message("C08678XJ66C", msg)

            print(f"✅ Thread [{thread.status}]: {summary[:50]}...")

        except Exception as e:  # pylint: disable=W0718

            print(f"❌ Thread Failed: {e}")

            telemetry.log_event(thread.thread_id, "THREAD_ERROR", {"error": str(e)})

            thread.status = ThreadStatus.FAILED

            thread.final_summary = str(e)

            await store.save_thread(thread)  # PERSIST ERROR

            self.slack.post_message(
                "C08678XJ66C", f"🚨 *Thread Failed* `{thread.thread_id[:8]}`\nError: {str(e)}")

        return thread


# Test entry point
if __name__ == "__main__":

    async def main():

        runner = ThreadRunner("unk-app-480102")

        t = Thread(goal="Fix the login page typo", context_refs=["ticket-123"])

        result = await runner.run_thread(t)

        print(result.json(indent=2))

    asyncio.run(main())
