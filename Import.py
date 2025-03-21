import os
import shutil
from datetime import datetime

import downloadFromERP
import downloadFromGTNexus
import loadBulkFile
import loadSampleFile


def move_files_to_folder(files, source_folder, name_type):
    timestamp_folder = name_type + datetime.now().strftime('%Y%m%d%H%M%S')
    destination_folder = os.path.join(source_folder, f'{timestamp_folder}')
    os.makedirs(destination_folder, exist_ok=True)

    for file in files.values():
        if os.path.exists(file):
            try:
                shutil.move(file, destination_folder)
                print(f"Moved {file} to {destination_folder}")
            except Exception as e:
                print(f"Error moving {file}: {e}")

    return destination_folder


def are_paths_valid(paths):
    return all(paths.values())


def check_file_exists(file_path):
    if file_path and os.path.exists(file_path):
        return True
    else:
        return False


def get_file_paths(_folder_path, file_conditions):
    paths = {key: None for key in file_conditions}

    try:
        filenames = [f for f in os.listdir(_folder_path) if os.path.isfile(os.path.join(_folder_path, f))]

        for filename in filenames:
            file_path = os.path.join(_folder_path, filename)

            for key, condition in file_conditions.items():
                if all(substring in filename for substring in condition):
                    paths[key] = file_path

        return paths

    except Exception as e:
        return {"error": f"Error: {e}"}


def process_sample_files():
    _check = False
    while not _check:
        folder_path_sample = r'C:\Users\Admin\Downloads\Check price\Check price\Sample'
        sample_conditions = {
            "lo_path": ["pricelist"],
            "tc_path": ["adidas", "Released"],
            "import_path": ["Import sales order"]
        }
        sample_paths = get_file_paths(folder_path_sample, sample_conditions)

        if are_paths_valid(sample_paths):
            result_sample = loadSampleFile.load_sample_file(
                sample_paths['import_path'],
                sample_paths['lo_path'],
                sample_paths['tc_path']
            )
            print(f"{datetime.now()} - Success Sample: {result_sample}")
            folder_path_result = r'C:\Users\Admin\Downloads\Check price\Check price\Result\Old'
            destination_folder = move_files_to_folder(sample_paths, folder_path_result, 'Sample')
            print(f"Processed files moved to: {destination_folder}")
            _check = True
        elif check_file_exists(sample_paths['import_path']) and not check_file_exists(
                sample_paths['tc_path']):
            print(f"{datetime.now()} - Start download...")
            result = downloadFromGTNexus.run_and_check_download(
                r"C:\Users\Admin\Downloads\Check price\Check price\Result\Download"
                , sample_paths['import_path']
                , r'C:\Users\Admin\Downloads\Check price\Check price\Sample')
            print(f"{datetime.now()} - Complete") if result else print(f"{datetime.now()} - Failed")
        else:
            print(f"{datetime.now()} - One or more sample paths are missing. Please check the file paths.")


def process_bulk_files():
    _check = False
    while not _check:
        folder_path_bulk = r'C:\Users\Admin\Downloads\Check price\Check price\Bulk'
        bulk_conditions = {
            "excel_path_bulk": ["Import sales order"],
            "excel_path_lineSheet_SS": ["SS", "Final all"],
            "excel_path_lineSheet_FW": ["FW", "Final all"],
            "excel_path_weekly": ["WEEKLY"],
            "excel_path_erp": ["Order lines"]
        }
        bulk_paths = get_file_paths(folder_path_bulk, bulk_conditions)

        if are_paths_valid(bulk_paths):
            result_bulk = loadBulkFile.load_bulk_file(
                bulk_paths['excel_path_bulk'],
                bulk_paths['excel_path_lineSheet_SS'],
                bulk_paths['excel_path_lineSheet_FW'],
                bulk_paths['excel_path_weekly'],
                bulk_paths['excel_path_erp']
            )
            output_path = r'C:\Users\Admin\Downloads\Check price\Check price\Result\Bulk\Compare_Price_{}.xlsx'.format(
                datetime.now().strftime('%Y%m%d%H%M%S')
            )
            result_bulk.to_excel(output_path, index=False)
            print(f"{datetime.now()} - Success Bulk. File saved to: {output_path}")

            folder_path_result = r'C:\Users\Admin\Downloads\Check price\Check price\Result\Old'
            destination_folder = move_files_to_folder(bulk_paths, folder_path_result, 'Bulk')
            print(f"Processed files moved to: {destination_folder}")
            _check = True
        elif check_file_exists(bulk_paths['excel_path_weekly']) and not check_file_exists(
                bulk_paths['excel_path_erp']):
            print(f"{datetime.now()} - Start download...")
            result = downloadFromERP.run_and_check_download(
                r"C:\Users\Admin\Downloads\Check price\Check price\Result\Download"
                , bulk_paths['excel_path_weekly']
                , r'C:\Users\Admin\Downloads\Check price\Check price\Bulk')
            print(f"{datetime.now()} - Complete") if result else print(f"{datetime.now()} - Failed")
        else:
            print(f"{datetime.now()} - One or more bulk paths are missing. Please check the file paths.")


def main():
    # while True:
    #     print(f"{datetime.now()} - Checking for new files...")

    process_sample_files()
    process_bulk_files()

    # print(f"{datetime.now()} - Waiting for 10 minutes...\n")
    # time.sleep(600)


if __name__ == "__main__":
    main()
