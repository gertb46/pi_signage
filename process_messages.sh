#!/bin/bash
#============================================================================
# NAME        : process_messages.sh
# DESCRIPTION : Process the messages stored in the messages folder.
#             : This is part of the "Digital Signage" project.
# SYNOPSIS    : process_messages.sh
# AUTHOR      : Gert Bakker, Coleshill, UK
# DATE        : January 2024
# VERSION     : 1.0
# USAGE       : This script is started by the check_read_email.py program.
# NOTES       : This script processes the read email messages that have been
#             : stored in the messages folder.
#             : It then starts the scripts for SysAdmin and Presentations.
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
# Get my program name (Currently unused. Keep for future use)
MYNAME=$(basename "$0") # Not used in this script. Keep for future use.

#============================================================================
# INCLUDED SOURCES
. signage.conf
. logging.func

#============================================================================
# VARIABLE DEFINITIONS
# MY_DEBUG statement.
MY_DEBUG='logging DEBUG'

#============================================================================
# MAIN PROCESSING

${MY_DEBUG} "===== Started ${MYNAME}"

# Process the email messages
./process_messages.py

# Start the system admin manager if the manage_next file is found.
if [ -s "$RUN_ADM" ]; then
    ${MY_DEBUG} "System Admin file found: ${RUN_ADM}"
    # cp ${RUN_ADM}  manage_saved  # For testing
    ./sysadmin_tasks.sh
fi

# Start the presentation if the running_next file if found.
if [ -s "$RUN_NEXT" ]; then
    ${MY_DEBUG}  "Starting next presentation! Please wait..."
    # Start the presentation in background. Suppress the error messages.
    ( ./start_presentation.sh  & ) 2>/dev/null
fi

exit 0
# END OF SCRIPT
