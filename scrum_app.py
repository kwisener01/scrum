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

### Step 5: Complete the Sprint and Tasks
1️⃣ Conduct a **Sprint Review** (show progress).
2️⃣ Conduct a **Sprint Retrospective** (improve future sprints).
3️⃣ Move unfinished tasks to the next sprint.
4️⃣ Close completed tasks.

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

# Sprint Statistics and Burndown Chart
if st.session_state.sprints:
    sprint_data = pd.DataFrame(st.session_state.sprints)
    sprint_data["End Date"] = pd.to_datetime(sprint_data["End Date"], errors='coerce')
    today = datetime.now(est).date()
    
    # Calculate completion rate
    total_tasks = sum([len(sprint["Tasks"].split(", ")) for sprint in st.session_state.sprints if sprint["Tasks"]])
    completed_tasks = sum([len([t for t in sprint["Tasks"].split(", ") if "(Completed)" in t]) for sprint in st.session_state.sprints if sprint["Tasks"]])
    completion_rate = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
    st.metric("Completion Rate", f"{completion_rate:.2f}%")
    
    # Burndown Chart
    sprint_dates = [sprint["Start Date"] for sprint in st.session_state.sprints]
    task_counts = [len(sprint["Tasks"].split(", ")) for sprint in st.session_state.sprints if sprint["Tasks"]]
    
    fig, ax = plt.subplots()
    ax.plot(sprint_dates, task_counts, marker='o', linestyle='-', label='Remaining Tasks')
    ax.set_xlabel("Sprint Start Date")
    ax.set_ylabel("Number of Tasks")
    ax.set_title("Sprint Burndown Chart")
    ax.legend()
    st.pyplot(fig)
else:
    st.write("No sprint data available.")

# AI-Powered Sprint Suggestions
st.header("AI Sprint Suggestions")
if st.session_state.sprints:
    sprint_velocity = [len(sprint["Tasks"].split(", ")) for sprint in st.session_state.sprints if sprint["Tasks"]]
    avg_velocity = sum(sprint_velocity) / len(sprint_velocity) if sprint_velocity else 0
    st.write(f"Based on past sprints, the average velocity is {avg_velocity:.2f} tasks per sprint.")
    suggested_tasks = avg_velocity  # Suggest assigning a similar number of tasks
    st.write(f"For the next sprint, consider selecting around {int(suggested_tasks)} tasks.")
else:
    st.write("Not enough sprint data available for suggestions.")

# Track Task and Sprint Completion Status
if st.session_state.sprints:
    sprint_data = pd.DataFrame(st.session_state.sprints)
    sprint_data["End Date"] = pd.to_datetime(sprint_data["End Date"], errors='coerce')
    if "Actual Close Date" in sprint_data.columns:
        sprint_data["Actual Close Date"] = pd.to_datetime(sprint_data["Actual Close Date"], errors='coerce')
    else:
        sprint_data["Actual Close Date"] = None
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
    if sprint_data["Actual Close Date"].notna().any():
        sprint_data["Actual Close Date"] = sprint_data["Actual Close Date"].dt.strftime('%Y-%m-%d')
    else:
        sprint_data["Actual Close Date"] = ""
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

# Task Completion Feature
st.header("Task Completion")
if st.session_state.backlog:
    backlog_data = pd.DataFrame(st.session_state.backlog)
    with st.form("close_task"):
        selected_task = st.selectbox("Select Task to Close", backlog_data["Task"].unique() if "Task" in backlog_data.columns else [])
        close_task = st.form_submit_button("Mark Task as Completed")
        
        if close_task:
            for task in st.session_state.backlog:
                if task["Task"] == selected_task:
                    task["Status"] = "Completed"
            backlog_ws.update('A2', [list(t.values()) for t in st.session_state.backlog])
            st.success(f"Task '{selected_task}' marked as Completed!")
