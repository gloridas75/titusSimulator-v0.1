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
    app.state.uploaded_roster = None  # For file-based simulation
    
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
        Upload confirmation with RequestId for each PersonnelId
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
        
        # Store in app state
        app.state.uploaded_roster = results
        
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
        state_store: StateStore = app.state.state_store
        await state_store.log_roster_upload(
            assignments_count=len(results),
            source="File Upload",
            roster_data=json.dumps(roster_data)
        )
        
        logger.info(f"Uploaded roster with {len(results)} assignments")
        
        return {
            "success": True,
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


@app.post("/run-from-file")
async def run_from_file():
    """
    Run simulation using uploaded roster file instead of API.
    
    Uses the roster data uploaded via /upload-roster endpoint.
    
    Returns:
        Summary of the simulation run
    """
    logger.info("File-based simulation triggered")
    
    if not app.state.uploaded_roster:
        return {
            "status": "error",
            "message": "No roster file uploaded. Please upload a roster first.",
        }
    
    simulator: TitusSimulator = app.state.simulator
    
    try:
        result = await simulator.run_cycle_from_roster_data(app.state.uploaded_roster)
        
        return {
            "status": "completed",
            "result": result,
        }
    
    except Exception as e:
        logger.error(f"Error in file-based simulation: {e}")
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
