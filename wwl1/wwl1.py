#!/usr/bin/python
import serial
import os
import time
#import numpy as np
import sys
import paho.mqtt.client as mqtt
import json
from phant import Phant
import serial_openlock
#import get_ip
from upload_phant import upload_phant
# below required by gpio
import RPi.GPIO as GPIO            # import RPi.GPIO module  
from time import sleep,gmtime,localtime,strftime


with open('/home/pi/pyduino/credential/wwl1.json') as f:
    credential = json.load(f) #,object_pairs_hook=collections.OrderedDict)

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
SLEEP_TIME_SECONDS = 60 * 60 # seconds

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

field_name=['volt','dht22_rh','dht22_t',
        'mo1_ec', 'mo2_ec', 'mo3_ec','mo4_ec','mo5_ec',
        'mo6_ec','mo7_ec','mo8_ec','mo9_ec',
        'mo10_ec','mo11_ec',
        'mo12_ec','mo13_ec','mo14_ec',
        'mo1_temp', 'mo2_temp', 'mo3_temp','mo4_temp','mo5_temp',
        'mo6_temp','mo7_temp','mo8_temp','mo9_temp',
        'mo10_temp','mo11_temp',
        'mo12_temp','mo13_temp','mo14_temp',
        'mo1_dp', 'mo2_dp', 'mo3_dp','mo4_dp','mo5_dp',
        'mo6_dp','mo7_dp','mo8_dp','mo9_dp',
        'mo10_dp','mo11_dp',
        'mo12_dp','mo13_dp','mo14_dp',
        # 'su_a0','su_a1','su_a2','su_a3','su_a4',
        # 'su_b0','su_b1','su_b2','su_b3','su_b4',
        # 'su_c0','su_c1','su_c2','su_c3','su_c4',
        # 'su_d0','su_d1','su_d2','su_d3','su_d4',
        # 'su_e0','su_e1','su_e2','su_e3','su_e4',
        # 'su_f0','su_f1','su_f2','su_f3','su_f4',
        # 'su_g0','su_g1','su_g2','su_g3','su_g4',
        # 'su_h0','su_h1','su_h2','su_h3','su_h4',
        # 'su_i0','su_i1','su_i2','su_i3','su_i4',
        # 'su_j0','su_j1','su_j2','su_j3','su_j4',
        # 'su_k0','su_k1','su_k2','su_k3','su_k4',
        # 'su_l0','su_l1','su_l2','su_l3','su_l4',
        # 'su_m0','su_m1','su_m2','su_m3','su_m4',
        # 'su_n0','su_n1','su_n2','su_n3','su_n4',
        # 'su_o0','su_o1','su_o2','su_o3','su_o4',
        # 'su_p0','su_p1','su_p2','su_p3','su_p4',
        'su_temp_a','su_temp_b','su_temp_c','su_temp_d','su_temp_e',
        'su_temp_f','su_temp_g','su_temp_h','su_temp_i','su_temp_j',
	    'su_temp_k','su_temp_l','su_temp_m','su_temp_n','su_temp_o','su_temp_p'
        'su_temp_a_max','su_temp_b_max','su_temp_c_max','su_temp_d_max','su_temp_e_max',
        'su_temp_f_max','su_temp_g_max','su_temp_h_max','su_temp_i_max','su_temp_j_max',
	    'su_temp_k_max','su_temp_l_max','su_temp_m_max','su_temp_n_max','su_temp_o_max','su_temp_p_max',
        'su_temp_a_diff','su_temp_b_diff','su_temp_c_diff','su_temp_d_diff','su_temp_e_diff',
        'su_temp_f_diff','su_temp_g_diff','su_temp_h_diff','su_temp_i_diff','su_temp_j_diff',
	    'su_temp_k_diff','su_temp_l_diff','su_temp_m_diff','su_temp_n_diff','su_temp_o_diff','su_temp_p_diff'
        ]

#look_up = {
#	'0_DEC' : ['gstemp0', 'gsec0', 'gsdp0'],
#	'1_DEC' : ['gstemp1', 'gsec1', 'gsdp1'],
#	'2_DEC' : ['gstemp2', 'gsec2', 'gsdp2'],
#	'3_DEC' : ['gstemp3', 'gsec3', 'gsdp3'],
#	'A_Cam' : ['cstemp0', 'csec0', 'csdp0'],
#	'B_Cam' : ['cstemp1', 'csec1', 'csdp1'],
#	'C_Cam' : ['cstemp2', 'csec2', 'csdp2'],
#	'D_Cam' : ['cstemp3', 'csec3', 'csdp3'],
#	'E_Cam' : ['cstemp4', 'csec4', 'csdp4'],
#
#}
#
#sensor_name = #strip and split to get the name
#name_field = look_up.get(sensor_name) #list of strings for certain sensor_name
#temp_filed = name_field[0]
#ec_field = name_field[1]
#dp_filed = name_file[2]


wwl1=dict((el,0.0) for el in field_name)
pht_sensor = Phant(publicKey=credential["public_wwl1"], fields=field_name ,privateKey=credential["private_wwl1"],baseUrl=credential["nectar_address"])

port_sensor  = '/dev/ttyS0'

# whether the result will be displayed on the screen
SCREEN_DISPLAY = True

# whether save the result as a file 
SAVE_TO_FILE = True
# the Filename of the csv file for storing file
file_name= 'wwl1.csv'

# Whether to publish to thingsboard
PUBLISH_TO_THINGSBOARD = True

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

try:

    while True:
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
        

        #----------Moisture Sensor 2 (MO2)--------------
        try:
            ard.write("SDI-12,52,power,46,default_cmd,read,debug,1")
            #SDI-12,52,power,46,default_cmd,read,debug,1
            #SDI-12,52,default_cmd,read,power,46,power_off,1,no_sensors,1,Addr,6_MET,points,3,1816.27,17.2,0,
            ard.flushInput()
            msg = ard.readline()
            current_read = msg.split('Addr')

            if SCREEN_DISPLAY:
                print("MO2: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
            sleep(2)
            
            if (len(current_read) > 1):
                data_values = current_read[-1].split(',')[1:-1]
                mo_type = data_values[0][-3:].lower()
                wwl1['mo2_dp'] = float(data_values[-3])
                if (mo_type == "cam"):
                    # Campbell scientific sensor data order
                    wwl1['mo2_ec'] = float(data_values[-2])
                    wwl1['mo2_temp'] = float(data_values[-1])
                else:
                    # Sensor default data order
                    wwl1['mo2_ec'] = float(data_values[-1])
                    wwl1['mo2_temp'] = float(data_values[-2])

        except Exception:
            if SCREEN_DISPLAY:
                print "MO2 reading failed, error:", sys.exc_info()[0]
        

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
            # SDI-12,50,power,46,default_cmd,read,debug,1
            # SDI-12,50,default_cmd,read,power,46,power_off,1,no_sensors,1,Addr,4_DEC,points,3,1.92,14.7,1,
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
            #SDI-12,62,default_cmd,read,power,47,power_off,1,No SDI12 found!
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
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_a'] = zeroeth_value
                wwl1['su_temp_a_max'] = max_value
                wwl1['su_temp_a_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-1 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 2 -----------------------
        # tank
        try:
            ard.write("fred,A19C7FBB,dgin,18,snpw,27,htpw,23,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-2: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_b'] = zeroeth_value
                wwl1['su_temp_b_max'] = max_value
                wwl1['su_temp_b_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-2 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 3 -----------------------
        # tank
        try:
            ard.write("fred,069D7FAF,dgin,18,snpw,27,htpw,24,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-3: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_c'] = zeroeth_value
                wwl1['su_temp_c_max'] = max_value
                wwl1['su_temp_c_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-3 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 4 -----------------------
        # tank
        try:
            ard.write("fred,936A7F02,dgin,18,snpw,27,htpw,25,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-4: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_d'] = zeroeth_value
                wwl1['su_temp_d_max'] = max_value
                wwl1['su_temp_d_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-4 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 5 -----------------------
        # tank
        try:
            ard.write("fred,9F6A7F7F,dgin,18,snpw,27,htpw,26,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-5: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_e'] = zeroeth_value
                wwl1['su_temp_e_max'] = max_value
                wwl1['su_temp_e_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-5 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 6 -----------------------
        # tank
        try:
            ard.write("fred,AB6A7F4E,dgin,17,snpw,33,htpw,28,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-6: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_f'] = zeroeth_value
                wwl1['su_temp_f_max'] = max_value
                wwl1['su_temp_f_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-6 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 7 -----------------------
        # tank
        try:
            ard.write("fred,2B7F7F0A,dgin,17,snpw,33,htpw,29,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-7: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_g'] = zeroeth_value
                wwl1['su_temp_g_max'] = max_value
                wwl1['su_temp_g_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-7 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 8 -----------------------
        # tank
        try:
            ard.write("fred,AE9C7F9F,dgin,17,snpw,33,htpw,30,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-8: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_h'] = zeroeth_value
                wwl1['su_temp_h_max'] = max_value
                wwl1['su_temp_h_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-8 reading failed, error:", sys.exc_info()[0]


        # -------------- Suction 9 -----------------------
        # tank
        try:
            ard.write("fred,2E927FD7,dgin,17,snpw,33,htpw,31,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-9: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_i'] = zeroeth_value
                wwl1['su_temp_i_max'] = max_value
                wwl1['su_temp_i_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-9 reading failed, error:", sys.exc_info()[0]

    
        # -------------- Suction 10 -----------------------
        # tank
        try:
            ard.write("fred,2E927FD7,dgin,17,snpw,33,htpw,32,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-10: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                # wwl1['su_temp_j'] = zeroeth_value
                # wwl1['su_temp_j_max'] = max_value
                # wwl1['su_temp_j_diff'] = max_value - zeroeth_value
                sleep(2)

        except Exception:
            if SCREEN_DISPLAY:
                print "Suction-10 reading failed, error:", sys.exc_info()[0]

        
        # -------------- Suction 11 -----------------------
        # tank
        try:
            ard.write("fred,AAA,dgin,16,snpw,37,htpw,34,itv," + SUCTION_HEAT_TIME + ",otno,5")
            msg = ard.flushInput()
            msg = ard.readline()

            if SCREEN_DISPLAY:
                print("Suction-11: " + msg.rstrip())
            if SAVE_TO_FILE:
                fid.write(time_now_local_str + DELIMITER + msg)
                
            current_read = msg.split(',')[0:-1]
            current_read_length = len(current_read)
            if (current_read_length > 2):
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_k'] = zeroeth_value
                wwl1['su_temp_k_max'] = max_value
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
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_l'] = zeroeth_value
                wwl1['su_temp_l_max'] = max_value
                wwl1['su_temp_l_diff'] = max_value - zeroeth_value
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
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_m'] = zeroeth_value
                wwl1['su_temp_m_max'] = max_value
                wwl1['su_temp_m_diff'] = max_value - zeroeth_value
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
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_n'] = zeroeth_value
                wwl1['su_temp_n_max'] = max_value
                wwl1['su_temp_n_diff'] = max_value - zeroeth_value
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
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_o'] = zeroeth_value
                wwl1['su_temp_o_max'] = max_value
                wwl1['su_temp_o_diff'] = max_value - zeroeth_value
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
                zeroeth_value = current_read[3]
                max_value = current_read[3+5]
                # max_value = 0.0
                # # Loop through to get zeroeth reading and max reading
                # for i in range(3, current_read_length):
                #     current_value = float(current_read[i])
                #     if max_value == 0.0:
                #         zeroeth_value = current_value # Store zero reading
                #     elif current_value > max_value:
                #         max_value = current_value
                
                wwl1['su_temp_p'] = zeroeth_value
                wwl1['su_temp_p_max'] = max_value
                wwl1['su_temp_p_diff'] = max_value - zeroeth_value
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

        # client.publish('v1/devices/me/telemetry', json.dumps(wwl1), 1)
        # #upload_phant(pht_sensor,wwl1,SCREEN_DISPLAY)
        # print "uploaded"

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

