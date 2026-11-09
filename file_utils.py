import os
import shutil
from datetime import datetime

import pandas as pd
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
    with os.scandir(folder_path) as entries:
        return [entry.name for entry in entries if entry.is_file()]


def get_result_files_by_date(folder_path, top_num):
    """Get files from a folder ordered by modification date (newest first) with timestamps."""
    if not os.path.exists(folder_path):
        return []

    files_with_info = []
    with os.scandir(folder_path) as entries:
        for entry in entries:
            if entry.is_file():
                modified_time = entry.stat().st_mtime  # Get modification time
                formatted_time = datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
                files_with_info.append((entry.name, formatted_time))  # Store file name and formatted time

    # Sort by modification time (newest first)
    files_with_info.sort(key=lambda x: x[1], reverse=True)

    # Return only the top 10 results
    return files_with_info[:top_num]


def read_excel_with_header_detection(file_path, sheet_name=0, dtype=None, usecols=None):
    """
    Read Excel file and detect if first row is N/A, then use second row as header
    """
    with pd.ExcelFile(file_path, engine='openpyxl') as xls:
        # First, read just the first two rows to check the header
        temp_df = pd.read_excel(xls, sheet_name=sheet_name, nrows=2, header=None)

        # Check if first cell [0,0] is N/A, NaN, or similar
        first_cell = temp_df.iloc[0, 0]

        # Check for various forms of N/A
        if (pd.isna(first_cell) or
                str(first_cell).upper() in ['N/A', 'NA', 'NULL', '#N/A'] or
                first_cell == ''):

            print("First row appears to be N/A, using second row as header")
            # Use second row (index 1) as header
            df = pd.read_excel(xls, sheet_name=sheet_name, header=1, dtype=dtype, usecols=usecols)
        else:
            print("Using first row as header")
            # Use first row (index 0) as header (default)
            df = pd.read_excel(xls, sheet_name=sheet_name, header=0, dtype=dtype, usecols=usecols)

    return df


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
    # Save the DataFrame and format as an Excel Table in a single pass
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        result_bulk.to_excel(writer, index=False, sheet_name='Sheet1')
        ws = writer.sheets['Sheet1']

        # Define table range (e.g., A1:C10)
        max_row = ws.max_row
        max_col = ws.max_column
        end_col_letter = get_column_letter(max_col)
        table_range = f"A1:{end_col_letter}{max_row}"

        # Create a table
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

        # Set white font for header row
        header_font = Font(color="FFFFFF", bold=True)
        for col in range(1, max_col + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = header_font
