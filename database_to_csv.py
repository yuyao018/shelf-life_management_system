"""
- fetch data from database to be input into csv file
- generate barcodes based on batch_id, batch_name, submission_date and storage_loaction
- the barcode image path will be saved under the barcode column in the csv file

 === Download commands for imports ===
pip install mysql-connector-python python-barcode
pip install --upgrade python-barcode Pillow

"""

import mysql.connector
import csv
from datetime import date
import os
from barcode import get_barcode_class
from barcode.writer import ImageWriter
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

# === Setup directories ===
os.makedirs('csv_reports', exist_ok=True)
os.makedirs('barcodes', exist_ok=True)

# === Connect to MySQL ===
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

# === Get today's date ===
today = date.today()

# === Fetch today's batches ===
cursor.execute("SELECT * FROM batch WHERE DATE(submission_date) = %s", (today,))
batches = cursor.fetchall()

if not batches:
    print("No batches submitted today.")
else:
    csv_filename = f'csv_reports/batch_report_{today}.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = list(batches[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for batch in batches:
            submission_date_str = batch['submission_date'].strftime('%Y%m%d')
            storage_location_clean = batch['storage_location'].replace(' ', '_')  # avoid spaces in barcode
            barcode_string = f"{batch['batch_id']}-{batch['batch_name']}-{submission_date_str}-{storage_location_clean}"

            # Generate barcode image
            barcode_class = get_barcode_class('code128')
            barcode_filename = f"{batch['batch_id']}_barcode"
            barcode_path = os.path.join("barcodes", barcode_filename)
            barcode_image_path = barcode_class(barcode_string, writer=ImageWriter()).save(barcode_path)

            # Update DB with image path
            cursor_update = conn.cursor()
            cursor_update.execute(
                "UPDATE batch SET barcode = %s WHERE batch_id = %s",
                (barcode_image_path, batch['batch_id'])
            )
            conn.commit()
            cursor_update.close()

            # Update the dict for CSV export
            batch['barcode'] = barcode_image_path

            writer.writerow(batch)

    print(f"✅ CSV saved to: {csv_filename}")
    print("✅ Barcode images saved in 'barcodes/'")
    print("✅ Database updated with barcode image paths.")

# === Clean up ===
cursor.close()
conn.close()