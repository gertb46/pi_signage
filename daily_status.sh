#!/bin/bash
#============================================================================
# NAME        : daily_status.sh
# DESCRIPTION : Daily status email for System Administrator
#             : This is part of the "Digital Signage" project.
# SYNOPSIS    : daily_status.sh
# SEE ALSO    : ~/bin/syslogquick.sh -- Syslog entries
#             : ~/bin/src/syslogcheck.conf -- Syslog configuration elements
# AUTHOR      : Gert Bakker, Coleshill, UK
# DATE        : January 2024
# VERSION     : 1.0
# USAGE       : Run with a CRON entry once a day
# NOTES       : This script must be run daily to remove expired files and to
#             : provide an email message to the System Administrator with the
#             : latest status information.
#             : This log file will be cleared once the email has been sent.
#             : This script optionally uses the syslogquick.sh utility to scan
#             : for the syslog entries for yesterday and today.
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
MYNAME=$(basename "$0")

#============================================================================
# INCLUDED SOURCES
.  signage.conf  # Configuration settings for this project.
.  logging.func  # Logging function definition
.  send_email.func  # Include the send_email functions.

#============================================================================
# FUNCTION Definitions
# Function to delete the files that are due to be removed.
deletefiles() {
    for str in "$@"; do
        #echo Deleting ${str}
        # Delete the file and log to the logging message file.
        rm -f "${str}"
        logging "INFO" "${MYNAME}: File deleted: ${str}"
    done
}

#============================================================================
# VARIABLE DEFINITIONS
EMAILMSG=/tmp/sign_status1$$  # Email message file.
# SYSLOG MESSAGES. File to get the syslog messages of interest into.
MY_SYSMSG=/tmp/sign_status2$$  # File to get the syslogquick.sh messages.

# CLEAN_UP. List of the temp files to be deleted when this script ends.
FILES2DELETE="${EMAILMSG} ${MY_SYSMSG}"

# Email Subject line.
EMAIL_SUBJ="System status for $(uname -n) at $(date +"%a %d %b %H:%M")"

#============================================================================
# MAIN PROCESSING

# DELETE EXPIRED FILES
# Get the list of files for deleting in the attachment folder
FILES=$(find ${ATCH_FOLDER} -iname '*' -type f -mtime ${FDEL_ATCH} -print)
deletefiles ${FILES}

# Get the list of files for deleting in the unqueue folder
FILES=$(find ${UNQUEUE_DIR} -iname '*' -type f -mtime ${FDEL_UNQU} -print)
deletefiles ${FILES}

# Get the list of files for deleting in the other_msg folder
FILES=$(find ${OTHR_FOLDER} -iname '*' -type f -mtime ${FDEL_OTHR} -print)
deletefiles ${FILES}

# GENERATE THE STATUS EMAIL
# Collect the system status information
MY_UPSINCE=$(uptime -s)

# CPU TEMPERATURE. Get the CPU temperature.
# If vcgencmd is present, use that command to get the CPU temperature.
if [ -x "/usr/bin/vcgencmd" ]; then
    MY_CPU_TEMP=$(vcgencmd measure_temp | cut -d= -f2 | cut -d. -f1)
else
    # Possibly not Raspberry Pi, so use Linux command.
    MY_CPU_TEMP=$(sensors | grep 'temp1:' | xargs | cut -d' ' -f2)
fi

# Collect the disk usage percentage.
FS_USAGE=$(df -PTh | grep -E -iw "ext4|ext3|xfs|gfs|gfs2|btrfs" \
           | sort -k6n | awk '!seen[$1]++')
MY_DISK_USAGE=$(echo "$FS_USAGE" | awk '{print $1, $6}')

# Generate the status message.
{
    echo -e "\nUp since:  ${MY_UPSINCE}"  # UPTIME.
    echo -e "CPU Temp:  ${MY_CPU_TEMP}"  # CPU TEMPEATURE
    echo -e "Disk status:  ${MY_DISK_USAGE}"  # DISK usage
    echo -e "\n===== Other email messages in ${OTHR_FOLDER}"
    ls -l "${OTHR_FOLDER}"  # List files in the other_mesg folder.
} >> ${EMAILMSG}

# SYSLOG ENTRIES.
# Only do this if the syslogquick.sh script is installed in the ~/bin folder.
# Find the SYSLOG messages of interest (using a preset search string) and
# include these into the email message.
if [ -x ~/bin/syslogquick.sh ] ; then
    echo -e "\n===== Syslog entries"  >> ${EMAILMSG}
    ~/bin/syslogquick.sh  > ${MY_SYSMSG}  # Create the syslog message file.
    if [ -s "${MY_SYSMSG}" ] ; then     # Check if any messages were found
        # Copy the syslog essages to the email message
        cat ${MY_SYSMSG}        >> ${EMAILMSG}
    else
        # No syslog messages found. Put notification in.
        echo -e "No entries were found"     >> ${EMAILMSG}
    fi
fi

# Logging messages to be added to the email message.
if [ -s "${PI_SIGN_LOG}" ]; then
    echo -e "\n===== Logging messages"  >> ${EMAILMSG}
    cat "${PI_SIGN_LOG}"    >> ${EMAILMSG}
    rm -f "${PI_SIGN_LOG}"  # Remove the logging file
fi
rm -f "${PI_SIGN_LOG}"  # Always delete the logging file
touch "${PI_SIGN_LOG}"  # and create an empty one.
logging "INFO" "${MYNAME}: Restarted logging file"

# Email the message using the send_email process
send_email_now  "${SA_EMAIL_TO}"  "${EMAIL_SUBJ}"  "${EMAILMSG}"

# Cleaning up after the status message has been emailed if required
rm -f "${FILES2DELETE}"
exit 0
# END OF SCRIPT
