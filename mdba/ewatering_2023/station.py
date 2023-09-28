#!/usr/bin/env python
import os
import sys
import traceback
import time
import datetime  #required by is_time_between
import json
import serial
# import subprocess
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
sys.path.append("/home/pi/pyduino/python/lib")
from sensor.davis import (Rain, WindSpeed, WindDirection)
import mqtthelper # MQTT helper module for publishing archive

"""
This is the code for the MDBA Ewatering Project for 2023 October Deployment.
For 1 Station
The peripherals include:
    1x Camera
    1x UV Sensor
    1x Ambient Temperature and Humidity
    1x Barometer
    1x Wind Anemometer and Wind Vane
    1x Rain Gauge (Tip Bucket)
    10x Teros 12 Moisture Sensors
    1x Aqua Troll 200
"""
#------------------- Constants and Ports Information---------------------------

SCREEN_DISPLAY = True
SAVE_TO_CSV = True
PUBLISH_TO_THINGSBOARD = True
DELIMITER = ','
SLEEP_TIME_SECONDS = 60 * 30 # s every 30 minutes
SERIAL_PORT = '/dev/serial0' # datalogger version 2 uses ttyS0
SERIAL_BAUD = 9600
# PORT_SCALE = '/dev/serial/by-path/platform-20980000.usb-usb-0:1:1.0-port0' #the USB port connected to the scale
# PORT_SCALE = '/dev/serial/by-id/usb-FTDI_USB__-__Serial-if00-port0'
#HEAT_TIME = 24000


#---------------------- Configuration -------------------------

CSV_FILE_NAME = '2023_mdba-ewatering.csv'

# TODO: check field_names and suction sensor addresses
field_name = ["battery",
            'temp_internal',
            'humidity_internal',
            'light_visible', 'light_ir', 'light_uv',
            'temp_ambient','humidity_ambient',
            'wind_dir',
            'light_visible', 'light_ir', 'light_uv',
            'mos1','mos2','mos3','mos4','mos5','mos6','mos7','mos8', 'mos9', 'mos10',
            'mos1_temp','mos2_temp','mos3_temp','mos4_temp','mos5_temp','mos6_temp','mos7_temp','mos8_temp','mos9_temp','mos10_temp',
            'mos1_ec','mos2_ec','mos3_ec','mos4_ec','mos5_ec','mos6_ec','mos7_ec','mos8_ec','mos9_ec','mos10_ec'
            ]

data_collected = {}


#--------------------- Support Functions --------------------------------------
def is_time_between(begin_time, end_time, check_time=None):
    check_time = datetime.datetime.now().time()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time

def on_connect(client, userdata, flags, rc):
    if rc == mqtt.CONNACK_ACCEPTED:
        print("connected OK Returned code=" + str(rc))
    else:
        print("Bad connection Returned code=" + str(rc))

def on_disconnect(client, userdata, rc):
    if rc != mqtt.CONNACK_ACCEPTED:
        print("Unexpected disconnection. Returned Code= " + str(rc))

#---------------------------- Initiation --------------------------------------
camera_switch_on = False
first_run = True

rain_tip_bucket = Rain(name="rain", pin=2, debounce=0.001, volume=0.2, debug=False)
wind_speed = WindSpeed(name="wind_speed", pin=3, debounce=None, debug=False)

rain_tip_bucket.begin()
wind_speed.begin()

if (PUBLISH_TO_THINGSBOARD):
    with open('/home/pi/pyduino/credential/thingsboard.json') as f:
        credential = json.load(f)

    try:
        # You can publish without starting a loop but failed publishes cannot be
        # accurately tracked.
        # Please use unique client_id for each client, and you should be able to use
        # same thingsboard device token for multiple clients.
        client = mqtt.Client(client_id=None)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.username_pw_set(credential['mdba_ewatering_2023'])
        client.connect(credential['thingsboard_host'], 1883, 60)
        client.loop_start()
    except Exception:
        print("Failed to connect to thingsboard")
        # time.sleep(30)

try:
    while True:
        ard = serial.Serial(port=SERIAL_PORT, baudrate=SERIAL_BAUD, timeout=30)
        time.sleep(3)

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
                csv_fid.write("Timestamp, Temp_Internal (C), Humidity_Internal (%), " \
                            "Temp_Ambient (C), Humidity_Ambient (%), " \
                            "Temp_Baro (C), Baro (Pa), " \
                            "Light_Vis, Light_IR, Light_UV (index*100), " \
                            "rain (mm), wind_speed (km/hr), Wind_Direction (Deg), " \
                            "MOS1_VWP, MOS1_Temp, MOS1_EC, " \
                            "MOS2_VWP, MOS2_Temp, MOS2_EC, " \
                            "MOS3_VWP, MOS3_Temp, MOS3_EC, " \
                            "MOS4_VWP, MOS4_Temp, MOS4_EC, " \
                            "MOS5_VWP, MOS5_Temp, MOS5_EC, " \
                            "MOS6_VWP, MOS6_Temp, MOS6_EC, " \
                            "MOS7_VWP, MOS7_Temp, MOS7_EC, " \
                            "MOS8_VWP, MOS8_Temp, MOS8_EC, " \
                            "MOS9_VWP, MOS9_Temp, MOS9_EC, " \
                            "MOS10_VWP, MOS10_Temp, MOS10_EC," \
                            "sa1_p_piezo, sa1_t_piezo (C), sa1_ec_piezo," \
                            "\r\n") # Allocate column names
            else:
                csv_fid = open(CSV_FILE_NAME, 'a', buffering=1) # Open file for appending
            # csv_fid.write(time_now_local_str + '\r\n')
            csv_fid.write(time_now_local_str)   # For standard csv format

        if SCREEN_DISPLAY:
            print(time_now_local_str)


        # --------------------------------- Serial Test ------------------------------
        # Test serial connection if failed then reset arduino
        ard.flushInput()
        command = "abc"
        ard.write(command)
        msg = ard.readline()
        if msg != "abc\r\n":
            print("Failed Handshake: No Response, resetting mcu")
            GPIO.setmode(GPIO.BCM)
            RPI_RESET_PIN = 27  #GPIO/BCM pin number to reset arduino
            GPIO.setup(RPI_RESET_PIN, GPIO.OUT)
            GPIO.output(RPI_RESET_PIN, GPIO.LOW)
            time.sleep(2) # Hold reset line for x seconds
            GPIO.cleanup(RPI_RESET_PIN)
            time.sleep(5) # give arduino time to configure it self

        #--------------------------- camera switch-------------------------------
        whether_time_for_camera_on = is_time_between(datetime.time(7,30), datetime.time(16,40))   #brisbane time
        if whether_time_for_camera_on and camera_switch_on is False:
            ard.flushInput()
            ard.write("power_switch,8,power_switch_status,1")
            msg = ard.readline()
            if SCREEN_DISPLAY:
                print("Camera: Turn on")
                print (msg.rstrip())
            camera_switch_on = True
            # time.sleep(120)
        elif whether_time_for_camera_on and camera_switch_on:
            if SCREEN_DISPLAY:
                print("Camera: Keep on")
        elif whether_time_for_camera_on is False and camera_switch_on:
            ard.flushInput()
            ard.write("power_switch,8,power_switch_status,0")
            msg = ard.readline()
            if SCREEN_DISPLAY:
                print("Camera: Turn off")
                print (msg.rstrip())
            camera_switch_on = False
            # time.sleep(180)
        elif whether_time_for_camera_on is False and camera_switch_on is False:
            if SCREEN_DISPLAY:
                print("Camera: Keep Off")
        # time.sleep(5)

        # ---------------------------------Temp & Hum DHT22-----------------------------
        # DHT22 temp and humidity onboard
        try:
            command = "dht22,54,power,2,points,3,dummies,1,interval_mm,200,debug,0"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline()
            current_read = msg.split(',')[0:-1]
            dht22_temp = float(current_read[-2])
            dht22_hum = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                print("DHT22 reading failed, error: {0}".format(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER)
        else:
            data_collected['temp_internal'] = dht22_temp
            data_collected['humidity_internal'] = dht22_hum
            if SCREEN_DISPLAY:
                print("Enclosure Temp (C)" + ": " + str(dht22_temp))
                print("Enclosure Humidity (%): " + str(dht22_hum))
            if SAVE_TO_CSV:
                csv_fid.write("{0}{1}{0}{2}".format(DELIMITER, dht22_temp, dht22_hum))
        finally:
            time.sleep(1)


        command = "9548_reset"
        ard.write(command)
        time.sleep(1)


        # ------------------ Ambient Temperature & Humidity ------------------------
        # SHT31
        try:
            sensor_name = "SHT31"
            command = "9548,1,type,sht31,power,24,points,3,dummies,1,debug,0"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline() # <temperature>,humidity,
            current_read = msg.split(',')[0:-1]
            sht31_temperature = float(current_read[-2])
            sht31_humidity = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                print("SHT31 reading failed, error: {0}".format(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER)
        else:
            data_collected['temp_ambient'] = sht31_temperature
            data_collected['humidity_ambient'] = sht31_humidity
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write("{0}{1}{0}{2}".format(DELIMITER, sht31_temperature, sht31_humidity))
        finally:
            pass

        command = "9548_reset"
        ard.write(command)
        time.sleep(1)

        # ------------------ Barometer ------------------------
        # 5803
        try:
            sensor_name = "baro"
            command = "9548,0,type,5803,power,23,points,3,dummies,1,debug,0"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline() # <temperature>,pressure,
            current_read = msg.split(',')[0:-1]
            barometer_temperature = float(current_read[-2])
            barometer_pressure = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                print("5803 reading failed, error: {0}".format(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER)
        else:
            data_collected['baro_temp'] = barometer_temperature
            data_collected['baro_pressure'] = barometer_pressure
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write("{0}{1}{0}{2}".format(DELIMITER, barometer_temperature, barometer_pressure))
        finally:
            pass


        command = "9548_reset"
        ard.write(command)
        time.sleep(1)

        # --------------------------------- UV & Iradiance-----------------------------
        # UV and Iradiance Sensor
        try:
            sensor_name = "UV"
            command = "9548,2,type,si1145,power,25,points,3,dummies,1,debug,0"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline() # Vis,261.67,IR,264.00,UV,2.33,
            current_read = msg.split(',')[0:-1]
            light_visible = float(current_read[-5])
            light_ir = float(current_read[-3])
            light_uv = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                print("UV reading failed, error: {0}".format(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER + DELIMITER)
        else:
            data_collected['light_visible'] = light_visible
            data_collected['light_ir'] = light_ir
            data_collected['light_uv'] = light_uv
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write("{0}{1}{0}{2}{0}{3}".format(DELIMITER, light_visible, light_ir, light_uv))
        finally:
            time.sleep(1)

        #---------------------------- Rain ------------------------------------
        try:
            cumulative_rain = rain_tip_bucket.get_cumulative()
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
            average_wind = wind_speed.get_average()
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

        # ------------------------- Wind Direction --------------------------------
        # Wind Direction
        try:
            sensor_name = "wind_dir"
            wind_dir_device = WindDirection(name=sensor_name, offset=0)
            command = "analog,1,power,22,points,3,dummies,1,interval_mm,100,debug,1"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline() # <adc>,
            current_read = msg.split(',')[0:-1]
            wind_direction_adc = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                print("Wind Direction reading failed, error: {0}".format(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER)
        else:
            wind_direction_degree = wind_dir_device.get_calibrated_direction(wind_direction_adc)
            data_collected['wind_dir'] = wind_direction_degree
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write("{0}{1}".format(DELIMITER, wind_direction_degree))
        finally:
            pass


        #---------------------------Moisture Sensor 1--------------
        # Moisture Sensor 1
        try:
            sensor_name = "mos1"
            command = "SDI-12,50,power,26,default_cmd,read,debug,0"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline() # "a+<calibratedCountsVWC>+-<temperature>+<electricalConductivity>"
            current_read = msg.split(',')[0:-1]
            mos_vwp = float(current_read[-3])
            mos_temp = float(current_read[-2])
            mos_ec = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
                print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER + DELIMITER)
        else:
            data_collected['mos1'] = mos_vwp
            data_collected['mos1_temp'] = mos_temp
            data_collected['mos1_ec'] = mos_ec
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + str(mos_vwp) +
                              DELIMITER + str(mos_temp) +
                              DELIMITER + str(mos_ec))
                # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

        #---------------------------Moisture Sensor 2--------------
        # Moisture Sensor 2
        try:
            sensor_name = "mos2"
            command = "SDI-12,51,power,27,default_cmd,read,debug,0"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline() # "a+<calibratedCountsVWC>+-<temperature>+<electricalConductivity>"
            current_read = msg.split(',')[0:-1]
            mos_vwp = float(current_read[-3])
            mos_temp = float(current_read[-2])
            mos_ec = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
                print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER + DELIMITER)
        else:
            data_collected['mos2'] = mos_vwp
            data_collected['mos2_temp'] = mos_temp
            data_collected['mos2_ec'] = mos_ec
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + str(mos_vwp) +
                              DELIMITER + str(mos_temp) +
                              DELIMITER + str(mos_ec))
                # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

        #---------------------------Moisture Sensor 3--------------
        # Moisture Sensor 3
        try:
            sensor_name = "mos3"
            command = "SDI-12,52,power,28,default_cmd,read,debug,0"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline() # "a+<calibratedCountsVWC>+-<temperature>+<electricalConductivity>"
            current_read = msg.split(',')[0:-1]
            mos_vwp = float(current_read[-3])
            mos_temp = float(current_read[-2])
            mos_ec = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
                print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER + DELIMITER)
        else:
            data_collected['mos3'] = mos_vwp
            data_collected['mos3_temp'] = mos_temp
            data_collected['mos3_ec'] = mos_ec
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + str(mos_vwp) +
                              DELIMITER + str(mos_temp) +
                              DELIMITER + str(mos_ec))
                # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

        #---------------------------Moisture Sensor 4--------------
        # Moisture Sensor 4
        try:
            sensor_name = "mos4"
            command = "SDI-12,53,power,29,default_cmd,read,debug,0"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline() # "a+<calibratedCountsVWC>+-<temperature>+<electricalConductivity>"
            current_read = msg.split(',')[0:-1]
            mos_vwp = float(current_read[-3])
            mos_temp = float(current_read[-2])
            mos_ec = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
                print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER + DELIMITER)
        else:
            data_collected['mos4'] = mos_vwp
            data_collected['mos4_temp'] = mos_temp
            data_collected['mos4_ec'] = mos_ec
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + str(mos_vwp) +
                              DELIMITER + str(mos_temp) +
                              DELIMITER + str(mos_ec))
                # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

        #---------------------------Moisture Sensor 5--------------
        # Moisture Sensor 5
        try:
            sensor_name = "mos5"
            command = "SDI-12,62,power,30,default_cmd,read,debug,0"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline() # "a+<calibratedCountsVWC>+-<temperature>+<electricalConductivity>"
            current_read = msg.split(',')[0:-1]
            mos_vwp = float(current_read[-3])
            mos_temp = float(current_read[-2])
            mos_ec = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
                print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER + DELIMITER)
        else:
            data_collected['mos5'] = mos_vwp
            data_collected['mos5_temp'] = mos_temp
            data_collected['mos5_ec'] = mos_ec
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + str(mos_vwp) +
                              DELIMITER + str(mos_temp) +
                              DELIMITER + str(mos_ec))
                # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

        #---------------------------Moisture Sensor 6--------------
        # Moisture Sensor 6
        try:
            sensor_name = "mos6"
            command = "SDI-12,63,power,31,default_cmd,read,debug,0"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline() # "a+<calibratedCountsVWC>+-<temperature>+<electricalConductivity>"
            current_read = msg.split(',')[0:-1]
            mos_vwp = float(current_read[-3])
            mos_temp = float(current_read[-2])
            mos_ec = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
                print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER + DELIMITER)
        else:
            data_collected['mos6'] = mos_vwp
            data_collected['mos6_temp'] = mos_temp
            data_collected['mos6_ec'] = mos_ec
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + str(mos_vwp) +
                              DELIMITER + str(mos_temp) +
                              DELIMITER + str(mos_ec))
                # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

        #---------------------------Moisture Sensor 7--------------
        # Moisture Sensor 7
        try:
            sensor_name = "mos7"
            command = "SDI-12,64,power,32,default_cmd,read,debug,0"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline() # "a+<calibratedCountsVWC>+-<temperature>+<electricalConductivity>"
            current_read = msg.split(',')[0:-1]
            mos_vwp = float(current_read[-3])
            mos_temp = float(current_read[-2])
            mos_ec = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
                print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER + DELIMITER)
        else:
            data_collected['mos7'] = mos_vwp
            data_collected['mos7_temp'] = mos_temp
            data_collected['mos7_ec'] = mos_ec
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + str(mos_vwp) +
                              DELIMITER + str(mos_temp) +
                              DELIMITER + str(mos_ec))
                # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

        #---------------------------Moisture Sensor 8--------------
        # Moisture Sensor 8
        try:
            sensor_name = "mos8"
            command = "SDI-12,65,power,33,default_cmd,read,debug,0"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline() # "a+<calibratedCountsVWC>+-<temperature>+<electricalConductivity>"
            current_read = msg.split(',')[0:-1]
            mos_vwp = float(current_read[-3])
            mos_temp = float(current_read[-2])
            mos_ec = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
                print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER + DELIMITER)
        else:
            data_collected['mos8'] = mos_vwp
            data_collected['mos8_temp'] = mos_temp
            data_collected['mos8_ec'] = mos_ec
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + str(mos_vwp) +
                              DELIMITER + str(mos_temp) +
                              DELIMITER + str(mos_ec))
                # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

        #---------------------------Moisture Sensor 9--------------
        # Moisture Sensor 9
        try:
            sensor_name = "mos9"
            command = "SDI-12,66,power,34,default_cmd,read,debug,0"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline() # "a+<calibratedCountsVWC>+-<temperature>+<electricalConductivity>"
            current_read = msg.split(',')[0:-1]
            mos_vwp = float(current_read[-3])
            mos_temp = float(current_read[-2])
            mos_ec = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
                print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER + DELIMITER)
        else:
            data_collected['mos9'] = mos_vwp
            data_collected['mos9_temp'] = mos_temp
            data_collected['mos9_ec'] = mos_ec
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + str(mos_vwp) +
                              DELIMITER + str(mos_temp) +
                              DELIMITER + str(mos_ec))
                # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

        #---------------------------Moisture Sensor 10--------------
        # Moisture Sensor 10
        try:
            sensor_name = "mos10"
            command = "SDI-12,67,power,35,default_cmd,read,debug,0"
            ard.flushInput()
            ard.write(command)
            msg = ard.readline() # "a+<calibratedCountsVWC>+-<temperature>+<electricalConductivity>"
            current_read = msg.split(',')[0:-1]
            mos_vwp = float(current_read[-3])
            mos_temp = float(current_read[-2])
            mos_ec = float(current_read[-1])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
                print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER + DELIMITER)
        else:
            data_collected['mos10'] = mos_vwp
            data_collected['mos10_temp'] = mos_temp
            data_collected['mos10_ec'] = mos_ec
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + str(mos_vwp) +
                              DELIMITER + str(mos_temp) +
                              DELIMITER + str(mos_ec))
                # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')


        #------------------------aqua troll 200 for sa1-----------------------------
        try:
            sensor_name = "aquatroll_sa1"
            ard.flushInput()
            ard.write("SDI-12,68,custom_cmd,aM!,debug,0")  # do measurement
            msg = ard.readline() # a0013

            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())

            time.sleep(3) # this appears to be important

            ard.flushInput()
            ard.write("SDI-12,68,custom_cmd,aD0!,debug,0")
            msg = ard.readline()
            current_read = msg[:-3].split('+')
            aqua_troll_pressure = float(current_read[1])
            aqua_troll_temperature = float(current_read[2])
            aqua_troll_ec = float(current_read[3])
        except Exception:
            if SCREEN_DISPLAY:
                print(msg.rstrip())
                # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
                print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + DELIMITER + DELIMITER)
        else:
            data_collected['sa1_p_piezo'] = aqua_troll_pressure
            data_collected['sa1_t_piezo'] = aqua_troll_temperature
            data_collected['sa1_ec_piezo'] = aqua_troll_ec
            if SCREEN_DISPLAY:
                print(sensor_name.upper() + ": " + msg.rstrip())
            if SAVE_TO_CSV:
                csv_fid.write(DELIMITER + str(aqua_troll_pressure) +
                              DELIMITER + str(aqua_troll_temperature) +
                              DELIMITER + str(aqua_troll_ec))


        # ------------------------------DO NOT EDIT Battery Check---------------------
        # ---------------------------------System Battery-----------------------------
        # System Battery
        try:
            ard.flushInput()
            command = "analog,15,power,9,points,3,dummies,1,interval_mm,200,debug,1"
            ard.write(command)
            msg = ard.readline()
            current_read = msg.split(',')[0:-1]
            battery_adc = float(current_read[-1])
        except Exception as error:
            if SCREEN_DISPLAY:
                print(msg.strip())
                print("Battery Reading failed, error: {0}".format(sys.exc_info()[0]))
                # print("Battery Reading failed, error:", type(error), error)
        else:
            # ADC * (ADC_Resolution) * ((R2 + R3) / R3)
            vref = 5.1 # ADC Reference Voltage
            r2 = 120e3
            r3 = 39e3
            battery_voltage = battery_adc * float(((r2 + r3)/r3)) * float((vref/1024))
            battery_voltage = round(battery_voltage, 2)
            # data_collected['battery_adc'] = battery_adc
            data_collected['battery_voltage'] = battery_voltage
            if SCREEN_DISPLAY:
                print("Battery Voltage (ADC): " + str(battery_adc) + ", " + str(battery_voltage) + " V")
            if SAVE_TO_CSV:
                # csv_fid.write(time_now_local_str + DELIMITER + 'Battery Voltage' + DELIMITER + "ADC" + DELIMITER+DELIMITER + str(battery_adc) + '\r\n')
                # csv_fid.write(time_now_local_str + DELIMITER + 'Battery Voltage' + DELIMITER + "V" + DELIMITER+DELIMITER + str(battery_voltage) + '\r\n')
                # csv_fid.write("{0}{1}".format(DELIMITER, battery_adc))
                pass

        try:
            if SAVE_TO_CSV:
                csv_fid.write("\r\n")
                csv_fid.flush()
                if not csv_fid.closed:
                    csv_fid.close()
        except (NameError):
            pass
        #----------------------------Upload data -----------------------------------
        if (ard.isOpen()):
            ard.close()

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

        # Tidying up
        data_collected.clear()
        print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ' - sleep for ' + str(SLEEP_TIME_SECONDS) + ' seconds')
        time.sleep(SLEEP_TIME_SECONDS) # sleep to the next loop

        if SCREEN_DISPLAY:
            print("")

except KeyboardInterrupt:
    pass
# except Exception:
#     traceback.print_exc()

else:
    pass

finally:
    # GPIO.setwarnings(False)
    # GPIO.cleanup()
    try:
        if SAVE_TO_CSV:
            csv_fid.write("\r\n")
            csv_fid.flush()
            if not csv_fid.closed:
                csv_fid.close()
    except (NameError):
        pass
    if (ard.isOpen()):
        ard.close()
    if (PUBLISH_TO_THINGSBOARD and client.is_connected()):
        client.loop_stop()
        client.disconnect()
