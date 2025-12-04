A Python-based Titus Time-Attendance Simulator designed to:

Fetch roster assignments from the NGRS backend.

Simulate clock-in & clock-out behaviour based on roster timing.

Send simulated attendance events back to NGRS.

Store sent events in a lightweight SQLite DB to avoid duplication.

Run as a FastAPI microservice + background scheduler (APScheduler).

Work seamlessly with VS Code + GitHub Copilot + Claude Code for full AI-enabled development workflow.

1. Tech Stack Overview
Backend Language

Python 3.11

Framework

FastAPI (REST API service)

Uvicorn (ASGI server)

APScheduler (background periodic jobs)

Database

SQLite (aiosqlite)

Networking / JSON

httpx (Async HTTP client)

pydantic (Data models, JSON validation)

Other Libraries

python-dotenv (environment configs)

loguru (structured logging)

zoneinfo (timezone handling)

uuid, datetime, etc.

Tooling

VS Code

GitHub Copilot

Claude Code (Anthropic)

Full AI-driven development workflow

2. Development Prompts (2.1 → 2.10)

Below are all the refined prompts you will give to Copilot or Claude Code inside VS Code.

Each prompt corresponds to one major part of the system.

2.1 Project Skeleton (Create Folder Structure)

Prompt:

I’m building a “Titus Simulator” backend in Python using this tech stack:

- Python 3.11
- FastAPI + Uvicorn
- SQLite (aiosqlite)
- httpx
- pydantic
- python-dotenv
- APScheduler
- loguru

Create a new package called `titus_simulator` under `src/` with this structure:

src/titus_simulator/__init__.py
src/titus_simulator/config.py
src/titus_simulator/models.py
src/titus_simulator/roster_client.py
src/titus_simulator/clocking_client.py
src/titus_simulator/state_store.py
src/titus_simulator/simulator.py
src/titus_simulator/api.py
src/titus_simulator/scheduler.py

Also create a `pyproject.toml` with dependencies:

fastapi
uvicorn[standard]
httpx
pydantic
python-dotenv
aiosqlite
apscheduler
loguru

Add a simple README.md that explains in one paragraph what the Titus Simulator does.

2.2 Config: BaseSettings-driven configuration

Prompt:

In `src/titus_simulator/config.py`, implement configuration using pydantic_settings.BaseSettings.

Class: Settings(BaseSettings)
Fields:
- ngrs_roster_url: str
- ngrs_clocking_url: str
- ngrs_api_key: str | None = None
- poll_interval_seconds: int = 60
- timezone: str = "Asia/Singapore"
- database_path: str = "sim_state.db"

Load environment variables from `.env` if present.

Expose a module-level singleton:
settings = Settings()

2.3 Models: Roster & Clocking Payloads

Prompt:

In `src/titus_simulator/models.py`, define Pydantic models for:

1. Raw input from NGRS → Titus simulator
   - Create the nested envelope structure:
     FunctionName
     list_item.data.d.results → list[RawRosterMetadata]
     list_item.data.d.summary →

   RawRosterMetadata fields (from __metadata):
     PersonnelId
     personnel_first_name
     personnel_last_name
     PersonnelType
     PersonnelTypeDescription
     SecSeqNum
     PrimarySeqNum
     demand_item_id
     customer_id
     customer_name
     deployment_location
     deployment_date (like "/Date(1755216000000)/")
     deploymentItm
     planner_group_id
     plant
     planned_start_time (PT10H15M00S)
     planned_end_time
     demand_type

2. Flattened model `RosterAssignment` with:
   deployment_item_id
   personnel_id
   first_name
   last_name
   plant
   planner_group_id
   demand_item_id
   customer_id
   customer_name
   deployment_location
   deployment_date (date)
   planned_start (datetime)
   planned_end (datetime)

   Implement classmethod:
     from_raw(cls, raw: RawRosterMetadata, tz: ZoneInfo)
     - parse /Date(milliseconds)/ format
     - parse PTxxHxxMxxS durations and combine with deployment_date
     - return a fully populated RosterAssignment

3. ClockEvent model for Titus → NGRS POST:
   buId: str
   ClockedDateTime: str (YYYYMMDDHHMMSS)
   ClockedDeviceId: str
   ClockedStatus: str ("IN" | "OUT")
   ClockingId: str
   PersonnelId: str
   DeploymentItemId: str
   PlannedStartDateTime: str
   PlannedEndDateTime: str
   RequestId: str
   SendFrom: str (always "titusSimulator")

Include any helper functions for formatting timestamps.

2.4 Roster Client (GET from NGRS)

Prompt:

In `src/titus_simulator/roster_client.py`, implement async `RosterClient` using httpx.AsyncClient.

Constructor: accepts base_url: str and Settings.

Method:
async fetch_roster(from_date: date, to_date: date) -> list[RosterAssignment]

- Send GET to settings.ngrs_roster_url with params:
    from=YYYY-MM-DD
    to=YYYY-MM-DD
- Add Authorization: Bearer <api_key> if provided.
- Parse JSON into the raw envelope model (RawRosterMetadata etc).
- Convert each raw entry using RosterAssignment.from_raw(...)
- Log number of assignments using loguru.

2.5 Clocking Client (POST to NGRS)

Prompt:

In `src/titus_simulator/clocking_client.py`, implement async ClockingClient using httpx.AsyncClient.

Method:
async send_events(events: list[ClockEvent]) -> None

- If events is empty, return.
- POST to settings.ngrs_clocking_url with JSON:
  {
    "source": "titusSimulator",
    "events": [ ... ]
  }
- Log the number of events and the response status.
- Raise an exception on non-2xx responses.

2.6 SQLite State Store

Prompt:

In `src/titus_simulator/state_store.py`, implement SQLite storage using aiosqlite.

DB file: settings.database_path

On init():
- Create table simulated_events if not exists:
  deployment_item_id TEXT
  personnel_id TEXT
  in_sent_at TEXT NULL
  out_sent_at TEXT NULL
  PRIMARY KEY (deployment_item_id, personnel_id)

Class StateStore:
  async init()
  async has_in_sent(deployment_item_id, personnel_id) -> bool
  async has_out_sent(deployment_item_id, personnel_id) -> bool
  async mark_in_sent(deployment_item_id, personnel_id, ts)
  async mark_out_sent(deployment_item_id, personnel_id, ts)

Store timestamps as ISO 8601.

2.7 Simulation Logic

Prompt:

In `src/titus_simulator/simulator.py`, create class TitusSimulator with dependencies:
- RosterClient
- ClockingClient
- StateStore
- Settings

Implement:
plan_events_for_assignment(self, assignment: RosterAssignment) -> list[ClockEvent]
- Use deterministic random seed = deployment_item_id + personnel_id
- IN event:
    planned_start ± random(-5 to +10 min)
- OUT event:
    planned_end ± random(-10 to +15 min)
- Construct ClockEvent:
    ClockedStatus = "IN" or "OUT"
    ClockedDateTime = YYYYMMDDHHMMSS
    ClockedDeviceId = "SIM-10.0.0.5"
    buId = assignment.plant
    PersonnelId = assignment.personnel_id
    DeploymentItemId = assignment.deployment_item_id
    PlannedStartDateTime / PlannedEndDateTime compact timestamps
    ClockingId = uuid4
    RequestId = uuid4
    SendFrom = "titusSimulator"

Implement:
async run_cycle_for_date(self, target_date: date):
  1. Fetch assignments for date
  2. For each assignment:
      - check if IN or OUT already sent via StateStore
      - plan events
      - filter events to only unsent ones
      - send via ClockingClient
      - update StateStore
  3. Log how many were sent.

2.8 Scheduler Integration

Prompt:

In `src/titus_simulator/scheduler.py`, add APScheduler AsyncIOScheduler support.

Function:
setup_scheduler(app: FastAPI, simulator: TitusSimulator, store: StateStore)

- Create AsyncIOScheduler
- Schedule job:
    simulator.run_cycle_for_date(date.today())
  every settings.poll_interval_seconds
- Start scheduler on app startup
- Shutdown scheduler on app shutdown
- Use the same event loop as FastAPI

2.9 FastAPI Application

Prompt:

In `src/titus_simulator/api.py`, build FastAPI service.

app = FastAPI(title="Titus Simulator", version="0.1")

On startup:
- Instantiate Settings, StateStore, RosterClient, ClockingClient, TitusSimulator
- await store.init()
- Save objects in app.state
- Call setup_scheduler(app, simulator, store)

Endpoints:
GET /health:
  return { "status": "ok" }

POST /run-once:
  trigger:
     await simulator.run_cycle_for_date(date.today())
  return summary JSON

2.10 Running the Simulator

Prompt:

Create a `.env` file with:

NGRS_ROSTER_URL=http://localhost:8080/api/integration/titus/roster
NGRS_CLOCKING_URL=http://localhost:8080/api/integration/titus/clocking
NGRS_API_KEY=dev-token
POLL_INTERVAL_SECONDS=60
TIMEZONE=Asia/Singapore
DATABASE_PATH=sim_state.db

Install dependencies:
pip install -e .

Run server:
uvicorn titus_simulator.api:app --host 0.0.0.0 --port 8000

Test:
GET http://localhost:8000/health
POST http://localhost:8000/run-once
