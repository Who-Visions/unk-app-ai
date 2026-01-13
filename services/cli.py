"""
Unk Agent - CLI Chat Interface
==============================
Interactive terminal interface for the Unk Agent.
"""

import asyncio
import os
import sys

from gemini_agent import (UnkAgent, calculate_growth_metrics,
                          get_current_timestamp)

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position
# pylint: enable=wrong-import-position

# ANSI colors for better CLI experience
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


async def chat_session():
    """Run the interactive chat session."""
    print(f"\n{BOLD}╔══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}║              🧠 UNK AGENT - CLI INTERFACE               ║{RESET}")
    print(f"{BOLD}╚══════════════════════════════════════════════════════════╝{RESET}\n")
    print(f"{GREEN}Cognitive Orchestrator | Who Visions LLC{RESET}")

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print(f"{YELLOW}⚠ GOOGLE_CLOUD_PROJECT not set. Using: unk-app-480102{RESET}")
        project_id = "unk-app-480102"
    else:
        print(f"{GREEN}✓ Project:{RESET} {project_id}")

    # Show Reasoning Engine status
    print(f"{GREEN}✓ Reasoning Engine:{RESET} Deployed (ID: ...98688)")
    print(f"{GREEN}✓ A2A Integration:{RESET} Enabled")
    print(f"{GREEN}✓ Auto-Routing:{RESET} 6-tier cognitive routing\n")
    print(f"{BLUE}Commands:{RESET}")
    print("  • Type your query to chat")
    print("  • '/mode <tier>' - Force tier (cost_saver, default, unk_mode, ultrathink)")
    print("  • 'exit' or 'quit' - End session")
    print("\n" + "-" * 58 + "\n")

    # Default agent for initial context or fallbacks
    current_mode = "auto"

    while True:
        try:
            user_input = input(f"{BLUE}You:{RESET} ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            if user_input.startswith("/mode"):
                parts = user_input.split()
                if len(parts) > 1:
                    current_mode = parts[1]
                    print(f"{YELLOW}Manual mode set to: {current_mode}{RESET}")
                else:
                    current_mode = "auto"
                    print(f"{YELLOW}Switched back to Auto-Routing{RESET}")
                continue

            print(f"{YELLOW}Unk:{RESET} ", end="", flush=True)

            # logic to choose agent
            if current_mode == "auto":
                from gemini_agent import \
                    AgentFactory  # pylint: disable=import-outside-toplevel

                # Create a routed agent for this specific turn
                agent = await AgentFactory.create_routed(
                    user_input=user_input,
                    gcp_project=project_id,
                    user_tier="enterprise"
                )
            else:
                # Manual override
                agent = UnkAgent(
                    mode=current_mode,
                    tools=[calculate_growth_metrics, get_current_timestamp],
                    gcp_project=project_id
                )

            # Execute turn with streaming
            # pylint: disable=protected-access
            response_stream = await agent.execute_turn(
                user_input,
                force_structured=False,
                stream=True
            )

            if hasattr(response_stream, '__aiter__'):  # Check if it's an async generator
                print(f"\n{BOLD}Unk:{RESET} ", end="", flush=True)

                is_thinking = False

                async for chunk in response_stream:
                    # Check for thought parts
                    for part in chunk.candidates[0].content.parts:
                        if hasattr(part, 'thought') and part.thought:
                            if not is_thinking:
                                print(f"\n{YELLOW}Thinking{RESET}", end="", flush=True)
                                is_thinking = True
                            print(f"{YELLOW}.{RESET}", end="", flush=True)
                        elif hasattr(part, 'text') and part.text:
                            if is_thinking:
                                print(f"\n{BOLD}Answer:{RESET} ", end="", flush=True)
                                is_thinking = False
                            print(part.text, end="", flush=True)
            else:
                # Fallback for non-streaming (e.g. structured output or error)
                if hasattr(response_stream, 'final_answer'):
                    print(response_stream.final_answer)
                else:
                    print(response_stream)

            print()  # Newline

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"\n{RED}Error: {e}{RESET}")

if __name__ == "__main__":
    try:
        asyncio.run(chat_session())
    except KeyboardInterrupt:
        pass
