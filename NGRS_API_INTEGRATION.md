# NGRS API Integration - Successfully Configured

## ✅ Integration Status: **WORKING**

The Titus Simulator is successfully integrated with the production NGRS API. All 80 clocking events were sent and received by NGRS.

## Production Configuration

### NGRS API Endpoint
- **URL**: `https://ngrs-api.comcentricapps.com/api/external/clocking/receive`
- **Method**: POST
- **Content-Type**: application/json
- **Authentication**: `x-api-key` header
- **API Key**: `3a0e3418-34a1-4c2a-bdfa-fed82dfddbce`

### Titus Simulator Endpoints
- **API**: `https://titussim.comcentricapps.com/api`
- **Web UI**: `https://titussim.comcentricapps.com`
- **Health Check**: `https://titussim.comcentricapps.com/api/health`

## Test Results (December 5, 2025)

### Test 1: Initial Test with Old Data
**Upload Roster** (`rosterdata_0412_001.json` - Dec 4, 2024 dates):
```bash
curl -X POST "https://titussim.comcentricapps.com/api/upload-roster" \
  -H "Content-Type: application/json" \
  -d @rosterdata_0412_001.json
```

**Result**: ✅ Success
- RosterFileId: `5372c50c-9707-48be-92ad-6c9d2256ee3b`
- 40 assignments uploaded
- 40 RequestIds generated

**Run Simulation (Immediate Mode)**:
```bash
curl -X POST "https://titussim.comcentricapps.com/api/run-from-file?mode=immediate&rosterFileId=5372c50c-9707-48be-92ad-6c9d2256ee3b"
```

**Result**: ✅ Integration Working (with validation errors)
- 80 events generated (40 IN + 40 OUT)
- All 80 events sent to NGRS API
- NGRS received all events (clockingLogIds: 5-84)
- Authentication successful (x-api-key working)
- All events rejected: "Business unit not found: SLS" (errorCode: 2)

### Test 2: Second Test (Same Data)
**Result**: ✅ Integration Working (different validation error)
- RosterFileId: `bc807237-8490-431a-b279-3fed14a79789`
- 80 events sent to NGRS (clockingLogIds: 107-186)
- All events rejected: "No attendance record found for employee on 2025-12-05" (errorCode: 4)
- **Note**: Error changed from business unit validation to attendance record validation

### NGRS Response
All events were received by NGRS but rejected due to **data validation**:

```json
{
  "success": false,
  "message": "Business unit not found: SLS",
  "data": {
    "clockingId": "303d1088-7a27-45bc-9379-75d9ee665893",
    "status": "Failed",
    "clockingLogId": 5,
    "timeAttendanceId": null,
    "errorCode": 2
  }
}
```

**Analysis**: 
- ✅ API connectivity: **Working**
- ✅ Authentication: **Working** 
- ✅ Event sending: **Working**
- ✅ NGRS receiving: **Working**
- ❌ Data validation: **Failed** (Business unit "SLS" not found in NGRS database)

## Data Issue Resolution

The roster file `rosterdata_0412_001.json` contains business unit code "SLS" which doesn't exist in the NGRS database.

### To Fix:
1. **Option A**: Update roster data with valid business unit codes
2. **Option B**: Add "SLS" business unit to NGRS database
3. **Option C**: Use a different roster file with valid business units

### Valid Business Units
Check with NGRS team for list of valid business unit codes in the system.

## Event Format

Clocking events sent to NGRS follow this format:

```json
{
  "BuWerks": "SLS",
  "ClockedDateTime": "20241204093022",
  "ClockedDeviceId": "SIM-10.0.0.5",
  "ClockedStatus": "IN",
  "ClockingId": "303d1088-7a27-45bc-9379-75d9ee665893",
  "PersonnelId": "00141547",
  "RequestId": "689e27df-34a8-4418-993f-99568f862c23",
  "SendFrom": "titusSimulator"
}
```

### Field Mapping:
- `BuWerks`: Business unit code from roster `planner_group_id` or `plant`
- `ClockedDateTime`: Format `YYYYMMDDHHmmss`
- `ClockedDeviceId`: Simulated device ID `SIM-10.0.0.5`
- `ClockedStatus`: `IN` or `OUT`
- `ClockingId`: Unique UUID for each event
- `PersonnelId`: From roster `PersonnelId`
- `RequestId`: UUID from upload-roster response
- `SendFrom`: Fixed value `titusSimulator`

## Error Codes

Based on NGRS responses:

| Code | Description |
|------|-------------|
| 2 | Business unit not found |
| ... | (Other codes to be documented) |

## Monitoring

### Check Sent Events
```bash
curl "https://titussim.comcentricapps.com/api/stats"
```

### View Logs
```bash
ssh ubuntu@ec2-47-128-231-85.ap-southeast-1.compute.amazonaws.com
sudo journalctl -u titus-simulator -f
```

### Filter for NGRS Responses
```bash
sudo journalctl -u titus-simulator --since '10 minutes ago' | grep -i 'ngrs\|clocking'
```

## Next Steps

1. ✅ **API Integration**: Complete
2. ✅ **Authentication**: Complete
3. ✅ **Event Sending**: Complete
4. ❌ **Data Validation**: Needs valid business units
5. ⏳ **Production Testing**: Awaiting valid roster data

## Troubleshooting

### Connection Issues
If events fail to send:
1. Check NGRS API is accessible
2. Verify API key in `.env` file
3. Check network/firewall settings

### Authentication Errors
If receiving 401/403 errors:
1. Verify API key: `3a0e3418-34a1-4c2a-bdfa-fed82dfddbce`
2. Ensure `x-api-key` header is sent (not Bearer token)
3. Check API key hasn't expired

### Data Validation Errors
Current issue: Business unit codes
- Review roster data business units
- Coordinate with NGRS team for valid codes
- Test with known valid business units

## Contact

- **NGRS API**: https://ngrs-api.comcentricapps.com
- **Titus Simulator**: https://titussim.comcentricapps.com
- **API Documentation**: See `/postman/README.md`
