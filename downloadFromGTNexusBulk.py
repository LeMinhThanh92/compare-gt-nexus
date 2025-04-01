import os
import shutil
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait


def run_and_check_download(folder_path_download, _file_import, destination_dir):
    options = webdriver.EdgeOptions()
    prefs = {"download.default_directory": folder_path_download}
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("detach", True)
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--window-size=1920x1080")
    driver = webdriver.Edge(options=options)
    _tableWeekly = pd.read_excel(_file_import, sheet_name=0)
    po_string = ",".join(_tableWeekly['PO'].dropna().astype(str).unique())
    url = "https://network.infornexus.com/en/trade/ReportRun?key=432826891033"
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

    po = Select(select_elements[12])
    po.select_by_index(7)
    po_select = driver.find_element(By.XPATH,
                                    "//textarea[@class='gwt-TextArea valuewidgettextbox' and contains(@style, 'vertical-align: middle')]")
    po_select.click()

    po_select.send_keys(po_string)
    button = driver.find_element(By.XPATH, "//button[text()='Run']")
    button.click()

    # destination_dir = r'C:\Compare\Sample'
    while True:
        files = os.listdir(folder_path_download)
        matching_files = [file for file in files if "A1A+Released+Order" in file]

        if matching_files:
            for file in matching_files:
                source_path = os.path.join(folder_path_download, file)
                destination_path = os.path.join(destination_dir, file)

                shutil.move(source_path, destination_path)
                print(f"Moved file: {file} to {destination_dir}")
                driver.quit()
            return True

        time.sleep(10)

# result = run_and_check_download(r"C:\Compare\Result\Download"
#                                 ,
#                                 r'C:\Compare\Result\Old\Bulk20250324143931\Copy of WEEKLY SHIPMENT ADIDAS 2025--shipment mar.xlsx'
#                                 , r'C:\Compare\Bulk')
# print(result)
