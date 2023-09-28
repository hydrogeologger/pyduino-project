#!/bin/bash

# Use this file as a template but make your own copy of it.
# For files to be using crontab to schedule to run at specific times.
# You do not require sleep.


# sleep 23 # Only required if script is to be executed at boot time
#su pi

PROJECT_DIR=/home/pi/pyduino-project/mdba/ewatering_2023

cd "$PROJECT_DIR" || { echo "Unable to enter $PROJECT_DIR"; exit 2; }

# Run the python in unbuffered mode
/usr/bin/stdbuf -i0 -oL -eL python -u station.py >> log_ewatering.log 2>&1
