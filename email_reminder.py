"""
- generate emails to be sent to the testers and cc the product owner
- emails that will be sent are 60 days and 10 days before the maturity date
- email contains BATCH_ID, BATCH_NAME, MATURITY_DATE, NAME

Email Setup:
1. Go to this link
https://myaccount.google.com/apppasswords
2. Add in app name (Shelf Life Management System)
3. 16 character password generated. Add in as the 'EMAIL_PASSWORD'
4. Ensure the 'EMAIL_ADDRESS' used is the same as the email address used to logged in to generate the password.

Run this code without using an organisation's WiFi

Updated by: Shirlyn, 20/05/2025, 8.54a.m. 
"""

import smtplib
import os
from email.message import EmailMessage
import mysql.connector
from datetime import date
from collections import defaultdict
from dotenv import load_dotenv

# === Load environment variables ===
def load_db_config():
    load_dotenv()
    port_str = os.getenv('DB_PORT')
    return {
        'host': os.getenv('DB_HOST'),
        'port': int(port_str) if port_str and port_str.isdigit() else 3306,  # default to 3306 if not set
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }

# === Connect to MySQL ===
def connect_db(config):
    return mysql.connector.connect(**config)

# --- Query to fetch batches with maturity 60 or 10 days from today ---
def fetch_batches(cursor):
    query = """
    SELECT 
        t.test_id,
        a.name AS tester_name,
        a.email AS tester_email,
        b.batch_id,
        b.batch_name,
        b.maturity_date,
        b.product_owner_email
    FROM batch b
    JOIN tester t ON b.test_id = t.test_id
    JOIN account a ON t.tester_id = a.user_id
    WHERE DATE(b.maturity_date) = DATE_ADD(CURDATE(), INTERVAL 60 DAY)
       OR DATE(b.maturity_date) = DATE_ADD(CURDATE(), INTERVAL 10 DAY)
    ORDER BY t.test_id, b.maturity_date;
    """
    cursor.execute(query)
    return cursor.fetchall()

# --- Group batches by tester ---
def group_batches_by_tester(rows):
    testers = defaultdict(lambda: {"name": "", "email": "", "cc": set(), "batches": []})

    for row in rows:
        tid = row['test_id']
        maturity_date = row['maturity_date']
        days_left = (maturity_date.date() - date.today()).days
        label = f"{days_left} days left"

        testers[tid]["name"] = row['tester_name']
        testers[tid]["email"] = row['tester_email']
        testers[tid]["cc"].add(row['product_owner_email'])
        testers[tid]["batches"].append({
            "batch_id": row["batch_id"],
            "batch_name": row["batch_name"],
            "maturity_date": maturity_date.strftime('%Y-%m-%d'),
            "label": label
        })
    return testers

# --- Send grouped emails ---
def send_emails(testers, email_address, email_password):
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(email_address, email_password)

        for tester in testers.values():
            if not tester["email"]:
                continue  # skip if email is missing

            msg = EmailMessage()
            msg['Subject'] = "Upcoming Batch Maturity Reminders"
            msg['From'] = email_address
            msg['To'] = tester["email"]
            msg['Cc'] = ', '.join(tester["cc"])

            batch_list = "\n".join(
               f"- {b['batch_name']} (ID: {b['batch_id']}, Maturity: {b['maturity_date']} — {b['label']})"
                for b in tester["batches"]
            )

            msg.set_content(f"""Dear {tester['name']},

This is a reminder for the following batches that are approaching their maturity date:

{batch_list}

Please take the necessary actions.

Best regards,
Automated Notification System
""")

            smtp.send_message(msg)

def main():
    db_config = load_db_config()
    conn = connect_db(db_config)
    cursor = conn.cursor(dictionary=True)

    rows = fetch_batches(cursor)
    testers = group_batches_by_tester(rows)

    if not testers:
        print("No upcoming batches found. No emails sent.")
    else:
        # --- Email Setup ---
        EMAIL_ADDRESS = "summerpineapple4s26@gmail.com"
        EMAIL_PASSWORD = "cexm gbdo uhoo vnnn"  # replace with your app password or load from env

        send_emails(testers, EMAIL_ADDRESS, EMAIL_PASSWORD)
        print("Grouped emails sent.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
