import pytest
import pytest_html
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import base64

# python -m pytest testing/admin_test.py --html=testing/report_admin.html --self-contained-html

screenshot_storage = "C:/Users/chook/OneDrive/Documents/INTI/Sem 4/Software Engineering/Assignment/script/testing/screenshots"

@pytest.fixture(scope="session")
def browser_driver():
    options = Options()
    options.binary_location = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
    service = Service(executable_path="C:/webdriver/msedgedriver.exe")
    driver = webdriver.Edge(service=service, options=options)
    driver.implicitly_wait(10)
    driver.get("http://localhost/app/shelf-life-management-system/login-68299e4a0b957058348e8aec?branch=frontend")
    yield driver
    driver.quit()

def test_login(browser_driver):
    print("Testing the Log In functionality.")
    wait = WebDriverWait(browser_driver, 20)

    inputs = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "bp3-input")))
    email = inputs[0]
    email.send_keys("alicetan@gmail.com")
    print("Email input successfully!")

    password = inputs[1]
    password.send_keys("admin12345")
    print("Password input successfully!")

    button = browser_driver.find_element(By.CSS_SELECTOR, "button.bp3-button.bp3-fill[data-test-variant='PRIMARY']")
    # selenium can't click on the button, there is something blocking it. Hence, Javascript is used to click the button.
    browser_driver.execute_script("arguments[0].click();", button)
    print("Click on the Log In button successfully!")

    time.sleep(5)

def test_navbar(browser_driver):
    wait = WebDriverWait(browser_driver, 20)
    try:
        print("\n=== Navigate to Manage Batch page ===")
        button = browser_driver.find_elements(By.CSS_SELECTOR, "button.bp3-button.bp3-fill.sc-klEEPK.fjNcfO[data-test-variant='TERTIARY']")
        print(len(button))
        manage_batch_button = button[1]
        browser_driver.execute_script("arguments[0].click();", manage_batch_button)
        wait.until(EC.visibility_of_element_located((
            By.XPATH,
            "//div[contains(@class, 'sc-hYXlKe') and contains(., 'Manage Batch')]//span[text()='Manage Batch']"
        )))
        print("Click on Manage Batch button to navigate to the page successfully!")
    except Exception as e:
        print("Error: loading the Manage Batch page.")
        assert False, str(e)

    try:
        print("\n=== Navigate to Manage User page ===")
        button = browser_driver.find_elements(By.CSS_SELECTOR, "button.bp3-button.bp3-fill.sc-klEEPK.fjNcfO[data-test-variant='TERTIARY']")
        manage_user_button = button[2]
        browser_driver.execute_script("arguments[0].click();", manage_user_button)
        wait.until(EC.visibility_of_element_located((
            By.XPATH,
            "//div[contains(@class, 'sc-hYXlKe')]//span[text()='Manage User']"
        )))
        print("Click on Manage User button to navigate to the page successfully!")
    except Exception as e:
        print("Error: loading the Manage User page.")
        assert False, str(e)

    try:
        print("\n=== Navigate to Dashboard page ===")
        button = browser_driver.find_elements(By.CSS_SELECTOR, "button.bp3-button.bp3-fill.sc-klEEPK.fjNcfO[data-test-variant='TERTIARY']")
        dashboard_button = button[0]
        browser_driver.execute_script("arguments[0].click();", dashboard_button)
        wait.until(EC.visibility_of_element_located((
            By.XPATH,
            "//div[contains(@class, 'sc-hYXlKe')]//span[text()='Dashboard']"
        )))
        print("Click on Dashboard button to navigate to the page successfully!")
    except Exception as e:
        print("Error: loading the Dashboard page.")
        assert False, str(e)

def test_load_dashboard(browser_driver, extras):
    try:
        print("\n=== Loading the Manage Batch page ===")
        element = WebDriverWait(browser_driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Dashboard page loaded successfully!")
        screenshot_filename = f"{screenshot_storage}/Dashboard page.png"
        element.screenshot(screenshot_filename)

        with open(screenshot_filename, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')

        extras.append(pytest_html.extras.image(img_base64, mime_type="image/png"))
        print(f"✓ Screenshot attached: {screenshot_filename}")

    except Exception as e:
        print(f"✖ Error capturing {screenshot_filename}: {str(e)}")
        raise

def test_dashboard_cards(browser_driver, extras):
    print("\n=== Starting dashboard cards test ===")

    screenshot_count = 0
    try:
        wait = WebDriverWait(browser_driver, 20)
        cards = [
            ("Pending Requests", "div.appsmith_widget_rxv4sy5a4e.container-with-scrollbar"),
            ("Approved Requests", "div.appsmith_widget_76absbl5ec.container-with-scrollbar"),
            ("Rejected Requests", "div.appsmith_widget_q5w3x54k09.container-with-scrollbar"),
            ("Canceled Requests", "div.appsmith_widget_sjwtarppry.container-with-scrollbar"),
            ("Testing Not Started", "div.appsmith_widget_eq5bougz5b.container-with-scrollbar"),
            ("Testing In Progress", "div.appsmith_widget_s0qyy4q5ya.container-with-scrollbar"),
            ("Completed Testing", "div.appsmith_widget_4wpzc8etwg.container-with-scrollbar")
        ]

        for label, selector in cards:
            print(f"\nProcessing card: {label}")
            try:
                card = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                browser_driver.execute_script("arguments[0].scrollIntoView(true);", card)
                screenshot_filename = f"{screenshot_storage}/{label}.png"
                card.screenshot(screenshot_filename)

                with open(screenshot_filename, "rb") as f:
                    img_base64 = base64.b64encode(f.read()).decode('utf-8')

                extras.append(pytest_html.extras.image(img_base64, mime_type="image/png"))
                print(f"\"{card}\" card loaded successfully!")
                print(f"✓ Screenshot attached: {label}.png")
                screenshot_count += 1

            except Exception as e:
                print(f"✖ Error capturing {label}: {str(e)}")
                raise

        print(f"\n=== Test completed: {screenshot_count}/{len(cards)} screenshots attached ===")
        assert screenshot_count == len(cards)

    except Exception as e:
        print(f"\n!!! Test failed: {str(e)}")
        assert False, f"Failed to capture all screenshots: {str(e)}"

def test_dashboard_tables(browser_driver, extras):
    print("\n=== Starting dashboard tables test ===")

    screenshot_count = 0
    try:
        wait = WebDriverWait(browser_driver, 20)
        tables = [
            ("Pending Requests", "div.appsmith_widget_jlqeas7j8b.container-with-scrollbar"),
            ("Maturity Overview", "div.appsmith_widget_ts33suuw9m.container-with-scrollbar"),
            ("Test Queue", "div.appsmith_widget_tfqv5qoxvg.container-with-scrollbar")
        ]

        for label, selector in tables:
            print(f"\nProcessing table: {label}")
            try:
                table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                browser_driver.execute_script("arguments[0].scrollIntoView(true);", table)
                screenshot_filename = f"{screenshot_storage}/{label}.png"
                table.screenshot(screenshot_filename)

                with open(screenshot_filename, "rb") as f:
                    img_base64 = base64.b64encode(f.read()).decode('utf-8')

                extras.append(pytest_html.extras.image(img_base64, mime_type="image/png"))
                print(f"\"{table}\" table loaded successfully!")
                print(f"✓ Screenshot attached: {label}.png")
                screenshot_count += 1

            except Exception as e:
                print(f"✖ Error capturing {label}: {str(e)}")
                raise

        print(f"\n=== Test completed: {screenshot_count}/{len(tables)} screenshots attached ===")
        assert screenshot_count == len(tables)

    except Exception as e:
        print(f"\n!!! Test failed: {str(e)}")
        assert False, f"Failed to capture all screenshots: {str(e)}"

def test_dashboard_charts(browser_driver, extras):
    print("\n=== Starting dashboard charts test ===")

    screenshot_count = 0
    try:
        wait = WebDriverWait(browser_driver, 20)
        charts = [
            ("Batch per Day", "div.appsmith_widget_kj3cchthzg.container-with-scrollbar"),
            ("Testing by Tester", "div.appsmith_widget_9hvom3ohml.container-with-scrollbar"),
            ("Pending Requests by Owners", "div.appsmith_widget_vmn7ip43h1.container-with-scrollbar"),
            ("Volume per Batch", "div.appsmith_widget_3t5admj7fe.container-with-scrollbar")
        ]

        for label, selector in charts:
            print(f"\nProcessing chart: {label}")
            try:
                chart = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                browser_driver.execute_script("arguments[0].scrollIntoView(true);", chart)
                screenshot_filename = f"{screenshot_storage}/{label}.png"
                chart.screenshot(screenshot_filename)

                with open(screenshot_filename, "rb") as f:
                    img_base64 = base64.b64encode(f.read()).decode('utf-8')

                extras.append(pytest_html.extras.image(img_base64, mime_type="image/png"))
                print(f"\"{chart}\" chart loaded successfully!")
                print(f"✓ Screenshot attached: {label}.png")
                screenshot_count += 1

            except Exception as e:
                print(f"✖ Error capturing {label}: {str(e)}")
                raise

        print(f"\n=== Test completed: {screenshot_count}/{len(charts)} screenshots attached ===")
        assert screenshot_count == len(charts)

    except Exception as e:
        print(f"\n!!! Test failed: {str(e)}")
        assert False, f"Failed to capture all screenshots: {str(e)}"

def test_load_manage_batch(browser_driver, extras):
    try:
        print("\n=== Navigate to Manage Batch page ===")
        button = browser_driver.find_elements(By.CSS_SELECTOR, "button.bp3-button.bp3-fill.sc-klEEPK.fjNcfO[data-test-variant='TERTIARY']")
        manage_batch_button = button[1]
        browser_driver.execute_script("arguments[0].click();", manage_batch_button)
        print("Click on Manage Batch button to navigate to the page successfully!")
    except Exception as e:
        print("Error: loading the Manage Batch page.")
        assert False, str(e)

    try:
        print("\n=== Loading the Manage Batch page ===")
        element = WebDriverWait(browser_driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Manage Batch page loaded successfully!")
        time.sleep(5)

        screenshot_filename = f"{screenshot_storage}/Manage Batch page.png"
        element.screenshot(screenshot_filename)

        with open(screenshot_filename, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')

        extras.append(pytest_html.extras.image(img_base64, mime_type="image/png"))
        print(f"✓ Screenshot attached: {screenshot_filename}")

    except Exception as e:
        print(f"✖ Error capturing {screenshot_filename}: {str(e)}")
        raise

def test_barcode_display(browser_driver, extras):
    wait = WebDriverWait(browser_driver, 20)
    try:
        print("\n=== Check Barcode Image Display ===")

        # Wait for and click the first row in the table
        print("Waiting for table...")
        table = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div[data-widgetname-cy='all_request_table']")
        ))
        select_row = table.find_element(By.CSS_SELECTOR, "div.tr[role='button']")
        browser_driver.execute_script("arguments[0].click();", select_row)
        browser_driver.execute_script("arguments[0].click();", select_row)
        print("Row selected.")

        # Wait for barcode container
        print("Waiting for barcode container...")
        barcode_container = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "sc-jizTit.jNyFwB")
        ))

        print("Barcode container found. Searching for <img> tag...")
        img_elements = barcode_container.find_elements(By.TAG_NAME, "img")
        if not img_elements:
            print("No <img> element found inside barcode container.")
            return

        img_tag = img_elements[0]
        img_src = img_tag.get_attribute("src")
        print(f"Found image source: {img_src[:50]}...")

        # Check the src
        if img_src.startswith("data:image/png;base64"):
            print("Barcode image is present.")
        elif "default.png" in img_src:
            print("No barcode image (default placeholder).")
        else:
            print(f"Unexpected image src: {img_src}")

    except Exception as e:
        print("Error displaying barcode:", repr(e))

def test_button_availability(browser_driver):
    buttons = [
        ("Approve", "button.bp3-button.bp3-fill.sc-klEEPK.kDTWxe[data-test-variant='PRIMARY']"),
        ("Reject", "button.bp3-button.bp3-fill.sc-klEEPK.iqouFQ[data-test-variant='PRIMARY']"),
        ("Edit", "button.bp3-button.bp3-fill.sc-klEEPK.flhGLU[data-test-variant='PRIMARY']")
    ]
    for label, selector in buttons:
        try:
            print(f"\n=== Cheking {label} Button Availability ===")
            button = browser_driver.find_element(By.CSS_SELECTOR, selector)
            if button.is_displayed():
                print(f"{label} button is visible and available!")
            else:
                print(f"{label} button is not visible and available!")
        except NoSuchElementException:
            print(f"{label} button not found on the page.")

def test_load_manage_user(browser_driver, extras):
    try:
        print("\n=== Navigate to Manage User page ===")
        button = browser_driver.find_elements(By.CSS_SELECTOR, "button.bp3-button.bp3-fill.sc-klEEPK.fjNcfO[data-test-variant='TERTIARY']")
        manage_batch_button = button[2]
        browser_driver.execute_script("arguments[0].click();", manage_batch_button)
        print("Click on Manage User button to navigate to the page successfully!")
    except Exception as e:
        print("Error: loading the Manage User page.")
        assert False, str(e)

    try:
        print("\n=== Loading the Manage User page ===")
        element = WebDriverWait(browser_driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("Manage User page loaded successfully!")
        time.sleep(5)

        screenshot_filename = f"{screenshot_storage}/Manage User page.png"
        element.screenshot(screenshot_filename)

        with open(screenshot_filename, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')

        extras.append(pytest_html.extras.image(img_base64, mime_type="image/png"))
        print(f"✓ Screenshot attached: {screenshot_filename}")

    except Exception as e:
        print(f"✖ Error capturing {screenshot_filename}: {str(e)}")
        raise

def test_manage_user_functionality(browser_driver):
    wait = WebDriverWait(browser_driver, 20)
    try:
        print("\n=== User Management Table Test ===")
        table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-widgetname-cy='admin_table']")))
        rows = table.find_elements(By.CSS_SELECTOR, "div.tr[role='button']")

        if not rows:
            print("No rows found in 'awaiting_test_table'.")
            return

        for index, row in enumerate(rows):
            browser_driver.execute_script("arguments[0].scrollIntoView(true);", row)
            browser_driver.execute_script("arguments[0].click();", row)
            print(f"Row {index + 1}/{len(rows)} selected successfully.")

    except Exception as e:
        print("Error selecting row:", e)

def test_buttons_disabled_when_no_row_selected(browser_driver):
    wait = WebDriverWait(browser_driver, 20)
    try:
        table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-widgetname-cy='admin_table']")))
        selected_rows = table.find_elements(By.CSS_SELECTOR, "div.tr.selected-row")
        for row in selected_rows:
            browser_driver.execute_script("arguments[0].scrollIntoView(true);", row)
            browser_driver.execute_script("arguments[0].click();", row)

        deselected_check = table.find_elements(By.CSS_SELECTOR, "div.tr.selected-row")
        assert len(deselected_check) == 0, "A row is still selected after attempting to deselect."

        disabled_buttons = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.sc-QlApj[disabled]")
        ))

        edit_found = False
        delete_found = False

        for button_container in disabled_buttons:
            try:
                span = button_container.find_element(By.CSS_SELECTOR, "span.bp3-button-text")
                text = span.text.strip()

                if text == "Edit Account":
                    edit_found = True
                    assert "dMqDPw" in button_container.get_attribute("class"), "Edit button not in disabled class state."
                elif text == "Delete Account":
                    delete_found = True
                    assert "dMqDPw" in button_container.get_attribute("class"), "Delete button not in disabled class state."

            except Exception as inner_e:
                continue  # Ignore malformed buttons

        assert edit_found, "Disabled Edit Account button not found."
        assert delete_found, "Disabled Delete Account button not found."

        print("Both 'Edit Account' and 'Delete Account' buttons are correctly disabled when no row is selected.")

    except Exception as e:
        print("Error checking disabled buttons.")
        assert False, str(e)

def test_buttons_enabled_when_row_selected(browser_driver):
    wait = WebDriverWait(browser_driver, 20)
    try:
        table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-widgetname-cy='admin_table']")))
        select_row = table.find_element(By.CSS_SELECTOR, "div.tr[role='button']")
        browser_driver.execute_script("arguments[0].scrollIntoView(true);", select_row)
        browser_driver.execute_script("arguments[0].click();", select_row)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tr.selected-row")))
        selected_rows = table.find_elements(By.CSS_SELECTOR, "div.tr.selected-row")
        assert len(selected_rows) == 1, "A row is not selected after attempting to select."

        enabled_buttons = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.sc-QlApj")
        ))

        edit_found = False
        delete_found = False

        for button_container in enabled_buttons:
            try:
                span = button_container.find_element(By.CSS_SELECTOR, "span.bp3-button-text")
                text = span.text.strip()

                if text == "Edit Account":
                    edit_found = True
                    assert "bdMtGF" in button_container.get_attribute("class"), "Edit button not in enabled class state."
                elif text == "Delete Account":
                    delete_found = True
                    assert "bdMtGF" in button_container.get_attribute("class"), "Delete button not in enabled class state."

            except Exception as inner_e:
                continue  # Ignore malformed buttons

        assert edit_found, "Enabled Edit Account button not found."
        assert delete_found, "Enabled Delete Account button not found."

        print("Both 'Edit Account' and 'Delete Account' buttons are correctly enabled when a row is selected.")

    except Exception as e:
        print("Error checking enabled buttons.")
        assert False, str(e)

def test_logout(browser_driver):
    try:
        print("\n=== Testing Logout Functionality ===")
        logout_icon = WebDriverWait(browser_driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.bp3-icon.bp3-icon-log-out")))
        clickable_element = logout_icon.find_element(By.XPATH, "./ancestor::button | ./ancestor::div")
        browser_driver.execute_script("arguments[0].scrollIntoView(true);", clickable_element)
        browser_driver.execute_script("arguments[0].click();", clickable_element)
        print("Logout clicked successfully!")

    except Exception as e:
        print("Error: failed to logout.", str(e))
        assert False, str(e)