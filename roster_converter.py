"""
Roster Converter - Transform shift assignment data to NGRS/Titus Simulator format

Converts shift scheduling output (output.json) into the format required by
the Titus Simulator's roster client.

Input Format:
- Shift assignments with employeeId, date, start/end times
- Demand and requirement information
- Work pattern and status

Output Format:
- NGRS roster envelope structure
- RawRosterMetadata format with personnel and deployment details
- /Date(milliseconds)/ and PT duration formats
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class RosterConverter:
    """Convert shift assignment data to NGRS roster format."""
    
    def __init__(self):
        """Initialize the converter."""
        self.default_plant = "PLANT001"
        self.default_customer_id = "C001"
        self.default_customer_name = "Default Customer"
        self.default_location_prefix = "Site"
        
    def convert_file(self, input_path: str | Path, output_path: str | Path = None) -> dict:
        """
        Convert a shift assignment JSON file to NGRS roster format.
        
        Args:
            input_path: Path to input JSON file (output.json format)
            output_path: Optional path to save converted JSON
            
        Returns:
            Converted roster data in NGRS format
        """
        # Read input file
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        # Convert assignments
        roster_data = self.convert_assignments(data.get('assignments', []))
        
        # Save if output path provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(roster_data, f, indent=2)
            print(f"✅ Converted {len(data.get('assignments', []))} assignments")
            print(f"📄 Output saved to: {output_path}")
        
        return roster_data
    
    def convert_assignments(self, assignments: list[dict]) -> dict:
        """
        Convert assignments list to NGRS roster envelope format.
        
        Args:
            assignments: List of assignment dictionaries
            
        Returns:
            NGRS roster envelope with converted results
        """
        results = []
        
        for assignment in assignments:
            if assignment.get('status') == 'ASSIGNED':
                roster_item = self.convert_single_assignment(assignment)
                results.append(roster_item)
        
        # Create NGRS envelope structure
        roster_envelope = {
            "FunctionName": "getRoster",
            "list_item": {
                "data": {
                    "d": {
                        "results": results,
                        "summary": {
                            "total_count": len(results),
                            "converted_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                }
            }
        }
        
        return roster_envelope
    
    def convert_single_assignment(self, assignment: dict) -> dict:
        """
        Convert a single assignment to NGRS RawRosterMetadata format.
        
        Args:
            assignment: Assignment dictionary from output.json
            
        Returns:
            RawRosterMetadata dictionary
        """
        # Extract employee information
        employee_id = assignment['employeeId']
        
        # Parse dates
        date_str = assignment['date']
        start_dt = datetime.fromisoformat(assignment['startDateTime'])
        end_dt = datetime.fromisoformat(assignment['endDateTime'])
        
        # Convert date to milliseconds format
        deployment_date_ms = self.to_milliseconds_format(start_dt)
        
        # Convert times to PT duration format
        planned_start_time = self.to_duration_format(start_dt)
        planned_end_time = self.to_duration_format(end_dt)
        
        # Extract demand and requirement info
        demand_id = assignment['demandId']
        requirement_id = assignment['requirementId']
        deployment_item_id = assignment['assignmentId']
        
        # Parse employee name (if not provided, generate from ID)
        first_name = f"Employee"
        last_name = employee_id
        
        # Determine location from demandId or other fields
        location = self.extract_location(assignment)
        
        # Build RawRosterMetadata
        roster_metadata = {
            "PersonnelId": employee_id,
            "personnel_first_name": first_name,
            "personnel_last_name": last_name,
            "PersonnelType": "Officer",
            "PersonnelTypeDescription": "Security Officer",
            "SecSeqNum": str(assignment.get('newRotationOffset', 0)),
            "PrimarySeqNum": "1",
            "demand_item_id": demand_id,
            "customer_id": self.default_customer_id,
            "customer_name": self.default_customer_name,
            "deployment_location": location,
            "deployment_date": deployment_date_ms,
            "deploymentItm": deployment_item_id,
            "planner_group_id": requirement_id,
            "plant": self.default_plant,
            "planned_start_time": planned_start_time,
            "planned_end_time": planned_end_time,
            "demand_type": "Regular"
        }
        
        return roster_metadata
    
    def to_milliseconds_format(self, dt: datetime) -> str:
        """
        Convert datetime to /Date(milliseconds)/ format.
        
        Args:
            dt: Datetime object
            
        Returns:
            String in format "/Date(1733097600000)/"
        """
        # Convert to UTC if timezone-aware
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
        else:
            # Assume local time
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Get milliseconds since epoch
        milliseconds = int(dt.timestamp() * 1000)
        
        return f"/Date({milliseconds})/"
    
    def to_duration_format(self, dt: datetime) -> str:
        """
        Convert datetime to PT duration format (time of day).
        
        Args:
            dt: Datetime object
            
        Returns:
            String in format "PT8H0M0S" for 8:00 AM
        """
        hours = dt.hour
        minutes = dt.minute
        seconds = dt.second
        
        return f"PT{hours}H{minutes}M{seconds}S"
    
    def extract_location(self, assignment: dict) -> str:
        """
        Extract deployment location from assignment data.
        
        Args:
            assignment: Assignment dictionary
            
        Returns:
            Location string
        """
        # Try to extract from demandId or use default
        demand_id = assignment.get('demandId', '')
        
        # You can customize this based on your demandId structure
        # For now, use a simple pattern
        if demand_id:
            # Extract meaningful part from demandId
            parts = demand_id.split('-')
            if len(parts) >= 3:
                return f"{self.default_location_prefix} {parts[-1]}"
        
        return f"{self.default_location_prefix} - Default"
    
    def filter_by_date_range(
        self,
        input_path: str | Path,
        start_date: str,
        end_date: str,
        output_path: str | Path = None
    ) -> dict:
        """
        Convert assignments and filter by date range.
        
        Args:
            input_path: Path to input JSON file
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            output_path: Optional path to save filtered output
            
        Returns:
            Filtered roster data
        """
        # Read input file
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        # Filter assignments by date
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        filtered_assignments = [
            a for a in data.get('assignments', [])
            if start <= datetime.fromisoformat(a['date']) <= end
            and a.get('status') == 'ASSIGNED'
        ]
        
        print(f"📅 Filtered: {len(filtered_assignments)} assignments between {start_date} and {end_date}")
        
        # Convert filtered assignments
        roster_data = self.convert_assignments(filtered_assignments)
        
        # Save if output path provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(roster_data, f, indent=2)
            print(f"📄 Output saved to: {output_path}")
        
        return roster_data
    
    def get_summary(self, input_path: str | Path) -> dict:
        """
        Get summary statistics from input file.
        
        Args:
            input_path: Path to input JSON file
            
        Returns:
            Summary dictionary with statistics
        """
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        assignments = data.get('assignments', [])
        
        # Calculate statistics
        total = len(assignments)
        assigned = len([a for a in assignments if a.get('status') == 'ASSIGNED'])
        
        # Get unique employees
        employees = set(a['employeeId'] for a in assignments if a.get('status') == 'ASSIGNED')
        
        # Get date range
        dates = [a['date'] for a in assignments if a.get('status') == 'ASSIGNED']
        min_date = min(dates) if dates else None
        max_date = max(dates) if dates else None
        
        # Get unique demands
        demands = set(a['demandId'] for a in assignments if a.get('status') == 'ASSIGNED')
        
        summary = {
            "total_assignments": total,
            "assigned_count": assigned,
            "unique_employees": len(employees),
            "unique_demands": len(demands),
            "date_range": {
                "start": min_date,
                "end": max_date
            },
            "planning_reference": data.get('planningReference'),
            "solver_status": data.get('solverRun', {}).get('status')
        }
        
        return summary


def main():
    """Command-line interface for the converter."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert shift assignment data to NGRS roster format'
    )
    parser.add_argument(
        'input',
        help='Input JSON file (output.json format)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output JSON file (NGRS roster format)',
        default='converted_roster.json'
    )
    parser.add_argument(
        '--start-date',
        help='Filter start date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        help='Filter end date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary only, do not convert'
    )
    parser.add_argument(
        '--plant',
        help='Plant/Business Unit ID',
        default='PLANT001'
    )
    parser.add_argument(
        '--customer-id',
        help='Customer ID',
        default='C001'
    )
    parser.add_argument(
        '--customer-name',
        help='Customer name',
        default='Default Customer'
    )
    
    args = parser.parse_args()
    
    # Create converter
    converter = RosterConverter()
    converter.default_plant = args.plant
    converter.default_customer_id = args.customer_id
    converter.default_customer_name = args.customer_name
    
    # Show summary if requested
    if args.summary:
        summary = converter.get_summary(args.input)
        print("\n📊 Roster Summary:")
        print(f"  Total Assignments: {summary['total_assignments']}")
        print(f"  Assigned: {summary['assigned_count']}")
        print(f"  Unique Employees: {summary['unique_employees']}")
        print(f"  Unique Demands: {summary['unique_demands']}")
        print(f"  Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        print(f"  Planning Ref: {summary['planning_reference']}")
        print(f"  Solver Status: {summary['solver_status']}")
        return 0
    
    # Convert with optional date filtering
    if args.start_date and args.end_date:
        converter.filter_by_date_range(
            args.input,
            args.start_date,
            args.end_date,
            args.output
        )
    else:
        converter.convert_file(args.input, args.output)
    
    print("\n✨ Conversion complete!")
    print(f"📁 Output file: {args.output}")
    print("\nYou can now use this file with the Titus Simulator:")
    print("  1. Upload in Web UI (http://localhost:8501)")
    print("  2. Or place at your NGRS roster API endpoint")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
