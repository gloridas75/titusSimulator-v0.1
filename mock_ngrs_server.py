#!/usr/bin/env python3
"""
Mock NGRS Server to capture clocking events from Titus Simulator
Saves all received events to mock_ngrs_captured_events.json
"""

from fastapi import FastAPI, Request
from datetime import datetime
import json
import uvicorn

app = FastAPI()

# Store captured events
captured_events = []

@app.post("/api/integration/titus/clocking")
async def receive_clocking(request: Request):
    """Receive and capture clocking events"""
    try:
        event = await request.json()
        
        # Add metadata
        captured_event = {
            "received_at": datetime.now().isoformat(),
            "event": event
        }
        captured_events.append(captured_event)
        
        # Save to file
        with open("mock_ngrs_captured_events.json", "w") as f:
            json.dump(captured_events, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"📥 RECEIVED CLOCKING EVENT #{len(captured_events)}")
        print(f"{'='*60}")
        print(json.dumps(event, indent=2))
        print(f"{'='*60}\n")
        
        # Return success response (mimicking NGRS API)
        return {
            "status": "success",
            "message": "Clocking event received",
            "clockingId": event.get("ClockingId"),
            "requestId": event.get("RequestId")
        }
        
    except Exception as e:
        print(f"❌ Error processing clocking event: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/integration/titus/clocking/summary")
async def get_summary():
    """Get summary of captured events"""
    return {
        "total_events": len(captured_events),
        "events": captured_events
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "service": "mock-ngrs-server",
        "events_captured": len(captured_events)
    }

if __name__ == "__main__":
    print("🚀 Starting Mock NGRS Server on http://localhost:8080")
    print("📝 Captured events will be saved to: mock_ngrs_captured_events.json")
    print("-" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8080)
