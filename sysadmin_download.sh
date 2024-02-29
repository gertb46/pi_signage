#!/bin/bash
#============================================================================
# NAME        : sysadmin_download.sh
# DESCRIPTION : Email any file as an attachment to the SysAdmin
#             : This is part of the "Digital Signage" project.
# SYNOPSIS    : sysadmin_download.sh  file_to_attach
# AUTHOR      : Gert Bakker, Coleshill, UK
# DATE        : January 2024
# VERSION     : 1.0
# USAGE       : Called by the SysAdmin task script
# NOTES       : This script sends a file as an attachment to the SysAdmin
#             : email address,
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
MY_DEBUG='logging DEBUG'   # For debug messages

# Email message constants
EMAIL_DATA=/tmp/sign_list_$$  # Email message file.
EMAIL_SUBJ="Download of file ${1}"

# Setup the email message
( cat <<EOM
Attached is the requested file: ${1}

Regards
Digitial Signage System
EOM
) > "${EMAIL_DATA}"

#============================================================================
# MAIN PROCESSING

case ${1,,} in
    'crontab')
        # This is a special case for downloading the crontab.
        # Get the crontab entries into a file
        crontab -l >crontab.txt
        send_email_now  "${SA_EMAIL_TO}"  "${EMAIL_SUBJ}"  \
                        "${EMAIL_DATA}"   "crontab.txt"
        logging "INFO" "${MYNAME}: Crontab emailed"
        ;;
    *)
        # All other files.
        if [ -f "${1}" ]; then
            send_email_now  "${SA_EMAIL_TO}"  "${EMAIL_SUBJ}"  \
                            "${EMAIL_DATA}"  "${1}"
            logging "INFO" "${MYNAME}: File emailed: ${1}"
        else
            logging "ERROR" "${MYNAME}: File not found: ${1}"
        fi
        ;;
esac

exit 0
# END OF SCRIPT