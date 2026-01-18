"""Quick test of thread-safe agent."""
import sys
import threading
sys.path.insert(0, "c:/Users/super/Watchtower/unk-app-ai")

from services.llm.unk_agent import UnkAiAgent

def test():
    agent = UnkAiAgent()
    print(agent.run("hi"))

t = threading.Thread(target=test)
t.start()
t.join()
print("Thread test complete!")
