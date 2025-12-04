# Roster Converter - Quick Start

Convert external shift assignment files to NGRS roster format in 3 steps.

## 📋 Quick Commands

```bash
# 1. View summary (check what's in the file)
python roster_converter.py output.json --summary

# 2. Convert the file
python roster_converter.py output.json -o converted_roster.json

# 3. Upload via Web UI
# Open http://localhost:8501
# Go to "Upload Roster" tab
# Drag & drop converted_roster.json
```

## 🎯 Common Use Cases

### Full Month Conversion
```bash
python roster_converter.py output.json -o converted_roster.json
```

### Single Week
```bash
python roster_converter.py output.json \
  --start-date 2026-01-01 \
  --end-date 2026-01-07 \
  -o week1_roster.json
```

### Using Makefile
```bash
# Show summary
make summary FILE=output.json

# Convert
make convert FILE=output.json OUTPUT=converted.json
```

## 📊 Example Output

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
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Converted 1240 assignments
📄 Output saved to: converted_roster.json
```

## 🔄 Format Transformation

**Input (External Format):**
```json
{
  "employeeId": "00158375",
  "demandId": "DI-2512010803-15160815",
  "startDateTime": "2026-01-01T08:00:00",
  "endDateTime": "2026-01-01T20:00:00"
}
```

**Output (NGRS Format):**
```json
{
  "PersonnelId": "00158375",
  "demand_item_id": "DI-2512010803-15160815",
  "deployment_date": "/Date(1767254400000)/",
  "planned_start_time": "PT8H0M0S",
  "planned_end_time": "PT20H0M0S"
}
```

## ✅ Next Steps After Conversion

1. **Upload to Web UI**
   - Open http://localhost:8501
   - Upload Roster tab → drag & drop converted file
   - Click "Run Simulation Now"

2. **Check Results**
   - Status Dashboard → see IN/OUT times
   - Statistics → view completion rates
   - Export to CSV for analysis

3. **Verify Events**
   - Check NGRS API received clock events
   - Monitor logs for any errors

## 📖 Full Documentation

For complete details, see [docs/CONVERTER_GUIDE.md](docs/CONVERTER_GUIDE.md)

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "File not found" | Check path: `ls -l output.json` |
| "Invalid JSON" | Validate: `python -m json.tool output.json` |
| No assignments after filtering | Check date range with `--summary` |
| Conversion slow | Use `--start-date` and `--end-date` filters |

## 🔗 Related Commands

```bash
# Start API server
make run

# Start Web UI
make ui

# Health check
curl http://localhost:8000/health

# View stats
make stats
```
