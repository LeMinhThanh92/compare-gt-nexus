import os
import shutil
from datetime import datetime

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo


def validate_filename(filename, patterns):
    """
    Check if the filename contains any of the required patterns
    Returns True if a match is found, False otherwise
    """
    filename = filename.lower()
    for pattern in patterns:
        if pattern.lower() in filename:
            return True
    return False


def get_result_files(folder_path):
    """Get a list of result files in the specified folder"""
    if not os.path.exists(folder_path):
        return []
    return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]


def get_result_files_by_date(folder_path, top_num):
    """Get files from a folder ordered by modification date (newest first) with timestamps."""
    if not os.path.exists(folder_path):
        return []

    files = os.listdir(folder_path)
    files_with_info = []

    for file in files:
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            modified_time = os.path.getmtime(file_path)  # Get modification time
            formatted_time = datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
            files_with_info.append((file, formatted_time))  # Store file name and formatted time

    # Sort by modification time (newest first)
    files_with_info.sort(key=lambda x: datetime.strptime(x[1], '%Y-%m-%d %H:%M:%S'), reverse=True)

    # Return only the top 10 results
    return files_with_info[:top_num]


def save_uploaded_files(files_dict, destination_folder):
    """Save uploaded files to the specified destination folder"""
    for file_key, file_obj in files_dict.items():
        file_path = os.path.join(destination_folder, file_obj.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file_obj.file, buffer)


def validate_uploaded_files(file_validations):
    """
    Validate uploaded files against required patterns
    file_validations: list of tuples (file_object, patterns, file_description)
    Returns error message if validation fails, None otherwise
    """
    for file_obj, patterns, file_desc in file_validations:
        if not validate_filename(file_obj.filename, patterns):
            return f"{file_desc} must contain one of these patterns: {patterns}"
    return None


def check_required_files_exist(folder_path, required_files):
    """
    Check if required files exist in the folder
    required_files: list of tuples (patterns, file_description)
    Returns list of missing file descriptions
    """
    missing_files = []

    for filename in os.listdir(folder_path):
        for patterns, file_desc in required_files[:]:
            if validate_filename(filename, patterns):
                required_files.remove((patterns, file_desc))

    return [file_desc for _, file_desc in required_files]


def export_to_excel_with_table(result_bulk: pd.DataFrame, output_path: str):
    # Step 1: Save the DataFrame to Excel
    result_bulk.to_excel(output_path, index=False)

    # Step 2: Load the workbook and worksheet
    wb = load_workbook(output_path)
    ws = wb.active

    # Step 3: Define table range (e.g., A1:C10)
    max_row = ws.max_row
    max_col = ws.max_column
    end_col_letter = get_column_letter(max_col)
    table_range = f"A1:{end_col_letter}{max_row}"

    # Step 4: Create a table
    table = Table(displayName="DataTable", ref=table_range)
    style = TableStyleInfo(
        name="TableStyleLight13",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False
    )
    table.tableStyleInfo = style
    ws.add_table(table)

    # Step 5: Set white font for header row
    for col in range(1, max_col + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(color="FFFFFF", bold=True)

    # Step 6: Save the workbook
    wb.save(output_path)
