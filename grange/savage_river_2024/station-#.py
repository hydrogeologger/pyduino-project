#!/usr/bin/env python
import os
import sys
import traceback
import time
import json
import serial
import RPi.GPIO as GPIO
# import subprocess
import paho.mqtt.client as mqtt
import mqtthelper # MQTT helper module for publishing archive
# sys.path.append("/home/pi/pyduino/python/lib")
# from sensor.davis import (WindDirection)

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
SLEEP_TIME_SECONDS = 60*30 # s
SERIAL_PORT = '/dev/serial0' # datalogger version 2 uses ttyS0
SERIAL_BAUD = 9600
# PORT_SCALE = '/dev/serial/by-path/platform-20980000.usb-usb-0:1:1.0-port0' #the USB port connected to the scale
# PORT_SCALE = '/dev/serial/by-id/usb-FTDI_USB__-__Serial-if00-port0'
#HEAT_TIME = 24000

#---------------------- Configuration -------------------------

CSV_FILE_NAME = '2024_grange-savage#.csv'

field_name = ["battery",
            'temp_internal',
            'humidity_internal',
            'temp_ambient','humidity_ambient',
            'pressure_vapor', 'pressure_ambient',
            'light_visible', 'light_ir', 'light_uv',
            'wind_dir',
            'mos1','mos2','mos3','mos4','mos5','mos6',
            'mos1_temp','mos2_temp','mos3_temp','mos4_temp','mos5_temp','mos6_temp',
            'mos1_ec','mos2_ec','mos3_ec','mos4_ec','mos5_ec','mos6_ec',
            'oxy1','oxy2',
            'oxy1_temp','oxy2_temp',
            'oxy1_baro','oxy2_baro',
            'oxy1_percent','oxy2_percent',
            ]

data_collected = {}

#---------------------------- Initiation --------------------------------------
if (PUBLISH_TO_THINGSBOARD):
    with open('/home/pi/pyduino/credential/thingsboard.json') as f:
        credential = json.load(f)

#     try:
#         # You can publish without starting a loop but failed publishes cannot be
#         # accurately tracked.
#         # Please use unique client_id for each client, and you should be able to use
#         # same thingsboard device token for multiple clients.
#         client = mqtt.Client(client_id="savage_#")
#         client.username_pw_set(credential['access_token_savage#'])
#         client.connect(credential['thingsboard_host'], 1883, 60)
#         client.loop_start()
#     except Exception:
#         print("Failed to connect to thingsboard")
#         # time.sleep(30)

try:
    # while True:
    ard = serial.Serial(port=SERIAL_PORT, baudrate=SERIAL_BAUD, timeout=30)
    # time.sleep(3)

    # --------------------------------- Serial Test ------------------------------
    # Test serial connection if failed then reset arduino
    ard.flushInput()
    command = "abc"
    ard.write(command.encode())
    msg = ard.readline().decode()
    if msg != "abc\r\n":
        print("Failed Handshake: No Response, resetting mcu")
        GPIO.setmode(GPIO.BCM)
        RPI_RESET_PIN = 27  #GPIO/BCM pin number to reset arduino
        GPIO.setup(RPI_RESET_PIN, GPIO.OUT)
        GPIO.output(RPI_RESET_PIN, GPIO.LOW)
        time.sleep(2) # Hold reset line for x seconds
        GPIO.cleanup(RPI_RESET_PIN)
        time.sleep(5) # give arduino time to configure it self

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
            csv_fid.write("Timestamp,Temp_Internal (C),Humidity_Internal (%)," \
                        # "Temp_Ambient (C),Humidity_Ambient (%),Pressure_Atmo (kPa)," \
                        # "Pressure_Vapor (kPa)," \
                        # "Wind_Direction (Deg)," \
                        # "Light_Vis,Light_IR,Light_UV (index*100)," \
                        "MOS1_VWP,MOS1_Temp,MOS1_EC," \
                        "MOS2_VWP,MOS2_Temp,MOS2_EC," \
                        "MOS3_VWP,MOS3_Temp,MOS3_EC," \
                        "MOS4_VWP,MOS4_Temp,MOS4_EC," \
                        "MOS5_VWP,MOS5_Temp,MOS5_EC," \
                        "MOS6_VWP,MOS6_Temp,MOS6_EC," \
                        "OXY1,OXY1_Temp,OXY1_Baro,OXY1_%," \
                        "OXY2,OXY2_Temp,OXY2_Baro,OXY2_%," \
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

    # # ------------------ Ambient Temperature & Humidity ------------------------
    # # ATMOS-14
    # try:
    #     sensor_name = "ATMOS14"
    #     command = "SDI-12,53,power,31,default_cmd,read,debug,0"
    #     ard.write(command.encode())
    #     ard.flushInput()
    #     msg = ard.readline().decode() # "a+<vaporPressure>±<temperature>+<relativeHumidity>±<atmosphericPressure>"
    #     current_read=msg.split(',')[0:-1]
    #     atmos_vapor_pressure = float(current_read[-4])
    #     atmos_temperature = float(current_read[-3])
    #     atmos_relative_humidity = float(current_read[-2])
    #     atmos_pressure = float(current_read[-1])
    # except Exception:
    #     if SCREEN_DISPLAY:
    #         print(msg.rstrip())
    #         # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
    #         print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
    #     if SAVE_TO_CSV:
    #         csv_fid.write(DELIMITER + DELIMITER + DELIMITER + DELIMITER)
    # else:
    #     data_collected['temp_ambient'] = atmos_temperature
    #     data_collected['humidity_ambient'] = round(atmos_relative_humidity * 100, 1)
    #     data_collected['pressure_vapor'] = atmos_vapor_pressure
    #     data_collected['pressure_ambient'] = atmos_pressure
    #     if SCREEN_DISPLAY:
    #         print(sensor_name.upper() + ": " + msg.rstrip())
    #     if SAVE_TO_CSV:
    #         csv_fid.write("{0}{1}{0}{2}{0}{3}{0}{4}".format(DELIMITER,
    #                 atmos_temperature, atmos_relative_humidity,
    #                 atmos_pressure, atmos_vapor_pressure))
    #         # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    # # ------------------------- Wind Direction --------------------------------
    # # Wind Direction
    # try:
    #     sensor_name = "wind_dir"
    #     wind_dir_device = WindDirection(name=sensor_name, offset=0)
    #     command = "analog,1,power,32,points,3,dummies,1,interval_mm,100,debug,1"
    #     ard.write(command.encode())
    #     ard.flushInput()
    #     msg = ard.readline().decode() # <adc>,
    #     current_read = msg.split(',')[0:-1]
    #     wind_direction_adc = float(current_read[-1])
    # except Exception:
    #     if SCREEN_DISPLAY:
    #         print(msg.rstrip())
    #         print("Wind Direction reading failed, error: {0}".format(sys.exc_info()[0]))
    #     if SAVE_TO_CSV:
    #         csv_fid.write(DELIMITER)
    # else:
    #     wind_direction_degree = round(
    #             wind_dir_device.get_calibrated_direction(wind_direction_adc), 1)
    #     data_collected['wind_dir'] = wind_direction_degree
    #     if SCREEN_DISPLAY:
    #         print(sensor_name.upper() + ": " + msg.rstrip())
    #     if SAVE_TO_CSV:
    #         csv_fid.write("{0}{1}".format(DELIMITER, wind_direction_degree))
    # finally:
    #     pass

    # # --------------------------------- UV & Iradiance-----------------------------
    # # UV and Iradiance Sensor
    # try:
    #     sensor_name = "UV"
    #     command = "9548,0,type,si1145,power,30,points,3,dummies,1,debug,0"
    #     ard.write(command.encode())
    #     ard.flushInput()
    #     msg = ard.readline().decode() # Vis,261.67,IR,264.00,UV,2.33,
    #     current_read = msg.split(',')[0:-1]
    #     light_visible = float(current_read[-5])
    #     light_ir = float(current_read[-3])
    #     light_uv = float(current_read[-1])
    # except Exception:
    #     if SCREEN_DISPLAY:
    #         print(msg.rstrip())
    #         print("UV reading failed, error: {0}".format(sys.exc_info()[0]))
    #     if SAVE_TO_CSV:
    #         csv_fid.write(DELIMITER + DELIMITER + DELIMITER)
    # else:
    #     data_collected['light_visible'] = light_visible
    #     data_collected['light_ir'] = light_ir
    #     data_collected['light_uv'] = light_uv
    #     if SCREEN_DISPLAY:
    #         print(sensor_name.upper() + ": " + msg.rstrip())
    #     if SAVE_TO_CSV:
    #         csv_fid.write("{0}{1}{0}{2}{0}{3}".format(DELIMITER, light_visible, light_ir, light_uv))
    # finally:
    #     pass


    #---------------------------Moisture Sensor 1--------------
    # Moisture Sensor 1
    try:
        sensor_name = "mos1"
        command = "SDI-12,62,power,22,default_cmd,read,debug,0"
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
        command = "SDI-12,63,power,23,default_cmd,read,debug,0"
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
        command = "SDI-12,64,power,24,default_cmd,read,debug,0"
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
        command = "SDI-12,65,power,25,default_cmd,read,debug,0"
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
        command = "SDI-12,66,power,26,default_cmd,read,debug,0"
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
        command = "SDI-12,67,power,27,default_cmd,read,debug,0"
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


    #---------------------------Oxygen Sensor 1--------------------------------
    # Oxygen Sensor 1
    try:
        sensor_name = "oxy1"
        command = "SDI-12,50,power,28,delay,1000,default_cmd,read,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # "a+<OxygenLevel>±<temperature>+<pressure>"+<O2%>+<ErrorCode>"
        current_read=msg.split(',')[0:-1]
        o2_level = float(current_read[-5])
        o2_temp = float(current_read[-4])
        o2_baro = float(current_read[-3])
        o2_percent = float(current_read[-2])
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
    finally:
        pass

    #---------------------------Oxygen Sensor 2--------------------------------
    # Oxygen Sensor 2
    try:
        sensor_name = "oxy2"
        command = "SDI-12,51,power,29,delay,1000,default_cmd,read,debug,0"
        ard.write(command.encode())
        ard.flushInput()
        msg = ard.readline().decode() # "a+<OxygenLevel>±<temperature>+<pressure>"+<O2%>+<ErrorCode>"
        current_read=msg.split(',')[0:-1]
        o2_level = float(current_read[-5])
        o2_temp = float(current_read[-4])
        o2_baro = float(current_read[-3])
        o2_percent = float(current_read[-2])
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
    finally:
        pass


    #----------------------------Upload data -----------------------------------
    if (ard.isOpen()):
        ard.close()

    if (PUBLISH_TO_THINGSBOARD):
        try:
            # You can publish without starting a loop but failed publishes cannot be
            # accurately tracked.
            # Please use unique client_id for each client, and you should be able to use
            # same thingsboard device token for multiple clients.
            client = mqtt.Client(client_id="savage_#")
            client.username_pw_set(credential['access_token_savage#'])
            client.connect(credential['thingsboard_host'], 1883, 60)
            client.loop_start()
        except Exception:
            print("Failed to connect to thingsboard")
            # time.sleep(30)

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
    # try:
    #     GPIO.setwarnings(False)
    #     GPIO.cleanup()
    # except NameError:
    #     pass
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
