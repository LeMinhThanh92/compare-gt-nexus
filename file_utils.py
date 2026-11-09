import os
import re
import shutil
from datetime import datetime

import pandas as pd
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo


DEFAULT_COLUMN_ALIASES = {
    # Weekly file variations
    "style no": "Style No/",
    "style no.": "Style No/",
    "style number": "Style No/",
    "article no": "Article Number",
    "article no.": "Article Number",
    "schedule ex factory": "Schedule ex.Factory",
    "schedule ex-factory": "Schedule ex.Factory",
    # Season LineSheet variations
    "costsheet status (c)": "Status (C)",
}


def normalize_col_key(col_name: object) -> str:
    """
    Normalize an Excel column name for case-insensitive and whitespace-tolerant matching:
    - Convert to string, replace newlines/tabs with space, strip leading/trailing whitespace
    - Collapse multiple internal spaces into a single space
    - Normalize spaces around '.', '/', '(', ')'
    - Convert to lowercase
    """
    if col_name is None or pd.isna(col_name):
        return ""
    s = str(col_name).replace("\r", " ").replace("\n", " ").replace("\t", " ").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*\.\s*", ".", s)
    s = re.sub(r"\s*/\s*", "/", s)
    s = re.sub(r"\s*\(\s*", " (", s)
    s = re.sub(r"\s*\)\s*", ")", s)
    return s.strip().lower()


def resolve_sheet_name(xls: pd.ExcelFile, requested_sheet=0):
    """
    Resolve sheet name forgivingly (case-insensitive, ignoring extra spaces).
    If 'Sheet1' is requested but renamed in the workbook, falls back to the first sheet (index 0).
    """
    sheet_names = xls.sheet_names
    if isinstance(requested_sheet, int):
        return sheet_names[requested_sheet] if 0 <= requested_sheet < len(sheet_names) else sheet_names[0]

    if requested_sheet in sheet_names:
        return requested_sheet

    norm_req = normalize_col_key(requested_sheet).replace(" ", "")
    for s in sheet_names:
        if normalize_col_key(s).replace(" ", "") == norm_req:
            return s

    print(f"Worksheet '{requested_sheet}' not found, falling back to first sheet '{sheet_names[0]}'")
    return sheet_names[0]


def _build_column_mapping(raw_headers, target_cols, aliases=None):
    """
    Match target canonical column names against raw Excel header names.
    Priority:
      1. Exact string match
      2. Normalized key match (case-insensitive, whitespace/punctuation normalized)
      3. Alias fallback match (only if primary name is not present)
    Returns (target_to_raw, raw_to_target)
    """
    if aliases is None:
        aliases = DEFAULT_COLUMN_ALIASES

    raw_strs = [str(h) for h in raw_headers if h is not None and not pd.isna(h)]
    exact_map = {h: h for h in raw_strs}
    norm_map = {}
    for h in raw_strs:
        nk = normalize_col_key(h)
        if nk and nk not in norm_map:
            norm_map[nk] = h

    target_to_raw = {}
    raw_to_target = {}

    for target in target_cols:
        norm_target = normalize_col_key(target)
        matched_raw = None

        # 1. Exact match
        if target in exact_map:
            matched_raw = exact_map[target]
        # 2. Normalized match
        elif norm_target in norm_map:
            matched_raw = norm_map[norm_target]
        # 3. Alias fallback
        else:
            for alias_norm, canonical in aliases.items():
                if canonical == target and alias_norm in norm_map:
                    matched_raw = norm_map[alias_norm]
                    break

        if matched_raw is not None:
            target_to_raw[target] = matched_raw
            raw_to_target[matched_raw] = target

    return target_to_raw, raw_to_target


def smart_read_excel(
    file_path,
    sheet_name=0,
    dtype=None,
    usecols=None,
    canonical_cols=None,
    detect_header=False,
    xls: pd.ExcelFile = None,
) -> pd.DataFrame:
    """
    Read an Excel sheet while automatically resolving:
    - Sheet name casing/whitespace differences
    - Optional N/A first row header detection (row 0 vs row 1)
    - Column name casing, leading/trailing/multiple spaces, newlines, and aliases
    - dtype mapping even when raw column names have extra spaces or different casing
    """
    own_xls = False
    if xls is None:
        xls = pd.ExcelFile(file_path, engine="openpyxl")
        own_xls = True

    try:
        resolved_sheet = resolve_sheet_name(xls, sheet_name)

        # Read only the first 1 or 2 header rows via pandas (which resets bogus openpyxl dimensions)
        preview_nrows = 2 if detect_header else 1
        temp_df = pd.read_excel(xls, sheet_name=resolved_sheet, nrows=preview_nrows, header=None)

        header_row = 0
        if detect_header and not temp_df.empty:
            first_cell = temp_df.iloc[0, 0]
            if (
                pd.isna(first_cell)
                or str(first_cell).strip().upper() in ["N/A", "NA", "NULL", "#N/A"]
                or str(first_cell).strip() == ""
            ):
                print("First row appears to be N/A, using second row as header")
                header_row = 1
            else:
                print("Using first row as header")
                header_row = 0

        raw_headers = list(temp_df.iloc[header_row].values) if len(temp_df) > header_row else []

        target_cols = list(usecols) if usecols is not None else (list(canonical_cols) if canonical_cols is not None else [])
        target_to_raw, raw_to_target = _build_column_mapping(raw_headers, target_cols)

        if usecols is not None:
            missing = [col for col in usecols if col not in target_to_raw]
            if missing:
                available = [str(h) for h in raw_headers if h is not None and not pd.isna(h)]
                raise ValueError(
                    f"Missing required column(s) {missing} in '{os.path.basename(str(file_path))}'. "
                    f"Available columns: {available}"
                )

        # Build resolved dtype dict matching actual raw column names in the sheet
        resolved_dtype = None
        if dtype is not None:
            resolved_dtype = dict(dtype)
            norm_dtype = {normalize_col_key(k): v for k, v in dtype.items()}
            for h in raw_headers:
                if h is None or pd.isna(h):
                    continue
                h_str = str(h)
                if h_str in dtype:
                    resolved_dtype[h_str] = dtype[h_str]
                elif h_str in raw_to_target and raw_to_target[h_str] in dtype:
                    resolved_dtype[h_str] = dtype[raw_to_target[h_str]]
                else:
                    nh = normalize_col_key(h_str)
                    if nh in norm_dtype:
                        resolved_dtype[h_str] = norm_dtype[nh]

        # Build usecols filter function if usecols was requested
        usecols_arg = None
        if usecols is not None:
            matched_raw_set = set(target_to_raw.values())
            norm_usecols_set = {normalize_col_key(u) for u in usecols}
            usecols_arg = lambda col: str(col) in matched_raw_set or normalize_col_key(col) in norm_usecols_set

        df = pd.read_excel(
            xls,
            sheet_name=resolved_sheet,
            header=header_row,
            dtype=resolved_dtype,
            usecols=usecols_arg,
        )

        # Ensure df.columns are mapped to canonical target_cols
        if target_cols:
            _, df_raw_to_target = _build_column_mapping(list(df.columns), target_cols)
            rename_dict = {
                raw_col: canon_col
                for raw_col, canon_col in df_raw_to_target.items()
                if raw_col != canon_col and canon_col not in df.columns
            }
            if rename_dict:
                df.rename(columns=rename_dict, inplace=True)

        if usecols is not None:
            df = df[list(usecols)].copy()

        return df
    finally:
        if own_xls:
            xls.close()


def read_excel_with_header_detection(file_path, sheet_name=0, dtype=None, usecols=None, canonical_cols=None):
    """
    Read Excel file and detect if first row is N/A, then use second row as header,
    with automatic column name normalization.
    """
    return smart_read_excel(
        file_path=file_path,
        sheet_name=sheet_name,
        dtype=dtype,
        usecols=usecols,
        canonical_cols=canonical_cols,
        detect_header=True,
    )


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
