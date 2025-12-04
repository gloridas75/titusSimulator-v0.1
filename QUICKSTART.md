# 🚀 Quick Start - Running Both API and UI

## Visual Guide

```
┌─────────────────────────────────────────────────────┐
│              Titus Simulator System                 │
└─────────────────────────────────────────────────────┘

  Terminal 1                    Terminal 2
  ──────────                    ──────────
  
  ./start.sh                    ./start_ui.sh
      │                              │
      │                              │
      ▼                              ▼
  ┌─────────┐                  ┌─────────┐
  │   API   │◄─────────────────│   UI    │
  │  :8000  │      HTTP        │  :8501  │
  └────┬────┘                  └─────────┘
       │
       │ Fetches Roster
       │ Sends Events
       │
       ▼
  ┌─────────┐
  │  NGRS   │
  │ Backend │
  └─────────┘
       │
       │ Stores
       │
       ▼
  ┌─────────┐
  │ SQLite  │
  │   DB    │
  └─────────┘
```

## Step-by-Step Setup

### 1️⃣ First Time Setup

```bash
# Clone/navigate to project
cd titusSimulator-v0.1

# Setup environment
make setup
# This creates venv, installs dependencies, creates .env
```

### 2️⃣ Configure

```bash
# Edit .env file
nano .env

# Required settings:
NGRS_ROSTER_URL=http://your-ngrs:8080/api/integration/titus/roster
NGRS_CLOCKING_URL=http://your-ngrs:8080/api/integration/titus/clocking
```

### 3️⃣ Start Everything

**Option A: Separate Terminals (Recommended for Development)**

```bash
# Terminal 1 - Start API
make run
# or
./start.sh

# Terminal 2 - Start UI
make ui
# or
./start_ui.sh
```

**Option B: Single Command (Quick Testing)**

```bash
make both
# Starts both API and UI together
```

**Option C: Manual Control**

```bash
# Terminal 1
source venv/bin/activate
uvicorn titus_simulator.api:app --reload

# Terminal 2
source venv/bin/activate
streamlit run streamlit_ui.py
```

### 4️⃣ Access

Open your browser:

- **API Docs**: http://localhost:8000/docs
- **Web UI**: http://localhost:8501

### 5️⃣ Test

In the Web UI:

1. Check that **API Status** shows ✅ (sidebar)
2. Go to **"Upload Roster"** tab
3. Upload `sample_roster.json`
4. Click **"Run Simulation Now"** (sidebar)
5. Go to **"Status Dashboard"** tab
6. See your simulated events! 🎉

## Common Commands

| Task | Command |
|------|---------|
| First setup | `make setup` |
| Install deps | `make install` |
| Run tests | `make test` |
| Start API | `make run` |
| Start API (dev) | `make dev` |
| Start UI | `make ui` |
| Start both | `make both` |
| Get health | `make health` |
| Trigger sim | `make trigger` |
| View stats | `make stats` |
| Clean up | `make clean` |
| Help | `make help` |

## What Each Service Does

### API Server (Port 8000)

- ✅ Accepts REST API requests
- 🔄 Runs background scheduler (every 60s)
- 📞 Calls NGRS APIs (roster & clocking)
- 💾 Manages SQLite database
- 📊 Provides statistics endpoint

### Web UI (Port 8501)

- 🖥️ Beautiful web interface
- 📤 Upload roster files
- ▶️ Manual simulation trigger
- 📊 Real-time status dashboard
- 📈 Statistics visualization
- 🎨 Color-coded status

## Stopping Services

### Stop API
```bash
# In Terminal 1, press:
Ctrl+C
```

### Stop UI
```bash
# In Terminal 2, press:
Ctrl+C
```

### Kill All
```bash
# If running in background
pkill -f uvicorn
pkill -f streamlit
```

## Ports Used

| Service | Port | URL |
|---------|------|-----|
| API | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |
| Web UI | 8501 | http://localhost:8501 |
| NGRS (your) | 8080 | http://localhost:8080 |

## Troubleshooting

### Port Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
uvicorn titus_simulator.api:app --port 8001
```

### API Not Running (in UI)

1. Check Terminal 1 - is API still running?
2. Try: `curl http://localhost:8000/health`
3. Restart API: `make run`

### Database Not Found

```bash
# Check if it exists
ls -la sim_state.db

# If missing, trigger a simulation
curl -X POST http://localhost:8000/run-once
# Or use UI: Click "Run Simulation Now"
```

### Dependencies Missing

```bash
# Reinstall everything
make install
# or
pip install -e .
```

## Development Workflow

```bash
# 1. Start API in dev mode (auto-reloads on changes)
make dev

# 2. In another terminal, start UI
make ui

# 3. Make changes to code
# - API: Changes auto-reload
# - UI: Press 'R' in browser to reload

# 4. Test changes immediately in UI

# 5. Run tests
make test
```

## Production Deployment

### Using systemd (Linux)

```bash
# API service
sudo systemctl start titus-simulator

# Access UI remotely
streamlit run streamlit_ui.py --server.address=0.0.0.0
```

### Using Docker

```bash
# Build
docker build -t titus-simulator .

# Run API
docker run -p 8000:8000 --env-file .env titus-simulator

# Run UI (separate container)
docker run -p 8501:8501 streamlit-ui
```

## Environment Variables Summary

```env
# Required
NGRS_ROSTER_URL=...          # Where to fetch roster
NGRS_CLOCKING_URL=...        # Where to send events

# Optional
NGRS_API_KEY=...             # API authentication
POLL_INTERVAL_SECONDS=60     # How often to run
TIMEZONE=Asia/Singapore      # Your timezone
DATABASE_PATH=sim_state.db   # SQLite file path
```

## Monitoring

### Check Health
```bash
curl http://localhost:8000/health
```

### Get Statistics
```bash
curl http://localhost:8000/stats
```

### Trigger Manually
```bash
curl -X POST http://localhost:8000/run-once
```

### Or Use Web UI
All of the above can be done visually in the Web UI!

## Files & Directories

```
titusSimulator-v0.1/
├── src/titus_simulator/   # Main application code
├── streamlit_ui.py        # Web UI application
├── start.sh              # Start API
├── start_ui.sh           # Start UI
├── sample_roster.json    # Test data
├── .env                  # Configuration (create from .env.example)
├── sim_state.db          # SQLite database (created on first run)
└── venv/                 # Virtual environment (created by setup)
```

## Next Steps

1. ✅ **Setup Complete** - You've installed everything
2. ✅ **API Running** - Backend is working
3. ✅ **UI Running** - Web interface is accessible
4. 📝 **Configure** - Set your NGRS endpoints in `.env`
5. 🎮 **Test** - Upload `sample_roster.json` and trigger simulation
6. 📊 **Monitor** - Watch events in the dashboard
7. 🚀 **Deploy** - When ready, deploy to production

## Support

- 📖 **USAGE.md** - Detailed usage guide
- 🎨 **UI_GUIDE.md** - Web UI documentation
- 🚀 **GETTING_STARTED.md** - Setup guide
- 📚 API Docs: http://localhost:8000/docs

---

**You're all set! Start both services and begin testing!** 🎉
