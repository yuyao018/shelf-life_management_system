"""
Script for backend unit testing

Updated by: Shirlyn, 09/06/2025, 9.28p.m.
"""

import unittest
import os
import subprocess
import mysql.connector
from unittest.mock import patch, MagicMock
from api_trigger import app
from dotenv import load_dotenv
from email_reminder import main as email_reminder_main
from datetime import datetime

# Load environment variables
load_dotenv()

class ScriptIntegrationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up DB connection and fetch the latest batch_id."""
        cls.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "user": os.getenv("DB_USER", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "shelf_life_management_system"),
            "port": int(os.getenv("DB_PORT") or 3306)
        }

        try:
            conn = mysql.connector.connect(**cls.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT batch_id FROM batch ORDER BY batch_id DESC LIMIT 1")
            result = cursor.fetchone()
            cls.test_batch_id = result[0] if result else None
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            raise Exception(f"❌ Database connection failed: {err}")

        if not cls.test_batch_id:
            raise Exception("❌ No batch_id found in the database. Please add a batch first.")

        cls.client = app.test_client()

    # -------------------- Script Tests --------------------

    def test_database_to_csv_script(self):
        """🧪 database_to_csv.py generates CSV and updates DB with barcode image paths."""
        print("\n▶️ Running test: database_to_csv.py script execution")
        result = subprocess.run(['python', 'database_to_csv.py'],
                                capture_output=True, text=True)

        self.assertEqual(result.returncode, 0, "❌ Script exited with an error.")
        self.assertIn("CSV saved to:", result.stdout, "❌ Output missing 'CSV saved to:' message.")
        self.assertIn("Barcode images saved", result.stdout, "❌ Output missing 'Barcode images saved' message.")
        self.assertIn("Database updated", result.stdout, "❌ Output missing 'Database updated' message.")


    def test_edit_csv_script(self):
        """🧪 edit_csv.py regenerates CSV for a valid batch_id."""
        print("\n▶️ Running test: edit_csv.py script with batch_id")
        result = subprocess.run(['python', 'edit_csv.py', str(self.test_batch_id), '--verbose'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "edit_csv.py did not exit cleanly.")
        self.assertIn("Regenerated CSV", result.stdout, "Expected 'Regenerated CSV' in output.")

    @patch('email_reminder.smtplib.SMTP_SSL')
    def test_email_reminder_script(self, mock_smtp):
        """🧪 email_reminder.py sends grouped emails using SMTP."""
        print("\n▶️ Running test: email_reminder.py script with mocked SMTP")

        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        email_reminder_main()

         # Assert email login and message send
        mock_server.login.assert_called_once_with(
            os.getenv('EMAIL_ADDRESS'), os.getenv('EMAIL_PASSWORD')
        )
        self.assertTrue(mock_server.send_message.called, "Expected email to be sent.")

    # -------------------- API Tests --------------------

    def test_api_edit_csv(self):
        """🧪 API /?script=edit_csv should regenerate CSV."""
        print("\n▶️ Running test: API call to /?script=edit_csv")
        response = self.client.post(f"/?script=edit_csv&batch_id={self.test_batch_id}")
        self.assertEqual(response.status_code, 200)
        self._assert_api_success(response)

    def test_api_database_to_csv(self):
        """🧪 API /?script=database_to_csv should export DB to CSV."""
        print("\n▶️ Running test: API call to /?script=database_to_csv")
        response = self.client.post("/?script=database_to_csv")
        self.assertEqual(response.status_code, 200)
        self._assert_api_success(response)

    def test_api_email_reminder(self):
        """🧪 API /?script=email_reminder should trigger email reminders."""
        print("\n▶️ Running test: API call to /?script=email_reminder")
        response = self.client.post("/?script=email_reminder")
        self.assertEqual(response.status_code, 200)
        self._assert_api_success(response)

    def test_api_barcode_image_not_found(self):
        """🧪 API /?batch_id=invalid_id should return 404."""
        print("\n▶️ Running test: API call to /?batch_id=invalid_id")
        response = self.client.get("/?batch_id=invalid_id")
        self.assertEqual(response.status_code, 404)

    # -------------------- Helpers --------------------

    def _assert_api_success(self, response):
        json_data = response.get_json()
        if isinstance(json_data, list):
            json_data = json_data[0]
        self.assertEqual(json_data.get("status"), "success", f"Expected success, got: {json_data}")


if __name__ == "__main__":
    print(f"\n🧪 Starting integration tests: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    unittest.main(verbosity=2)
