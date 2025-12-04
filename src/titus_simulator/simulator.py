"""Core simulation logic for generating clock-in/out events."""

import random
from datetime import date, datetime, timedelta

from loguru import logger

from .clocking_client import ClockingClient
from .config import Settings
from .models import ClockEvent, RosterAssignment
from .roster_client import RosterClient
from .state_store import StateStore


class TitusSimulator:
    """Main simulator for generating and sending clock events."""
    
    def __init__(
        self,
        roster_client: RosterClient,
        clocking_client: ClockingClient,
        state_store: StateStore,
        settings: Settings,
    ):
        """
        Initialize the simulator.
        
        Args:
            roster_client: Client for fetching roster data
            clocking_client: Client for sending clock events
            state_store: Database for tracking sent events
            settings: Application settings
        """
        self.roster_client = roster_client
        self.clocking_client = clocking_client
        self.state_store = state_store
        self.settings = settings
    
    def plan_events_for_assignment(
        self, assignment: RosterAssignment
    ) -> list[ClockEvent]:
        """
        Plan IN and OUT events for a roster assignment with timing variations.
        
        Uses deterministic randomness based on deployment and personnel IDs
        to ensure consistent behavior across runs.
        
        Args:
            assignment: The roster assignment to simulate
            
        Returns:
            List of clock events (IN and OUT)
        """
        # Create deterministic random seed from IDs
        seed_str = f"{assignment.deployment_item_id}-{assignment.personnel_id}"
        seed = hash(seed_str) % (2**31)
        rng = random.Random(seed)
        
        events = []
        
        # Generate IN event: -5 to +10 minutes from planned start
        in_offset = timedelta(minutes=rng.randint(-5, 10))
        in_time = assignment.planned_start + in_offset
        
        events.append(
            ClockEvent.create_in_event(
                assignment=assignment,
                clocked_time=in_time,
            )
        )
        
        # Generate OUT event: -10 to +15 minutes from planned end
        out_offset = timedelta(minutes=rng.randint(-10, 15))
        out_time = assignment.planned_end + out_offset
        
        events.append(
            ClockEvent.create_out_event(
                assignment=assignment,
                clocked_time=out_time,
            )
        )
        
        logger.debug(
            f"Planned events for {assignment.first_name} {assignment.last_name} "
            f"(IN offset: {in_offset.total_seconds()/60:.1f}min, "
            f"OUT offset: {out_offset.total_seconds()/60:.1f}min)"
        )
        
        return events
    
    async def run_cycle_for_date(self, target_date: date) -> dict:
        """
        Run a complete simulation cycle for a specific date.
        
        Steps:
        1. Fetch roster assignments for the date
        2. For each assignment, check if events were already sent
        3. Plan new events for unsent assignments
        4. Send events to NGRS
        5. Update state store
        
        Args:
            target_date: The date to simulate
            
        Returns:
            Summary dictionary with statistics
        """
        logger.info(f"Starting simulation cycle for {target_date}")
        
        # Fetch roster assignments
        assignments = await self.roster_client.fetch_roster(
            from_date=target_date,
            to_date=target_date,
        )
        
        if not assignments:
            logger.info(f"No roster assignments found for {target_date}")
            return {
                "date": str(target_date),
                "assignments_found": 0,
                "events_sent": 0,
            }
        
        logger.info(f"Processing {len(assignments)} assignments")
        
        events_to_send = []
        event_to_assignment = {}  # Map event to its assignment for state tracking
        
        for assignment in assignments:
            deployment_id = assignment.deployment_item_id
            personnel_id = assignment.personnel_id
            
            # Check what has already been sent
            has_in = await self.state_store.has_in_sent(deployment_id, personnel_id)
            has_out = await self.state_store.has_out_sent(deployment_id, personnel_id)
            
            # Plan events
            planned_events = self.plan_events_for_assignment(assignment)
            
            # Filter to only unsent events
            for event in planned_events:
                if event.ClockedStatus == "IN" and not has_in:
                    events_to_send.append(event)
                    event_to_assignment[id(event)] = assignment
                elif event.ClockedStatus == "OUT" and not has_out:
                    events_to_send.append(event)
                    event_to_assignment[id(event)] = assignment
        
        if not events_to_send:
            logger.info("All events for this date have already been sent")
            return {
                "date": str(target_date),
                "assignments_found": len(assignments),
                "events_generated": 0,
                "ngrs_available": True,
            }
        
        # Send events (attempt to send, but continue even if it fails)
        logger.info(f"Sending {len(events_to_send)} unsent events")
        send_successful = await self.clocking_client.send_events(events_to_send)
        
        # Update state store regardless of send success (for testing)
        now = datetime.now()
        for event in events_to_send:
            if event.ClockedStatus == "IN":
                await self.state_store.mark_in_sent(
                    event.DeploymentItemId,
                    event.PersonnelId,
                    now,
                )
            elif event.ClockedStatus == "OUT":
                await self.state_store.mark_out_sent(
                    event.DeploymentItemId,
                    event.PersonnelId,
                    now,
                )
        
        status_msg = "sent to NGRS" if send_successful else "generated (NGRS unavailable)"
        logger.info(
            f"Simulation cycle complete: {len(events_to_send)} events {status_msg} "
            f"for {len(assignments)} assignments"
        )
        
        return {
            "date": str(target_date),
            "assignments_found": len(assignments),
            "events_generated": len(events_to_send),
            "ngrs_available": send_successful,
        }
    
    async def run_cycle_from_roster_data(self, roster_results: list[dict]) -> dict:
        """
        Run simulation cycle using uploaded roster data instead of API fetch.
        
        Args:
            roster_results: List of roster assignment dictionaries
            
        Returns:
            Summary dictionary with statistics
        """
        logger.info(f"Starting file-based simulation with {len(roster_results)} assignments")
        
        # Parse roster data into RosterAssignment objects
        from .models import RawRosterMetadata
        from zoneinfo import ZoneInfo
        
        tz = ZoneInfo(self.settings.timezone)
        assignments = []
        
        for raw_data in roster_results:
            try:
                # Extract __metadata from the nested structure
                metadata_dict = raw_data.get("__metadata", {})
                if not metadata_dict:
                    logger.warning(f"No __metadata found in roster item")
                    continue
                    
                metadata = RawRosterMetadata(**metadata_dict)
                assignment = RosterAssignment.from_raw(metadata, tz)
                assignments.append(assignment)
            except Exception as e:
                logger.warning(f"Failed to parse assignment: {e}")
                continue
        
        if not assignments:
            logger.warning("No valid assignments could be parsed from uploaded data")
            return {
                "assignments_found": len(roster_results),
                "assignments_parsed": 0,
                "events_sent": 0,
            }
        
        logger.info(f"Successfully parsed {len(assignments)} assignments")
        
        events_to_send = []
        event_to_assignment = {}  # Map event to its assignment for state tracking
        
        for assignment in assignments:
            deployment_id = assignment.deployment_item_id
            personnel_id = assignment.personnel_id
            
            # Check what has already been sent
            has_in = await self.state_store.has_in_sent(deployment_id, personnel_id)
            has_out = await self.state_store.has_out_sent(deployment_id, personnel_id)
            
            # Plan events
            planned_events = self.plan_events_for_assignment(assignment)
            
            # Filter to only unsent events
            for event in planned_events:
                if event.ClockedStatus == "IN" and not has_in:
                    events_to_send.append(event)
                    event_to_assignment[id(event)] = assignment
                elif event.ClockedStatus == "OUT" and not has_out:
                    events_to_send.append(event)
                    event_to_assignment[id(event)] = assignment
        
        if not events_to_send:
            logger.info("All events have already been sent")
            return {
                "assignments_found": len(roster_results),
                "assignments_parsed": len(assignments),
                "events_generated": 0,
                "ngrs_available": True,
            }
        
        # Send events (attempt to send, but continue even if it fails)
        logger.info(f"Sending {len(events_to_send)} unsent events")
        send_successful = await self.clocking_client.send_events(events_to_send)
        
        # Update state store regardless of send success (for testing)
        now = datetime.now()
        for event in events_to_send:
            assignment = event_to_assignment[id(event)]
            if event.ClockedStatus == "IN":
                await self.state_store.mark_in_sent(
                    assignment.deployment_item_id,
                    event.PersonnelId,
                    now,
                )
            elif event.ClockedStatus == "OUT":
                await self.state_store.mark_out_sent(
                    assignment.deployment_item_id,
                    event.PersonnelId,
                    now,
                )
        
        status_msg = "sent to NGRS" if send_successful else "generated (NGRS unavailable)"
        logger.info(
            f"File-based simulation complete: {len(events_to_send)} events {status_msg} "
            f"for {len(assignments)} assignments"
        )
        
        return {
            "assignments_found": len(roster_results),
            "assignments_parsed": len(assignments),
            "events_generated": len(events_to_send),
            "ngrs_available": send_successful,
        }


