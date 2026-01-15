# Unk Trading System Documentation

Comprehensive day trading and stock analysis capabilities for the Unk Agent.

---

## Overview

Unk now has **Advanced Trading Skills** powered by:
- **yfinance** for real-time market data
- **stockstats** for technical indicators (RSI, MACD, Bollinger, ATR)
- **Gemini AI** with Google Search grounding for analysis
- **ML-inspired scoring** from research repos

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CHAT WITH UNK                            │
│                    chat_with_unk.py                             │
│                                                                 │
│  tool_trading(symbol, strategy, portfolio_value)                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TRADING SERVICE                            │
│                    services/trading.py                          │
│                                                                 │
│  3 Strategies: DayTrader | SwingTrader | Scalper                │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   DayTrader           SwingTrader            Scalper
   2% risk/2:1         3% risk/3:1           1% risk/1.5:1
   1 day holds         3-10 day holds        Min-hours
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       STOCK SKILL                               │
│                   skills/stock_skill.py                         │
│                                                                 │
│  FUNDAMENTAL:                 TECHNICAL:                        │
│  • P/E, P/B, PEG              • RSI (14)                        │
│  • ROE, ROA                   • MACD + Signal                   │
│  • Revenue Growth             • Bollinger Bands                 │
│  • Debt/Equity                • ATR (volatility)                │
│  • Analyst Rating             • Stochastic RSI                  │
│  • 52-week Position           • Moving Averages                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Trading Strategies

| Strategy | Risk | R/R | Hold Period | Best For |
|----------|------|-----|-------------|----------|
| **DayTrader** | 2% | 2:1 | 1 day | Active traders, liquid stocks |
| **SwingTrader** | 3% | 3:1 | 3-10 days | Part-time traders, trending stocks |
| **Scalper** | 1% | 1.5:1 | Minutes-hours | High frequency, volatile stocks |

---

## Technical Indicators

| Indicator | Purpose | Signal |
|-----------|---------|--------|
| **RSI 14** | Momentum | < 30 oversold, > 70 overbought |
| **MACD** | Trend | Bullish/bearish crossover |
| **Bollinger Bands** | Volatility | Squeeze = breakout coming |
| **ATR 14** | Stop placement | Volatility-based stops |
| **Stochastic RSI** | Momentum | < 20 / > 80 extremes |
| **Williams %R** | Momentum | Overbought/oversold |
| **CCI 14** | Trend | Divergence signals |

---

## Scoring System

### Fundamental Factors
| Factor | Bullish Signal | Score |
|--------|---------------|-------|
| P/E Ratio | < 15 | +2 |
| Revenue Growth | > 20% | +2 |
| ROE | > 20% | +2 |
| Debt/Equity | < 0.5 | +1 |
| Analyst Rating | Buy | +1 |
| 52-Week Position | Near low | +1 |

### Technical Factors
| Factor | Bullish Signal | Score |
|--------|---------------|-------|
| RSI < 30 | Oversold | +2 |
| MACD Cross | Bullish | +1 |
| Price < Bollinger Lower | Oversold | +2 |
| MA Trend | Bullish | +1 |
| High Volume | Confirms move | +1 |

**Combined Score → Signal:**
- **5+**: STRONG BUY
- **2-4**: BUY  
- **-1 to 1**: HOLD
- **-4 to -2**: SELL
- **-5 or less**: STRONG SELL

---

## Usage Examples

### Chat with Unk
```
You: Unk, analyze NVDA for me
Unk: NVDA looking RIGHT! Score: 7. RSI at 45. Strong revenue growth. 
     Excellent ROE >20%. MA trend bullish. Entry $148.94, stop $140.52, 
     target $165.78. 25 shares ($4623.50). HANDLE YO BIZNASS, nephew!
```

### Direct Tool Call
```python
from services.trading import TradingService
from services.trading_types import TradingRequest

service = TradingService()

# DayTrader strategy
decision = service.analyze(TradingRequest(
    strategy="DayTrader",  # or "SwingTrader" or "Scalper"
    symbol="TSLA",
    market="stocks",
    portfolio_value=10000.0
))

print(decision.action)        # "buy" / "sell" / "watch"
print(decision.confidence)     # 0.85
print(decision.entry_price)    # 178.50
print(decision.stop_loss)      # 170.25
print(decision.take_profit)    # 195.00
print(decision.metadata["unk_explanation"])
```

---

## Files

| File | Purpose |
|------|---------|
| `skills/stock_skill.py` | Stock data + technical indicators |
| `services/trading.py` | TradingService coordinator |
| `services/trading_types.py` | TradingRequest/TradingDecision |
| `services/strategies/daytrader.py` | Day trading strategy |
| `services/strategies/swingtrader.py` | Swing trading strategy |
| `services/strategies/stockscalper.py` | Scalping strategy |
| `chat_with_unk.py` | Chat integration (tool_trading) |

---

## Dependencies

```
yfinance>=0.2.40    # Real-time stock data
pandas>=2.0.0       # Data manipulation
stockstats>=0.6.0   # Technical indicators
```

---

*Who Visions LLC - Ai with Dav3*
