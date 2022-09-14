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
SERIAL_PORT = '/dev/ttyS0' # datalogger version 2 uses ttyS0
SERIAL_BAUD = 9600
#SERIAL_PORT = '/dev/serial/by-path/platform-3f980000.usb-usb-0:1.4:1.0' # datalogger version 1 uses ttyACM0
# PORT_SCALE = '/dev/serial/by-path/platform-20980000.usb-usb-0:1:1.0-port0' #the USB port connected to the scale
# PORT_SCALE = '/dev/serial/by-id/usb-FTDI_USB__-__Serial-if00-port0'
#HEAT_TIME = 24000

#---------------------- Configuration -------------------------

CSV_FILE_NAME = 'yarwun_column.csv'

field_name = ['scale',
            'MOIS 5',
            'MOIS 2 ',
            'MOIS 1 ',
            'MOIS 3',
            'MOIS 4',
            'MOIS 6',
            'MOIS 7',
            'MOIS 8',
            'MOIS 9',
            'MOIS 10'
            'Suction 1'
            'Suction 2'
            'Suction 3'
            'Suction 4'
            'Suction 5'
            'Suction 6'
            'Suction 7'
            'Suction 8'
            'temp',
            'humidity']

data_collected = dict((el,0.0) for el in field_name)

#---------------------------- Initiation --------------------------------------
if (PUBLISH_TO_THINGSBOARD):
    with open('/home/pi/pyduino/credential/thingsboard.json') as f:
        credential = json.load(f)

    try:
        client = mqtt.Client()
        client.username_pw_set(credential['access_token_yarwun_roof_a'])
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
            fid = open(CSV_FILE_NAME, 'w', buffering=0) # Open file for writing
            fid.write("Timestamp,Temp (C),Humidity (%),Analog1,Analog2,Analog3,Analog4,Analog5,Analog6,Analog7,Analog8,Analog9,Analog10\r\n") # Allocate column names
        else:
            fid = open(CSV_FILE_NAME, 'a', buffering=0) # Open file for appending
        # fid.write(time_now_local_str + '\r\n')
        fid.write(time_now_local_str)   # For standard csv format

    if SCREEN_DISPLAY:
        print(time_now_local_str)

    #---------------------------------Temp & Hum DHT22-----------------------------
    # DHT22 temp and humidity onboard
    try:
        ard.write("dht22,54,power,2,points,3,dummies,1,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read = msg.split(',')[0:-1]
        dht22_temp = float(current_read[-2])
        dht22_hum = float(current_read[-1])
        data_collected['temp'] = dht22_temp
        data_collected['humidity'] = dht22_hum
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            print("DHT22 reading failed, error: {0}".format(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER + DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print("Ambient Temp (C)" + ": " + str(dht22_temp))
            print("Ambient Humdity (%): " + str(dht22_hum))
        if SAVE_TO_CSV:
            # fid.write(time_now_local_str + DELIMITER + 'Temp' + DELIMITER + "C" + DELIMITER+DELIMITER + str(dht22_temp) + '\r\n')
            # fid.write(time_now_local_str + DELIMITER + 'Humidity' + DELIMITER + "%" + DELIMITER+DELIMITER + str(dht22_hum) + '\r\n')
            fid.write("{0}{1}{0}{2}".format(DELIMITER, dht22_temp, dht22_hum))


    #---------------------------Moisture Sensor 1--------------
    try:
        sensor_name = "MOS1"
        ard.write("analog,14,power,44,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['MOIS 1'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')


    #----------------------------Moisture sensor 2---------------------------------
    # MOIS 2
    try:
        sensor_name = "MOS2"
        ard.write("analog,13,power,43,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read = msg.split(',')[0:-1]
        data_collected['MOIS 2'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')


    #----------------------------Moisture sensor 3---------------------------------
    # MOIS 3
    try:
        sensor_name = "MOS3"
        ard.write("analog,11,power,41,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['MOIS 3'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')


    #---------------------------Moisture Sensor 4--------------------------------
    # MOIS 4
    try:
        sensor_name = "MOS4"
        ard.write("analog,10,power,40,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['MOIS 4'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #--------------------------Moisture Sensor 5-------------------------------
    # MOIS 5
    try:
        sensor_name = "MOS5"
        ard.write("analog,12,power,42,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['MOIS 5'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')


    #---------------------------Moisture Sensor 6--------------------------------
    # MOIS 6
    try:
        sensor_name = "MOS6"
        ard.write("analog,9,power,39,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['MOIS 6'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 7--------------------------------
    # MOIS 7
    try:
        sensor_name = "MOS7"
        ard.write("analog,8,power,38,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['MOIS 7'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 8--------------------------------
    # MOIS 8
    try:
        sensor_name = "MOS8"
        ard.write("analog,8,power,38,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['MOIS 8'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 9--------------------------------
    # MOIS 9
    try:
        sensor_name = "MOS9"
        ard.write("analog,8,power,38,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['MOIS 9'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Moisture Sensor 10--------------------------------
    # MOIS 10
    try:
        sensor_name = "MOS10"
        ard.write("analog,8,power,38,points,3,interval_mm,200,debug,0")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['MOIS 10'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')


    #---------------------------Suction Sensor 1--------------------------------
    # Suction 1
    try:
        sensor_name = "SUC1"
        ard.write("fred,286BD0CF0C000063,dgin,52,snpw,49,htpw,48,itv,1000,otno,5,debug,1")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['Suction 1'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 2--------------------------------
    # Suction 2
    try:
        sensor_name = "SUC2"
        ard.write("fred,285CABCF0C000016,dgin,52,snpw,49,htpw,48,itv,1000,otno,5,debug,1")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['Suction 2'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 3--------------------------------
    # Suction 3
    try:
        sensor_name = "SUC3"
        ard.write("fred,2864D0CF0C000047,dgin,52,snpw,49,htpw,48,itv,1000,otno,5,debug,1")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['Suction 3'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 4--------------------------------
    # Suction 4
    try:
        sensor_name = "SUC4"
        ard.write("fred,2859ABCF0C0000FD,dgin,52,snpw,49,htpw,48,itv,1000,otno,5,debug,1")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['Suction 4'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 5--------------------------------
    # Suction 5
    try:
        sensor_name = "SUC5"
        ard.write("fred,28214B330E000032,dgin,52,snpw,49,htpw,48,itv,1000,otno,5,debug,1")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['Suction 5'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 6--------------------------------
    # Suction 6
    try:
        sensor_name = "SUC6"
        ard.write("fred,2804D0CF0C000084,dgin,52,snpw,49,htpw,48,itv,1000,otno,5,debug,1")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['Suction 6'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 7--------------------------------
    # Suction 7
    try:
        sensor_name = "SUC7"
        ard.write("fred,288CABCF0C0000D2,dgin,52,snpw,49,htpw,48,itv,1000,otno,5,debug,1")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['Suction 7'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')

    #---------------------------Suction Sensor 8--------------------------------
    # Suction 8
    try:
        sensor_name = "SUC8"
        ard.write("fred,283204D00C000038,dgin,52,snpw,49,htpw,48,itv,1000,otno,5,debug,1")
        ard.flushInput()
        msg = ard.readline()
        current_read=msg.split(',')[0:-1]
        data_collected['Suction 8'] = float(current_read[2])
    except Exception:
        if SCREEN_DISPLAY:
            print(msg.rstrip())
            # print("{1} reading failed, error: {0}".format(sys.exc_info()[0], sensor_name))
            print(sensor_name + " reading failed, error: " + str(sys.exc_info()[0]))
        if SAVE_TO_CSV:
            fid.write(DELIMITER)
    else:
        if SCREEN_DISPLAY:
            print(sensor_name + ": " + msg.rstrip())
        if SAVE_TO_CSV:
            fid.write(DELIMITER + current_read[2])
            # fid.write(time_now_local_str + DELIMITER + field_name[field_name_id] + DELIMITER + msg.rstrip() + '\r\n')



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

    if SAVE_TO_CSV:
        fid.write("\r\n")
        if not fid.closed:
            fid.close()

    # print("begin to sleep")
    # time.sleep(SLEEP_TIME_SECONDS) # sleep to the next loop


except KeyboardInterrupt:
    pass
except Exception:
    traceback.print_exc()

finally:
    try:
        if (SAVE_TO_CSV):
            fid.close()
    except (NameError):
        pass
    if (ard.isOpen()):
        ard.close()
    if (PUBLISH_TO_THINGSBOARD and client.is_connected()):
        client.loop_stop()
        client.disconnect()

