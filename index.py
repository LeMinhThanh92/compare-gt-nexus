import asyncio
import os

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from starlette.staticfiles import StaticFiles

from Import import process_sample_files, process_bulk_files
from file_utils import (
    get_result_files_by_date,
    get_result_files,
    save_uploaded_files,
    validate_uploaded_files,
    check_required_files_exist
)
from html_template import generate_html_template

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Define the folder paths
FOLDER_PATH_SAMPLE = r'C:\Compare\Sample'
FOLDER_PATH_BULK = r'C:\Compare\Bulk'
FOLDER_PATH_RESULT_SAMPLE = r'C:\Compare\Result\Sample'
FOLDER_PATH_RESULT_BULK = r'C:\Compare\Result\Bulk'

# Create directories if they don't exist
for path in [FOLDER_PATH_SAMPLE, FOLDER_PATH_BULK, FOLDER_PATH_RESULT_SAMPLE, FOLDER_PATH_RESULT_BULK]:
    os.makedirs(path, exist_ok=True)

# Define the required file name patterns
FILE_PATTERNS = {
    "sample": {
        "lo_path": ["pricelist"],
        "import_path": ["Import sales order"]
    },
    "bulk": {
        "excel_path_bulk": ["Import sales order"],
        "excel_path_lineSheet_SS": ["SS", "Final all"],
        "excel_path_lineSheet_FW": ["FW", "Final all"],
        "excel_path_weekly": ["WEEKLY"]
    }
}


@app.get("/", response_class=HTMLResponse)
async def home():
    """Returns an HTML page with a split screen file upload form."""
    # Get current result files, ordered by modification date
    sample_result_files = get_result_files_by_date(FOLDER_PATH_RESULT_SAMPLE, 5)
    bulk_result_files = get_result_files_by_date(FOLDER_PATH_RESULT_BULK, 10)

    return generate_html_template(sample_result_files, bulk_result_files)


@app.get("/get-result-files/")
async def get_result_files_api():
    """Get all result files from both Sample and Bulk result folders."""
    try:
        sample_files = get_result_files_by_date(FOLDER_PATH_RESULT_SAMPLE, 5)
        bulk_files = get_result_files_by_date(FOLDER_PATH_RESULT_BULK, 10)
        return {
            "sample_files": sample_files,
            # "sample_files": [file[0] for file in sample_files],
            # "bulk_files": [file[0] for file in bulk_files]
            "bulk_files": bulk_files
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error getting result files: {str(e)}"}
        )


@app.get("/download-result/{file_type}/{filename}")
async def download_result(file_type: str, filename: str):
    """Download a result file."""
    try:
        if file_type.lower() == "sample":
            file_path = os.path.join(FOLDER_PATH_RESULT_SAMPLE, filename)
        elif file_type.lower() == "bulk":
            file_path = os.path.join(FOLDER_PATH_RESULT_BULK, filename)
        else:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid file type. Use 'sample' or 'bulk'."}
            )

        if not os.path.exists(file_path):
            return JSONResponse(
                status_code=404,
                content={"detail": f"File {filename} not found."}
            )

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error downloading file: {str(e)}"}
        )


@app.post("/upload-sample-files/")
async def upload_sample_files(
        sample_file1: UploadFile = File(...),
        sample_file2: UploadFile = File(...)
):
    """Handles sample file uploads and saves them in the Sample folder."""
    try:
        # Validate file names
        validation_result = validate_uploaded_files(
            [
                (sample_file1, FILE_PATTERNS["sample"]["import_path"], "Sample File 1"),
                (sample_file2, FILE_PATTERNS["sample"]["lo_path"], "Sample File 2")
            ]
        )

        if validation_result:
            return JSONResponse(status_code=400, content={"detail": validation_result})

        files = {
            "sample_file1": sample_file1,
            "sample_file2": sample_file2
        }

        save_uploaded_files(files, FOLDER_PATH_SAMPLE)
        return {"message": "Sample files uploaded successfully!"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error uploading sample files: {str(e)}"}
        )


@app.post("/upload-bulk-files/")
async def upload_bulk_files(
        bulk_file1: UploadFile = File(...),
        bulk_file2: UploadFile = File(...),
        bulk_file3: UploadFile = File(...),
        bulk_file4: UploadFile = File(...)
):
    """Handles bulk file uploads and saves them in the Bulk folder."""
    try:
        # Validate file names
        validation_result = validate_uploaded_files(
            [
                (bulk_file1, FILE_PATTERNS["bulk"]["excel_path_bulk"], "Bulk File 1"),
                (bulk_file2, FILE_PATTERNS["bulk"]["excel_path_lineSheet_SS"], "Bulk File 2"),
                (bulk_file3, FILE_PATTERNS["bulk"]["excel_path_lineSheet_FW"], "Bulk File 3"),
                (bulk_file4, FILE_PATTERNS["bulk"]["excel_path_weekly"], "Bulk File 4")
            ]
        )

        if validation_result:
            return JSONResponse(status_code=400, content={"detail": validation_result})

        files = {
            "bulk_file1": bulk_file1,
            "bulk_file2": bulk_file2,
            "bulk_file3": bulk_file3,
            "bulk_file4": bulk_file4
        }

        save_uploaded_files(files, FOLDER_PATH_BULK)
        return {"message": "Bulk files uploaded successfully!"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error uploading bulk files: {str(e)}"}
        )


@app.post("/process-sample-files/")
async def process_sample_files_api():
    """Process the sample files that have been uploaded."""
    try:
        # Check if required files exist
        missing_files = check_required_files_exist(
            FOLDER_PATH_SAMPLE,
            [
                (FILE_PATTERNS["sample"]["import_path"], "Import file"),
                (FILE_PATTERNS["sample"]["lo_path"], "LO file")
            ]
        )

        if missing_files:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Missing files: {', '.join(missing_files)}. Please upload them first."}
            )

        # Call the imported process_sample_files function
        process_sample_files()

        # Get list of created result files
        result_files = get_result_files(FOLDER_PATH_RESULT_SAMPLE)

        return {
            "message": "Sample files processed successfully!",
            "result_files": result_files
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error processing sample files: {str(e)}"}
        )


bulk_process_semaphore = asyncio.Semaphore(1)


@app.post("/process-bulk-files/")
async def process_bulk_files_api():
    """Process the bulk files that have been uploaded."""
    try:
        # Check if required files exist
        missing_files = check_required_files_exist(
            FOLDER_PATH_BULK,
            [
                (FILE_PATTERNS["bulk"]["excel_path_bulk"], "Import sales order file"),
                (FILE_PATTERNS["bulk"]["excel_path_lineSheet_SS"], "LineSheet SS file"),
                (FILE_PATTERNS["bulk"]["excel_path_lineSheet_FW"], "LineSheet FW file"),
                (FILE_PATTERNS["bulk"]["excel_path_weekly"], "Weekly file")
            ]
        )

        if missing_files:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": f"Missing files: {', '.join(missing_files)}. Please upload all required files first."}
            )

        # Call the imported process_bulk_files function
        process_bulk_files()

        # Get list of created result files
        result_files = get_result_files(FOLDER_PATH_RESULT_BULK)

        return {
            "message": "Bulk files processed successfully!",
            "result_files": result_files
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error processing bulk files: {str(e)}"}
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
