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
This project is intended to run on a Raspberry Pi running Linux (Debian) and using existing video facilities. 
The Raspberry Pi is a small device that can be easily located anywhere to provide the Digital Signage facility. 
This project can also run on any Linux machine.

This project consists of a set of BASH shell scripts, Python programs and data and configuration files.

It relies on CRON to start, stop presentations, read and send emails, do regular maintenance, etc. 
This is very much dependent on where this project is implemented.

Configuration files, such as "dotenv" and main configuration data, are used to allow customisation of this project.

Language changes can be done in the Python programs. The error and information messages and command words are grouped for easy translation to a preferred language.

## Start the project
To start implementing this project, download the ZIP file to a computer that is running Linux. 
Extract the contents into a *working* folder. This folder is where the project is configured and tested before being put into production. A MAKE file is available to copy the files to the production folder.

Before doing anything, read the **System Documentation** and the **User Manual** to understand what this project is about, how it works and how to install it. 
It explains the command structure to use in the email body.

An email address will need to be set-up for the device. This is where the instructions are emailed to and where emails are send from. The project has a Python program running in background that will check the INBOX regularly for emails.

## Installation
To install the system, please read the "**System Documentation**" that is in the *documentation* folder.
Follow the instructions in Appendix D. 
It is not difficult to do for anyone with Linux experience.

The system <u>does</u> require a number of Python modules and Linux utilities to be installed. 
All this is described in the document.

There is also documentation for the Python programs, the Shell scripts (man pages) and for the configuration and common function files. These documents are all in the *documentation* folder. It is strongly advised to check these documents out.

## User instructions
The user instructions are in the **User Manual**.

There are two roles defined for this project. 

The first is the *presentation creator*.
This role creates and manages the actual presentation that is the purpose of this project.

The second role is the *System Administrator*. 
This is a more technical role and ideally performed by the one that implemented this project. 
It is kept as simple as possible with minimal direct interaction with the target device.
It may require SSH or VNC access to the device if required.

## LICENSE
Copyright (C) 2023 Gert Bakker, Coleshill,  UK

This file is part of the **pi_signage** Digital Signage project.

pi_signage is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by the
Free Software Foundation, version 3.

pi_signage is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <[https://www.gnu.org/licenses/](https://www.gnu.org/licenses/)>.

