# Postman Collection Guide

## Overview
This folder contains Postman collections and environments for testing the Titus Simulator API.

## Files

1. **Titus_Simulator_API.postman_collection.json** - Main API collection
2. **Titus_Simulator.postman_environment.json** - Local development environment
3. **Titus_Simulator_Production.postman_environment.json** - Production environment

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
   - **Titus Simulator Environment** (for local testing on localhost:8085)
   - **Titus Simulator - Production** (for production server)

## Environment Configuration

### Local Environment
- **base_url**: `http://localhost:8085`
- **ngrs_clocking_url**: `http://localhost:8080/api/integration/titus/clocking`
- **ngrs_api_key**: (empty for local testing)

### Production Environment
- **base_url**: `http://your-production-server:8085`
- **ngrs_clocking_url**: `http://your-ngrs-server:8080/api/integration/titus/clocking`
- **ngrs_api_key**: (set your production API key)

**Note**: Update the production environment URLs with your actual server addresses before deployment.

## Available Endpoints

### 1. Health Check
- **Method**: GET
- **URL**: `{{base_url}}/health`
- **Description**: Verify API is running
- **Expected Response**: 
  ```json
  {
    "status": "healthy",
    "version": "0.1.0"
  }
  ```

### 2. Upload Roster Data
- **Method**: POST
- **URL**: `{{base_url}}/upload-roster`
- **Body**: JSON roster data in NGRS format (with `__metadata`)
- **Description**: Upload roster assignments to simulator
- **Expected Response**:
  ```json
  {
    "status": "success",
    "message": "Roster uploaded successfully",
    "assignments_count": 2
  }
  ```

### 3. Run Simulation from Uploaded File
- **Method**: POST
- **URL**: `{{base_url}}/run-from-file`
- **Description**: Generate clock events from uploaded roster
- **Expected Response**:
  ```json
  {
    "status": "completed",
    "result": {
      "assignments_found": 2,
      "assignments_parsed": 2,
      "events_generated": 4,
      "ngrs_available": false
    }
  }
  ```

### 4. Run Simulation by Date
- **Method**: POST
- **URL**: `{{base_url}}/run-once?date=2026-01-15`
- **Query Params**:
  - `date`: YYYY-MM-DD format
- **Description**: Fetch roster from NGRS and simulate
- **Note**: Requires NGRS API to be running

### 5. Get Statistics
- **Method**: GET
- **URL**: `{{base_url}}/stats`
- **Description**: View simulation statistics
- **Expected Response**:
  ```json
  {
    "total_assignments": 2,
    "total_events": 4,
    "in_events": 2,
    "out_events": 2,
    "completion_rate": 100.0
  }
  ```

### 6. NGRS - Receive Clocking Event (Mock)
- **Method**: POST
- **URL**: `{{ngrs_clocking_url}}`
- **Body**: Single clocking event JSON
- **Description**: Mock NGRS endpoint for testing event format
- **Note**: This is a reference request - actual NGRS endpoint must be implemented separately

## Environment Variables

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `base_url` | `http://localhost:8085` | Titus Simulator API base URL |
| `ngrs_clocking_url` | `http://localhost:8080/api/integration/titus/clocking` | NGRS Clocking API endpoint |
| `ngrs_api_key` | _(empty)_ | Optional API key for NGRS authentication |

Note: `ngrs_roster_url` is no longer needed as NGRS POSTs roster data directly to Titus Simulator's `/upload-roster` endpoint.

## Configuration

### Modify Environment Variables
1. Click environment dropdown (top right)
2. Click the eye icon next to **Titus Simulator Environment**
3. Edit values as needed
4. Click **Save**

### Common Configurations

**Local Development:**
```
base_url = http://localhost:8085
ngrs_clocking_url = http://localhost:8080/api/integration/titus/clocking
```

**Remote Server:**
```
base_url = http://your-server-ip:8085
ngrs_clocking_url = http://ngrs-server:8080/api/integration/titus/clocking
```

## Usage Workflow

### Testing File Upload Flow
1. Run **Health Check** to verify API is running
2. Run **Upload Roster Data** with sample data
3. Run **Run Simulation from Uploaded File**
4. Run **Get Statistics** to view results

### Testing NGRS Integration Flow
1. Ensure NGRS API is running
2. NGRS should POST roster data to Titus Simulator's `/upload-roster` endpoint
3. Run **Run Simulation from Uploaded File** to process the roster
4. Run **Get Statistics** to view results

### Testing Clocking Event Format
1. Modify the body in **NGRS - Receive Clocking Event (Mock)**
2. Send request to your mock NGRS endpoint
3. Verify format matches expected schema

## Sample Roster Data

The collection includes a sample roster with 2 assignments:

- **Officer 1**: Cheng Fong Lee (00037056)
  - Date: 2026-01-01
  - Shift: 10:15 - 19:15
  - Location: Bank Of China - Westgate

- **Officer 2**: John Doe (00012345)
  - Date: 2026-01-02
  - Shift: 08:00 - 17:00
  - Location: Bank Of China - Westgate

## Troubleshooting

### Connection Refused
- **Issue**: Cannot connect to `http://localhost:8085`
- **Solution**: 
  - Ensure Titus Simulator is running: `python -m uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8085`
  - Check if port 8085 is available

### NGRS API Not Available
- **Issue**: `/run-once` returns error about NGRS connection
- **Solution**: 
  - This is expected if NGRS is not running
  - Use `/upload-roster` + `/run-from-file` workflow instead
  - Events are still generated and tracked locally

### Invalid Date Format
- **Issue**: Error when calling `/run-once`
- **Solution**: Ensure date is in `YYYY-MM-DD` format (e.g., `2026-01-15`)

### Empty Statistics
- **Issue**: `/stats` returns zeros
- **Solution**: Run a simulation first using `/run-from-file` or `/run-once`

## API Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid data) |
| 404 | Endpoint not found |
| 500 | Internal server error |

## Additional Resources

- **API Documentation**: See `/implementation_docs/JSON_SCHEMAS.md`
- **Source Code**: `/src/titus_simulator/`
- **Web UI**: `http://localhost:8501` (if Streamlit is running)

## Support

For issues or questions:
1. Check logs in terminal where API is running
2. Review `/implementation_docs/JSON_SCHEMAS.md` for schema details
3. Verify environment variables are correctly configured

---

**Version**: 1.0  
**Last Updated**: 2025-12-04
