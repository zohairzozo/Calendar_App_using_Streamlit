import streamlit as st
import pandas as pd
import requests
import datetime
import os
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

# EmailJS configuration (replace with your own)
SENDGRID_API_KEY = st.secrets["sendgrid"]["api_key"] # Replace with your SendGrid API Key
ADMIN_EMAIL = "shehzadzohair@gmail.com"
# Accessing the admin password securely from Streamlit's secrets
ADMIN_PASSWORD = st.secrets["general"]["admin_password"]
EXCEL_FILE = "appointments.xlsx"

# Define slot logic
SLOTS = {
    0: [  # Monday
        "18:00", "18:30", "19:00", "19:30"
    ],
    1: [  # Tuesday
        "16:00", "16:30", "17:00", "17:30"
    ],
    5: [  # Saturday
        "13:00", "13:30", "14:00", "14:30"
    ],
    6: [  # Sunday
        "13:00", "13:30", "14:00", "14:30"
    ]
}

def save_appointment(data):
    df_new = pd.DataFrame([data])
    if os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
        df = pd.concat([df, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_excel(EXCEL_FILE, index=False)
    
# Function to send email using SendGrid
def send_email_sendgrid(to_email, subject, message):
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    from_email = Email("zohair.ahmedshahzad@gmail.com")  # Replace with a valid email
    to_email = To(to_email)
    content = Content("text/plain", message)
    mail = Mail(from_email, to_email, subject, content)

    try:
        response = sg.send(mail)
        if response.status_code == 202:
            st.success("Email sent successfully!")
            return True
        else:
            st.error(f"Failed to send email. Status Code: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return False

def admin_page():
    st.header("Admin - All Appointments")
    password = st.text_input("Enter admin password", type="password")
    if password == ADMIN_PASSWORD:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            st.dataframe(df)
        else:
            st.info("No appointments yet!")
    else:
        st.warning("Enter the correct password to view appointments.")

def booking_page():
    st.header("Book an Appointment")

    today = datetime.date.today()
    date = st.date_input("Select a Date", min_value=today)
    weekday = date.weekday()
    slots = SLOTS.get(weekday, [])

    st.write(f"Selected date: {date}, weekday: {weekday}")

    submitted = False
    
    if slots:
        time = st.selectbox("Available Time Slots", slots)
        with st.form("booking_form"):
            name = st.text_input("Your Name")
            email = st.text_input("Your Email")
            reason = st.text_area("Reason for Appointment")
            submitted = st.form_submit_button("Book Appointment")

            if submitted:
                appointment = {
                    "Name": name,
                    "Email": email,
                    "Date": str(date),
                    "Time": time,
                    "Reason": reason
                }
                save_appointment(appointment)
                
                message = f"Booking Details:\nName: {name}\nEmail: {email}\nDate: {date}\nTime: {time}\nReason: {reason}"
                
                # Send email to the user using SendGrid API
                if send_email_sendgrid(email, "Appointment Confirmation", message):
                    st.success("Appointment booked! Confirmation sent to your email.")
                
                # Send email to the admin using SendGrid API
                if send_email_sendgrid(ADMIN_EMAIL, "New Appointment Booking", message):
                    st.success("Admin has been notified.")
                else:
                    st.error("Failed to notify admin via email.")
    else:
        st.warning("No sessions available for the selected day. Please pick Monday, Tuesday, Saturday, or Sunday.")

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Book Appointment", "Admin"])
    if page == "Book Appointment":
        booking_page()
    else:
        admin_page()

if __name__ == "__main__":
    main()