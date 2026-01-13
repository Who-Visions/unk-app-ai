import sys
import os
from pathlib import Path

# POC: Verify SpecialistStrategy loads and follows 5-step interface
try:
    from services.strategies.specialist import SpecialistStrategy
    from services.betting_types import BettingRequest
    
    print("✅ Successfully imported SpecialistStrategy")
    
    strat = SpecialistStrategy()
    print(f"✅ Instantiated {strat.name}")
    
    req = BettingRequest(
        strategy="Specialist",
        sport="nba",
        market="moneyline",
        bankroll=1000.0,
        inputs={}
    )
    
    # Run the pipeline
    decision = strat.decide(req, config={})
    print(f"✅ Decision generated: {decision.action} on {decision.selection}")
    print(f"✅ Unk says: {decision.metadata.get('unk_explanation')}")
    
except Exception as e:
    print(f"❌ Verification Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
