#!/bin/bash
#============================================================================
# NAME        : send_email.sh
# DESCRIPTION : Send emails that are in an RFC 5322 formatted message file.
#             : This is part of the "Church Digital Signage" project.
# SYNOPSIS    : send_email.sh [message_file] [...]
# EXIT CODE   : 0 - All OK. No other return codes.
# AUTHOR      : Gert Bakker, Coleshill, UK
# DATE        : January 2024
# VERSION     : 1.0
# USAGE       : CRON for regular sending of queued files or specific file to
#             : be send now or as a command with arguments.
# NOTES       : This script is to be run by any script that wants to
#             : send an email message.
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

#============================================================================
# CONSTANT DEFINITIONS
# Debug statements. Messages depend on the dotenv DEBUG value.
MY_DEBUG='logging DEBUG'

#============================================================================
# MAIN PROCESSING
${MY_DEBUG} "===== ${MYNAME}"  # Just a divider line in debug messages.

# If there are arguments, then those are the messages to be emailed.
# If no arguments, then use all files in the 'queue' directory.
if [ ${#} -gt 0 ]; then
    # Arguments found so use these as messages to email
    ${MY_DEBUG} "Arguments ${#}"
    FILES=${@}  # Get all message file names
else
    # No argument found, so we get the message files that are in the queue
    # directory instead.
    ${MY_DEBUG} "No Arguments, checking queue directory"
    FILES=$(find "${QUEUE_DIR}" -maxdepth 1  -type f)
    # Check if there are any messages in the email queue directory.
    if [[ -z "${FILES}" ]]; then
        #   No files found, just exit as this is OK
        ${MY_DEBUG}  "No files found"
        exit 0
    fi
    ${MY_DEBUG}  "There are queued files to email"
fi

./send_email.py  ${FILES}
if [ $? != 0 ]; then
    logging "INFO" "${MYNAME}: send_email.py outcome $?"
fi


exit 0
# END OF SCRIPT
