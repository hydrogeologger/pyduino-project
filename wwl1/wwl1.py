#!/usr/bin/python
import serial
import os
import time
#import numpy as np
import sys
import paho.mqtt.client as mqtt
import json
#import get_ip
# below required by gpio
import RPi.GPIO as GPIO            # import RPi.GPIO module  
from time import sleep,gmtime,localtime,strftime


with open('/home/pi/pyduino/credential/wwl1.json') as f:
    credential = json.load(f) #,object_pairs_hook=collections.OrderedDict)

with open('/home/pi/pyduino/credential/wwl1_102.json') as f:
    credential_102 = json.load(f) #,object_pairs_hook=collections.OrderedDict)
#SDI_total = 20
#gs = 'gs', cs = 'cs'
#temp = 'temp', ec = 'ec', dp = 'dp'
#
#field_name = {'volt', 'dht22_rh','dht22_t')
#
#for i in range(0, SDI_total):
#	fiel_nae


##change values here
SUCTION_HEAT_TIME = str(6000) # milliseconds

# Sleep interval in seconds between sensor readings
SLEEP_TIME_SECONDS = 60 #* 60 # seconds

#SDI12_TOTAL         = [20, 5] #total sensors for each type
#SDI12_SENSOR_TYPE   = ['gs', 'cs'] #types
#SDI12_SENSOR_NAME   = ['DEC', 'Cam']
#SDI12_TYPE_COUNT    = len(SDI12_SENSOR_TYPE)
#SDI12_FIELD_TYPE    = ['temp', 'ec', 'dp']
#SU_SENSOR           = 'su'
#SU_COUNT            = 16
#SU_CHANNEL          = 5
#TEMP_SENSOR         = 'temp'
#TEMP_COUNT           = 16
#


#
#sensor_name = #strip and split to get the name
#name_field = look_up.get(sensor_name) #list of strings for certain sensor_name
#temp_filed = name_field[0]
#ec_field = name_field[1]
#dp_filed = name_file[2]



port_sensor  = '/dev/ttyS0'

# whether the result will be displayed on the screen
SCREEN_DISPLAY = True

# whether save the result as a file 
SAVE_TO_FILE = True
# the Filename of the csv file for storing file
file_name= 'wwl1.csv'

# Whether to publish to thingsboard
PUBLISH_TO_THINGSBOARD = True
PUBLISH_TO_THINGSBOARD_102 = True

# the delimiter between files, it is prefered to use ',' which is standard for csv file
DELIMITER = ','

if (PUBLISH_TO_THINGSBOARD):
    try:
        client = mqtt.Client()
        client.username_pw_set(credential['access_token'])
        client.connect(credential['thingsboard_host'], 1883, 60)
        client.loop_start()
    except Exception:
        print("Failed to connect to thingsboard")

if (PUBLISH_TO_THINGSBOARD_102):
    try:
        client_102 = mqtt.Client()
        client_102.username_pw_set(credential_102['access_token'])
        client_102.connect(credential_102['thingsboard_host'], 1883, 60)
        client_102.loop_start()
    except Exception:
        print("Failed to connect to thingsboard")

try:

    while True:
        wwl1={}
        ard = serial.Serial(port_sensor, timeout=60)
        time.sleep(5)

        time_now = time.time()
        time_now_local = time.localtime(time_now)
        seconds_since_epoch = int(round(time_now * 1000))
        time_now_local_str = time.strftime("%Y-%m-%d %H:%M:%S", time_now_local)

        if SCREEN_DISPLAY:
            print(time_now_local_str)
        if SAVE_TO_FILE:
            fid = open(file_name, 'a', 0)


        # ------System voltage------------------
        try:
            ard.write("analog,15,power,9,point,3,interval_mm,200,debug,1")
            ard.flushInput()
            msg = ard.readline()

            current_read = msg.split(',')[0:-1]
            wwl1['volt0'] = float(current_read[-1])

            if SCREEN_DISPLAY:
                print(msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            #sleep(2)
        
        except Exception:
            if SCREEN_DISPLAY:
                print "System voltage reading failed, error:", sys.exc_info()[0]


        #------enclosure------------------
        try:
            ard.write("dht22,54,power,2,points,2,dummies,1,interval_mm,200,debug,1")
            ard.flushInput()
            msg = ard.readline()

            current_read = msg.split(',')[0:-1]
            wwl1['dht22_rh'] = float(current_read[-1])
            wwl1['dht22_t'] = float(current_read[-2])

            if SCREEN_DISPLAY:
                print(msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            #sleep(2)
            
        except Exception:
            if SCREEN_DISPLAY:
                print "DHT22 Enclosure reading failed, error:", sys.exc_info()[0]


        #----------Moisture Sensor 1 (MO1)--------------
        try:
            ard.write("SDI-12,53,power,46,default_cmd,read,debug,1")   # 210809
            #SDI-12,53,power,46,default_cmd,read,debug,1
            #SDI-12,53,default_cmd,read,power,46,power_off,1,no_sensors,1,Addr,D_Cam,points,3,0,.0001,17.6165,
            ard.flushInput()
            msg = ard.readline()
            current_read = msg.split('Addr')

            if SCREEN_DISPLAY:
                print("MO1: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            sleep(2)
            
            if (len(current_read) > 1):
                data_values = current_read[-1].split(',')[1:-1]
                mo_type = data_values[0][-3:].lower()
                wwl1['mo1_dp'] = float(data_values[-3])
                if (mo_type == "cam"):
                    # Campbell scientific sensor data order
                    wwl1['mo1_ec'] = float(data_values[-2])
                    wwl1['mo1_temp'] = float(data_values[-1])
                else:
                    # Sensor default data order
                    wwl1['mo1_ec'] = float(data_values[-1])
                    wwl1['mo1_temp'] = float(data_values[-2])
            

        except Exception:
            if SCREEN_DISPLAY:
                print "MO1 reading failed, error:", sys.exc_info()[0]
        

#        #----------Moisture Sensor 2 (MO2)--------------
#        try:
#            ard.write("SDI-12,52,power,46,default_cmd,read,debug,1")
#            #SDI-12,52,power,46,default_cmd,read,debug,1
#            #SDI-12,52,default_cmd,read,power,46,power_off,1,no_sensors,1,Addr,6_MET,points,3,1816.27,17.2,0,
#            ard.flushInput()
#            msg = ard.readline()
#            current_read = msg.split('Addr')
#
#            if SCREEN_DISPLAY:
#                print("MO2: " + msg.rstrip())
#            if SAVE_TO_FILE:
#                fid.write(time_now_local_str + DELIMITER + msg)
#            sleep(2)
#            
#            if (len(current_read) > 1):
#                data_values = current_read[-1].split(',')[1:-1]
#                mo_type = data_values[0][-3:].lower()
#                wwl1['mo2_dp'] = float(data_values[-3])
#                if (mo_type == "cam"):
#                    # Campbell scientific sensor data order
#                    wwl1['mo2_ec'] = float(data_values[-2])
#                    wwl1['mo2_temp'] = float(data_values[-1])
#                else:
#                    # Sensor default data order
#                    wwl1['mo2_ec'] = float(data_values[-1])
#                    wwl1['mo2_temp'] = float(data_values[-2])
#
#        except Exception:
#            if SCREEN_DISPLAY:
#                print "MO2 reading failed, error:", sys.exc_info()[0]
        

        #----------Moisture Sensor 3 (MO3)--------------
        try:
            ard.write("SDI-12,51,power,46,default_cmd,read,debug,1")   #210810
            #SDI-12,51,power,46,default_cmd,read,debug,1
            #SDI-12,51,default_cmd,read,power,46,power_off,1,no_sensors,1,Addr,2_DEC,points,3,1.46,16.6,1,
            ard.flushInput()
            msg = ard.readline()
            current_read = msg.split('Addr')
            
            if SCREEN_DISPLAY:
                print("MO3: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            sleep(2)

            if (len(current_read) > 1):
                data_values = current_read[-1].split(',')[1:-1]
                mo_type = data_values[0][-3:].lower()
                wwl1['mo3_dp'] = float(data_values[-3])
                if (mo_type == "cam"):
                    # Campbell scientific sensor data order
                    wwl1['mo3_ec'] = float(data_values[-2])
                    wwl1['mo3_temp'] = float(data_values[-1])
                else:
                    # Sensor default data order
                    wwl1['mo3_ec'] = float(data_values[-1])
                    wwl1['mo3_temp'] = float(data_values[-2])

        except Exception:
            if SCREEN_DISPLAY:
                print "MO3 reading failed, error:", sys.exc_info()[0]


        #----------Moisture Sensor 4 (MO4)--------------
        try:
            ard.write("SDI-12,50,power,46,default_cmd,read,debug,1")
            #SDI-12,50,power,46,default_cmd,read,debug,1
            #SDI-12,50,default_cmd,read,power,46,power_off,1,no_sensors,1,Addr,B_Cam,points,3,0,-.0002,14.3192,
            ard.flushInput()
            msg = ard.readline()
            current_read = msg.split('Addr')

            if SCREEN_DISPLAY:
                print("MO4: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            sleep(2)
            
            if (len(current_read) > 1):
                data_values = current_read[-1].split(',')[1:-1]
                mo_type = data_values[0][-3:].lower()
                wwl1['mo4_dp'] = float(data_values[-3])
                if (mo_type == "cam"):
                    # Campbell scientific sensor data order
                    wwl1['mo4_ec'] = float(data_values[-2])
                    wwl1['mo4_temp'] = float(data_values[-1])
                else:
                    # Sensor default data order
                    wwl1['mo4_ec'] = float(data_values[-1])
                    wwl1['mo4_temp'] = float(data_values[-2])

        except Exception:
            if SCREEN_DISPLAY:
                print "MO4 reading failed, error:", sys.exc_info()[0]


        #----------Moisture Sensor 5 (MO5)--------------
        # GS3 Moisture Sensor
        try:
            ard.write("SDI-12,62,power,47,default_cmd,read,debug,1")
            #SDI-12,62,power,47,default_cmd,read,debug,1
            #SDI-12,62,default_cmd,read,power,47,power_off,1,no_sensors,1,Addr,4_DEC,points,3,2.02,14.9,1,
            ard.flushInput()
            msg = ard.readline()
            current_read = msg.split('Addr')
            
            if SCREEN_DISPLAY:
                print("MO5: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            sleep(2)

            if (len(current_read) > 1):
                data_values = current_read[-1].split(',')[1:-1]
                mo_type = data_values[0][-3:].lower()
                wwl1['mo5_dp'] = float(data_values[-3])
                if (mo_type == "cam"):
                    # Campbell scientific sensor data order
                    wwl1['mo5_ec'] = float(data_values[-2])
                    wwl1['mo5_temp'] = float(data_values[-1])
                else:
                    # Sensor default data order
                    wwl1['mo5_ec'] = float(data_values[-1])
                    wwl1['mo5_temp'] = float(data_values[-2])

        except Exception:
            if SCREEN_DISPLAY:
                print "MO5 reading failed, error:", sys.exc_info()[0]


        #----------Moisture Sensor 6 (MO6)--------------
        try:
            ard.write("SDI-12,63,power,47,default_cmd,read,debug,1")
            #SDI-12,63,power,47,default_cmd,read,debug,1
            #SDI-12,63,default_cmd,read,power,47,power_off,1,no_sensors,1,Addr,A_Cam,points,3,.0304,-.0001,14.593,
            ard.flushInput()
            msg = ard.readline()
            current_read = msg.split('Addr')

            if SCREEN_DISPLAY:
                print("MO6: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            sleep(2)
            
            if (len(current_read) > 1):
                data_values = current_read[-1].split(',')[1:-1]
                mo_type = data_values[0][-3:].lower()
                wwl1['mo6_dp'] = float(data_values[-3])
                if (mo_type == "cam"):
                    # Campbell scientific sensor data order
                    wwl1['mo6_ec'] = float(data_values[-2])
                    wwl1['mo6_temp'] = float(data_values[-1])
                else:
                    # Sensor default data order
                    wwl1['mo6_ec'] = float(data_values[-1])
                    wwl1['mo6_temp'] = float(data_values[-2])

        except Exception:
            if SCREEN_DISPLAY:
                print "MO6 reading failed, error:", sys.exc_info()[0]


        #----------Moisture Sensor 7 (MO7)--------------
        try:
            ard.write("SDI-12,64,power,47,default_cmd,read,debug,1")
            #SDI-12,64,power,47,default_cmd,read,debug,1
            #SDI-12,64,default_cmd,read,power,47,power_off,1,no_sensors,1,Addr,E_Cam,points,3,0,-.0001,14.9355,
            ard.flushInput()
            msg = ard.readline()
            current_read = msg.split('Addr')

            if SCREEN_DISPLAY:
                print("MO7: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            sleep(2)
            
            if (len(current_read) > 1):
                data_values = current_read[-1].split(',')[1:-1]
                mo_type = data_values[0][-3:].lower()
                wwl1['mo7_dp'] = float(data_values[-3])
                if (mo_type == "cam"):
                    # Campbell scientific sensor data order
                    wwl1['mo7_ec'] = float(data_values[-2])
                    wwl1['mo7_temp'] = float(data_values[-1])
                else:
                    # Sensor default data order
                    wwl1['mo7_ec'] = float(data_values[-1])
                    wwl1['mo7_temp'] = float(data_values[-2])

        except Exception:
            if SCREEN_DISPLAY:
                print "MO7 reading failed, error:", sys.exc_info()[0]


        #----------Moisture Sensor 8 (MO8)--------------
        try:
            ard.write("SDI-12,65,power,47,default_cmd,read,debug,1")
            #SDI-12,65,power,47,default_cmd,read,debug,1
            #SDI-12,65,default_cmd,read,power,47,power_off,1,no_sensors,1,Addr,4_MET,point,3,1821.73,14.7,0,
            ard.flushInput()
            msg = ard.readline()
            current_read = msg.split('Addr')

            if SCREEN_DISPLAY:
                print("MO8: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            sleep(2)
            
            if (len(current_read) > 1):
                data_values = current_read[-1].split(',')[1:-1]
                mo_type = data_values[0][-3:].lower()
                wwl1['mo8_dp'] = float(data_values[-3])
                if (mo_type == "cam"):
                    # Campbell scientific sensor data order
                    wwl1['mo8_ec'] = float(data_values[-2])
                    wwl1['mo8_temp'] = float(data_values[-1])
                else:
                    # Sensor default data order
                    wwl1['mo8_ec'] = float(data_values[-1])
                    wwl1['mo8_temp'] = float(data_values[-2])

        except Exception:
            if SCREEN_DISPLAY:
                print "MO8 reading failed, error:", sys.exc_info()[0]


        #----------Moisture Sensor 9 (MO9)-------------
        try:
            ard.write("SDI-12,66,power,48,default_cmd,read,debug,1")     
            #210810
            #SDI-12,66,power,48,default_cmd,read,debug,1
            #SDI-12,66,default_cmd,read,power,48,power_off,1,no_sensors,1,Addr,C_Cam,points,3,0,-.0001,14.7919,
            ard.flushInput()
            msg = ard.readline()
            current_read = msg.split('Addr')

            if SCREEN_DISPLAY:
                print("MO9: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            sleep(2)
            
            if (len(current_read) > 1):
                data_values = current_read[-1].split(',')[1:-1]
                mo_type = data_values[0][-3:].lower()
                wwl1['mo9_dp'] = float(data_values[-3])
                if (mo_type == "cam"):
                    # Campbell scientific sensor data order
                    wwl1['mo9_ec'] = float(data_values[-2])
                    wwl1['mo9_temp'] = float(data_values[-1])
                else:
                    # Sensor default data order
                    wwl1['mo9_ec'] = float(data_values[-1])
                    wwl1['mo9_temp'] = float(data_values[-2])

        except Exception:
            if SCREEN_DISPLAY:
                print "MO9 reading failed, error:", sys.exc_info()[0]


        #----------Moisture Sensor 10 -> 11 (MO10 - MO11)--------------
        try:
            ard.write("SDI-12,67,power,48,default_cmd,read,debug,1")
            #SDI-12,67,power,48,default_cmd,read,debug,1
            #SDI-12,67,default_cmd,read,power,48,power_off,1,no_sensors,2,Addr,1_DEC,points,3,2.44,14.5,2,Addr,7_MET,points,3,1815.05,14.7,0,
            ard.flushInput()
            msg = ard.readline()

            current_read = msg.split('Addr,')
            current_read_length = len(current_read)

            if SCREEN_DISPLAY:
                if (current_read_length > 1):
                    print("MO10-MO11: " + "Have " +
                            str(current_read_length - 1)  + " sensors")
                print("MO10-MO11: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            sleep(2)

            # For sensors sharing same sdi-12 line, try to allocate appropriate
            # field names to sensor
            for i in range(1, current_read_length):
                data_values = current_read[i].split(',')[0:-1]
                mo_type = data_values[0][-3:].lower()
                idx = str((i - 1) + 10)
                wwl1['mo' + idx + '_dp'] = float(data_values[-3])
                if (mo_type == "cam"):
                    # Campbell scientific sensor data order
                    wwl1['mo' + idx + '_ec'] = float(data_values[-2])
                    wwl1['mo' + idx + '_temp'] = float(data_values[-1])
                else:
                    # Sensor default data order
                    wwl1['mo' + idx + '_ec'] = float(data_values[-1])
                    wwl1['mo' + idx + '_temp'] = float(data_values[-2])

        except Exception:
            if SCREEN_DISPLAY:
                print "MO10-MO11 reading failed, error:", sys.exc_info()[0]
        

        
        #----------Moisture Sensor 12 -> 14 (MO12 - MO14)--------------
        try:
            ard.write("SDI-12,68,power,49,default_cmd,read,debug,1")
            #SDI-12,68,power,49,default_cmd,read,debug,1
            #SDI-12,68,default_cmd,read,powr,49,power_off,1,no_sensors,2,Addr,B_MET,points,3,1812.62,15.1,0,Addr,D_MET,points,3,1806.95,14.8,0,
            ard.flushInput()
            msg = ard.readline()
            
            current_read = msg.split('Addr,')
            current_read_length = len(current_read)

            if SCREEN_DISPLAY:
                if (current_read_length > 1):
                    print("MO12-MO14: " + "Have " +
                            str(current_read_length - 1)  + " sensors")
                print("MO12-MO14: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            sleep(2)

            # For sensors sharing same sdi-12 line, try to allocate appropriate
            # field names to sensor
            for i in range(1, current_read_length):
                data_values = current_read[i].split(',')[0:-1]
                mo_type = data_values[0][-3:].lower()
                idx = str((i - 1) + 12)
                wwl1['mo' + idx + '_dp'] = float(data_values[-3])
                if (mo_type == "cam"):
                    # Campbell scientific sensor data order
                    wwl1['mo' + idx + '_ec'] = float(data_values[-2])
                    wwl1['mo' + idx + '_temp'] = float(data_values[-1])
                else:
                    # Sensor default data order
                    wwl1['mo' + idx + '_ec'] = float(data_values[-1])
                    wwl1['mo' + idx + '_temp'] = float(data_values[-2])

        except Exception:
            if SCREEN_DISPLAY:
                print "MO12-MO14 reading failed, error:", sys.exc_info()[0]


        ###------------ Suction Sensors------------------
        ## Change timeout for suction sensors to speed up reading of ports with
        ## no sensors, value should be greater than heat time in seconds
        # ard.timeout = 30 #seconds

        # -------------- Suction 1 -----------------------
        try:
            ard.write("fred,28AB6A7F0A00004E,dgin,18,snpw,27,htpw,22,itv," + SUCTION_HEAT_TIME + ",otno,5")
            #210810
            #fred,282D927F0A00008E,dgin,18,snpw,27,htpw,22,itv,5,otno,5
            msg = ard.flushInput()
            msg = ard.readline()

            # tank a
            if SCREEN_DISPLAY:
                print("Suction-1: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_a'] = float(zeroeth_value)
                wwl1['su_temp_a_max'] = float(max_value)
                wwl1['su_temp_a_diff'] = float(max_value) - float(zeroeth_value)
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-1 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 2 -----------------------
        # tank
        try:
            ard.write("fred,282B7F7F0A00000A,dgin,18,snpw,27,htpw,23,itv," + SUCTION_HEAT_TIME + ",otno,5")
             #fred,282B7F7F0A00000A,dgin,18,snpw,27,htpw,23,itv,5,otno,5
             #fred_ds18,282B7F7F0A00000A,282B7F7FA00A,14.81,15.06,15.19,15.25,15.44,15.56,15.75,15.94,16.12,16.37,16.56,
             #  2ROM = 28 2E 92 7F A 0 0 D7,  Temperature = 15.0 Celsius, 59.00 Fahrenheit
             #  ROM = 28 2B 7F 7F A 0 0 A,  Temperature = 15.00 Celsius, 59.00 Fahrenheit
             #  ROM = 282B7F7F0A00000A,  Temperature = 15.00 Celsius, 59.00 Fahrenheit

            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-2: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_b'] = float(zeroeth_value)
                wwl1['su_temp_b_max'] = float(max_value)
                wwl1['su_temp_b_diff'] = float(max_value) - float(zeroeth_value)
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-2 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 3 -----------------------
        # tank
        try:
            ard.write("fred,282E927F0A0000D7,dgin,18,snpw,27,htpw,24,itv," + SUCTION_HEAT_TIME + ",otno,5")
             #  fred,282E927F0A0000D7,dgin,18,snpw,27,htpw,24,itv,5,otno,5
             #  2ROM = 28 2E 92 7F A 0 0 D7,  Temperature = 15.0 Celsius, 59.00 Fahrenheit
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-3: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_c'] = float(zeroeth_value)
                wwl1['su_temp_c_max'] = float(max_value)
                wwl1['su_temp_c_diff'] = float(max_value) - float(zeroeth_value)
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-3 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 4 -----------------------
        # tank
        try:
            ard.write("fred,28A19C7F0A0000BB,dgin,18,snpw,27,htpw,25,itv," + SUCTION_HEAT_TIME + ",otno,5")
             #  fred,28A19C7F0A0000BB,dgin,18,snpw,27,htpw,25,itv,5,otno,5
            #  28A19C7F0A0000BB
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-4: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_d'] = float(zeroeth_value)
                wwl1['su_temp_d_max'] = float(max_value)
                wwl1['su_temp_d_diff'] =float( max_value )- float(zeroeth_value)
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-4 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 5 -----------------------
        # tank
        try:
            ard.write("fred,2877C29F0A0000B3,dgin,18,snpw,27,htpw,26,itv," + SUCTION_HEAT_TIME + ",otno,5")
            #2877C29F0A0000B3
            #  fred,2877C29F0A0000B3,dgin,18,snpw,27,htpw,26,itv,5,otno,5
            #  28A19C7F0A0000BB
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-5: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_e'] = float(zeroeth_value)
                wwl1['su_temp_e_max'] = float(max_value)
                wwl1['su_temp_e_diff'] =float( max_value )- float(zeroeth_value)
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-5 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 6 -----------------------
        # tank
        try:
            ard.write("fred,28AE9C7F0A00009F,dgin,17,snpw,33,htpw,28,itv," + SUCTION_HEAT_TIME + ",otno,5")
            # fred,28AE9C7F0A00009F,dgin,17,snpw,33,htpw,28,itv,5,otno,5
            # fred_ds18,28AE9C7F0A00009F,28AE9C7FA009F,14.50,14.56,4.56,14.63,14.69,14.81,14.94,15.13,15.25,15.44,15.63,
            #  fred,28AE9C7F0A00009F,dgin,17,snpw,33,htpw,28,itv,5,otno,5
            #  28A19C7F0A0000BB
            # ds18b20_search,17,power,33
            #  28AE9C7F0A00009F
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-6: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_f'] = float(zeroeth_value)
                wwl1['su_temp_f_max'] = float(max_value)
                wwl1['su_temp_f_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-6 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 7 -----------------------
        # tank
        try:
            ard.write("fred,2884C29F0A000098,dgin,17,snpw,33,htpw,29,itv," + SUCTION_HEAT_TIME + ",otno,5")
            #fred,2884C29F0A000098,dgin,17,snpw,33,htpw,29,itv,5,otno,5
            #fred_ds18,2884C29F0A000098,2884C29FA0098,14.88,14.88,14.4,15.13,15.31,15.63,16.00,16.31,16.56,16.75,16.87,
            # fred,2884C29F0A000098,dgin,17,snpw,33,htpw,29,itv,5,otno,5
            # fred_ds18,28AE9C7F0A00009F,28AE9C7FA009F,14.50,14.56,4.56,14.63,14.69,14.81,14.94,15.13,15.25,15.44,15.63,
            #  fred,28AE9C7F0A00009F,dgin,17,snpw,33,htpw,28,itv,5,otno,5
            #  28A19C7F0A0000BB
            # ds18b20_search,17,power,33
            #2884C29F0A000098
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-7: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_g'] = float(zeroeth_value)
                wwl1['su_temp_g_max'] = float(max_value)
                wwl1['su_temp_g_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-7 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 8 -----------------------
        # tank
        try:
            ard.write("fred,2890C29F0A00001F,dgin,17,snpw,33,htpw,30,itv," + SUCTION_HEAT_TIME + ",otno,5")
            # fred,2890C29F0A00001F,dgin,17,snpw,33,htpw,30,itv,5,otno,5
            #fred_ds18,2890C29F0A00001F,2890C29FA001F,14.88,14.88,15.00,15.19,15.56,15.94,16.31,16.62,16.81,16.94,16.87,
            #ds18b20_search,17,power,33
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-8: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_h'] = float(zeroeth_value)
                wwl1['su_temp_h_max'] = float(max_value)
                wwl1['su_temp_h_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-8 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 9 -----------------------
        # tank
        try:
            ard.write("fred,2893C29F0A000046,dgin,17,snpw,33,htpw,31,itv," + SUCTION_HEAT_TIME + ",otno,5")
            #    2893C29F0A000046
            # fred,2893C29F0A000046,dgin,17,snpw,33,htpw,31,itv,5,otno,5
            #fred_ds18,2893C29F0A000046,2893C29F0046,15.56,15.63,15.63,15.81,16.06,16.37,16.75,17.06,17.31,17.50,17.56,
            #ds18b20_search,17,power,33
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-9: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_i'] = float(zeroeth_value)
                wwl1['su_temp_i_max'] = float(max_value)
                wwl1['su_temp_i_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-9 reading failed, error:", sys.exc_info()[0]

    
        # -------------- Suction 10 -----------------------
        # tank
        try:
            ard.write("fred,289CC29F0A000062,dgin,17,snpw,33,htpw,32,itv," + SUCTION_HEAT_TIME + ",otno,5")
            # fred,289CC29F0A000062,dgin,17,snpw,33,htpw,32,itv,5,otno,5
            # fred_ds18,289CC29F0A000062,289CC29FA0062,15.19,15.19,15.25,15.44,15.69,16.06,16.44,16.81,17.06,17.19,17.25,
            #ds18b20_search,17,power,33
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-10: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_j'] = zeroeth_value
                wwl1['su_temp_j_max'] = max_value
                wwl1['su_temp_j_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-10 reading failed, error:", sys.exc_info()[0]

        
        # -------------- Suction 11 -----------------------
        # tank
        try:
            ard.write("fred,2887C29F0A0000C1,dgin,16,snpw,37,htpw,34,itv," + SUCTION_HEAT_TIME + ",otno,5")
            # fred,2887C29F0A0000C1,dgin,16,snpw,37,htpw,34,itv,5,otno,5
            # fred_ds18,2887C29F0A0000C1,2887C29F00C1,1525,15.31,15.38,15.50,15.69,15.94,16.25,16.50,16.75,16.94,17.06,
            #ds18b20_search,16,power,37
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-11: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_k'] = float(zeroeth_value)
                wwl1['su_temp_k_max'] = float(max_value)
                wwl1['su_temp_k_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-11 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 12 -----------------------
        # tank
        try:
            ard.write("fred,AAA,dgin,16,snpw,37,htpw,35,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-12: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_l'] = float(zeroeth_value)
                wwl1['su_temp_l_max'] = float(max_value)
                wwl1['su_temp_l_diff'] = float(max_value - zeroeth_value)
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-12 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 13 -----------------------
        # tank
        try:
            ard.write("fred,AAA,dgin,16,snpw,37,htpw,36,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-13: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_m'] = float(zeroeth_value)
                wwl1['su_temp_m_max'] = float(max_value)
                wwl1['su_temp_m_diff'] = float(max_value) - float(zeroeth_value)
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-13 reading failed, error:", sys.exc_info()[0]
        

        # -------------- Suction 14 -----------------------
        # tank
        try:
            ard.write("fred,AAA,dgin,15,snpw,41,htpw,38,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-14: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_n'] = float(zeroeth_value)
                wwl1['su_temp_n_max'] = float(max_value)
                wwl1['su_temp_n_diff'] = float(max_value) - float(zeroeth_value)
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-14 reading failed, error:", sys.exc_info()[0]
        

        # -------------- Suction 15 -----------------------
        # tank
        try:
            ard.write("fred,AAA,dgin,15,snpw,41,htpw,39,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-15: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_o'] = float(zeroeth_value)
                wwl1['su_temp_o_max'] = float(max_value)
                wwl1['su_temp_o_diff'] = float(max_value) - float(zeroeth_value)
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-15 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 16 -----------------------
        # tank
        try:
            ard.write("fred,AAA,dgin,15,snpw,41,htpw,40,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-16: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = float(current_read[3])
                max_value = float(current_read[3+5])
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_p'] = float(zeroeth_value)
                wwl1['su_temp_p_max'] = float(max_value)
                wwl1['su_temp_p_diff'] = float(max_value )- float(zeroeth_value)
                sleep(2)
            
            #old code for historical review
            # current_read = msg.split(',')[0:-1]
            # if (len(current_read) > 2):
            #     current_read_zero_value = float(current_read[2])
            #     wwl1['su_temp_p'] = current_read_zero_value
            #     wwl1['su_p0'] = float(current_read[4]) - current_read_zero_value
            #     wwl1['su_p1'] = float(current_read[6]) - current_read_zero_value
            #     wwl1['su_p2'] = float(current_read[8]) - current_read_zero_value
            #     wwl1['su_p3'] = float(current_read[10]) - current_read_zero_value
            #     wwl1['su_p4'] = float(current_read[12]) - current_read_zero_value
            #     sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-16 reading failed, error:", sys.exc_info()[0]
        
        ## End of suction sensors, return serial timeout to 60 seconds
        # ard.timeout = 60 #change timeout for suction sensors


        ## ------ Finish reading all sensors--------------
        ard.close()

        if (PUBLISH_TO_THINGSBOARD):
            json_data = {"ts":seconds_since_epoch, "values": wwl1}
            # json_data = data_collected
            val = client.publish('v1/devices/me/telemetry', payload=json.dumps(json_data), qos=1)
            if SCREEN_DISPLAY:
                print(val)
                print(json_data)
                print "uploaded"

        if (PUBLISH_TO_THINGSBOARD_102):
            json_data = {"ts":seconds_since_epoch, "values": wwl1}
            # json_data = data_collected
            val = client_102.publish('v1/devices/me/telemetry', payload=json.dumps(json_data), qos=1)
            if SCREEN_DISPLAY:
                print(val)
                print(json_data)

        if SAVE_TO_FILE:
            fid.write("\r\n")
            fid.close()

        # Sleep to the next loop
        if SCREEN_DISPLAY:
            print("Sleep for " + str(SLEEP_TIME_SECONDS) + " Seconds")
            print("")

        time.sleep(SLEEP_TIME_SECONDS)


except KeyboardInterrupt:
    pass

finally:
    if (SAVE_TO_FILE and (fid.closed == False)):
        fid.close()
    if (ard.isOpen()):
        ard.close()
    if (PUBLISH_TO_THINGSBOARD):
        client.loop_stop()
        client.disconnect()

