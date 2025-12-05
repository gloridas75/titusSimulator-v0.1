# Postman Collection Guide

## Overview
This folder contains Postman collections and environments for testing the Titus Simulator API with RosterFileId UUID-based workflow.

## Files

1. **Titus_Simulator_API.postman_collection.json** - Complete API collection with RosterFileId workflow
2. **Titus_Simulator.postman_environment.json** - Local development environment
3. **Titus_Simulator_Production.postman_environment.json** - Production environment (updated)

## Import Instructions

### Step 1: Import Collection
1. Open Postman
2. Click **Import** button (top left)
3. Select **Titus_Simulator_API.postman_collection.json**
4. Click **Import**

### Step 2: Import Environment
1. Click **Import** button again
2. Select both environment files:
   - **Titus_Simulator.postman_environment.json** (Local)
   - **Titus_Simulator_Production.postman_environment.json** (Production)
3. Click **Import**

### Step 3: Activate Environment
1. Click the environment dropdown (top right)
2. Select either:
   - **Titus Simulator Environment** (for local testing on localhost:8087)
   - **Titus Simulator - Production** (for production on titussim.comcentricapps.com)

## Environment Configuration

### Local Environment
- **base_url**: `http://localhost:8087`
- **ngrs_clocking_url**: `http://localhost:8080/api/integration/titus/clocking`
- **ngrs_api_key**: (empty for local testing)
- **roster_file_id**: Auto-populated by test scripts

### Production Environment
- **base_url**: `https://titussim.comcentricapps.com/api`
- **web_ui_url**: `https://titussim.comcentricapps.com`
- **api_port**: `8087`
- **ui_port**: `8088`
- **server_ip**: `47.128.231.85`
- **domain**: `titussim.comcentricapps.com`
- **ngrs_clocking_url**: `https://ngrs-api.comcentricapps.com/api/external/clocking/receive`
- **ngrs_api_key**: `3a0e3418-34a1-4c2a-bdfa-fed82dfddbce` (sent as `x-api-key` header)
- **roster_file_id**: Auto-populated by test scripts

## RosterFileId Workflow (NEW)

The simulator now uses UUID-based roster tracking. Each uploaded roster receives a unique `roster_file_id` that must be used for processing.

### Typical Workflow:
1. **Upload Roster** → Get `roster_file_id`
2. **Run Simulation** → Use `roster_file_id` parameter
3. **Check Status** → Query by `roster_file_id`

**Auto-Capture Feature**: The Upload Roster request includes a test script that automatically saves the `roster_file_id` to the environment, so you don't need to copy/paste it manually.

## Available Endpoints

### 1. Health Check
- **Method**: GET
- **URL**: `{{base_url}}/health`
- **Description**: Verify API is running
- **Expected Response**: 
  ```json
  {
    "status": "ok",
    "service": "titus-simulator",
    "version": "0.1.0"
  }
  ```

### 2. Upload Roster Data
- **Method**: POST
- **URL**: `{{base_url}}/upload-roster`
- **Body**: JSON roster data in NGRS format (with `__metadata`)
- **Description**: Upload roster and receive unique RosterFileId
- **Expected Response**:
  ```json
  {
    "success": true,
    "roster_file_id": "e8d63206-3ab3-41a5-961d-1e406c1c7de9",
    "results": [
      {
        "PersonnelId": "00037056",
        "RequestId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
      }
    ]
  }
  ```
- **Note**: The `roster_file_id` is automatically stored in environment variable

### 3. Get Roster by RosterFileId (NEW)
- **Method**: GET
- **URL**: `{{base_url}}/roster?rosterFileId={{roster_file_id}}`
- **Description**: Retrieve roster data and status by UUID
- **Expected Response**:
  ```json
  {
    "status": "ok",
    "roster_file_id": "e8d63206-3ab3-41a5-961d-1e406c1c7de9",
    "uploaded_at": "2025-12-05T03:25:10.908609",
    "assignments_count": 40,
    "roster_status": "completed",
    "roster": [...]
  }
  ```

### 4. Run Simulation - Immediate Mode (UPDATED)
- **Method**: POST
- **URL**: `{{base_url}}/run-from-file?mode=immediate&rosterFileId={{roster_file_id}}`
- **Query Params**:
  - `mode`: `immediate` (generates all events at once)
  - `rosterFileId`: UUID from upload response (required)
- **Description**: Batch process - generate all events, post to NGRS, cleanup database
- **Expected Response**:
  ```json
  {
    "status": "completed",
    "roster_file_id": "e8d63206-3ab3-41a5-961d-1e406c1c7de9",
    "result": {
      "mode": "immediate",
      "assignments_found": 40,
      "assignments_parsed": 40,
      "events_generated": 80,
      "events_posted": 80,
      "records_cleaned": 80,
      "ngrs_available": true
    }
  }
  ```

### 5. Run Simulation - Realtime Mode (NEW)
- **Method**: POST
- **URL**: `{{base_url}}/run-from-file?mode=realtime&rosterFileId={{roster_file_id}}`
- **Query Params**:
  - `mode`: `realtime` (time-based event generation)
  - `rosterFileId`: UUID from upload response (required)
- **Description**: Scheduled execution - generate events only for current 15-min window
- **Expected Response**:
  ```json
  {
    "status": "completed",
    "roster_file_id": "e8d63206-3ab3-41a5-961d-1e406c1c7de9",
    "result": {
      "mode": "realtime",
      "assignments_found": 40,
      "assignments_parsed": 40,
      "events_generated": 4,
      "events_posted": 4
    }
  }
  ```

### 6. Run Simulation by Date
- **Method**: POST
- **URL**: `{{base_url}}/run-once?date=2026-01-15`
- **Query Params**:
  - `date`: YYYY-MM-DD format
- **Description**: Fetch roster from NGRS and simulate
- **Note**: Requires NGRS API to be running

### 7. Get Statistics
- **Method**: GET
- **URL**: `{{base_url}}/stats`
- **Description**: View simulation statistics
- **Expected Response**:
  ```json
  {
    "status": "ok",
    "stats": {
      "total_assignments": 42,
      "in_events_sent": 42,
      "out_events_sent": 42
    }
  }
  ```

### 8. Get Roster Upload Logs
- **Method**: GET
- **URL**: `{{base_url}}/roster-logs`
- **Description**: View roster upload history
- **Expected Response**:
  ```json
  {
    "status": "ok",
    "logs": [...]
  }
  ```

### 9. NGRS - Receive Clocking Event (Mock)
- **Method**: POST
- **URL**: `{{ngrs_clocking_url}}`
- **Body**: Single clocking event JSON
- **Description**: Mock NGRS endpoint for testing event format
- **Note**: This is a reference request - actual NGRS endpoint must be implemented separately

## Simulation Modes

### Immediate Mode
- **Use Case**: Batch processing, testing, backfill
- **Behavior**: Generate all events immediately with random time variations
- **Timing**: -5 to +10 min for IN, -10 to +15 min for OUT
- **Cleanup**: Deletes all events after posting
- **When to use**: One-time roster processing, testing, historical data

### Realtime Mode
- **Use Case**: Production scheduled execution
- **Behavior**: Generate events only for current time window
- **Window**: 15 minutes before/after shift start/end time
- **Retention**: Keeps last 2 days of events
- **Overdue**: Sends overdue events immediately
- **When to use**: Automated scheduled processing, production operations

## Roster Status Values

- `pending`: Roster uploaded, not yet processed
- `processing`: Currently being processed
- `completed`: Successfully processed
- `failed`: Processing failed (check logs)

## Environment Variables

| Variable | Production Value | Description |
|----------|-----------------|-------------|
| `base_url` | `https://titussim.comcentricapps.com/api` | Titus Simulator API base URL |
| `web_ui_url` | `https://titussim.comcentricapps.com` | Streamlit web UI URL |
| `api_port` | `8087` | API service port |
| `ui_port` | `8088` | Web UI port |
| `server_ip` | `47.128.231.85` | EC2 instance IP |
| `domain` | `titussim.comcentricapps.com` | Production domain |
| `ngrs_clocking_url` | `https://ngrs-api.comcentricapps.com/api/external/clocking/receive` | NGRS Clocking API endpoint |
| `ngrs_api_key` | `3a0e3418-34a1-4c2a-bdfa-fed82dfddbce` | NGRS API key (x-api-key header) |
| `roster_file_id` | Auto-populated | Current roster UUID |

**Note**: The NGRS API key is sent as `x-api-key` header with each clocking event POST request.

## Configuration

### Modify Environment Variables
1. Click environment dropdown (top right)
2. Click the eye icon next to environment name
3. Edit values as needed
4. Click **Save**

### Common Configurations

**Local Development:**
```
base_url = http://localhost:8087
ngrs_clocking_url = http://localhost:8080/api/integration/titus/clocking
```

**Production Server:**
```
base_url = https://titussim.comcentricapps.com/api
ngrs_clocking_url = https://ngrs-api.comcentricapps.com/api/external/clocking/receive
ngrs_api_key = 3a0e3418-34a1-4c2a-bdfa-fed82dfddbce
```

## Usage Workflow

### Standard RosterFileId Workflow
1. **Health Check** - Verify API is running
2. **Upload Roster** - Upload roster JSON → Get `roster_file_id` (auto-saved to environment)
3. **Run Simulation** - Choose mode:
   - **Immediate Mode** - For batch processing or testing
   - **Realtime Mode** - For scheduled/production use
4. **Get Roster Details** - Check roster status and data
5. **Get Statistics** - View overall simulation stats

### Testing Concurrent Rosters
1. **Upload Roster 1** - Note the `roster_file_id`
2. **Upload Roster 2** - Note the different `roster_file_id`
3. **Process Roster 1** - Use first UUID
4. **Process Roster 2** - Use second UUID
5. Both rosters processed independently!

## Sample Roster Data

The collection includes sample roster with NGRS format:

- **Officer 1**: Cheng Fong Lee (00037056)
  - Date: 2025-12-31
  - Shift: 10:15 - 19:15
  - Location: Bank Of China - Westgate

- **Officer 2**: John Doe (00012345)
  - Date: 2026-01-01
  - Shift: 08:00 - 17:00
  - Location: Bank Of China - Westgate

## Troubleshooting

### Connection Refused
- **Issue**: Cannot connect to API
- **Solution**: 
  - **Local**: Ensure Titus Simulator is running: `python -m uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8087`
  - **Production**: Check service status: `sudo systemctl status titus-simulator`

### RosterFileId Not Found
- **Issue**: Error message "Roster file {uuid} not found"
- **Solution**:
  - Verify the UUID is correct
  - Check if roster was successfully uploaded (run Upload Roster first)
  - Roster may have been cleaned up (7-day retention policy)

### Missing RosterFileId Parameter
- **Issue**: Error "rosterFileId parameter is required"
- **Solution**: Ensure you've uploaded a roster first, or manually set the `roster_file_id` environment variable

### NGRS Posting Fails
- **Issue**: `ngrs_available: false` in response
- **Solution**:
  - Set `NGRS_CLOCKING_URL` in `.env` file
  - Verify NGRS server is accessible
  - Check NGRS API endpoint is correct
  - Verify API key if required

### Invalid Simulation Mode
- **Issue**: Error "Invalid mode 'xxx'. Must be 'immediate' or 'realtime'."
- **Solution**: Use only `immediate` or `realtime` as mode parameter

### Empty Statistics
- **Issue**: `/stats` returns zeros
- **Solution**: Run a simulation first using `/run-from-file`

### Auto-Capture Not Working
- **Issue**: `roster_file_id` environment variable not auto-populated
- **Solution**: Ensure test scripts are enabled in Postman settings, or manually copy UUID from response

## RosterFileId Benefits

✅ **Thread-Safe** - Multiple rosters can be uploaded concurrently without conflicts  
✅ **Persistent** - Roster data survives service restarts  
✅ **Traceable** - Full audit trail with status tracking  
✅ **Retryable** - Failed processing can be retried using UUID  
✅ **Automatic Cleanup** - Old roster files deleted after 7 days  

## API Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid data) |
| 404 | Endpoint not found |
| 500 | Internal server error |

## Additional Resources

- **RosterFileId Workflow Guide**: `/ROSTERFILEID_WORKFLOW.md`
- **API Documentation**: See `/implementation_docs/JSON_SCHEMAS.md`
- **Source Code**: `/src/titus_simulator/`
- **Web UI**: Production - `https://titussim.comcentricapps.com`
- **Web UI**: Local - `http://localhost:8088` (if Streamlit is running)

## Production URLs

- **API**: https://titussim.comcentricapps.com/api
- **Web UI**: https://titussim.comcentricapps.com
- **Health Check**: https://titussim.comcentricapps.com/api/health
- **Server**: ec2-47-128-231-85.ap-southeast-1.compute.amazonaws.com

## Support

For issues or questions:
1. Check service logs: `sudo journalctl -u titus-simulator -n 50`
2. Review `/ROSTERFILEID_WORKFLOW.md` for workflow details
3. Review `/implementation_docs/JSON_SCHEMAS.md` for schema details
4. Verify environment variables are correctly configured

---

**Version**: 1.0  
**Last Updated**: 2025-12-04
