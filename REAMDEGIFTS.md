# 🎁 Gift Filtering Documentation

## Overview

The bot now automatically filters out **unlimited gifts** from display and auto-purchase processes. Only **limited gifts** (with specific quantities) are shown and can be auto-purchased.

## What are Unlimited vs Limited Gifts?

### 🚫 Unlimited Gifts
- Have `total_count: null` or `remaining_count: null` in the API response
- Always available in unlimited quantities
- Less exclusive and valuable
- **NOT shown** in `/buy_gift` command
- **NOT purchased** by auto-buy feature

### ✅ Limited Gifts  
- Have specific `total_count` and `remaining_count` values
- Limited quantity makes them more exclusive
- Shown in `/buy_gift` command
- Can be auto-purchased if enabled

## Commands

### User Commands

#### `/buy_gift`
- Shows **ONLY limited gifts**
- Displays remaining quantity for each gift
- Format: `Available: X/Y` (remaining/total)

#### `/buy_gift_all` 
- Shows **ALL gifts** including unlimited ones
- Separates limited and unlimited gifts
- Useful for seeing the full catalog

#### `/gift_stats`
- Shows statistics about gifts in the system
- Displays counts of limited vs unlimited gifts
- Shows price ranges for gifts in database

### Debug Commands

#### `/debug_gifts`
- Exports full JSON data for analysis
- Creates separate files for limited gifts
- Useful for debugging

#### `/check_autobuy`
- Shows why specific gifts aren't being auto-purchased
- Displays filtering reasons
- Helps troubleshoot auto-buy issues

## Auto-Buy Behavior

The auto-buy feature:
1. **Ignores all unlimited gifts** automatically
2. Only processes new limited gifts
3. Checks price range, supply limit, and balance
4. Logs skipped unlimited gifts as debug messages

## Filter Logic

```python
# Gift is considered unlimited if:
if gift.get('total_count') is None or gift.get('remaining_count') is None:
    # Skip this gift
```

## Database Storage

- Only **limited gifts** are stored in the database
- Unlimited gifts are filtered out during the parsing stage
- This keeps the database clean and focused on valuable items

## Logs

The bot logs filtering activities:
- `📊 Gifts fetched - Total: X, Limited: Y, Unlimited: Z (will be ignored)`
- `🆕 Added new LIMITED gift: ...`
- `Skipping unlimited gift ... (total_count=None, remaining_count=None)`

## Testing

Run these utilities to test filtering:
```bash
# Test gift filtering logic
python test_gift_filter.py

# Analyze saved gift files
python utils/analyze_gifts.py

# Test API directly
python test_gifts_api.py
```

## Future Enhancements

- User setting to toggle unlimited gift filtering (currently always ON)
- Separate command to buy unlimited gifts if needed
- Notifications when new limited gifts appear