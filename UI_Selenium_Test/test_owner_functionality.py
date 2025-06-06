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

# python -m pytest testing/owner_test.py --html=testing/report_owner.html --self-contained-html

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
    email.send_keys("benjaminlim@gmail.com")
    print("Email input successfully!")

    password = inputs[1]
    password.send_keys("owner12345")
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
            ("Maturity Overview", "div.appsmith_widget_fobvnj1l0q.container-with-scrollbar"),
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

        try:
            volume_per_batch_chart = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.appsmith_widget_3t5admj7fe.container-with-scrollbar")))
            browser_driver.execute_script("arguments[0].scrollIntoView(true);", volume_per_batch_chart)
            screenshot_filename = f"{screenshot_storage}/Volume per Batch.png"
            volume_per_batch_chart.screenshot(screenshot_filename)

            with open(screenshot_filename, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode('utf-8')

            extras.append(pytest_html.extras.image(img_base64, mime_type="image/png"))
            print(f"\"Volume per Batch\" chart loaded successfully!")
            print(f"✓ Screenshot attached: {screenshot_filename}")
            screenshot_count += 1

        except Exception as e:
            print(f"✖ Error capturing {screenshot_filename}: {str(e)}")
            raise
    except Exception as e:
        print("Error: loading one or more tables in Dashboard page.")
        assert False, str(e)

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
        time.sleep(2)

        screenshot_filename = f"{screenshot_storage}/Manage Batch page.png"
        element.screenshot(screenshot_filename)

        with open(screenshot_filename, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')

        extras.append(pytest_html.extras.image(img_base64, mime_type="image/png"))
        print(f"✓ Screenshot attached: {screenshot_filename}")

    except Exception as e:
        print(f"✖ Error capturing {screenshot_filename}: {str(e)}")
        raise

def test_load_new_request_form(browser_driver, extras):
    wait = WebDriverWait(browser_driver, 20)
    try:
        print("\n=== Navigate to New Request form ===")
        button = browser_driver.find_elements(By.CSS_SELECTOR, "button.bp3-button.bp3-fill.sc-klEEPK.dIYoez[data-test-variant='TERTIARY']")
        new_request_button = button[1]
        browser_driver.execute_script("arguments[0].click();", new_request_button)
        print("Click on New Request button to navigate to the form successfully!")
    except Exception as e:
        print("Error: loading the New Request form.")
        assert False, str(e)
    time.sleep(5)

    try:
        print("\n=== Loading the New Request form ===")
        element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.appsmith_widget_n9myayjoxe.container-with-scrollbar")))
        print("New Request form loaded successfully!")
        time.sleep(5)

        screenshot_filename = f"{screenshot_storage}/New Request form.png"
        element.screenshot(screenshot_filename)

        with open(screenshot_filename, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')

        extras.append(pytest_html.extras.image(img_base64, mime_type="image/png"))
        print(f"✓ Screenshot attached: {screenshot_filename}")

    except Exception as e:
        print(f"✖ Error capturing {screenshot_filename}: {str(e)}")
        raise

    try:
        print("\n=== Checking Submit Button Availability in New Request Form ===")
        submit_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.bp3-button.bp3-fill.sc-klEEPK.cUnEoh[data-test-variant='PRIMARY']")))
        if submit_button.is_displayed():
            print("Submit button is visible and available!")
        else:
            print("Submit button is not visible and available!")
    except NoSuchElementException:
            print("Submit button not found on the page.")

def test_load_my_request(browser_driver, extras):
    try:
        print("\n=== Navigate to My Request section ===")
        button = browser_driver.find_elements(By.CSS_SELECTOR, "button.bp3-button.bp3-fill.sc-klEEPK.dIYoez[data-test-variant='TERTIARY']")
        new_request_button = button[0]
        browser_driver.execute_script("arguments[0].click();", new_request_button)
        print("Click on New Request button to navigate to the section successfully!")
    except Exception as e:
        print("Error: loading the New Request form.")
        assert False, str(e)
    time.sleep(5)

    try:
        print("\n=== Loading the My Request section ===")
        element = WebDriverWait(browser_driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.appsmith_widget_ar5ig8gfix.container-with-scrollbar")))
        print("New Request section loaded successfully!")
        time.sleep(5)

        screenshot_filename = f"{screenshot_storage}/New Request section.png"
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
        time.sleep(1)
        browser_driver.execute_script("arguments[0].click();", select_row)
        time.sleep(1)
        print("Row selected.")

        # Wait for barcode container
        print("Waiting for barcode container...")
        barcode_container = wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "sc-jizTit.gWVvrW")
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

def test_my_request_table_functionality(browser_driver):
    wait = WebDriverWait(browser_driver, 20)
    try:
        print("\n=== Testing My Request Table Row Selection ===")
        table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-widgetname-cy='all_request_table']")))
        rows = table.find_elements(By.CSS_SELECTOR, "div.tr[role='button']")

        if not rows:
            print("No rows found in 'My Request Table'.")
            return

        for index, row in enumerate(rows):
            browser_driver.execute_script("arguments[0].scrollIntoView(true);", row)
            browser_driver.execute_script("arguments[0].click();", row)
            print(f"Row {index + 1}/{len(rows)} selected successfully.")

    except Exception as e:
        print("Error selecting row:", e)

    try:
        print("\n=== Checking Cancel Button Availability During My Request Table Row Selection ===")
        cancel_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.bp3-button.bp3-fill.sc-klEEPK.iqouFQ[data-test-variant='PRIMARY']")))
        if cancel_button.is_displayed():
                print("Cancel button is visible and available!")
        else:
            print("Cancel button is not visible and available!")
    except NoSuchElementException:
            print("Cancel button not found on the page.")

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
