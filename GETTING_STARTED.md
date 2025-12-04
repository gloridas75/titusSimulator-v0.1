# 🚀 Titus Simulator - Quick Start Guide

## What You Have

A complete, production-ready Python application that simulates time-attendance clock-in/out events for the NGRS backend.

## Project Structure ✅

```
titusSimulator-v0.1/
├── src/titus_simulator/       # Main application package
│   ├── api.py                 # FastAPI REST service
│   ├── config.py              # Configuration management
│   ├── models.py              # Data models with parsing
│   ├── roster_client.py       # NGRS roster API client
│   ├── clocking_client.py     # NGRS clocking API client
│   ├── state_store.py         # SQLite event tracking
│   ├── simulator.py           # Event generation logic
│   └── scheduler.py           # Background job scheduling
├── pyproject.toml             # Package configuration
├── requirements.txt           # Dependencies
├── .env.example              # Configuration template
├── README.md                 # Project overview
├── USAGE.md                  # Detailed usage guide
├── start.sh                  # Easy startup script
└── test_components.py        # Component testing
```

## Next Steps

### Step 1: Set Up Environment

```bash
# Navigate to project
cd "/Users/glori/1 Anthony_Workspace/My Developments/NGRS/titusSimulator-v0.1"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .
```

### Step 2: Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your NGRS API endpoints
nano .env  # or use your preferred editor
```

Required configuration in `.env`:
```env
NGRS_ROSTER_URL=http://your-ngrs-host:8080/api/integration/titus/roster
NGRS_CLOCKING_URL=http://your-ngrs-host:8080/api/integration/titus/clocking
NGRS_API_KEY=your-api-key-if-needed
```

### Step 3: Test Components (Optional but Recommended)

```bash
python test_components.py
```

This verifies that all components work correctly before running the full server.

### Step 4: Start the Server

**Easy way:**
```bash
./start.sh
```

**Or manually:**
```bash
uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8000 --reload
```

### Step 5: Verify It's Running

```bash
# Health check
curl http://localhost:8000/health

# View interactive API docs
open http://localhost:8000/docs
```

### Step 6: Trigger a Test Simulation

```bash
# Manually run a simulation cycle for today
curl -X POST http://localhost:8000/run-once

# Check statistics
curl http://localhost:8000/stats
```

## What Happens Automatically

Once started, the simulator:

1. **Every 60 seconds** (configurable):
   - Fetches today's roster from NGRS
   - Generates realistic clock-in/out events
   - Sends only new events (no duplicates)
   - Updates SQLite database

2. **Event Timing**:
   - Clock-IN: -5 to +10 minutes from planned start
   - Clock-OUT: -10 to +15 minutes from planned end
   - Deterministic (same input = same output)

3. **State Management**:
   - Tracks sent events in SQLite (`sim_state.db`)
   - Prevents duplicate submissions
   - Provides statistics via API

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/run-once` | POST | Manual trigger for today |
| `/stats` | GET | Event statistics |
| `/docs` | GET | Interactive API documentation |
| `/redoc` | GET | Alternative API docs |

## Key Features Implemented

✅ **Roster Integration**
- Fetches assignments from NGRS
- Parses complex date/time formats
- Handles timezone conversions

✅ **Event Simulation**
- Realistic timing variations
- Deterministic randomness
- IN and OUT events

✅ **State Management**
- SQLite database for tracking
- Duplicate prevention
- Event history

✅ **REST API**
- FastAPI framework
- Health checks
- Manual triggers
- Statistics endpoint

✅ **Background Scheduler**
- APScheduler integration
- Configurable intervals
- Automatic execution

✅ **Robust Error Handling**
- Structured logging (Loguru)
- HTTP error handling
- Database error handling

✅ **Configuration**
- Environment-based settings
- Pydantic validation
- Secure API key support

## Customization

### Change Poll Interval

Edit `.env`:
```env
POLL_INTERVAL_SECONDS=30  # Run every 30 seconds
```

### Change Timezone

Edit `.env`:
```env
TIMEZONE=America/New_York
```

### Custom Event Timing

Edit `src/titus_simulator/simulator.py` in the `plan_events_for_assignment` method:

```python
# Current: -5 to +10 minutes for IN
in_offset = timedelta(minutes=rng.randint(-5, 10))

# Make it: -10 to +20 minutes for IN
in_offset = timedelta(minutes=rng.randint(-10, 20))
```

## Monitoring

### View Logs

The application logs to console. To save logs:
```bash
uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8000 2>&1 | tee simulator.log
```

### Check Database

```bash
sqlite3 sim_state.db "SELECT COUNT(*) FROM simulated_events;"
```

### Monitor with Health Checks

```bash
# Set up a cron job or monitoring tool
*/5 * * * * curl -f http://localhost:8000/health || echo "Service down!"
```

## Troubleshooting

### Issue: Dependencies not found
**Solution:**
```bash
pip install -e .
```

### Issue: Can't connect to NGRS
**Solution:**
- Check `NGRS_ROSTER_URL` and `NGRS_CLOCKING_URL` in `.env`
- Verify NGRS is running and accessible
- Test with: `curl http://your-ngrs-host:8080/api/integration/titus/roster`

### Issue: Database locked
**Solution:**
- Only one instance should run at a time
- Stop other instances: `pkill -f "uvicorn titus_simulator"`

### Issue: No events being generated
**Solution:**
- Check that roster exists for today: `curl -X POST http://localhost:8000/run-once`
- Review logs for errors
- Verify date format matches NGRS expectations

## Development Workflow

1. **Make changes** to code in `src/titus_simulator/`
2. **Test** with `python test_components.py`
3. **Run** with `--reload` flag for auto-reload:
   ```bash
   uvicorn titus_simulator.api:app --reload
   ```
4. **Verify** via API docs at http://localhost:8000/docs

## Production Deployment

See `USAGE.md` for:
- Docker deployment
- systemd service setup
- Production configuration
- Monitoring strategies

## Documentation Files

- **README.md**: Project overview and features
- **USAGE.md**: Comprehensive usage guide
- **GETTING_STARTED.md**: This quick start guide
- **prompts_for_startofdevelopment.md**: Original requirements

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI Server                    │
│                  (Port 8000)                        │
└───────────────┬─────────────────────────────────────┘
                │
        ┌───────┴────────┐
        │                │
   ┌────▼─────┐    ┌────▼────────┐
   │  Manual  │    │  Scheduler  │
   │ Trigger  │    │(Every 60s)  │
   │(/run-once)│    │             │
   └────┬─────┘    └────┬────────┘
        │               │
        └───────┬───────┘
                │
         ┌──────▼───────┐
         │  Simulator   │
         └──────┬───────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼──┐  ┌────▼────┐  ┌──▼────┐
│Roster│  │Clocking │  │ State │
│Client│  │ Client  │  │ Store │
└───┬──┘  └────┬────┘  └──┬────┘
    │          │           │
┌───▼──┐  ┌────▼────┐  ┌──▼────┐
│ NGRS │  │  NGRS   │  │SQLite │
│Roster│  │Clocking │  │  DB   │
│ API  │  │   API   │  │       │
└──────┘  └─────────┘  └───────┘
```

## Success Criteria

You'll know it's working when:

1. ✅ Server starts without errors
2. ✅ `/health` returns `"status": "ok"`
3. ✅ `/run-once` processes assignments and sends events
4. ✅ `/stats` shows increasing event counts
5. ✅ `sim_state.db` file is created and growing
6. ✅ NGRS receives clocking events successfully

## Next Level Features (Future Enhancements)

The current implementation handles basic IN/OUT events. You can extend it to:

- **Absent scenarios**: No events generated for certain assignments
- **Very late**: Generate events much later than planned
- **Early departure**: Generate OUT events significantly early
- **Multiple shifts**: Handle assignments with break periods
- **Overtime**: Generate OUT events much later than planned end
- **Historical simulation**: Process past dates, not just today
- **Batch processing**: Process multiple dates in one cycle
- **Event replay**: Regenerate and resend events for testing

To add these, modify `simulator.py::plan_events_for_assignment()`.

## Support & Help

- Review `USAGE.md` for detailed documentation
- Check logs for error messages
- Test components with `test_components.py`
- Use `/docs` endpoint for API exploration
- Inspect database: `sqlite3 sim_state.db`

---

**Congratulations! Your Titus Simulator is ready to use!** 🎉

Start the server and watch it simulate realistic attendance events for your NGRS backend.
