#!/bin/bash
#============================================================================
# NAME        : kill_check_email.sh
# DESCRIPTION : Kill the check_email program
# SYNOPSIS    : kill_check_email.sh
# AUTHOR      : Gert Bakker, Coleshill, UK
# DATE        : January 2024
# VERSION     : 1.0
# USAGE       : Use this in CRON to stop the check_email program.
# NOTES       : Use to terminate the background program that checks
#             : for unread emails
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
# Get my program name (Currently unused, Keep for future use)
# MYNAME=$(basename "$0")

#============================================================================
# INCLUDED SOURCES
.  signage.conf  # Configuration settings for this project.

#============================================================================
# CONSTANT DEFINITIONS
# Set the name of the program to be killed.
PROGRAM_NAME='check_read_email.py'

#============================================================================
# MAIN PROCESSING

# Send the SIGINT signal to the Python program.
pkill -2 -f ${PROGRAM_NAME}

exit
# END OF SCRIPT
