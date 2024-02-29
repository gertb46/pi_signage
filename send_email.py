#!/usr/bin/python3
"""
Send an email using an RFC 5322 formatted file.

Synopsis:
    send_email.py  message_file [...]

Description:
    This program sends emails using the contents of the message_file
    given as arguments to this program.
    Each file must be formatted using the RFC 5322 format and contain at
    least the "To" and "Subject" header lines. Optionally it can have
    the header "Attachment" if there is a file to be attached to the
    email. All other header lines are ignored. The "From" address will
    be the device name and the user account name from the dotenv
    configuration.
    Every message is tested for properly formatted "To:" address and
    that there is a "Subject:" line. If these checks fail, the message
    is written to the "other_msg" folder for inspection.
    The validated message is then send to the SMTP server using the
    dotenv credentials.
    When a message has been emailed successfully, it is moved to the
    'unqueue' folder where it is awaiting deletion. Otherwise the
    file is moved to the queue folder. This allows a message that
    was not send to be tried again at the next running of this program.

Arguments:
    message_file -- The RFC 5322 formatted message(s).

Return:
    0 -- No errors detected.
    1 -- Error detected. Errors are written to the logging file.
    3 -- No internet access or SMTP connection failed.

Run info:
    This program must be run from the send_email.sh script.

See also:
    dotenv -- Dotenv file with the secrets and other configurable data.
    send_email.sh -- Script that executes this program.
    unqueue/ -- Folder for storing emailed message.
    queue/ -- Folder that holds messages to be queued for sending.
    signage.conf -- Configuration data providing environment variables.
                    Only if program executed by a shell script.

Version:
    1.0

Copyright (C) 2023 Gert Bakker, Coleshill,  UK

This file is part of the <Digital Signage> project.

Digital Signage is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by the
Free Software Foundation, version 3.

Digital Signage is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""


# -----------------------------------------------------------------------------
# IMPORT THE MODULES
import email
import smtplib
import sys
import os
import re
import shutil
import socket
import dotenv
import logging  # For logging errors etc.
import mimetypes  # For detecting attachment MIME type
from email.message import EmailMessage
from urllib.request import urlopen


# -----------------------------------------------------------------------------
# VARIABLES and CONSTANTS
# Set the filenames for the logging messages and the dotenv file.
LOG_FNAME = os.getenv('PI_SIGN_LOG', default='pi_signage.log')
DOTENV_FILE = os.path.join(os.getcwd(), ".env")

# Get the name of this program for use in the debug messages.
progname = os.path.basename(sys.argv[0])

# Get the the folder names used in this program
UNQUEUE_DIR = os.getenv('UNQUEUE_DIR', default='./unqueue')
QUEUE_DIR = os.getenv("QUEUE_DIR", default='./queue')
OTHR_FOLDER = os.getenv("OTHR_FOLDER", default='./other_msg')

# Define the global variables
smtp_server = ""  # SMTP server name
smtp_port = ""  # SMTP server port number
mail_username = ""  # User name of email account
mail_password = ""  # Password of email account
hostname = ''  # Name of the device this program is running on
smtplink = ''  # SMTP object

# -----------------------------------------------------------------------------
# LANGUAGE SPECIFIC constants
# The following texts can be translated into other languages if needed.
# The DEBUG messages are not considered to need translation as they are only
# there during testing and for diagnostics.

# Logging messages definition. SNDEM is this program identification
# LOG_ERR are the error messages
LOG_ERR = ('SNDEM: No internet access',
           'SNDEM: SMTP connection error',
           'SNDEM: %s: TO is empty',
           'SNDEM: Msg: %s: TO invalid: %s',
           'SNDEM: %s: SUBJECT is empty',
           'SNDEM: Could not open file: %s',
           'SNDEM: Unable to send email: %s Error: %s',
           'SNDEM: Insufficient arguments',
           'SNDEM: Attachment file not found: %s')


# -----------------------------------------------------------------------------
# INITIALISE
def initialise():
    """
    Initialise the program.

    Declare variables used in other parts of the program as Global.
    Set the hostname to the name of the device for use in the From: line
    of the email message.
    From the dotenv file, get the user and server data.
    Set the logging level depending on the value of the dotenv DEBUG
    variable.

    Arguments:
        None

    Return:
        None
    """

    # Define these variables as Global as they are used in other functions.
    global smtp_server, smtp_port, mail_username, mail_password, hostname

    # Get the hostname of this device to use in the From address
    hostname = socket.gethostname()

    #   Get the secrets from the Dotenv file
    secrets = dotenv.dotenv_values(DOTENV_FILE)
    mail_username = secrets["USERNAME"]
    mail_password = secrets["PASSWORD"]
    smtp_server = secrets['SMTP_SERVER']
    smtp_port = secrets['SMTP_PORT']

    # Set the logging level depending on the DEBUG value in th secrets file
    loglevel = getattr(logging, 'INFO', None)  # Default level is INFO
    if secrets["DEBUG"].lower() == "true":
        loglevel = getattr(logging, 'DEBUG', None)  # Set level to DEBUG

    # Setup the logging facility with message format, filename and log level
    logging.basicConfig(filename=LOG_FNAME, encoding='utf-8',
                        format='%(asctime)s %(levelname)s - %(message)s',
                        datefmt='%b %d %H:%M:%S',
                        level=loglevel)
# End initialise


# -----------------------------------------------------------------------------
# OPEN_SMTP_SERVER
def open_smtp_server():
    """
    Open and connect to the SMTP server.

    First check that we have internet access. Then open a link to the
    SMTP server and log-on to the email account.

    Arguments:
        None

    Return:
        True - Internet access is OK and logged onto the SMTP server
        False - There is no internet access or SMTP logon failed
    """

    # Define the smtplink variable as Global
    global smtplink

    # Check that there is internet access.
    try:
        urlopen('https://docs.google.com/', timeout=3)
    except Exception:
        logging.error(LOG_ERR[0])
        return False

    # Open the email server and logon to the mail account
    try:
        smtplink = smtplib.SMTP(smtp_server, port=smtp_port)
        smtplink.starttls()
        smtplink.login(mail_username, mail_password)
        logging.debug("Logged onto the email service")
    except Exception:
        logging.error(LOG_ERR[1])
        return False

    return True
# End open_smtp_server


# -----------------------------------------------------------------------------
# EMAIL_CHECKS
def email_checks(p_to_adrs, p_subject, p_msgname):
    """
    Email TO and SUBJECT sanity checks.

    Check that the TO string is not empty or None. Then extract the
    email address from the TO string (if needed) and then check that the
    email address has the correct format.
    Check that the SUBJECT string is not None or empty.
    Any errors, return with a False value.

    Arguments:
        p_to_adrs -- The TO email address to be checked
        p_subject -- The email subject text to be checked
        p_msgname -- Name of the message file to include in error messages

    Return:
        True -- The TO and SUBJECT are OK
        False -- The TO and/or SUBJECT data are invalid
    """

    # Check the TO email address is not empty
    if (p_to_adrs is None or len(p_to_adrs) < 2):
        logging.error(LOG_ERR[2], p_msgname)
        return False

    # Extract the email address part from the TO line if possible
    try:
        regex = "<(.+?)>"
        mail_adrs = re.search(regex, p_to_adrs).group(1)
    except AttributeError:
        mail_adrs = p_to_adrs

    # Check that TO is a proper email address
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+'
                       r'@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    if not re.fullmatch(regex, mail_adrs):
        logging.error(LOG_ERR[3], p_msgname, mail_adrs)
        return False

    # Check the SUBJECT data
    if (p_subject is None or len(p_subject) < 1):
        logging.error(LOG_ERR[4], p_msgname)
        return False

    return True
# End email_checks


# -----------------------------------------------------------------------------
# SEND_THE_MESSAGE
def send_the_message(p_filename, p_from_adrs):
    """
    Send the message contained in the file passed in p-filename.

    Send the message that is in the RFC 5322 formatted file.
    Extract from the header the "To" and "Subject" information.
    If the "Attachment" header is present, then the file named
    on this line is to be attached to the email message.
    Other header lines in the message are ignored.

    Arguments:
        p_filename -- Name of the file with the message to email.
        p_from_adrs -- The sender address for the email to use.

    Return:
        True -- Send message OK
        False -- Error detected.
    """

    # Open the RFC5322 message, get the envelope data and message text.
    try:
        fd = open(p_filename, 'r', encoding="utf-8")
    except Exception:
        # If the message file is not found, error message and return False.
        logging.error(LOG_ERR[5], p_filename)
        return False

    # Parse the info from an RFC 5322 formatted file.
    mail_data = email.message_from_file(fd)
    # Get the email TO, SUBJECT data from the file.
    mail_to = mail_data.get('To')
    mail_subject = mail_data.get('Subject')
    # Get the attachment line. If not there, it results in a None value.
    mail_attach = mail_data.get('Attachment')
    # Get the email payload.
    mail_mesg = mail_data.get_payload(decode=False)
    fd.close()  # CLose the message file now.

    # Do some sanity checks on the TO and SUBJECT data
    if not email_checks(mail_to, mail_subject, p_filename):
        # There is a problem with the message itself. Move the message to the
        # other_msg folder for inspection by the System Administrator.
        newname = os.path.join(OTHR_FOLDER, os.path.basename(p_filename))
        # Move the file to the other_msg folder and ignore any errors
        try:
            shutil.move(p_filename, newname)
        except Exception:
            pass
        return False  # Exit function with failure

    # Create the email message
    message = EmailMessage()

    # Set the envelope information
    message["Subject"] = mail_subject
    message["To"] = mail_to
    message["From"] = p_from_adrs

    # Add the plain text part of the message.
    message.set_content(mail_mesg, subtype='plain')

    # Turn message body into an HTML object and add.
    html = f'''<html>
<body>
<pre style="font-family:'Courier new', monospace; font-size:100%;">
{mail_mesg}
</pre>
</body>
</html>'''
    message.set_content(html, subtype='html')

    # Add the attachment if this is requested,
    if mail_attach:
        # An attachment is to be emailed
        if os.path.isfile(mail_attach):
            basename = os.path.basename(mail_attach)

            # Get the MIME main and subtypes
            ctype, encode = mimetypes.guess_type(mail_attach)
            if ctype is None or encode is not None:
                # No guess could be made, or the file is encoded (compressed),
                # so use a generic type.
                ctype = 'application/octet-stream'

            # Get the MIME types for adding to the attachment
            maintype, subtype = ctype.split('/', 1)

            # Add the attachment to the email message
            with open(mail_attach, 'rb') as fp:
                message.add_attachment(fp.read(),
                                       maintype=maintype,
                                       subtype=subtype,
                                       filename=basename)
        else:
            # If file not been found, log error message, but do send email
            logging.error(LOG_ERR[8], mail_attach)

    # Send the email message created above.
    outcome = True  # Just making sure this is defined
    try:
        smtplink.sendmail(mail_username, mail_to, message.as_string())
        logging.debug("%s: Emailed the message: %s", progname, p_filename)
        outcome = True
    except Exception as errormsg:
        logging.error(LOG_ERR[6], p_filename, errormsg)
        outcome = False

    # If the message was send OK, move the message file to the unqueue folder
    # otherwise, as the message itself is OK, move it to the queue folder
    # where the sending will be retried at a later time
    if outcome:
        # Move the file to the unqueue folder for deleting
        newname = os.path.join(UNQUEUE_DIR, os.path.basename(p_filename))
        shutil.move(p_filename, newname)
    else:
        # There was an error sending the message, move it to the queue folder
        newname = os.path.join(QUEUE_DIR, os.path.basename(p_filename))
        try:
            # Move the mail file to the queue folder and ignore any errors
            shutil.move(p_filename, newname)
        except Exception:
            pass

    return outcome
# End send_the_message


# -----------------------------------------------------------------------------
# MAIN
def main():
    """
    Main control of sending email in an RFC 5322 formatted file.

    Initialise the program and its global variables.
    Check that there is at least one argument given. This must be an
    RFC 5322 formatted message filename.
    Call the function to open the SMTP link and to logon to the email
    account. This involves an internet access check. If failed, exit.
    Call the function to send the email. Outcome is True if the email
    was send successfully and False if there was an error detected.
    When a file has been emailed, it is moved to the "unqueu" folder so
    that it can be deleted by the script in which this program is run.
    Message file that was not send correctly is moved back to the queue
    folder to be tried again later.

    Arguments:
        None

    Return:
        0 -- Emailed message OK
        1 -- Error detected. See the logging messages file.
        3 -- SMTP link could not be established.
    """

    # Initialise the program
    initialise()
    logging.debug("===== Started %s", progname)

    # Set the exit status to OK, any errors detected will change this.
    outcome = 0

    # Check that there are any arguments. If not, exit with status 1
    if len(sys.argv) < 2:
        logging.error(LOG_ERR[7])
        sys.exit(1)

    # Open the SMTP link and logon to the email server
    if not open_smtp_server():
        sys.exit(3)  # Problem with connecting to the email server

    # For each argument passed, email the message.
    for mail_file in sys.argv[1:]:
        # Setup the From address line
        from_adrs = f'{hostname} <{mail_username}>'

        # Send the email and set the program exit status to the outcome of the
        # function.
        if not send_the_message(mail_file, from_adrs):
            outcome = 1

    smtplink.quit()
    logging.debug("===== Finished %s", progname)
    sys.exit(outcome)
# End main


if __name__ == "__main__":
    main()
# End Program
