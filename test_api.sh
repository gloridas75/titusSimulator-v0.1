#!/bin/bash

# Titus Simulator API Test Script
# This script tests all the main API endpoints

BASE_URL="http://localhost:8087"
NGRS_URL="http://localhost:8080/api/integration/titus/clocking"

echo "========================================="
echo "Titus Simulator API Test"
echo "========================================="
echo

# 1. Health Check
echo "1. Testing Health Check..."
curl -s "$BASE_URL/health" | python3 -m json.tool
echo
echo "---"
echo

# 2. Get Statistics
echo "2. Getting Statistics..."
curl -s "$BASE_URL/stats" | python3 -m json.tool
echo
echo "---"
echo

# 3. Get Roster Logs
echo "3. Getting Roster Upload Logs..."
curl -s "$BASE_URL/roster-logs" | python3 -m json.tool | head -30
echo
echo "---"
echo

# 4. Upload Roster
echo "4. Uploading Sample Roster..."
ROSTER_RESPONSE=$(curl -s -X POST "$BASE_URL/upload-roster" \
  -H "Content-Type: application/json" \
  -d @sample_roster.json)

echo "$ROSTER_RESPONSE" | python3 -m json.tool
echo

# Extract roster_file_id from response
ROSTER_FILE_ID=$(echo "$ROSTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('roster_file_id', ''))")
echo "Roster File ID: $ROSTER_FILE_ID"
echo
echo "---"
echo

# 5. Query Roster by RosterFileId
if [ -n "$ROSTER_FILE_ID" ]; then
    echo "5. Querying Roster by RosterFileId..."
    curl -s "$BASE_URL/roster?rosterFileId=$ROSTER_FILE_ID" | python3 -m json.tool | head -50
    echo
    echo "---"
    echo
fi

# 6. Test Clocking Event Format (Mock NGRS endpoint)
echo "6. Testing Clocking Event Format..."
echo "Sample clocking event (as per JSON_SCHEMAS.md):"
cat << 'EOF' | python3 -m json.tool
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
EOF
echo
echo "---"
echo

# 7. Run Simulation (Immediate Mode) - Optional
echo "7. Simulation Test (Optional - Uncomment to run)"
echo "To run immediate simulation:"
echo "  curl -X POST \"$BASE_URL/run-from-file?mode=immediate&rosterFileId=$ROSTER_FILE_ID\""
echo
echo "To run realtime simulation:"
echo "  curl -X POST \"$BASE_URL/run-from-file?mode=realtime&rosterFileId=$ROSTER_FILE_ID\""
echo
echo "---"
echo

echo "========================================="
echo "API Tests Completed!"
echo "========================================="
echo
echo "API Documentation: http://localhost:8087/docs"
echo "Postman Collection: postman/Titus_Simulator_API.postman_collection.json"
