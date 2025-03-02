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
3️⃣ Click **"Assign Task to Sprint"**.

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
    submit = st.form_submit_button("Add to Backlog")
    if submit and task_name:
        new_task = {"Task": task_name, "Priority": priority, "Story Points": story_points, "Status": "Backlog"}
        st.session_state.backlog.append(new_task)
        backlog_ws.append_row(list(new_task.values()))

# Display Backlog
if st.session_state.backlog:
    df_backlog = pd.DataFrame(st.session_state.backlog)
    st.dataframe(df_backlog)

# Sprint Planning
st.header("Sprint Planning")
sprint_name = st.text_input("Sprint Name")
sprint_duration = st.number_input("Sprint Duration (days)", min_value=1, max_value=30, step=1)
start_sprint = st.button("Start Sprint")

if start_sprint and sprint_name:
    current_time = datetime.now(est)
    new_sprint = {
        "Sprint Name": sprint_name,
        "Start Date": str(current_time.date()),
        "End Date": str((current_time + timedelta(days=int(round(sprint_duration)))).date()),
        "Tasks": ""
    }
    st.session_state.sprints.append(new_sprint)
    sprint_ws.append_row(list(new_sprint.values()))
    st.success(f"Sprint '{sprint_name}' started!")

# Assign Tasks to Sprint
if st.session_state.sprints:
    selected_sprint = st.selectbox(
    "Select Sprint", 
    [s.get("Sprint Name", "Unnamed Sprint") for s in st.session_state.sprints] if st.session_state.sprints else ["No sprints available"]
)
    selected_task = st.selectbox(
    "Select Task from Backlog", 
    [task.get("Task", "Unnamed Task") for task in st.session_state.backlog] if st.session_state.backlog else ["No tasks available"]
)
    assign_task = st.button("Assign Task to Sprint")
    
    if assign_task and selected_sprint and selected_task:
        for task in st.session_state.backlog:
            if task.get("Task") == selected_task:
                for sprint in st.session_state.sprints:
                    if sprint.get("Sprint Name") == selected_sprint:
                        sprint["Tasks"] += selected_task + ", "
                task["Status"] = "In Sprint"
        backlog_ws.update([list(t.values()) for t in st.session_state.backlog])
        sprint_ws.update([list(s.values()) for s in st.session_state.sprints])
        st.success(f"Task '{selected_task}' assigned to Sprint '{selected_sprint}'")

# Display Sprint Details
st.header("Sprint Overview")
for sprint in st.session_state.sprints:
    sprint_name = sprint.get("Sprint Name", "Unnamed Sprint")
    start_date = sprint.get("Start Date", "Unknown Start")
    end_date = sprint.get("End Date", "Unknown End")
    tasks = sprint.get("Tasks", "No tasks assigned")
    
    st.subheader(sprint_name)
    st.write(f"Start: {start_date}, End: {end_date}")
    st.write(f"Tasks: {tasks}")

# AI-Powered Sprint Suggestions
st.header("AI Sprint Suggestions")
if st.session_state.sprints:
    sprint_velocity = [len(s.get("Tasks", "").split(", ")) for s in st.session_state.sprints]
    avg_velocity = sum(sprint_velocity) / len(sprint_velocity) if sprint_velocity else 0
    st.write(f"Based on past sprints, the average velocity is {avg_velocity:.2f} tasks per sprint.")
    
    suggested_tasks = avg_velocity  # Suggest assigning a similar number of tasks
    st.write(f"For the next sprint, consider selecting around {int(suggested_tasks)} tasks.")
else:
    st.write("Not enough sprint data available for suggestions.")

# Burndown Chart
st.header("Sprint Burndown Chart")
if st.session_state.sprints:
    import matplotlib.pyplot as plt
    
    sprint_dates = [s.get("Start Date", "") for s in st.session_state.sprints]
    sprint_tasks = [len(s.get("Tasks", "").split(", ")) for s in st.session_state.sprints]
    
    fig, ax = plt.subplots()
    ax.plot(sprint_dates, sprint_tasks, marker='o', linestyle='-')
    ax.set_xlabel("Sprint Date")
    ax.set_ylabel("Remaining Tasks")
    ax.set_title("Sprint Burndown Chart")
    st.pyplot(fig)
else:
    st.write("No sprint data available for a burndown chart.")
