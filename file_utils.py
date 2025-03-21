import os
import shutil
from datetime import datetime


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


def get_result_files_by_date(folder_path):
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
    return files_with_info[:10]


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
