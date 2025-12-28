# Attendance Pattern Implementation Summary

## ✅ Successfully Implemented - 80:20 Split

The Titus Simulator now generates realistic attendance patterns with two distinct employee groups.

## Group Distribution

### Group 1: Compliant Employees (80%)
**Characteristics**: Always work ≥ planned hours
- **Clock IN**: -5 to 0 minutes (arrive early or on-time, never late)
- **Clock OUT**: 0 to +5 minutes (leave on-time or with overtime)
- **Result**: Positive time difference (always work extra 0-10 minutes)

**Pattern**: ✅ Arrive early/on-time & leave on-time/late → Extra hours

### Group 2: Short Hours Employees (20%)
**Characteristics**: Always work < planned hours
- **Clock IN**: 0 to +2 minutes (on-time to slightly late)
- **Clock OUT**: -5 to -3 minutes (leave 3-5 minutes early)
- **Result**: Negative time difference (short by 3-7 minutes)

**Pattern**: ⚠️ Arrive late & leave early → Short hours

## Implementation Details

### Deterministic Behavior
- Group assignment based on `hash(personnel_id) % 100`
- 80% (0-79): Compliant group
- 20% (80-99): Short hours group
- Same employee always falls into the same group
- Random offsets are deterministic based on deployment and personnel IDs

### Distribution Example (10 employees sample)
- **Compliant (80%)**: 8-9 employees - All show positive time difference
- **Short Hours (20%)**: 1-2 employees - All show 3-5 minute shortage

### Logging Enhancement
Each event includes:
- Group label: `[Compliant (80%)]`, `[Short Hours (20%)]`
- IN and OUT offsets in minutes
- Actual worked hours vs planned hours
- Time difference in minutes with sign (+/-)

## Verification

The implementation successfully achieves:
1. ✅ 80% compliant employees always exceed planned hours
2. ✅ 20% employees consistently short by 3-5 minutes
3. ✅ ALL 20% group members arrive late AND leave early
4. ✅ Deterministic and reproducible results
5. ✅ Enhanced logging for tracking and analysis

## Example Log Output

```
Planned events for Lothar Bin Mertesacker [Short Hours (20%)] 
  - IN offset: +1.0min, OUT offset: -3.0min
  - Worked: 11.93h (Planned: 12.00h, Diff: -4.0min)

Planned events for Lisa Bte Mertesacker [Compliant (80%)]
  - IN offset: -1.0min, OUT offset: +4.0min
  - Worked: 12.08h (Planned: 12.00h, Diff: +5.0min)
```

## Version History

| Version | Date | Split | Description |
|---------|------|-------|-------------|
| 2.0 | 2025-12-28 | 80:20 | Simplified to two groups - All 20% have shortage pattern |
| 1.0 | 2025-12-04 | 90:10 | Initial with sub-groups |
