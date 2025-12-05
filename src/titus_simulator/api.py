"""FastAPI application for the Titus Simulator service."""

from contextlib import asynccontextmanager
from datetime import date
from typing import Any

from fastapi import FastAPI, Request
from loguru import logger

from .clocking_client import ClockingClient
from .config import settings
from .roster_client import RosterClient
from .scheduler import setup_scheduler
from .simulator import TitusSimulator
from .state_store import StateStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Initializing Titus Simulator")
    
    # Create components
    state_store = StateStore(settings)
    await state_store.init()
    
    roster_client = RosterClient(settings)
    clocking_client = ClockingClient(settings)
    
    simulator = TitusSimulator(
        roster_client=roster_client,
        clocking_client=clocking_client,
        state_store=state_store,
        settings=settings,
    )
    
    # Store in app state for endpoint access
    app.state.simulator = simulator
    app.state.state_store = state_store
    
    # Set up and start scheduler
    scheduler = setup_scheduler(app, simulator, state_store, settings)
    
    logger.info("Titus Simulator initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Titus Simulator")


app = FastAPI(
    title="Titus Simulator",
    version="0.1.0",
    description="A time-attendance simulation service for NGRS backend",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Status information
    """
    return {
        "status": "ok",
        "service": "titus-simulator",
        "version": "0.1.0",
    }


@app.post("/run-once")
async def run_once():
    """
    Manually trigger a simulation cycle for today.
    
    Returns:
        Summary of the simulation run
    """
    logger.info("Manual simulation cycle triggered")
    
    simulator: TitusSimulator = app.state.simulator
    today = date.today()
    
    result = await simulator.run_cycle_for_date(today)
    
    return {
        "status": "completed",
        "result": result,
    }


@app.get("/stats")
async def get_stats():
    """
    Get statistics about simulated events.
    
    Returns:
        Event statistics from the database
    """
    state_store: StateStore = app.state.state_store
    stats = await state_store.get_stats()
    
    return {
        "status": "ok",
        "stats": stats,
    }


@app.post("/upload-roster")
async def upload_roster(request: Request):
    """
    Upload roster JSON data for file-based simulation.
    
    Accepts NGRS roster format and stores it for processing.
    
    Returns:
        Upload confirmation with RosterFileId and RequestId for each PersonnelId
    """
    try:
        import json
        import uuid
        
        roster_data = await request.json()
        
        # Validate it's in NGRS format
        results = roster_data.get("list_item", {}).get("data", {}).get("d", {}).get("results", [])
        
        if not results:
            return {
                "success": False,
                "message": "No assignments found in roster data",
                "results": []
            }
        
        # Generate unique RosterFileId
        roster_file_id = str(uuid.uuid4())
        
        # Store roster in database
        state_store: StateStore = app.state.state_store
        await state_store.store_roster_file(
            roster_file_id=roster_file_id,
            roster_data=json.dumps(roster_data),
            assignments_count=len(results)
        )
        
        # Generate RequestId for each PersonnelId
        request_results = []
        for item in results:
            metadata = item.get("__metadata", {})
            personnel_id = metadata.get("PersonnelId", "UNKNOWN")
            request_id = str(uuid.uuid4())
            request_results.append({
                "PersonnelId": personnel_id,
                "RequestId": request_id
            })
        
        # Log the roster upload
        await state_store.log_roster_upload(
            assignments_count=len(results),
            source="File Upload",
            roster_data=json.dumps(roster_data)
        )
        
        logger.info(f"Uploaded roster with {len(results)} assignments (RosterFileId: {roster_file_id})")
        
        return {
            "success": True,
            "roster_file_id": roster_file_id,
            "results": request_results
        }
    
    except Exception as e:
        logger.error(f"Error uploading roster: {e}")
        return {
            "success": False,
            "message": str(e),
            "results": []
        }


@app.get("/roster")
async def get_roster(rosterFileId: str = None):
    """
    Get roster data by RosterFileId.
    
    Args:
        rosterFileId: UUID of the roster file (optional, returns most recent if not provided)
    
    Returns:
        Roster data with metadata
    """
    import json
    
    state_store: StateStore = app.state.state_store
    
    if rosterFileId:
        # Get specific roster
        roster_file = await state_store.get_roster_file(rosterFileId)
        if not roster_file:
            return {
                "status": "error",
                "message": f"Roster file {rosterFileId} not found"
            }
        
        roster_data = json.loads(roster_file["roster_data"])
        results = roster_data.get("list_item", {}).get("data", {}).get("d", {}).get("results", [])
        
        return {
            "status": "ok",
            "roster_file_id": roster_file["roster_file_id"],
            "uploaded_at": roster_file["uploaded_at"],
            "assignments_count": roster_file["assignments_count"],
            "roster_status": roster_file["status"],
            "roster": results,
        }
    else:
        # Return message that rosterFileId is required
        return {
            "status": "ok",
            "message": "Provide rosterFileId parameter to retrieve specific roster",
            "roster": []
        }


@app.get("/roster-logs")
async def get_roster_logs():
    """
    Get recent roster upload logs.
    
    Returns:
        List of recent roster uploads with timestamps and counts
    """
    state_store: StateStore = app.state.state_store
    logs = await state_store.get_roster_logs(limit=50)
    
    return {
        "status": "ok",
        "logs": logs,
    }


@app.post("/run-from-file")
async def run_from_file(mode: str = "realtime", rosterFileId: str = None):
    """
    Run simulation using uploaded roster file instead of API.
    
    Supports two modes:
    - "immediate": Generate all events, post immediately, cleanup database
    - "realtime": Generate events based on actual shift timing (default)
    
    Args:
        mode: Simulation mode ("immediate" or "realtime")
        rosterFileId: UUID of the roster file to process (required)
    
    Uses the roster data stored in database via /upload-roster endpoint.
    
    Returns:
        Summary of the simulation run with roster_file_id
    """
    import json
    from .simulation_mode import SimulationMode
    
    # Validate rosterFileId required
    if not rosterFileId:
        return {
            "status": "error",
            "message": "rosterFileId parameter is required",
        }
    
    # Validate mode
    try:
        sim_mode = SimulationMode(mode.lower())
    except ValueError:
        return {
            "status": "error",
            "message": f"Invalid mode '{mode}'. Must be 'immediate' or 'realtime'.",
        }
    
    logger.info(f"File-based simulation triggered with mode: {sim_mode.value}, rosterFileId: {rosterFileId}")
    
    # Fetch roster from database
    state_store: StateStore = app.state.state_store
    roster_file = await state_store.get_roster_file(rosterFileId)
    
    if not roster_file:
        return {
            "status": "error",
            "message": f"Roster file {rosterFileId} not found",
        }
    
    # Update status to processing
    await state_store.update_roster_file_status(rosterFileId, "processing")
    
    simulator: TitusSimulator = app.state.simulator
    
    try:
        # Parse roster data
        roster_data = json.loads(roster_file["roster_data"])
        results = roster_data.get("list_item", {}).get("data", {}).get("d", {}).get("results", [])
        
        # Run simulation
        if sim_mode == SimulationMode.IMMEDIATE:
            result = await simulator.run_immediate_mode(results)
        else:  # REALTIME
            result = await simulator.run_realtime_mode(results)
        
        # Update status to completed
        await state_store.update_roster_file_status(rosterFileId, "completed")
        
        return {
            "status": "completed",
            "roster_file_id": rosterFileId,
            "result": result,
        }
    
    except Exception as e:
        logger.error(f"Error in file-based simulation: {e}")
        # Update status to failed
        await state_store.update_roster_file_status(rosterFileId, "failed")
        return {
            "status": "error",
            "message": str(e),
        }



@app.get("/roster")
async def get_roster():
    """
    Get the currently uploaded roster data.
    
    Returns:
        Current roster assignments or empty list if none uploaded
    """
    roster = app.state.uploaded_roster or []
    
    return {
        "status": "ok",
        "count": len(roster),
        "roster": roster,
    }


@app.get("/roster-logs")
async def get_roster_logs():
    """
    Get recent roster upload logs.
    
    Returns:
        List of recent roster uploads with timestamps and counts
    """
    state_store: StateStore = app.state.state_store
    logs = await state_store.get_roster_logs(limit=50)
    
    return {
        "status": "ok",
        "logs": logs,
    }
