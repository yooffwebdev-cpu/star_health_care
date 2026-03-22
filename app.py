from flask import Flask, render_template, request, jsonify, send_from_directory
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import os
from datetime import datetime
import psycopg2

app = Flask(__name__)

# Email configuration
SENDER_EMAIL = "sidhesh464@gmail.com"
SENDER_PASSWORD = "bisiypctvzdbmkjo"
RECIPIENT_EMAIL = "sidhesh464@gmail.com"

DATABASE_URL = "postgresql://star_care_user:BKjfJ7yGe08lwUymE3iuICFatoI3tCHG@dpg-d6vtcgma2pns73apvsig-a.singapore-postgres.render.com/star_care"

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Create tables if they don't exist."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
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
        cur.close()
        conn.close()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Database init error: {e}")

# Initialize DB on startup
init_db()

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
        conn = get_db_connection()
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
    try:
        print("START EMAIL FUNCTION")

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=25)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        print("LOGIN SUCCESS")

        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = "New Lead"

        body = f"Name: {name}, Phone: {phone}, Age: {age}"
        msg.attach(MIMEText(body, 'plain'))

        server.send_message(msg)
        server.quit()

        print("EMAIL SENT SUCCESS")

    except Exception as e:
        print("EMAIL ERROR:", e)

@app.route('/dashboard')
def dashboard():
    leads = []
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name, phone, age, timestamp FROM leads ORDER BY id DESC")
        leads = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error fetching leads: {e}")
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

        # Save lead to DB
        save_lead_to_db(name, phone, age, arrival_time)

        # Send email directly (Synchronous)
        # This is more reliable on Render's free tier than background threads,
        # ensuring the email finishes before the request completes.
        email_sent = True
        email_error = None
        try:
            send_email(name, phone, age)
        except Exception as e:
            email_sent = False
            email_error = str(e)
            print(f"[EMAIL ERROR] {e}")

        print(f"Lead saved. Email sent: {email_sent} for {name}.")
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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
