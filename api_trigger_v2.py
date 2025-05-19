from flask import Flask, request, jsonify
import subprocess
import sys

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

def handle_database_to_csv():
    return execute_script(['python', 'database_to_csv_env.py'])

def handle_edit_csv(batch_id):
    return execute_script(['python', 'edit_csv.py', str(batch_id), '--verbose'])

app = Flask(__name__)

@app.route("/", methods=["POST"])
def run_script():
    script_name = request.args.get("script")
    batch_id = request.args.get("batch_id")
    print("Script:", script_name)
    print("Batch ID:", batch_id)

    if script_name == "database_to_csv":
        return jsonify(*handle_database_to_csv())
    elif script_name == "edit_csv" and batch_id:
        return jsonify(*handle_edit_csv(batch_id))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)