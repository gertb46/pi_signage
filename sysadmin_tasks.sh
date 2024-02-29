#!/bin/bash
#============================================================================
# NAME        : sysadmin_task.sh
# DESCRIPTION : Perform the System Administration tasks for this project.
#             : This is part of the "Digital Signage" project.
# SYNOPSIS    : sysadmin_task.sh
# AUTHOR      : Gert Bakker, Coleshill, UK
# DATE        : January 2024
# VERSION     : 1.0
# USAGE       : Run this script when SysAdmin requests have been received
# NOTES       : This script will interpret the SysAdmin commands that have
#             : been emailed to the system.
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
# Include the configuration settings for this project.
. signage.conf
. logging.func
. send_email.func

#============================================================================
# CONSTANT DEFINITIONS
# Debug statements. Messages depend on the dotenv DEBUG value.
MY_DEBUG='logging DEBUG'  # For debug messages

# Email message constants
EMAIL_DATA=/tmp/sign_task_$$  # Email message file.

#============================================================================
# MAIN PROCESSING

# Check that we have a "manage_next" file before we source it in.
if [ -f "${RUN_ADM}" ]; then
    . ${RUN_ADM}
else
    logging "INFO" "${MYNAME}: ${RUN_ADM} file not found"
    exit 0
fi

# Setup the email subject line
EMAIL_SUBJ="Sysadmin result for ${RUN_CMND^^}"

# Read the variables and depending on what the command is, take the action
${MY_DEBUG} "===== Started ${MYNAME}"
case ${RUN_CMND,,} in
    'list')
        # List command requesting a directory listing to be send by email.
        logging "INFO" "${MYNAME}: List requested"
        ./sysadmin_list.sh  "${RUN_DATA}"
    ;;

    'update')
        # Update by replacing an existing file with a new one found as an
        # attachment to the email requesting it.
        logging "INFO" "${MYNAME}: Update requested ${RUN_DATA}, ${RUN_ATCH}"
        ./sysadmin_update.sh  "${RUN_DATA}"  "${RUN_ATCH}"
    ;;

    'reboot'|'shutdown')
        # Request to reboot the system.
        ./kill_check_email.sh  # Kill the check_email program.
        ./issue_command.sh stop  # Stop any running presentation.
        # Turn off all Energenie sockets.
        [ -x ./turn_on_off.py ] && ./turn_on_off.py 0 off
        rm -f ${RUN_ADM}  # Remove the trigger file
        sync  # Sync up all the files.
        sleep 10 # Just so things are happening
        logging "INFO" "${MYNAME}: ${RUN_CMND^^} requested"
        sudo ${RUN_CMND,,} now
    ;;

    'screen')
        # Request to turn screen 0-4 on or off.
        # The data should contain the socket number and the word on or off.
        # First get the data into an array.
        IFS=', ' read -r -a array <<< "${RUN_DATA}"
        # If the turn_on_off program exists execute the program with the data.
        [ -x ./turn_on_off.py ] && ./turn_on_off.py "${array[0]}" "${array[1]}"
        if [ $? == 0 ]; then  # If the program exists and returns OK, log msg.
            logging "INFO" "${MYNAME}: Screen ${array[0]} ${array[1]} requested"
        fi
    ;;

    'save_now')
        # Saving the running_now to a permanent file and with any attachments.
        # This saving is done with a Python program as that is more efficient.
        ./sysadmin_save_now.py "${RUN_DATA}"
        # Depending on outcome, email a status message.
        if [ $? == 0 ]; then
            echo -e "SAVENOW: Updated ${RUN_DATA}" >> ${EMAIL_DATA}
        else
            echo -e "SAVENOW: Could not replace ${RUN_DATA}" >> ${EMAIL_DATA}
        fi
    ;;

    'crontab')
        # Replace the crontab with a new version given as an attachment.
        # Any errors, ignore the cron update.
        if [ -f "${ATCH_FOLDER}/${RUN_ATCH}" ]; then
            # The attachment file has been found.
            # Ensure that the attachment is in LINUX text format.
            dos2unix "${ATCH_FOLDER}/${RUN_ATCH}" 2>/dev/null
            # Replace the crontab with the new version.
            crontab "${ATCH_FOLDER}/${RUN_ATCH}"
            if [ $? == 0 ]; then
                # Crontab was updated with a new version.
                logging "INFO" "${MYNAME}: Crontab replaced by: ${RUN_ATCH}"
                echo -e "\nCRONTAB: Crontab Replaced by: ${RUN_ATCH}" \
                        >> ${EMAIL_DATA}
            else
                # There was an error doing the update.
                logging "ERROR" "${MYNAME}: Crontab replace failed"
                echo -e "\nCRONTAB: Crontab update failed: ${RUN_ATCH}" \
                        >> ${EMAIL_DATA}
            fi
        else
            # The attachment was not found. This should not really happen.
            # but is here for completeness.
            logging "ERROR" "${MYNAME}: New crontab: ${RUN_ATCH} - not found!"
            echo -e "ERROR: Crontab: ${RUN_ATCH} - not found!" >> ${EMAIL_DATA}
        fi
    ;;

    'download')
        # Email a file as an attachment to the SysAdmin
        logging "INFO" "${MYNAME}: Download requested"
        ./sysadmin_download.sh "${RUN_DATA}"
    ;;

    'delete')
        # Delete a file in the permanent folder.
        logging "INFO" "${MYNAME}: Delete requested"
        # Get the filenames into an array
        IFS=', ' read -r -a ARRAY <<< "${RUN_DATA}"

        for FILENAME in "${ARRAY[@]}"
        do
            # Generate the path to the file to be deleted.
            FNAME=$(basename ${FILENAME})
            FULL_PATH="${PERM_FOLDER}/${FNAME}"
            # If the file exists, delete it.
            if [ -f "${FULL_PATH}" ]; then
                rm -f "${FULL_PATH}"
                logging "INFO" "${MYNAME}: Deleted file: ${FILENAME}"
                echo -e "\nDELETE: Deleted file: ${FILENAME}" \
                        >> ${EMAIL_DATA}
            else
                # File does not exist
                logging "ERROR" "${MYNAME}: File not found: ${FILENAME}"
                echo -e "\nDELETE: File not found: ${FILENAME}" \
                        >> ${EMAIL_DATA}
            fi
        done
    ;;

    *)
        logging "ERROR" "${MYNAME}: Unknown sysadmin command: $1"
    ;;
esac

# Once used, remove the manage_next file.
rm -f ${RUN_ADM}

# If there were any messages in the email data file, email it now
if [ -s "${EMAIL_DATA}" ]; then
    echo -e "\nRegards\nDigital Signage" >> ${EMAIL_DATA}
    send_email_now  "${SA_EMAIL_TO}"  "${EMAIL_SUBJ}"  "${EMAIL_DATA}"
fi

exit 0
# END OF SCRIPT
