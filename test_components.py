#!/usr/bin/env python3
"""
Simple test script to verify the Titus Simulator components.
Run this to test individual components without starting the full server.
"""

import asyncio
from datetime import date
from zoneinfo import ZoneInfo

from titus_simulator.config import settings
from titus_simulator.models import RawRosterMetadata, RosterAssignment, ClockEvent


async def test_models():
    """Test data model parsing."""
    print("=" * 50)
    print("Testing Data Models")
    print("=" * 50)
    
    # Sample raw data
    raw = RawRosterMetadata(
        PersonnelId="P001",
        personnel_first_name="John",
        personnel_last_name="Doe",
        PersonnelType="Officer",
        PersonnelTypeDescription="Security Officer",
        SecSeqNum="1",
        PrimarySeqNum="1",
        demand_item_id="D001",
        customer_id="C001",
        customer_name="Test Customer",
        deployment_location="Site A",
        deployment_date="/Date(1733097600000)/",  # Dec 2, 2024
        deploymentItm="DEPLOY001",
        planner_group_id="PG001",
        plant="PLANT001",
        planned_start_time="PT8H0M0S",  # 8:00 AM
        planned_end_time="PT17H0M0S",  # 5:00 PM
        demand_type="Regular",
    )
    
    # Parse to assignment
    tz = ZoneInfo(settings.timezone)
    assignment = RosterAssignment.from_raw(raw, tz)
    
    print(f"\nParsed Assignment:")
    print(f"  Personnel: {assignment.first_name} {assignment.last_name} ({assignment.personnel_id})")
    print(f"  Deployment: {assignment.deployment_item_id}")
    print(f"  Date: {assignment.deployment_date}")
    print(f"  Time: {assignment.planned_start} to {assignment.planned_end}")
    print(f"  Location: {assignment.deployment_location}")
    
    # Create clock events
    from datetime import datetime
    now = datetime.now(tz)
    
    in_event = ClockEvent.create_in_event(assignment, now)
    out_event = ClockEvent.create_out_event(assignment, now.replace(hour=17))
    
    print(f"\nGenerated Events:")
    print(f"  IN Event: {in_event.ClockedStatus} at {in_event.ClockedDateTime}")
    print(f"  OUT Event: {out_event.ClockedStatus} at {out_event.ClockedDateTime}")
    
    print("\n✓ Model tests passed!")


async def test_state_store():
    """Test SQLite state store."""
    print("\n" + "=" * 50)
    print("Testing State Store")
    print("=" * 50)
    
    from titus_simulator.state_store import StateStore
    
    # Use test database
    test_settings = settings.model_copy(update={"database_path": "test_state.db"})
    store = StateStore(test_settings)
    
    await store.init()
    print("✓ Database initialized")
    
    # Test marking events
    from datetime import datetime
    deployment_id = "TEST_DEPLOY_001"
    personnel_id = "TEST_PERSON_001"
    now = datetime.now()
    
    # Check initial state
    has_in = await store.has_in_sent(deployment_id, personnel_id)
    has_out = await store.has_out_sent(deployment_id, personnel_id)
    print(f"\nInitial state: IN={has_in}, OUT={has_out}")
    
    # Mark IN sent
    await store.mark_in_sent(deployment_id, personnel_id, now)
    has_in = await store.has_in_sent(deployment_id, personnel_id)
    print(f"After marking IN: IN={has_in}, OUT={has_out}")
    
    # Mark OUT sent
    await store.mark_out_sent(deployment_id, personnel_id, now)
    has_out = await store.has_out_sent(deployment_id, personnel_id)
    print(f"After marking OUT: IN={has_in}, OUT={has_out}")
    
    # Get stats
    stats = await store.get_stats()
    print(f"\nDatabase stats: {stats}")
    
    print("\n✓ State store tests passed!")


async def test_simulator_logic():
    """Test simulator event planning."""
    print("\n" + "=" * 50)
    print("Testing Simulator Logic")
    print("=" * 50)
    
    from titus_simulator.simulator import TitusSimulator
    from titus_simulator.roster_client import RosterClient
    from titus_simulator.clocking_client import ClockingClient
    from titus_simulator.state_store import StateStore
    
    # Create mock components
    roster_client = RosterClient(settings)
    clocking_client = ClockingClient(settings)
    store = StateStore(settings)
    
    simulator = TitusSimulator(
        roster_client=roster_client,
        clocking_client=clocking_client,
        state_store=store,
        settings=settings,
    )
    
    # Create test assignment
    tz = ZoneInfo(settings.timezone)
    from datetime import datetime
    
    assignment = RosterAssignment(
        deployment_item_id="DEPLOY001",
        personnel_id="PERSON001",
        first_name="Jane",
        last_name="Smith",
        plant="PLANT001",
        planner_group_id="PG001",
        demand_item_id="D001",
        customer_id="C001",
        customer_name="Test Customer",
        deployment_location="Site B",
        deployment_date=date.today(),
        planned_start=datetime.now(tz).replace(hour=9, minute=0),
        planned_end=datetime.now(tz).replace(hour=17, minute=30),
    )
    
    # Plan events
    events = simulator.plan_events_for_assignment(assignment)
    
    print(f"\nPlanned {len(events)} events for {assignment.first_name} {assignment.last_name}:")
    for event in events:
        print(f"  - {event.ClockedStatus} at {event.ClockedDateTime}")
    
    # Test determinism (same assignment should generate same events)
    events2 = simulator.plan_events_for_assignment(assignment)
    assert events[0].ClockedDateTime == events2[0].ClockedDateTime
    print("\n✓ Event planning is deterministic")
    
    print("\n✓ Simulator logic tests passed!")


async def main():
    """Run all tests."""
    print("\n" + "=" * 50)
    print("Titus Simulator Component Tests")
    print("=" * 50)
    print(f"\nConfiguration:")
    print(f"  Roster URL: {settings.ngrs_roster_url}")
    print(f"  Clocking URL: {settings.ngrs_clocking_url}")
    print(f"  Timezone: {settings.timezone}")
    print(f"  Poll Interval: {settings.poll_interval_seconds}s")
    print()
    
    try:
        await test_models()
        await test_state_store()
        await test_simulator_logic()
        
        print("\n" + "=" * 50)
        print("✓ All tests passed!")
        print("=" * 50)
        print("\nYou can now start the server with:")
        print("  ./start.sh")
        print("  or")
        print("  uvicorn titus_simulator.api:app --reload")
        print()
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
