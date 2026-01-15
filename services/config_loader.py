"""
Config Loader
=============
Loads trading configuration from YAML with environment variable overrides.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Default config path
CONFIG_DIR = Path(__file__).parent.parent / "configs"
DEFAULT_CONFIG = CONFIG_DIR / "trading.yaml"


class TradingConfig:
    """Trading configuration with typed access."""
    
    _instance: Optional["TradingConfig"] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls) -> "TradingConfig":
        """Singleton pattern for config."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self) -> None:
        """Load config from YAML file."""
        config_path = os.environ.get("TRADING_CONFIG_PATH", str(DEFAULT_CONFIG))
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            self._config = self._defaults()
        except yaml.YAMLError as e:
            print(f"Warning: Failed to parse config: {e}")
            self._config = self._defaults()
    
    def _defaults(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "strategies": {
                "DayTrader": {
                    "risk_per_trade": 0.02,
                    "reward_ratio": 2.0,
                    "atr_multiplier": 1.5,
                    "min_score_buy": 3,
                    "min_score_sell": -3,
                },
                "SwingTrader": {
                    "risk_per_trade": 0.03,
                    "reward_ratio": 3.0,
                    "atr_multiplier": 2.0,
                    "min_score_buy": 2,
                    "min_score_sell": -2,
                },
                "Scalper": {
                    "risk_per_trade": 0.01,
                    "reward_ratio": 1.5,
                    "atr_multiplier": 1.0,
                    "min_volume_ratio": 1.5,
                    "min_score_buy": 2,
                    "min_score_sell": -2,
                },
            },
            "indicators": {
                "rsi": {"oversold": 30, "overbought": 70},
                "volume": {"high_threshold": 1.5},
            },
            "api": {
                "yfinance": {"max_retries": 3, "retry_delay_seconds": 2},
            },
            "backtesting": {
                "default_starting_equity": 10000,
                "default_risk_pct": 0.02,
            },
        }
    
    def reload(self) -> None:
        """Force reload configuration."""
        self._load_config()
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get nested config value.
        
        Example: config.get("strategies", "DayTrader", "risk_per_trade")
        """
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            if value is None:
                return default
        return value
    
    def get_strategy(self, name: str) -> Dict[str, Any]:
        """Get strategy-specific config."""
        return self.get("strategies", name, default={})
    
    def get_indicator(self, name: str) -> Dict[str, Any]:
        """Get indicator-specific config."""
        return self.get("indicators", name, default={})
    
    def get_api(self, name: str) -> Dict[str, Any]:
        """Get API-specific config."""
        return self.get("api", name, default={})
    
    @property
    def strategies(self) -> Dict[str, Any]:
        """All strategy configs."""
        return self._config.get("strategies", {})
    
    @property
    def indicators(self) -> Dict[str, Any]:
        """All indicator configs."""
        return self._config.get("indicators", {})
    
    @property
    def backtesting(self) -> Dict[str, Any]:
        """Backtesting config."""
        return self._config.get("backtesting", {})


# Global singleton instance
def get_config() -> TradingConfig:
    """Get the trading configuration singleton."""
    return TradingConfig()
