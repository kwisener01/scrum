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

# Backlog Management
st.header("Product Backlog")
with st.form("add_backlog_item"):
    task_name = st.text_input("Task Name")
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    story_points = st.number_input("Story Points", min_value=1, max_value=21, step=1)
    assigned_to = st.text_input("Assigned To")
    submit = st.form_submit_button("Add to Backlog")
    if submit and task_name:
        new_task = {"Task": task_name, "Priority": priority, "Story Points": story_points, "Assigned To": assigned_to, "Status": "Backlog"}
        st.session_state.backlog.append(new_task)
        backlog_ws.append_row([new_task["Task"], new_task["Priority"], new_task["Story Points"], new_task["Assigned To"], new_task["Status"]], table_range='A2')

# Display Backlog
if st.session_state.backlog:
    df_backlog = pd.DataFrame(st.session_state.backlog)
    st.dataframe(df_backlog)

# Sprint Planning
st.header("Sprint Planning")
sprint_name = st.text_input("Sprint Name")
sprint_duration = st.number_input("Sprint Duration (days)", min_value=1, max_value=30, step=1)
start_sprint = st.button("Start Sprint")

if start_sprint and sprint_name.strip():
    current_time = datetime.now(est)
    new_sprint = {
        "Sprint Name": sprint_name,
        "Start Date": str(current_time.date()),
        "End Date": str((current_time + timedelta(days=int(round(sprint_duration)))).date()),
        "Tasks": ""
    }
    st.session_state.sprints.append(new_sprint)
    sprint_ws.append_row([new_sprint["Sprint Name"], new_sprint["Start Date"], new_sprint["End Date"], new_sprint["Tasks"]])
    st.success(f"Sprint '{sprint_name}' started!")

# Assign Tasks to Sprint
if st.session_state.sprints:
    selected_sprint = st.selectbox("Select Sprint", [s["Sprint Name"] for s in st.session_state.sprints if "Sprint Name" in s and s["Sprint Name"].strip()] if st.session_state.sprints else ["No sprints available"])
    selected_task = st.selectbox(
    "Select Task from Backlog", 
    [task["Task"] for task in st.session_state.backlog if "Task" in task] if st.session_state.backlog else ["No tasks available"]
)
    assigned_person = next((task["Assigned To"] for task in st.session_state.backlog if task["Task"] == selected_task), "")
    assigned_person = st.text_input("Assign To (Enter Name)", assigned_person)
    
            assign_task = st.button("Assign Task to Sprint")
    
    if assign_task and selected_sprint and selected_task and assigned_person:
        for task in st.session_state.backlog:
            if task.get("Task") == selected_task:
                for sprint in st.session_state.sprints:
                    if sprint.get("Sprint Name") == selected_sprint:
                        sprint["Tasks"] += f"{selected_task} (Assigned to: {assigned_person}), "
                task["Status"] = "In Sprint"
        backlog_ws.update([list(t.values()) for t in st.session_state.backlog])
        sprint_ws.update('A2', [list(s.values()) for s in st.session_state.sprints])
        st.success(f"Task '{selected_task}' assigned to Sprint '{selected_sprint}' and assigned to '{assigned_person}'")
