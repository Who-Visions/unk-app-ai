import json
import time
import os
from enum import Enum
from datetime import datetime

class GovernorState(Enum):
    MONITORING = "MONITORING"
    ARMED = "ARMED"
    IN_TRADE = "IN_TRADE"
    LOCKOUT = "LOCKOUT"

class SafeGovernor:
    def __init__(self, config_path=None):
        if config_path is None:
            # Absolute path to avoid lookup issues in refactored structure
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "configs", "governor.json")
            
        self.config_path = config_path
        self.config = self._load_config()
        
        # State
        self.state = GovernorState.MONITORING
        self.daily_pnl_pct = 0.0
        self.consecutive_losses = 0
        self.lockout_until = 0
        
        # Rate Limiting
        self.last_order_time_global = 0
        self.last_order_time_symbol = {}
        
        print(f"🛡️ SafeGovernor Initialized (Mode: {self.config['governor']['mode']})")

    def _load_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def _check_rate_gate(self, symbol):
        now = time.time()
        gate = self.config["rate_gate"]
        
        # Global Check
        if now - self.last_order_time_global * 1000 < gate["min_time_between_any_orders_ms_global"]:
            return False, "Global Rate Limit"
            
        # Symbol Check
        last_sym = self.last_order_time_symbol.get(symbol, 0)
        if now - last_sym * 1000 < gate["min_time_between_orders_ms_per_symbol"]:
            return False, f"Symbol Rate Limit ({symbol})"
            
        return True, ""

    def _check_risk_gate(self):
        gate = self.config["risk_gate"]
        
        # Daily Loss
        if self.daily_pnl_pct <= -gate["max_daily_loss_pct"]:
            self.state = GovernorState.LOCKOUT
            return False, "Max Daily Loss Exceeded"
            
        # Consecutive Losses
        if self.consecutive_losses >= gate["max_consecutive_losses"]:
            # Check if lockout period has passed
            if time.time() < self.lockout_until:
                return False, f"Loss Streak Lockout ({int(self.lockout_until - time.time())}s remaining)"
            else:
                # Reset after lockout
                self.consecutive_losses = 0
                
        return True, ""

    def _check_liquidity_gate(self, symbol):
        gate = self.config["liquidity_gate"]
        allowed_lists = []
        for tier in gate["allowed_tiers"]:
            allowed_lists.extend(gate.get(tier, []))
            
        if symbol not in allowed_lists:
            return False, f"Symbol {symbol} not in allowed tiers"
            
        return True, ""

    def _check_churn_gate(self, symbol, action, last_buy_time=0):
        if not self.config.get("churn_gate", {}).get("enabled", False):
            return True, ""
            
        if action.lower() != "sell":
            return True, ""
            
        if symbol in self.config["churn_gate"].get("allowed_exceptions", []):
            return True, ""
            
        if last_buy_time <= 0:
            return True, "" # No data, assume safe or manual override needed
            
        min_hold = self.config["churn_gate"]["min_hold_minutes"] * 60
        held_time = time.time() - last_buy_time
        
        if held_time < min_hold:
            return False, f"Anti-Churn: Must hold for {int(min_hold/60)}m (Held: {int(held_time/60)}m)"
            
        return True, ""

    def _check_hard_floor(self, symbol, action, current_price, entry_price):
        gate = self.config.get("hard_floor", {})
        if not gate.get("enabled", False):
            return True, ""
            
        if action.lower() != "sell":
            return True, ""
            
        if entry_price <= 0 or current_price <= 0:
            return True, ""
            
        # COST_BASIS Protection
        if gate.get("mode") == "COST_BASIS":
            # If Loss > 0 (Price < Entry)
            if current_price < entry_price:
                # Check for Stop-Loss Exception (Reversal)
                # Not fully implemented without trend data, so we Hard Block for now
                return False, f"Hard Floor: Price ${current_price:.6f} < Entry ${entry_price:.6f}"
        
        return True, ""

    def can_trade(self, symbol, action="buy", current_spread_bps=0, current_price=0, entry_price=0, last_buy_time=0):
        # 1. Check State
        if self.state == GovernorState.LOCKOUT:
            return False, "Governor LOCKOUT"
            
        # 2. Check Risk
        passed, reason = self._check_risk_gate()
        if not passed: return False, reason
        
        # 3. Check Rate
        passed, reason = self._check_rate_gate(symbol)
        if not passed: return False, reason
        
        # 4. Check Liquidity
        passed, reason = self._check_liquidity_gate(symbol)
        if not passed: return False, reason
        
        # 5. Check Spread (Market Gate)
        gate = self.config["market_gate"]
        is_major = symbol in self.config["liquidity_gate"]["tier_1_majors"]
        max_spread = gate["max_spread_bps_majors"] if is_major else gate["max_spread_bps_alts"]
        
        if current_spread_bps > max_spread:
            return False, f"Spread {current_spread_bps}bps > {max_spread}bps Limit"
            
        # 6. Check Churn (V2)
        passed, reason = self._check_churn_gate(symbol, action, last_buy_time)
        if not passed: return False, reason
        
        # 7. Check Hard Floor (V2)
        passed, reason = self._check_hard_floor(symbol, action, current_price, entry_price)
        if not passed: return False, reason
            
        return True, "OK"

    def record_order(self, symbol):
        now = time.time()
        self.last_order_time_global = now
        self.last_order_time_symbol[symbol] = now
        self.state = GovernorState.IN_TRADE

    def record_result(self, pnl_pct):
        self.daily_pnl_pct += pnl_pct
        
        if pnl_pct < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
            
        # Check for Lockout Trigger
        gate = self.config["risk_gate"]
        if self.consecutive_losses >= gate["max_consecutive_losses"]:
            lockout_sec = gate["lockout_minutes_after_streak"] * 60
            self.lockout_until = time.time() + lockout_sec
            self.state = GovernorState.LOCKOUT
            print(f"⛔ Governor: Loss Streak Lockout triggered until {datetime.fromtimestamp(self.lockout_until)}")
        else:
            self.state = GovernorState.MONITORING

    def get_status(self):
        return {
            "state": self.state.value,
            "daily_pnl": f"{self.daily_pnl_pct:.2f}%",
            "streak": self.consecutive_losses,
            "lockout": max(0, int(self.lockout_until - time.time()))
        }
