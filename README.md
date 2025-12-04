# Titus Simulator

A Python-based time-attendance simulation service that integrates with the NGRS backend. The Titus Simulator fetches roster assignments from NGRS, generates realistic clock-in and clock-out events with timing variations, and sends them back to NGRS for testing and development purposes. It uses SQLite to track already-simulated events and runs as a FastAPI microservice with a background scheduler.

## Features

- Fetches roster assignments from NGRS API
- Simulates realistic clock-in/out events with timing variations
- Prevents duplicate event generation using SQLite state tracking
- Runs as a FastAPI service with REST endpoints
- Background scheduler for automatic periodic simulation
- Configurable via environment variables
- **Web UI** for easy testing and monitoring (Streamlit-based)
- **Roster Converter** - Transform external shift assignment formats to NGRS format

## Tech Stack

- **Python 3.11+**
- **FastAPI** - REST API framework
- **Uvicorn** - ASGI server
- **SQLite** (aiosqlite) - State storage
- **httpx** - Async HTTP client
- **Pydantic** - Data validation and settings
- **APScheduler** - Background job scheduling
- **Loguru** - Structured logging

## Installation

```bash
# Install dependencies
pip install -e .

# For development
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file in the project root:

```env
NGRS_ROSTER_URL=http://localhost:8080/api/integration/titus/roster
NGRS_CLOCKING_URL=http://localhost:8080/api/integration/titus/clocking
NGRS_API_KEY=dev-token
POLL_INTERVAL_SECONDS=60
TIMEZONE=Asia/Singapore
DATABASE_PATH=sim_state.db
```

## Running

```bash
# Start the server
uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8000

# In development with auto-reload
uvicorn titus_simulator.api:app --reload

# Start the Web UI (in another terminal)
streamlit run streamlit_ui.py
# or use the convenience script
./start_ui.sh
```

## API Endpoints

- `GET /health` - Health check endpoint
- `POST /run-once` - Manually trigger a simulation cycle for today
- `GET /stats` - Get event statistics

## Web UI

Access the intuitive web interface at http://localhost:8501

- 📤 Upload and validate roster JSON files
- ▶️ Trigger simulations with one click
- 📊 View assignment status with IN/OUT times
- 📈 Monitor statistics and completion rates
- 🎨 Color-coded status indicators

See [UI_GUIDE.md](docs/UI_GUIDE.md) for detailed UI documentation.

## Roster Converter

Convert external shift assignment formats to NGRS-compatible roster format:

```bash
# View summary of assignments
python roster_converter.py output.json --summary

# Convert to NGRS format
python roster_converter.py output.json -o converted_roster.json

# Filter by date range
python roster_converter.py output.json \
  --start-date 2026-01-05 \
  --end-date 2026-01-10 \
  -o weekly_roster.json
```

After conversion, upload `converted_roster.json` via the Web UI or use it with the API.

See [CONVERTER_GUIDE.md](docs/CONVERTER_GUIDE.md) for complete documentation.

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Trigger manual simulation
curl -X POST http://localhost:8000/run-once
```

## How It Works

1. **Fetch Roster**: Retrieves scheduled deployments from NGRS
2. **Plan Events**: Generates clock-in/out events with realistic timing variations
3. **Check State**: Verifies which events have already been sent using SQLite
4. **Send Events**: Posts new simulated events to NGRS clocking API
5. **Update State**: Marks events as sent in the database

The simulator runs automatically in the background based on the configured poll interval.
