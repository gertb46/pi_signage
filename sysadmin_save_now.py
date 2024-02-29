#!/usr/bin/python3
"""
System Admin task to save the running_now file

Synopsis:
    sysadmin_save_now.py perm_file

Description:
    Save the running_now trigger file. This copies the running_now
    file to the permanent folder using the file name given in
    argument 1. If the presentation requires an attachment file, copy
    the attachment file to the permanent folder.

Arguments:
    perm_file -- Filename for the saved running_now file.

Return:
    0 -- Normal exit.
    1 -- Errors detected. See the logging file.

See also:
    dotenv -- dotenv file with the secret information in.
    sysadmin_tasks.sh -- Script that executes this program.
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
# MODULES
import os
import sys
import re
import shutil  # Used for copying running files
import logging  # Debug and other message logging system.
import dotenv  # Secrets and other configuration data


# -----------------------------------------------------------------------------
# CONSTANT DEFINITIONS
# File prefix and suffixes for the filenames in the messages folder
FILE_PREFIX = "msg"  # Message file prefix
TEXT_SUFFIX = ".txt"  # Text file name suffix
HTML_SUFFIX = ".html"  # HTML file name suffix
PPOINT_SUFFIX = ".ppsx"  # PowerPoint file extension

# Get the working folder
WORK_FOLDER = os.getcwd()

# Get information from the environment variables as defined in
# the signage.conf file.

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
# LANGUAGE SPECIFIC constants
# The following texts can be translated to other languages if needed.
# The DEBUG messages are not listed here as they are not considered to need
# translation as they are only used during testing and for diagnostics.

# Logging messages definition. SYSSV is this program identification
# LOG_ERR are the error messages
LOG_ERR = ('SYSSV: Insufficient arguments',
           'SYSSV: Moving attachment failed!',
           'SYSSV: Copy running_now file failed')


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

    # Get the secrets values from the dotenv file
    secrets = dotenv.dotenv_values(DOTENV_FILE)

    # Set the logging level depending on the DEBUG value in the secrets file
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
# MAIN
def main():
    """
    Main control of this program.

    Initialise the program.
    If there is no argument with this program then log an error and exit
    the program with code 1.
    Open the running now file and read the contents. This is necessary
    because of the attachment that may be associated with this trigger
    file.
    If the RUN_CMND is for a PowerPoint or LibreOffice Impress
    presentation, get the filename from the RUN_DATA and copy the
    attachment file to the permanent folder. Any errors, log them and
    exit the program with code 1.
    Now copy the running now file to the new filename and store in the
    permanent folder.

    Arguments:
        filename -- Name of the file to save the running now trigger
                    file to.

    Return:
        0 -- All OK
        1 -- Argument or file error
    """

    # Initialise the program
    initialise()

    # Argument 1 is the new permanent file name for the running_now copy.
    if len(sys.argv) < 2:
        logging.error(LOG_ERR[0])
        sys.exit(1)

    perm_name = sys.argv[1]  # Get the filename for the permanent copy.

    # Read the running_now file
    with open(RUN_NOW_FILE, 'r', encoding='utf8') as fd:
        txt = fd.read()

    # Split the read data into lines. This produces a list.
    lines = txt.splitlines()

    if 'powerpoint' in lines[0] or 'impress' in lines[0]:
        # This is a powerpoint or impress cmnd
        # so run data is the attachment filename.

        # Now get the data from the second line.
        atch_name = re.findall("'([^']*)'", lines[1])

        # Copy the attachment to the permanent folder.
        atch_path = os.path.join(ATCH_FOLDER, atch_name[0])
        perm_path = os.path.join(PERM_FOLDER, atch_name[0])
        try:
            shutil.move(atch_path, perm_path)
        except Exception:
            logging.error(LOG_ERR[1])
            sys.exit(1)

    # Now copy the running_now file to the permanent folder using the
    # second argument as the filename to use for this.
    perm_path = os.path.join(PERM_FOLDER, perm_name)
    try:
        shutil.copy(RUN_NOW_FILE, perm_path)
    except Exception:
        logging.error(LOG_ERR[2])
        sys.exit(1)

    logging.info('SAVENOW: Copied running_now to permanant file %s', perm_name)

    logging.debug("===== Finished %s", os.path.basename(sys.argv[0]))
    sys.exit(0)
# End main


if __name__ == "__main__":
    main()
# End Program
