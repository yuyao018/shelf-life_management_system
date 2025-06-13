
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

Updated by: Shirlyn, 06/06/2025, 10.28a.m. 
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
        'port': int(port_str) if port_str and port_str.isdigit() else 3306, # default to 3306 if not set
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }

# === Connect to MySQL ===
def connect_db(config):
    return mysql.connector.connect(**config)

# === Fetch all admin emails ===
def fetch_admin_emails(cursor):
    cursor.execute("SELECT email FROM account WHERE role = 'admin'")
    return [row['email'] for row in cursor.fetchall()]

# === Fetch batches with maturity 60 or 10 days from today ===
def fetch_batches(cursor):
    query = """
    SELECT 
        a.name AS tester_name,
        a.email AS tester_email,
        b.batch_id,
        b.batch_name,
        b.maturity_date
    FROM batch b
    JOIN tester t ON b.test_id = t.test_id
    JOIN account a ON t.tester_id = a.user_id
    WHERE DATE(b.maturity_date) = DATE_ADD(CURDATE(), INTERVAL 60 DAY)
       OR DATE(b.maturity_date) = DATE_ADD(CURDATE(), INTERVAL 10 DAY)
    ORDER BY a.email, b.maturity_date;
    """
    cursor.execute(query)
    return cursor.fetchall()

# === Group batches by tester email ===
def group_batches_by_tester(rows, admin_emails):
    testers = defaultdict(lambda: {"name": "", "email": "", "cc": set(), "batches": []})

    for row in rows:
        tester_email = row['tester_email']
        maturity_date = row['maturity_date']
        days_left = (maturity_date.date() - date.today()).days
        label = f"{days_left} days left"

        testers[tester_email]["name"] = row['tester_name']
        testers[tester_email]["email"] = tester_email
        testers[tester_email]["cc"].update(admin_emails)  # Use admins instead of product owner
        testers[tester_email]["batches"].append({
            "batch_id": row["batch_id"],
            "batch_name": row["batch_name"],
            "maturity_date": maturity_date.strftime('%Y-%m-%d'),
            "label": label
        })
    return testers


# === Send emails ===
def send_emails(testers, admin_emails, email_address, email_password):
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(email_address, email_password)

        for tester_email, tester_data in testers.items():
            if not tester_email:
                continue

            msg = EmailMessage()
            msg['Subject'] = "Upcoming Batch Maturity Reminders"
            msg['From'] = email_address
            msg['To'] = tester_email
            msg['Cc'] = ', '.join(admin_emails)

            # Build HTML table
            table_rows = ''.join(
                f"<tr><td>{b['batch_id']}</td><td>{b['batch_name']}</td><td>{b['maturity_date']}</td><td>{b['label']}</td></tr>"
                for b in tester_data["batches"]
            )

            html_content = f"""
            <html>
            <body>
                <p>Dear {tester_data['name']},</p>
                <p>This is a reminder for the following batches that are approaching their maturity date:</p>
                <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
                    <tr>
                        <th>BATCH ID</th>
                        <th>BATCH NAME</th>
                        <th>MATURITY DATE</th>
                        <th>DAYS LEFT</th>
                    </tr>
                    {table_rows}
                </table>
                <p>Please take the necessary actions.</p>
                <p>Best regards,<br>Automated Notification System</p>
            </body>
            </html>
            """
            msg.set_content("This email contains HTML content. Please view in an HTML-compatible client.")
            msg.add_alternative(html_content, subtype='html')

            smtp.send_message(msg)

# === Main ===
def main():
    db_config = load_db_config()
    conn = connect_db(db_config)
    cursor = conn.cursor(dictionary=True)

    rows = fetch_batches(cursor)
    admin_emails = fetch_admin_emails(cursor)
    testers = group_batches_by_tester(rows, admin_emails)


    if not testers:
        print("No upcoming batches found. No emails sent.")
    else:
        EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
        EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
        send_emails(testers, admin_emails, EMAIL_ADDRESS, EMAIL_PASSWORD)
        print("Grouped emails sent.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
