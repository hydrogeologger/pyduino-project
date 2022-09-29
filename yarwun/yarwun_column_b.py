import os
import sys
import traceback
import time
import json
import serial
# import subprocess
import paho.mqtt.client as mqtt

"""
This is the code for the Yarwun project.
The peripherals include:
    10*moisture sensors
    8*suction sensors
    1*Pi CAM
"""
#------------------- Constants and Ports Information---------------------------

SCREEN_DISPLAY = True
SAVE_TO_CSV = True
PUBLISH_TO_THINGSBOARD = True
DELIMITER = ','
SLEEP_TIME_SECONDS = 60*30 # s
# SERIAL_PORT = '/dev/ttyS0' # datalogger version 2 uses ttyS0
SERIAL_PORT = '/dev/ttySOFT0' # datalogger version 2 uses ttyS0
# SERIAL_BAUD = 9600
SERIAL_BAUD = 4800
#SERIAL_PORT = '/dev/serial/by-path/platform-3f980000.usb-usb-0:1.4:1.0' # datalogger version 1 uses ttyACM0
# PORT_SCALE = '/dev/serial/by-path/platform-20980000.usb-usb-0:1:1.0-port0' #the USB port connected to the scale
# PORT_SCALE = '/dev/serial/by-id/usb-FTDI_USB__-__Serial-if00-port0'
#HEAT_TIME = 24000

#---------------------- Configuration -------------------------

CSV_FILE_NAME = 'yarwun_column.csv'

field_name = ['mos1',
            'mos2',
            'mos3',
            'mos4',
            'mos5',
            'mos6',
            'mos7',
            'mos8',
            'mos9',
            'mos10',
            'suct1',
            'suct2',
            'suct3',
            'suct4',
            'suct5',
            'suct6',
            'suct7',
            'suct8'
            # 'temp',
            # 'humidity'
            ]

data_collected = dict((el,0.0) for el in field_name)

#---------------------------- Initiation --------------------------------------
if (PUBLISH_TO_THINGSBOARD):
    with open('/home/pi/pyduino/credential/thingsboard.json') as f:
        credential = json.load(f)

    try:
        client = mqtt.Client()
        client.username_pw_set(credential['access_token_yarwun_roof_b'])
        client.connect(credential['thingsboard_host'], 1883, 60)
        client.loop_start()
    except Exception:
        print("Failed to connect to thingsboard")
        # time.sleep(30)

try:
    # while True:
    ard = serial.Serial(port=SERIAL_PORT, baudrate=SERIAL_BAUD, timeout=60)
    # time.sleep(3)

    time_now = time.time()
    time_now_local = time.localtime(time_now)
    seconds_since_epoch = int(round(time_now * 1000))
    time_now_local_str = time.strftime("%Y-%m-%d %H:%M:%S", time_now_local)

    # Open file for appending
    if SAVE_TO_CSV:
        # Check if file exist to add column headings
        if not os.path.isfile(CSV_FILE_NAME):
            csv_fid = open(CSV_FILE_NAME, 'w', buffering=0) # Open file for writing
            csv_fid.write("Timestamp,Temp (C),Humidity (%),MOS1 (ADC),MOS2 (ADC),MOS3 (ADC)" \
                        ",MOS4 (ADC),MOS5 (ADC),MOS6 (ADC),MOS7 (ADC),MOS8 (ADC),MOS9 (ADC),MOS10 (ADC)" \
                        ",SUCT1 (C),SUCT2 (C),SUCT3 (C),SUCT4 (C),SUCT5 (C),SUCT6 (C),SUCT7 (C),SUCT8 (C)" \
                        "\r\n") # Allocate column names
        else:
            csv_fid = open(CSV_FILE_NAME, 'a', buffering=0) # Open file for appending
        # csv_fid.write(time_now_local_str + '\r\n')
        csv_fid.write(time_now_local_str)   # For standard csv format

    if SCREEN_DISPLAY:
        print(time_now_local_str)

    #---------------------------------Temp & Hum DHT22-----------------------------
    # DHT22 temp and humidity onboard
    # Don't need it as already getting from vaisala weather station process
    # try:
    #     ard.write("dht22,54,power,2,points,3,dummies,1,interval_mm,200,debug,0")
    #     ard.flushInput()
    #     msg = ard.readline()
    #     current_read = msg.split(',')[0:-1]
    #     dht22_temp = float(current_read[-2])
    #     dht22_hum = float(current_read[-1])
    #     data_collected['temp'] = dht22_temp
    #     data_collected['humidity'] = dht22_hum
    # except Exception:
    #     if SCREEN_DISPLAY:
    #         print(msg.rstrip())
    #         print("DHT22 reading failed, error: {0}".format(sys.exc_info()[0]))
    #     if SAVE_TO_CSV:
    #         csv_fid.write(DELIMITER + DELIMITER)
    # else:
    #     if SCREEN_DISPLAY:
    #         print("Ambient Temp (C)" + ": " + str(dht22_temp))
    #         print("Ambient Humdity (%): " + str(dht22_hum))
    #     if SAVE_TO_CSV:
    #         # csv_fid.write(time_now_local_str + DELIMITER + 'Temp' + DELIMITER + "C" + DELIMITER+DELIMITER + str(dht22_temp) + '\r\n')
    #         # csv_fid.write(time_now_local_str + DELIMITER + 'Humidity' + DELIMITER + "%" + DELIMITER+DELIMITER + str(dht22_hum) + '\r\n')
    #         csv_fid.write("{0}{1}{0}{2}".format(DELIMITER, dht22_temp, dht22_hum))


    #---------------------------Moisture Sensor 1--------------
    # Moisture Sensor 1
    try:
        sensor_name = "mos1"
        ard.write("analog,1,power,38,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['mos1'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + current_read[2])
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')


    #----------------------------Moisture sensor 2---------------------------------
    # Moisture Sensor 2
    try:
        sensor_name = "mos2"
        ard.write("analog,2,power,39,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read = msg.split(',')[0:-1]
        data_collected['mos2'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + current_read[2])
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')


    #----------------------------Moisture sensor 3---------------------------------
    # Moisture Sensor 3
    try:
        sensor_name = "mos3"
        ard.write("analog,3,power,40,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['mos3'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + current_read[2])
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')


    #---------------------------Moisture Sensor 4--------------------------------
    # Moisture Sensor 4
    try:
        sensor_name = "mos4"
        ard.write("analog,4,power,41,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['mos4'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + current_read[2])
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #--------------------------Moisture Sensor 5-------------------------------
    # Moisture Sensor 5
    try:
        sensor_name = "mos5"
        ard.write("analog,5,power,42,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['mos5'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + current_read[2])
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')


    #---------------------------Moisture Sensor 6--------------------------------
    # Moisture Sensor 6
    try:
        sensor_name = "mos6"
        ard.write("analog,6,power,43,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['mos6'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + current_read[2])
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 7--------------------------------
    # Moisture Sensor 7
    try:
        sensor_name = "mos7"
        ard.write("analog,7,power,44,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['mos7'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + current_read[2])
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 8--------------------------------
    # Moisture Sensor 8
    try:
        sensor_name = "mos8"
        ard.write("analog,8,power,45,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['mos8'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + current_read[2])
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 9--------------------------------
    # Moisture Sensor 9
    try:
        sensor_name = "mos9"
        ard.write("analog,9,power,46,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['mos9'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + current_read[2])
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 10--------------------------------
    # Moisture Sensor 10
    try:
        sensor_name = "mos10"
        ard.write("analog,10,power,47,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['mos10'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + current_read[2])
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')


    #---------------------------Suction Sensor 1--------------------------------
    # Suction Sensor 1
    try:
        sensor_name = "suct1"
        ard.write("fred,288CABCF0C0000D2,dgin,19,snpw,22,htpw,30,itv,1000,otno,5,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
        data_collected['suct1'] = temp_diff
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 2--------------------------------
    # Suction Sensor 2
    try:
        sensor_name = "suct2"
        ard.write("fred,28264B330E0000B7,dgin,18,snpw,23,htpw,31,itv,1000,otno,5,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
        data_collected['suct2'] = temp_diff
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 3--------------------------------
    # Suction Sensor 3
    try:
        sensor_name = "suct3"
        ard.write("fred,2859ABCF0C0000FD,dgin,17,snpw,24,htpw,32,itv,1000,otno,5,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
        data_collected['suct3'] = temp_diff
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 4--------------------------------
    # Suction Sensor 4
    try:
        sensor_name = "suct4"
        ard.write("fred,285CABCF0C000016,dgin,16,snpw,25,htpw,33,itv,1000,otno,5,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
        data_collected['suct4'] = temp_diff
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 5--------------------------------
    # Suction Sensor 5
    try:
        sensor_name = "suct5"
        ard.write("fred,2804D0CF0C000084,dgin,15,snpw,26,htpw,34,itv,1000,otno,5,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
        data_collected['suct5'] = temp_diff
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 6--------------------------------
    # Suction Sensor 6
    try:
        sensor_name = "suct6"
        ard.write("fred,283204D00C000038,dgin,14,snpw,27,htpw,35,itv,1000,otno,5,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
        data_collected['suct6'] = temp_diff
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 7--------------------------------
    # Suction Sensor 7
    try:
        sensor_name = "suct7"
        ard.write("fred,28214B330E000032,dgin,3,snpw,28,htpw,36,itv,1000,otno,5,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
        data_collected['suct7'] = temp_diff
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 8--------------------------------
    # Suction Sensor 8
    try:
        sensor_name = "suct8"
        ard.write("fred,2864D0CF0C000047,dgin,4,snpw,29,htpw,37,itv,1000,otno,5,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        temp_baseline = float(current_read[-11])
        temp_diff = float(current_read[-6]) - temp_baseline
        data_collected['suct8'] = temp_diff
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name.upper()))
            print(sensor_name.upper() + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name.upper() + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            csv_fid.write(DELIMITER + str(temp_diff))
            # csv_fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')



    #----------------------------Upload data -----------------------------------
    if (ard.isOpen()):
        ard.close()

    if (PUBLISH_TO_THINGSBOARD):
        json_data = {"ts":seconds_since_epoch, "values": data_collected}
        # json_data = data_collected
        try:
            # Result is in tuple (rc, mid) of MQTTMessageInfo class
            publish_result = client.publish('v1/devices/me/telemetry', payload=json.dumps(json_data), qos=1)
            # publish_result.wait_for_publish(timeout=1)
            # print(publish_result.is_published())
            # if (not publish_result.is_published()):
            if (publish_result.rc != mqtt.MQTT_ERR_SUCCESS):
                if SCREEN_DISPLAY:
                    print(mqtt.error_string(publish_result.rc))
                json_filename = "tsqueue_testbench_basin.json"
                listObj = []
                # Read json file
                if (os.path.isfile(json_filename)):
                    with open(json_filename) as json_file:
                        listObj = json.load(json_file)
                # Verify existing list
                # print(listObj)
                # print(type(listObj))
                # print(json.dumps(listObj))
                # print(json.dumps(listObj[0]))
                listObj.append(json_data)
                with open(json_filename, 'w') as json_file:
                    json.dump(listObj, json_file, indent=4, separators=(",",": "))
        except (ValueError, RuntimeError) as error:
            if SCREEN_DISPLAY:
                print(error)
        finally:
            if SCREEN_DISPLAY:
                print(publish_result)
                print(json_data)

    if SCREEN_DISPLAY:
        print("")

except KeyboardInterrupt:
    if SAVE_TO_CSV:
        csv_fid.write("\r\n")
except Exception:
    traceback.print_exc()

else:
    if SAVE_TO_CSV:
        csv_fid.write("\r\n")
        if not csv_fid.closed:
            csv_fid.close()

    # print("begin to sleep")
    # time.sleep(SLEEP_TIME_SECONDS) # sleep to the next loop
finally:
    try:
        if (SAVE_TO_CSV):
            csv_fid.close()
    except (NameError):
        pass
    if (ard.isOpen()):
        ard.close()
    if (PUBLISH_TO_THINGSBOARD and client.is_connected()):
        client.loop_stop()
        client.disconnect()

