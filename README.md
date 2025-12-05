# Titus Simulator

A Python-based time-attendance simulation service that integrates with the NGRS backend. The Titus Simulator fetches roster assignments from NGRS, generates realistic clock-in and clock-out events with timing variations, and sends them back to NGRS for testing and development purposes. It uses SQLite to track already-simulated events and runs as a FastAPI microservice with a background scheduler.

## Features

- Receives roster assignments from NGRS via direct POST to `/upload-roster` endpoint
- Simulates realistic clock-in/out events with timing variations
- Prevents duplicate event generation using SQLite state tracking
- Runs as a FastAPI service with REST endpoints
- Background scheduler for automatic periodic simulation
- Configurable via environment variables
- **Web UI** for easy testing, monitoring, and roster management (Streamlit-based)

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
# NGRS API Configuration
# Production NGRS Clocking API
NGRS_CLOCKING_URL=https://ngrs-api.comcentricapps.com/api/external/clocking/receive
NGRS_API_KEY=3a0e3418-34a1-4c2a-bdfa-fed82dfddbce

# Port Configuration
TITUS_API_PORT=8087
TITUS_UI_PORT=8088

# Scheduler Configuration
POLL_INTERVAL_SECONDS=60

# Application Configuration
TIMEZONE=Asia/Singapore
DATABASE_PATH=sim_state.db
```

**Note**: The API key is sent as `x-api-key` header to the NGRS clocking endpoint.

## Running

```bash
# Start the server
uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8085

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

Access the intuitive web interface at http://localhost:8086

- 📤 Upload and validate roster JSON files
- ▶️ Trigger simulations with one click
- 📊 View assignment status with IN/OUT times
- 📈 Monitor statistics and completion rates
- 🎨 Color-coded status indicators

## Documentation

### Guides
- [Getting Started](implementation_docs/guides/GETTING_STARTED.md) - Quick start guide
- [Usage Guide](implementation_docs/guides/USAGE.md) - Detailed usage instructions
- [Quickstart](implementation_docs/guides/QUICKSTART.md) - Fast setup guide
- [UI Guide](implementation_docs/guides/UI_GUIDE.md) - Web interface documentation

### Deployment
- [Deployment Guide](implementation_docs/deployment/DEPLOYMENT.md) - Production deployment
- [Quick Deployment](implementation_docs/deployment/QUICKSTART_DEPLOYMENT.md) - Fast deploy checklist

### Technical
- [JSON Schemas](implementation_docs/JSON_SCHEMAS.md) - API data formats
- [Postman Collection](postman/README.md) - API testing

## Testing

```bash
# Health check
curl http://localhost:8085/health

# Trigger manual simulation
curl -X POST http://localhost:8085/run-once
```

## How It Works

1. **Receive Roster**: NGRS posts scheduled deployments directly to `/upload-roster` endpoint
2. **Plan Events**: Generates clock-in/out events with realistic timing variations
3. **Check State**: Verifies which events have already been sent using SQLite
4. **Send Events**: Posts simulated clocking events to NGRS clocking API
5. **Update State**: Marks events as sent in the database

The simulator runs automatically in the background based on the configured poll interval.
