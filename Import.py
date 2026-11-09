import io
import os
import shutil
import smtplib
import time
from datetime import datetime
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd

import downloadFromGTNexus
import downloadFromGTNexusBulk
import loadBulkNew
import loadSampleFile
import queryFromERP
from file_utils import export_to_excel_with_table


def move_files_to_folder(files, source_folder, name_type):
    timestamp_folder = name_type + datetime.now().strftime('%Y%m%d%H%M%S')
    destination_folder = os.path.join(source_folder, f'{timestamp_folder}')
    os.makedirs(destination_folder, exist_ok=True)

    for file in files.values():
        # Check if file is not None before checking if it exists
        if file is not None and os.path.exists(file):
            try:
                shutil.move(file, destination_folder)
                print(f"Moved {file} to {destination_folder}")
            except Exception as e:
                print(f"Error moving {file}: {e}")
        elif file is None:
            print("Skipping None file path")
        else:
            print(f"File does not exist: {file}")

    return destination_folder


# def are_paths_valid(paths):
#     return all(paths.values())


def are_paths_valid(paths, optional_keys=None):
    if optional_keys is None:
        optional_keys = []
    for key, path in paths.items():
        if key in optional_keys:
            # Optional keys can be None or valid path
            continue
        if not path:
            return False
    return True


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
                    # Special handling for SS and FW to exclude _3rd files
                    if key in ["excel_path_lineSheet_SS", "excel_path_lineSheet_FW"]:
                        if "_3rd" not in filename:
                            paths[key] = file_path
                    else:
                        paths[key] = file_path

        return paths

    except Exception as e:
        print(f"Error in get_file_paths: {e}")
        return {"error": f"Error: {e}"}


def process_sample_files(mode = 'A1A'):
    _check = False
    output_path = None
    output_dataframe = None
    output_filename = None

    while not _check:
        folder_path_sample = r'C:\Compare\Sample'
        sample_conditions = {
            "lo_path": ["pricelist"],
            "tc_path": ["adidas", "Released"],
            "import_path": ["Import sales order"]
        }
        sample_paths = get_file_paths(folder_path_sample, sample_conditions)

        if are_paths_valid(sample_paths):
            try:
                # Process the sample files
                result_sample = loadSampleFile.load_sample_file(
                    sample_paths['import_path'],
                    sample_paths['lo_path'],
                    sample_paths['tc_path']
                )

                # Generate timestamp for filename
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

                # Ensure the output directory exists
                os.makedirs(r'C:\Compare\Result\Sample', exist_ok=True)

                # Define output path and save file (keeping this for backup)
                output_path = r'C:\Compare\Result\Sample\Updated_Sample_{}.xlsx'.format(timestamp)
                output_filename = f"Updated_Sample_{timestamp}.xlsx"
                # result_sample.to_excel(output_path, index=False)
                print(result_sample)
                export_to_excel_with_table(result_sample, output_path)

                # Wait for file to be written completely
                time.sleep(2)

                print(f"{datetime.now()} - Success Sample. File saved to: {output_path}")

                # Store DataFrame for email attachment
                output_dataframe = result_sample

                # Move input files to archive folder
                folder_path_result = r'C:\Compare\Result\Old'
                destination_folder = move_files_to_folder(sample_paths, folder_path_result, 'Sample')
                print(f"Processed files moved to: {destination_folder}")

                recipient_emails = ['mio@allianceone.com.vn',
                                    'mera.orders@allianceoneapparel.com',
                                    'allice@allianceone.com.vn',
                                    'mera.orders3@allianceone.com.vn',
                                    'mera.thanhqui@allianceone.com.vn',
                                    'mera.orders4@allianceone.com.vn',
                                    'mera.orders5@allianceone.com.vn']

                # Send email with DataFrame attachment
                # send_email_with_dataframes(
                #     recipient_email=recipient_emails,
                #     subject='Process Sample File Complete',
                #     body=send_completion_email(sample_paths, [output_path], 'Sample'),
                #     dataframes=[(output_dataframe, output_filename)]
                # )

                _check = True

            except Exception as e:
                print(f"Error in processing sample files: {e}")
                time.sleep(60)  # Wait before retrying

        elif check_file_exists(sample_paths.get('import_path')) and not check_file_exists(sample_paths.get('tc_path')):
            print(f"{datetime.now()} - Start download...")
            result = downloadFromGTNexus.run_and_check_download(
                r"C:\Compare\Result\Download"
                , sample_paths['import_path']
                , r'C:\Compare\Sample'
                ,mode)
            print(f"{datetime.now()} - Complete") if result else print(f"{datetime.now()} - Failed")

        else:
            print(f"{datetime.now()} - One or more sample paths are missing. Please check the file paths.")
            time.sleep(60)  # Wait before checking again

    return output_path


def process_bulk_files():
    optional_keys = ["excel_path_lineSheet_3rd"]
    folder_path_bulk = r'C:\Compare\Bulk'
    folder_path_result = r'C:\Compare\Result\Old'
    output_dir = r'C:\Compare\Result\Bulk'
    bulk_conditions = {
        "excel_path_bulk": ["Import sales order"],
        "excel_path_lineSheet_SS": ["SS", "Final all"],
        "excel_path_lineSheet_FW": ["FW", "Final all"],
        "excel_path_lineSheet_3rd": ["_3rd", "Final all"],  # Optional
        "excel_path_weekly": ["WEEKLY"],
        "excel_path_erp": ["Order lines"],
        "excel_path_tc": ["A1A Released Order"]
    }

    output_dataframes = []
    output_names = []

    while True:
        bulk_paths = get_file_paths(folder_path_bulk, bulk_conditions)

        # Destructure paths once
        excel_path_bulk = bulk_paths.get('excel_path_bulk')
        excel_path_lineSheet_SS = bulk_paths.get('excel_path_lineSheet_SS')
        excel_path_lineSheet_FW = bulk_paths.get('excel_path_lineSheet_FW')
        excel_path_lineSheet_3rd = bulk_paths.get('excel_path_lineSheet_3rd')
        excel_path_weekly = bulk_paths.get('excel_path_weekly')
        excel_path_erp = bulk_paths.get('excel_path_erp')
        excel_path_tc = bulk_paths.get('excel_path_tc')


        if are_paths_valid(bulk_paths, optional_keys=optional_keys):
            try:
                result_bulk, result_bulk_update = loadBulkNew.load_bulk_file(
                    excel_path_bulk,
                    excel_path_lineSheet_SS,
                    excel_path_lineSheet_FW,
                    excel_path_weekly,
                    excel_path_erp,
                    excel_path_tc,
                    excel_path_lineSheet_3rd
                )

                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                os.makedirs(output_dir, exist_ok=True)

                output_path = os.path.join(output_dir, f"Compare_Price_{timestamp}.xlsx")
                output_path_update = os.path.join(output_dir, f"Updated_Bulk_{timestamp}.xlsx")

                # result_bulk.to_excel(output_path, index=False)
                export_to_excel_with_table(result_bulk, output_path)
                # result_bulk_update.to_excel(output_path_update, index=False)
                export_to_excel_with_table(result_bulk_update, output_path_update)

                time.sleep(2)  # Ensure files are written

                print(f"{datetime.now()} - Success Bulk. Files saved to disk.")

                output_dataframes.extend([
                    (result_bulk, f"Compare_Price_{timestamp}.xlsx"),
                    (result_bulk_update, f"Updated_Bulk_{timestamp}.xlsx")
                ])
                output_names = [output_path, output_path_update]

                destination_folder = move_files_to_folder(bulk_paths, folder_path_result, 'Bulk')
                print(f"{datetime.now()} - Processed files moved to: {destination_folder}")

                # recipient_emails = [
                #     'thanh-it@allianceone.com.vn'
                # ]
                recipient_emails = [
                    'mio@allianceone.com.vn',
                    'mera.orders@allianceoneapparel.com',
                    'allice@allianceone.com.vn',
                    'mera.orders3@allianceone.com.vn',
                    'mera.thanhqui@allianceone.com.vn',
                    'mera.orders4@allianceone.com.vn',
                    'mera.orders5@allianceone.com.vn'
                ]

                # Uncomment to send email
                # send_email_with_dataframes(
                #     recipient_email=recipient_emails,
                #     subject='Process Bulk File Complete',
                #     body=send_completion_email(bulk_paths, output_names, 'Bulk'),
                #     dataframes=output_dataframes
                # )

                break  # Exit loop after success

            except Exception as e:
                print(f"{datetime.now()} - Error in processing bulk files: {e}")
                time.sleep(60)

        elif check_file_exists(excel_path_weekly) and not check_file_exists(excel_path_erp):
            # print(f"{datetime.now()} - Start download...")
            # result = downloadFromERP.run_and_check_download(
            #     r"C:\Compare\Result\Download",
            #     excel_path_weekly,
            #     folder_path_bulk
            # )
            print(f"{datetime.now()} - Start RunQuery...")
            result = queryFromERP.queryFromERP(
                excel_path_weekly,
                folder_path_bulk
            )
            print(f"{datetime.now()} - Complete" if result else f"{datetime.now()} - Failed")

        elif check_file_exists(excel_path_weekly) and not check_file_exists(excel_path_tc):
            print(f"{datetime.now()} - Start download TC...")
            result = downloadFromGTNexusBulk.run_and_check_download(
                r"C:\Compare\Result\Download",
                excel_path_weekly,
                folder_path_bulk
            )
            print(f"{datetime.now()} - Complete" if result else f"{datetime.now()} - Failed")

        else:
            print(f"{datetime.now()} - One or more bulk paths are missing. Please check the file paths.")
            time.sleep(60)

    return output_names


# def process_bulk_files():
#     _check = False
#     output_dataframes = []
#     output_names = []
#
#     while not _check:
#         folder_path_bulk = r'C:\Compare\Bulk'
#         bulk_conditions = {
#             "excel_path_bulk": ["Import sales order"],
#             "excel_path_lineSheet_SS": ["SS", "Final all"],
#             "excel_path_lineSheet_FW": ["FW", "Final all"],
#             "excel_path_weekly": ["WEEKLY"],
#             "excel_path_erp": ["Order lines"],
#             "excel_path_tc": ["A1A+Released+Order"]
#         }
#         bulk_paths = get_file_paths(folder_path_bulk, bulk_conditions)
#
#         if are_paths_valid(bulk_paths):
#             try:
#                 # Process the files as before
#                 result_bulk, result_bulk_update = loadBulkFile.load_bulk_file(
#                     bulk_paths['excel_path_bulk'],
#                     bulk_paths['excel_path_lineSheet_SS'],
#                     bulk_paths['excel_path_lineSheet_FW'],
#                     bulk_paths['excel_path_weekly'],
#                     bulk_paths['excel_path_erp'],
#                     bulk_paths['excel_path_tc']
#                 )
#
#                 # Generate timestamp for filenames
#                 timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
#
#                 # Ensure the output directory exists
#                 os.makedirs(r'C:\Compare\Result\Bulk', exist_ok=True)
#
#                 # Define output paths and save files
#                 output_path = r'C:\Compare\Result\Bulk\Compare_Price_{}.xlsx'.format(timestamp)
#                 output_path_update = r'C:\Compare\Result\Bulk\Updated_Bulk_{}.xlsx'.format(timestamp)
#
#                 # Save to disk (keeping this for backup)
#                 result_bulk.to_excel(output_path, index=False)
#                 result_bulk_update.to_excel(output_path_update, index=False)
#
#                 # Wait for files to be written completely
#                 time.sleep(2)
#
#                 print(f"{datetime.now()} - Success Bulk. Files saved to disk.")
#
#                 # Store DataFrames and filenames for email attachment
#                 output_dataframes.append((result_bulk, f"Compare_Price_{timestamp}.xlsx"))
#                 output_dataframes.append((result_bulk_update, f"Updated_Bulk_{timestamp}.xlsx"))
#                 output_names = [output_path, output_path_update]
#
#                 # Move input files to archive folder
#                 folder_path_result = r'C:\Compare\Result\Old'
#                 destination_folder = move_files_to_folder(bulk_paths, folder_path_result, 'Bulk')
#                 print(f"Processed files moved to: {destination_folder}")
#
#                 # recipient_emails = ['thanh-it@allianceone.com.vn'
#                 #                     ]
#                 recipient_emails = ['mio@allianceone.com.vn',
#                                     'mera.orders@allianceoneapparel.com',
#                                     'allice@allianceone.com.vn',
#                                     'mera.orders3@allianceone.com.vn',
#                                     'mera.thanhqui@allianceone.com.vn',
#                                     'mera.orders4@allianceone.com.vn',
#                                     'mera.orders5@allianceone.com.vn']
#
#                 # Send email with DataFrame attachments
#                 # send_email_with_dataframes(
#                 #     recipient_email=recipient_emails,
#                 #     subject='Process Bulk File Complete',
#                 #     body=send_completion_email(bulk_paths, output_names, 'Bulk'),
#                 #     dataframes=output_dataframes
#                 # )
#
#                 _check = True
#
#             except Exception as e:
#                 print(f"Error in processing bulk files: {e}")
#                 time.sleep(60)  # Wait before retrying
#
#         elif check_file_exists(bulk_paths.get('excel_path_weekly')) and not check_file_exists(
#                 bulk_paths.get('excel_path_erp')):
#             print(f"{datetime.now()} - Start download...")
#             result = downloadFromERP.run_and_check_download(
#                 r"C:\Compare\Result\Download"
#                 , bulk_paths['excel_path_weekly']
#                 , r'C:\Compare\Bulk')
#             print(f"{datetime.now()} - Complete") if result else print(f"{datetime.now()} - Failed")
#
#         elif check_file_exists(bulk_paths.get('excel_path_weekly')) and not check_file_exists(
#                 bulk_paths.get('excel_path_tc')):
#             print(f"{datetime.now()} - Start download TC...")
#             result = downloadFromGTNexusBulk.run_and_check_download(
#                 r"C:\Compare\Result\Download"
#                 , bulk_paths['excel_path_weekly']
#                 , r'C:\Compare\Bulk')
#             print(f"{datetime.now()} - Complete") if result else print(f"{datetime.now()} - Failed")
#
#         else:
#             print(f"{datetime.now()} - One or more bulk paths are missing. Please check the file paths.")
#             time.sleep(60)  # Wait before checking again
#
#     return output_names


def main():
    try:
        print(f"{datetime.now()} - Starting processing...")

        # Process sample files first
        sample_output = process_sample_files()
        print(f"{datetime.now()} - Sample processing complete.")

        # Then process bulk files
        bulk_outputs = process_bulk_files()
        print(f"{datetime.now()} - Bulk processing complete.")

        print(f"{datetime.now()} - All processing completed successfully.")

        # If you want to run this continuously, uncomment the following:
        # print(f"{datetime.now()} - Waiting for 10 minutes...\n")
        # time.sleep(600)
        # main()  # Recursive call to continue processing

    except Exception as e:
        print(f"{datetime.now()} - Critical error in main process: {e}")
        # Send alert email about the failure
        send_email_alert(
            recipient_email='thanh-it@allianceone.com.vn',
            subject='ERROR: File Processing Failed',
            body=f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; font-size: 12px;">
    <p style="margin-top: 10px; margin-bottom: 10px;">Dear Support Team,</p>

    <p style="margin-top: 10px; margin-bottom: 10px;">There was an error in the file processing system:</p>

    <p style="margin-top: 10px; margin-bottom: 10px; color: red; font-weight: bold;">{str(e)}</p>

    <p style="margin-top: 10px; margin-bottom: 10px;">Please check the system logs for more details.</p>

    <p style="margin-top: 15px; border-top: 1px solid #eee; padding-top: 10px;">
    Best regards<br>
    System Alert
    </p>
</body>
</html>
            """
        )


def send_email_with_dataframes(recipient_email='thanh-it@allianceone.com.vn',
                               subject='A',
                               body='A',
                               dataframes=None,
                               sender_email='elslpom1@allianceoneapparel.com',
                               sender_password='hAn71@$2{0[22!',
                               smtp_server='mail.allianceoneapparel.com',
                               smtp_port=465):
    """
    Send an email alert with pandas DataFrames attached as Excel files.

    Args:
        recipient_email (str or list): Email address of the recipient(s)
        subject (str): Email subject
        body (str): Email body text
        dataframes (list): List of tuples (DataFrame, filename)
        sender_email (str): Sender's email address
        sender_password (str): Sender's email password
        smtp_server (str): SMTP server address
        smtp_port (int): SMTP server port
    """
    try:
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = sender_email

        # Handle recipient_email as either a string or a list
        if isinstance(recipient_email, list):
            msg['To'] = ', '.join(recipient_email)
            recipients = recipient_email
        else:
            msg['To'] = recipient_email
            # Split by comma and strip whitespace to handle comma-separated emails
            recipients = [email.strip() for email in recipient_email.split(',')]

        msg['Subject'] = subject

        # Add HTML content as a MIMEText part
        msg.attach(MIMEText(body, 'html'))

        # Attach DataFrames if provided
        attachment_count = 0
        attachment_errors = []

        if dataframes:
            for df, filename in dataframes:
                try:
                    # Create a BytesIO object to hold the Excel file
                    excel_buffer = io.BytesIO()

                    # Write the DataFrame to the BytesIO object
                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False)

                    # Get the bytes from the BytesIO object
                    excel_buffer.seek(0)
                    excel_data = excel_buffer.read()

                    # Create a MIME base part
                    part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    part.set_payload(excel_data)

                    # Encode in base64
                    encode_base64(part)

                    # Add header
                    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                    part.add_header('Content-ID', f'<{filename}>')

                    # Attach to message
                    msg.attach(part)
                    attachment_count += 1
                    print(f"Attached DataFrame as: {filename}")

                except Exception as e:
                    error_msg = f"Error attaching DataFrame {filename}: {e}"
                    print(error_msg)
                    attachment_errors.append(error_msg)

        # Log attachment status
        print(f"Total attachments: {attachment_count}")
        if attachment_errors:
            print("Attachment errors:")
            for error in attachment_errors:
                print(f"  - {error}")

        # Establish SMTP connection with detailed error handling
        try:
            print(f"Connecting to SMTP server {smtp_server}:{smtp_port}...")
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            server.set_debuglevel(1)  # Enable verbose debug output

            print("Sending EHLO...")
            server.ehlo()  # Say hello to the server

            print("Starting TLS...")
            # server.starttls()  # Enable TLS encryption

            print("Sending EHLO after TLS...")
            server.ehlo()  # Say hello again after TLS

            print("Logging in...")
            server.login(sender_email, sender_password)

            # Send the email
            print(f"Sending email to: {recipients}")
            text = msg.as_string()
            server.sendmail(sender_email, recipients, text)
            print("Email sent successfully!")

            # Close the connection
            server.quit()

            # Return success
            return True
        except smtplib.SMTPAuthenticationError:
            print("SMTP Authentication Error: Invalid username or password")
            return False
        except smtplib.SMTPException as e:
            print(f"SMTP Error: {e}")
            return False
        except Exception as e:
            print(f"Email sending error: {e}")
            return False

    except Exception as e:
        print(f"Failed to prepare email: {e}")
        return False


def send_completion_email(input_paths, output_paths=None, process_type="", include_notice=False):
    # Get current date and time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Create file details section for input files
    file_details = "<ul style='margin-top: 5px; margin-bottom: 5px;'>"
    for key, path in input_paths.items():
        if path and not key.startswith("error"):
            filename = os.path.basename(path)
            file_details += f"<li>Input Filename: <strong>{filename}</strong></li>"

    # Add output file details
    if output_paths:
        file_details += "<li>Output Files:</li>"
        file_details += "<ul>"
        for path in output_paths:
            filename = os.path.basename(path)
            # Check if the file really exists
            if os.path.exists(path):
                file_size_mb = os.path.getsize(path) / (1024 * 1024)
                if file_size_mb < 20:
                    file_details += f"<li><strong>{filename}</strong> ({file_size_mb:.2f} MB) (attached)</li>"
                else:
                    file_details += f"<li><strong>{filename}</strong> ({file_size_mb:.2f} MB) (too large to attach)</li>"
            else:
                file_details += f"<li><strong>{filename}</strong> (file not found)</li>"
        file_details += "</ul>"

    # Add status information
    file_details += f"<li>Upload Date: {current_time}</li>"
    file_details += f"<li>Processing Completed: {current_time}</li>"
    file_details += f"<li>Status: <span style='color: green;'>Completed</span></li></ul>"

    # Additional notice if files are too large
    large_file_notice = ""
    if include_notice:
        large_file_notice = """
        <p style="margin-top: 10px; margin-bottom: 10px; color: #e74c3c;">
        <strong>Note:</strong> Some output files were too large to attach to this email. 
        You can find these files in the system at C:\Compare\Result\Bulk\ or contact IT support for assistance.
        </p>
        """

    # Create email HTML content
    content = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; font-size: 12px;">
    <p style="margin-top: 10px; margin-bottom: 10px;">Dear User,</p>

    <p style="margin-top: 10px; margin-bottom: 10px;">We're pleased to inform you that your {process_type} files uploaded to the Price Check File Upload System have been successfully processed.</p>

    <h3 style="color: #2c5282; font-size: 14px; margin-top: 15px; margin-bottom: 5px;">File Details:</h3>
    {file_details}

    {large_file_notice}

    <p style="margin-top: 10px; margin-bottom: 10px;">The processed result files are attached to this email for your convenience. They will also be available in the system for the next 30 days.</p>

    <p style="margin-top: 10px; margin-bottom: 10px;">If you have any questions or need assistance with the processed data, please contact our support team.</p>

    <p style="margin-top: 10px; margin-bottom: 10px;">Thank you for using our Price Check File Upload System.</p>

    <p style="margin-top: 15px; border-top: 1px solid #eee; padding-top: 10px;">
    Best regards<br>
    </p>
</body>
</html>
    """

    return content


def send_email_alert(recipient_email='thanh-it@allianceone.com.vn',
                     subject='A',
                     body='A',
                     attachments=None,
                     sender_email='elslpom1@allianceoneapparel.com',
                     sender_password='hAn71@$2{0[22!',
                     smtp_server='103.1.208.204',
                     smtp_port=25):
    """
    Send an email alert about process completion with file attachments.

    Args:
        recipient_email (str): Email address of the recipient
        subject (str): Email subject
        body (str): Email body text
        attachments (list): List of file paths to attach
        sender_email (str): Sender's email address
        sender_password (str): Sender's email password
        smtp_server (str): SMTP server address
        smtp_port (int): SMTP server port
    """
    try:
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        # Add HTML content as a MIMEText part
        msg.attach(MIMEText(body, 'html'))

        # Attach files if provided
        attachment_count = 0
        attachment_errors = []

        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    try:
                        # Check file size - limit to 20MB
                        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        if file_size_mb > 20:
                            print(f"Skipping attachment {file_path} - file too large ({file_size_mb:.2f} MB)")
                            attachment_errors.append(
                                f"File too large: {os.path.basename(file_path)} ({file_size_mb:.2f} MB)")
                            continue

                        # Open the file in binary mode
                        with open(file_path, 'rb') as attachment:
                            # Create a MIME base part
                            part = MIMEBase('application', 'octet-stream')
                            # Read file content
                            part.set_payload(attachment.read())

                        # Encode in base64
                        encode_base64(part)

                        # Add header
                        filename = os.path.basename(file_path)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{filename}"'
                        )
                        part.add_header('Content-ID', f'<{filename}>')

                        # Attach to message
                        msg.attach(part)
                        attachment_count += 1
                        print(f"Attached file: {file_path}")
                    except Exception as e:
                        error_msg = f"Error attaching file {file_path}: {e}"
                        print(error_msg)
                        attachment_errors.append(error_msg)
                else:
                    error_msg = f"Warning: Attachment file not found: {file_path}"
                    print(error_msg)
                    attachment_errors.append(error_msg)

        # Log attachment status
        print(f"Total attachments: {attachment_count}")
        if attachment_errors:
            print("Attachment errors:")
            for error in attachment_errors:
                print(f"  - {error}")

        # Establish SMTP connection with detailed error handling
        try:
            print(f"Connecting to SMTP server {smtp_server}:{smtp_port}...")
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.set_debuglevel(1)  # Enable verbose debug output

            print("Sending EHLO...")
            server.ehlo()  # Say hello to the server

            print("Starting TLS...")
            server.starttls()  # Enable TLS encryption

            print("Sending EHLO after TLS...")
            server.ehlo()  # Say hello again after TLS

            print("Logging in...")
            server.login(sender_email, sender_password)

            # Send the email
            print("Sending email...")
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            print("Email sent successfully!")

            # Close the connection
            server.quit()

            # Return success
            return True
        except smtplib.SMTPAuthenticationError:
            print("SMTP Authentication Error: Invalid username or password")
            return False
        except smtplib.SMTPException as e:
            print(f"SMTP Error: {e}")
            return False
        except Exception as e:
            print(f"Email sending error: {e}")
            return False

    except Exception as e:
        print(f"Failed to prepare email: {e}")
        return False


if __name__ == "__main__":
    main()
