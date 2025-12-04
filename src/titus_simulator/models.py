"""Data models for roster assignments and clocking events."""

import re
from datetime import date, datetime, timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator


class RawRosterMetadata(BaseModel):
    """Raw roster metadata from NGRS API response - nested under __metadata."""
    
    PersonnelId: str
    personnel_first_name: str
    personnel_last_name: str
    PersonnelType: str
    PersonnelTypeDescription: str
    SecSeqNum: str  # "01", "02", "03" - number of shift splits
    PrimarySeqNum: str  # "001" to "010" - sequence for multiple officers on same shift
    demand_item_id: str
    customer_id: str
    customer_name: str
    deployment_location: str
    deployment_date: str  # Format: "/Date(1755216000000)/"
    deploymentItm: str  # Unique identifier per shift per day
    planner_group_id: str
    plant: str
    planned_start_time: str  # Format: "PT10H15M00S"
    planned_end_time: str  # Format: "PT19H15M00S"
    demand_type: str


class RawRosterResult(BaseModel):
    """Wrapper for result item containing __metadata."""
    
    metadata: RawRosterMetadata = Field(alias="__metadata")
    
    class Config:
        populate_by_name = True


class RawRosterSummary(BaseModel):
    """Summary metadata for deployment items."""
    
    deployment_item: str
    totalQty: int
    changedTime: int  # Format: YYYYMMDDHHMMSS


class RawRosterSummaryItem(BaseModel):
    """Wrapper for summary item containing __metadata."""
    
    metadata: RawRosterSummary = Field(alias="__metadata")
    
    class Config:
        populate_by_name = True


class RawRosterData(BaseModel):
    """Wrapper for the raw roster data response."""
    
    results: list[RawRosterResult]
    summary: list[RawRosterSummaryItem] = Field(default_factory=list)


class RawRosterEnvelope(BaseModel):
    """Top-level envelope for NGRS roster API response."""
    
    FunctionName: str
    list_item: dict[str, Any]
    
    def get_results(self) -> list[RawRosterMetadata]:
        """Extract results from nested structure."""
        data = self.list_item.get("data", {})
        d = data.get("d", {})
        results = d.get("results", [])
        # Extract __metadata from each result item
        return [RawRosterMetadata(**item.get("__metadata", {})) for item in results if "__metadata" in item]


class RosterAssignment(BaseModel):
    """Flattened and parsed roster assignment."""
    
    deployment_item_id: str
    personnel_id: str
    first_name: str
    last_name: str
    plant: str
    planner_group_id: str
    demand_item_id: str
    customer_id: str
    customer_name: str
    deployment_location: str
    deployment_date: date
    planned_start: datetime
    planned_end: datetime
    
    @classmethod
    def from_raw(cls, raw: RawRosterMetadata, tz: ZoneInfo) -> "RosterAssignment":
        """
        Convert raw roster metadata to a parsed assignment.
        
        Args:
            raw: Raw metadata from NGRS
            tz: Timezone for localization
            
        Returns:
            Parsed RosterAssignment
        """
        # Parse deployment date from /Date(milliseconds)/ format
        deployment_dt = cls._parse_date_milliseconds(raw.deployment_date)
        
        # Parse duration strings and combine with date
        planned_start = cls._combine_date_and_duration(deployment_dt, raw.planned_start_time, tz)
        planned_end = cls._combine_date_and_duration(deployment_dt, raw.planned_end_time, tz)
        
        return cls(
            deployment_item_id=raw.deploymentItm,
            personnel_id=raw.PersonnelId,
            first_name=raw.personnel_first_name,
            last_name=raw.personnel_last_name,
            plant=raw.plant,
            planner_group_id=raw.planner_group_id,
            demand_item_id=raw.demand_item_id,
            customer_id=raw.customer_id,
            customer_name=raw.customer_name,
            deployment_location=raw.deployment_location,
            deployment_date=deployment_dt.date(),
            planned_start=planned_start,
            planned_end=planned_end,
        )
    
    @staticmethod
    def _parse_date_milliseconds(date_str: str) -> datetime:
        """Parse /Date(milliseconds)/ format."""
        match = re.search(r"/Date\((\d+)\)/", date_str)
        if not match:
            raise ValueError(f"Invalid date format: {date_str}")
        
        milliseconds = int(match.group(1))
        return datetime.fromtimestamp(milliseconds / 1000.0, tz=ZoneInfo("UTC"))
    
    @staticmethod
    def _parse_duration(duration_str: str) -> timedelta:
        """Parse PT10H15M00S format into timedelta."""
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", duration_str)
        if not match:
            raise ValueError(f"Invalid duration format: {duration_str}")
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = float(match.group(3) or 0)
        
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    
    @classmethod
    def _combine_date_and_duration(
        cls, base_date: datetime, duration_str: str, tz: ZoneInfo
    ) -> datetime:
        """Combine a date with a duration offset and localize to timezone."""
        duration = cls._parse_duration(duration_str)
        # Start from midnight of the deployment date in the target timezone
        base_midnight = datetime(
            base_date.year, base_date.month, base_date.day,
            tzinfo=tz
        )
        return base_midnight + duration


class ClockEvent(BaseModel):
    """Clocking event to send to NGRS."""
    
    BuWerks: str = Field(..., max_length=4)  # Max length: 4
    ClockedDateTime: str = Field(..., max_length=14)  # Format: YYYYMMDDHHMMSS, Max length: 14
    ClockedDeviceId: str = Field(..., max_length=15)  # Max length: 15
    ClockedStatus: str = Field(..., max_length=3)  # "IN" or "OUT", Max length: 3
    ClockingId: str = Field(..., max_length=40)  # Max length: 40
    PersonnelId: str = Field(..., max_length=8)  # Max length: 8
    RequestId: str = Field(..., max_length=40)  # Max length: 40
    SendFrom: str = Field(default="titusSimulator", max_length=15)  # Max length: 15
    
    @field_validator('PersonnelId')
    @classmethod
    def validate_personnel_id(cls, v: str) -> str:
        """Ensure PersonnelId is max 8 characters."""
        if len(v) > 8:
            return v[:8]
        return v
    
    @field_validator('ClockedStatus')
    @classmethod
    def validate_clocked_status(cls, v: str) -> str:
        """Ensure ClockedStatus is IN or OUT (max 3 chars)."""
        if v not in ["IN", "OUT"]:
            raise ValueError("ClockedStatus must be 'IN' or 'OUT'")
        return v
    
    @field_validator('BuWerks')
    @classmethod
    def validate_buwerks(cls, v: str) -> str:
        """Ensure BuWerks is max 4 characters."""
        if len(v) > 4:
            return v[:4]
        return v
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """Format datetime to YYYYMMDDHHMMSS."""
        return dt.strftime("%Y%m%d%H%M%S")
    
    @classmethod
    def create_in_event(
        cls,
        assignment: RosterAssignment,
        clocked_time: datetime,
        device_id: str = "SIM-10.0.0.5",
    ) -> "ClockEvent":
        """Create a clock-IN event."""
        return cls(
            BuWerks=assignment.plant[:4],  # Ensure max 4 chars
            ClockedDateTime=cls.format_datetime(clocked_time),
            ClockedDeviceId=device_id[:15],  # Ensure max 15 chars
            ClockedStatus="IN",
            ClockingId=str(uuid4()),
            PersonnelId=assignment.personnel_id[:8],  # Ensure max 8 chars
            RequestId=str(uuid4()),
        )
    
    @classmethod
    def create_out_event(
        cls,
        assignment: RosterAssignment,
        clocked_time: datetime,
        device_id: str = "SIM-10.0.0.5",
    ) -> "ClockEvent":
        """Create a clock-OUT event."""
        return cls(
            BuWerks=assignment.plant[:4],  # Ensure max 4 chars
            ClockedDateTime=cls.format_datetime(clocked_time),
            ClockedDeviceId=device_id[:15],  # Ensure max 15 chars
            ClockedStatus="OUT",
            ClockingId=str(uuid4()),
            PersonnelId=assignment.personnel_id[:8],  # Ensure max 8 chars
            RequestId=str(uuid4()),
        )

