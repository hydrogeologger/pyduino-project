#!/bin/bash

# Use this file as a template but make your own copy of it.
# i.e. `cp run_template.sh /own_directory/run_file.sh`
# For files to be using crontab to schedule to run at specific times.
# You do not require sleep.
# Remember to make own file executable i.e. `chmod 755 run_once.sh`

# Sleep is only required if script is to be executed at boot time
# using python loop.
# sleep 23 # Uncomment this line if using python loop and NOT crontab
# su pi

PROJECT_NAME="project_name"
PROJECT_DIR="/home/pi/pyduino-project/project_directory"

cd "$PROJECT_DIR" || { echo "Unable to enter $PROJECT_DIR"; exit 2; }

# Run the python in unbuffered mode
/usr/bin/stdbuf -i0 -oL -eL python -u station.py >> "log_$PROJECT_NAME.log" 2>&1
