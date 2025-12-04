# JSON Schema Documentation

## Overview
This document defines the JSON schemas used for communication between Titus Simulator and NGRS API.

---

## 1. NGRS Roster Data Schema (Input to Titus Simulator)

### Purpose
This schema defines the roster information (shift slots and employee assignments) that Titus Simulator receives from NGRS.

### Complete Schema

```json
{
    "FunctionName": "POC-NGRSIntegration",
    "list_item": {      
        "data": {
            "d": {
                "results": [
                    {
                        "__metadata": {
                            "PersonnelId": "00037056",
                            "personnel_first_name": "Cheng Fong",
                            "personnel_last_name": "Lee",
                            "PersonnelType": "01",
                            "PersonnelTypeDescription": "APO",
                            "SecSeqNum": "01",
                            "PrimarySeqNum": "001",
                            "demand_item_id": "DI-8000122864-000020",
                            "customer_id": "103936",
                            "customer_name": "BANK OF CHINA LIMITED",
                            "deployment_location": "Bank Of China - Westgate",
                            "deployment_date": "/Date(1755216000000)/",
                            "deploymentItm": "065A7B378D781FD0869E4BA3E5FE1484",
                            "planner_group_id": "B5W",
                            "plant": "4120",
                            "planned_start_time": "PT10H15M00S",
                            "planned_end_time": "PT19H15M00S",
                            "demand_type": "01"
                        }
                    },
                    {
                        "__metadata": {
                            "PersonnelId": "00000000",
                            "personnel_first_name": "",
                            "personnel_last_name": "",
                            "PersonnelType": "01",
                            "PersonnelTypeDescription": "APO",
                            "SecSeqNum": "01",
                            "PrimarySeqNum": "001",
                            "demand_item_id": "DI-8000122864-000020",
                            "customer_id": "103936",
                            "customer_name": "BANK OF CHINA LIMITED",
                            "deployment_location": "Bank Of China - Westgate",
                            "deployment_date": "/Date(1755302400000)/",
                            "deploymentItm": "065A7B378D781FD0869E4BA3E5FE3484",
                            "planner_group_id": "B5W",
                            "plant": "4120",
                            "planned_start_time": "PT10H15M00S",
                            "planned_end_time": "PT17H30M00S",
                            "demand_type": "01"
                        }
                    }
                ],
                "summary": [
                    {
                        "__metadata": {
                            "deployment_item": "065A7B378D781FD0869E4BA3E5FE1484",
                            "totalQty": 0,
                            "changedTime": 20250814145850
                        }
                    },
                    {
                        "__metadata": {
                            "deployment_item": "065A7B378D781FD0869E4BA3E5FE3484",
                            "totalQty": 1,
                            "changedTime": 20250814145848
                        }
                    }
                ]
            }
        }
    }  
}
```

### Field Definitions

#### Envelope Structure
| Field | Type | Description |
|-------|------|-------------|
| `FunctionName` | string | API function identifier (e.g., "POC-NGRSIntegration") |
| `list_item.data.d.results` | array | Array of roster assignment objects |
| `list_item.data.d.summary` | array | Array of summary metadata objects |

#### Results Array - __metadata Fields

**Personnel Information:**
| Field | Type | Max Length | Description |
|-------|------|------------|-------------|
| `PersonnelId` | string | 8 | Employee ID (e.g., "00037056") |
| `personnel_first_name` | string | - | Employee first name |
| `personnel_last_name` | string | - | Employee last name |
| `PersonnelType` | string | - | Personnel type code |
| `PersonnelTypeDescription` | string | - | Personnel type description (e.g., "APO") |

**Deployment Details:**
| Field | Type | Description |
|-------|------|-------------|
| `deployment_date` | string | Date in `/Date(milliseconds)/` format (Unix epoch in milliseconds) |
| `deploymentItm` | string | **Unique identifier per shift per day** (e.g., "065A7B378D781FD0869E4BA3E5FE1484") |
| `deployment_location` | string | Physical location description |
| `demand_item_id` | string | Demand item reference |
| `demand_type` | string | Type of demand (e.g., "01") |

**Time Information:**
| Field | Type | Format | Description |
|-------|------|--------|-------------|
| `planned_start_time` | string | PT{H}H{M}M{S}S | ISO 8601 duration format (e.g., "PT10H15M00S" = 10:15:00) |
| `planned_end_time` | string | PT{H}H{M}M{S}S | ISO 8601 duration format (e.g., "PT19H15M00S" = 19:15:00) |

**Organizational Data:**
| Field | Type | Max Length | Description |
|-------|------|------------|-------------|
| `plant` | string | 4 | Business unit/plant ID (e.g., "4120") |
| `planner_group_id` | string | - | Planner group identifier |
| `customer_id` | string | - | Customer identifier |
| `customer_name` | string | - | Customer name |

**Sequence Numbers:**
| Field | Type | Format | Description |
|-------|------|--------|-------------|
| `SecSeqNum` | string | "01"-"03" | **Shift split number**: "01", "02", or "03" based on number of splits when shift is divided into 2-3 parts |
| `PrimarySeqNum` | string | "001"-"010" | **Primary sequence**: "001" to "010" for up to 10 different officers assigned to same shift time |

#### Summary Array - __metadata Fields

| Field | Type | Format | Description |
|-------|------|--------|-------------|
| `deployment_item` | string | - | Deployment item identifier (matches `deploymentItm` in results) |
| `totalQty` | integer | - | Total quantity of assignments |
| `changedTime` | integer | YYYYMMDDHHMMSS | Last change timestamp (e.g., 20250814145850) |

### Date/Time Format Details

1. **deployment_date**: `/Date(1755216000000)/`
   - Unix timestamp in milliseconds wrapped in `/Date()/`
   - Example: `/Date(1755216000000)/` = 2025-08-15

2. **planned_start_time / planned_end_time**: `PT10H15M00S`
   - ISO 8601 duration format
   - Represents time of day (not duration)
   - Format: `PT{hours}H{minutes}M{seconds}S`
   - Example: `PT10H15M00S` = 10:15:00 AM

3. **changedTime**: `20250814145850`
   - Format: YYYYMMDDHHMMSS
   - Example: `20250814145850` = 2025-08-14 14:58:50

### Important Notes

- **PersonnelId "00000000"** with empty name fields indicates an **unassigned/vacant slot**
- **deploymentItm** is the unique identifier for each shift per day - this is crucial for tracking
- **SecSeqNum** indicates how many parts a shift has been split into (common for long shifts)
- **PrimarySeqNum** allows multiple officers to be assigned to the same shift time slot

---

## 2. Clocking Event Schema (Output from Titus Simulator to NGRS)

### Purpose
This schema defines the simulated clock-in/clock-out events that Titus Simulator sends to the NGRS Clocking API.

### Complete Schema

```json
{
    "BuWerks": "4120",
    "ClockedDateTime": "20240915092822",
    "ClockedDeviceId": "898.10.15.14",
    "ClockedStatus": "OUT",
    "ClockingId": "00c2awe0-96f9-4dba-a891-83014e23447a",
    "PersonnelId": "00023280",
    "RequestId": "4aaweu6e-42be-4957-bsd5-3f721e8f4020",
    "SendFrom": "titusSimulator"
}
```

### Field Definitions

| Attribute Name | Data Type | Max Length | Required | Description |
|----------------|-----------|------------|----------|-------------|
| `BuWerks` | Edm.String | 4 | Yes | Business unit/plant ID (e.g., "4120") |
| `ClockedDateTime` | Edm.String | 14 | Yes | Actual clock-in/out timestamp in YYYYMMDDHHMMSS format |
| `ClockedDeviceId` | Edm.String | 15 | Yes | Device identifier (e.g., "898.10.15.14" or "SIM-10.0.0.5") |
| `ClockedStatus` | Edm.String | 3 | Yes | Clock event type: "IN" or "OUT" |
| `ClockingId` | Edm.String | 40 | Yes | Unique identifier for this clocking event (UUID format) |
| `PersonnelId` | Edm.String | 8 | Yes | Employee ID (e.g., "00023280") |
| `RequestId` | Edm.String | 40 | Yes | Unique request identifier (UUID format) |
| `SendFrom` | Edm.String | 15 | Yes | Source system identifier (default: "titusSimulator") |

### Field Details

#### BuWerks
- **Format**: Up to 4 characters
- **Example**: "4120"
- **Source**: Mapped from `plant` field in roster data
- **Validation**: Auto-truncated to 4 characters if longer

#### ClockedDateTime
- **Format**: YYYYMMDDHHMMSS (14 digits)
- **Example**: "20240915092822" = 2024-09-15 09:28:22
- **Description**: The actual simulated time when employee clocked in/out
- **Generation**: Based on planned shift times with random variations (±15 minutes)

#### ClockedDeviceId
- **Format**: Up to 15 characters
- **Example**: "898.10.15.14" or "SIM-10.0.0.5"
- **Description**: Identifier of the clocking device/terminal
- **Default**: "SIM-10.0.0.5" (simulated device)
- **Validation**: Auto-truncated to 15 characters if longer

#### ClockedStatus
- **Format**: 3 characters maximum
- **Values**: 
  - `"IN"` - Clock-in event
  - `"OUT"` - Clock-out event
- **Validation**: Must be exactly "IN" or "OUT"

#### ClockingId
- **Format**: UUID string, up to 40 characters
- **Example**: "00c2awe0-96f9-4dba-a891-83014e23447a"
- **Description**: Unique identifier for this specific clocking event
- **Generation**: Auto-generated UUID for each event

#### PersonnelId
- **Format**: Up to 8 characters
- **Example**: "00023280"
- **Source**: From roster data `PersonnelId` field
- **Validation**: Auto-truncated to 8 characters if longer

#### RequestId
- **Format**: UUID string, up to 40 characters
- **Example**: "4aaweu6e-42be-4957-bsd5-3f721e8f4020"
- **Description**: Unique identifier for the API request
- **Generation**: Auto-generated UUID for each event

#### SendFrom
- **Format**: Up to 15 characters
- **Example**: "titusSimulator"
- **Description**: Identifies the source system sending the clocking data
- **Default**: "titusSimulator"

### Event Generation Logic

For each roster assignment, Titus Simulator generates **two events**:

1. **Clock-IN Event**
   - `ClockedStatus`: "IN"
   - `ClockedDateTime`: Planned start time ± random variation (0-15 minutes)
   - All other fields populated from roster data

2. **Clock-OUT Event**
   - `ClockedStatus`: "OUT"
   - `ClockedDateTime`: Planned end time ± random variation (0-15 minutes)
   - All other fields populated from roster data

### API Endpoint

- **URL**: `http://localhost:8080/api/integration/titus/clocking` (default)
- **Method**: POST
- **Content-Type**: application/json
- **Authentication**: Optional Bearer token via `Authorization` header

### Transmission Format

**Important**: Events are sent **individually**, one JSON object per HTTP POST request.

Each POST body contains a single event object (not wrapped in an array or envelope):

```json
{
    "BuWerks": "4120",
    "ClockedDateTime": "20240915092822",
    "ClockedDeviceId": "898.10.15.14",
    "ClockedStatus": "OUT",
    "ClockingId": "00c2awe0-96f9-4dba-a891-83014e23447a",
    "PersonnelId": "00023280",
    "RequestId": "4aaweu6e-42be-4957-bsd5-3f721e8f4020",
    "SendFrom": "titusSimulator"
}
```

### Field Order

The JSON fields are serialized in the exact order shown above to ensure consistency with NGRS API expectations.

---

## Integration Flow

### Step 1: Roster Data Ingestion
1. NGRS sends roster data to Titus Simulator using **Schema 1** (Roster Data)
2. Simulator parses the nested `__metadata` structure
3. Extracts assignment details for each shift

### Step 2: Event Generation
1. For each roster assignment with valid `PersonnelId` (not "00000000"):
   - Generate Clock-IN event
   - Generate Clock-OUT event
2. Apply time variations to simulate realistic clocking behavior
3. Store events in local SQLite database

### Step 3: Event Transmission
1. For each generated event:
   - Format as JSON using **Schema 2** (Clocking Event)
   - Send individual POST request to NGRS Clocking API
   - Log success/failure status

### Step 4: State Tracking
1. Mark events as sent in database
2. Maintain audit trail of all simulated clocking activity
3. Generate statistics and reports

---

## Validation Rules

### Roster Data Validation
- ✅ `PersonnelId` must be 8 digits or less
- ✅ `deployment_date` must be in `/Date(milliseconds)/` format
- ✅ `planned_start_time` and `planned_end_time` must be valid ISO 8601 durations
- ✅ `deploymentItm` must be unique per shift per day
- ✅ Empty `PersonnelId` ("00000000" or blank) indicates unassigned slot (skip event generation)

### Clocking Event Validation
- ✅ All string fields must not exceed maximum length
- ✅ `ClockedStatus` must be "IN" or "OUT"
- ✅ `ClockedDateTime` must be 14 digits (YYYYMMDDHHMMSS)
- ✅ `PersonnelId` must match a valid roster assignment
- ✅ UUIDs must be properly formatted

---

## Error Handling

### Common Issues

1. **Missing PersonnelId**: Skip event generation (vacant slot)
2. **Invalid date formats**: Log error and skip assignment
3. **Network failures**: Retry logic not implemented (events logged as unsent)
4. **Field length violations**: Auto-truncation applied with warning log

### Logging Levels

- **INFO**: Successful operations (roster loaded, events sent)
- **WARNING**: Non-critical issues (NGRS API unavailable, auto-truncation)
- **ERROR**: Critical failures (parsing errors, invalid data)
- **DEBUG**: Detailed state tracking (individual event generation)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-04 | Initial schema documentation |

---

## Contact

For questions or issues regarding these schemas, please contact the NGRS Integration Team.
