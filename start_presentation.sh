#!/bin/bash
#============================================================================
# NAME        : start_presentation.sh
# DESCRIPTION : Start a presentation as per the running file instructions.
#             : This is part of the "Digital Signage" project.
# SYNOPSIS    : start_presentation.sh [wait] [on] [off]
# AUTHOR      : Gert Bakker
# VERSION     : 1.0
# DATE        : January 2024
# USAGE       : Do not use as an interactive command.
# NOTES       : This script is normally started at boot-up and as and when
#             : a new presentation is to be displayed. The wait argument
#             : provides a sleep time after boot-up for the network to become
#             : stable.
# ---------------------------------------------------------------------------
# Copyright (C) 2023 Gert Bakker, Coleshill,  UK
# All rights reserved.
# Distributed under the GNU general Public License as published by the
# Free Software Foundation, version 3.
# For full text of the license, see the file gnu_licence.txt
#============================================================================

#============================================================================
# Set the working directory.
# Required when auto-starting this script in X windows
cd "${HOME}"/Documents/pi_signage || exit 1
# Get my program name
MYNAME=$(basename "$0")

#============================================================================
# INCLUDED SOURCES
# Include the configuration settings for this project.
. signage.conf
. logging.func

#============================================================================
# Check the arguments and act upon them first.
for arg in "${@}"; do
    #echo $arg
    case "${arg,,}" in
        wait)
            # If argument is "wait", sleep for 10 seconds. This is used when
            # this script is started at boot time to ensure network is up.
            sleep 10
        ;;
        on|off)
            [ -x ./turn_on_off.py ] && ./turn_on_off.py 0 "${arg,,}"
        ;;
    esac
done

#============================================================================
# CONSTANT DEFINITIONS

# Find out which browser to run.
[ -x /usr/bin/chromium ] && BROWSER="chromium"
[ -x /usr/bin/chromium-browser ] && BROWSER="chromium-browser"

# Set the GUI display to use. Need this for running via CRON or from terminal.
export DISPLAY=:0

#============================================================================
# CHECK FOR NEXT RUNNING FILE
# If the file "running_next" is present, move it to become the file to
# use as the "running_now" source-in file.
if [ -f "${RUN_NEXT}" ] ; then
    mv "${RUN_NOW}"  "${RUN_LAST}"  # Keep the last NOW contents.
    mv "${RUN_NEXT}" "${RUN_NOW}"  # Move next to now running file
fi

#============================================================================
# GET THE RUNNING INFO
# Get the information on what to run from the sourced-in file running_now.
if [ -f "${RUN_NOW}" ] ; then
    source "${RUN_NOW}"
else
    logging "ERROR" "${MYNAME}: ${RUN_NOW} file not found"
    exit 1
fi

#============================================================================
# KILL RUNNING PRESENTATION
# We need to kill the current presentation no matter what it is.
# Possibilities are chromium, LibreOffice etc.
pkill chromium
pkill soffice

#============================================================================
# START THE PRESENTATION
#   Depending on what was in the running_now file, start the presentation.
case "${RUN_CMND,,}" in     # Set the variable to all lowercase (,,).

    'google')
        # First remove any previous errors from the chromium Preferences.
        CROM_PREFS="${HOME}/.config/chromium/Default/Preferences"
        sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' "$CROM_PREFS"
        sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' "$CROM_PREFS"

        # Start Chromium browser in Kiosk mode
        ${BROWSER}  --noerrdialogs --incognito --disable-infobars \
                    --kiosk "$RUN_DATA" 2>/dev/null &
    ;;

    'powerpoint'|'impress')
        # First create the two possible locations for the attachment.
        # It could be in attachments or in permanent. Either will do.
        ATCH_FILE="${ATCH_FOLDER}/${RUN_DATA}"
        PERM_FILE="${PERM_FOLDER}/${RUN_DATA}"

        # Test where the PowerPoint file is.
        if [ -f "${ATCH_FILE}" ]; then  # Is it in attachments?
            PWR_FILE="${ATCH_FILE}"
            touch "${ATCH_FILE}"
        elif [ -f "${PERM_FILE}" ]; then  # Is it in permanent?
            PWR_FILE="${PERM_FILE}"
        else
            # The file does not exist in either directory. Exit.
            logging "ERROR" "${MYNAME}: Attachment not found: ${RUN_DATA}"
            exit
        fi

        # Start the PowerPoint presentation using LibreOffice.
        # NOTE: the norestore option is needed to ignore restore messages.
        libreoffice  --norestore  "${PWR_FILE}"  2>/dev/null &
    ;;

    'stop'|'halt')
        # Kill the presentation. As this has already been done, just copy
        # the last running file to the now running file, so that a restart
        # request will restart what was running last time.
        cp  "${RUN_LAST}"  "${RUN_NOW}"
    ;;

    * )
        logging "ERROR" "${MYNAME}: Unknown running type: ${RUN_CMND}"
    ;;
esac

# End of script
exit 0