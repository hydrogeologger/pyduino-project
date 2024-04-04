#!/usr/bin/env python3
import os
import sys
import traceback
import time
import json
# import subprocess
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import mqtthelper # MQTT helper module for publishing archive
sys.path.append("/home/pi/pyduino/python/lib")
# sys.path.append("C:\\Users\\uqltan14\\Desktop\\pyduino\\python\\lib")
from sensor.davis import (WindSpeed, Rain)

"""
This is the code for the Grange - Savage River Project, deployment April 2024.
For 1 Station
The peripherals include:
    6x Teros 12 Moisture Sensors
    2x Oxygen Luminox Sensors (SDI-12)

    The following are only for selected stations
    1x UV Sensor
    1x Ambient Temperature and Humidity (ATMOS 14)
    1x Wind Anemometer and Wind Vane
    1x Rain Gauge (Tip Bucket)
"""
#------------------- Constants and Ports Information---------------------------

SCREEN_DISPLAY = True
SAVE_TO_CSV = True
PUBLISH_TO_THINGSBOARD = True
DELIMITER = ','
SLEEP_TIME_SECONDS = 60*10 # s
SERIAL_PORT = '/dev/serial0' # datalogger version 2 uses ttyS0
SERIAL_BAUD = 9600
# PORT_SCALE = '/dev/serial/by-path/platform-20980000.usb-usb-0:1:1.0-port0' #the USB port connected to the scale
# PORT_SCALE = '/dev/serial/by-id/usb-FTDI_USB__-__Serial-if00-port0'
#HEAT_TIME = 24000

#---------------------- Configuration -------------------------

CSV_FILE_NAME = '2024_grange-savage1-rain-winddir.csv'

# TODO: check field_names and suction sensor addresses
field_name = ["rain",
            "wind_speed"
            ]

# data_collected = dict((el,0.0) for el in field_name)
data_collected = {}

#---------------------------- Initiation --------------------------------------
if PUBLISH_TO_THINGSBOARD:
    with open('/home/pi/pyduino/credential/thingsboard.json') as f:
        credential = json.load(f)

    try:
        # You can publish without starting a loop but failed publishes cannot be
        # accurately tracked.
        # Please use unique client_id for each client, and you should be able to use
        # same thingsboard device token for multiple clients.
        client = mqtt.Client(client_id="savage_1-wind-rain")
        client.username_pw_set(credential['access_token_savage1'])
        client.connect(credential['thingsboard_host'], 1883, 60)
        client.loop_start()
    except Exception:
        print("Failed to connect to thingsboard")
        # time.sleep(30)

try:
    rain_tip_bucket = Rain(name="rain", pin=18, debounce=0.001, resolution=0.2, debug=False)
    wind_speed = WindSpeed(name="wind_speed", pin=3, debounce=None, debug=False)

    rain_tip_bucket.begin()
    wind_speed.begin()

    first_run = True

    while True:
        # ard = serial.Serial(port=SERIAL_PORT, baudrate=SERIAL_BAUD, timeout=30)
        # time.sleep(3)

        time_now = time.time()
        time_now_local = time.localtime(time_now)
        seconds_since_epoch = int(round(time_now * 1000))
        time_now_local_str = time.strftime("%Y-%m-%d %H:%M:%S", time_now_local)

        # Open file for appending
        if SAVE_TO_CSV:
            # Check if file exist to add column headings
            if not os.path.isfile(CSV_FILE_NAME):
                csv_fid = open(CSV_FILE_NAME, 'w', buffering=1) # Open file for writing
                # TODO: Check headers
                csv_fid.write("Timestamp, rain (mm), wind_speed (km/hr)" \
                            "\r\n") # Allocate column names
            else:
                csv_fid = open(CSV_FILE_NAME, 'a', buffering=1) # Open file for appending
            # csv_fid.write(time_now_local_str + '\r\n')
            csv_fid.write(time_now_local_str)   # For standard csv format

        if SCREEN_DISPLAY:
            print(time_now_local_str)

        #---------------------------- Rain ------------------------------------
        try:
            cumulative_rain = round(rain_tip_bucket.get_cumulative(), 1)
        except Exception:
            if SCREEN_DISPLAY:
                print("Rain reading failed, error: {0}".format(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER)
        else:
            if first_run:
                cumulative_rain = ""
            else:
                data_collected['rain'] = cumulative_rain
            if SCREEN_DISPLAY:
                print(rain_tip_bucket.name.upper() + ": " + str(cumulative_rain))
            if SAVE_TO_CSV:
                csv_fid.write("{0}{1}".format(DELIMITER, cumulative_rain))
        finally:
            pass


        #---------------------------- Wind speed ------------------------------
        try:
            average_wind = round(wind_speed.get_average(), 2)
        except Exception:
            if SCREEN_DISPLAY:
                print("wind reading failed, error: {0}".format(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER)
        else:
            if first_run:
                average_wind = ""
            else:
                data_collected['wind_speed'] = average_wind
            if SCREEN_DISPLAY:
                print(wind_speed.name.upper() + ": " + str(average_wind))
            if SAVE_TO_CSV:
                csv_fid.write("{0}{1}".format(DELIMITER, average_wind))
        finally:
            pass


        # End of pulse sensor
        first_run = False

        #--------------------------- End of Sampling --------------------------
        if SAVE_TO_CSV:
            csv_fid.write("\r\n")
            csv_fid.flush()
            if not csv_fid.closed:
                csv_fid.close()

        #----------------------------Upload data ------------------------------
        # if (ard.isOpen()):
        #     ard.close()

        if (PUBLISH_TO_THINGSBOARD):
            try:
                # Result is in tuple (rc, mid) of MQTTMessageInfo class
                publish_result = mqtthelper.publish_to_thingsboard(client, payload=data_collected, ts=seconds_since_epoch, display_payload=True, debug=False)
            except (ValueError, RuntimeError) as error:
                if SCREEN_DISPLAY:
                    print(error)
            else:
                if SCREEN_DISPLAY:
                    print(publish_result)


        if SCREEN_DISPLAY:
            print("begin to sleep")
            print("")
            sys.stdout.flush()

        time.sleep(SLEEP_TIME_SECONDS) # sleep to the next loop

except KeyboardInterrupt:
    pass
except Exception:
    traceback.print_exc()

else:
    # print("begin to sleep")
    # time.sleep(SLEEP_TIME_SECONDS) # sleep to the next loop
    pass

finally:
    # GPIO.cleanup()
    try:
        if SAVE_TO_CSV:
            csv_fid.flush()
            if not csv_fid.closed:
                csv_fid.close()
    except NameError:
        pass
    # if (ard.isOpen()):
    #     ard.close()
    if (PUBLISH_TO_THINGSBOARD and client.is_connected()):
        client.loop_stop()
        client.disconnect()
