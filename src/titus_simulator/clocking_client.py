"""Client for sending simulated clocking events to NGRS."""

import httpx
from loguru import logger

from .config import Settings
from .models import ClockEvent


class ClockingClient:
    """Client for sending clock events to NGRS API."""
    
    def __init__(self, settings: Settings):
        """
        Initialize the clocking client.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.url = settings.ngrs_clocking_url
    
    async def send_events(self, events: list[ClockEvent]) -> None:
        """
        Send clocking events to NGRS.
        
        Args:
            events: List of clock events to send
            
        Raises:
            httpx.HTTPStatusError: If the API returns an error status
        """
        if not events:
            logger.debug("No events to send")
            return
        
        headers = {"Content-Type": "application/json"}
        if self.settings.ngrs_api_key:
            headers["x-api-key"] = self.settings.ngrs_api_key
        
        logger.info(f"Sending {len(events)} clock events to NGRS at {self.url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Send each event individually
            success_count = 0
            for event in events:
                try:
                    response = await client.post(
                        self.url,
                        json=event.model_dump(),
                        headers=headers,
                    )
                    response.raise_for_status()
                    success_count += 1
                    logger.debug(f"Event {event.ClockingId} sent successfully")
                    
                except httpx.HTTPStatusError as e:
                    logger.error(
                        f"HTTP error sending event {event.ClockingId}: {e.response.status_code} - "
                        f"{e.response.text}"
                    )
                except httpx.ConnectError as e:
                    logger.warning(
                        f"NGRS API not available (Connection refused). "
                        f"Events generated but not sent. This is normal for testing without NGRS running."
                    )
                    return False
                except Exception as e:
                    logger.error(f"Error sending event {event.ClockingId}: {e}")
            
            if success_count == len(events):
                logger.info(f"Successfully sent all {success_count} events to {self.url}")
                return True
            elif success_count > 0:
                logger.warning(f"Partially sent {success_count}/{len(events)} events")
                return False
            else:
                return False

