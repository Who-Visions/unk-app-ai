"""
Elliott Wave Analysis Module
============================
Detects Elliott Wave patterns in price data.

Theory:
- Impulse waves: 5-wave motive pattern (1-2-3-4-5)
- Corrective waves: 3-wave pattern (A-B-C)
- Wave 2 never retraces more than 100% of Wave 1
- Wave 3 cannot be the shortest impulse wave
- Wave 4 never enters Wave 1 price territory
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Tuple


class WaveType(Enum):
    """Type of Elliott Wave pattern."""
    IMPULSE = "impulse"      # 5-wave motive pattern
    CORRECTIVE = "corrective"  # 3-wave ABC pattern


class WaveLabel(Enum):
    """Individual wave labels."""
    WAVE_1 = "1"
    WAVE_2 = "2"
    WAVE_3 = "3"
    WAVE_4 = "4"
    WAVE_5 = "5"
    WAVE_A = "A"
    WAVE_B = "B"
    WAVE_C = "C"


@dataclass
class Wave:
    """Represents a single Elliott wave."""
    label: WaveLabel
    wave_type: WaveType
    start_price: float
    end_price: float
    start_idx: int
    end_idx: int
    
    @property
    def is_up(self) -> bool:
        return self.end_price > self.start_price
    
    @property
    def magnitude(self) -> float:
        return abs(self.end_price - self.start_price)


def find_pivots(prices: List[float], window: int = 5) -> Tuple[List[int], List[int]]:
    """
    Find pivot highs and lows in price data.
    
    Args:
        prices: List of prices
        window: Lookback/forward window for pivot detection
    
    Returns:
        Tuple of (pivot_high_indices, pivot_low_indices)
    """
    if len(prices) < window * 2 + 1:
        return [], []
    
    pivot_highs = []
    pivot_lows = []
    
    for i in range(window, len(prices) - window):
        # Check if pivot high
        is_high = all(prices[i] >= prices[i-j] and prices[i] >= prices[i+j] 
                      for j in range(1, window + 1))
        if is_high:
            pivot_highs.append(i)
        
        # Check if pivot low
        is_low = all(prices[i] <= prices[i-j] and prices[i] <= prices[i+j] 
                     for j in range(1, window + 1))
        if is_low:
            pivot_lows.append(i)
    
    return pivot_highs, pivot_lows


def detect_impulse_pattern(
    prices: List[float],
    pivot_highs: List[int],
    pivot_lows: List[int]
) -> Optional[List[Wave]]:
    """
    Attempt to detect a 5-wave impulse pattern.
    
    Simplified algorithm:
    1. Find alternating high/low sequence
    2. Validate Elliott Wave rules
    
    Returns:
        List of 5 waves if pattern found, None otherwise
    """
    # Merge and sort pivots
    all_pivots = [(i, "high", prices[i]) for i in pivot_highs] + \
                 [(i, "low", prices[i]) for i in pivot_lows]
    all_pivots.sort(key=lambda x: x[0])
    
    if len(all_pivots) < 5:
        return None
    
    # Look for 5-wave pattern in last 6 pivots
    recent = all_pivots[-6:] if len(all_pivots) >= 6 else all_pivots
    
    # Basic validation - need alternating highs and lows
    waves = []
    for i in range(len(recent) - 1):
        wave_num = i + 1
        if wave_num > 5:
            break
        
        start_idx, _, start_price = recent[i]
        end_idx, _, end_price = recent[i + 1]
        
        label = WaveLabel(str(wave_num))
        waves.append(Wave(
            label=label,
            wave_type=WaveType.IMPULSE,
            start_price=start_price,
            end_price=end_price,
            start_idx=start_idx,
            end_idx=end_idx
        ))
    
    if len(waves) < 3:
        return None
    
    # Validate Elliott rules
    if validate_impulse_rules(waves):
        return waves
    
    return None


def validate_impulse_rules(waves: List[Wave]) -> bool:
    """
    Validate Elliott Wave impulse rules.
    
    Rules:
    1. Wave 2 never retraces more than 100% of Wave 1
    2. Wave 3 cannot be the shortest of waves 1, 3, 5
    3. Wave 4 never enters Wave 1 price territory
    """
    if len(waves) < 3:
        return False
    
    wave1 = waves[0] if len(waves) > 0 else None
    wave2 = waves[1] if len(waves) > 1 else None
    wave3 = waves[2] if len(waves) > 2 else None
    wave4 = waves[3] if len(waves) > 3 else None
    wave5 = waves[4] if len(waves) > 4 else None
    
    # Rule 1: Wave 2 retracement
    if wave1 and wave2:
        if wave2.magnitude > wave1.magnitude:
            return False
    
    # Rule 2: Wave 3 not shortest
    if wave1 and wave3 and wave5:
        if wave3.magnitude < min(wave1.magnitude, wave5.magnitude):
            return False
    
    # Rule 3: Wave 4 doesn't overlap Wave 1
    if wave1 and wave4:
        if wave1.is_up:  # Uptrend
            if wave4.end_price < wave1.end_price:
                return False
        else:  # Downtrend
            if wave4.end_price > wave1.end_price:
                return False
    
    return True


def get_wave_context(prices: List[float], window: int = 5) -> Dict:
    """
    Analyze price data and return current Elliott Wave context.
    
    Args:
        prices: Historical price data
        window: Pivot detection window
    
    Returns:
        Dict with wave analysis results
    """
    if len(prices) < 20:
        return {
            "pattern": "INSUFFICIENT_DATA",
            "wave_count": 0,
            "current_wave": "N/A",
            "context": "Need more price history",
            "confidence": 0.0
        }
    
    pivot_highs, pivot_lows = find_pivots(prices, window)
    
    # Try to detect impulse pattern
    impulse = detect_impulse_pattern(prices, pivot_highs, pivot_lows)
    
    if impulse and len(impulse) >= 3:
        last_wave = impulse[-1]
        current_num = int(last_wave.label.value) if last_wave.label.value.isdigit() else 0
        next_wave = current_num + 1 if current_num < 5 else "Correction"
        
        if current_num in [1, 3]:
            context = f"Wave {current_num} complete. Expect corrective Wave {current_num + 1}"
        elif current_num in [2, 4]:
            context = f"Wave {current_num} correction. Expect impulse Wave {current_num + 1}"
        elif current_num == 5:
            context = "Wave 5 complete. Expect ABC correction"
        else:
            context = "Pattern developing"
        
        return {
            "pattern": "IMPULSE",
            "wave_count": len(impulse),
            "current_wave": f"Wave {current_num}",
            "next_expected": str(next_wave),
            "trend": "BULLISH" if impulse[-1].is_up else "BEARISH",
            "context": context,
            "confidence": 0.6 + (0.1 * len(impulse))  # Higher confidence with more waves
        }
    
    # Check for general trend if no clear pattern
    if len(prices) >= 10:
        trend = "BULLISH" if prices[-1] > prices[-10] else "BEARISH"
        return {
            "pattern": "DEVELOPING",
            "wave_count": 0,
            "current_wave": "N/A",
            "trend": trend,
            "context": f"No clear wave pattern. General trend: {trend}",
            "confidence": 0.3
        }
    
    return {
        "pattern": "UNKNOWN",
        "wave_count": 0,
        "current_wave": "N/A",
        "context": "Unable to determine pattern",
        "confidence": 0.0
    }
