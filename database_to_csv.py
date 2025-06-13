"""
- fetch data from database to be input into csv file
- generate barcodes based on batch_id, batch_name, submission_date and storage_loaction
- the barcode image path will be saved under the barcode column in the csv file

=== Download commands for imports ===
pip install mysql-connector-python python-barcode
pip install --upgrade python-barcode Pillow

Updated by: Shirlyn, 13/06/2025, 11.30p.m.
"""

import mysql.connector
import csv
from datetime import date, datetime 
import os
from barcode import get_barcode_class
from barcode.writer import ImageWriter
from dotenv import load_dotenv
import sys 

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

# === Fetch batches based on a specific date ===
def fetch_batches_for_date(cursor, target_date):
    cursor.execute("SELECT * FROM batch WHERE DATE(submission_date) = %s", (target_date,))
    return cursor.fetchall()

# === Generate barcode image ===
def generate_barcode(batch):
    submission_date_str = batch['submission_date'].strftime('%Y%m%d')
    # Ensure storage_location is not None before calling replace
    storage_location_clean = batch['storage_location'].replace(' ', '_') if batch['storage_location'] else 'unknown_location'
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
    # Ensure batches list is not empty before attempting to get keys
    if not batches:
        return

    # Use batches[0].keys() to get fieldnames if batches is a list of dictionaries
    # Otherwise, define fixed fieldnames or handle accordingly
    fieldnames = list(batches[0].keys()) if batches else []

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for batch in batches:
            writer.writerow(batch)

# === Main function, now accepting an optional current_date parameter ===
def main(current_date=None):
    db_config = load_db_config()
    setup_directories()

    # Determine the date to process:
    # 1. Use 'current_date' if provided (for testing/direct calls)
    # 2. Check command-line arguments (e.g., python database_to_csv.py --date=YYYY-MM-DD)
    # 3. Fallback to today's actual date
    if current_date is None:
        if len(sys.argv) > 1 and sys.argv[1].startswith('--date='):
            try:
                date_str = sys.argv[1].split('=')[1]
                current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                print(f"Processing batches for specified date from command line: {current_date}")
            except (ValueError, IndexError):
                print("Invalid --date format. Using today's date.")
                current_date = date.today()
        else:
            current_date = date.today()
            print(f"Processing batches for today's date: {current_date}")
    else:
        print(f"Processing batches for provided date: {current_date}")

    conn = None
    cursor = None
    try:
        conn = connect_db(db_config)
        cursor = conn.cursor(dictionary=True)

        batches = fetch_batches_for_date(cursor, current_date) # Use the determined current_date

        if not batches:
            print("No batches submitted today.")
        else:
            for batch in batches:
                barcode_image_path = generate_barcode(batch)
                update_barcode_path_in_db(conn, batch['batch_id'], barcode_image_path)
                batch['barcode'] = barcode_image_path # Update the dict for CSV export

            csv_filename = f'csv_reports/batch_report_{current_date}.csv' # Use current_date for filename
            write_batches_to_csv(batches, csv_filename)

            print(f"CSV saved to: {csv_filename}")
            print("Barcode images saved in 'barcodes/'")
            print("Database updated with barcode image paths.")
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # === Clean up ===
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 