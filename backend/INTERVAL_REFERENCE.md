# Retraining Interval Quick Reference

## How to Change the Retraining Interval

**Location:** `backend/app/config/.env`
**Setting:** `RETRAINING_INTERVAL_HOURS`

### Steps:
1. Open `backend/app/config/.env`
2. Change `RETRAINING_INTERVAL_HOURS` value
3. Restart Flask server (`python run.py`)

---

## Common Intervals

Copy the value you want into your `.env` file:

### Testing / Development
```bash
# 30 seconds
RETRAINING_INTERVAL_HOURS=0.0083

# 1 minute
RETRAINING_INTERVAL_HOURS=0.0167

# 2 minutes (CURRENT)
RETRAINING_INTERVAL_HOURS=0.0333

# 5 minutes
RETRAINING_INTERVAL_HOURS=0.0833

# 10 minutes
RETRAINING_INTERVAL_HOURS=0.1667

# 30 minutes
RETRAINING_INTERVAL_HOURS=0.5
```

### Production
```bash
# 1 hour
RETRAINING_INTERVAL_HOURS=1

# 2 hours
RETRAINING_INTERVAL_HOURS=2

# 6 hours
RETRAINING_INTERVAL_HOURS=6

# 12 hours
RETRAINING_INTERVAL_HOURS=12

# Daily (24 hours)
RETRAINING_INTERVAL_HOURS=24

# Weekly (168 hours)
RETRAINING_INTERVAL_HOURS=168
```

---

## Formula for Custom Intervals

If you want a custom interval:

**Minutes to Hours:**
```
Hours = Minutes / 60
```

**Seconds to Hours:**
```
Hours = Seconds / 3600
```

### Examples:
- 45 seconds: `45 / 3600 = 0.0125`
- 15 minutes: `15 / 60 = 0.25`
- 90 minutes: `90 / 60 = 1.5`

---

## Current Configuration

Your current setup:
- **Interval:** 0.0333 hours = **2 minutes**
- **Enabled:** true
- **Mode:** Integrated (runs with Flask server)

---

## Important Notes

1. **Restart Required:** After changing `.env`, you MUST restart Flask server
2. **First Run:** Scheduler starts on first HTTP request after server starts
3. **Training Duration:** With 355K records, each training takes several minutes
4. **Set Realistic Intervals:** Don't set intervals shorter than training duration
5. **Production Default:** 24 hours is recommended for production

---

## Warning ⚠️

If you set the interval **too short** (e.g., 30 seconds) and training takes **longer** than the interval, multiple training jobs may overlap and cause issues.

**Rule of thumb:** Set interval to at least **2x the training duration**

Example:
- Training takes 5 minutes
- Set interval to at least 10 minutes (0.1667 hours)
