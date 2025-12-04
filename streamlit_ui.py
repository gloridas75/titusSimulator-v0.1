"""
Streamlit Web UI for Titus Simulator Testing

A simple web interface to:
- Upload roster JSON files
- Trigger simulation cycles
- View assignment status with clock-in/out times
- Monitor statistics and logs
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import httpx
import pandas as pd
import streamlit as st

# Configuration
API_BASE_URL = "http://localhost:8000"
DB_PATH = "sim_state.db"


def check_api_health() -> bool:
    """Check if the Titus Simulator API is running."""
    try:
        response = httpx.get(f"{API_BASE_URL}/health", timeout=2.0)
        return response.status_code == 200
    except:
        return False


def get_stats() -> dict:
    """Get statistics from the API."""
    try:
        response = httpx.get(f"{API_BASE_URL}/stats", timeout=5.0)
        response.raise_for_status()
        return response.json().get("stats", {})
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
        return {}


def trigger_simulation() -> dict:
    """Trigger a manual simulation cycle."""
    try:
        response = httpx.post(f"{API_BASE_URL}/run-once", timeout=30.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error triggering simulation: {e}")
        return {"status": "error", "message": str(e)}


def upload_roster_json(json_data: dict) -> dict:
    """Upload roster JSON to the simulator API."""
    try:
        response = httpx.post(
            f"{API_BASE_URL}/upload-roster",
            json=json_data,
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error uploading roster: {e}")
        return {"status": "error", "message": str(e)}


def trigger_file_simulation() -> dict:
    """Trigger simulation using uploaded file."""
    try:
        response = httpx.post(f"{API_BASE_URL}/run-from-file", timeout=60.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error triggering file simulation: {e}")
        return {"status": "error", "message": str(e)}


def get_database_data() -> pd.DataFrame:
    """Read data from the SQLite database."""
    if not Path(DB_PATH).exists():
        return pd.DataFrame()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
        SELECT 
            deployment_item_id,
            personnel_id,
            in_sent_at,
            out_sent_at
        FROM simulated_events
        ORDER BY in_sent_at DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Format timestamps
        if not df.empty:
            df['in_sent_at'] = pd.to_datetime(df['in_sent_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
            df['out_sent_at'] = pd.to_datetime(df['out_sent_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
            df['in_sent_at'] = df['in_sent_at'].replace('NaT', '-')
            df['out_sent_at'] = df['out_sent_at'].replace('NaT', '-')
        
        return df
    except Exception as e:
        st.error(f"Error reading database: {e}")
        return pd.DataFrame()


def main():
    """Main Streamlit application."""
    
    st.set_page_config(
        page_title="Titus Simulator - Test UI",
        page_icon="🕐",
        layout="wide",
    )
    
    st.title("🕐 Titus Simulator - Test Interface")
    st.markdown("---")
    
    # Sidebar - API Status & Controls
    with st.sidebar:
        st.header("🔧 Controls")
        
        # API Health Check
        st.subheader("API Status")
        if check_api_health():
            st.success("✅ API Running")
        else:
            st.error("❌ API Not Running")
            st.info("Start the simulator with:\n```bash\nmake run\n```")
        
        st.markdown("---")
        
        # Manual Trigger
        st.subheader("Manual Trigger")
        
        # Check if roster is uploaded
        if 'roster_uploaded' in st.session_state and st.session_state.roster_uploaded:
            st.info("📁 Roster file uploaded")
            if st.button("▶️ Run Simulation Now", use_container_width=True, type="primary"):
                with st.spinner("Running file-based simulation..."):
                    result = trigger_file_simulation()
                    if result.get("status") == "completed":
                        st.success("✅ Simulation completed!")
                        st.json(result.get("result", {}))
                        # Clear the uploaded flag after successful run
                        # st.session_state.roster_uploaded = False
                    elif result.get("status") == "error":
                        st.error(f"❌ {result.get('message', 'Simulation failed')}")
        else:
            if st.button("▶️ Run Simulation (API)", use_container_width=True):
                with st.spinner("Running API-based simulation..."):
                    result = trigger_simulation()
                    if result.get("status") == "completed":
                        st.success("✅ Simulation completed!")
                        st.json(result.get("result", {}))
                    elif result.get("status") == "error":
                        st.error(f"❌ {result.get('message', 'Simulation failed')}")
        
        st.markdown("---")
        
        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    # Main content area - Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Upload Roster",
        "📊 Status Dashboard",
        "📈 Statistics",
        "ℹ️ About"
    ])
    
    # Tab 1: Upload Roster
    with tab1:
        st.header("📤 Upload Roster JSON")
        st.markdown("""
        Upload a roster JSON file to send to the simulator. The JSON should follow the NGRS format:
        ```json
        {
          "FunctionName": "getRoster",
          "list_item": {
            "data": {
              "d": {
                "results": [ ... ]
              }
            }
          }
        }
        ```
        """)
        
        uploaded_file = st.file_uploader(
            "Choose a JSON file",
            type=['json'],
            help="Upload a roster JSON file in NGRS format"
        )
        
        if uploaded_file is not None:
            try:
                # Read and parse JSON
                json_data = json.load(uploaded_file)
                
                # Display preview
                st.success(f"✅ File loaded: {uploaded_file.name}")
                
                with st.expander("📄 View JSON Data"):
                    st.json(json_data)
                
                # Upload to API
                result = upload_roster_json(json_data)
                
                if result.get("status") == "success":
                    st.session_state.roster_uploaded = True
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Assignments Found", result.get("assignments_count", 0))
                    with col2:
                        st.success("✅ Uploaded to simulator")
                    
                    # Show how to use the data
                    st.markdown("### Next Steps:")
                    st.markdown("""
                    1. The roster has been uploaded to the simulator
                    2. Click **"Run Simulation Now"** in the sidebar to process
                    3. View results in the **Status Dashboard** tab
                    """)
                elif result.get("status") == "error":
                    st.error(f"❌ Error: {result.get('message', 'Upload failed')}")
                
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON file: {e}")
            except Exception as e:
                st.error(f"❌ Error processing file: {e}")
    
    # Tab 2: Status Dashboard
    with tab2:
        st.header("📊 Assignment Status Dashboard")
        st.markdown("View all roster assignments with their clock-in/out status")
        
        # Fetch data
        df = get_database_data()
        
        if df.empty:
            st.info("ℹ️ No data available. Run a simulation to generate events.")
        else:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_assignments = len(df)
            in_sent = df[df['in_sent_at'] != '-'].shape[0]
            out_sent = df[df['out_sent_at'] != '-'].shape[0]
            completed = df[(df['in_sent_at'] != '-') & (df['out_sent_at'] != '-')].shape[0]
            
            col1.metric("Total Assignments", total_assignments)
            col2.metric("Clock-IN Sent", in_sent)
            col3.metric("Clock-OUT Sent", out_sent)
            col4.metric("Completed", completed)
            
            st.markdown("---")
            
            # Filters
            st.subheader("🔍 Filters")
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                filter_status = st.selectbox(
                    "Filter by Status",
                    ["All", "Both IN & OUT Sent", "Only IN Sent", "Only OUT Sent", "None Sent"]
                )
            
            with filter_col2:
                search_term = st.text_input("Search Deployment or Personnel ID", "")
            
            # Apply filters
            filtered_df = df.copy()
            
            if filter_status == "Both IN & OUT Sent":
                filtered_df = filtered_df[(filtered_df['in_sent_at'] != '-') & (filtered_df['out_sent_at'] != '-')]
            elif filter_status == "Only IN Sent":
                filtered_df = filtered_df[(filtered_df['in_sent_at'] != '-') & (filtered_df['out_sent_at'] == '-')]
            elif filter_status == "Only OUT Sent":
                filtered_df = filtered_df[(filtered_df['in_sent_at'] == '-') & (filtered_df['out_sent_at'] != '-')]
            elif filter_status == "None Sent":
                filtered_df = filtered_df[(filtered_df['in_sent_at'] == '-') & (filtered_df['out_sent_at'] == '-')]
            
            if search_term:
                filtered_df = filtered_df[
                    filtered_df['deployment_item_id'].str.contains(search_term, case=False) |
                    filtered_df['personnel_id'].str.contains(search_term, case=False)
                ]
            
            # Display table
            st.subheader(f"📋 Assignments ({len(filtered_df)} records)")
            
            # Style the dataframe
            def highlight_status(row):
                if row['in_sent_at'] != '-' and row['out_sent_at'] != '-':
                    return ['background-color: #d4edda'] * len(row)
                elif row['in_sent_at'] != '-' or row['out_sent_at'] != '-':
                    return ['background-color: #fff3cd'] * len(row)
                else:
                    return ['background-color: #f8d7da'] * len(row)
            
            if not filtered_df.empty:
                st.dataframe(
                    filtered_df.style.apply(highlight_status, axis=1),
                    use_container_width=True,
                    hide_index=True,
                )
                
                # Legend
                st.markdown("**Legend:**")
                legend_col1, legend_col2, legend_col3 = st.columns(3)
                legend_col1.markdown("🟢 **Green** = Both IN & OUT sent")
                legend_col2.markdown("🟡 **Yellow** = Partially sent")
                legend_col3.markdown("🔴 **Red** = Not sent")
                
                # Download button
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"roster_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
            else:
                st.warning("No records match the selected filters.")
    
    # Tab 3: Statistics
    with tab3:
        st.header("📈 Statistics & Metrics")
        
        stats = get_stats()
        
        if stats:
            col1, col2, col3 = st.columns(3)
            
            col1.metric(
                "Total Assignments",
                stats.get("total_assignments", 0),
                help="Total number of unique assignments tracked"
            )
            col2.metric(
                "IN Events Sent",
                stats.get("in_events_sent", 0),
                help="Number of clock-IN events sent to NGRS"
            )
            col3.metric(
                "OUT Events Sent",
                stats.get("out_events_sent", 0),
                help="Number of clock-OUT events sent to NGRS"
            )
            
            st.markdown("---")
            
            # Calculate completion rate
            total = stats.get("total_assignments", 0)
            in_sent = stats.get("in_events_sent", 0)
            out_sent = stats.get("out_events_sent", 0)
            
            if total > 0:
                in_rate = (in_sent / total) * 100
                out_rate = (out_sent / total) * 100
                
                st.subheader("📊 Completion Rates")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Clock-IN Rate", f"{in_rate:.1f}%")
                    st.progress(in_rate / 100)
                
                with col2:
                    st.metric("Clock-OUT Rate", f"{out_rate:.1f}%")
                    st.progress(out_rate / 100)
        else:
            st.info("ℹ️ Unable to fetch statistics. Ensure the API is running.")
        
        st.markdown("---")
        
        # Database info
        st.subheader("💾 Database Information")
        if Path(DB_PATH).exists():
            db_size = Path(DB_PATH).stat().st_size
            st.info(f"📂 Database: `{DB_PATH}` ({db_size:,} bytes)")
        else:
            st.warning("⚠️ Database file not found. Run a simulation to create it.")
    
    # Tab 4: About
    with tab4:
        st.header("ℹ️ About Titus Simulator")
        
        st.markdown("""
        ### What is Titus Simulator?
        
        The Titus Simulator is a Python-based service that simulates time-attendance 
        clock-in and clock-out events for the NGRS backend.
        
        ### Features
        
        - 📥 **Roster Integration**: Fetches assignments from NGRS API
        - 🎲 **Event Simulation**: Generates realistic timing variations
        - 💾 **State Tracking**: SQLite database prevents duplicates
        - 🔄 **Auto Scheduling**: Background jobs run automatically
        - 🌐 **REST API**: Full API with interactive docs
        
        ### How It Works
        
        1. **Fetch Roster**: Gets scheduled deployments from NGRS
        2. **Generate Events**: Creates clock-in/out with timing variations
        3. **Check State**: Verifies what's already been sent
        4. **Send Events**: Posts new events to NGRS
        5. **Update State**: Marks events as sent in database
        
        ### Timing Variations
        
        Events are generated with realistic randomness:
        - **Clock-IN**: -5 to +10 minutes from planned start
        - **Clock-OUT**: -10 to +15 minutes from planned end
        
        ### API Endpoints
        
        - `GET /health` - Health check
        - `POST /run-once` - Manual trigger
        - `GET /stats` - Statistics
        - `GET /docs` - Interactive API documentation
        
        ### Tech Stack
        
        - **Python 3.11+**
        - **FastAPI** - REST framework
        - **SQLite** - State storage
        - **APScheduler** - Background jobs
        - **Streamlit** - This UI
        
        ### Links
        
        - 📚 [API Documentation](http://localhost:8000/docs)
        - 📖 [Usage Guide](../USAGE.md)
        - 🚀 [Getting Started](../GETTING_STARTED.md)
        
        ### Version
        
        **v0.1.0** - Initial Release
        """)
        
        st.markdown("---")
        
        # System info
        st.subheader("🔧 System Information")
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.markdown(f"""
            - **API Base URL**: `{API_BASE_URL}`
            - **Database Path**: `{DB_PATH}`
            - **Current Time**: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
            """)
        
        with info_col2:
            api_status = "🟢 Running" if check_api_health() else "🔴 Not Running"
            db_status = "🟢 Exists" if Path(DB_PATH).exists() else "🔴 Not Found"
            
            st.markdown(f"""
            - **API Status**: {api_status}
            - **Database**: {db_status}
            - **UI Framework**: Streamlit
            """)


if __name__ == "__main__":
    main()
