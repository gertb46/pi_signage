#!/usr/bin/python3
"""
Check for emails and store them for processing.

Synopsis:
    check_read_email.py

Description:
    This program will check for emails at regular intervals and
    if any found it will read and store the messages. When all emails
    have been saved including any attachments, it starts the script that
    processes the saved messages.
    This program is intended to be run continuously in background.
    The correct way to stop this program is by sending it a SIGINT
    signal. That way the program terminates properly. The interval
    between checks is configurable in the common configuration file.

Arguments:
    None

Return:
    0 -- Normal exit

Run info:
    This program is to be run in background. It is started after a
    reboot and started and stopped via CRON entries.

See also:
    dotenv -- dotenv file with the secret information in.
    check_read_email.sh -- Script that executes this program.
    kill_check_email.sh -- Script to terminate this program.
    process_messages.sh -- Script to process the saved emails.
    signage.conf -- Configuration data providing environment variables.

Version:
    1.1

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
# Import the modules
import os
import sys
from time import sleep
import signal
import logging  # Debug and other message logging system.
import imaplib  # IMAP library
import email
from email.header import decode_header
import re  # Regular expressions
import dotenv   # To keep secrets in a dotenv file.


# -----------------------------------------------------------------------------
# VARIABLES AND CONSTANTS.
# Set the filename prefix and suffix to use for the message files
FILE_PREFIX = "msg"  # Message file prefix
TEXT_SUFFIX = ".txt"  # Text file name suffix
HTML_SUFFIX = ".html"  # HTML file name suffix

# Set the full path for the dotenv file
DOTENV_FILE = os.path.join(os.getcwd(), ".env")

# Set the path names for the message and attachment folders
MESG_FOLDER = os.getenv('MESG_FOLDER', default='messages')
ATCH_FOLDER = os.getenv('ATCH_FOLDER', default='attachments')
OTHR_FOLDER = os.getenv('OTHR_FOLDER', default='other_msg')

# Get the following constants from the main configuration file.
# Filename for the "logging" messages file.
LOG_FNAME = os.getenv('PI_SIGN_LOG', default='pi_signage.log')
# Timeout between checking for emails from the environment variable
EMAIL_TIMEOUT = os.getenv('EMAIL_TIMEOUT', default='30')
# Make sure the interval between email checks is an integer value.
EMAIL_TIMEOUT = int(EMAIL_TIMEOUT)

# Script name to read and process the emails
PROCESS_SCRIPT = './process_messages.sh'

# Global variables predefined here
#secrets = ''  # DOTENV secrets instance
imap = ''  # IMAP object to access the email server
mail_username = ''  # Email user account name
mail_server = ''  # Email server address
mail_portno = 993  # IMAP server port address
mail_password = ''  # Email user account password
mail_auth = []  # Sender authorisation email list
imap_open = False  # Flag true is connection to server is active

# Get the name of this program for use in the debug logging messages.
MYNAME = os.path.basename(sys.argv[0])

# -----------------------------------------------------------------------------
# LANGUAGE SPECIFIC constants
# The following texts can be translated to other languages if needed.
# The DEBUG messages are not listed here as they are not considered to need
# translation as they are only there during testing and for diagnostics.

# Logging messages definition. CKEML is this program identification
# LOG_ERR are the error messages
LOG_ERR = ('CKEML_0: Could not connect to IMAP server: %s',
           'CKEML_1: Process messages script outcome: %s',
           'CKEML_2: Failed imap search: %s',
           'CKEML_3: Failed to login: %s',
           'CKEML_4: INBOX not selected: %s',
           'CKEML_5: Unknown sender: %s')

# LOG_INFO are the information only messages
LOG_INFO = ('CKEML: Caught signal %s',
            'CKEML: Started pid=%s')


# -----------------------------------------------------------------------------
# SIGNAL_TERM_HANDLER
def signal_term_handler(signalnumber, frame):
    """
    Process the SIGINT signal.

    This function is called when the SIGINT signal has been sent to this
    program. It will log a INFO message to indicate that the signal was
    received. If the IMAP connection was open, close the connection.
    This makes it neat and tidy.
    Terminate this program with exit code 0 as this is a normal
    termination.

    Arguments:
        signalnumber -- The number of the signal that was caught
        frame -- Info about when the signal was caught. Ignore this.

    Return:
        Exit the program with code 0.
    """

    logging.info(LOG_INFO[0], signalnumber)
    # If the imap_open flag is True, close the imap connection.
    if imap_open:
        close_email_link()

    sys.exit(0)
# End signal_term_handler


# -----------------------------------------------------------------------------
# FUNCTION DEFINITIONS -- Common functions
def clean(text):
    """
    Clean text by replacing non-alphanumeric characters with underscore.
    This is used to clean up the attachment filenames.

    All non alphanumeric characters in the given text are replaced with
    an underscore. It will also preserve the dot character which is
    essential for file extensions.

    Arguments:
        text -- The text to be cleaned

    Return:
        string -- Cleaned text string.
    """

    return "".join(c if c.isalnum() or c == "." else "_" for c in text)


def check_mail_auth(from_adrs):
    """
    Check that sender email is in the authorised list.

    Check that the sender email address is in the list of authorised
    email addresses. The checked email address is between the <..>
    brackets in the from_adrs of the email message.

    Arguments:
        from_adrs -- Text of the From line of the email message.

    Return:
        True if in the list, False if not in the list.
    """

    # Extract the mailbox name from the <..> part of the string
    try:
        regex_pattern = "<(.+?)>"
        str_found = re.search(regex_pattern, from_adrs).group(1)
    except AttributeError:
        str_found = from_adrs

    # check that the email address found is in the list of senders ok to
    # send material. Return True or False acordingly.
    return bool(str_found in mail_auth)
# End Function definitions


# -----------------------------------------------------------------------------
# INITIALISE
def initialise():
    """
    Initialise the program.

    Setup the variables that are also used by other functions as GLOBAL.
    Extract from the Dotenv file the configuration variables and get the
    DEBUG flag. Configure the logging function with the desired logging
    level (depends on the DEBUG flag) and the message format.
    Set the signal capture for the SIGINT signal.

    Arguments:
        None

    Return:
        None
    """

    # Global variables for the email server, login, etc.
    global mail_username, mail_server, mail_portno, mail_password, mail_auth

    # Get the secrets from the Dotenv file
    secrets = dotenv.dotenv_values(DOTENV_FILE)
    mail_username = secrets["USERNAME"]
    mail_server = secrets["IMAP_SERVER"]
    mail_portno = secrets["IMAP_PORT"]
    mail_password = secrets["PASSWORD"]
    # Get the list of authorised email addresses
    mail_auth = list(secrets["EMAIL_AUTH"].split(","))

    # Set the logging level depending on the DEBUG value in th secrets file
    loglevel = getattr(logging, 'INFO', None)  # Default level is INFO
    if secrets["DEBUG"].lower() == "true":
        loglevel = getattr(logging, 'DEBUG', None)  # Set level to DEBUG

    # Setup the logging facility with message format, filename and log level
    logging.basicConfig(filename=LOG_FNAME, encoding='utf-8',
                        format='%(asctime)s %(levelname)s - %(message)s',
                        datefmt='%b %d %H:%M:%S',
                        level=loglevel)

    # Set-up the handler for the SIGINT interrupt signal.
    signal.signal(signal.SIGINT, signal_term_handler)

    # Send startup message with process id to the logging file
    logging.info(LOG_INFO[1], str(os.getpid()))
# End of INITIALISE


# -----------------------------------------------------------------------------
# OPEN_EMAIL_INBOX
def open_email_inbox():
    """
    Open the link to the email inbox and logon to the email account.

    Setup the link to the mail server and then logon to the INBOX using
    the username and password from the dotenv configuration file.
    Set the variable "imap" as a global variable as it will be used in
    other functions.
    If it is all successful, set the imap_open flag to True.

    Arguments:
        None

    Return:
        True -- Connected and logged on successfully
        False -- Problem with connecting to the IMAP server.
    """

    global imap, imap_open

    # Create an IMAP4 class with SSL
    logging.debug("Connecting to IMAP")
    try:
        imap = imaplib.IMAP4_SSL(mail_server, port=mail_portno, timeout=None)
    except Exception as err:
        logging.error(LOG_ERR[0], err)
        imap_open = False
        return False

    #sleep(2)  # See if this delay solves the login problem.
    #imap.noop()  # See if this works

    # Logon to the email server.
    try:
        imap.login(mail_username, mail_password)
    except Exception as err:
        logging.error(LOG_ERR[3], err)
        imap_open = False
        return False

    # Select the INBOX folder.
    try:
        imap.select("inbox")  # connect to inbox.
    except Exception as err:
        logging.error(LOG_ERR[4], err)
        imap_open = False
        return False

    logging.debug("Logged into imap server")
    imap_open = True
    return True
# End open_email_inbox


# -----------------------------------------------------------------------------
# CLOSE_EMAIL_LINK
def close_email_link():
    """
    Close the email link

    Close the IMAP email link and logout from the mailbox.
    Set the open flag to False.

    Arguments:
        None

    Return:
        False -- Always return with False
    """

    global imap_open

    try:
        imap.close()  # Close the IMAP connection
    except Exception:
        pass  # Ignore errors

    try:
        imap.logout()  # Logout of the email server
    except Exception:
        pass  # Ignore errors

    imap_open = False  # Mark connection as closed.
    return False
# End close_email_link


# -----------------------------------------------------------------------------
# READ_EMAILS
def read_emails(messages):
    """
    Read the emails, store in a file and download any attachments.

    Get the message count value from the DOTENV file and save the value
    to trigger the updating of the DOTENV counter at the end of this
    function.
    Read each email, store its contents into a file and download any
    attachments. Filenames of attachments that have the designation
    "=?UTF-8?" in the name are translated to proper filenames.
    Messages are stored in the "messages" folder and any attachments
    are stored in the "attachments" folder.

    Arguments:
        messages - Number of messages to retrieve

    Return:
        None
    """

    remove_list = []  # Empty list of messages to remove

    # Get the message counter value from the DOTENV file and save it.
    secrets = dotenv.dotenv_values(DOTENV_FILE)
    mcount = int(secrets["MESG_COUNT"])
    mcount_old = mcount  # Save the current message count
    logging.debug('Message count %s', mcount)

    # For all messages in the INBOX, process it.
    for i in range(1, messages + 1):

        # fetch the email message by ID
        res, msg = imap.fetch(str(i), "(RFC822)")
        logging.debug("i=%s, res=%s, msg type=%s", i, res, type(msg))

        for response in msg:
            logging.debug("for response in msg")
            if isinstance(response, tuple):
                logging.debug("instance is tuple")
                # Parse a bytes email into a message object
                emsg = email.message_from_bytes(response[1])

                # Decode email sender.
                from_email, encoding = decode_header(emsg.get("From"))[0]
                if isinstance(from_email, bytes):
                    from_email = from_email.decode(encoding)

                # Check if sender is authorised.
                if not check_mail_auth(from_email):
                    logging.error(LOG_ERR[5], from_email)
                    filename = FILE_PREFIX + str(mcount) + TEXT_SUFFIX
                    filepath = os.path.join(OTHR_FOLDER, filename)
                    with open(filepath, "w", encoding="utf-8") as fd:
                        fd.write(str(emsg))
                    mcount += 1
                    remove_list.append(str(i))
                    continue

                # Decode the email subject
                subject, encoding = decode_header(emsg["Subject"])[0]
                logging.debug("Subject type: %s Decode %s %s",
                              type(subject), type(encoding), encoding)
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding)
                    logging.debug("Subject is type bytes")

                # Decode email date
                date, encoding = decode_header(emsg.get("Date"))[0]
                if isinstance(date, bytes):
                    date = date.decode(encoding)

                logging.debug("Subject: %s", subject)
                logging.debug("From   : %s", from_email)
                logging.debug("Date   : %s", date)

                # If the email message is multipart
                if emsg.is_multipart():
                    logging.debug("Multipart detected")

                    # Iterate over email parts
                    for part in emsg.walk():
                        logging.debug("for part in emsg.walk")
                        # Extract content type of email
                        content_type = part.get_content_type()
                        content_disp = str(part.get("Content-Disposition"))
                        logging.debug("type: %s disposition %s",
                                      content_type, content_disp)

                        try:
                            # get the email body
                            body = part.get_payload(decode=True).decode()
                            logging.debug("message body found")
                        except Exception:
                            pass  # Ignore the error.

                        if (content_type == "text/plain" and
                           "attachment" not in content_disp):
                            # Save text/plain message
                            filename = FILE_PREFIX + str(mcount) + TEXT_SUFFIX
                            filepath = os.path.join(MESG_FOLDER, filename)
                            with open(filepath, "w", encoding="utf-8") as fd:
                                fd.write(body)

                        elif (content_type == "text/html" and
                              "attachment" not in content_disp):
                            # Save HTML message
                            logging.debug("Content type HTML found")
                            filename = FILE_PREFIX + str(mcount) + HTML_SUFFIX
                            filepath = os.path.join(MESG_FOLDER, filename)
                            with open(filepath, "w", encoding="utf-8") as fd:
                                fd.write(body)

                        elif "attachment" in content_disp:
                            # Download attachment
                            logging.debug("Attachment found")
                            filename = part.get_filename()
                            logging.debug("filename is type: %s",
                                          type(filename))
                            if filename:
                                # Check if filename needs translating (UTF-8)
                                if "=?UTF-8" in filename:
                                    filename, encoding = \
                                        decode_header(filename)[0]
                                    if isinstance(filename, bytes):
                                        filename = filename.decode(encoding)
                                logging.debug("Filename found: %s", filename)
                                filename = (FILE_PREFIX + str(mcount) +
                                            "_" + clean(filename))
                                filepath = os.path.join(ATCH_FOLDER, filename)
                                # Download attachment and save it
                                with open(filepath, "wb") as f:
                                    f.write(part.get_payload(decode=True))
                                logging.debug("Attachment: %s downloaded",
                                              filename)

                else:
                    # Extract content type of email
                    logging.debug("Not multipart")
                    content_type = emsg.get_content_type()
                    # Get the email body
                    body = emsg.get_payload(decode=True).decode()
                    if content_type == "text/plain":
                        filename = FILE_PREFIX + str(mcount) + TEXT_SUFFIX
                        filepath = os.path.join(MESG_FOLDER, filename)
                        with open(filepath, "w", encoding="utf-8") as fd:
                            fd.write(body)

                # End if emsg.is_multipart()

            # End if isinstance(response, tuple)

        remove_list.append(str(i))  # Add message id to removal list
        mcount += 1  # Add one to the message counter

        # End for response in msg
    # End for i in range

    # Delete the read emails using the message numbers in the remove_list
    if len(remove_list) > 0:  # if any messages in the list
        logging.debug("remove_list= %s", remove_list)
        delete_emails(remove_list)

    # Write the message counter into the dotenv file only if changed.
    if mcount_old != mcount:
        if mcount > 9990:  # Reset message counter to 1 after 9990.
            mcount = 1
        dotenv.set_key(DOTENV_FILE, 'MESG_COUNT', str(mcount))
        logging.debug("Message counter is: %d", mcount)
# End read_emails()


# -----------------------------------------------------------------------------
# DELETE_EMAILS
def delete_emails(rem_list):
    """
    Remove the emails as per the given list of email IDs

    Delete the emails as per the given list of messages IDs.

    Arguments:
        rem_list -- List of email IDs to delete from the email inbox

    return:
        None
    """

    logging.debug("Deleting emails")

    for mail_id in rem_list:
        resp_code, response = imap.store(mail_id, "+FLAGS", "\\Deleted")
        logging.debug("Delete code %s Resp %s", resp_code,
                      response[0].decode() if response[0] else None)

    resp_code, response = imap.expunge()
    logging.debug("Expunge code %s Resp %s", resp_code,
                  response[0].decode() if response[0] else None)
# End delete_emails


# -----------------------------------------------------------------------------
# MAIN
def main():
    """
    Main control of this program

    Perform the initialisation routine to ensure that all constants are
    obtained from the dotenv file and the logging level set to include
    or exclude debug logging messages.
    The -outer- loop is a perpetual loop that opens the email inbox.
    Any problems with this will then ensure that the inner loop is not
    executed and will sleep for the configurable amount of seconds. The
    latter is to ensure that there is a wait before the connection to
    the email server is attempted again.
    Then the -inner- loop is started. This loop is only run if the
    'sentry' flag is true. Therefore this flag controls the loop.
    This inner loop is the one that will check if there are any INBOX
    email messages. If messages found, read and save the messages and
    any attachments. Then process the email messages.
    At the end of this -inner- loop, wait for a "configurable" number
    of seconds before continuing the loop.

    Arguments:
        None

    Return:
        None

    """
    global imap_open

    initialise()  # Set-up the program and the constants.

    # This is the outer loop of this program. It runs forever.
    # This program is terminated by sending the SIGINT signal.
    while True:
        sentry = True  # Allows the inner loop to work.

        # Open the connection to the email server and log on.
        if not open_email_inbox():
            # There is a problem with logging on.
            sentry = False  # Set to false to bypass the inner loop

        # This is the inner loop that will check for any emails in the INBOX.
        # Its loop is stopped by the 'sentry' flag being False.
        while sentry:
            count = 0  # Set message counter to zero

            # Select the INBOX folder.
            try:
                imap.select()  # connect to inbox.
            except Exception as err:
                logging.error(LOG_ERR[4], err)
                imap_open = close_email_link()
                sentry = False
                continue

            # Check for any email messages
            try:
                return_code, mail_ids = imap.search(None, 'ALL')
            except Exception as err:
                logging.error(LOG_ERR[2], err)
                return_code = None

            if return_code == 'OK':
                # Get the number of new email messages
                logging.debug("Return Code %s, Mail ID %s, length %s",
                              return_code, mail_ids[0], len(mail_ids[0]))
                count = len((mail_ids[0].decode()).split(" ")) \
                    if len(mail_ids[0]) > 0 else 0
            else:
                # Email check failed. Close cnx and wait the time out
                imap_open = close_email_link()  # Close the IMAP link
                sentry = False  # Stop this inner loop, forces reconnect

            # If there are any emails waiting, read and save them.
            # When read and saved, run the script to process them.
            if count > 0:
                # There are unread emails. First close the email link
                #imap_open = close_email_link()  # Close the IMAP link
                logging.debug("There are %d INBOX messages", count)

                # Read and save the email in the INBOX
                read_emails(count)

                # Start the script to reead and process the emails
                outcome = os.system(PROCESS_SCRIPT)
                if outcome != 0:
                    logging.error(LOG_ERR[1], outcome)

            # Sleep for a number of seconds before checking again
            sleep(EMAIL_TIMEOUT)
        # End while sentry

        sleep(EMAIL_TIMEOUT)
    # End while True

    # Unlikely to finish here, but keep just in case.
    imap_open = close_email_link()  # Close the IMAP link
# End of main


if __name__ == "__main__":
    main()
# End Program
