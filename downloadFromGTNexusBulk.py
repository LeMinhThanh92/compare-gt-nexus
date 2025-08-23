import os
import shutil
import time
import traceback

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait


def run_and_check_download(folder_path_download, _file_import, destination_dir, max_retries=5):
    retry_count = 0
    driver = None

    def read_excel_with_header_detection(file_path, sheet_name=0, dtype=None):
        """
        Read Excel file and detect if first row is N/A, then use second row as header
        """
        # First, read just the first two rows to check the header
        temp_df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=2, header=None)

        # Check if first cell [0,0] is N/A, NaN, or similar
        first_cell = temp_df.iloc[0, 0]

        # Check for various forms of N/A
        if (pd.isna(first_cell) or
                str(first_cell).upper() in ['N/A', 'NA', 'NULL', '#N/A'] or
                first_cell == ''):

            print("First row appears to be N/A, using second row as header")
            # Use second row (index 1) as header
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=1, dtype=dtype)
        else:
            print("Using first row as header")
            # Use first row (index 0) as header (default)
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=0, dtype=dtype)

        return df

    while retry_count < max_retries:
        try:
            print(f"Attempt {retry_count + 1}/{max_retries} to download from GTNexus")

            # Make sure the driver is closed from any previous attempts
            if driver:
                try:
                    driver.quit()
                    print("Closed browser from previous attempt")
                except:
                    pass
                driver = None

            # Setup WebDriver
            options = webdriver.EdgeOptions()
            prefs = {"download.default_directory": folder_path_download}
            options.add_experimental_option("prefs", prefs)
            options.add_experimental_option("detach", True)
            # options.add_argument("--headless")
            # options.add_argument("--disable-gpu")
            # options.add_argument("--window-size=1920x1080")
            driver = webdriver.Edge(options=options)

            # Read Excel file and prepare PO string
            _tableWeekly = read_excel_with_header_detection(_file_import, sheet_name=0, dtype={"PO": str})
            _tableWeekly['PO'] = _tableWeekly['PO'].astype(str)
            po_string = ",".join(_tableWeekly['PO'].dropna().astype(str).unique())
            url = "https://network.infornexus.com/en/trade/ReportRun?key=432826891033"
            driver.get(url)

            # Login
            username_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "login"))
            )
            username_field.send_keys("213001_T&A")

            password_field = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_field.send_keys("a1ateam@123")

            login_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "loginButton"))
            )
            login_button.click()

            # Wait for page to load
            time.sleep(10)

            # Find select elements
            try:
                select_elements = WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "predicateoperator"))
                )

                # Select seller party
                seller_party = Select(select_elements[0])
                seller_party.select_by_index(2)
            except Exception as e:
                print(f"Error finding select elements: {str(e)}")
                raise Exception("Failed to find or interact with select elements")

            # Select party
            try:
                select_party = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         "//span[@class='gwt-InlineHTML partysearch-onelineinnerdiv']/i[text()='Select a party']"))
                )
                select_party.click()

                select_party_value = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//a[@class='gwt-Anchor' and text()='5717-9890-1825-2755']"))
                )
                select_party_value.click()
            except Exception as e:
                print(f"Error selecting party: {str(e)}")
                raise Exception("Failed to select party value")

            # Enter PO information
            try:
                po = Select(select_elements[12])
                po.select_by_index(7)

                po_select = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH,
                                                "//textarea[@class='gwt-TextArea valuewidgettextbox' and contains(@style, 'vertical-align: middle')]"))
                )
                po_select.click()
                po_select.send_keys(po_string)
            except Exception as e:
                print(f"Error entering PO information: {str(e)}")
                raise Exception("Failed to enter PO information")

            # Click Run button
            try:
                button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Run']"))
                )
                button.click()
            except Exception as e:
                print(f"Error clicking Run button: {str(e)}")
                raise Exception("Failed to click Run button")

            # Wait for download with timeout
            download_timeout = 600  # 2 minutes to wait for download
            download_start_time = time.time()
            download_success = False

            while time.time() - download_start_time < download_timeout:
                files = os.listdir(folder_path_download)
                matching_files = [file for file in files if "A1A+Released+Order" in file]

                if matching_files:
                    for file in matching_files:
                        source_path = os.path.join(folder_path_download, file)
                        destination_path = os.path.join(destination_dir, file)

                        # Check if file is being written to
                        try:
                            # Wait a bit to ensure file is fully downloaded
                            time.sleep(3)

                            # Try to move the file
                            shutil.move(source_path, destination_path)
                            print(f"Successfully moved file: {file} to {destination_dir}")
                            download_success = True
                        except (PermissionError, OSError) as e:
                            print(f"File still being written to: {e}")
                            time.sleep(2)
                            continue

                if download_success:
                    break

                time.sleep(10)
                print(f"Waiting for download... Elapsed: {int(time.time() - download_start_time)}s")

            # Check if download was successful
            if not download_success:
                raise Exception("Download timed out or failed")

            # Clean up and return success
            if driver:
                driver.quit()
                print("Browser closed successfully after download")
            return True

        except Exception as e:
            retry_count += 1
            error_message = f"Error on attempt {retry_count}/{max_retries}: {str(e)}"
            print(error_message)
            print(f"Stack trace: {traceback.format_exc()}")

            # Make sure to close the browser before retrying
            if driver:
                try:
                    driver.quit()
                    print("Closed browser after error")
                except:
                    print("Failed to close browser")

            if retry_count >= max_retries:
                print(f"Maximum retries ({max_retries}) reached. Download failed.")
                return False

            # Wait before retrying - exponential backoff
            wait_time = 5 * (2 ** retry_count)  # 10, 20, 40 seconds
            print(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)

    return False

# Example usage:
# result = run_and_check_download(r"C:\Compare\Result\Download"
#                                 ,
#                                 r'C:\Compare\Result\Old\Bulk20250324143931\Copy of WEEKLY SHIPMENT ADIDAS 2025--shipment mar.xlsx'
#                                 , r'C:\Compare\Bulk')
# print(result)
