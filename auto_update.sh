#!/bin/bash
#============================================================================
# NAME        : auto_update.sh
# DESCRIPTION : Unattended update of the operating system
# SYNOPSIS    : auto_update.sh
# AUTHOR      : Gert Bakker, Coleshill, UK
# DATE        : February 2024
# VERSION     : 1.0
# USAGE       : Use with CRON for user "pi"
# NOTES       : Check for Patches and Updates and if found, apply the
#             : updates. Reboot may be required.
#============================================================================

#============================================================================
# CONSTANT DEFINITIONS
# Setup the logger command and the files to get the update messages in.
LOGGER='logger -t AUTOUPDATE --'
AVAIL='avail.txt'
UPDATE='update.txt'
UPGRADE='upgrade.txt'

#============================================================================
# FUNCTION DEFINITIONS
#   Logging message function that logs a message into the SYSLOG
#   use as:    err  "error message" ...
logging() {
    ${LOGGER} $@
}

#============================================================================
# MAIN PROCESSING

# If not already there, create the folder for the messages that "apt" produces
mkdir -p ~/auto_update
# Make it our working directory
cd ~/auto_update || exit 1

logging "INFO: $(basename $0) started"

# Get updates to the list
sudo apt update -y > ${UPDATE} 2>/dev/null

# Get the list of upgradeable components
apt list --upgradeable > ${AVAIL} 2>/dev/null

# Check the number of lines in the available list and if more than 1 line,
# there are updates to apply
if [ -f ${AVAIL} ]; then
    # Count the number of lines in the available file
    count=`wc -l ${AVAIL} | cut -d' ' -f1`
    # If only one line, then there are no updates to be done.
    if (( $count < 2 )); then
        logging "INFO: No updates found."
    else
        # TODO: This may need to be changed. Depends on experience gained.
        logging "INFO: Updates found"
        # Apply the updates
        sudo apt upgrade -y  > ${UPGRADE} 2>/dev/null
        #sudo apt full-upgrade -y  >> ${UPGRADE}  2>/dev/null
        echo '--' >> ${UPGRADE}
        sudo apt autoremove -y  >> ${UPGRADE}  2>/dev/null
        echo '--' >> ${UPGRADE}
        sudo apt clean -y  >> ${UPGRADE}  2>/dev/null
        #sudo reboot now  # Not always required.
    fi
fi

logging "INFO: $(basename $0) finished"
exit 0
# END OF script
