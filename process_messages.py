#!/usr/bin/python3
"""
Process the files in the messages folder.

Synopsis:
    process_messages.py

Description:
    Process the files in the messages folder and any attachments.
    For each message file, read the contents and extract the commands
    and data. Generate from this information the trigger files.
    If the command needs any attachments, add that information to
    the trigger file.
    If the command is for a system admin task, generate a trigger file
    for the system admin task.
    All files are processed first and when finished, the trigger files
    will start the necessary scripts.

Arguments:
    None

Return:
    0 -- Normal exit

Run info:
    This program must be run by the process_messages.sh script only.

See also:
    dotenv -- dotenv file for configuration information.
    process_messages.sh -- Script that executes this program.
    html2text -- Utility to convert HTML to text.
    signage.conf -- Configuration data providing environment variables
                    when running this inside a BASH script.

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
# MODULES
import glob
import os
import sys
import csv
import re
import subprocess  # For running the html2text utility
import shutil  # Used for copying running files
import logging  # Debug and other message logging system
import dotenv  # Secrets and other configuration data
import platform   # To detect which html2text command to run


# -----------------------------------------------------------------------------
# CONSTANT DEFINITIONS
# File prefix and suffixes for the filenames in the messages folder
FILE_PREFIX = "msg"  # Message file prefix
TEXT_SUFFIX = ".txt"  # Text file name suffix
HTML_SUFFIX = ".html"  # HTML file name suffix
PPOINT_SUFFIX = ".ppsx"  # PowerPoint file extension
IMPRES_SUFFIX = ".odp"  # LibreOffice Impress file extension

# Get the working folder
WORK_FOLDER = os.getcwd()

# Get information from the environment variables set by the signage.conf file.

# Set the path names for the folders accesses by this program
MESG_FOLDER = os.getenv('MESG_FOLDER', default='messages')
ATCH_FOLDER = os.getenv('ATCH_FOLDER', default='attachments')
PERM_FOLDER = os.getenv('PERM_FOLDER', default='permanent')

# Set the full path for the dotenv file
DOTENV_FILE = os.path.join(WORK_FOLDER, ".env")

# Set the filename for the "logging" messages file
LOG_FNAME = os.getenv('PI_SIGN_LOG', default='pi_signage.log')

# Define the running now and next and manage next filenames
RUN_NEXT_FILE = os.getenv('RUN_NEXT', default='running_next')
RUN_NOW_FILE = os.getenv('RUN_NOW', default='running_now')
RUN_ADM_FILE = os.getenv('RUN_ADM', default='manage_next')

# -----------------------------------------------------------------------------
# LANGUAGE CHANGEABLE constants
# The following texts can be translated to other languages if needed.
# The DEBUG messages are not listed here as they are not considered to need
# translation as they are only there during testing and for diagnostics.

# Management commands that are recognised as valid ones
# These commands are passed to the SysAdmin task script!
SYSADM_CMDS = ('list', 'update', 'reboot', 'screen', 'save_now',
               'crontab', 'shutdown', 'download', 'delete')

# Command words for the presentations. These are processed by this program!
CMND_GOOGLE = 'google'  # Google Slides presentation
CMND_POWERP = 'powerpoint'  # PowerPoint presentation
CMND_IMPRESS = 'impress'  # LibreOffice Impress presentation
CMND_HALT = 'halt'  # Stop the current presentation
CMND_STOP = 'stop'  # Stop the current presentation
CMND_START = 'start'  # Start the current presentation (running_now)
CMND_RSTART = 'restart'  # Start the current presentation (running_now)
CMND_RUN = 'run'  # Start a saved presentation
CMND_DEBUG = 'debug'  # Turn DEBUG flag on or off
CMND_AUTH1 = 'email_auth'  # Update the authorised email sender list
CMND_AUTH2 = 'emailauth'  # Update the authorised email sender list

# Logging messages definition. PRMSG is this program identification
# LOG_ERR are the error messages
LOG_ERR = ('PRMSG: Unknown file extn for: %s',
           'PRMSG: No data in the list of email addresses',
           'PRMSG: Restart: Copy to running_next failed!',
           'PRMSG: Email address invalid: %s',
           'PRMSG: Google URL is not for google slides',
           'PRMSG: Could not copy permanent file: %s',
           'PRMSG: Permanent file %s does not exist',
           'PRMSG: No filename given with RUN command',
           'PRMSG: Could not remove file %s')

# LOG_INF are the information messages.
LOG_INF = ('PRMSG: Updated EMAIL AUTH to: %s',
           'PRMSG: Updated DEBUG to %s',
           'PRMSG: Command requested: %s')
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# GET_FILENAME_EXT
def get_filename_ext(filepath):
    """
    Get the filename and it's extension from a given filename.

    Extracts from the given filepath, the filename and the extension and
    return them as a two elements.

    Arguments:
        filepath -- The file path name from which to extract the
                    filename and extension (.extn)

    Return:
        filename, fileext -- Return tuple with filename and extension
    """

    #   Return the filename and it's extension.
    return os.path.splitext(os.path.basename(filepath))
# End get_filename_ext


# -----------------------------------------------------------------------------
# WRITE_NEXT_FILE
def write_next_file(parm_cmnd, parm_data):
    """
    Write the command and data to the running next trigger file.

    Arguments:
        parm_cmnd -- Command to write to the file
        parm_data -- Data to write to the file

    Return:
        None
    """
    # Open a new running next file and write the cmnd and data to it.
    with open(RUN_NEXT_FILE, 'w', encoding="utf-8") as f:
        f.write(f"export RUN_CMND='{parm_cmnd}'\n")
        f.write(f"export RUN_DATA='{parm_data}'\n")
# End write_next_file


# -----------------------------------------------------------------------------
# WRITE_ADM_FILE
def write_adm_file(parm_cmnd, parm_data, parm_atch):
    """
    Write the date to the System Admin management trigger file.

    Arguments:
        parm_cmnd -- Command to write to the file
        parm_data -- Data to write to the file
        parm_atch -- Attachment file name to write to the file

    Return:
        None
    """

    # Open a new sys admin next file and write the cmnd and data to it.
    with open(RUN_ADM_FILE, 'w', encoding="utf-8") as f:
        f.write(f"export RUN_CMND='{parm_cmnd}'\n")
        f.write(f"export RUN_DATA='{parm_data}'\n")
        f.write(f"export RUN_ATCH='{parm_atch}'\n")

    logging.debug("Written the manage file: %s.", RUN_ADM_FILE)

# End write_adm_file


# -----------------------------------------------------------------------------
# INITIALISE
def initialise():
    """
    Initialise this program.

    From the dotenv set of variables, get the logging level.
    Set the logging level depending on the DEBUG variable from the
    dotenv secrets file.

    Arguments:
        None

    Return:
        None
    """

    # Get the secrets from the dotenv file
    secrets = dotenv.dotenv_values(DOTENV_FILE)

    # Set the logging level depending on the DEBUG value in th secrets file
    loglevel = getattr(logging, 'INFO', None)  # Default level is INFO
    if secrets["DEBUG"].lower() == "true":
        loglevel = getattr(logging, 'DEBUG', None)  # Set level to DEBUG

    # Setup the logging facility with message format, filename and log level
    logging.basicConfig(filename=LOG_FNAME, encoding='utf-8',
                        format='%(asctime)s %(levelname)s - %(message)s',
                        datefmt='%b %d %H:%M:%S',
                        level=loglevel)

    logging.debug("===== Started %s", os.path.basename(sys.argv[0]))
# End initialise


# -----------------------------------------------------------------------------
# PROCESS_FILES
def process_files():
    """
    Process all files in the "messages" folder.

    If no files in the message folder, exit this function with empty
    list of files to remove. This function only deals with message files
    with the extension ".html" and ".txt". Any files not having the
    correct file extension are ignored and are deleted.
    HTML files are converted to text using the "html2text" utility.
    If a .txt file has a corresponding .html file, it is ignored,
    otherwise the file contents is used.
    The text data is then processed by the "process_data" function.

    Arguments:
        None

    Return
        remove_list -- The list of message files that are to be deleted.
    """

    # Create an empty list of emails to remove
    remove_list = []

    # Check that the messages folder is not empty, else exit this function
    if not os.listdir(MESG_FOLDER):
        logging.debug("No files found in messages folder")
        return remove_list

    # For each file in the messages folder
    for filename in sorted(glob.glob(MESG_FOLDER + '/*')):
        # Get the filename and suffix in separate variables
        fname, extn = get_filename_ext(filename)
        logging.debug("filename: %s fname: %s extn: %s", filename, fname, extn)

        if extn.lower() == HTML_SUFFIX:
            # Process the HTML version of the email message
            logging.debug("HTML file processing %s", filename)

            # Setup the command to run the html2text utility
            if platform.machine() == 'x86_64':  # Which machine is this?
                # This command is for when testing on Linux-Mint
                cmd = ['html2text', '-b', '0', '--ignore-links', filename]
            else:
                # This is the command for when running on a Raspberry Pi
                cmd = ['html2text', '-width', '300', filename]

            # Convert the HTML file to text using the HTML2TEXT program.
            html_lines = subprocess.check_output(cmd, text=True)
            # Replace non-breaking spaces with real spaces.
            html_lines = html_lines.replace(u'\xa0', ' ')
            process_data(html_lines, fname)
            remove_list.append(filename)

        elif extn.lower() == TEXT_SUFFIX:
            # Process the TEXT version of the email message
            # If there is an HTML version of this file, ignore the
            # text file as it may not be in the correct format.
            logging.debug("TEXT file processing")

            # Check that the TXT file does not have an HTML file also
            # because then we can ignore the TXT file.
            if os.path.isfile(MESG_FOLDER + "/" + fname + HTML_SUFFIX):
                remove_list.append(filename)
                logging.debug("Ignoring this txt file")
            else:
                logging.debug("--TXT is only one")
                with open(filename, 'r', encoding="utf-8") as f:
                    text_lines = f.read()
                process_data(text_lines, fname)
                remove_list.append(filename)

        else:
            # Unknown extension. This should not happen, but is possible.
            # Just log the error and add the name to the removal list.
            logging.error(LOG_ERR[0], filename)
            remove_list.append(filename)

    return remove_list
# End process_files


# -----------------------------------------------------------------------------
# PROCESS_DATA
def process_data(text_data, mesg_prefix):
    """
    Process the data taken from a file in the messages folder.

    The data consists of the lines of text taken from the email message.
    Each line is considered to be an instruction with the first word
    being the command and the rest of the line the data to be used.
    The command is tested in lowercase to avoid any upper and
    lower case problems. Appropriate trigger files are created depending
    on the command and data provided.

    Arguments:
        text_data -- The text data (multiple lines) to be processed.
        mesg_prefix -- Prefix of the message file being processed.

    Return:
        None
    """

    # For every line in the text data, process the words in the line.
    logging.debug("Processing the data")

    for line in text_data.splitlines():
        line = line.strip()  # Get rid of leading/trailing spaces
        if len(line) < 1:  # If line is empty
            continue  # ignore the line and get next one

        logging.debug("Doing line: %s", line)

        # Get all the words in a line into a word list
        word_list = line.split()

        # If there are no words in the list (empty line), ignore this line.
        if len(word_list) == 0:
            continue

        # Get the first word in the line, which is the command to execute.
        command = word_list[0].lower()
        logging.debug("Found first word: %s", command)

        # Get the rest of the words after cmd. This is now in a CSV format.
        rest_of_list = ','.join(word_list[1:])
        logging.debug("Rest of list is: %s", rest_of_list)

        # Process the command.
        if command in (CMND_AUTH1, CMND_AUTH2):
            if len(rest_of_list) > 0:   # At least one word in the line
                logging.debug("Found %s List: %s", word_list[0], rest_of_list)
                update_email_auth(rest_of_list)
            else:
                # If there are no words in the list then do not update the
                # email authorisation list.
                logging.error(LOG_ERR[1])

        elif command == CMND_DEBUG:
            # Debug command. Change the dotenv file setting
            update_debug_var(rest_of_list)
            logging.info(LOG_INF[2], command)

        elif command == CMND_GOOGLE:
            # Google will set the parameters for the next presentation to
            # run and when program terminates this triggers a restart.
            write_google_data(rest_of_list)
            logging.info(LOG_INF[2], command)

        elif command in (CMND_POWERP, CMND_IMPRESS):
            # PowerPoint or Impress command.
            # Copy the data to the running_next file
            write_pp_impress_data(mesg_prefix)
            logging.info(LOG_INF[2], command)

        elif command == CMND_RUN:
            # RUN command found. Create the running_next file from the data
            write_run_file(rest_of_list)
            logging.info(LOG_INF[2], command)

        elif command in (CMND_START, CMND_RSTART):
            # Copy the running now file to the running next file.
            # This should trigger a restart when this program terminates.
            try:
                shutil.copy(RUN_NOW_FILE, RUN_NEXT_FILE)
            except Exception:
                logging.error(LOG_ERR[2])

            logging.info(LOG_INF[2], command)

        elif command in (CMND_STOP, CMND_HALT):
            # These commands simply create a running_next file with just the
            # command and the data left empty
            write_next_file(CMND_STOP, '')
            logging.info(LOG_INF[2], command)

        elif command in SYSADM_CMDS:
            # These command generate a manage_next file with the three
            # variables for the management process
            write_manage_next(mesg_prefix, command, line)

        else:
            # Ignore all unknown commands
            # This statement is here for completeness
            pass

    # End for line in text_data
# End process_data


# -----------------------------------------------------------------------------
# UPDATE_EMAIL_AUTH
def update_email_auth(email_list):
    """
    Update the authorised email list in the dotenv file.

    This given list will be converted to a list variable. The email
    addresses are checked for having at least one @ sign it them.
    If not correct, then the variable is not updated.

    Arguments:
        email_list -- list of words that were on the same line as the
                      EMAIL_AUTH command.

    Return:
        None
    """

    # Make a regular expression for validating an Email
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+'
                       r'@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')

    # First check that all email addresses have a proper format.
    for email_adrs in email_list.split(','):
        # Check that email_adrs is a proper email address
        if not re.fullmatch(regex, email_adrs):
            logging.error(LOG_ERR[3], email_adrs)
            return

    # Set the EMAIL_AUTH variable to the given email list.
    outcome = dotenv.set_key(DOTENV_FILE, "EMAIL_AUTH", email_list)
    logging.debug("dotenv AUTH set outcome=%s", outcome)

    logging.info(LOG_INF[0], email_list)
# End update_email_auth


# -----------------------------------------------------------------------------
# UPDATE_DEBUG_VAR
def update_debug_var(param_list):
    """
    Update the DEBUG variable in the dotenv file.

    Arguments:
        param_list -- List of words that were on the same line as the
                      DEBUG command.

    Return:
        None.
    """

    # Get the arguments from the given parameter list
    arg_list = param_list.split(',')
    logging.debug("debug param_list: %s", arg_list[0])
    # Set debug flag to True if argument[1] is yes or on, False otherwise
    new_debug = bool(arg_list[0].lower() == 'yes' or
                     arg_list[0].lower() == 'on' or
                     arg_list[0].lower() == 'true')
    # Update the dotenv file with the new debug value
    outcome = dotenv.set_key(DOTENV_FILE, 'DEBUG', str(new_debug))
    logging.debug("dotenv DEBUG set outcome=%s", outcome)

    logging.info(LOG_INF[1], str(new_debug))
# End update_debug_var


# -----------------------------------------------------------------------------
# WRITE_GOOGLE_DATA
def write_google_data(rest_of_list):
    """
    Write the running_next data for a Google slides show.

    Using the data in the "rest_of_list" parameter, check first that it
    is for a Google Slide show by ensuring it has the right DNS name
    in the URL. If not, error message and remove any existing run_next
    file.
    Write the two environment variables to the next presentation to run.
    The variables are RUN_CMND and RUN_DATA, where RUN_CMND is set to
    'google'. Add the command 'export' to the variables so that they can
    be used in a Python or other program,

    Arguments:
        rest_of_list -- The remainder of the line from the email data

    Return:
        None
    """

    # Check that the URL is for a Google slides presentation
    if "docs.google.com" not in rest_of_list.lower():
        logging.error(LOG_ERR[4])
        return

    # Generate the sourced-in file for the next slide show to run.
    # "rest_of_list" is the URL for the Google slides to run.
    # Write the two environment variables for the Google Slides.
    write_next_file(CMND_GOOGLE, rest_of_list)

    logging.debug("Written the running_next file: %s.", RUN_NEXT_FILE)
# End write_google_data


# -----------------------------------------------------------------------------
# WRITE_PP_IMPRESS_DATA
def write_pp_impress_data(fileprefix):
    """
    Write a PowerPoint or Impress running_next file.

    Get a list of attachments from the attachment folder and search
    this list for a file that starts with the file same prefix as the
    message and ends with the suffix for PowerPoint or Impress.

    If not found, exit the function with a False value. Ensure that
    the message filename goes into the list of messages to delete.
    Log this condition.

    Arguments:
        fileprefix -- The string that should be at the start of the
                      attachment file.

    Return:
        None
    """

    # Get the list of files in the attachment folder
    atch_folder = os.path.join(WORK_FOLDER, ATCH_FOLDER)
    atch_list = list(os.listdir(atch_folder))

    # If there are any files in the attachment folder
    if len(atch_list) > 0:
        logging.debug("Files found in attachment folder")
        # Check if any of the files start with the message name and has
        # the PowerPoint file extension
        for atch_name in atch_list:
            if (atch_name.startswith(fileprefix) and
               (atch_name.endswith(IMPRES_SUFFIX) or
               atch_name.endswith(PPOINT_SUFFIX))):
                # Attachment found
                logging.debug("Attachment %s found", atch_name)
                # Generate the running_next file.
                # full_path = os.path.join(ATCH_FOLDER, atch_name)
                write_next_file(CMND_POWERP, atch_name)
                logging.debug("Written the running_next file: %s.",
                              RUN_NEXT_FILE)

    else:
        logging.debug("No files in attachment folder found")
# End write_pp_impress_data


# -----------------------------------------------------------------------------
# WRITE_RUN_FILE
def write_run_file(p_filedata):
    """
    Get the RUN filename and copy from permanent file to running_next

    Using the data given with the RUN command, if there is any data and
    if the data is a file name in the permanent folder, copy the
    permanent file to the running-next file. This will trigger the start
    of that presentation.

    Arguments:
        p_filedata -- Filename data from the RUN command in the message

    Return:
        None
    """

    # Check that there is any data and that it is for an existing file
    if len(p_filedata) > 0:
        perm_file = os.path.join(PERM_FOLDER, p_filedata)
        if os.path.isfile(perm_file):
            logging.debug("Found the permanent file %s", p_filedata)
            try:
                shutil.copy(perm_file, RUN_NEXT_FILE)
            except Exception:
                logging.error(LOG_ERR[5], perm_file)
        else:
            logging.error(LOG_ERR[6], perm_file)
    else:
        logging.error(LOG_ERR[7])
# End write_run_file


# -----------------------------------------------------------------------------
# WRITE_MANAGE_NEXT
def write_manage_next(p_fileprefix,  p_cmnd, p_data):
    """
    Write the System Admin manage_next file.

    The p_data is unravelled using the csv module methods. This will
    result in a list within a list. It contains the command and data
    provided.
    The attachment files are checked and the one with the filename that
    starts with the file prefix parameter is selected. If found, that is
    used in the manage_next trigger file.

    Arguments:
        p_fileprefix -- Filename prefix used for finding attachment
        p_cmnd -- Management command
        p_data -- Data for the management command

    Return:
        None
    """

    # Unravel the line of text and get the command and filename from the line
    # There may be more than one data items after the command but those
    # are ignored.
    lines = p_data.splitlines()
    words = list(csv.reader(lines, delimiter=' ', quotechar='"'))
    # words is now a one element list with an embedded list in it
    mng_data = ''  # Define data variable and set to empty
    atch_file = ''  # Attachment file name when found
    mng_data = ' '.join(words[0][1:]).strip()

    # Get the list of files in the attachment folder
    atch_list = os.listdir(ATCH_FOLDER)

    # If there are any files in the attachment folder
    if len(atch_list) > 0:
        logging.debug("Files found in attachment folder")
        # Check if any of the files start with the message name (fileprefix)
        for atch_name in atch_list:
            if atch_name.startswith(p_fileprefix):
                # Attachment found
                logging.debug("Attachment %s found", atch_name)
                # Make sure multiple attachments are concatenated properly
                if atch_file == '':
                    atch_file = atch_name
                else:
                    atch_file = atch_file + "," + atch_name
    else:
        logging.debug("No files in attachment folder found")

    # Generate the running_next file
    write_adm_file(p_cmnd, mng_data, atch_file)
# End write_manage_next


# -----------------------------------------------------------------------------
# REMOVE_FILES
def remove_files(remove_list):
    """
    Remove all the files that are in the removal list given.

    Arguments:
        remove_list -- The list of files to be removed.

    Return:
        None
    """

    logging.debug("Removing the files")

    for filename in remove_list:
        try:
            os.remove(filename)
        except FileNotFoundError:
            logging.error(LOG_ERR[8], filename)
# End remove_files


# -----------------------------------------------------------------------------
# MAIN
def main():
    """
    Main control of the program.

    Initialise the program setting global variable values.
    Process the message files and return a list of message files that
    can be deleted. This process creates one or more 'command' files
    that are used by other scripts to perform specific functions.
    If there are any message files to be deleted, remove them.

    Arguments:
        None

    Return:
        0 -- OK
    """

    #   Initialise the program
    initialise()

    #   Process the files, returning the list of files to delete.
    remove_list = process_files()

    #   Remove the processed files as per the remove_list
    if len(remove_list) > 0:  # if any messages in the list
        logging.debug("Remove list= %s", remove_list)
        remove_files(remove_list)

    logging.debug("===== Finished %s", os.path.basename(sys.argv[0]))

    sys.exit(0)
# End main


if __name__ == "__main__":
    main()
