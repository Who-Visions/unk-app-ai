"""
20-Turn Efficiency Validation
==============================
Tests chat response times and refactors for efficiency.
Target: <500ms per response.

Who Visions LLC - AI with Dav3
"""

import sys
import time
import statistics
from datetime import datetime

sys.path.insert(0, "c:\\Users\\super\\Watchtower\\unk-app-ai")


class EfficiencyValidator:
    """20-Turn efficiency validation with timing."""
    
    def __init__(self):
        self.latencies = []
        self.turn = 0
        self.target_ms = 500  # Target: <500ms
        
    def run_turn(self, query: str) -> tuple:
        """Run a single query and measure latency."""
        self.turn += 1
        print(f"\n[{self.turn}/20] Query: {query[:50]}...")
        
        start = time.time()
        try:
            from services.llm.unk_agent import UnkAiAgent
            from services.trading_memory import TradingMemory
            
            # Get context (should be fast - cached)
            tm = TradingMemory()
            ctx_start = time.time()
            context = tm.get_context_for_ai()
            ctx_time = (time.time() - ctx_start) * 1000
            
            # Build prompt
            prompt = f"{context}\n\nUSER: {query}"
            
            # Call Gemini Flash with minimal thinking
            agent_start = time.time()
            agent = UnkAiAgent(mode="unk")
            resp = agent.run(
                prompt,
                config={
                    "system_instruction": "You are Unk. Answer concisely.",
                    "thinking_config": {"thinking_level": "low"}
                }
            )
            agent_time = (time.time() - agent_start) * 1000
            
            total_time = (time.time() - start) * 1000
            self.latencies.append(total_time)
            
            status = "✅" if total_time < self.target_ms else "⚠️"
            print(f"  {status} {total_time:.0f}ms (ctx:{ctx_time:.0f}ms, ai:{agent_time:.0f}ms)")
            print(f"  Response: {resp[:80]}..." if len(resp) > 80 else f"  Response: {resp}")
            
            return total_time, resp, None
            
        except Exception as e:
            total_time = (time.time() - start) * 1000
            print(f"  ❌ FAILED ({total_time:.0f}ms): {e}")
            return total_time, None, str(e)
    
    def run_all(self):
        """Run all 20 validation turns."""
        print("="*60)
        print("⚡ 20-TURN EFFICIENCY VALIDATION")
        print(f"Target: <{self.target_ms}ms per response")
        print("="*60)
        print(f"Started: {datetime.now().isoformat()}")
        
        queries = [
            # Simple queries (should be ~200ms)
            "hi",
            "what time is it",
            "how are you",
            "thanks",
            "ok",
            
            # Trading context queries (should be ~300ms)
            "what's my P&L",
            "show my holdings",
            "last trade",
            "how many trades today",
            "am I profitable",
            
            # Slightly complex (should be ~400ms)
            "what crypto should I buy",
            "is BTC a good investment",
            "what's the market doing",
            "should I sell my ETH",
            "analyze my portfolio",
            
            # More complex (may be ~500ms+)
            "give me a trading strategy",
            "explain my recent performance",
            "what are the risks",
            "help me understand my gains",
            "summarize my trading activity",
        ]
        
        errors = []
        for q in queries[:20]:
            latency, resp, err = self.run_turn(q)
            if err:
                errors.append(f"Turn {self.turn}: {err}")
        
        self._print_summary(errors)
    
    def _print_summary(self, errors):
        print("\n" + "="*60)
        print("📊 EFFICIENCY SUMMARY")
        print("="*60)
        
        if not self.latencies:
            print("No successful turns!")
            return
        
        avg = statistics.mean(self.latencies)
        med = statistics.median(self.latencies)
        p95 = sorted(self.latencies)[int(len(self.latencies) * 0.95)] if len(self.latencies) > 1 else self.latencies[0]
        fastest = min(self.latencies)
        slowest = max(self.latencies)
        
        under_target = sum(1 for l in self.latencies if l < self.target_ms)
        
        print(f"Turns: {len(self.latencies)}/20")
        print(f"Under {self.target_ms}ms: {under_target}/{len(self.latencies)} ({under_target/len(self.latencies)*100:.0f}%)")
        print(f"Average: {avg:.0f}ms")
        print(f"Median: {med:.0f}ms")
        print(f"P95: {p95:.0f}ms")
        print(f"Fastest: {fastest:.0f}ms")
        print(f"Slowest: {slowest:.0f}ms")
        
        if errors:
            print(f"\n❌ Errors: {len(errors)}")
            for e in errors:
                print(f"  • {e}")
        
        # Grade
        if avg < 300:
            print("\n🏆 EXCELLENT - Average under 300ms!")
        elif avg < 500:
            print("\n✅ GOOD - Average under 500ms")
        elif avg < 1000:
            print("\n⚠️ ACCEPTABLE - Needs optimization")
        else:
            print("\n❌ POOR - Major optimization needed")
        
        print("="*60)


if __name__ == "__main__":
    validator = EfficiencyValidator()
    validator.run_all()
