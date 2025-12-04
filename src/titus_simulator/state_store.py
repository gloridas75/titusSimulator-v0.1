"""SQLite-based state store for tracking sent events."""

from datetime import datetime

import aiosqlite
from loguru import logger

from .config import Settings


class StateStore:
    """SQLite database for tracking simulated events."""
    
    def __init__(self, settings: Settings):
        """
        Initialize the state store.
        
        Args:
            settings: Application settings
        """
        self.db_path = settings.database_path
    
    async def init(self) -> None:
        """Initialize the database and create tables if needed."""
        logger.info(f"Initializing state store at {self.db_path}")
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS simulated_events (
                    deployment_item_id TEXT NOT NULL,
                    personnel_id TEXT NOT NULL,
                    in_sent_at TEXT NULL,
                    out_sent_at TEXT NULL,
                    PRIMARY KEY (deployment_item_id, personnel_id)
                )
            """)
            await db.commit()
        
        logger.info("State store initialized")
    
    async def has_in_sent(
        self, deployment_item_id: str, personnel_id: str
    ) -> bool:
        """
        Check if an IN event has been sent for this assignment.
        
        Args:
            deployment_item_id: Deployment item ID
            personnel_id: Personnel ID
            
        Returns:
            True if IN event was already sent
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT in_sent_at FROM simulated_events
                WHERE deployment_item_id = ? AND personnel_id = ?
                """,
                (deployment_item_id, personnel_id),
            )
            row = await cursor.fetchone()
            return row is not None and row[0] is not None
    
    async def has_out_sent(
        self, deployment_item_id: str, personnel_id: str
    ) -> bool:
        """
        Check if an OUT event has been sent for this assignment.
        
        Args:
            deployment_item_id: Deployment item ID
            personnel_id: Personnel ID
            
        Returns:
            True if OUT event was already sent
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT out_sent_at FROM simulated_events
                WHERE deployment_item_id = ? AND personnel_id = ?
                """,
                (deployment_item_id, personnel_id),
            )
            row = await cursor.fetchone()
            return row is not None and row[0] is not None
    
    async def mark_in_sent(
        self, deployment_item_id: str, personnel_id: str, timestamp: datetime
    ) -> None:
        """
        Mark that an IN event was sent.
        
        Args:
            deployment_item_id: Deployment item ID
            personnel_id: Personnel ID
            timestamp: When the event was sent
        """
        ts_str = timestamp.isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO simulated_events 
                    (deployment_item_id, personnel_id, in_sent_at)
                VALUES (?, ?, ?)
                ON CONFLICT(deployment_item_id, personnel_id)
                DO UPDATE SET in_sent_at = excluded.in_sent_at
                """,
                (deployment_item_id, personnel_id, ts_str),
            )
            await db.commit()
        
        logger.debug(
            f"Marked IN sent for deployment={deployment_item_id}, "
            f"personnel={personnel_id}"
        )
    
    async def mark_out_sent(
        self, deployment_item_id: str, personnel_id: str, timestamp: datetime
    ) -> None:
        """
        Mark that an OUT event was sent.
        
        Args:
            deployment_item_id: Deployment item ID
            personnel_id: Personnel ID
            timestamp: When the event was sent
        """
        ts_str = timestamp.isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO simulated_events 
                    (deployment_item_id, personnel_id, out_sent_at)
                VALUES (?, ?, ?)
                ON CONFLICT(deployment_item_id, personnel_id)
                DO UPDATE SET out_sent_at = excluded.out_sent_at
                """,
                (deployment_item_id, personnel_id, ts_str),
            )
            await db.commit()
        
        logger.debug(
            f"Marked OUT sent for deployment={deployment_item_id}, "
            f"personnel={personnel_id}"
        )
    
    async def get_stats(self) -> dict:
        """
        Get statistics about simulated events.
        
        Returns:
            Dictionary with event statistics
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN in_sent_at IS NOT NULL THEN 1 ELSE 0 END) as in_count,
                    SUM(CASE WHEN out_sent_at IS NOT NULL THEN 1 ELSE 0 END) as out_count
                FROM simulated_events
                """
            )
            row = await cursor.fetchone()
            
            if row:
                return {
                    "total_assignments": row[0],
                    "in_events_sent": row[1],
                    "out_events_sent": row[2],
                }
            return {
                "total_assignments": 0,
                "in_events_sent": 0,
                "out_events_sent": 0,
            }

