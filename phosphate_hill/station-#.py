#!/usr/bin/env python3
import os
import sys
import traceback
import time
import json
import serial
# import subprocess
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
sys.path.append("/home/pi/pyduino/python/lib")
import mqtthelper # MQTT helper module for publishing archive

"""
This is the code for the Phosphate Hill Rehabilitation Cover Project.
For Stations 2, 3 and 4
The peripherals include:
    1x Camera
    1x UV Sensor
    2x Strings of Sensors per Station.
        Per String:
        4x Teros 12 Moisture Sensors
        4x Suction Sensors
        2x Oxygen Sensors
"""
#------------------- Constants and Ports Information---------------------------

SCREEN_DISPLAY = True
SAVE_TO_CSV = True
PUBLISH_TO_THINGSBOARD = False
DELIMITER = ','
SLEEP_TIME_SECONDS = 60*30 # s
SERIAL_PORT = '/dev/serial0' # datalogger version 2 uses ttyS0
SERIAL_BAUD = 9600
# PORT_SCALE = '/dev/serial/by-path/platform-20980000.usb-usb-0:1:1.0-port0' #the USB port connected to the scale
# PORT_SCALE = '/dev/serial/by-id/usb-FTDI_USB__-__Serial-if00-port0'
#HEAT_TIME = 24000

#---------------------- Configuration -------------------------

CSV_FILE_NAME = 'phosphate_hill-#.csv'

# TODO: check field_names and suction sensor addresses
field_name = ["battery",
            'temp_internal',
            'humidity_internal',
            'light_visible', 'light_ir', 'light_uv',
            'mos1','mos2','mos3','mos4','mos5','mos6','mos7','mos8',
            'mos1_temp','mos2_temp','mos3_temp','mos4_temp','mos5_temp','mos6_temp','mos7_temp','mos8_temp',
            'mos1_ec','mos2_ec','mos3_ec','mos4_ec','mos5_ec','mos6_ec','mos7_ec','mos8_ec',
            'suct1','suct2','suct3','suct4','suct5','suct6','suct7','suct8',
            'oxy1','oxy2','oxy3','oxy4',
            'oxy1_temp','oxy2_temp','oxy3_temp','oxy4_temp',
            'oxy1_baro','oxy2_baro','oxy3_baro','oxy4_baro',
            'oxy1_percent','oxy2_percent','oxy3_percent','oxy4_percent'
            ]

data_collected = dict((el,0.0) for el in field_name)

#---------------------------- Initiation --------------------------------------
if (PUBLISH_TO_THINGSBOARD):
    with open('/home/pi/pyduino/credential/thingsboard.json') as f:
        credential = json.load(f)

    try:
        # You can publish without starting a loop but failed publishes cannot be
        # accurately tracked.
        # Please use unique client_id for each client, and you should be able to use
        # same thingsboard device token for multiple clients.
        client = mqtt.Client(client_id="phosphatehill_#")
        client.username_pw_set(credential['access_token_phosphate_hill'])
        client.connect(credential['thingsboard_host'], 1883, 60)
        client.loop_start()
    except Exception:
        print("Failed to connect to thingsboard")
        # time.sleep(30)

try:
    # while True:
    ard = serial.Serial(port=SERIAL_PORT, baudrate=SERIAL_BAUD, timeout=30)
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
            csv_fid.write("Timestamp, Temp_Internal (C),Humidity_Internal (%)," \
                        "Light_Vis,Light_IR,Light_UV," \
                        "MOS1_VWP, MOS1_Temp, MOS1_EC," \
                        "MOS2_VWP, MOS2_Temp, MOS2_EC," \
                        "MOS3_VWP, MOS3_Temp, MOS3_EC," \
                        "MOS4_VWP, MOS4_Temp, MOS4_EC," \
                        "MOS5_VWP, MOS5_Temp, MOS5_EC," \
                        "MOS6_VWP, MOS6_Temp, MOS6_EC," \
                        "MOS7_VWP, MOS7_Temp, MOS7_EC," \
                        "MOS8_VWP, MOS8_Temp, MOS8_EC," \
                        "SUCT1 (C),SUCT2 (C),SUCT3 (C),SUCT4 (C),SUCT5 (C),SUCT6 (C),SUCT7 (C),SUCT8 (C)," \
                        "OXY1,OXY1_Temp,OXY1_Baro,OXY1_%," \
                        "OXY2,OXY2_Temp,OXY2_Baro,OXY2_%," \
                        "OXY3,OXY3_Temp,OXY3_Baro,OXY3_%," \
                        "OXY4,OXY4_Temp,OXY4_Baro,OXY4_%," \
                        "\r\n") # Allocate column names
        else:
            csv_fid = open(CSV_FILE_NAME, 'a', buffering=1) # Open file for appending
        # csv_fid.write(time_now_local_str + '\r\n')
        csv_fid.write(time_now_local_str)   # For standard csv format

    if SCREEN_DISPLAY:
        print(time_now_local_str)


    # ---------------------------------System Battery-----------------------------
    # System Battery
    try:
        ard.flushInput()
        command = "analog,15,power,9,points,3,dummies,1,interval_mm,200,debug,1"
        ard.write(command.encode())
        msg = ard.readline().decode()
        current_read = msg.split(',')[0:-1]
        battery_adc = float(current_read[-1])
        # ADC * (ADC_Resolution) * ((R2 + R3) / R3)
        vref = 5.1 # ADC Reference Voltage
        r2 = 120e3
        r3 = 39e3
        battery_voltage = battery_adc * float(((r2 + r3)/r3)) * float((vref/1024))

    except Exception as error:
        if SCREEN_DISPLAY:
            print(msg.strip())
            print("Battery Reading failed, error: {0}".format(sys.exc_info()[0]))
            # print("Battery Reading failed, error:", type(error), error)
    else:
        data_collected['battery_adc'] = battery_adc
        if SCREEN_DISPLAY:
            print("Battery Voltage (ADC): " + str(battery_adc) + ", " + str(battery_voltage) + "V")
        if SAVE_TO_CSV:
            # csv_fid.write(time_now_local_str + DELIMITER + 'Battery Voltage' + DELIMITER + "ADC" + DELIMITER+DELIMITER + str(battery_adc) + '\r\n')
            # csv_fid.write(time_now_local_str + DELIMITER + 'Battery Voltage' + DELIMITER + "V" + DELIMITER+DELIMITER + str(battery_voltage) + '\r\n')
            # csv_fid.write("{0}{1}".format(DELIMITER, battery_adc))
            pass


    # ---------------------------------Temp & Hum DHT22-----------------------------
    # DHT22 temp and humidity onboard
    try:
        command = "dht22,54,power,2,points,3,dummies,1,interval_mm,200,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode()
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


    # --------------------------------- UV & Iradiance-----------------------------
    # UV and Iradiance Sensor
    try:
        sensor_name = "UV"
        GPIO.setmode(GPIO.BCM)
        rpi_pin = 4
        GPIO.setup(rpi_pin, GPIO.OUT)
        GPIO.output(rpi_pin, GPIO.HIGH)
        command = "9548,0,type,si1145,points,3,dummies,1,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # Vis,261.67,IR,264.00,UV,2.33,
        GPIO.output(rpi_pin, GPIO.LOW)
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
        GPIO.cleanup()


    #---------------------------Moisture Sensor 1--------------
    # Moisture Sensor 1
    try:
        sensor_name = "mos1"
        command = "SDI-12,50,power,22,default_cmd,read,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # "a+<calibratedCountsVWC>±<temperature>+<electricalConductivity>"
        current_read=msg.split(',')[0:-1]
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
            csv_fid.write(DELIMITER + str(mos_vwp) + DELIMITER + str(mos_temp) + DELIMITER + str(mos_ec))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 2--------------
    # Moisture Sensor 2
    try:
        sensor_name = "mos2"
        command = "SDI-12,51,power,23,default_cmd,read,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # "a+<calibratedCountsVWC>±<temperature>+<electricalConductivity>"
        current_read=msg.split(',')[0:-1]
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
            csv_fid.write(DELIMITER + str(mos_vwp) + DELIMITER + str(mos_temp) + DELIMITER + str(mos_ec))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 3--------------
    # Moisture Sensor 3
    try:
        sensor_name = "mos3"
        command = "SDI-12,52,power,24,default_cmd,read,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # "a+<calibratedCountsVWC>±<temperature>+<electricalConductivity>"
        current_read=msg.split(',')[0:-1]
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
            csv_fid.write(DELIMITER + str(mos_vwp) + DELIMITER + str(mos_temp) + DELIMITER + str(mos_ec))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 4--------------
    # Moisture Sensor 4
    try:
        sensor_name = "mos4"
        command = "SDI-12,53,power,25,default_cmd,read,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # "a+<calibratedCountsVWC>±<temperature>+<electricalConductivity>"
        current_read=msg.split(',')[0:-1]
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
            csv_fid.write(DELIMITER + str(mos_vwp) + DELIMITER + str(mos_temp) + DELIMITER + str(mos_ec))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 5--------------
    # Moisture Sensor 5
    try:
        sensor_name = "mos5"
        command = "SDI-12,11,power,26,default_cmd,read,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # "a+<calibratedCountsVWC>±<temperature>+<electricalConductivity>"
        current_read=msg.split(',')[0:-1]
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
            csv_fid.write(DELIMITER + str(mos_vwp) + DELIMITER + str(mos_temp) + DELIMITER + str(mos_ec))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 6--------------
    # Moisture Sensor 6
    try:
        sensor_name = "mos6"
        command = "SDI-12,12,power,27,default_cmd,read,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # "a+<calibratedCountsVWC>±<temperature>+<electricalConductivity>"
        current_read=msg.split(',')[0:-1]
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
            csv_fid.write(DELIMITER + str(mos_vwp) + DELIMITER + str(mos_temp) + DELIMITER + str(mos_ec))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 7--------------
    # Moisture Sensor 7
    try:
        sensor_name = "mos7"
        command = "SDI-12,13,power,28,default_cmd,read,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # "a+<calibratedCountsVWC>±<temperature>+<electricalConductivity>"
        current_read=msg.split(',')[0:-1]
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
            csv_fid.write(DELIMITER + str(mos_vwp) + DELIMITER + str(mos_temp) + DELIMITER + str(mos_ec))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 8--------------
    # Moisture Sensor 8
    try:
        sensor_name = "mos8"
        command = "SDI-12,14,power,29,default_cmd,read,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # "a+<calibratedCountsVWC>±<temperature>+<electricalConductivity>"
        current_read=msg.split(',')[0:-1]
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
            csv_fid.write(DELIMITER + str(mos_vwp) + DELIMITER + str(mos_temp) + DELIMITER + str(mos_ec))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')


    #---------------------------Suction Sensor 1--------------------------------
    # Suction Sensor 1
    try:
        sensor_name = "suct1"
        command = "fred,___,dgin,55,snpw,30,htpw,31,itv,6000,otno,5,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() #<addr>,<base temp>,<heat temp_0>,<heat temp_...>,<cool temp_0>,<cool temp_...>
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        data_collected['suct1'] = temp_diff
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 2--------------------------------
    # Suction Sensor 2
    try:
        sensor_name = "suct2"
        command = "fred,___,dgin,56,snpw,32,htpw,33,itv,6000,otno,5,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() #<addr>,<base temp>,<heat temp_0>,<heat temp_...>,<cool temp_0>,<cool temp_...>
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        data_collected['suct2'] = temp_diff
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 3--------------------------------
    # Suction Sensor 3
    try:
        sensor_name = "suct3"
        command = "fred,___,dgin,57,snpw,34,htpw,35,itv,6000,otno,5,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() #<addr>,<base temp>,<heat temp_0>,<heat temp_...>,<cool temp_0>,<cool temp_...>
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        data_collected['suct3'] = temp_diff
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 4--------------------------------
    # Suction Sensor 4
    try:
        sensor_name = "suct4"
        command = "fred,___,dgin,58,snpw,36,htpw,37,itv,6000,otno,5,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() #<addr>,<base temp>,<heat temp_0>,<heat temp_...>,<cool temp_0>,<cool temp_...>
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        data_collected['suct4'] = temp_diff
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 5--------------------------------
    # Suction Sensor 5
    try:
        sensor_name = "suct5"
        command = "fred,___,dgin,59,snpw,38,htpw,39,itv,6000,otno,5,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() #<addr>,<base temp>,<heat temp_0>,<heat temp_...>,<cool temp_0>,<cool temp_...>
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        data_collected['suct5'] = temp_diff
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 6--------------------------------
    # Suction Sensor 6
    try:
        sensor_name = "suct6"
        command = "fred,___,dgin,60,snpw,40,htpw,41,itv,6000,otno,5,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() #<addr>,<base temp>,<heat temp_0>,<heat temp_...>,<cool temp_0>,<cool temp_...>
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        data_collected['suct6'] = temp_diff
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 7--------------------------------
    # Suction Sensor 7
    try:
        sensor_name = "suct7"
        command = "fred,___,dgin,61,snpw,42,htpw,43,itv,6000,otno,5,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() #<addr>,<base temp>,<heat temp_0>,<heat temp_...>,<cool temp_0>,<cool temp_...>
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        data_collected['suct7'] = temp_diff
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 8--------------------------------
    # Suction Sensor 8
    try:
        sensor_name = "suct8"
        command = "fred,___,dgin,62,snpw,44,htpw,45,itv,6000,otno,5,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() #<addr>,<base temp>,<heat temp_0>,<heat temp_...>,<cool temp_0>,<cool temp_...>
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        data_collected['suct8'] = temp_diff
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Oxygen Sensor 1--------------------------------
    # Oxygen Sensor 1
    try:
        sensor_name = "oxy1"
        command = "luminox,A,power,46,serial,1,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # “O xxxx.x T yxx.x P xxxx % xxx.xx e xxxx\r\n”
        current_read=msg.split(',')[-1].split(' ')
        o2_level = float(current_read[1])
        o2_temp = float(current_read[3])
        o2_baro = float(current_read[5])
        o2_percent = float(current_read[7])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + DELIMITER + DELIMITER + DELIMITER)
    else:
        data_collected['oxy1'] = o2_level
        data_collected["oxy1_temp"] = o2_temp
        data_collected["oxy1_baro"] = o2_baro
        data_collected["oxy1_percent"] = o2_percent
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(o2_level) + DELIMITER + str(o2_temp) + DELIMITER + str(o2_baro) + DELIMITER + str(o2_percent))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Oxygen Sensor 2--------------------------------
    # Oxygen Sensor 2
    try:
        sensor_name = "oxy2"
        command = "luminox,A,power,47,serial,3,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # “O xxxx.x T yxx.x P xxxx % xxx.xx e xxxx\r\n”
        current_read=msg.split(',')[-1].split(' ')
        o2_level = float(current_read[1])
        o2_temp = float(current_read[3])
        o2_baro = float(current_read[5])
        o2_percent = float(current_read[7])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + DELIMITER + DELIMITER + DELIMITER)
    else:
        data_collected['oxy2'] = o2_level
        data_collected["oxy2_temp"] = o2_temp
        data_collected["oxy2_baro"] = o2_baro
        data_collected["oxy2_percent"] = o2_percent
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(o2_level) + DELIMITER + str(o2_temp) + DELIMITER + str(o2_baro) + DELIMITER + str(o2_percent))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Oxygen Sensor 3--------------------------------
    # Oxygen Sensor 3
    try:
        sensor_name = "oxy3"
        command = "luminox,A,power,48,serial,2,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # “O xxxx.x T yxx.x P xxxx % xxx.xx e xxxx\r\n”
        current_read=msg.split(',')[-1].split(' ')
        o2_level = float(current_read[1])
        o2_temp = float(current_read[3])
        o2_baro = float(current_read[5])
        o2_percent = float(current_read[7])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + DELIMITER + DELIMITER + DELIMITER)
    else:
        data_collected['oxy3'] = o2_level
        data_collected["oxy3_temp"] = o2_temp
        data_collected["oxy3_baro"] = o2_baro
        data_collected["oxy3_percent"] = o2_percent
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(o2_level) + DELIMITER + str(o2_temp) + DELIMITER + str(o2_baro) + DELIMITER + str(o2_percent))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Oxygen Sensor 4--------------------------------
    # Oxygen Sensor 4
    try:
        sensor_name = "oxy4"
        command = "luminox,A,power,49,serial,3,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # “O xxxx.x T yxx.x P xxxx % xxx.xx e xxxx\r\n”
        current_read=msg.split(',')[-1].split(' ')
        o2_level = float(current_read[1])
        o2_temp = float(current_read[3])
        o2_baro = float(current_read[5])
        o2_percent = float(current_read[7])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + DELIMITER + DELIMITER + DELIMITER)
    else:
        data_collected['oxy4'] = o2_level
        data_collected["oxy4_temp"] = o2_temp
        data_collected["oxy4_baro"] = o2_baro
        data_collected["oxy4_percent"] = o2_percent
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(o2_level) + DELIMITER + str(o2_temp) + DELIMITER + str(o2_baro) + DELIMITER + str(o2_percent))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')


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

    if SCREEN_DISPLAY:
        print("")

except KeyboardInterrupt:
    pass
except Exception:
    traceback.print_exc()

else:
    # print("begin to sleep")
    # time.sleep(SLEEP_TIME_SECONDS) # sleep to the next loop
    pass

finally:
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

