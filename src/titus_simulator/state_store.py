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
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS roster_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uploaded_at TEXT NOT NULL,
                    assignments_count INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    roster_data TEXT NOT NULL
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS roster_files (
                    roster_file_id TEXT PRIMARY KEY,
                    uploaded_at TEXT NOT NULL,
                    assignments_count INTEGER NOT NULL,
                    roster_data TEXT NOT NULL,
                    status TEXT DEFAULT 'pending'
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


    async def log_roster_upload(
        self, assignments_count: int, source: str, roster_data: str
    ) -> None:
        """
        Log a roster upload.
        
        Args:
            assignments_count: Number of assignments in roster
            source: Source of the roster (e.g., "NGRS", "File Upload")
            roster_data: JSON string of roster data
        """
        timestamp = datetime.now().isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO roster_logs (uploaded_at, assignments_count, source, roster_data)
                VALUES (?, ?, ?, ?)
                """,
                (timestamp, assignments_count, source, roster_data),
            )
            await db.commit()
        
        logger.info(f"Logged roster upload: {assignments_count} assignments from {source}")
    
    async def get_roster_logs(self, limit: int = 50) -> list[dict]:
        """
        Get recent roster upload logs.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of roster log entries
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, uploaded_at, assignments_count, source
                FROM roster_logs
                ORDER BY uploaded_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = await cursor.fetchall()
            
            return [
                {
                    "id": row[0],
                    "uploaded_at": row[1],
                    "assignments_count": row[2],
                    "source": row[3],
                }
                for row in rows
            ]
    
    async def cleanup_posted_events(
        self, deployment_ids: list[tuple[str, str]]
    ) -> int:
        """
        Delete specific events that were successfully posted (immediate mode).
        
        Args:
            deployment_ids: List of (deployment_item_id, personnel_id) tuples
            
        Returns:
            Number of records deleted
        """
        if not deployment_ids:
            return 0
            
        async with aiosqlite.connect(self.db_path) as db:
            deleted = 0
            for deployment_id, personnel_id in deployment_ids:
                await db.execute(
                    """
                    DELETE FROM simulated_events
                    WHERE deployment_item_id = ? AND personnel_id = ?
                    """,
                    (deployment_id, personnel_id),
                )
                deleted += 1
            await db.commit()
        
        logger.info(f"Cleaned up {deleted} posted event records")
        return deleted
    
    async def cleanup_old_events(self, days_to_keep: int = 2) -> int:
        """
        Delete events older than specified days (realtime mode).
        
        Args:
            days_to_keep: Number of days to keep (default: 2)
            
        Returns:
            Number of records deleted
        """
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Delete events where both IN and OUT are older than cutoff
            cursor = await db.execute(
                """
                DELETE FROM simulated_events
                WHERE (in_sent_at < ? OR in_sent_at IS NULL)
                  AND (out_sent_at < ? OR out_sent_at IS NULL)
                RETURNING deployment_item_id
                """,
                (cutoff_str, cutoff_str),
            )
            rows = await cursor.fetchall()
            deleted = len(rows)
            await db.commit()
        
        logger.info(f"Cleaned up {deleted} old event records (older than {days_to_keep} days)")
        return deleted
    
    async def store_roster_file(
        self, roster_file_id: str, roster_data: str, assignments_count: int
    ) -> None:
        """
        Store a roster file in the database.
        
        Args:
            roster_file_id: UUID for the roster file
            roster_data: JSON string of roster data
            assignments_count: Number of assignments in roster
        """
        timestamp = datetime.now().isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO roster_files (roster_file_id, uploaded_at, assignments_count, roster_data, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (roster_file_id, timestamp, assignments_count, roster_data, "pending"),
            )
            await db.commit()
        
        logger.info(f"Stored roster file {roster_file_id} with {assignments_count} assignments")
    
    async def get_roster_file(self, roster_file_id: str) -> dict | None:
        """
        Retrieve a roster file from the database.
        
        Args:
            roster_file_id: UUID of the roster file
            
        Returns:
            Dictionary with roster data or None if not found
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT roster_file_id, uploaded_at, assignments_count, roster_data, status
                FROM roster_files
                WHERE roster_file_id = ?
                """,
                (roster_file_id,),
            )
            row = await cursor.fetchone()
            
            if row:
                return {
                    "roster_file_id": row[0],
                    "uploaded_at": row[1],
                    "assignments_count": row[2],
                    "roster_data": row[3],
                    "status": row[4],
                }
            return None
    
    async def update_roster_file_status(
        self, roster_file_id: str, status: str
    ) -> None:
        """
        Update the status of a roster file.
        
        Args:
            roster_file_id: UUID of the roster file
            status: New status (pending, processing, completed, failed)
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE roster_files
                SET status = ?
                WHERE roster_file_id = ?
                """,
                (status, roster_file_id),
            )
            await db.commit()
        
        logger.info(f"Updated roster file {roster_file_id} status to {status}")
    
    async def cleanup_old_roster_files(self, days_to_keep: int = 7) -> int:
        """
        Delete roster files older than specified days.
        
        Args:
            days_to_keep: Number of days to keep (default: 7)
            
        Returns:
            Number of files deleted
        """
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                DELETE FROM roster_files
                WHERE uploaded_at < ?
                RETURNING roster_file_id
                """,
                (cutoff_str,),
            )
            rows = await cursor.fetchall()
            deleted = len(rows)
            await db.commit()
        
        logger.info(f"Cleaned up {deleted} old roster files (older than {days_to_keep} days)")
        return deleted
