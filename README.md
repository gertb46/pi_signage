# pi_signage - A Digital Signage facility managed using email

## Introduction
A Digital Signage facility, as implemented by this project, is one that displays a slide presentation on screens in a church or other environment.
The presentation can be created using various methods and is managed using emails.
It is designed to be simple to set-up, maintain and to create presentations for.
It is intended to be used where a simple informational display is all that is needed.

## Project goals
  * Keep the overall cost to an absolute minimum by utilising low cost equipment, free software, free email services, existing facilities, etc.
  * Use internet and email to deliver presentations and manage the system.
  * Keep maintaining and updating the system and the presentations as simple as possible.
  * System Administrator to receive a daily status message to deal with potential problems.
  * Provide security whereby only authorised email addresses can send instructions to the system.

## Implementation
This project (it) is intended to run on a Raspberry Pi running Linux (Debian) and using existing video facilities.
The Raspberry Pi is a small device that can be easily located anywhere to provide this facility.
It can also run on any Linux machine.

It consists of a set of BASH shell scripts, Python programs and some data and configuration files.

It relies on "*start-up*" (e.g. the LXDI *autostart*) configurations and *CRON* to start and stop presentations, read and send emails, do regular maintenance, etc.
These CRON entries are very much dependent on where and for what purpose this project is implemented.

The Python module "*dotenv*" is used to access the secret information.

A main configuration file is used to allow for customisation of this project.

To allow remote turning on and off of the screen(s), this project uses the ENERGENiE remote power sockets for Raspberry Pi.
This feature is optional and purchase information is in the documentation.

Language changes can be done in the Python programs. The error and information messages and command words are grouped for easy translation to a preferred language.

## Start the project
To start this project, download the compressed file to a Raspberry Pi or a device that is running Linux.

Extract the contents into a *working* folder.
It is recommended to create **~/Documents/pi_signage** as the working folder.

The working folder is where the project is configured and tested before being put into production.
Only make changes to the files in the working folder and never those in the production folder.
A "*Makefile*" is available to copy the files to the production folder once it is all running properly.

Now read the **System Documentation** and the **User Manual** to understand what this project is about, how it works and how to install it.

## Installation
To install the system, follow the instructions in **Appendix D** of the *System Documentation*.
Follow the steps in the order they are listed in the appendix.

The project **<u>does</u>** require a number of Python modules and Linux utilities to be installed.
These are in addition to what is installed with the current version of the Raspberry Pi operating system.
If the implementation is not using a Raspberry Pi, check that all utilities used by the project are available on the Linux device.

There is "*PYDOC*" generated documentation for each of the Python programs.
There is a PDF document with "*man*" pages for the Shell scripts, the configuration and the common function files.
There is also an index of which script/program is used in which other script/program.
The latter is for reference only.

Complete the installation steps and the project will be ready for testing.

## Testing
It is recommended that during testing the <u>DEBUG</u> flag is set to *True* in the *dotenv* secrets file.
This will write debug messages to the main log file "*pi_signage.log*".
The debug messages will be very useful in finding out what went right, what went wrong and where.

The first thing to do is to ensure that the email service is working properly.
Execute the script "**check_read_email.sh**".
This script will start in background the Python program that checks for and reads the emails.
Check the debug messages to make sure the program works.

Create a test presentation as described in the "*User Manual*" and email the relevant presentation command to the system.

If the email message with the test presentation information was received and processed correctly, the presentation will start automatically.

Use the "*issue_command.sh*" script to issue commands to perform a set of functions that tests the system.
See the documentation on how to use this script.

Test all the possible emailed commands to ensure everything is working properly.

## User instructions
The user instructions are in the **User Manual**.

There are two roles defined for this project.

The first is the *presentation creator*.
This role creates and manages the actual presentation that is the purpose of this project.

The second role is the *System Administrator*.
This is a more technical role and ideally performed by whomever implemented this project.
It is kept as simple as possible with minimal direct interaction with the device itself.
It will require SSH or VNC access to the device to allow direct access.
There is a command implemented that allows the updating of scripts and programs simply by
emailing a new version to the device.
Only existing files can be updated this way.
Crontab entries can also be updated by emailing a new version of the crontab.

## Operating System upgrades
A script is available to do automatic upgrading of the operating system.
The script name is called **auto_update.sh**.
It is not officially part of this project.
It was deemed to be of use since the project is assumed to be working headless and operator-less.
It is provided on an as-is basis as it is not necessarily complete.
*Use with caution!*

## Future
Anyone using these scripts and programs will no doubt come up with new ideas.
The author is open to any suggestions to improve this project.

## LICENSE
### Copyright
Project name: pi_signage - The Digital Signage project.

Copyright © 2023, Gert Bakker, Coleshill, UK. All right reserved.

### GNU licence
Digital Signage is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.

Digital Signage is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this project. If not, see <https://www.gnu.org/licenses/>.

All copyrights and trademarks mentioned in all documents and files making up this Digital Signage project are acknowledged.
