from flask import Flask, render_template, request, jsonify, send_from_directory
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import threading
import json
import os
from datetime import datetime
import psycopg2

app = Flask(__name__)

# Email configuration
SENDER_EMAIL = "sidhesh464@gmail.com"
SENDER_PASSWORD = "bisiypctvzdbmkjo"
RECIPIENT_EMAIL = "sidhesh464@gmail.com"

DATABASE_URL = "postgresql://star_care_user:BKjfJ7yGe08lwUymE3iuICFatoI3tCHG@dpg-d6vtcgma2pns73apvsig-a.singapore-postgres.render.com/star_care"
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Create leads table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    name TEXT,
    phone TEXT,
    age TEXT,
    timestamp TEXT
)
""")
conn.commit()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(app.static_folder, 'sitemap.xml')

def save_lead_to_db(name, phone, age, timestamp):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO leads (name, phone, age, timestamp) VALUES (%s, %s, %s, %s)",
            (name, phone, age, timestamp)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error saving lead to database: {e}")
        raise e

def send_email(name, phone, age):
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{start_time}] Attempting to send email for {name}...")

    subject = f"New Lead: {name}"
    body = f"NEW LEAD RECEIVED\n\nName: {name}\nPhone: {phone}\nAge: {age}\nTime: {start_time}"

    server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server.send_message(msg)
    server.quit()

    done_time = datetime.now().strftime("%H:%M:%S")
    print(f"[{done_time}] Email successfully sent for {name}")

@app.route('/dashboard')
def dashboard():
    leads = []
    try:
        conn_dash = psycopg2.connect(DATABASE_URL)
        cur_dash = conn_dash.cursor()
        cur_dash.execute("SELECT name, phone, age, timestamp FROM leads ORDER BY id DESC")
        leads = cur_dash.fetchall()
        cur_dash.close()
        conn_dash.close()
    except Exception as e:
        print(f"Error fetching leads from database: {e}")
        leads = []
    today_date = datetime.now().strftime("%Y-%m-%d")
    return render_template('dashboard.html', leads=leads, todaydate=today_date)

@app.route('/submit_lead', methods=['POST'])
def submit_lead():
    try:
        arrival_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Processing lead at {arrival_time}")

        if not request.is_json:
            return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Empty lead data"}), 400

        name = data.get('name')
        phone = data.get('phone')
        age = data.get('age')

        if not all([name, phone, age]):
            return jsonify({"status": "error", "message": "All fields are required"}), 400

        # Save lead to DB first
        save_lead_to_db(name, phone, age, arrival_time)

        # Send email SYNCHRONOUSLY — Render free tier kills background threads
        # before SMTP can complete, so we must wait for it here
        email_sent = True
        email_error = None
        try:
            send_email(name, phone, age)
        except Exception as e:
            email_sent = False
            email_error = str(e)
            print(f"[EMAIL ERROR] {e}")

        finish_time = datetime.now().strftime("%H:%M:%S")
        print(f"Lead saved at {finish_time}. Email sent: {email_sent}")

        return jsonify({
            "status": "success",
            "message": "Lead submitted successfully",
            "email_sent": email_sent,
            "email_error": email_error
        })

    except Exception as e:
        print(f"Critical Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Use Waitress for production server on Windows
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
