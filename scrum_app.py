import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from datetime import date, datetime, timedelta
import gspread
import pytz
from google.oauth2.service_account import Credentials

# Ensure timedelta is correctly recognized
from datetime import timedelta

# Google Sheets setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# Load credentials from Streamlit Secrets
credentials = Credentials.from_service_account_info(st.secrets["google_sheets"], scopes=scope)

# Authorize gspread
client = gspread.authorize(credentials)

# Set timezone to EST (Eastern Standard Time)
est = pytz.timezone("US/Eastern")
sheet = client.open("scrum")

# Define worksheets outside of session state checks to ensure they are always accessible
backlog_ws = sheet.worksheet("Backlog")
sprint_ws = sheet.worksheet("Sprints")

# Initialize session state for backlog and sprints
if 'backlog' not in st.session_state:
    st.session_state.backlog = backlog_ws.get_all_records()
if 'sprints' not in st.session_state:
    st.session_state.sprints = sprint_ws.get_all_records()

st.set_page_config(page_title="Scrum Project Management", layout="wide")

# Sidebar How-To Guide
st.sidebar.title("How To Use This App")
st.sidebar.markdown("""
### Step 1: Populate the Backlog
1️⃣ Go to the **Product Backlog** section.
2️⃣ Enter **Task Name**.
3️⃣ Choose a **Priority** (High, Medium, Low).
4️⃣ Define **Story Points** (effort estimate).
5️⃣ Click **"Add to Backlog"**.

### Step 2: Create a Sprint
1️⃣ Navigate to **Sprint Planning**.
2️⃣ Enter a **Sprint Name**.
3️⃣ Set a **Sprint Duration** (e.g., 2 weeks).
4️⃣ Click **"Start Sprint"**.

### Step 3: Assign Tasks to the Sprint
1️⃣ Select a **Sprint** from the dropdown.
2️⃣ Select a **Task** from the backlog.
3️⃣ Select a **Person to Assign** the task to.
4️⃣ Click **"Assign Task to Sprint"**.

### Step 4: Track Progress
1️⃣ View active sprints under **Sprint Overview**.
2️⃣ Update tasks as they are completed.

### Step 5: Complete the Sprint
1️⃣ Conduct a **Sprint Review** (show progress).
2️⃣ Conduct a **Sprint Retrospective** (improve future sprints).
3️⃣ Move unfinished tasks to the next sprint.

### Best Practices for Scrum Success
✅ **Keep Sprints Short** (1-4 weeks).
✅ **Prioritize High-Value Tasks First**.
✅ **Hold Daily Standups to Remove Blockers**.
✅ **Update Backlog and Sprint Progress Regularly**.
✅ **Retrospectives Improve Process Efficiency**.
""")

st.title("Scrum Project Management App")

# Daily Sprint Report
st.header("Daily Sprint Report")

# Track Task Completion Status (On Time, Early, Late)
if st.session_state.sprints:
    sprint_data = pd.DataFrame(st.session_state.sprints)
    sprint_data["End Date"] = pd.to_datetime(sprint_data["End Date"], errors='coerce')
    sprint_data["Actual Close Date"] = pd.to_datetime(sprint_data.get("Actual Close Date", None), errors='coerce')
    today = datetime.now(est).date()
    
    def task_status(row):
        if pd.notna(row["Actual Close Date"]):
            if row["Actual Close Date"].date() <= row["End Date"].date():
                return "Closed On Time"
            else:
                return "Closed Late"
        elif row["End Date"].date() > today:
            return "On Track"
        elif row["End Date"].date() == today:
            return "On Time"
        else:
            return "Late"
    
    sprint_data["Status"] = sprint_data.apply(task_status, axis=1)
    sprint_data["Actual Close Date"] = sprint_data["Actual Close Date"].dt.strftime('%Y-%m-%d')
    st.dataframe(sprint_data[["Sprint Name", "Start Date", "End Date", "Actual Close Date", "Status"]])

    # Allow user to update actual close date
    with st.form("update_close_date"):
        selected_sprint = st.selectbox("Select Sprint to Close", sprint_data["Sprint Name"].unique())
        actual_close_date = st.date_input("Actual Close Date", value=datetime.now(est).date())
        close_sprint = st.form_submit_button("Update Close Date")
        
        if close_sprint:
            for sprint in st.session_state.sprints:
                if sprint["Sprint Name"] == selected_sprint:
                    sprint["Actual Close Date"] = str(actual_close_date)
            sprint_ws.update('A2', [list(s.values()) for s in st.session_state.sprints])
            st.success(f"Sprint '{selected_sprint}' closed on {actual_close_date}!")
