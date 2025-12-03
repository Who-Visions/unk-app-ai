"""
Unk Agent - CLI Chat Interface
==============================
Interactive terminal interface for the Unk Agent.
"""

import asyncio
import os
import sys
from gemini_agent import UnkAgent, calculate_growth_metrics, get_current_timestamp

# ANSI colors for better CLI experience
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

async def chat_session():
    print(f"{BOLD}Unk Agent CLI{RESET}")
    print("Initializing...")

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print(f"{YELLOW}Warning: GOOGLE_CLOUD_PROJECT not set. Defaulting to 'who-visions-llc'{RESET}")
        project_id = "who-visions-llc"

    print(f"{GREEN}Connected to Unk Agent (Auto-Routing Enabled){RESET}")
    print("Type 'exit' or 'quit' to end the session.")
    print("Type '/mode <mode_name>' to force a specific mode.")
    print("-" * 50)

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
                from gemini_agent import AgentFactory
                # Create a routed agent for this specific turn
                # In a real app, we'd pass history here to maintain context
                agent = await AgentFactory.create_routed(
                    user_input=user_input,
                    gcp_project=project_id,
                    # Assuming 'pro' tier for CLI user to access all models
                    user_tier="enterprise" 
                )
                # print(f"(Routing to: {agent.mode})... ", end="", flush=True)
            else:
                # Manual override
                agent = UnkAgent(
                    mode=current_mode,
                    tools=[calculate_growth_metrics, get_current_timestamp],
                    gcp_project=project_id
                )
            
            # Execute turn with streaming
            response_stream = await agent.execute_turn(user_input, force_structured=False, stream=True)
            
            if hasattr(response_stream, '__aiter__'): # Check if it's an async generator
                print(f"\n{BOLD}Unk:{RESET} ", end="", flush=True)
                
                thought_buffer = ""
                is_thinking = False
                
                async for chunk in response_stream:
                    # Check for thought parts
                    # Note: Structure depends on SDK. Usually chunk.candidates[0].content.parts[0]
                    # The SDK wrapper might yield simpler objects if not raw.
                    # Assuming standard SDK response chunks.
                    
                    for part in chunk.candidates[0].content.parts:
                        if hasattr(part, 'thought') and part.thought:
                            if not is_thinking:
                                print(f"\n{YELLOW}Thinking{RESET}", end="", flush=True)
                                is_thinking = True
                            print(f"{YELLOW}.{RESET}", end="", flush=True)
                            # thought_buffer += part.text
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
                
            print() # Newline

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\n{RED}Error: {e}{RESET}")

if __name__ == "__main__":
    try:
        asyncio.run(chat_session())
    except KeyboardInterrupt:
        pass
