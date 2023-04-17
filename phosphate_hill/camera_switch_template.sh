#!/bin/bash

# Please make own copy of this file to execute and remove sections as required

######### ------ CONFIGURATION ------- #######

# Start and end time in 24 hour (hh:mm) time format
START_TIME="07:45"
END_TIME="16:15"

# Power PIN Configuration
CAMERA_1_RPI_BCM_PIN=5
CAMERA_2_RPI_BCM_PIN=6


######### ------ Schedule Check ------- #######

# Only allow program to run within certain time
current_time=$(/usr/bin/date +"%H:%M")
if [[ $current_time < $START_TIME ]] || [[ $current_time > $END_TIME ]]; then
    exit 0
fi


######### ------ For switching on ------- #######
/usr/local/bin/gpio -g mode $CAMERA_1_RPI_BCM_PIN out
/usr/local/bin/gpio -g write $CAMERA_1_RPI_BCM_PIN 1

/usr/local/bin/gpio -g mode $CAMERA_2_RPI_BCM_PIN out
/usr/local/bin/gpio -g write $CAMERA_2_RPI_BCM_PIN 1


######### ----- SHUTDOWN SEQUENCE ------ ########

## For initiating shutdown sequence and turning off
ssh pi@phosphatehill-camera-#.local "sudo shutdown now"
ssh pi@phosphatehill-camera-#.local "sudo shutdown now"

sleep 120 # Give enough time for shutdown to complete

/usr/local/bin/gpio -g mode $CAMERA_1_RPI_BCM_PIN out
/usr/local/bin/gpio -g write $CAMERA_1_RPI_BCM_PIN 0

/usr/local/bin/gpio -g mode $CAMERA_2_RPI_BCM_PIN out
/usr/local/bin/gpio -g write $CAMERA_2_RPI_BCM_PIN 0
