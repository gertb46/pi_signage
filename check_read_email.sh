#!/bin/bash
#============================================================================
# NAME        : check_read_email.sh
# DESCRIPTION : Start the Python program "check_read_email.py" if it is not
#             : already active.
#             : This is part of the "Church Digital Signage" project.
# SYNOPSIS    : check_read_email.sh
# AUTHOR      : Gert Bakker, Coleshill, UK
# DATE        : January 2024
# VERSION     : 1.0
# USAGE       : Use in CRON only.
# NOTES       : The email checking is done with a Python program that at
#             : regular intervals (30 or so secs) tests for emails.
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

#============================================================================
# Before continuing, check that the program is not already running.
LOCK_NAME='check_read_email.py'  # Name of the program to check
# If the program is already running, exit the script with code 80.
pgrep -f ${LOCK_NAME} >/dev/null && { exit 80 ; }

#============================================================================
# INCLUDED SOURCES
.  signage.conf  # Configuration settings for this project.

#============================================================================
# MAIN PROCESSING

# Run the python program in background as the script is now no longer needed.
# Added the capture of the STDERR messages.
# date >>check_email.stderr - 2>>check_email.stderr  #
( ./check_read_email.py & )  2>/dev/null

exit 0
# END OF SCRIPT
