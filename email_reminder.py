"""
- generate emails to be sent to the testers of  and cc the product owner
- emails that will be sent are 60 days and 10 days before the maturity date
- email contains BATCH_ID, BATCH_NAME, MATURITY_DATE, NAME

Email Setup:
1. Go to this link
https://myaccount.google.com/apppasswords
2. Add in app name (Shelf Life Management System)
3. 16 character password generated. Add in as the 'EMAIL_PASSWORD'
4. Ensure the 'EMAIL_ADDRESS' used is the same as the email address used to logged in to generate the password.

Run this code without using an organisation's WiFi

Updated by: Shirlyn, 17/05/2025, 3.12p.m. 
"""


import smtplib
import os
from email.message import EmailMessage
import mysql.connector
from datetime import datetime, date
from collections import defaultdict
from dotenv import load_dotenv

# === Load environment variables ===
load_dotenv()

port_str = os.getenv('DB_PORT')
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(port_str) if port_str and port_str.isdigit() else 3306,  # default to 3306 if not set
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# === Connect to MySQL ===
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

# --- Query ---
cursor.execute("""
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
""")
rows = cursor.fetchall()

# --- Group batches by tester ---
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

if not testers:
    print("No upcoming batches found. No emails sent.")
else:
    # --- Email Setup ---
    EMAIL_ADDRESS = "summerpineapple4s26@gmail.com"
    EMAIL_PASSWORD = "cexm gbdo uhoo vnnn" 

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        for tester in testers.values():
            if not tester["email"]:
                continue  # skip if email is missing

            msg = EmailMessage()
            msg['Subject'] = "Upcoming Batch Maturity Reminders"
            msg['From'] = EMAIL_ADDRESS
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

    print("Grouped emails sent.")
