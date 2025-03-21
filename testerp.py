from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from datetime import datetime
import os
import shutil
def run_and_check_download():
    options = webdriver.EdgeOptions()
    download_dir = r"C:\Users\Admin\Downloads\Check price\Check price\Result\Old\Sample20250305084736\Down"
    prefs = {"download.default_directory": download_dir}
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("detach", True)
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--window-size=1920x1080")
    driver = webdriver.Edge(options=options)
    # _file_import = r'C:\Users\Admin\Downloads\Check price\Check price\Result\Old\FolderBulk20250305080356\WEEKLY SHIPMENT ADIDAS 2025--.xlsx'
    _file_import = r'C:\Users\Admin\Downloads\Check price\Check price\Result\Old\FolderBulk20250305080356\Copy of WEEKLY SHIPMENT ADIDAS 2025--shipment mar.xlsx'
    _tableWeekly = pd.read_excel(_file_import
                                 , sheet_name=0
                                 )
    print(f"{datetime.now()} - Start Download")
    # _now = datetime.today()
    # _currentMonth = _now.month
    # _currentYear = _now.year
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
        EC.presence_of_element_located((By.CSS_SELECTOR, "input#__FilterField_SalesLine_SalesNum_SalesId_Input_0_input"))
    )
    sales_order_filter.click()
    sales_order_filter.clear()
    sales_order_filter.send_keys(so_string)
    sales_order_filter.send_keys(Keys.ENTER)

    time.sleep(150)

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

    btn_download2 = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "span#DocuFileSaveDialog_3_DownloadButton_label"))
    )
    btn_download2.click()

    destination_dir = r'C:\Users\Admin\Downloads\Check price\Check price\Bulk'
    while True:
        files = os.listdir(download_dir)
        matching_files = [file for file in files if "Order lines" in file]

        if matching_files:
            for file in matching_files:
                source_path = os.path.join(download_dir, file)
                destination_path = os.path.join(destination_dir, file)

                shutil.move(source_path, destination_path)
                print(f"Moved file: {file} to {destination_dir}")
                print(f"{datetime.now()} - Finish Download")
                driver.quit()
            return
        time.sleep(10)

result = run_and_check_download()
print(result)





