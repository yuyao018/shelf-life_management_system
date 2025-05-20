"""
- fetch data from database to be input into csv file
- generate barcodes based on batch_id, batch_name, submission_date and storage_loaction
- the barcode image path will be saved under the barcode column in the csv file

 === Download commands for imports ===
pip install mysql-connector-python python-barcode
pip install --upgrade python-barcode Pillow

Updated by: Shirlyn, 20/05/2025, 8.40a.m.
"""

import mysql.connector
import csv
from datetime import date
import os
from barcode import get_barcode_class
from barcode.writer import ImageWriter
from dotenv import load_dotenv

# === Load environment variables ===
def load_db_config():
    load_dotenv()
    port_str = os.getenv('DB_PORT')
    return {
        'host': os.getenv('DB_HOST'),
        'port': int(port_str) if port_str and port_str.isdigit() else 3306,
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }

# === Setup directories ===
def setup_directories():
    os.makedirs('csv_reports', exist_ok=True)
    os.makedirs('barcodes', exist_ok=True)

# === Connect to MySQL ===
def connect_db(config):
    return mysql.connector.connect(**config)

# === Fetch today's batches ===
def fetch_today_batches(cursor, today):
    cursor.execute("SELECT * FROM batch WHERE DATE(submission_date) = %s", (today,))
    return cursor.fetchall()

# === Generate barcode image ===
def generate_barcode(batch):
    submission_date_str = batch['submission_date'].strftime('%Y%m%d')
    storage_location_clean = batch['storage_location'].replace(' ', '_')
    barcode_string = f"{batch['batch_id']}-{batch['batch_name']}-{submission_date_str}-{storage_location_clean}"
    barcode_class = get_barcode_class('code128')
    barcode_filename = f"{batch['batch_id']}_barcode"
    barcode_path = os.path.join("barcodes", barcode_filename)
    return barcode_class(barcode_string, writer=ImageWriter()).save(barcode_path)

# === Update DB with image path ===
def update_barcode_path_in_db(conn, batch_id, barcode_image_path):
    cursor_update = conn.cursor()
    cursor_update.execute(
        "UPDATE batch SET barcode = %s WHERE batch_id = %s",
        (barcode_image_path, batch_id)
    )
    conn.commit()
    cursor_update.close()

# === Write results to CSV ===
def write_batches_to_csv(batches, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = list(batches[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for batch in batches:
            writer.writerow(batch)

def main():
    db_config = load_db_config()
    setup_directories()

    conn = connect_db(db_config)
    cursor = conn.cursor(dictionary=True)

    # === Get today's date ===
    today = date.today()

    batches = fetch_today_batches(cursor, today)

    if not batches:
        print("No batches submitted today.")
    else:
        for batch in batches:
            barcode_image_path = generate_barcode(batch)
            update_barcode_path_in_db(conn, batch['batch_id'], barcode_image_path)
            batch['barcode'] = barcode_image_path # Update the dict for CSV export

        csv_filename = f'csv_reports/batch_report_{today}.csv'
        write_batches_to_csv(batches, csv_filename)

        print(f"✅ CSV saved to: {csv_filename}")
        print("✅ Barcode images saved in 'barcodes/'")
        print("✅ Database updated with barcode image paths.")

    # === Clean up ===
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
