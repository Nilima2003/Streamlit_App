import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta

# ---------------- CONFIG ----------------
DB_CONFIG = {
    "host": "sql12.freesqldatabase.com",
    "user": "sql12808805",
    "password": "6lsT8QsmSh",
    "database": "sql12808805",
    "port": 3306
}

# ---------------- DB CONNECTION ----------------
def get_db_connection(use_database=True):
    params = {
        "host": DB_CONFIG["host"],
        "user": DB_CONFIG["user"],
        "password": DB_CONFIG["password"],
        "port": DB_CONFIG["port"],
        "auth_plugin": "mysql_native_password"
    }
    if use_database:
        params["database"] = DB_CONFIG["database"]
    return mysql.connector.connect(**params)

# ---------------- DB + TABLE CREATION ----------------
def ensure_database_and_tables():
    try:
        conn = get_db_connection(use_database=False)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.close()
        conn.close()
    except Error as e:
        st.error(f"Error creating DB: {e}")
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE,
                email VARCHAR(100),
                contact_no VARCHAR(20),
                password VARCHAR(255)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50),
                date DATE,
                task_assigned_by VARCHAR(50),
                work_assignment VARCHAR(50),
                assigned_to_person VARCHAR(100),
                task_description TEXT,
                work_done_today TEXT,
                task_status VARCHAR(30),
                work_plan_next_day TEXT,
                expense_purpose VARCHAR(255),
                other_purpose VARCHAR(255),
                amount FLOAT
            );
        """)

        conn.commit()
        cursor.close()
        conn.close()

    except Error as e:
        st.error(f"Error creating tables: {e}")


ensure_database_and_tables()

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "expense" not in st.session_state:
    st.session_state.expense = {
        "travelling": False, "travelling_amt": 0.0,
        "mobile": False, "mobile_amt": 0.0,
        "food": False, "food_amt": 0.0,
        "other": False, "other_amt": 0.0, "other_purpose": "",
        "none": False
    }

# ---------------- REGISTER USER ----------------
def register_user(username, email, contact_no, password):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return False, "Username already exists!"

        cursor.execute("""
            INSERT INTO users (username, email, contact_no, password)
            VALUES (%s, %s, %s, %s)
        """, (username, email, contact_no, password))

        conn.commit()
        cursor.close()
        conn.close()
        return True, "Registration successful!"

    except Error as e:
        return False, f"Database error: {e}"

# ---------------- LOGIN ----------------
def login_user(username, password):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM users
            WHERE username=%s AND password=%s
        """, (username, password))

        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return bool(user)

    except Error:
        return False

# ---------------- LOAD TASKS ----------------
def load_tasks(username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT username, date, task_assigned_by, work_assignment, assigned_to_person,
                   task_description, work_done_today, task_status, work_plan_next_day,
                   expense_purpose, other_purpose, amount
            FROM tasks
            WHERE username=%s
        """, (username,))

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        df = pd.DataFrame(rows, columns=[
            "username", "date", "task_assigned_by", "work_assignment", "assigned_to_person",
            "task_description", "work_done_today", "task_status", "work_plan_next_day",
            "expense_purpose", "other_purpose", "amount"
        ])

        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])

        return df

    except Error:
        return pd.DataFrame()

# ---------------- SAVE TASK ----------------
def append_task(row):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tasks (
                username, date, task_assigned_by, work_assignment, assigned_to_person,
                task_description, work_done_today, task_status, work_plan_next_day,
                expense_purpose, other_purpose, amount
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row["username"], row["date"], row["task_assigned_by"], row["work_assignment"],
            row["assigned_to_person"], row["task_description"], row["work_done_today"],
            row["task_status"], row["work_plan_next_day"], row["expense_purpose"],
            row["other_purpose"], row["amount"]
        ))

        conn.commit()
        cursor.close()
        conn.close()

    except Error as e:
        st.error(f"Error saving task: {e}")

# ---------------- SIDEBAR ----------------
st.sidebar.title("Menu")

if st.session_state.logged_in:
    st.sidebar.success(f"Logged in as **{st.session_state.username}**")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    page = st.sidebar.radio("Navigate", ["Dashboard", "Add Task"])

else:
    page = st.sidebar.radio("Navigate", ["Login", "Register"])

# ---------------- REGISTER PAGE ----------------
if page == "Register":
    st.title("Register")

    with st.form("regform"):
        u = st.text_input("Username")
        e = st.text_input("Email")
        c = st.text_input("Contact No")
        p = st.text_input("Password", type="password")

        reg_btn = st.form_submit_button("Register")

        if reg_btn:
            ok, msg = register_user(u, e, c, p)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

# ---------------- LOGIN PAGE ----------------
elif page == "Login":
    st.title("Login")

    with st.form("loginform"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        log_btn = st.form_submit_button("Login")

        if log_btn:
            if login_user(u, p):
                st.session_state.logged_in = True
                st.session_state.username = u
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid login details!")

# ---------------- DASHBOARD ----------------
elif page == "Dashboard":
    st.title("Dashboard")

    df = load_tasks(st.session_state.username)

    total_tasks = len(df)
    total_expense = 0.0

    if "amount" in df.columns and not df.empty:
        total_expense = pd.to_numeric(df["amount"], errors="coerce").fillna(0).sum()

    col1, col2 = st.columns(2)
    col1.metric("Total Tasks", total_tasks)
    col2.metric("Total Expense", f"₹{total_expense:.2f}")

    st.subheader("Recent Tasks")

    if df.empty:
        st.info("No tasks found.")

    else:
        last_30 = datetime.now() - timedelta(days=30)

        if "date" in df.columns:
            recent = df[df["date"] >= last_30]
        else:
            recent = df

        if recent.empty:
            st.info("No recent tasks.")
        else:
            for _, t in recent.sort_values("date", ascending=False).iterrows():
                date_str = t["date"].strftime("%Y-%m-%d") if pd.notna(t["date"]) else ""
                st.write("###", date_str)
                st.write("Assigned By:", t.get("task_assigned_by", ""))
                st.write("Task:", t.get("task_description", ""))
                st.write("Work Done:", t.get("work_done_today", ""))
                st.write("Status:", t.get("task_status", ""))
                st.write("Next Day:", t.get("work_plan_next_day", ""))
                amt = t.get("amount", 0)
                exp_purp = t.get("expense_purpose", "")
                st.write(f"Expense: ₹{amt} ({exp_purp})")
                st.divider()

# ---------------- ADD TASK PAGE ----------------
elif page == "Add Task":
    st.title("Add Task & Expense")

    e = st.session_state.expense

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        e["travelling"] = st.checkbox("Travelling", value=e.get("travelling", False))
    with col2:
        e["mobile"] = st.checkbox("Mobile", value=e.get("mobile", False))
    with col3:
        e["food"] = st.checkbox("Food", value=e.get("food", False))
    with col4:
        e["other"] = st.checkbox("Other", value=e.get("other", False))

    e["none"] = st.checkbox("No Expense", value=e.get("none", False))

    if e["none"]:
        e["travelling"] = e["mobile"] = e["food"] = e["other"] = False
        e["travelling_amt"] = e["mobile_amt"] = e["food_amt"] = e["other_amt"] = 0

    if e["travelling"]:
        e["travelling_amt"] = st.number_input("Travelling Amount", value=e.get("travelling_amt", 0.0))

    if e["mobile"]:
        e["mobile_amt"] = st.number_input("Mobile Amount", value=e.get("mobile_amt", 0.0))

    if e["food"]:
        e["food_amt"] = st.number_input("Food Amount", value=e.get("food_amt", 0.0))

    if e["other"]:
        e["other_amt"] = st.number_input("Other Amount", value=e.get("other_amt", 0.0))
        e["other_purpose"] = st.text_input("Other Purpose", value=e.get("other_purpose", ""))

    total = (
        float(e.get("travelling_amt", 0)) +
        float(e.get("mobile_amt", 0)) +
        float(e.get("food_amt", 0)) +
        float(e.get("other_amt", 0))
    )

    st.text_input("Total Expense", value=str(total), disabled=True)

    st.subheader("Task Details")

    with st.form("taskform"):
        date = st.date_input("Date", datetime.now())
        assigned_by = st.text_input("Assigned By")
        work_assign = st.selectbox("Assignment", ["", "self", "other"])
        assigned_to = ""

        if work_assign == "other":
            assigned_to = st.text_input("Assigned To")

        desc = st.text_area("Task Description")
        done = st.text_area("Work Done Today")
        status = st.selectbox("Status", ["", "pending", "in_progress", "completed"])
        next_day = st.text_area("Next Day Plan")

        save_btn = st.form_submit_button("Save Task")

        if save_btn:

            if e["none"]:
                exp_purpose = "none"
                other_purpose = ""
                amount = 0.0

            else:
                tags = []
                if e["travelling"]: tags.append("travelling")
                if e["mobile"]: tags.append("mobile")
                if e["food"]: tags.append("food")
                if e["other"]: tags.append("other")

                exp_purpose = ", ".join(tags)
                other_purpose = e.get("other_purpose", "")
                amount = float(total)

            row = {
                "username": st.session_state.username,
                "date": date.strftime("%Y-%m-%d"),
                "task_assigned_by": assigned_by,
                "work_assignment": work_assign,
                "assigned_to_person": assigned_to,
                "task_description": desc,
                "work_done_today": done,
                "task_status": status,
                "work_plan_next_day": next_day,
                "expense_purpose": exp_purpose,
                "other_purpose": other_purpose,
                "amount": amount
            }

            append_task(row)
            st.success("Task saved successfully!")
