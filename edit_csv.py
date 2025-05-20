"""
- update the csv file from the data at database by:
- deleting the old/existing generated csv file according to the batch_id
- update barcode according to the updated batch_id
- regenerate a csv file with the lastest data from database based on the date submitted

Command to run this script:
python edit_csv.py (insert batch_id) --verbose

Updated by: Shirlyn, 20/5/2025 8.43a.m.
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
def parse_arguments():
    parser = argparse.ArgumentParser(description="Regenerate CSV and barcodes for specific batch IDs.")
    parser.add_argument("batch_ids", nargs="+", help="One or more batch IDs to process")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    return parser.parse_args()

# === Load DB config ===
def get_db_config():
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

# === Fetch specified batch data ===
def fetch_batches_by_ids(cursor, batch_ids):
    format_str = ','.join(['%s'] * len(batch_ids))
    cursor.execute(f"SELECT * FROM batch WHERE batch_id IN ({format_str})", batch_ids)
    return cursor.fetchall()

# === Group batches by submission date ===
def group_batches_by_date(batches):
    grouped = defaultdict(list)
    for batch in batches:
        submission_date = batch['submission_date'].date()
        grouped[submission_date].append(batch)
    return grouped

# === Fetch all batches by submission date ===
def fetch_all_batches_by_date(cursor, submission_date):
    cursor.execute("SELECT * FROM batch WHERE DATE(submission_date) = %s", (submission_date,))
    return cursor.fetchall()

# === Generate and save barcode ===
def generate_and_save_barcode(batch):
    submission_date_str = batch['submission_date'].strftime('%Y%m%d')
    storage_location_clean = batch['storage_location'].replace(' ', '_')
    barcode_string = f"{batch['batch_id']}-{batch['batch_name']}-{submission_date_str}-{storage_location_clean}"
    barcode_class = get_barcode_class('code128')
    barcode_filename = f"{batch['batch_id']}_barcode"
    barcode_path = os.path.join("barcodes", barcode_filename)
    return barcode_class(barcode_string, writer=ImageWriter()).save(barcode_path)

# === Update DB with barcode path ===
def update_barcode_in_db(conn, batch_id, barcode_path):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE batch SET barcode = %s, updated_at = %s WHERE batch_id = %s",
        (barcode_path, datetime.now(), batch_id)
    )
    conn.commit()
    cursor.close()

# === Write batches to CSV ===
def write_batches_to_csv(csv_filename, all_batches, updated_batch_ids, conn, verbose):
    if os.path.exists(csv_filename):
        os.remove(csv_filename)
        if verbose:
            print(f"Deleted old CSV: {csv_filename}")

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = list(all_batches[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for batch in all_batches:
            if str(batch['batch_id']) in updated_batch_ids:
                barcode_path = generate_and_save_barcode(batch)
                update_barcode_in_db(conn, batch['batch_id'], barcode_path)
                batch['barcode'] = barcode_path
                if verbose:
                    print(f"Updated barcode for batch {batch['batch_id']}")
            writer.writerow(batch)

    print(f"Regenerated CSV: {csv_filename}")

# === Main logic ===
def main():
    args = parse_arguments()
    setup_directories()

    db_config = get_db_config()
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    batches = fetch_batches_by_ids(cursor, args.batch_ids)

    if not batches:
        print("No matching batches found.")
        cursor.close()
        conn.close()
        exit(0)

    grouped_batches = group_batches_by_date(batches)

    for submission_date, affected_batches in grouped_batches.items():
        all_batches = fetch_all_batches_by_date(cursor, submission_date)
        csv_filename = f'csv_reports/batch_report_{submission_date}.csv'
        write_batches_to_csv(csv_filename, all_batches, args.batch_ids, conn, args.verbose)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()