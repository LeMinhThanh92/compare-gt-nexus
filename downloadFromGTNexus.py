import calendar
import os
import shutil
import time
import traceback

import pandas as pd
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

from fileConfig import _dtypeSample


def run_and_check_download(folder_path_download, _file_import, destination_dir, mode='A1A', max_retries=5):
    retry_count = 0
    driver = None

    print(mode)

    # Read only the required CUSTREQDATE column once before the retry loop
    _tableSample = pd.read_excel(
        _file_import,
        dtype={'CUSTREQDATE': str},
        sheet_name='Sheet1',
        usecols=['CUSTREQDATE']
    )
    _tableSample['CUSTREQDATE'] = pd.to_datetime(_tableSample['CUSTREQDATE'], errors='coerce')

    min_date = pd.Timestamp(_tableSample['CUSTREQDATE'].min())
    max_date = pd.Timestamp(_tableSample['CUSTREQDATE'].max())
    min_date = min_date.replace(day=1).strftime('%Y-%m-%d')
    next_month = max_date.month + 2
    year_offset = max_date.year + (next_month - 1) // 12
    next_month = (next_month - 1) % 12 + 1  # Ensure month is between 1-12

    # Get the last day of that month
    last_day = calendar.monthrange(year_offset, next_month)[1]
    max_date = max_date.replace(year=year_offset, month=next_month, day=last_day).strftime('%Y-%m-%d')

    first_day_minus_6_months = (_tableSample['CUSTREQDATE'].max() - relativedelta(months=5)).replace(
        day=1).strftime(
        '%Y-%m-%d')

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

            url = "https://network.infornexus.com/en/trade/ReportRun.jsp?key=357945647677#"
            driver.get(url)
            # is_trx_file = 'TRX' in os.path.basename(_file_import).upper()
            username = '213001_T&A'
            password = 'Ear@123123!@#'
            company = '5717-9890-1825-2755'
            if mode == 'TRX':
                username = 'Q5S001-SAMPLE'
                password = 'Q5S001_2024@mt'
                company = '5717-9890-1834-7753'

            # Login with better error handling
            try:
                username_field = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.ID, "login"))
                )
                username_field.send_keys(username)

                password_field = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.ID, "password"))
                )
                password_field.send_keys(password)

                login_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "loginButton"))
                )
                login_button.click()
            except Exception as e:
                print(f"Error during login: {str(e)}")
                raise Exception("Failed to complete login process")

            # Wait for page to load
            time.sleep(10)

            # Form filling with better error handling
            try:
                select_elements = WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "predicateoperator"))
                )

                seller_party = Select(select_elements[0])
                seller_party.select_by_index(2)

                select_party = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.XPATH,
                         "//span[@class='gwt-InlineHTML partysearch-onelineinnerdiv']/i[text()='Select a party']"))
                )
                select_party.click()

                select_party_value = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f"//a[@class='gwt-Anchor' and text()='{company}']"))
                )
                select_party_value.click()
            except Exception as e:
                print(f"Error selecting party: {str(e)}")
                raise Exception("Failed to select party")

            try:
                po_delivery_date = Select(select_elements[3])
                po_delivery_date.select_by_index(8)
                ele = driver.find_elements(By.CSS_SELECTOR, ".valuewidgetdatebox")
                ele[0].clear()
                ele[0].send_keys(min_date)
                ele[1].clear()
                ele[1].send_keys(max_date)
                po_s_delivery_date = Select(select_elements[4])
                po_s_delivery_date.select_by_index(8)
                ele = driver.find_elements(By.CSS_SELECTOR, ".valuewidgetdatebox")
                ele[2].clear()
                ele[2].send_keys(min_date)
                ele[3].clear()
                ele[3].send_keys(max_date)
                time.sleep(2)
                issue_date = Select(select_elements[8])
                issue_date.select_by_index(8)
                ele = driver.find_elements(By.CSS_SELECTOR, ".valuewidgetdatebox")
                ele[4].clear()
                ele[4].send_keys(first_day_minus_6_months)
                ele[5].clear()
                ele[5].send_keys(max_date)
                time.sleep(2)
            except Exception as e:
                print(f"Error setting dates: {str(e)}")
                raise Exception("Failed to set dates")

            try:
                option3 = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@id='navbarsearch']"))
                )
                option3.click()

                devision = Select(select_elements[9])
                devision.select_by_index(3)
                devision_select = driver.find_element(By.ID, "gwt_uid_36")
                devision_select.click()
                Select(devision_select).deselect_all()
                # devision_select = driver.find_element(By.XPATH, "(//select)[21]")
                # devision_select.click()
                # devision_select = driver.find_element(By.XPATH, "(//select)[21]")
                # devision_select.click()

                option1 = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//option[@value='02']"))
                )
                option1.click()

                order = Select(select_elements[10])
                order.select_by_index(3)
                order_select = driver.find_element(By.ID, "gwt_uid_37")
                order_select.click()
                Select(order_select).deselect_all()

                option1 = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//option[text()='Sample']"))
                )
                option1.click()
                time.sleep(2)
            except Exception as e:
                print(f"Error selecting options: {str(e)}")
                raise Exception("Failed to select options")

            # Click Run button
            try:
                button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Run']"))
                )
                button.click()
            except Exception as e:
                print(f"Error clicking Run button: {str(e)}")
                raise Exception("Failed to click Run button")

            # Improved download waiting mechanism
            download_timeout = 600  # 5 minutes to wait for download
            download_start_time = time.time()
            download_success = False

            print("Waiting for download to complete...")

            while time.time() - download_start_time < download_timeout:
                files = os.listdir(folder_path_download)
                matching_files = [file for file in files if "A1A Released Order" in file]

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
                raise Exception(f"Download timed out after {download_timeout} seconds")

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
# result = run_and_check_download(r"C:\Compare\Result\Old\Sample20250305084736\Down"
#                                 ,r'C:\Compare\Result\Old\Sample20250305084736\Import sales order original template- Monthly.xlsx'
#                                 ,r'C:\Compare\Sample')
# print(result)
