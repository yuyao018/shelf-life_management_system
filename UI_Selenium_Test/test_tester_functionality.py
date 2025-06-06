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

# python -m pytest testing/tester_test.py --html=testing/report_tester.html --self-contained-html

screenshot_storage = "your/path/to/store/screenshots"

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
    email.send_keys("liamtan@gmail.com")
    print("Email input successfully!")

    password = inputs[1]
    password.send_keys("tester1234")
    print("Password input successfully!")

    button = browser_driver.find_element(By.CSS_SELECTOR, "button.bp3-button.bp3-fill[data-test-variant='PRIMARY']")
    # selenium can't click on the button, there is something blocking it. Hence, Javascript is used to click the button.
    browser_driver.execute_script("arguments[0].click();", button)
    print("Click on the Log In button successfully!")

    time.sleep(5)

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

def test_navbar(browser_driver):
    wait = WebDriverWait(browser_driver, 20)
    try:
        print("\n=== Navigate to Manage Batch page ===")
        button = browser_driver.find_elements(By.CSS_SELECTOR, "button.bp3-button.bp3-fill.sc-klEEPK.fjNcfO[data-test-variant='TERTIARY']")
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

def test_dashboard_cards(browser_driver, extras):
    print("\n=== Starting dashboard cards test ===")

    screenshot_count = 0
    try:
        wait = WebDriverWait(browser_driver, 20)
        cards = [
            ("Testing Not Started", "div.appsmith_widget_eq5bougz5b.container-with-scrollbar"),
            ("Testing In Progress", "div.appsmith_widget_s0qyy4q5ya.container-with-scrollbar"),
            ("Completed Testing", "div.appsmith_widget_4wpzc8etwg.container-with-scrollbar"),
            ("My Testing In Progress", "div.appsmith_widget_x5wts1c7e5.container-with-scrollbar"),
            ("My Completed Testing", "div.appsmith_widget_viydivs5n5.container-with-scrollbar")
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
            ("Testing by Tester", "div.appsmith_widget_9hvom3ohml.container-with-scrollbar"),
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

def test_awaiting_tester_table_functionality(browser_driver, index=0):
    wait = WebDriverWait(browser_driver, 20)
    try:
        print("\n=== Testing Awaiting Tester Table Row Selection ===")
        table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-widgetname-cy='awaiting_test_table']")))
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

    try:
        time.sleep(1)
        print("\n=== Checking Barcode Generation During Awaiting Tester Table Row Selection ===")
        print("Waiting for barcode container...")
        barcode_container = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "sc-jizTit")
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

    try:
        print("\n=== Checking Assign Button Availability During Awaiting Tester Table Row Selection ===")
        assign_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.bp3-button.bp3-fill.sc-klEEPK.flhGLU[data-test-variant='PRIMARY']")))
        if assign_button.is_displayed():
                print("Assign button is visible and available!")
        else:
            print("Assign button is not visible and available!")
    except NoSuchElementException:
            print("Assign button not found on the page.")

def test_my_assigned_test_table_functionality(browser_driver, index=0):
    wait = WebDriverWait(browser_driver, 20)
    try:
        print("\n=== Testing My Assigned Test Table Row Selection ===")
        table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-widgetname-cy='my_assigned_test_table']")))
        rows = table.find_elements(By.CSS_SELECTOR, "div.tr[role='button']")

        if not rows:
            print("No rows found in 'My Assigned Test table'.")
            return

        for index, row in enumerate(rows):
            browser_driver.execute_script("arguments[0].scrollIntoView(true);", row)
            browser_driver.execute_script("arguments[0].click();", row)
            print(f"Row {index + 1}/{len(rows)} selected successfully.")

    except Exception as e:
        print("Error selecting row:", e)

    try:
        time.sleep(1)
        print("\n=== Checking Barcode Generation During My Assigned Test Table Row Selection ===")
        print("Waiting for barcode container...")
        barcode_container = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "sc-jizTit")
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

    try:
        print("\n=== Checking Completed Button Availability During My Assigned Test Table Row Selection ===")
        completed_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.bp3-button.bp3-fill.sc-klEEPK.kDTWxe[data-test-variant='PRIMARY']")))
        if completed_button.is_displayed():
                print("Completed button is visible and available!")
        else:
            print("Completed button is not visible and available!")
    except NoSuchElementException:
            print("Completed button not found on the page.")

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