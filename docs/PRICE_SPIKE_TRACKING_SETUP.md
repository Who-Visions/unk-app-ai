# Price Spike Tracking - Quick Setup Guide

## ✅ What's Been Created

A complete price tracking and spike detection system has been implemented:

### 📁 Files Created

1. **`gemini_agent/price_tracker.py`** - Core tracking engine
   - `PriceTracker` class for storing and analyzing prices
   - `PriceSnapshot` dataclass for price records
   - `PriceSpike` dataclass for detected spikes
   - Spike detection with severity classification
   - Trend analysis capabilities

2. **`scripts/import_pricing_csv.py`** - CSV import tool
   - Imports pricing data from GCP contract CSV files
   - Supports dry-run mode for testing

3. **`scripts/check_price_spikes.py`** - Spike detection CLI
   - Checks for price spikes above configurable thresholds
   - Generates formatted reports
   - Shows price trends
   - Exits with error code for critical spikes (for alerting)

4. **API Endpoints** (added to `deploy.py`)
   - `GET /pricing/spikes` - Get detected price spikes
   - `GET /pricing/history` - Get price history
   - `GET /pricing/trends` - Get price trend analysis
   - `POST /pricing/record` - Manually record prices

5. **Documentation**
   - `docs/PRICING_BREAKDOWN.md` - Complete pricing breakdown from CSV
   - `docs/PRICE_TRACKING.md` - Full system documentation
   - `docs/PRICE_SPIKE_TRACKING_SETUP.md` - This file

---

## 🚀 Quick Start

### Step 1: Import Your Pricing Data

```bash
# Windows
python scripts\import_pricing_csv.py "c:\Users\super\Downloads\Pricing for Who Visions LLC (1).csv"

# Linux/Mac
python scripts/import_pricing_csv.py "/path/to/pricing.csv"
```

This will:
- Parse the CSV file
- Extract all pricing information
- Store it in `data/price_history.json`

### Step 2: Check for Price Spikes

```bash
# Basic check (10% threshold)
python scripts/check_price_spikes.py

# Custom threshold (25%)
python scripts/check_price_spikes.py --threshold 25

# Check specific service
python scripts/check_price_spikes.py --service GCP

# Show trends
python scripts/check_price_spikes.py --trend
```

### Step 3: Set Up Automated Monitoring

**Windows Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 9 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `scripts\check_price_spikes.py --threshold 10`
7. Start in: `C:\Users\super\Watchtower\unk-app-ai`

**Linux/Mac Cron:**
```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 9 AM)
0 9 * * * cd /path/to/unk-app-ai && python scripts/check_price_spikes.py --threshold 10 >> logs/price_checks.log 2>&1
```

---

## 📊 How It Works

### Price Tracking Flow

```
CSV Import → Price History Storage → Spike Detection → Alerts/Reports
     ↓              ↓                      ↓
  Parse CSV    data/price_history.json   Compare prices
  Extract      Store timestamps          Calculate % change
  SKUs/Prices  Track changes             Flag spikes
```

### Spike Detection Logic

1. **Compare Latest vs Previous**: For each SKU, compares the most recent price with the previous price
2. **Calculate Increase**: Computes percentage and absolute increase
3. **Apply Threshold**: Flags increases above the threshold (default: 10%)
4. **Classify Severity**:
   - 🔴 **Critical**: ≥50% increase
   - 🟠 **High**: ≥25% increase
   - 🟡 **Medium**: ≥15% increase
   - 🟢 **Low**: ≥10% increase

### Example Output

```
🚨 PRICE SPIKE ALERT - 1 spike(s) detected
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

## 🔧 Configuration

### Environment Variables

- `PRICE_HISTORY_PATH`: Path to price history JSON file (default: `data/price_history.json`)

### Thresholds

- **Default**: 10% - Good for general monitoring
- **Alerting**: 25% - For important cost increases
- **Critical**: 50% - For major price changes

---

## 📈 API Usage Examples

### Get Price Spikes

```bash
curl "http://localhost:8080/pricing/spikes?threshold=10&days=30"
```

### Get Price History

```bash
curl "http://localhost:8080/pricing/history?service=GCP&price_type=input"
```

### Get Price Trends

```bash
curl "http://localhost:8080/pricing/trends?days=30"
```

---

## 🎯 Next Steps

1. **Import Current Pricing**: Run the CSV import script with your pricing file
2. **Set Up Monitoring**: Schedule daily/weekly price checks
3. **Integrate Alerts**: Connect spike detection to your alerting system
4. **Update Pricing**: Re-import CSV monthly or when contract changes
5. **Review Trends**: Use `--trend` flag to understand pricing patterns

---

## 💡 Tips

- **Start with Higher Thresholds**: Use 25%+ initially to avoid noise
- **Focus on High-Usage Services**: Monitor Vertex AI pricing closely
- **Track Trends**: Use `--trend` to see long-term patterns
- **Archive Old Data**: Periodically archive `data/price_history.json` for performance
- **Combine with Usage Data**: Multiply price spikes by usage to see cost impact

---

## 🐛 Troubleshooting

### Import Fails
- Check CSV file path is correct
- Verify CSV format matches expected structure
- Ensure `data/` directory exists and is writable

### No Spikes Detected
- Lower threshold: `--threshold 5`
- Check history exists: `python scripts/check_price_spikes.py --trend`
- Verify CSV import completed successfully

### API Errors
- Check `data/` directory exists
- Verify `PRICE_HISTORY_PATH` environment variable
- Review server logs for details

---

## 📚 Related Documentation

- **Full System Docs**: `docs/PRICE_TRACKING.md`
- **Pricing Breakdown**: `docs/PRICING_BREAKDOWN.md`
- **API Reference**: See `docs/PRICE_TRACKING.md` API section

---

*Who Visions LLC - AI with Dav3*

