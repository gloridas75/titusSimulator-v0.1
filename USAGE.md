# Titus Simulator - Usage Guide

## Quick Start

### 1. Initial Setup

```bash
# Clone or navigate to the project directory
cd titusSimulator-v0.1

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your NGRS API endpoints
# Minimum required configuration:
# - NGRS_ROSTER_URL
# - NGRS_CLOCKING_URL
```

### 3. Run the Simulator

**Option A: Using the startup script (recommended)**
```bash
./start.sh
```

**Option B: Using uvicorn directly**
```bash
uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8000 --reload
```

**Option C: Production mode**
```bash
uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "service": "titus-simulator",
  "version": "0.1.0"
}
```

### Manual Trigger
Manually trigger a simulation cycle for today:
```bash
curl -X POST http://localhost:8000/run-once
```

Response:
```json
{
  "status": "completed",
  "result": {
    "date": "2024-12-02",
    "assignments_found": 15,
    "events_sent": 30
  }
}
```

### Statistics
Get statistics about simulated events:
```bash
curl http://localhost:8000/stats
```

Response:
```json
{
  "status": "ok",
  "stats": {
    "total_assignments": 150,
    "in_events_sent": 145,
    "out_events_sent": 140
  }
}
```

## Interactive API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API documentation where you can test endpoints directly.

## Testing Components

Before running the full server, test individual components:

```bash
python test_components.py
```

This will verify:
- Data model parsing (date/time formats)
- SQLite state store operations
- Event planning logic and determinism

## How It Works

### Background Scheduler

The simulator runs automatically in the background based on the configured interval:

1. Every `POLL_INTERVAL_SECONDS` (default: 60 seconds)
2. Fetches today's roster from NGRS
3. Plans IN/OUT events with random timing variations
4. Checks which events were already sent (SQLite)
5. Sends only new events to NGRS
6. Updates the database

### Event Timing

Clock events are generated with realistic variations:

- **Clock IN**: -5 to +10 minutes from planned start
  - Early: Person arrives 5 minutes early
  - Late: Person arrives 10 minutes late
  
- **Clock OUT**: -10 to +15 minutes from planned end
  - Early: Person leaves 10 minutes early
  - Late: Person leaves 15 minutes late

The timing is deterministic based on deployment and personnel IDs, so the same assignment always generates the same events.

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NGRS_ROSTER_URL` | NGRS roster API endpoint | Required |
| `NGRS_CLOCKING_URL` | NGRS clocking API endpoint | Required |
| `NGRS_API_KEY` | API authentication key | None |
| `POLL_INTERVAL_SECONDS` | How often to run simulation | 60 |
| `TIMEZONE` | Timezone for date/time operations | Asia/Singapore |
| `DATABASE_PATH` | SQLite database file path | sim_state.db |

### Adjusting Poll Interval

For testing, you might want faster cycles:
```env
POLL_INTERVAL_SECONDS=30  # Run every 30 seconds
```

For production, slower intervals might be appropriate:
```env
POLL_INTERVAL_SECONDS=300  # Run every 5 minutes
```

## Database

### Location

The SQLite database is stored at the path specified in `DATABASE_PATH` (default: `sim_state.db`).

### Schema

```sql
CREATE TABLE simulated_events (
    deployment_item_id TEXT NOT NULL,
    personnel_id TEXT NOT NULL,
    in_sent_at TEXT NULL,
    out_sent_at TEXT NULL,
    PRIMARY KEY (deployment_item_id, personnel_id)
);
```

### Inspecting the Database

```bash
# Using sqlite3 command-line tool
sqlite3 sim_state.db

# View all records
SELECT * FROM simulated_events;

# Count sent events
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN in_sent_at IS NOT NULL THEN 1 ELSE 0 END) as in_sent,
    SUM(CASE WHEN out_sent_at IS NOT NULL THEN 1 ELSE 0 END) as out_sent
FROM simulated_events;
```

### Resetting the Database

To start fresh and resend all events:
```bash
rm sim_state.db
# Restart the server - database will be recreated
```

## Logs

The application uses Loguru for structured logging. Logs are output to the console and include:

- Roster fetch operations
- Event planning and sending
- Scheduler triggers
- Database operations
- Errors and warnings

Example log output:
```
2024-12-02 14:30:00.123 | INFO     | Starting simulation cycle for 2024-12-02
2024-12-02 14:30:00.234 | INFO     | Fetched 25 roster assignments
2024-12-02 14:30:00.345 | INFO     | Sending 50 unsent events
2024-12-02 14:30:00.456 | INFO     | Successfully sent 50 events (status: 200)
2024-12-02 14:30:00.567 | INFO     | Simulation cycle complete: 50 events sent for 25 assignments
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'titus_simulator'"

Make sure you've installed the package:
```bash
pip install -e .
```

### "ValidationError" on startup

Check your `.env` file. The required fields are:
- `NGRS_ROSTER_URL`
- `NGRS_CLOCKING_URL`

### Database locked errors

Only one instance of the simulator should run at a time. Stop any other running instances.

### No events being sent

1. Check that roster data exists for today's date
2. Verify NGRS API endpoints are accessible
3. Check logs for HTTP errors
4. Use the `/run-once` endpoint to manually trigger a cycle and see detailed results

### Events sent but not appearing in NGRS

1. Check NGRS API authentication (NGRS_API_KEY)
2. Verify the payload format matches NGRS expectations
3. Check NGRS logs for processing errors

## Development

### Project Structure

```
titusSimulator-v0.1/
├── src/
│   └── titus_simulator/
│       ├── __init__.py
│       ├── api.py              # FastAPI application
│       ├── config.py           # Settings management
│       ├── models.py           # Pydantic data models
│       ├── roster_client.py   # NGRS roster API client
│       ├── clocking_client.py # NGRS clocking API client
│       ├── state_store.py     # SQLite state management
│       ├── simulator.py       # Core simulation logic
│       └── scheduler.py       # Background job scheduler
├── pyproject.toml            # Project metadata & dependencies
├── requirements.txt          # Dependencies list
├── .env.example             # Environment template
├── .gitignore              # Git ignore patterns
├── README.md               # Project overview
├── USAGE.md                # This file
├── start.sh                # Startup script
└── test_components.py      # Component tests

```

### Running in Development Mode

Use the `--reload` flag for auto-reloading on code changes:
```bash
uvicorn titus_simulator.api:app --reload
```

### Adding New Features

To add new simulation scenarios (e.g., absent, very late):

1. Modify `simulator.py::plan_events_for_assignment()`
2. Add new event generation logic
3. Update state store if needed for new event types
4. Test with `test_components.py`

## Production Deployment

### Using Docker (Optional)

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -e .

CMD ["uvicorn", "titus_simulator.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t titus-simulator .
docker run -p 8000:8000 --env-file .env titus-simulator
```

### Using systemd (Linux)

Create `/etc/systemd/system/titus-simulator.service`:
```ini
[Unit]
Description=Titus Simulator Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/titusSimulator-v0.1
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable titus-simulator
sudo systemctl start titus-simulator
sudo systemctl status titus-simulator
```

### Monitoring

Use the health check endpoint for monitoring:
```bash
# Automated health check (cron, monitoring tool, etc.)
curl -f http://localhost:8000/health || alert-system
```

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Review this usage guide
3. Test individual components with `test_components.py`
4. Verify NGRS API connectivity and authentication
