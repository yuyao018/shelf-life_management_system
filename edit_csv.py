"""
- update the csv file from the data at database by:
- deleting the old/existing generated csv file according to the batch_id
- update barcode according to the updated batch_id
- regenerate a csv file with the lastest data from database based on the date submitted

Command to run this script:
python edit_csv.py (insert batch_id) --verbose

Updated by: Shirlyn, 13/5/2025 9.03a.m.
"""

import mysql.connector
import csv
import os
from barcode import get_barcode_class
from barcode.writer import ImageWriter
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv
import argparse

# === Argument Parser ===
parser = argparse.ArgumentParser(description="Regenerate CSV and barcodes for specific batch IDs.")
parser.add_argument("batch_ids", nargs="+", help="One or more batch IDs to process")
parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
args = parser.parse_args()


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


# === Setup directories ===
os.makedirs('csv_reports', exist_ok=True)
os.makedirs('barcodes', exist_ok=True)

# === Connect to MySQL ===
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

# === Fetch specified batch data ===
format_str = ','.join(['%s'] * len(args.batch_ids))
cursor.execute(f"SELECT * FROM batch WHERE batch_id IN ({format_str})", args.batch_ids)
batches = cursor.fetchall()

if not batches:
    print("⚠️ No matching batches found.")
    cursor.close()
    conn.close()
    exit(0)

# === Group by submission_date ===
grouped_batches = defaultdict(list)
for batch in batches:
    submission_date = batch['submission_date'].date()
    grouped_batches[submission_date].append(batch)

for submission_date, affected_batches in grouped_batches.items():
    # Fetch all batches with that submission date
    cursor.execute("SELECT * FROM batch WHERE DATE(submission_date) = %s", (submission_date,))
    all_batches = cursor.fetchall()

    csv_filename = f'csv_reports/batch_report_{submission_date}.csv'
    if os.path.exists(csv_filename):
        os.remove(csv_filename)
        if args.verbose:
            print(f"🗑️ Deleted old CSV: {csv_filename}")

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = list(all_batches[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for batch in all_batches:
            submission_date_str = batch['submission_date'].strftime('%Y%m%d')
            storage_location_clean = batch['storage_location'].replace(' ', '_')
            barcode_string = f"{batch['batch_id']}-{batch['batch_name']}-{submission_date_str}-{storage_location_clean}"

            if str(batch['batch_id']) in args.batch_ids:
                barcode_class = get_barcode_class('code128')
                barcode_filename = f"{batch['batch_id']}_barcode"
                barcode_path = os.path.join("barcodes", barcode_filename)
                barcode_image_path = barcode_class(barcode_string, writer=ImageWriter()).save(barcode_path)

                cursor_update = conn.cursor()
                cursor_update.execute(
                    "UPDATE batch SET barcode = %s, updated_at = %s WHERE batch_id = %s",
                    (barcode_image_path, datetime.now(), batch['batch_id'])
                )

                conn.commit()
                cursor_update.close()

                batch['barcode'] = barcode_image_path

                if args.verbose:
                    print(f"🔄 Updated barcode for batch {batch['batch_id']}")

            writer.writerow(batch)

    print(f"✅ Regenerated CSV: {csv_filename}")

# === Clean up ===
cursor.close()
conn.close()