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
            text=True,
            check=False # Do not raise CalledProcessError automatically
        )
        # Check return code manually for success/error if check=False
        if result.returncode == 0:
            return {
                "status": "success",
                "output": result.stdout.strip() # Strip whitespace for cleaner output
            }, 200
        else:
            # If script exits with non-zero code, it's an error from the script itself
            error_message = f"Script execution failed with exit code {result.returncode}."
            print(f"{error_message} Stderr: {result.stderr.strip()}", file=sys.stderr)
            return {
                "status": "error",
                "message": error_message,
                "stderr": result.stderr.strip(),
                "stdout": result.stdout.strip() # Include stdout for debugging
            }, 500
    except Exception as e: # Catch broader exceptions during subprocess creation/execution
        error_message = f"Error running subprocess: {e}"
        print(error_message, file=sys.stderr)  # Log error to Flask app's stderr
        return {
            "status": "error",
            "message": error_message
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
        # Changed to jsonify for consistent API error responses
        return jsonify({"status": "error", "message": "Missing 'batch_id' parameter"}), 400

    image_filename = f"{batch_id}_barcode.png"
    # Ensure this path is correct and accessible for your system
    image_path = os.path.join(BARCODE_IMAGE_FOLDER, image_filename)

    if not os.path.exists(image_path):
        # Changed to jsonify for consistent API error responses
        return jsonify({"status": "error", "message": "Barcode image not found"}), 404

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
    elif script_name is None: # Added this block to handle missing 'script' parameter
        return jsonify({
            "status": "success",
            "output": "Welcome to the Shelf Life Management System API. Please specify a 'script' parameter (e.g., database_to_csv, edit_csv, email_reminder) for POST requests, or a 'batch_id' for GET requests."
        }), 200
    else: # Added this block to handle unrecognized 'script' parameters
        return jsonify({
            "status": "error",
            "message": f"Unknown script: '{script_name}'. Valid scripts are 'database_to_csv', 'edit_csv', 'email_reminder'."
        }), 400

# === Email Scheduler ===
def trigger_email_reminder():
    try:
        # handle_email_reminder returns a tuple (dict, status_code). We only need the dict here.
        result_dict, _ = handle_email_reminder()
        print("Triggered email reminder:", result_dict.get('output', result_dict.get('message', 'No specific output message.')))
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