import os
from time import strftime, localtime
import pytz
import re
import secrets
import streamlit as st
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash

# Initialize the database
db = SQL("sqlite:///coffee.db")
secret_key = 'Secret'
s = URLSafeTimedSerializer(secret_key)

# Helper Functions
def calculate_age(DOB):
    if DOB is None or DOB == '':
        return None
    b_date = datetime.strptime(DOB, '%Y-%m-%d')
    return (datetime.today() - b_date).days / 365

def sending_confirmation(username, email):
    token = s.dumps(email, salt='email-confirm-key')
    confirm_url = f'{st.get_option("server.baseUrlPath")}/confirm/{token}/{username}'
    st.info(f'Send confirmation link to {email} using this URL: {confirm_url}')

# Streamlit Functions
def register():
    st.title("Register")
    with st.form("register_form"):
        DOB = st.date_input("Birthday")
        email = st.text_input("Email")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirmation = st.text_input("Confirm Password", type="password")
        submit_button = st.form_submit_button("Register")

    if submit_button:
        age = calculate_age(DOB.strftime('%Y-%m-%d'))
        if age < 4:
            st.error("Must be at least 4 years old to register!")
        elif not username or len(username) < 3:
            st.error("Username must be at least 3 characters")
        elif not email:
            st.error("Must provide email")
        elif not password or password != confirmation or len(password) < 8:
            st.error("Password requirements not met")
        else:
            existing_user = db.execute("SELECT username FROM users WHERE username = :username", username=username)
            existing_email = db.execute("SELECT email FROM users WHERE email = :email", email=email)
            if existing_user:
                st.error("Username already exists")
            elif existing_email:
                st.error("Email already exists")
            else:
                db.execute("INSERT INTO users (username, hash, email, age) VALUES (:username, :hash, :email, :age)",
                           username=username, hash=generate_password_hash(password), email=email, age=age)
                st.success("You successfully registered! A confirmation link was sent to your email.")
                sending_confirmation(username, email)

def confirm_email(token, username):
    try:
        email = s.loads(token, salt="email-confirm-key", max_age=3600)
        db.execute("UPDATE email_confirmation SET confirmed = :confirmed WHERE user = :user", confirmed='TRUE', user=username)
        st.success("Email successfully confirmed!")
    except SignatureExpired:
        st.error("Your confirmation link has expired. Request a new one.")

def login():
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

    if submit_button:
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            st.error("Invalid username and/or password")
        else:
            st.session_state["user_id"] = rows[0]["id"]
            st.success("Logged in successfully!")

def lookup():
    st.title("Lookup Drinks")
    drink_chosen = st.selectbox("Choose a drink:", [row["Drink"] for row in db.execute("SELECT Drink FROM caffeine")])
    if drink_chosen:
        caffeine = db.execute("SELECT Caffeine_mg, fl_oz, mg_floz FROM caffeine WHERE Drink = :drink", drink=drink_chosen)
        st.write(f"{drink_chosen} contains {caffeine[0]['Caffeine_mg']} mg of caffeine per {caffeine[0]['fl_oz']} oz.")

def dashboard():
    if "user_id" not in st.session_state:
        st.warning("Please log in to access the dashboard.")
        return

    user_id = st.session_state["user_id"]
    st.title("Dashboard")

    daily_intake = db.execute(
        "SELECT Sum(Intake) as daily_intake FROM history WHERE user_id = :user_id AND date_added BETWEEN datetime('now', 'localtime', 'start of day') AND datetime('now', 'localtime')",
        user_id=user_id
    )
    st.write(f"Today's caffeine intake: {daily_intake[0]['daily_intake']} mg")

    weekly_intake = db.execute(
        "SELECT Sum(Intake) as weekly_intake FROM history WHERE user_id = :user_id AND date_added BETWEEN datetime('now', '-6 days', 'localtime') AND datetime('now', 'localtime')",
        user_id=user_id
    )
    if weekly_intake[0]['weekly_intake']:
        weekly_average_intake = int(weekly_intake[0]['weekly_intake'] / 7)
        st.write(f"Weekly average intake: {weekly_average_intake} mg")
    else:
        st.write("No intake recorded for this week.")

def profile():
    if "user_id" not in st.session_state:
        st.warning("Please log in to view your profile.")
        return

    user_id = st.session_state["user_id"]
    st.title("Profile")
    user_info = db.execute("SELECT firstname, lastname, weight, age FROM users WHERE id = :user_id", user_id=user_id)
    
    with st.form("profile_form"):
        firstname = st.text_input("First Name", value=user_info[0]["firstname"])
        lastname = st.text_input("Last Name", value=user_info[0]["lastname"])
        weight = st.number_input("Weight (kg)", value=user_info[0]["weight"])
        DOB = st.date_input("Birthday")
        unit = st.radio("Weight Unit", ("Kilograms", "Pounds"))
        
        submit_button = st.form_submit_button("Update Profile")
    
    if submit_button:
        age = calculate_age(DOB.strftime('%Y-%m-%d'))
        if unit == "Pounds":
            weight /= 2.205  # Convert pounds to kilograms
        db.execute("UPDATE users SET firstname = :firstname, lastname = :lastname, weight = :weight, age = :age WHERE id = :user_id",
                   firstname=firstname, lastname=lastname, weight=weight, age=age, user_id=user_id)
        st.success("Profile updated successfully!")

# Main app
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Register", "Login", "Dashboard", "Lookup", "Profile", "Confirm Email"])

if page == "Register":
    register()
elif page == "Login":
    login()
elif page == "Dashboard":
    dashboard()
elif page == "Lookup":
    lookup()
elif page == "Profile":
    profile()
elif page == "Confirm Email":
    token = st.sidebar.text_input("Enter token")
    username = st.sidebar.text_input("Enter username")
    if st.sidebar.button("Confirm"):
        confirm_email(token, username)
