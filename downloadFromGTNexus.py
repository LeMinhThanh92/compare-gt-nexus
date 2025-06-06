import calendar
import os
import shutil
import time

import pandas as pd
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait

from fileConfig import _dtypeSample


def run_and_check_download(folder_path_download, _file_import, destination_dir):
    options = webdriver.EdgeOptions()
    prefs = {"download.default_directory": folder_path_download}
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("detach", True)
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--window-size=1920x1080")
    driver = webdriver.Edge(options=options)
    _tableSample = pd.read_excel(_file_import
                                 , dtype=_dtypeSample
                                 , sheet_name='Sheet1'
                                 )
    _tableSample['CUSTREQDATE'] = pd.to_datetime(_tableSample['CUSTREQDATE'], errors='coerce')

    # min_date = _tableSample['CUSTREQDATE'].min().strftime('%Y-%m-%d')
    # max_date = _tableSample['CUSTREQDATE'].max().strftime('%Y-%m-%d')
    min_date = pd.Timestamp(_tableSample['CUSTREQDATE'].min())
    max_date = pd.Timestamp(_tableSample['CUSTREQDATE'].max())
    min_date = min_date.replace(day=1).strftime('%Y-%m-%d')
    next_month = max_date.month + 2
    year_offset = max_date.year + (next_month - 1) // 12
    next_month = (next_month - 1) % 12 + 1  # Ensure month is between 1-12

    # Get the last day of that month
    last_day = calendar.monthrange(year_offset, next_month)[1]
    max_date = max_date.replace(year=year_offset, month=next_month, day=last_day).strftime('%Y-%m-%d')

    first_day_minus_6_months = (_tableSample['CUSTREQDATE'].max() - relativedelta(months=5)).replace(day=1).strftime(
        '%Y-%m-%d')
    url = "https://network.infornexus.com/en/trade/ReportRun.jsp?key=357945647677#"
    driver.get(url)

    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "login"))
    )
    username_field.send_keys("213001_T&A")

    password_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "password"))
    )
    password_field.send_keys("a1ateam@123")

    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "loginButton"))
    )
    login_button.click()

    time.sleep(5)

    select_elements = driver.find_elements(By.CLASS_NAME, "predicateoperator")

    seller_party = Select(select_elements[0])
    seller_party.select_by_index(2)

    select_party = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//span[@class='gwt-InlineHTML partysearch-onelineinnerdiv']/i[text()='Select a party']"))
    )
    select_party.click()

    select_party_value = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//a[@class='gwt-Anchor' and text()='5717-9890-1825-2755']"))
    )
    select_party_value.click()

    # script = """
    # var parentSpan = document.querySelector('.partysearch-onelineinnerdiv');
    # parentSpan.innerHTML = '';
    #
    # var newTag = document.createElement('b');
    # newTag.textContent = 'WELLCORP HOLDINGS TRADING HK LIMITED(213)';
    # parentSpan.appendChild(newTag);
    #
    # var newSpan = document.createElement('span');
    # newSpan.className = 'orgid';
    # newSpan.textContent = '5717-9890-1825-2755';
    # parentSpan.appendChild(newSpan);
    # """
    # driver.execute_script(script)
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
    option3 = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@id='navbarsearch']"))
    )
    option3.click()

    devision = Select(select_elements[9])
    devision.select_by_index(3)
    devision_select = driver.find_element(By.ID, "gwt_uid_35")
    devision_select.click()
    Select(devision_select).deselect_all()

    option1 = WebDriverWait(driver, 10).until(
        # EC.presence_of_element_located((By.XPATH, "//option[text()='02']"))
        EC.element_to_be_clickable((By.XPATH, "//option[@value='02']"))
    )
    option1.click()

    order = Select(select_elements[10])
    order.select_by_index(3)
    order_select = driver.find_element(By.ID, "gwt_uid_36")
    order_select.click()
    Select(order_select).deselect_all()

    option1 = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//option[text()='Sample']"))
    )
    option1.click()
    time.sleep(2)
    button = driver.find_element(By.XPATH, "//button[text()='Run']")
    button.click()

    # destination_dir = r'C:\Compare\Sample'
    while True:
        files = os.listdir(folder_path_download)
        matching_files = [file for file in files if "adidas+Released+Order" in file]

        if matching_files:
            for file in matching_files:
                source_path = os.path.join(folder_path_download, file)
                destination_path = os.path.join(destination_dir, file)

                shutil.move(source_path, destination_path)
                print(f"Moved file: {file} to {destination_dir}")
                driver.quit()
            return True

        time.sleep(10)

# result = run_and_check_download(r"C:\Compare\Result\Old\Sample20250305084736\Down"
#                                 ,r'C:\Compare\Result\Old\Sample20250305084736\Import sales order original template- Monthly.xlsx'
#                                 ,r'C:\Compare\Sample')
# print(result)
