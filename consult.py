import streamlit as st
import pandas as pd
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

BOOKING_FILE = "bookings.xlsx"

# ---------- Load Secrets from Streamlit Cloud ----------
# (set these in Streamlit → Settings → Secrets)
ADMIN_EMAIL = st.secrets["ADMIN_EMAIL"]
ADMIN_PASSWORD = st.secrets["EMAIL_PASS"]

# ---------- Utility: Load or Create Excel ----------
def load_bookings():
    if os.path.exists(BOOKING_FILE):
        return pd.read_excel(BOOKING_FILE)
    else:
        return pd.DataFrame(columns=["Name", "University", "Email", "Application Type", 
                                     "Destination Country", "Date", "Time Slot"])

def save_booking(df):
    df.to_excel(BOOKING_FILE, index=False)

# ---------- Utility: Send Email ----------
def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg["From"] = ADMIN_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(ADMIN_EMAIL, ADMIN_PASSWORD)
        server.send_message(msg)

# ---------- Streamlit UI ----------
st.title("📅 University Application Booking")

# User Input
name = st.text_input("Name")
university = st.text_input("University")
email = st.text_input("Email")
app_type = st.selectbox("Application Type", ["Bachelor", "Masters"])
destination = st.text_input("Desired Destination Country")

# Calendar input
date = st.date_input("Select a Date")
time_slots = ["10:00 - 11:00", "11:00 - 12:00", "14:00 - 15:00", "15:00 - 16:00"]
bookings = load_bookings()

# Show available vs booked slots
st.subheader("Available Slots")
for slot in time_slots:
    if ((bookings["Date"] == pd.to_datetime(date)) & (bookings["Time Slot"] == slot)).any():
        st.markdown(f"🔴 {slot} (Booked)")
    else:
        st.markdown(f"🟢 {slot} (Available)")

slot_choice = st.selectbox("Select Time Slot", time_slots)

# Booking button
if st.button("Confirm Booking"):
    if ((bookings["Date"] == pd.to_datetime(date)) & (bookings["Time Slot"] == slot_choice)).any():
        st.error("❌ This slot is already booked!")
    else:
        new_entry = pd.DataFrame([[name, university, email, app_type, destination, date, slot_choice]],
                                 columns=bookings.columns)
        bookings = pd.concat([bookings, new_entry], ignore_index=True)
        save_booking(bookings)

        # Prepare emails
        body_user = f"Hi {name},\n\nYour booking is confirmed:\nDate: {date}\nTime: {slot_choice}\n\nRegards,\nAdmin"
        body_admin = f"New booking:\n\nName: {name}\nUniversity: {university}\nEmail: {email}\nType: {app_type}\nDestination: {destination}\nDate: {date}\nSlot: {slot_choice}"
        
        try:
            send_email(email, "Booking Confirmation", body_user)
            send_email(ADMIN_EMAIL, "New Booking Alert", body_admin)
            st.success("✅ Booking confirmed and emails sent!")
        except Exception as e:
            st.warning(f"Booking saved, but email failed: {e}")
