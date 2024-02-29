#!/bin/bash
#============================================================================
# NAME        : sysadmin_update.sh
# DESCRIPTION : Perform the update requested
#             : This is part of the "Digital Signage" project.
# SYNOPSIS    : sysadmin_update.sh  data_string  attachment_name
# AUTHOR      : Gert Bakker, Coleshill, UK
# DATE        : January 2024
# VERSION     : 1.0
# USAGE       : Script is started by the sysadmin_tasks.sh script.
# NOTES       : This script replaces a system file with a new version that is
#             : provided as the attachment.
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
EMAIL_DATA=/tmp/sign_list_$$  # Email message file.
EMAIL_SUBJ="Sysadmin Update status"

# Directories to be changed in the file to ensure production folder is used.
# The construct below is to avoid the SED in the installation script changing
# them! NOLI ME TANGERE! (Touch me not!)
OLD_DIR='Documents/'
OLD_DIR+='pi_signage'
NEW_DIR='Production/'
NEW_DIR+='pi_signage'

#============================================================================
# MAIN PROCESSING

${MY_DEBUG} "===== Started ${MYNAME}"

if [ ${#} -lt 2 ]; then
    logging "ERROR" "${MYNAME}: Insufficient arguments supplied"
    exit 1
fi

${MY_DEBUG} "DATA= ${1}"
${MY_DEBUG} "ATCH= ${2}"

if [ -f "${1}" ]; then
    if [ -f "${ATCH_FOLDER}/${2}" ] ; then
        # Get the file permissions of the original file
        CHMOD=$(stat -c "%a" "${1}")
        # Move the attachment to the file to be replaced
        mv "${ATCH_FOLDER}/${2}" "${1}"
        # Just to make sure, convert the text in the file to UNIX format
        dos2unix "${1}" 2>/dev/null
        # Ensure production folder name is in the file
        sed -i "s,${OLD_DIR},${NEW_DIR},g" "${1}"
        # Restore the file permissions of the original file
        chmod "${CHMOD}" "${1}"
        logging "INFO" "${MYNAME}: Replacing file ${1}"
        echo -e "\nUPDATE: Replaced file ${1}" >> ${EMAIL_DATA}
    else
        logging "ERROR" "${MYNAME}: Attachment not found!"
        echo -e "\nUPDATE: Attachment ${2} not found!" >> ${EMAIL_DATA}
    fi
else
    logging "ERROR" "${MYNAME}: File \"${1}\" does not exist!"
    echo -e "\nUPDATE: File - ${1} - does not exist!" >> ${EMAIL_DATA}
fi

if [ -s "${EMAIL_DATA}" ]; then
    echo -e "\nRegards\nDigital Signage" >> ${EMAIL_DATA}
    send_email_now  "${SA_EMAIL_TO}"  "${EMAIL_SUBJ}"  "${EMAIL_DATA}"
fi

exit 0
# END OF SCRIPT