# Price Tracking & Spike Detection System

**Who Visions LLC - Unk Agent System**

---

## Overview

The Price Tracking System monitors GCP service pricing over time and automatically detects price spikes. This helps identify unexpected cost increases and track pricing trends.

## Features

- ✅ **Historical Price Tracking**: Stores all price snapshots with timestamps
- ✅ **Spike Detection**: Automatically detects price increases above configurable thresholds
- ✅ **Trend Analysis**: Analyzes price trends over time periods
- ✅ **CSV Import**: Import pricing data from GCP contract CSV exports
- ✅ **API Endpoints**: RESTful API for accessing price data
- ✅ **Severity Classification**: Categorizes spikes as low, medium, high, or critical

---

## Quick Start

### 1. Import Initial Pricing Data

```bash
python scripts/import_pricing_csv.py "c:\Users\super\Downloads\Pricing for Who Visions LLC (1).csv"
```

### 2. Check for Price Spikes

```bash
# Check for spikes above 10% increase
python scripts/check_price_spikes.py

# Check with custom threshold (25%)
python scripts/check_price_spikes.py --threshold 25

# Check specific service
python scripts/check_price_spikes.py --service GCP

# Show price trends
python scripts/check_price_spikes.py --trend
```

### 3. View Price History via API

```bash
# Get all price spikes
curl http://localhost:8080/pricing/spikes?threshold=10&days=30

# Get price history for Vertex AI
curl http://localhost:8080/pricing/history?service=GCP&price_type=input

# Get price trends
curl http://localhost:8080/pricing/trends?days=30
```

---

## Architecture

### Components

1. **PriceTracker** (`gemini_agent/price_tracker.py`)
   - Core tracking engine
   - Stores price snapshots in JSON format
   - Detects spikes and analyzes trends

2. **CLI Scripts**
   - `scripts/import_pricing_csv.py`: Import CSV pricing data
   - `scripts/check_price_spikes.py`: Check for spikes and generate reports

3. **API Endpoints** (`deploy.py`)
   - `/pricing/spikes`: Get detected price spikes
   - `/pricing/history`: Get price history
   - `/pricing/trends`: Get price trend analysis
   - `/pricing/record`: Manually record a price snapshot

### Data Storage

Price history is stored in `data/price_history.json` by default. This can be configured via the `PRICE_HISTORY_PATH` environment variable.

**Storage Format:**
```json
[
  {
    "timestamp": "2025-01-XXT12:00:00",
    "service": "GCP",
    "sku_id": "FDAB-647C-5A22",
    "sku_description": "Gemini 2.5 Flash GA Text Input - Predictions",
    "price_type": "input",
    "price_per_unit": 0.30,
    "unit": "count",
    "tier_start": null,
    "metadata": {
      "service_description": "Vertex AI",
      "source": "csv_import"
    }
  }
]
```

---

## Spike Detection

### How It Works

1. **Price Comparison**: Compares latest price with previous price for each SKU
2. **Threshold Check**: Flags increases above the threshold percentage
3. **Severity Classification**:
   - **Critical**: ≥50% increase
   - **High**: ≥25% increase
   - **Medium**: ≥15% increase
   - **Low**: ≥10% increase (configurable threshold)

### Example Output

```
🚨 PRICE SPIKE ALERT - 2 spike(s) detected
================================================================================

1. 🔴 CRITICAL SPIKE
   Service: GCP
   SKU: FDAB-647C-5A22
   Description: Gemini 2.5 Flash GA Text Input - Predictions
   Price Type: input
   Previous Price: $0.100000
   Current Price:  $0.300000
   Increase: +$0.200000 (200.00%)
   Detected: 2025-01-XXT12:00:00
   Days since last check: 30
--------------------------------------------------------------------------------
```

---

## API Reference

### GET `/pricing/spikes`

Get detected price spikes.

**Query Parameters:**
- `threshold` (float, default: 10.0): Minimum percentage increase
- `service` (string, optional): Filter by service name
- `days` (int, default: 30): Days to look back

**Response:**
```json
{
  "success": true,
  "count": 2,
  "threshold": 10.0,
  "lookback_days": 30,
  "spikes": [
    {
      "timestamp": "2025-01-XXT12:00:00",
      "service": "GCP",
      "sku_id": "FDAB-647C-5A22",
      "sku_description": "Gemini 2.5 Flash GA Text Input",
      "price_type": "input",
      "previous_price": 0.1,
      "current_price": 0.3,
      "percentage_increase": 200.0,
      "absolute_increase": 0.2,
      "severity": "critical",
      "days_since_last_check": 30
    }
  ]
}
```

### GET `/pricing/history`

Get price history for tracked SKUs.

**Query Parameters:**
- `service` (string, optional): Filter by service
- `sku_id` (string, optional): Filter by SKU ID
- `price_type` (string, optional): Filter by type (input, output, storage, etc.)
- `days` (int, optional): Limit to last N days

### GET `/pricing/trends`

Get price trend analysis.

**Query Parameters:**
- `service` (string, optional): Filter by service
- `sku_id` (string, optional): Filter by SKU ID
- `price_type` (string, optional): Filter by type
- `days` (int, default: 30): Analysis period

**Response:**
```json
{
  "success": true,
  "count": 1,
  "trends": [
    {
      "service": "GCP",
      "sku_id": "FDAB-647C-5A22",
      "price_type": "input",
      "data_points": 5,
      "first_price": 0.1,
      "last_price": 0.3,
      "average_price": 0.2,
      "max_price": 0.3,
      "min_price": 0.1,
      "percentage_change": 200.0,
      "trend": "increasing",
      "timeline": [...]
    }
  ]
}
```

### POST `/pricing/record`

Manually record a price snapshot.

**Body:**
```json
{
  "service": "GCP",
  "sku_id": "FDAB-647C-5A22",
  "sku_description": "Gemini 2.5 Flash Input",
  "price_type": "input",
  "price_per_unit": 0.30,
  "unit": "count",
  "tier_start": null
}
```

---

## Automation

### Scheduled Price Checks

Create a cron job or scheduled task to check for spikes:

**Linux/Mac (crontab):**
```bash
# Check for spikes daily at 9 AM
0 9 * * * cd /path/to/unk-app-ai && python scripts/check_price_spikes.py --threshold 10 >> logs/price_checks.log 2>&1
```

**Windows (Task Scheduler):**
```powershell
# Run daily at 9 AM
python scripts\check_price_spikes.py --threshold 10
```

### Alerting

The script exits with code 1 if critical spikes are detected, making it easy to integrate with alerting systems:

```bash
#!/bin/bash
python scripts/check_price_spikes.py --threshold 10
if [ $? -eq 1 ]; then
    # Send alert (email, Slack, etc.)
    echo "CRITICAL price spike detected!" | mail -s "Price Alert" admin@example.com
fi
```

---

## Integration with Cost Estimation

The price tracker can be integrated with the cost estimation system to use real-time pricing:

```python
from gemini_agent.price_tracker import get_tracker
from gemini_agent.models_spec import estimate_cost

def get_current_cost(mode: str, input_tokens: int, output_tokens: int) -> float:
    """Get cost using latest tracked prices."""
    tracker = get_tracker()
    spec = get_model(mode)
    
    # Try to get latest tracked price, fallback to spec
    input_price = spec["pricing"]["input_per_1m"]
    output_price = spec["pricing"]["output_per_1m"]
    
    # Check for tracked prices (example for Gemini 2.5 Flash)
    if mode == "default":
        latest = tracker.get_latest_price("GCP", "FDAB-647C-5A22", "input")
        if latest:
            input_price = latest.price_per_unit
    
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price
    return round(input_cost + output_cost, 6)
```

---

## Best Practices

1. **Regular Imports**: Import new pricing CSVs monthly or when contract changes
2. **Monitor Critical Services**: Focus spike detection on high-usage services
3. **Set Appropriate Thresholds**: Use 10% for general monitoring, 25%+ for alerts
4. **Review Trends**: Use `--trend` flag to understand long-term pricing patterns
5. **Archive Old Data**: Periodically archive old price history to maintain performance

---

## Troubleshooting

### No spikes detected

- Check that price history exists: `python scripts/check_price_spikes.py --trend`
- Verify CSV import completed: Check `data/price_history.json`
- Lower threshold: Try `--threshold 5`

### Import errors

- Verify CSV format matches expected structure
- Check file encoding (should be UTF-8)
- Ensure SKU IDs and prices are valid

### API errors

- Verify `data/` directory exists and is writable
- Check `PRICE_HISTORY_PATH` environment variable
- Review server logs for detailed errors

---

## Future Enhancements

- [ ] Firestore/BigQuery backend for production scale
- [ ] Email/Slack notifications for spikes
- [ ] Price prediction using ML models
- [ ] Cost impact analysis (spike × usage = cost increase)
- [ ] Dashboard UI for price visualization
- [ ] Automated CSV import from GCP billing exports

---

*Who Visions LLC - AI with Dav3*

