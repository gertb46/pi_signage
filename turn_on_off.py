#!/usr/bin/python3
"""
Turn the ENERGENiE power sockets on or off.

Synopsis:
    turn_on_off.py  socket_no  on|off

Description:
    This program will turn an ENERGENiE power socket on or off. This is
    either for an individual socket or for all sockets. The GPIO
    daughter board that is present can handle up to 4 sockets. It is
    assumed that the sockets are properly set up.

Arguments:
    socket_no --  Number of the socket (1-4) or 0 for all sockets
    on/off -- On or Off to turn the socket on or off

Return:
    0 -- Normal exit
    1 -- Error found with the arguments.

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
import sys
import os
import logging
import dotenv  # Secrets and other configuration data

from energenie import switch_on, switch_off

# Get the working directory
WORK_FOLDER = os.getcwd()

# Set the filename for the "logging" messages file
LOG_FNAME = os.getenv('PI_SIGN_LOG', default='pi_signage.log')

# Set the full path for the dotenv file
DOTENV_FILE = os.path.join(WORK_FOLDER, ".env")

# -----------------------------------------------------------------------------
# LANGUAGE SPECIFIC constants
# The following texts can be translated to other languages if needed.
# The DEBUG messages are not listed here as they are not considered to need
# translation as they are only there during testing and for diagnostics.

# Logging messages definition. TRNON is this program identification
# LOG_ERR are the error messages
LOG_ERR = ('TRNON: Invalid number of arguments!',
           'TRNON: Socket number is not 0-4',
           'TRNON: Socket number is not numeric',
           'TRNON: Argument 2 is not ON or OFF')


# -----------------------------------------------------------------------------
# MAIN
def main():
    """
    Main control of the program.

    First check that there are 2 arguments and that argument 1 is
    numeric and the value is from 0 to 4. Check that argument 2 is
    either ON or OFF (any case). Any problems, display an error message
    and exit with status 1.

    Now send the correct command to the socket(s) to turn them on or off
    and exit the program with status 0.

    Arguments:
        None

    Return:
        None
    """

    # First initialise the logging feature
    # Get the secrets values from the dotenv file
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

    # Check that there are 2 arguments given when executing this program.
    if len(sys.argv) < 3:
        logging.error(LOG_ERR[0])
        sys.exit(1)

    # Check that the first argument is numeric and that its value is from
    # zero to four.
    if sys.argv[1].isnumeric():
        socketno = int(sys.argv[1])
        if socketno not in range(5):
            logging.error(LOG_ERR[1])
            sys.exit(1)
    else:
        logging.error(LOG_ERR[2])
        sys.exit(1)

    # Turn the socket(s) on or off depending on the second argument.
    # If the second argument is not ON or OFF exit the program with status
    # of 1.
    if sys.argv[2].lower() == "on":
        switch_on(socketno)
    elif sys.argv[2].lower() == "off":
        switch_off(socketno)
    else:
        logging.error(LOG_ERR[3])
        sys.exit(1)

    sys.exit(0)
# End main


if __name__ == "__main__":
    main()
# End Program
