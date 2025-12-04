"""Simulation mode definitions."""

from enum import Enum


class SimulationMode(str, Enum):
    """Simulation execution modes."""
    
    IMMEDIATE = "immediate"  # Batch mode: Generate all events and post immediately
    REALTIME = "realtime"    # Time-based mode: Generate events based on actual shift timing
