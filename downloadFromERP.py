import os
import shutil
import time
import traceback

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
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
            print(f"Attempt {retry_count + 1}/{max_retries} to download from ERP")

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

            # Read Excel file
            _tableWeekly = read_excel_with_header_detection(_file_import, sheet_name=0)

            so_string = ",".join(_tableWeekly['SO'].dropna().astype(str).unique())
            url = "https://ax.allianceone.com.vn/namespaces/AXSF/?cmp=A1A&mi=SalesLineOpenOrder"
            driver.get(url)

            wait = WebDriverWait(driver, 15)

            # Login
            username_field = wait.until(
                EC.presence_of_element_located((By.ID, "userNameInput"))
            )
            username_field.send_keys("digitalization@allianceone.com.vn")

            password_field = wait.until(
                EC.presence_of_element_located((By.ID, "passwordInput"))
            )
            password_field.send_keys("giDDt@@98765")

            login_button = wait.until(
                EC.element_to_be_clickable((By.ID, "submitButton"))
            )
            login_button.click()

            time.sleep(5)

            date_begin = wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@id='SalesLine_SalesNum_3_0_0_input']"))
            )

            sales_order = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#SalesLine_SalesNum_3_0_header > .dyn-headerCellLabel"))
            )
            sales_order.click()

            sales_order_filter = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input#__FilterField_SalesLine_SalesNum_SalesId_Input_0_input"))
            )
            sales_order_filter.click()
            sales_order_filter.clear()
            sales_order_filter.send_keys(so_string)
            sales_order_filter.send_keys(Keys.ENTER)

            view_name = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "span#saleslineopenorder_1_SystemDefinedManageViewFilters_label"))
            )

            view_name_text = view_name.text
            date_begin_text = date_begin.get_attribute("value")

            # Check if it contains '*'
            _count = 0
            wait_limit = 600  # Add a maximum wait time of 60 seconds
            while '*' not in view_name_text and date_begin.get_attribute(
                    "value") == date_begin_text and _count < wait_limit:
                time.sleep(5)
                _count += 5
                view_name_text = view_name.text
                print(f"Waiting for data to load: {_count} seconds")

            # If we've waited too long without seeing the expected condition
            if _count >= wait_limit:
                raise Exception("Timed out waiting for data to load")

            time.sleep(15)
            btn_download = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "span.MicrosoftOffice-symbol"))
            )
            btn_download.click()

            btn_download1 = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "span#saleslineopenorder_1_SystemDefinedOfficeButton_Grid_SalesLine_label"))
            )
            btn_download1.click()

            time.sleep(5)
            btn_download2 = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@name='DownloadButton']"))
            )
            time.sleep(5)
            btn_download2.click()

            # Wait for download with timeout
            download_timeout = 600  # 60 seconds to wait for download
            download_start_time = time.time()
            download_success = False

            while time.time() - download_start_time < download_timeout:
                files = os.listdir(folder_path_download)
                matching_files = [file for file in files if "Order lines" in file]

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

                time.sleep(5)
                print(f"Waiting for download... Elapsed: {int(time.time() - download_start_time)}s")

            # Check if download was successful
            if not download_success:
                raise Exception("Download timed out or failed")

            # Clean up and return success
            if driver:
                driver.quit()
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
# result = run_and_check_download(r"C:\Compare\Result\Old\Sample20250305084736\Down"
#                                 ,r'C:\Compare\Result\Old\FolderBulk20250305080356\Copy of WEEKLY SHIPMENT ADIDAS 2025--shipment mar.xlsx'
#                                 ,r'C:\Compare\Bulk')
# print(result)
