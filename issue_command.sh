#!/bin/bash
#============================================================================
# NAME        : issue_command.sh
# DESCRIPTION : Issue a variety of commands for presentations and management.
#             : This is part of the "Digital Signage" project.
# SYNOPSIS    : issue_command.sh command [command argument ...]
# AUTHOR      : Gert Bakker, Coleshill, UK
# DATE        : January 2024
# VERSION     : 1.0
# USAGE       : Use from command line, via CRON and/or other scripts.
# NOTES       : This script issues commands for controlling presentations
#             : and other management tasks.
# -----------------------------------------------------------------------------
# Copyright (C) 2023 Gert Bakker, Coleshill,  UK
# All rights reserved.
# Distributed under the GNU general Public License as published by the
# Free Software Foundation, version 3.
# For full text of the license, see the file gnu_licence.txt
#============================================================================

#============================================================================
# Set the working directory.
cd "${HOME}"/Documents/pi_signage || exit 1
# Get my program name
MYNAME=$(basename "$0")

#============================================================================
# INCLUDED SOURCES
. signage.conf  # Main configuration constants
. logging.func  # Function to log messages to the main log file

#============================================================================
# FUNCTION DEFINITIONS

# Function to send an error message to STDERR
# use as:    err  "error message" ...
err() {
    echo "$(date +'%b %d %H:%M:%S') ERROR - $*" >&2
}

#============================================================================
# MAIN PROCESSING

# Check that there are any arguments passed to this script.
if [ ${#} -lt 1 ]; then
    err "Insufficient arguments"
    exit 1
fi

# Process the arguments passed to this script. Some arguments are single
# words and some need an additional parameter. See the help information.
while [[ ${#} -gt 0 ]]; do
    case ${1,,} in
        'stop')
            # Write the command and data to the running next file.
            echo -e "export RUN_CMND='stop'\nexport RUN_DATA=''" > "${RUN_NEXT}"
            logging "INFO" "${MYNAME}: STOP requested"
            shift
        ;;

        'restart'|'start')
            # Not much to do here as the running_now file will do the rest.
            cp "${RUN_NOW}" "${RUN_NEXT}"
            logging "INFO" "${MYNAME}: ${1^^} requested"
            shift
        ;;

        'reboot'|'shutdown')
            # Request to reboot the system
            # Terminate the check email program
            ./kill_check_email.sh
            # Turn off all Energenie power sockets
            [ -x ./turn_on_off.py ] && ./turn_on_off.py 0 off

            # We need to kill the current presentation no matter what it is.
            # Possibilities are chromium, pipresents, LibreOffice etc.
            pkill chromium
            pkill soffice
            logging "INFO" "${MYNAME}: ${1^^} requested"
            sync  # Sync all the files
            # Sleep for 5 seconds to get everything synced
            sleep 5
            # Start the reboot/shutdown
            sudo "${1,,}" now
            #err "Doing the ${1^^} as requested"  # DEBUG
            shift  # DEBUG
        ;;

        'run')
            # Run a permanent presentation from the permanent folder
            if [ ${#2} -lt 1 ]; then
                logging "ERROR" "${MYNAME}: RUN cmnd without filename"
                break
            fi
            PERM_FILE="${PERM_FOLDER}/${2}"
            if [ -f "${PERM_FILE}" ]; then
                cp "${PERM_FILE}" "${RUN_NEXT}"
                logging "INFO" "${MYNAME}: RUN ${PERM_FILE} copied to ${RUN_NEXT}"
            else
                logging "ERROR" "${MYNAME}: RUN ${PERM_FILE} does not exist"
                shift 2
                break
            fi
            shift 2
        ;;

        'turn_on'|'turn_off')
            # Get the on or off from the command.
            ON_OFF="${1:5}"

            # Make sure there is another argument
            if [ ${#2} -lt 1 ]; then
                logging "ERROR" \
                    "${MYNAME}: ${1^^} requires another argument"
                break
            fi

            # Test the second argument for being numeric and from 0 to 4 or
            # is missing.
            RE='^[0-9]+$'
            if ! [[ ${2} =~ $RE ]]; then
                err "Screen number is not numeric"
                logging "ERROR" "${MYNAME}: Screen number not numeric"
                shift 1
                break
            elif ! [ ${2} -ge 0 -a ${2} -le 4 ]; then
                err "Screen number not 0-4"
                logging "ERROR" "${MYNAME}: Screen number not 0-4"
                shift 1
                break
            fi
            # Request to turn on the ENERGENIE power socket
            logging "INFO" "${MYNAME}: ${1^^} requested for ${2}"
            #echo "Screen ${2} to be turned ${ON_OFF}"
            [ -x ./turn_on_off.py ] && ./turn_on_off.py "${2}" "${ON_OFF}"
            shift 2
        ;;

        help)
            # Display a help message and exit.
            cat << EOF1
SYNOPSIS
    issue_command.sh command [parameters] [...]

OPTIONS:
    command - One of these are possible:
    stop            Stop the current presentation
    restart         Restart the current presentation
    start           Start the current presentation
    reboot          Reboot the system
    shutdown        Shutdown the whole system
    run filename    Run the filename from the permanent folder
    turn_on N       Turn power socket N on [N=0-4]
    turn_off N      Turn power socket N off [N=0-4]
    help            Display this message
EOF1
            exit 0
        ;;

        *)
            # The argument is not recognised. Display an error message and
            # continue to check the next argument.
            err "Unknown argument: ${1}"
            logging "ERROR" "${MYNAME}: Unknown argument: ${1}"
            shift
        ;;
    esac
done

# If the RUN_NEXT file is present, start the main presentation script.
[ -f "${RUN_NEXT}" ]  &&  ./start_presentation.sh

exit 0
# END OF SCRIPT
