#!/bin/bash
#============================================================================
# NAME        : sysadmin_list.sh
# DESCRIPTION : Perform the list of directory as requested
#             : This is part of the "Digital Signage" project.
# SYNOPSIS    : sysadmin_list.sh  data_string
# AUTHOR      : Gert Bakker, Coleshill, UK
# DATE        : January 2024
# VERSION     : 1.0
# USAGE       : Script is started by the sysadmin_tasks.sh script.
# NOTES       : Emails a list of the folders mentioned in the command line.
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
MY_DEBUG='logging DEBUG'

# Email message constants
EMAIL_DATA=/tmp/sign_list_$$    # Email message file.
EMAIL_SUBJ="Directory listing from $(uname -n)"

#============================================================================
# MAIN PROCESSING

${MY_DEBUG} "===== Started ${MYNAME}"

# Check that we have an argument
if [ ${#} -lt 1 ]; then
    logging "ERROR" "${MYNAME}: list command: Insufficient arguments supplied"
    exit 1
fi

${MY_DEBUG} "DATA= ${@}"

# Get the arguments into a string
IFS=', ' read -r -a array <<< "${@}"

for dirname in ${array[@]}
do
    if [ -d "${dirname}" ]; then
        # This is for starting or continuing the message to ensure there is
        # a blank line between different directories.
        if [ -s "${dirname}" ]; then
            # Message file is not empty so add a blank line at the start
            echo -e "\n===== Directory: ${dirname} =====" >> ${EMAIL_DATA}
        else
            # Message file is empty so no additional blank line at the start
            echo -e "===== Directory: ${dirname} =====" > ${EMAIL_DATA}
        fi
        ls --group-directories-first -lh "${dirname}"  >> ${EMAIL_DATA}
    else
        logging "ERROR" "${MYNAME}: List requested for unknown dir: ${dirname}"
        # Add error message to the email.
        echo -e "\nERROR: Folder not known: ${dirname} \n"  >> ${EMAIL_DATA}
    fi

done

if [ -s "${EMAIL_DATA}" ]; then
    echo -e "\nRegards\nDigital Signage" >> ${EMAIL_DATA}
    send_email_now  "${SA_EMAIL_TO}"  "${EMAIL_SUBJ}"  "${EMAIL_DATA}"
fi


