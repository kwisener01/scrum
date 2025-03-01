import streamlit as st
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
    [task["Task"] for task in st.session_state.backlog] if st.session_state.backlog else ["No tasks available"]
)
    assign_task = st.button("Assign Task to Sprint")
    
    if assign_task and selected_sprint and selected_task:
        for task in st.session_state.backlog:
            if task["Task"] == selected_task:
                for sprint in st.session_state.sprints:
                    if sprint["Sprint Name"] == selected_sprint:
                        sprint["Tasks"] += selected_task + ", "
                task["Status"] = "In Sprint"
        backlog_ws.update([list(t.values()) for t in st.session_state.backlog])
        sprint_ws.update([list(s.values()) for s in st.session_state.sprints])
        st.success(f"Task '{selected_task}' assigned to Sprint '{selected_sprint}'")

# Display Sprint Details
st.header("Sprint Overview")
for sprint in st.session_state.sprints:
    st.subheader(sprint["Sprint Name"])
    st.write(f"Start: {sprint['Start Date']}, End: {sprint['End Date']}")
    st.write(f"Tasks: {sprint['Tasks']}")

# Placeholder for AI Sprint Suggestions (To be implemented later)
