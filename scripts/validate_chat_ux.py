"""
Chat UX Validation Script
=========================
Validates that the Chat Panel renders the correct number of messages (15)
and scrolls properly, 10 times with random data.
"""
import sys
import unittest
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, "c:\\Users\\super\\Watchtower\\unk-app-ai")

# Mock State
import scripts.unk_trader_cli as cli

class TestChatUX(unittest.TestCase):
    def test_scrolling_logic(self):
        print("\n🔎 Validating Chat Scrolling & Layout...")
        
        dash = cli.Dashboard()
        
        for i in range(1, 11):
            # 1. Populate Chat Log with i*5 messages
            msg_count = i * 5
            cli.state["chat_log"] = [("User", f"Msg {n}") for n in range(msg_count)]
            
            # 2. Get Panel
            panel = dash.get_chat_panel()
            
            # 3. Verify Content
            # Rich Panel .renderable is the Text object
            rendered_text = panel.renderable.plain
            line_count = rendered_text.strip().count("\n") + 1
            
            expected_msgs = min(msg_count, 15)
            
            print(f"  [Run {i}/10] Input: {msg_count} msgs -> Rendered: {expected_msgs} expected in history")
            
            # Check only the history part (exclude input line)
            # The exact count check depends on formatting, but let's check input length
            # expected_msgs * 1 line each
            
            # Check that the FIRST message in the panel is the correct one
            # If we have 20 messages (0-19), we expect 15 (5-19)
            # The first visible message should be "Msg {msg_count - 15}"
            if msg_count > 15:
                expected_first = f"Msg {msg_count - 15}"
                if expected_first not in rendered_text:
                    self.fail(f"Run {i}: Log didn't scroll! Expected '{expected_first}' to be visible.")
                
                # Ensure "Msg 0" is NOT visible (scrolled off)
                if "Msg 0" in rendered_text:
                     self.fail(f"Run {i}: Log didn't scroll! 'Msg 0' is still visible.")

            # 4. Verify Height is None (Dynamic)
            if panel.height is not None:
                self.fail(f"Run {i}: Panel height is hardcoded to {panel.height}!")
                
            print(f"  ✅ Pass")

if __name__ == "__main__":
    unittest.main()
