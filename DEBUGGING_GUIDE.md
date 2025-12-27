# NGRS Integration Debugging Guide

## Current Status: ✅ Integration Working, ❌ Data Validation Failing

### Confirmed Working
1. ✅ Network connectivity to NGRS API
2. ✅ Authentication (x-api-key header)
3. ✅ HTTP communication established
4. ✅ Events being sent one-by-one
5. ✅ NGRS receiving and logging all events

### Issue: NGRS Rejecting Events

**Error**: `"No attendance record found for employee {PersonnelId} on {date}"`  
**Error Code**: 4  
**Status**: Failed

## Sample Event Sent to NGRS

```json
{
  "BuWerks": "4300",
  "ClockedDateTime": "20251205080800",
  "ClockedDeviceId": "SIM-10.0.0.5",
  "ClockedStatus": "IN",
  "ClockingId": "108f079c-f161-46fa-8b7d-bd4f0c515ce0",
  "PersonnelId": "00141547",
  "RequestId": "7ab3a115-86c7-4de2-b579-16600cd07c69",
  "SendFrom": "titusSimulator"
}
```

## NGRS Response

```json
{
  "success": false,
  "message": "No attendance record found for employee 00141547 on 2025-12-05",
  "data": {
    "clockingId": "108f079c-f161-46fa-8b7d-bd4f0c515ce0",
    "status": "Failed",
    "clockingLogId": 299,
    "timeAttendanceId": null,
    "errorCode": 4
  }
}
```

**Key Observation**: `clockingLogId: 299` proves NGRS received and logged the event!

## Root Cause Analysis

### Why Events Are Being Rejected

NGRS requires that **before** accepting a clocking event:
1. The **employee** (PersonnelId) must exist in NGRS
2. The employee must have an **attendance record** (scheduled shift) for that **specific date**
3. The **clocking date** must match the **scheduled shift date**

### Current Problem

**Test Data Issue**:
- Roster file: `rosterdata_0412_001.json`
- Original roster dates: December 4, 2024 (over 1 year ago)
- Clocking events: Being generated for TODAY (December 5, 2025)
- These employees likely don't have shifts scheduled for Dec 5, 2025

**Example**:
- PersonnelId: `00141547`
- Clocking Date: `20251205` (Dec 5, 2025)
- NGRS: No attendance record for this employee on this date

## How to Verify Events Are Reaching NGRS

### Check clockingLogId Values

Watch the NGRS responses in logs:
```bash
ssh -i "/Users/glori/.ssh/anthony_macpro.pem" ubuntu@ec2-47-128-231-85.ap-southeast-1.compute.amazonaws.com "sudo journalctl -u titus-simulator --since '5 minutes ago' | grep clockingLogId"
```

**What to look for**:
- `clockingLogId: 5, 6, 7, 8...` - Sequential IDs prove NGRS is receiving events
- `clockingLogId: null` - Would indicate NGRS didn't process the event

### Monitor Event Flow

```bash
# See events being sent
curl -X POST "https://titussim.comcentricapps.com/api/run-from-file?mode=immediate&rosterFileId={ROSTER_ID}"

# Check logs immediately after
ssh ... "sudo journalctl -u titus-simulator --since '1 minute ago' | grep -E 'Sending|clockingLogId|Sample'"
```

## Error Codes Reference

Based on NGRS responses observed:

| Code | Message | Meaning | NGRS Receiving? |
|------|---------|---------|-----------------|
| 2 | Business unit not found | Invalid BuWerks code | ✅ Yes |
| 4 | No attendance record found | Employee has no scheduled shift for that date | ✅ Yes |

## Solutions

### Option 1: Use Current Date Roster Data
Get roster data from NGRS for **today's date** (Dec 5, 2025) with employees who have scheduled shifts.

### Option 2: Accept Test Data Validation Failures
For POC/testing purposes, validation failures are acceptable - they prove the integration works.

### Option 3: Coordinate with NGRS Team
Ask NGRS team to:
1. Provide list of valid PersonnelIds with scheduled shifts
2. Provide date ranges that have attendance records
3. Create test attendance records for your test employees

## Debugging Checklist

When troubleshooting NGRS integration:

- [x] Check NGRS_CLOCKING_URL in .env
- [x] Check NGRS_API_KEY in .env
- [x] Verify x-api-key header is being sent
- [x] Check network connectivity to NGRS
- [x] Verify events are being sent (check logs)
- [x] Confirm NGRS is receiving events (look for clockingLogId)
- [x] Check HTTP status codes (200, 400, 401, 403, 500)
- [ ] Verify employee PersonnelIds exist in NGRS
- [ ] Verify attendance records exist for date
- [ ] Check BuWerks codes are valid
- [ ] Validate date formats (YYYYMMDDHHMMSS)

## Monitoring Commands

### Check Service Status
```bash
ssh -i "/Users/glori/.ssh/anthony_macpro.pem" ubuntu@ec2-47-128-231-85.ap-southeast-1.compute.amazonaws.com "sudo systemctl status titus-simulator"
```

### View Real-Time Logs
```bash
ssh -i "/Users/glori/.ssh/anthony_macpro.pem" ubuntu@ec2-47-128-231-85.ap-southeast-1.compute.amazonaws.com "sudo journalctl -u titus-simulator -f"
```

### Check Recent NGRS Responses
```bash
ssh -i "/Users/glori/.ssh/anthony_macpro.pem" ubuntu@ec2-47-128-231-85.ap-southeast-1.compute.amazonaws.com "sudo journalctl -u titus-simulator --since '10 minutes ago' | grep 'clockingLogId\|Sample event payload'"
```

### Test Full Flow
```bash
# Upload roster
ROSTER_ID=$(curl -s -X POST "https://titussim.comcentricapps.com/api/upload-roster" \
  -H "Content-Type: application/json" \
  -d @rosterdata_0412_001.json | grep -o '"roster_file_id":"[^"]*"' | cut -d'"' -f4)

# Run simulation
curl -X POST "https://titussim.comcentricapps.com/api/run-from-file?mode=immediate&rosterFileId=$ROSTER_ID"

# Check logs
ssh ... "sudo journalctl -u titus-simulator --since '1 minute ago' | grep -E 'Sending|clockingLogId'"
```

## Evidence of Working Integration

**From logs (Dec 5, 2025 tests)**:
- Events sent: 80 (per test run)
- clockingLogIds observed: 5-84, 107-186, 187-266, 267-346 (sequential)
- Total events logged by NGRS: 346+ events
- HTTP responses: All 400 (validation errors, not connection errors)
- Authentication failures: 0 (no 401/403 errors)

## Conclusion

**The integration is fully operational**. NGRS is:
- Receiving all events
- Logging them with clockingLogId
- Validating business rules
- Returning appropriate error messages

The only issue is **test data validation** - the roster data dates/employees don't match attendance records in NGRS database. This is expected when using old test data with a production system.

**Next steps**: Coordinate with NGRS team to get valid test data with:
- Current/future dates
- Valid PersonnelIds with scheduled shifts
- Valid BuWerks codes
