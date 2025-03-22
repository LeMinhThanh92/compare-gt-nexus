import os
import shutil
import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
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
    _tableWeekly = pd.read_excel(_file_import
                                 , sheet_name=0
                                 )
    # _now = datetime.today()
    # _currentMonth = (_now.month % 12)
    # _currentYear = _now.year + (_currentMonth == 1)
    # _tableWeekly['Schedule ex.Factory'] = pd.to_datetime(_tableWeekly['Schedule ex.Factory'], errors='coerce')
    # _filterRow = _tableWeekly[_tableWeekly['Schedule ex.Factory'].dt.month == _currentMonth].copy()

    so_string = ",".join(_tableWeekly['SO'].dropna().astype(str).unique())
    url = "https://ax.allianceone.com.vn/namespaces/AXSF/?cmp=A1A&mi=SalesLineOpenOrder"
    driver.get(url)

    wait = WebDriverWait(driver, 15)

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

    sales_order = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#SalesLine_SalesNum_3_0_header > .dyn-headerCellLabel"))
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

    # Check if it contains '*'
    _count = 0
    while '*' not in view_name_text:
        time.sleep(5)
        _count += 5
        view_name_text = view_name.text
        print(_count)
    time.sleep(5)
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

    while True:
        files = os.listdir(folder_path_download)
        matching_files = [file for file in files if "Order lines" in file]

        if matching_files:
            for file in matching_files:
                source_path = os.path.join(folder_path_download, file)
                destination_path = os.path.join(destination_dir, file)

                shutil.move(source_path, destination_path)
                print(f"Moved file: {file} to {destination_dir}")
                driver.quit()
            return True

        time.sleep(10)

# result = run_and_check_download(r"C:\Users\Admin\Downloads\Check price\Check price\Result\Old\Sample20250305084736\Down"
#                                 ,r'C:\Users\Admin\Downloads\Check price\Check price\Result\Old\FolderBulk20250305080356\Copy of WEEKLY SHIPMENT ADIDAS 2025--shipment mar.xlsx'
#                                 ,r'C:\Users\Admin\Downloads\Check price\Check price\Bulk')
# print(result)
