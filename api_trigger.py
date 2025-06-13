"""
install the library (can run at terminal): pip install schedule

"""

from flask import Flask, request, jsonify, send_file, abort
import subprocess
import sys
import threading
import schedule
import time
import os

# set the folder path where the barcode images are stored
BARCODE_IMAGE_FOLDER = "C:/Users/chook/OneDrive/Documents/INTI/Sem 4/Software Engineering/Assignment/script/barcodes"

# === Utility Function to Execute External Python Scripts ===
def execute_script(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )
        return {
            "status": "success",
            "output": result.stdout
        }, 200
    except subprocess.CalledProcessError as e:
        error_message = f"Error executing script: {e}"
        print(error_message, file=sys.stderr)  # Log error to Flask app's stderr
        return {
            "status": "error",
            "message": error_message,
            "stderr": e.stderr
        }, 500

# === Script Handlers ===
def handle_database_to_csv(): # call the 'database_to_csv.py' script
    return execute_script(['python', 'database_to_csv.py'])

def handle_edit_csv(batch_id): # call the 'edit_csv.py' script with the specified batch id
    return execute_script(['python', 'edit_csv.py', str(batch_id), '--verbose'])

def handle_email_reminder(): # call the 'email_reminder.py' script
    return execute_script(['python', 'email_reminder.py'])

# === Flask App Setup ===
app = Flask(__name__)

# === Route: Serve Barcode Image ===
@app.route("/", methods=["GET"])
def get_barcode_image(): # Serves a barcode image file based on the batch ID passed as a query parameter.
    batch_id = request.args.get("batch_id", "")
    if not batch_id:
        return "Missing 'batch_id' parameter", 400

    image_filename = f"{batch_id}_barcode.png"
    image_path = os.path.join(BARCODE_IMAGE_FOLDER, image_filename)

    if not os.path.exists(image_path):
        return abort(404, description="Barcode image not found")

    return send_file(image_path, mimetype='image/png')

# === Route: Trigger Script Execution via HTTP POST ===
@app.route("/", methods=["POST"])
def run_script(): # Triggers script execution based on 'script' and optional 'batch_id' query parameters.
    script_name = request.args.get("script")
    batch_id = request.args.get("batch_id")
    print("Script:", script_name)
    print("Batch ID:", batch_id)

    if script_name == "database_to_csv":
        return jsonify(*handle_database_to_csv())
    elif script_name == "edit_csv" and batch_id:
        return jsonify(*handle_edit_csv(batch_id))
    elif script_name == "email_reminder":
        return jsonify(*handle_email_reminder())

# === Email Scheduler ===
def trigger_email_reminder():
    try:
        result, status = handle_email_reminder()
        print("Triggered email reminder:", result)
    except Exception as e:
        print("Failed to trigger email reminder:", e)

def schedule_runner():
    schedule.every().day.at("09:00").do(trigger_email_reminder)
    print("Email scheduler started...")
    while True:
        schedule.run_pending()
        time.sleep(60)

# === Start Flask and Scheduler Together ===
if __name__ == "__main__":
    # Start scheduler in a separate thread
    scheduler_thread = threading.Thread(target=schedule_runner, daemon=True)
    scheduler_thread.start()

    # Start Flask API server
    app.run(host="0.0.0.0", port=5000)