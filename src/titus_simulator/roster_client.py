"""Client for fetching roster assignments from NGRS."""

from datetime import date
from zoneinfo import ZoneInfo

import httpx
from loguru import logger

from .config import Settings
from .models import RosterAssignment, RawRosterEnvelope


class RosterClient:
    """Client for fetching roster data from NGRS API."""
    
    def __init__(self, settings: Settings):
        """
        Initialize the roster client.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.base_url = settings.ngrs_roster_url or ""  # Optional - NGRS now POSTs directly
        self.tz = ZoneInfo(settings.timezone)
        
    async def fetch_roster(
        self, from_date: date, to_date: date
    ) -> list[RosterAssignment]:
        """
        Fetch roster assignments for a date range.
        
        Args:
            from_date: Start date (inclusive)
            to_date: End date (inclusive)
            
        Returns:
            List of parsed roster assignments
        """
        params = {
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
        }
        
        headers = {}
        if self.settings.ngrs_api_key:
            headers["Authorization"] = f"Bearer {self.settings.ngrs_api_key}"
        
        logger.info(f"Fetching roster from {from_date} to {to_date}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                
                # Parse the response
                data = response.json()
                
                # Handle different response formats
                assignments = []
                
                # Check if response is the envelope format
                if isinstance(data, dict) and "FunctionName" in data:
                    envelope = RawRosterEnvelope(**data)
                    raw_results = envelope.get_results()
                    assignments = [
                        RosterAssignment.from_raw(raw, self.tz)
                        for raw in raw_results
                    ]
                # Check if response has direct list_item format
                elif isinstance(data, dict) and "list_item" in data:
                    envelope = RawRosterEnvelope(**data)
                    raw_results = envelope.get_results()
                    assignments = [
                        RosterAssignment.from_raw(raw, self.tz)
                        for raw in raw_results
                    ]
                # Handle direct array response
                elif isinstance(data, list):
                    from .models import RawRosterMetadata
                    assignments = [
                        RosterAssignment.from_raw(RawRosterMetadata(**item), self.tz)
                        for item in data
                    ]
                else:
                    logger.warning(f"Unexpected response format: {type(data)}")
                
                logger.info(f"Fetched {len(assignments)} roster assignments")
                return assignments
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error fetching roster: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Error fetching roster: {e}")
                raise

