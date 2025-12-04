# Roster Converter Guide

## Overview

The Roster Converter (`roster_converter.py`) transforms shift assignment data from external formats into the NGRS roster format required by the Titus Simulator.

## Purpose

External scheduling systems (e.g., optimization solvers, workforce management tools) often export shift assignments in different formats than what NGRS expects. This converter bridges that gap, allowing you to:

1. Import shift assignments from external tools
2. Convert them to NGRS-compatible roster format
3. Upload to Titus Simulator via Web UI or API

## Input Format

The converter expects JSON files with this structure:

```json
{
  "planningReference": "RST-20251201-D0D2F8F8",
  "demandFile": "demand_20241201_080335.json",
  "startDate": "2026-01-01T00:00:00",
  "endDate": "2026-01-31T23:59:59",
  "solverStatus": "OPTIMAL",
  "assignments": [
    {
      "employeeId": "00158375",
      "demandId": "DI-2512010803-15160815",
      "startDateTime": "2026-01-01T08:00:00",
      "endDateTime": "2026-01-01T20:00:00"
    }
  ]
}
```

### Key Fields

- **planningReference**: Unique identifier for the planning run
- **demandFile**: Source demand file name
- **startDate/endDate**: Planning period boundaries
- **solverStatus**: Optimization result (OPTIMAL, FEASIBLE, INFEASIBLE)
- **assignments**: Array of shift assignments with:
  - `employeeId`: Personnel identifier (8 digits)
  - `demandId`: Demand/site identifier
  - `startDateTime`: Shift start (ISO 8601 format)
  - `endDateTime`: Shift end (ISO 8601 format)

## Output Format

The converter produces NGRS roster format:

```json
{
  "FunctionName": "getRoster",
  "list_item": {
    "data": {
      "d": {
        "results": [
          {
            "PersonnelId": "00158375",
            "personnel_first_name": "Employee",
            "personnel_last_name": "00158375",
            "PersonnelType": "Officer",
            "PersonnelTypeDescription": "Security Officer",
            "SecSeqNum": "0",
            "PrimarySeqNum": "1",
            "demand_item_id": "DI-2512010803-15160815",
            "customer_id": "C001",
            "customer_name": "Default Customer",
            "deployment_location": "Site 15160815",
            "deployment_date": "/Date(1767254400000)/",
            "deploymentItm": "DI-2512010803-15160815-2026-01-01-D-00158375",
            "planner_group_id": "25_1",
            "plant": "PLANT001",
            "planned_start_time": "PT8H0M0S",
            "planned_end_time": "PT20H0M0S",
            "demand_type": "Regular"
          }
        ]
      }
    }
  }
}
```

### Date/Time Transformations

1. **deployment_date**: `"2026-01-01T08:00:00"` → `"/Date(1767254400000)/"`
   - Converts to milliseconds since epoch
   - Wrapped in `/Date(...)/` format

2. **planned_start_time**: `"2026-01-01T08:00:00"` → `"PT8H0M0S"`
   - Extracts time-of-day only
   - Converts to ISO 8601 duration format (PTxHxMxS)

3. **planned_end_time**: `"2026-01-01T20:00:00"` → `"PT20H0M0S"`
   - Same conversion as start time

## Usage

### Basic Conversion

Convert entire file:

```bash
python roster_converter.py input.json -o converted_roster.json
```

### Preview/Summary

View statistics without converting:

```bash
python roster_converter.py output.json --summary
```

Output:
```
📊 Roster File Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Planning Reference    : RST-20251201-D0D2F8F8
Demand File          : demand_20241201_080335.json
Planning Period      : 2026-01-01 to 2026-01-31
Solver Status        : OPTIMAL
Total Assignments    : 1,240
Unique Employees     : 60
Unique Demands       : 1
```

### Date Filtering

Convert specific date range:

```bash
python roster_converter.py input.json \
  --start-date 2026-01-05 \
  --end-date 2026-01-10 \
  -o weekly_roster.json
```

### Output to stdout

Print to console instead of file:

```bash
python roster_converter.py input.json
```

## Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `input_file` | - | Input JSON file path (required) | - |
| `--output` | `-o` | Output file path | stdout |
| `--start-date` | - | Filter start date (YYYY-MM-DD) | None |
| `--end-date` | - | Filter end date (YYYY-MM-DD) | None |
| `--summary` | - | Show summary without converting | False |

## Integration with Titus Simulator

### Method 1: Web UI Upload

1. Run the converter:
   ```bash
   python roster_converter.py output.json -o converted_roster.json
   ```

2. Open Web UI at http://localhost:8501

3. Navigate to **Upload Roster** tab

4. Drag & drop `converted_roster.json` or click Browse

5. Click **Run Simulation Now** in sidebar

6. View results in **Status Dashboard**

### Method 2: API Endpoint

1. Convert the file:
   ```bash
   python roster_converter.py output.json -o converted_roster.json
   ```

2. Upload via API:
   ```bash
   curl -X POST http://localhost:8000/upload \
     -H "Content-Type: application/json" \
     -d @converted_roster.json
   ```

3. Trigger simulation:
   ```bash
   curl -X POST http://localhost:8000/run-once
   ```

## Example Workflow

### Complete Conversion Pipeline

```bash
# Step 1: Analyze input file
python roster_converter.py output.json --summary

# Step 2: Convert full month
python roster_converter.py output.json -o converted_roster.json

# Step 3: Start services (if not running)
./start.sh        # API server on port 8000
./start_ui.sh     # Web UI on port 8501

# Step 4: Upload via Web UI
# Open http://localhost:8501 and upload converted_roster.json

# Step 5: Monitor simulation
# Check Status Dashboard for IN/OUT events
```

### Weekly Batch Processing

```bash
# Convert week 1 (Jan 1-7)
python roster_converter.py output.json \
  --start-date 2026-01-01 \
  --end-date 2026-01-07 \
  -o week1_roster.json

# Convert week 2 (Jan 8-14)
python roster_converter.py output.json \
  --start-date 2026-01-08 \
  --end-date 2026-01-14 \
  -o week2_roster.json

# Upload each week separately via Web UI
```

## Data Validation

The converter performs automatic validation:

### ✅ Valid Input
- ISO 8601 datetime format: `"2026-01-01T08:00:00"`
- 8-digit employee IDs: `"00158375"`
- Non-empty demand IDs
- Start time before end time

### ❌ Invalid Input
- Malformed dates: `"2026-13-45T25:99:99"`
- Missing required fields
- End time before start time
- Invalid JSON structure

## Output Verification

After conversion, verify the output:

```bash
# Check file size (should be larger due to NGRS envelope)
ls -lh converted_roster.json

# Preview first 100 lines
head -100 converted_roster.json

# Count assignments
grep -c "PersonnelId" converted_roster.json

# Validate JSON structure
python -m json.tool converted_roster.json > /dev/null && echo "✅ Valid JSON"
```

## Troubleshooting

### Issue: "File not found"
**Solution**: Verify input file path exists
```bash
ls -l output.json
```

### Issue: "Invalid JSON"
**Solution**: Validate input format
```bash
python -m json.tool output.json > /dev/null
```

### Issue: No assignments after filtering
**Solution**: Check date range overlaps with data
```bash
python roster_converter.py output.json --summary
# Verify planning period matches your filter dates
```

### Issue: Conversion too slow
**Solution**: Use date filtering for large files
```bash
# Instead of converting 10,000+ assignments
# Split by month or week
python roster_converter.py huge_file.json \
  --start-date 2026-01-01 \
  --end-date 2026-01-31 \
  -o january_only.json
```

## Advanced Usage

### Scripting Integration

```python
from roster_converter import RosterConverter

# Programmatic conversion
converter = RosterConverter()
converted_data = converter.convert_file(
    "input.json",
    start_date="2026-01-01",
    end_date="2026-01-31"
)

# Access metadata
print(f"Converted {len(converted_data['list_item']['data']['d']['results'])} assignments")
```

### Batch Processing Script

```bash
#!/bin/bash
# convert_all.sh - Convert multiple roster files

for file in rosters/*.json; do
    output="converted/$(basename "$file" .json)_converted.json"
    python roster_converter.py "$file" -o "$output"
    echo "✅ Converted: $file → $output"
done
```

## Field Mappings

| Input Field | Output Field | Transformation |
|-------------|--------------|----------------|
| `employeeId` | `PersonnelId` | Direct copy |
| `employeeId` | `personnel_first_name` | "Employee" |
| `employeeId` | `personnel_last_name` | employeeId value |
| `demandId` | `demand_item_id` | Direct copy |
| `demandId` | `deployment_location` | "Site {demandId}" |
| `startDateTime` (date) | `deployment_date` | To `/Date(ms)/` |
| `startDateTime` (time) | `planned_start_time` | To `PTxHxMxS` |
| `endDateTime` (time) | `planned_end_time` | To `PTxHxMxS` |
| - | `customer_id` | "C001" (default) |
| - | `customer_name` | "Default Customer" |
| - | `PersonnelType` | "Officer" |
| - | `demand_type` | "Regular" |

## Performance Notes

- **Small files** (< 100 assignments): < 1 second
- **Medium files** (100-1,000 assignments): 1-3 seconds
- **Large files** (1,000-10,000 assignments): 3-10 seconds
- **Very large files** (> 10,000 assignments): Consider date filtering

## Next Steps

After successful conversion:

1. **Test Upload**: Upload converted file via Web UI
2. **Run Simulation**: Execute one cycle to verify
3. **Check Results**: View Status Dashboard for IN/OUT events
4. **Export Data**: Download CSV from Statistics tab
5. **Verify in NGRS**: Check events posted to NGRS API

## Related Documentation

- [USAGE.md](USAGE.md) - Titus Simulator operations
- [UI_GUIDE.md](UI_GUIDE.md) - Web interface walkthrough
- [QUICKSTART.md](QUICKSTART.md) - Fast setup guide
- [README.md](../README.md) - Complete system overview

## Support

For issues or questions:
1. Check input file format matches expected structure
2. Run with `--summary` flag to diagnose data issues
3. Verify date ranges are valid
4. Test with small subset first
5. Review error messages for specific field issues
