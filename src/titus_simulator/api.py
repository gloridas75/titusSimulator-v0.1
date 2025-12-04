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
        Upload confirmation with assignment count
    """
    try:
        roster_data = await request.json()
        
        # Validate it's in NGRS format
        results = roster_data.get("list_item", {}).get("data", {}).get("d", {}).get("results", [])
        
        if not results:
            return {
                "status": "error",
                "message": "No assignments found in roster data",
            }
        
        # Store in app state
        app.state.uploaded_roster = results
        
        logger.info(f"Uploaded roster with {len(results)} assignments")
        
        return {
            "status": "success",
            "message": f"Roster uploaded successfully",
            "assignments_count": len(results),
        }
    
    except Exception as e:
        logger.error(f"Error uploading roster: {e}")
        return {
            "status": "error",
            "message": str(e),
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

