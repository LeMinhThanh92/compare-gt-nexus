import os
import shutil
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import downloadFromERP
import downloadFromGTNexus
import downloadFromGTNexusBulk
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
        folder_path_sample = r'C:\Compare\Sample'
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
            folder_path_result = r'C:\Compare\Result\Old'
            destination_folder = move_files_to_folder(sample_paths, folder_path_result, 'Sample')
            print(f"Processed files moved to: {destination_folder}")
            # send_email_alert()
            _check = True
        elif check_file_exists(sample_paths['import_path']) and not check_file_exists(
                sample_paths['tc_path']):
            print(f"{datetime.now()} - Start download...")
            result = downloadFromGTNexus.run_and_check_download(
                r"C:\Compare\Result\Download"
                , sample_paths['import_path']
                , r'C:\Compare\Sample')
            print(f"{datetime.now()} - Complete") if result else print(f"{datetime.now()} - Failed")
        else:
            print(f"{datetime.now()} - One or more sample paths are missing. Please check the file paths.")


def process_bulk_files():
    _check = False
    while not _check:
        folder_path_bulk = r'C:\Compare\Bulk'
        bulk_conditions = {
            "excel_path_bulk": ["Import sales order"],
            "excel_path_lineSheet_SS": ["SS", "Final all"],
            "excel_path_lineSheet_FW": ["FW", "Final all"],
            "excel_path_weekly": ["WEEKLY"],
            "excel_path_erp": ["Order lines"],
            "excel_path_tc": ["A1A+Released+Order"]
        }
        bulk_paths = get_file_paths(folder_path_bulk, bulk_conditions)

        if are_paths_valid(bulk_paths):
            result_bulk = loadBulkFile.load_bulk_file(
                bulk_paths['excel_path_bulk'],
                bulk_paths['excel_path_lineSheet_SS'],
                bulk_paths['excel_path_lineSheet_FW'],
                bulk_paths['excel_path_weekly'],
                bulk_paths['excel_path_erp'],
                bulk_paths['excel_path_tc']
            )
            output_path = r'C:\Compare\Result\Bulk\Compare_Price_{}.xlsx'.format(
                datetime.now().strftime('%Y%m%d%H%M%S')
            )
            result_bulk.to_excel(output_path, index=False)
            print(f"{datetime.now()} - Success Bulk. File saved to: {output_path}")

            folder_path_result = r'C:\Compare\Result\Old'
            destination_folder = move_files_to_folder(bulk_paths, folder_path_result, 'Bulk')
            print(f"Processed files moved to: {destination_folder}")
            # send_email_alert()
            _check = True
        elif check_file_exists(bulk_paths['excel_path_weekly']) and not check_file_exists(
                bulk_paths['excel_path_erp']):
            print(f"{datetime.now()} - Start download...")
            result = downloadFromERP.run_and_check_download(
                r"C:\Compare\Result\Download"
                , bulk_paths['excel_path_weekly']
                , r'C:\Compare\Bulk')
            print(f"{datetime.now()} - Complete") if result else print(f"{datetime.now()} - Failed")
        elif check_file_exists(bulk_paths['excel_path_weekly']) and not check_file_exists(
                bulk_paths['excel_path_tc']):
            print(f"{datetime.now()} - Start download TC...")
            result = downloadFromGTNexusBulk.run_and_check_download(
                r"C:\Compare\Result\Download"
                , bulk_paths['excel_path_weekly']
                , r'C:\Compare\Bulk')
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


def send_email(sender_email, sender_password, recipient_email, subject, body):
    """
    Send an email via Gmail SMTP server with SSL encryption.

    Args:
        sender_email (str): Your Gmail address
        sender_password (str): Your Gmail app password
        recipient_email (str): Recipient's email address
        subject (str): Email subject line
        body (str): Email body text
    """
    # Gmail SMTP server settings
    smtp_server = "smtp.gmail.com"
    port = 465  # SSL port

    # Create a multipart message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    try:
        # Create secure SSL context
        context = ssl.create_default_context()

        # Establish a secure session with Gmail's SMTP server
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            # Login to the sender's Gmail account
            server.login(sender_email, sender_password)

            # Send email
            server.sendmail(sender_email, recipient_email, message.as_string())

        print("Email sent successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")


def send_email_alert(recipient_email='thanh-it@allianceone.com.vn',
                     subject='A',
                     body='A',
                     sender_email='autoreply.a1a@allianceoneapprel.com',
                     sender_password='Ke@*%nfd159((@@#',
                     smtp_server='103.1.208.204',
                     smtp_port=25):
    """
    Send an email alert about process completion.

    Args:
        recipient_email (str): Email address of the recipient
        subject (str): Email subject
        body (str): Email body text
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

        # Attach body text
        msg.attach(MIMEText(body, 'plain'))

        # Establish SMTP connection
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Enable TLS encryption
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print("Email alert sent successfully!")

    except Exception as e:
        print(f"Failed to send email alert: {e}")


if __name__ == "__main__":
    main()
