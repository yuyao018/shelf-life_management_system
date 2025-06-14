"""
Script for backend integration testing

===Install at command line===
pip install freezegun

Updated by: Shirlyn, 14/06/2025, 9.28p.m.
"""

import unittest
import os
import subprocess
import mysql.connector
import time
from unittest.mock import patch, MagicMock
from api_trigger import app # Ensure api_trigger.py exists and handles the root endpoint
from dotenv import load_dotenv
from email_reminder import main as email_reminder_main
from database_to_csv import main as database_to_csv_main 
from datetime import datetime, date, timedelta
import csv
import shutil
from freezegun import freeze_time
import uuid

# Load environment variables from .env file
load_dotenv()

class ScriptIntegrationTests(unittest.TestCase):

    # --- Class-level Setup and Teardown for Test Database ---

    # Define the directories to clean up once, outside of individual tests
    # Use constants to avoid typos
    CSV_REPORTS_DIR = 'csv_reports'
    BARCODES_DIR = 'barcodes'

    @classmethod
    def setUpClass(cls):
        """
        Set up a dedicated test database, populate it with test data,
        and initialize the Flask test client.
        """
        print(f"\n✨ Setting up test environment and database: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        cls.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "port": int(os.getenv("DB_PORT") or 3306)
        }
        cls.db_name = os.getenv("TEST_DB_NAME", "shelf_life_management_system_test")
        cls.db_config_test = {**cls.db_config, "database": cls.db_name}

        # Store the 'today' date when the test data is created for later use in email_reminder tests
        # This ensures consistency even if the test suite runs over a day boundary.
        cls.test_data_creation_date = date.today()
        cls._create_and_populate_test_db()

        # Update environment variable for scripts/API to use the test DB
        os.environ['DB_NAME'] = cls.db_name

        try:
            conn = mysql.connector.connect(**cls.db_config_test)
            cursor = conn.cursor()
            cursor.execute("SELECT batch_id FROM batch ORDER BY batch_id DESC LIMIT 1")
            result = cursor.fetchone()
            cls.test_batch_id = result[0] if result else None
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            raise Exception(f"❌ Database connection to test DB failed: {err}")

        if not cls.test_batch_id:
            raise Exception("❌ No batch_id found in the test database. Test data population failed.")

        cls.client = app.test_client()
        print("✅ Test environment and database setup complete.")

    @classmethod
    def tearDownClass(cls):
        """
        Clean up: drop the test database and remove generated files.
        """
        print(f"\n🗑️ Tearing down test environment: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        cls._drop_test_db()
        cls._clean_generated_files() # Call cleanup at the very end
        # Restore original DB_NAME if it was changed
        if 'DB_NAME' in os.environ and os.environ['DB_NAME'] == cls.db_name:
            del os.environ['DB_NAME']
        print("✅ Test environment cleanup complete.")


    @classmethod
    def _create_and_populate_test_db(cls):
        """Helper to create and populate a dedicated test database."""
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**cls.db_config)
            cursor = conn.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS {cls.db_name}")
            cursor.execute(f"CREATE DATABASE {cls.db_name}")
            conn.database = cls.db_name

            # --- Create Schema and Insert Test Data ---
            # NOTE: You might want to load this from a .sql file for complex schemas
            schema_sql = """
            CREATE TABLE account (
                user_id CHAR(36) NOT NULL PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                email VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(12) NOT NULL,
                role VARCHAR(20) NOT NULL
            );
            CREATE TABLE tester (
                test_id CHAR(36) NOT NULL PRIMARY KEY,
                tester_id CHAR(36) DEFAULT NULL,
                assigned_at DATETIME NULL,
                FOREIGN KEY (tester_id) REFERENCES account(user_id)
            );
            CREATE TABLE batch (
                batch_id CHAR(36) NOT NULL PRIMARY KEY,
                batch_name VARCHAR(50) NOT NULL,
                quantity INT(11) DEFAULT NULL,
                storage_location VARCHAR(50) DEFAULT NULL,
                barcode VARCHAR(100) DEFAULT NULL,
                status VARCHAR(20) DEFAULT NULL,
                product_owner VARCHAR(50) DEFAULT NULL,
                product_owner_email VARCHAR(50) DEFAULT NULL,
                approved_by VARCHAR(50) DEFAULT NULL,
                approval_status VARCHAR(20) DEFAULT NULL,
                submission_date DATETIME NOT NULL,
                maturity_date DATETIME NOT NULL,
                completion_date DATETIME DEFAULT NULL,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP(),
                test_id CHAR(36) DEFAULT NULL,
                FOREIGN KEY (test_id) REFERENCES tester(test_id)
            );
            """
            for statement in schema_sql.split(';'):
                if statement.strip():
                    cursor.execute(statement)
            conn.commit()

            # Insert test data using the date captured in setUpClass
            today = cls.test_data_creation_date
            sixty_days_from_now = today + timedelta(days=60)
            ten_days_from_now = today + timedelta(days=10)

            # Generate UUIDs for the test data
            admin_user_id = str(uuid.uuid4())
            shirlyn_user_id = str(uuid.uuid4())
            john_user_id = str(uuid.uuid4())

            shirlyn_test_id = str(uuid.uuid4())
            john_test_id = str(uuid.uuid4())

            batch_a_id = str(uuid.uuid4())
            batch_b_id = str(uuid.uuid4())
            batch_c_id = str(uuid.uuid4())

            cursor.execute(
                "INSERT INTO account (user_id, name, email, password, role) VALUES (%s, %s, %s, %s, %s)",
                (admin_user_id, 'Admin User', 'admin@example.com', 'adminpass', 'admin')
            )
            cursor.execute(
                "INSERT INTO account (user_id, name, email, password, role) VALUES (%s, %s, %s, %s, %s)",
                (shirlyn_user_id, 'Shirlyn', 'shirlyn@example.com', 'shirlynpass', 'tester')
            )
            cursor.execute(
                "INSERT INTO account (user_id, name, email, password, role) VALUES (%s, %s, %s, %s, %s)",
                (john_user_id, 'John Doe', 'john.doe@example.com', 'johnpass', 'tester')
            )

            cursor.execute(
                "INSERT INTO tester (test_id, tester_id, assigned_at) VALUES (%s, %s, %s)",
                (shirlyn_test_id, shirlyn_user_id, datetime.now())
            )
            cursor.execute(
                "INSERT INTO tester (test_id, tester_id, assigned_at) VALUES (%s, %s, %s)",
                (john_test_id, john_user_id, datetime.now())
            )

            cursor.execute(
                "INSERT INTO batch (batch_id, batch_name, submission_date, maturity_date, storage_location, product_owner, product_owner_email, test_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (batch_a_id, 'BatchA', today, sixty_days_from_now, 'Lab 1', 'Owner A', 'owner.a@example.com', shirlyn_test_id)
            )
            cursor.execute(
                "INSERT INTO batch (batch_id, batch_name, submission_date, maturity_date, storage_location, product_owner, product_owner_email, test_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (batch_b_id, 'BatchB', today, ten_days_from_now, 'Warehouse A', 'Owner B', 'owner.b@example.com', john_test_id)
            )
            cursor.execute(
                "INSERT INTO batch (batch_id, batch_name, submission_date, maturity_date, storage_location, product_owner, product_owner_email, test_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (batch_c_id, 'BatchC(Old)', today - timedelta(days=30), ten_days_from_now, 'Lab 2', 'Owner C', 'owner.c@example.com', shirlyn_test_id)
            )
            conn.commit()

            # Set cls.test_batch_id to one of the newly created UUIDs for other tests
            cls.test_batch_id = batch_a_id
            print(f"✅ Test database '{cls.db_name}' created and populated with UUIDs.")
        except mysql.connector.Error as err:
            print(f"❌ Error setting up test database: {err}")
            raise
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    @classmethod
    def _drop_test_db(cls):
        """Helper to drop the dedicated test database."""
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(**cls.db_config)
            cursor = conn.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS {cls.db_name}")
            conn.commit()
        except mysql.connector.Error as err:
            print(f"❌ Error dropping test database: {err}")
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
            
    def setUp(self):
        """Ensure clean state before each test."""
        for directory in [self.CSV_REPORTS_DIR, self.BARCODES_DIR]:
            try:
                if os.path.exists(directory):
                    shutil.rmtree(directory, ignore_errors=True)
            except:
                pass
        os.makedirs(self.CSV_REPORTS_DIR, exist_ok=True)
        os.makedirs(self.BARCODES_DIR, exist_ok=True)

    @classmethod
    def _clean_generated_files(cls):
        """Silent but effective directory cleanup with accurate status reporting."""
        for directory in [cls.CSV_REPORTS_DIR, cls.BARCODES_DIR]:
            if not os.path.exists(directory):
                continue
                
            print(f"\n🔍 Cleaning up directory: {directory}")
            success = False
            
            # Try multiple approaches
            for attempt in range(1, 6):  # 5 attempts
                try:
                    # Approach 1: Standard deletion
                    if attempt == 1:
                        shutil.rmtree(directory, ignore_errors=False)
                    
                    # Approach 2: Individual file deletion
                    elif attempt == 2:
                        for root, dirs, files in os.walk(directory, topdown=False):
                            for name in files:
                                os.chmod(os.path.join(root, name), 0o777)
                                os.unlink(os.path.join(root, name))
                            for name in dirs:
                                os.rmdir(os.path.join(root, name))
                        os.rmdir(directory)
                    
                    # Approach 3: Windows-specific forced deletion
                    elif attempt == 3 and os.name == 'nt':
                        subprocess.run(f'rmdir /s /q "{directory}"', 
                                    shell=True, check=True, timeout=5)
                    
                    # Approach 4: Move and delete
                    elif attempt == 4:
                        temp_name = f"{directory}_temp_{int(time.time())}"
                        os.rename(directory, temp_name)
                        shutil.rmtree(temp_name, ignore_errors=True)
                    
                    # Approach 5: Final Windows API attempt
                    elif attempt == 5 and os.name == 'nt':
                        try:
                            import ctypes
                            kernel32 = ctypes.windll.kernel32
                            for root, _, files in os.walk(directory):
                                for file in files:
                                    filepath = os.path.join(root, file)
                                    handle = kernel32.CreateFileW(
                                        filepath, 0x80100000, 1, None, 3, 0, None)
                                    if handle != -1:
                                        kernel32.CloseHandle(handle)
                            shutil.rmtree(directory)
                        except:
                            pass
                    
                    # Verify deletion was successful
                    if not os.path.exists(directory):
                        success = True
                        print(f"✅ Directory successfully removed (attempt {attempt})")
                        break
                    
                except Exception:
                    if attempt == 5:
                        print(f"⚠️ Could not completely remove {directory}")
                    time.sleep(0.3 * attempt)
            
            if not success and not os.path.exists(directory):
                # Sometimes Windows reports failure but actually succeeded
                print("✅ Directory removed (Windows reported failure but succeeded)")

    # --- Helper Methods ---

    def _assert_api_success(self, response):
        """Helper to assert success status and 'output' from API response."""
        json_data = response.get_json()
        # If the response is a list (e.g., from jsonify(*handle_...) which returns a tuple)
        # take the first element assuming it's the actual JSON dictionary.
        if isinstance(json_data, list):
            self.assertGreater(len(json_data), 0, "API response list is empty.")
            json_data = json_data[0]
        self.assertEqual(json_data.get("status"), "success", f"Expected API status 'success', got: {json_data}. Full response: {json_data}")
        self.assertIn("output", json_data, f"API response missing 'output' key. Full response: {json_data}")
        print(f"API Success Output: {json_data.get('output')}")

    def _read_csv_content(self, filepath):
        """Reads a CSV file and returns its content as a list of dictionaries."""
        content = []
        with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                content.append(row)
        return content

    # -------------------- Script Tests --------------------

    def setUp(self):
        # Ensure a clean slate for each individual test that might create files
        self._clean_generated_files()

    @freeze_time(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) # Freeze time to today's date for deterministic tests
    def test_database_to_csv_script(self):
        """
        🧪 database_to_csv.py generates CSV and updates DB with barcode image paths for today's batches.
        Verifies: script exit code, output messages, CSV creation, and barcode image creation.
        """
        print("\n▶️ Running test: database_to_csv.py script execution")
        # No self._clean_generated_files() here, it's in setUp()

        result = subprocess.run(['python', 'database_to_csv.py'],
                                capture_output=True, text=True, check=False,
                                close_fds=True)
        time.sleep(0.5) # Crucial: Give OS time to release handles after script finishes

        self.assertEqual(result.returncode, 0, f"❌ Script exited with an error. Stderr: {result.stderr}")
        self.assertIn("CSV saved to:", result.stdout, "❌ Output missing 'CSV saved to:' message.")
        self.assertIn("Barcode images saved", result.stdout, "❌ Output missing 'Barcode images saved' message.")
        self.assertIn("Database updated", result.stdout, "❌ Output missing 'Database updated' message.")

        # Verify CSV file creation and content
        today_str = date.today().strftime('%Y-%m-%d') # This date depends on current system date or freezegun
        csv_filepath = f'csv_reports/batch_report_{today_str}.csv'
        self.assertTrue(os.path.exists(csv_filepath), f"❌ CSV file was not created: {csv_filepath}")
        csv_content = self._read_csv_content(csv_filepath)
        self.assertGreater(len(csv_content), 0, "❌ Generated CSV is empty.")
        # Check if barcodes were generated and paths are in CSV
        for row in csv_content:
            self.assertIn('barcode', row, "❌ 'barcode' column missing in CSV.")
            # It's better to check if the path is not empty first
            if row['barcode']:
                self.assertTrue(os.path.exists(row['barcode']), f"❌ Barcode image not found at: {row['barcode']}")
            else:
                self.fail(f"Barcode path is empty for row: {row}")

        print("✅ database_to_csv.py script executed successfully with output verification.")

    def test_database_to_csv_script_no_batches(self):
        """
        🧪 database_to_csv.py handles case with no batches for today.
        """
        print("\n▶️ Running test: database_to_csv.py script with no batches today")
        # No self._clean_generated_files() here, it's in setUp()

        remote_date = date(2000, 1, 1) # A date far in the past, no batches exist for it

        # Use subprocess.run to call the script with the date argument
        process = subprocess.run(
            ['python', 'database_to_csv.py', f'--date={remote_date.strftime("%Y-%m-%d")}'],
            capture_output=True, text=True, check=False, close_fds=True
        )
        time.sleep(0.5) # Crucial: Give OS time to release handles after script finishes

        print(f"\n--- test_database_to_csv_script_no_batches Output ---")
        print(f"Stdout:\n{process.stdout}")
        print(f"Stderr:\n{process.stderr}")
        print(f"Return Code: {process.returncode}")

        self.assertEqual(process.returncode, 0, f"Script exited with error: {process.stderr}")
        self.assertIn("No batches submitted today.", process.stdout, "❌ Script did not report no batches today.")

        # Ensure the directories might exist, but are empty
        # If the script creates the directories, they should be empty.
        # If they don't exist, that's also fine (len(os.listdir) will error if dir doesn't exist)
        if os.path.exists(self.CSV_REPORTS_DIR):
            self.assertEqual(len(os.listdir(self.CSV_REPORTS_DIR)), 0, "❌ 'csv_reports' directory should be empty.")
        if os.path.exists(self.BARCODES_DIR):
            self.assertEqual(len(os.listdir(self.BARCODES_DIR)), 0, "❌ 'barcodes' directory should be empty.")

        print("✅ database_to_csv.py correctly handled no batches for today.")


    @freeze_time(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) # Keep freeze_time for this script
    def test_edit_csv_script(self):
        """
        🧪 edit_csv.py regenerates CSV and barcodes for a valid batch_id.
        Verifies: script exit code, output messages, and updated barcode path in DB.
        """
        print("\n▶️ Running test: edit_csv.py script with batch_id")
        # No self._clean_generated_files() here, it's in setUp()

        # First, run database_to_csv to create initial CSVs
        initial_run = subprocess.run(['python', 'database_to_csv.py'], capture_output=True, text=True, check=False, close_fds=True)
        time.sleep(0.5) # Small delay after initial run
        self.assertEqual(initial_run.returncode, 0, f"Initial database_to_csv run failed: {initial_run.stderr}")

        # Now, run edit_csv for a specific batch
        batch_id_to_edit = self.test_batch_id # Using the latest batch ID
        result = subprocess.run(['python', 'edit_csv.py', str(batch_id_to_edit), '--verbose'],
                                capture_output=True, text=True, check=False,
                                close_fds=True)
        time.sleep(0.5) # Crucial: Give OS time to release handles after script finishes

        self.assertEqual(result.returncode, 0, f"❌ edit_csv.py did not exit cleanly. Stderr: {result.stderr}")
        self.assertIn("Regenerated CSV", result.stdout, "❌ Expected 'Regenerated CSV' in output.")
        self.assertIn(f"Updated barcode for batch {batch_id_to_edit}", result.stdout, "❌ Expected barcode update message.")

        # Verify the CSV is indeed regenerated
        today_str = date.today().strftime('%Y-%m-%d')
        csv_filepath = os.path.join(self.CSV_REPORTS_DIR, f'batch_report_{today_str}.csv')
        self.assertTrue(os.path.exists(csv_filepath), f"❌ Regenerated CSV file not found: {csv_filepath}")

        # Verify barcode image exists and DB path is updated (requires re-fetching from DB)
        conn = mysql.connector.connect(**self.db_config_test)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT barcode FROM batch WHERE batch_id = %s", (batch_id_to_edit,))
        db_barcode_path = cursor.fetchone()['barcode']
        cursor.close()
        conn.close()
        self.assertTrue(os.path.exists(db_barcode_path), f"❌ Barcode image not found at path stored in DB: {db_barcode_path}")

        print("✅ edit_csv.py script executed successfully and verified.")

    def test_edit_csv_script_invalid_batch_id(self):
        """
        🧪 edit_csv.py handles invalid batch_id gracefully.
        """
        print("\n▶️ Running test: edit_csv.py script with invalid batch_id")
        # No self._clean_generated_files() here, it's in setUp()
        invalid_batch_id = str(uuid.uuid4()) # Use a valid UUID format that won't exist
        result = subprocess.run(['python', 'edit_csv.py', str(invalid_batch_id)],
                                capture_output=True, text=True, check=False,
                                close_fds=True)
        time.sleep(0.5) # Small delay after script finishes

        self.assertEqual(result.returncode, 0, f"❌ Script exited with an error. Stderr: {result.stderr}")
        self.assertIn("No matching batches found.", result.stdout, "❌ Expected 'No matching batches found' message.")
        print("✅ edit_csv.py correctly handled invalid batch ID.")


    @patch('email_reminder.smtplib.SMTP_SSL')
    def test_email_reminder_script(self, mock_smtp):
        """
        🧪 email_reminder.py sends grouped emails using mocked SMTP.
        Verifies: SMTP login, send_message calls, and email content structure.
        """
        print("\n▶️ Running test: email_reminder.py script with mocked SMTP")

        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        with patch.dict(os.environ, {'EMAIL_ADDRESS': 'test@example.com', 'EMAIL_PASSWORD': 'test_password'}):
            # Pass the date when the test data was created to email_reminder_main
            email_reminder_main(current_date=self.test_data_creation_date)

        mock_server.login.assert_called_once_with('test@example.com', 'test_password')
        self.assertTrue(mock_server.send_message.called, "❌ Expected email to be sent.")

        # EXPECT 3 EMAILS NOW due to 3 distinct recipient groups
        self.assertEqual(mock_server.send_message.call_count, 3, "❌ Expected exactly three emails to be sent based on test data.")

        sent_messages = [call.args[0] for call in mock_server.send_message.call_args_list]
        self.assertGreater(len(sent_messages), 0, "No messages were sent.")

        for msg in sent_messages:
            to_recipients = set(addr.strip() for addr in msg['To'].split(','))
            html_content = ""
            # Iterate through the parts of the multipart message to find the HTML content
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    html_content = part.get_payload(decode=True).decode(part.get_content_charset())
                    break # Found the HTML part, no need to check others

            # Check for Shirlyn's Batch A email (Owner A)
            if 'shirlyn@example.com' in to_recipients and 'owner.a@example.com' in to_recipients:
                self.assertIn('admin@example.com', msg['Cc'])
                self.assertEqual(msg['Subject'], "Upcoming Batch Maturity Reminders")
                self.assertIn("BatchA", html_content)
                self.assertIn(f'{self.test_data_creation_date + timedelta(days=60):%Y-%m-%d}', html_content)
                self.assertIn('60 days left', html_content)
                # No 'break' here, as we continue to check other messages
                # We need to ensure all three expected emails are found
                continue # Move to the next message

            # Check for John Doe's Batch B email (Owner B)
            if 'john.doe@example.com' in to_recipients and 'owner.b@example.com' in to_recipients:
                self.assertIn('admin@example.com', msg['Cc'])
                self.assertEqual(msg['Subject'], "Upcoming Batch Maturity Reminders")
                self.assertIn("BatchB", html_content)
                self.assertIn(f'{self.test_data_creation_date + timedelta(days=10):%Y-%m-%d}', html_content)
                self.assertIn('10 days left', html_content)
                continue # Move to the next message

            # Check for Shirlyn's Batch C(Old) email (Owner C)
            if 'shirlyn@example.com' in to_recipients and 'owner.c@example.com' in to_recipients:
                self.assertIn('admin@example.com', msg['Cc'])
                self.assertEqual(msg['Subject'], "Upcoming Batch Maturity Reminders")
                self.assertIn("BatchC(Old)", html_content)
                self.assertIn(f'{self.test_data_creation_date + timedelta(days=10):%Y-%m-%d}', html_content)
                self.assertIn('10 days left', html_content)
                continue # Move to the next message

        # After checking all messages, verify that all three were found
        # (The individual 'if' blocks with 'continue' are slightly less robust
        # for verifying *all* expected emails were present. Let's re-introduce
        # the tracking flags.)
        shirlyn_email_A_found = False
        john_email_B_found = False
        shirlyn_email_C_found = False

        for msg in sent_messages:
            to_recipients = set(addr.strip() for addr in msg['To'].split(','))
            html_content = ""
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    html_content = part.get_payload(decode=True).decode(part.get_content_charset())
                    break

            if 'shirlyn@example.com' in to_recipients and 'owner.a@example.com' in to_recipients and 'BatchA' in html_content:
                shirlyn_email_A_found = True
            elif 'john.doe@example.com' in to_recipients and 'owner.b@example.com' in to_recipients and 'BatchB' in html_content:
                john_email_B_found = True
            elif 'shirlyn@example.com' in to_recipients and 'owner.c@example.com' in to_recipients and 'BatchC(Old)' in html_content:
                shirlyn_email_C_found = True

        self.assertTrue(shirlyn_email_A_found, "❌ Email for Shirlyn (Batch A) not found or incorrect.")
        self.assertTrue(john_email_B_found, "❌ Email for John Doe (Batch B) not found or incorrect.")
        self.assertTrue(shirlyn_email_C_found, "❌ Email for Shirlyn (Batch C Old) not found or incorrect.")

        print("✅ email_reminder.py script successfully mocked and verified.")

    @patch('email_reminder.smtplib.SMTP_SSL')
    def test_email_reminder_script_no_upcoming_batches(self, mock_smtp):
        """
        🧪 email_reminder.py handles case with no upcoming batches.
        """
        print("\n▶️ Running test: email_reminder.py script with no upcoming batches")
        with patch.dict(os.environ, {'EMAIL_ADDRESS': 'test@example.com', 'EMAIL_PASSWORD': 'test_password'}):
            # Pick a date far away from any test batch maturity dates.
            # Test batches were created relative to cls.test_data_creation_date.
            # So, picking a date far from that will ensure no matches.
            remote_date = date(2020, 1, 1) # Example: Jan 1, 2020
            email_reminder_main(current_date=remote_date)

        # Assert that no SMTP connection was made
        mock_smtp.assert_not_called()
        print("✅ email_reminder.py correctly handled no upcoming batches.")


    # -------------------- API Tests --------------------

    def test_api_edit_csv(self):
        """
        🧪 API /?script=edit_csv should regenerate CSV for a specific batch_id.
        Verifies: API status code and success message.
        """
        print("\n▶️ Running test: API call to /?script=edit_csv")
        # Ensure a clean slate before API calls that affect files
        self._clean_generated_files() # Call cleanup before this API test

        # First, ensure there's a CSV to edit (API handles its own subprocess calls)
        initial_api_run = self.client.post("/?script=database_to_csv")
        self.assertEqual(initial_api_run.status_code, 200, "Initial API database_to_csv call failed.")
        time.sleep(0.5) # Give API server time to process and release handles

        response = self.client.post(f"/?script=edit_csv&batch_id={self.test_batch_id}")
        self.assertEqual(response.status_code, 200, f"❌ Expected 200 OK, got {response.status_code}")
        self._assert_api_success(response)
        print("✅ API /?script=edit_csv call successful.")

    def test_api_database_to_csv(self):
        """
        🧪 API /?script=database_to_csv should export DB to CSV.
        Verifies: API status code and success message.
        """
        print("\n▶️ Running test: API call to /?script=database_to_csv")
        self._clean_generated_files() # Ensure a clean slate
        response = self.client.post("/?script=database_to_csv")
        self.assertEqual(response.status_code, 200, f"❌ Expected 200 OK, got {response.status_code}")
        self._assert_api_success(response)
        print("✅ API /?script=database_to_csv call successful.")

    def test_api_email_reminder(self):
        """
        🧪 API /?script=email_reminder should trigger email reminders.
        Verifies: API status code and success message. (SMTP mocking should be handled in underlying `email_reminder.py` test)
        """
        print("\n▶️ Running test: API call to /?script=email_reminder")
        response = self.client.post("/?script=email_reminder")
        self.assertEqual(response.status_code, 200, f"❌ Expected 200 OK, got {response.status_code}")
        self._assert_api_success(response)
        print("✅ API /?script=email_reminder call successful.")

    def test_api_barcode_image_not_found(self):
        """
        🧪 API /?batch_id=invalid_id should return 404 for non-existent batch ID.
        Verifies: API status code for a negative scenario.
        """
        print("\n▶️ Running test: API call to /?batch_id=invalid_id")
        # Ensure the directory exists but the specific file does not for a realistic test
        os.makedirs(self.BARCODES_DIR, exist_ok=True)
        response = self.client.get(f"/?batch_id={str(uuid.uuid4())}") # Use a fresh, non-existent UUID
        self.assertEqual(response.status_code, 404, f"❌ Expected 404 Not Found, got {response.status_code}")
        # API now returns JSON, so get_json() and check 'message'
        json_data = response.get_json()
        self.assertIn("Barcode image not found", json_data.get('message', ''), "❌ Expected 'not found' message in response JSON.")
        print("✅ API /?batch_id=invalid_id correctly returned 404.")

    def test_api_no_script_parameter(self):
        """
        🧪 API call with no 'script' parameter should return a default or error response.
        """
        print("\n▶️ Running test: API call with no script parameter")
        response = self.client.post("/")
        self.assertEqual(response.status_code, 200, f"❌ Expected 200 OK, got {response.status_code}")
        self._assert_api_success(response)
        json_data = response.get_json()
        self.assertIn("Welcome to the Shelf Life Management System API.", json_data.get('output', ''), "Expected welcome message in output.")
        print("✅ API call with no script parameter handled.")

    def test_api_unrecognized_script_parameter(self):
        """
        🧪 API call with an unrecognized 'script' parameter should return a 400 error.
        """
        print("\n▶️ Running test: API call with unrecognized script parameter")
        response = self.client.post("/?script=unrecognized_script")
        self.assertEqual(response.status_code, 400, f"❌ Expected 400 Bad Request, got {response.status_code}")
        json_data = response.get_json()
        self.assertIn("error", json_data.get("status"), "Expected status 'error'")
        self.assertIn("Unknown script", json_data.get("message"), "Expected 'Unknown script' message.")
        print("✅ API call with unrecognized script parameter handled.")


if __name__ == "__main__":
    print(f"\n🧪 Starting integration tests: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    report_path = "test_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        unittest.main(testRunner=runner, exit=False)

    print(f"\n📄 Test report generated: {report_path}")
