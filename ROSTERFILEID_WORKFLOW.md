# RosterFileId UUID-Based Workflow

## Overview
The Titus Simulator now uses UUID-based roster file tracking for better concurrency, persistence, and traceability. Each uploaded roster receives a unique `RosterFileId` that can be used to process that specific roster independently.

## Benefits
- **Thread-Safe**: Multiple rosters can be uploaded concurrently without conflicts
- **Persistent**: Roster data survives service restarts
- **Traceable**: Full audit trail of roster uploads and processing
- **Retryable**: Failed processing can be retried using the RosterFileId
- **Automatic Cleanup**: Old roster files are deleted after 7 days

## Workflow

### 1. Upload Roster
```bash
curl -X POST "https://titussim.comcentricapps.com/api/upload-roster" \
  -H "Content-Type: application/json" \
  -d @roster.json
```

**Response:**
```json
{
  "success": true,
  "roster_file_id": "e8d63206-3ab3-41a5-961d-1e406c1c7de9",
  "results": [
    {
      "PersonnelId": "P001",
      "RequestId": "d610c96b-faad-476d-a6f5-0fe717118869"
    }
  ]
}
```

### 2. Trigger Simulation
Use the `roster_file_id` from the upload response:

**Immediate Mode (batch processing):**
```bash
curl -X POST "https://titussim.comcentricapps.com/api/run-from-file?mode=immediate&rosterFileId=e8d63206-3ab3-41a5-961d-1e406c1c7de9"
```

**Realtime Mode (time-based):**
```bash
curl -X POST "https://titussim.comcentricapps.com/api/run-from-file?mode=realtime&rosterFileId=e8d63206-3ab3-41a5-961d-1e406c1c7de9"
```

**Response:**
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
    "records_cleaned": 80
  }
}
```

### 3. Retrieve Roster Details
```bash
curl "https://titussim.comcentricapps.com/api/roster?rosterFileId=e8d63206-3ab3-41a5-961d-1e406c1c7de9"
```

**Response:**
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

## Roster Status Values
- `pending`: Roster uploaded, not yet processed
- `processing`: Currently being processed
- `completed`: Successfully processed
- `failed`: Processing failed (check logs for details)

## Database Schema
```sql
CREATE TABLE roster_files (
    roster_file_id TEXT PRIMARY KEY,
    uploaded_at TEXT NOT NULL,
    assignments_count INTEGER NOT NULL,
    roster_data TEXT NOT NULL,
    status TEXT DEFAULT 'pending'
);
```

## Error Handling

### Missing RosterFileId
```bash
curl -X POST "https://titussim.comcentricapps.com/api/run-from-file?mode=immediate"
```
**Response:**
```json
{
  "status": "error",
  "message": "rosterFileId parameter is required"
}
```

### Invalid RosterFileId
```bash
curl -X POST "https://titussim.comcentricapps.com/api/run-from-file?mode=immediate&rosterFileId=invalid-uuid"
```
**Response:**
```json
{
  "status": "error",
  "message": "Roster file invalid-uuid not found"
}
```

## Automatic Cleanup
- Roster files older than **7 days** are automatically deleted
- Cleanup runs daily at **2:00 AM UTC**
- Simulated events are kept for **2 days**

## Testing Results

### Test 1: Upload First Roster
✅ Uploaded sample_roster.json (5 assignments)
- RosterFileId: `e8d63206-3ab3-41a5-961d-1e406c1c7de9`
- Status: `completed`

### Test 2: Upload Second Roster
✅ Uploaded rosterdata_0412_001.json (40 assignments)
- RosterFileId: `7a0a05dd-9d05-476a-bc78-c8470283708c`
- Status: `completed`

### Test 3: Process First Roster (Immediate Mode)
✅ Generated 0 events (sample roster has invalid dates)
- Roster file ID returned in response
- Status updated to `completed`

### Test 4: Process Second Roster (Immediate Mode)
✅ Generated 80 events (40 IN + 40 OUT)
- First roster unaffected
- Concurrent processing verified

### Test 5: Process with Realtime Mode
✅ Generated 0 events (shifts not in current time window)
- Mode validation working correctly

### Test 6: Error Handling
✅ Missing rosterFileId: Returns error message
✅ Invalid rosterFileId: Returns not found error

## Implementation Details

### Changed Files
1. **src/titus_simulator/state_store.py**
   - Added `roster_files` table
   - Added methods: `store_roster_file()`, `get_roster_file()`, `update_roster_file_status()`, `cleanup_old_roster_files()`

2. **src/titus_simulator/api.py**
   - Updated `/upload-roster`: Generates UUID, stores in database, returns roster_file_id
   - Updated `/run-from-file`: Accepts rosterFileId parameter, fetches from database
   - Updated `/roster`: Fetches roster by rosterFileId
   - Removed: `app.state.uploaded_roster` (in-memory storage)

3. **src/titus_simulator/scheduler.py**
   - Added roster file cleanup to daily job (7-day retention)

## Migration Notes
- Old workflow using in-memory storage is deprecated
- All roster operations now require rosterFileId
- Backward compatibility: None (breaking change)

## Next Steps
- [ ] Add webhook endpoint for NGRS to receive completion notifications
- [ ] Add status endpoint: `GET /roster-file/{rosterFileId}/status`
- [ ] Implement retry mechanism for failed roster processing
- [ ] Add rate limiting for roster uploads
- [ ] Update Postman collection with rosterFileId examples
