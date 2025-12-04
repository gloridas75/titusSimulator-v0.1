# 🎨 Titus Simulator - Web UI Guide

## Overview

A beautiful, intuitive web interface built with **Streamlit** for testing and monitoring the Titus Simulator. Test all functionality in one place without using curl or command-line tools.

## Features

### 📤 Upload Roster
- Upload roster JSON files
- Validate format automatically
- View JSON data preview
- See assignment counts

### 📊 Status Dashboard
- Real-time view of all assignments
- Clock-IN and Clock-OUT timestamps
- Color-coded status indicators
- Search and filter capabilities
- Export to CSV

### 📈 Statistics
- Total assignments tracked
- Event counts (IN/OUT)
- Completion rates with progress bars
- Database information

### 🔧 Controls
- API health monitoring
- Manual simulation trigger
- One-click refresh
- Real-time updates

## Quick Start

### Method 1: Using the Script (Recommended)

```bash
./start_ui.sh
```

This will:
1. Create/activate virtual environment
2. Install dependencies
3. Start the UI on http://localhost:8501

### Method 2: Using Make

```bash
# Start just the UI (server must be running separately)
make ui

# Start both server and UI together
make both
```

### Method 3: Manual Start

```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install streamlit pandas httpx

# Start the UI
streamlit run streamlit_ui.py
```

## Prerequisites

**The API server must be running** on port 8000 before using the UI.

Start the server in a separate terminal:
```bash
# Terminal 1 - API Server
./start.sh
# or
make run

# Terminal 2 - Web UI
./start_ui.sh
# or
make ui
```

## Using the Web UI

### 1. Check API Status

Look at the **sidebar** - you'll see:
- ✅ **API Running** (green) - Ready to use
- ❌ **API Not Running** (red) - Start the API server first

### 2. Upload a Roster File

**Tab: 📤 Upload Roster**

1. Click "**Browse files**" or drag & drop a JSON file
2. The file format will be validated automatically
3. View the JSON data in the expandable section
4. See the count of assignments found

**Sample File Included:**
Use `sample_roster.json` in the project root for testing.

**Expected JSON Format:**
```json
{
  "FunctionName": "getRoster",
  "list_item": {
    "data": {
      "d": {
        "results": [
          {
            "PersonnelId": "P001",
            "personnel_first_name": "John",
            "deployment_date": "/Date(1733097600000)/",
            "planned_start_time": "PT8H0M0S",
            ...
          }
        ]
      }
    }
  }
}
```

### 3. Trigger Simulation

**In the Sidebar:**

Click **"▶️ Run Simulation Now"**

This will:
- Fetch today's roster from NGRS
- Generate clock-in/out events
- Send events to NGRS
- Update the database

You'll see a success message with results:
```json
{
  "date": "2024-12-02",
  "assignments_found": 5,
  "events_sent": 10
}
```

### 4. View Status Dashboard

**Tab: 📊 Status Dashboard**

See all roster assignments with their status:

**Metrics at the Top:**
- Total Assignments
- Clock-IN Sent
- Clock-OUT Sent
- Completed (both IN & OUT)

**Filter Options:**
- **By Status**: All, Both IN & OUT Sent, Only IN Sent, etc.
- **Search**: Find specific deployment or personnel IDs

**Table View:**
| Deployment ID | Personnel ID | Time IN | Time OUT |
|---------------|--------------|---------|----------|
| DEPLOY001 | P001 | 2024-12-02 08:05:23 | 2024-12-02 17:08:45 |
| DEPLOY002 | P002 | 2024-12-02 09:02:15 | - |

**Color Coding:**
- 🟢 **Green Row** - Both IN & OUT sent (completed)
- 🟡 **Yellow Row** - Partially sent (only IN or OUT)
- 🔴 **Red Row** - Nothing sent yet

**Export:**
Click **"📥 Download CSV"** to export filtered data.

### 5. View Statistics

**Tab: 📈 Statistics**

Real-time metrics:
- Total assignments in database
- IN events sent count
- OUT events sent count
- Completion rates with visual progress bars

Database information:
- File path and size

### 6. About & Help

**Tab: ℹ️ About**

Information about:
- What Titus Simulator does
- How it works
- Technical architecture
- System status
- Links to documentation

## UI Features in Detail

### Sidebar Controls

**API Status Indicator**
- Real-time connection check
- Updates automatically
- Shows startup instructions if API is down

**Manual Trigger Button**
- Runs simulation immediately for today
- Shows spinner while processing
- Displays results or errors
- Automatically refreshes data on success

**Refresh Button**
- Reloads all data from database
- Updates statistics
- Refreshes dashboard table

### Dashboard Filters

**Status Filter Options:**
1. **All** - Show everything
2. **Both IN & OUT Sent** - Completed assignments only
3. **Only IN Sent** - Missing OUT events
4. **Only OUT Sent** - Missing IN events (unusual)
5. **None Sent** - Not processed yet

**Search Filter:**
- Search by Deployment Item ID
- Search by Personnel ID
- Case-insensitive
- Real-time filtering

### Data Table

**Columns:**
- `deployment_item_id` - Unique deployment identifier
- `personnel_id` - Personnel/officer identifier
- `in_sent_at` - Timestamp when IN event was sent (or `-`)
- `out_sent_at` - Timestamp when OUT event was sent (or `-`)

**Sorting:**
- Click column headers to sort
- Default: Most recent first

**Styling:**
- Color-coded rows for quick status recognition
- Clean, modern design
- Responsive layout

## Sample Workflow

### Complete Testing Workflow:

1. **Start Services**
   ```bash
   # Terminal 1
   make run
   
   # Terminal 2
   make ui
   ```

2. **Verify Connection**
   - Open http://localhost:8501
   - Check sidebar shows "✅ API Running"

3. **Upload Test Data**
   - Go to "📤 Upload Roster" tab
   - Upload `sample_roster.json`
   - Verify 5 assignments found

4. **Simulate Events**
   - Click "▶️ Run Simulation Now" in sidebar
   - Wait for success message
   - Note how many events were sent

5. **View Results**
   - Go to "📊 Status Dashboard" tab
   - See assignments with IN/OUT times
   - Note the color coding

6. **Filter Data**
   - Try different status filters
   - Search for specific IDs
   - Export to CSV if needed

7. **Check Statistics**
   - Go to "📈 Statistics" tab
   - Verify completion rates
   - See database size

8. **Run Again**
   - Click "▶️ Run Simulation Now" again
   - Notice: "0 events sent" (duplicates prevented)
   - Dashboard shows same data (idempotent)

## Troubleshooting

### "API Not Running" Error

**Problem:** Sidebar shows red "❌ API Not Running"

**Solution:**
```bash
# In another terminal
./start.sh
# or
make run
```

### "No data available"

**Problem:** Status Dashboard is empty

**Solution:**
1. Trigger a simulation: Click "▶️ Run Simulation Now"
2. Ensure NGRS API has roster data for today
3. Check API logs for errors

### "Error fetching stats"

**Problem:** Statistics tab shows errors

**Solution:**
1. Verify API is running
2. Check API logs: Look at terminal running `make run`
3. Try manual trigger to test connection

### Upload doesn't trigger simulation

**Note:** Upload only validates the JSON format. It doesn't automatically trigger simulation.

**To process uploaded roster:**
1. Upload the file to see validation
2. Ensure your NGRS API returns this data
3. Click "▶️ Run Simulation Now" to fetch from NGRS and process

### Database file not found

**Problem:** "Database file not found" warning

**Solution:**
- Run a simulation to create the database
- Database is created automatically on first run

## Keyboard Shortcuts

Streamlit provides these shortcuts:

- **R** - Rerun the app (refresh)
- **C** - Clear cache
- **⌘/Ctrl + K** - Open command palette
- **Q** - Stop the app

## Configuration

### Change API URL

Edit `streamlit_ui.py`:
```python
API_BASE_URL = "http://localhost:8000"  # Change this
```

### Change Database Path

Edit `streamlit_ui.py`:
```python
DB_PATH = "sim_state.db"  # Change this
```

### Customize Theme

Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

## Advanced Features

### Auto-Refresh

To enable auto-refresh every N seconds:

Add to `streamlit_ui.py`:
```python
import time

st_autorefresh = st.empty()
with st_autorefresh:
    time.sleep(60)  # Refresh every 60 seconds
    st.rerun()
```

### Custom Filters

The dashboard filtering can be extended to include:
- Date range filters
- Personnel type filters
- Customer/location filters

### Export Options

Currently supports CSV export. Can be extended to:
- Excel (.xlsx)
- PDF reports
- JSON export

## Performance

### Database Queries

- Efficient SQL with indexed columns
- Pagination support for large datasets
- Filtered queries only load needed data

### UI Responsiveness

- Streamlit caching for API calls
- Lazy loading of data
- Optimized rendering

### Limits

- Tested with up to 10,000 assignments
- UI remains responsive
- For larger datasets, consider pagination

## Security Notes

### Local Development

- UI runs on localhost only by default
- No authentication required (local use)
- API communication over HTTP (local)

### Production Considerations

If deploying to production:
1. Add authentication (Streamlit auth)
2. Use HTTPS for API communication
3. Implement role-based access
4. Add audit logging

## Tips & Tricks

### 1. Quick Testing Loop

```bash
# Terminal 1: Run API in dev mode
make dev

# Terminal 2: Run UI
make ui

# Make changes to code
# API auto-reloads (--reload flag)
# UI: Press 'R' to refresh
```

### 2. Batch Testing

Upload multiple roster files and trigger simulation for each to test different scenarios.

### 3. Data Analysis

Export to CSV, then use Excel or Python pandas for deeper analysis of timing patterns.

### 4. Debugging

- Enable debug mode in Streamlit: `streamlit run streamlit_ui.py --logger.level=debug`
- Check browser console for JavaScript errors
- Use "Clear Cache" (C key) if data seems stale

## Screenshots Description

### Main Dashboard
- Clean, modern interface
- Sidebar with controls on left
- Main content area with tabs
- Real-time status indicators

### Status Table
- Color-coded rows
- Sortable columns
- Search and filter bar
- Export button

### Statistics View
- Large metric cards
- Progress bars for rates
- System information panel

## Integration with API

The UI communicates with the API using these endpoints:

| UI Action | API Endpoint | Method |
|-----------|--------------|--------|
| Check health | `/health` | GET |
| Get statistics | `/stats` | GET |
| Trigger simulation | `/run-once` | POST |

All communication uses `httpx` library with proper error handling.

## Future Enhancements

Possible improvements:
- 📊 Real-time charts and graphs
- 📅 Historical data viewer
- 🔔 Notifications for errors
- 📧 Email reports
- 🎨 Dark mode toggle
- 🌐 Multi-language support
- 📱 Mobile-responsive layout
- 🔍 Advanced search with regex
- 📦 Bulk operations
- 🎯 Custom event scenarios

## Support

For issues with the UI:
1. Check API is running (`make run`)
2. Verify database exists (`ls -la sim_state.db`)
3. Review terminal logs
4. Clear browser cache
5. Restart both API and UI

For feature requests or bugs:
- Check main documentation
- Review USAGE.md
- Test with sample_roster.json

---

**The Web UI makes testing Titus Simulator simple and intuitive!**

No more curl commands or manual database queries - everything you need in one beautiful interface.
