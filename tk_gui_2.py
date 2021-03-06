#
#  This work is protected under applicable local and international
#  copyright laws.  Copying, transmitting, using, or any other activity
#  is expressly forbidden without prior signed written approval from
#  the copyright owner.
#
#  Copyright(c) 2019, 2020 Autonomous Medical Device, Incorporated,
#  ALL RIGHTS RESERVED.
#


try:
    import RPi.GPIO as GPIO
except Exception:
    print("Failed to load RPi.GPIO. Using Mock")
    import unittest
    from unittest.mock import patch, MagicMock

    MockRPi = MagicMock()
    modules = {
        "RPi": MockRPi,
        "RPi.GPIO": MockRPi.GPIO
    }
    patcher = patch.dict("sys.modules", modules)
    patcher.start()
    import RPi.GPIO as GPIO

try:
    import pymba
except Exception:
    print('Failed to load Vimba. Using Mock')
    MockPymba = MagicMock()
    MockSerial = MagicMock()
    modules = {
        "pymba": MockPymba,
        "serial": MockSerial,
    }
    patcher = patch.dict("sys.modules", modules)
    patcher.start()
    from pymba import Vimba

import smbus
import os 
from E20 import E20
from tkinter import *
from tkinter import font
import tkinter.messagebox as messagebox
from datetime import datetime
from PIL import Image, ImageTk
import time 
import json
import subprocess
import serial
import RPi.GPIO as GPIOEmail
import datetime as dt
# import matplotlib.pyplot as plt
# import matplotlib.animation as animation
import numpy as np
#import functions as cf
import cv2
import subprocess
from tkinter import StringVar
from datetime import datetime
from time import sleep
import json
from json2table import convert
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import subprocess
import shutil
from settings import LV1_PS_PIN, LV2_PS_PIN, LV1_PS_ON, LV1_PS_OFF, LV2_PS_ON, LV2_PS_OFF
from settings import ORANGE_LED, ORANGE_LED_ON, ORANGE_LED_OFF
from settings import WHITE_LED, WHITE_LED_ON, WHITE_LED_OFF
from settings import LASER_1, LASER_1_OUT_PIN, LASER1_INTENSITY
from settings import LASER_2, LASER_2_OUT_PIN, LASER2_INTENSITY
from settings import LED_ON, LED_OFF


class Multiplexer:

    def __init__(self, bus, devaddress):
        self.bus = smbus.SMBus(bus)
        self.devaddress = devaddress

    def __enter__(self):
        self.bus = smbus.SMBus(self.bus)
        return self.bus

    def __exit__(self, *args):
        raise Exception("Error with i2c")

    def channel(self, channel, register, intensity):
      
        # Turn on blue light
        # self.bus.write_byte_data(self.devaddress,  
        #                          0x06,
        #                          255  )


        #01 - orange
        #02 - white
                self.bus.write_byte_data(self.devaddress,  
                                 register,
                                 intensity  )


class TC74:
    '''
    class for the TC74
    '''
    def __init__(self, bus, devaddr):
        self.devaddr         = devaddr  # in the docs it seemed to be 0x4d?
        self.reg_temp        = 0x00     # temp register in 2's complement format
        self.reg_config      = 0x01
        self.ADC0MSB         = 0x0c
        self.ADC0LSB         = 0x0d
        self.ADC1MSB         = 0x0e
        self.ADC1LSB         = 0x0f
        self.stepper_bit     = 8
        self.shutdown_bit    = 7
        self.data_ready_bit  = 6
        self.tc74_i2c_bus    = smbus.SMBus(bus)

    def read_gain(self):
        gain1M = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.ADC0MSB)
        gain1L = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.ADC0LSB)

        
        Gain = 0
        if gain1M != 0:
            gain1M = gain1M << self.stepper_bit
            Gain = gain1M + gain1L

        return (Gain)

    def read_gain2(self):
        gain1M = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.ADC1MSB)
        gain1L = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.ADC1LSB)

        
        Gain = 0
        if gain1M != 0:
            gain1M = gain1M << self.stepper_bit
            Gain = gain1M + gain1L
            
        return (Gain)
    
    def read_temp(self):
        temp   = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.reg_temp)
        config = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.reg_config)

        if (config & (1 << self.shutdown_bit)):
            print('TC74 sensor is not available at this time (STANDBY) %x' % config)
            # attempt to bring it online for next time
            config |= (1 << self.shutdown_bit)
            self.tc74_i2c_bus.write_byte_data(self.devaddr, self.reg_config, config)
            return None
        if not (config & (1 << self.data_ready_bit)):
            print('TC74 sensor is not ready at this time (NOT READY) %x' % config)
            # attempt to bring it online for next time
            config |= (1 << self.data_ready_bit)
            self.tc74_i2c_bus.write_byte_data(self.devaddr, self.reg_config, config)
            return None

        if (temp > 127):
            return (128 - temp)

        return temp

class Window(Frame):

    v1 = 1795 #-199, -2211
    v5 = 2220 #-161, -1788
    va = 2589  #-127, -1411
    gain = 0
    gain2 = 0

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self.init_window()
        self.e20 = E20()

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(LV1_PS_PIN, GPIO.IN) 
        GPIO.setup(LV2_PS_PIN, GPIO.IN) 
        



    # Create init_window
    def init_window(self):


        def donde():
            count = self.e20.motor.get_actual_encoder_count()
            msgBox=messagebox.askquestion('Current tick, good?', count)

            print('position=',count)

        # Keeps spinning forever at given rpm
        def spinendlessly():
            #self.e20.motor.spin_settings()
            acc = int(varAcc.get())
            vel = int(varV.get())
            self.e20.motor.set_acceleration(acc)
            #self.e20.motor.stop()
            self.e20.motor.spin(vel)
            msgBox=messagebox.askquestion('Spin Motor','Did Motor spin?')
            if (msgBox == 'yes'):
                spinButton["bg"] = "green"
                results[test_Idx['Spin Motor']] = Result_T['PASS']
            else:
                spinButton["bg"] = "red"
                results[test_Idx['Spin Motor']] = Result_T['FAIL']

        # Move disc at given angle
        def move_position():
            #self.e20.motor.position_settings()
            self.e20.motor.velocity_max_pos_ctrl       = 40 # rpm/s position can only happen below this speed
            self.e20.motor.acceleration_pos_ctrl       = 40
            pos =float(varAng.get())
            self.e20.motor.position_abs(int(pos))
            msgBox=messagebox.askquestion('Move Angle','Did the angle move?')
            if (msgBox == 'yes'):
                positionButton["bg"] = "green"
                results[test_Idx['Move Angle']] = Result_T['PASS']
            else:
                positionButton["bg"] = "red"
                results[test_Idx['Move Angle']] = Result_T['FAIL']
            

        # Spins disc until index position is found 
        def home():
            #self.e20.motor.position_settings()
            #self.e20.motor.set_acceleration(10)
            #self.e20.motor.spin(500, 3)
            #self.e20.motor.position_abs(0)
            self.e20.motor.home()
            self.e20.motor.position_abs(0)
            msgBox=messagebox.askquestion('Find Index','Did Find Index found?')
            if (msgBox == 'yes'):
                findButton["bg"] = "green"
                results[test_Idx['Find Index']] = Result_T['PASS']
            else:
                findButton["bg"] = "red"
                results[test_Idx['Find Index']] = Result_T['FAIL']


        def detect1():

            if GPIO.input(LV1_PS_PIN) == LV1_PS_ON:
                print('laser1 is detected')
                messagebox.showinfo('laser1 detected by lid')
                return True
            
            else:
                print('laser1 is NOT! detected')
                return False

        def detect2():

            if GPIO.input(LV2_PS_PIN) == LV2_PS_ON:
                print('laser2 is detected')
                messagebox.showinfo('laser2 detected by lid')
                return True
            
            else:
                print('laser2 is NOT! detected')
                return False

        def detector1():

            detect1()
            self.e20.laser1.set_intensity(LASER_1, 100)
            self.e20.laser1.on()
            x = False
            while x == False:
                x= detect1()

            self.e20.laser1.off()
            sleep(1)
            
            detect1()
            msgBox=messagebox.askquestion('lsr1 detect','Was laser1 detected?')
            if (msgBox == 'yes'):
                laser12Button["bg"] = "green"
                results[test_Idx['lsr1 dtec']] = Result_T['PASS']
            else:
                laser12Button["bg"] = "red"
                results[test_Idx['lsr1 dtec']] = Result_T['FAIL']


        def detector2():

            detect2()
            self.e20.laser2.set_intensity(LASER_2, 100)
            self.e20.laser2.on()
            x = False
            while x == False:
                x= detect2()
          
            self.e20.laser2.off()
            sleep(1)
            detect2()
            msgBox=messagebox.askquestion('lsr2 detect','Was laser2 detected?')
            if (msgBox == 'yes'):
                laser22Button["bg"] = "green"
                results[test_Idx['lsr2 dtec']] = Result_T['PASS']
            else:
                laser22Button["bg"] = "red"
                results[test_Idx['lsr2 dtec']] = Result_T['FAIL']


        def filterLED_O():

            intensity = int(varLED.get())
            LID_SENSOR_MULTIPLEXER = 0x59

            mplx=Multiplexer(1, LID_SENSOR_MULTIPLEXER)
            x = mplx.channel(0, 0x01, intensity)

        def filterLED_W():

            intensity = int(varLED.get())
            LID_SENSOR_MULTIPLEXER = 0x59

            mplx=Multiplexer(1, LID_SENSOR_MULTIPLEXER)
            x = mplx.channel(0, 0x02, intensity)

        def lidLED():

            t = float(varTime.get())
            intensity = int(varLED.get())
            LID_LED_MULTIPLEXER = 0x49

            mplx=Multiplexer(1, LID_LED_MULTIPLEXER)
            x = mplx.channel(0, 0x01, intensity)
            sleep(1)
            x = mplx.channel(0, 0x01, 0)
            msgBox=messagebox.askquestion('Lid LED','Did the lid LED turn on?')
            if (msgBox == 'yes'):
                led2Button["bg"] = "green"
                results[test_Idx['Lid LED']] = Result_T['PASS']
            else:
                led2Button["bg"] = "red"
                results[test_Idx['Lid LED']] = Result_T['FAIL']  
           
                

            

        # Fires laser 1
        # def laser1():
        #     t = float(varTime.get())
        #     self.e20.laser1.on_time(t)

        def update():
            x = str(self.gain)
            displayVar.set(x)

        def laser1():
            s = int(varLaz.get())
            t = float(varTime.get())
            self.e20.laser1.set_intensity(LASER_1, s)
            
            timeout = time.time() + t
            self.e20.laser1.on()
            while True:
                self.gain = gainer()
                print('G1 =' , self.gain)
                sleep(1)
                if time.time() > timeout:
                    break
            self.e20.laser1.off()
            update()
            msgBox=messagebox.askquestion('Laser 1','Did the laser 1 go on?')
            if (msgBox == 'yes'):
                laser1Button["bg"] = "green"
                results[test_Idx['Laser 1']] = Result_T['PASS']
                #print("rsults[{}]= Pass".format(test_Idx['Laser 1 On']))
            else:
                laser1Button["bg"] = "red"
                results[test_Idx['Laser 1']] = Result_T['FAIL']
                #print("rsults[{}]= Fail".format(test_Idx['Laser 1 On']))

            # gain = gainer()
            # print(gain)
            # sleep(t)
            # self.e20.laser1.off()
            
                
        # Fires laser 2
        def laser2():
            s = int(varLaz.get())
            t = float(varTime.get())
            self.e20.laser2.set_intensity(LASER_2, s)
            self.e20.laser2.on()
            gain2 = gainer2()
            print('G2 = ', gain2)
            sleep(t)
            self.e20.laser2.off()
            msgBox=messagebox.askquestion('Laser 2','Did the laser 2 go on?')
            if (msgBox == 'yes'):
                laser2Button["bg"] = "green"
                results[test_Idx['Laser 2']] = Result_T['PASS']
            else:
                laser2Button["bg"] = "red"
                results[test_Idx['Laser 2']] = Result_T['FAIL']  
            
        def laserSweep():
            pos = float(varAng.get())
            self.e20.laser_sweep(start_tick=pos,
                                width=17,
                                delay=1.01,
                                steps=6)


        # LED 1
        # def led1():
        #    t = float(varTime.get())
        #    self.e20.led1(t)i
        def assayRun(self):
            os.system("python3 /opt/amdi/hardware_control/run_test.py M01011-CD4cooldown 51AB7F4B-3837-4066-A586-D9933C845BFD-MA1010-CD4536")
        
        # def flash_off_O(self):
        #     GPIO.output(self.ORANGE_LED, LED_OFF)
        #     logging.info("LED oFF.")
        #     # self.flash = False
        #     # return self.flash

        # def flash_on_W(self):
        #     GPIO.output(self.WHITE_LED, LED_ON)
        #     logging.info("LED on.")
        #     # self.flash = True
        #     # return self.flash
        
        # def flash_off_W(self):
        #     GPIO.output(self.WHITE_LED, LED_OFF)
        #     logging.info("LED oFF.")
        #     # self.flash = False
        #     # return self.flash


        def led1():
            intensity = int(varLED.get())
            LID_SENSOR_MULTIPLEXER = 0x59

            mplx=Multiplexer(1, LID_SENSOR_MULTIPLEXER)
            x = mplx.channel(0, 0x01, intensity)
            sleep(1)
            t = float(varTime.get())
            #self.e20.led1(t)
            self.e20.camera.flash_on()
            sleep(t)
            self.e20.camera.flash_off()
            msgBox=messagebox.askquestion('Orange LED','Did Orange LED turn on?')

            if (msgBox == 'yes'):
                led1Button["bg"] = "green"
                results[test_Idx['LED Orange']] = Result_T['PASS']
            else:
                led1Button["bg"] = "red"
                results[test_Idx['LED Orange']] = Result_T['FAIL']
            
           
        # LED 2
        # def led2():
        #     t = float(varTime.get())
        #     self.e20.led2(t)

        def led2():
            intensity = int(varLED.get())
            LID_SENSOR_MULTIPLEXER = 0x59

            mplx=Multiplexer(1, LID_SENSOR_MULTIPLEXER)
            x = mplx.channel(0, 0x02, intensity)
            sleep(1)
            t = float(varTime.get())
            GPIO.output(WHITE_LED, LED_ON)
            #logging.info("LED on.")
            sleep(t)
            GPIO.output(WHITE_LED, LED_OFF)
            msgBox=messagebox.askquestion('White LED','Did White LED turn on?')
            if (msgBox == 'yes'):
                led2Button["bg"] = "green"
                results[test_Idx['LED White']] = Result_T['PASS']
            else:
                led2Button["bg"] = "red"
                results[test_Idx['LED White']] = Result_T['FAIL']

        def ledR():
            intensity = int(varLED.get())
            t = float(varTime.get())
            LID_SENSOR_MULTIPLEXER = 0x49

            mplx=Multiplexer(1, LID_SENSOR_MULTIPLEXER)
            x = mplx.channel(0, 0x05, intensity)
            #sleep(1)
            msgBox=messagebox.askquestion('Red LED','Did Red LED intensity change?')
            if (msgBox == 'yes'):
                ledRButton["bg"] = "green"
                results[test_Idx['LED Red']] = Result_T['PASS']
            else:
                ledRButton["bg"] = "red"
                results[test_Idx['LED Red']] = Result_T['FAIL']
            

        def ledG():
            intensity = int(varLED.get())
            t = float(varTime.get())
            LID_SENSOR_MULTIPLEXER = 0x49

            mplx=Multiplexer(1, LID_SENSOR_MULTIPLEXER)
            x = mplx.channel(0, 0x06, intensity)
            #sleep(1)
            msgBox=messagebox.askquestion('Green LED','Did Green LED intensity change?')
            if (msgBox == 'yes'):
                ledGButton["bg"] = "green"
                results[test_Idx['LED Green']] = Result_T['PASS']
            else:
                ledGButton["bg"] = "red"
                results[test_Idx['LED Green']] = Result_T['FAIL']
            
            

        def ledB():
            intensity = int(varLED.get())
            t = float(varTime.get())
            LID_SENSOR_MULTIPLEXER = 0x49

            mplx=Multiplexer(1, LID_SENSOR_MULTIPLEXER)
            x = mplx.channel(0, 0x07, intensity)
            #sleep(1)
            msgBox=messagebox.askquestion('Blue LED','Did Blue LED intensity change?')
            if (msgBox == 'yes'):
                ledBButton["bg"] = "green"
                results[test_Idx['LED Blue']] = Result_T['PASS']
            else:
                ledBButton["bg"] = "red"
                results[test_Idx['LED Blue']] = Result_T['FAIL']

        def gainer():

            LID_SENSOR_MULTIPLEXER = 0x49
            tc74_sensor = TC74(1, LID_SENSOR_MULTIPLEXER)  # temp sensor on bus 1 address 0x48
            gain = tc74_sensor.read_gain()

            return gain

        def gainer2():

            LID_SENSOR_MULTIPLEXER = 0x49
            tc74_sensor = TC74(1, LID_SENSOR_MULTIPLEXER)  # temp sensor on bus 1 address 0x48
            gain = tc74_sensor.read_gain2()

            return gain
            
            
           
 
       # Fans
        def fans():
            t = float(varTime.get())
            self.e20.fans(t) 

        def lidCam():
            nombre = str(varNombre.get())
            nombre = '/home/autolab/Desktop/images/'+nombre
            cmd = 'v4l2-ctl --set-fmt-video=width=640,height=480,pixelformat=JPEG --stream-mmap --stream-count=1 --stream-to=%s.jpg --device /dev/video0' % nombre
            print('p:', cmd)
            os.system(cmd)
            msgBox=messagebox.askquestion('Lid Cam','Did lid camera capture a .jpg?')
            if (msgBox == 'yes'):
                lidcamButton["bg"] = "green"
                results[test_Idx['Lid cam']] = Result_T['PASS']
            else:
                lidcamButton["bg"] = "red"
                results[test_Idx['Lid cam']] = Result_T['FAIL']


            
 
        # Captures image with given input settings    
        def capture():
            #exposure = float(varExp.get())*1000000
            #gain = float(varGain.get())
            #gamma = float(varGamma.get())
            nombre = str(varNombre.get())
            date = str(datetime.now().strftime("%m-%d-%Y_%I:%M:%S_%p"))
            global filename
            filename = "/home/autolab/Desktop/images/%s-%s.tiff" % (nombre, date)
            print("filename=", filename)
            self.e20.camera.capture(
                                    flash=True,
                                    filename=filename)
            msgBox=messagebox.askquestion('Cam','Did camera capture a .tiff?')
            if (msgBox == 'yes'):
                captureButton["bg"] = "green"
                results[test_Idx['capture']] = Result_T['PASS']
            else:
                captureButton["bg"] = "red"
                results[test_Idx['capture']] = Result_T['FAIL']
            
                                    
            
                       
        def scanQRCode():
            process = subprocess.run('/opt/amdi/bin/QRreader',shell=True)
            msgBox=messagebox.askquestion('QR scanner','Did QR scanner work?')
            if (msgBox == 'yes'):
                FansButton["bg"] = "green"
                results[test_Idx['Scan QR']] = Result_T['PASS']
            else:
                FansButton["bg"] = "red"
                results[test_Idx['Scan QR']] = Result_T['FAIL']
            
                   
        def assay2():
            cycles = int(varOperator.get())
            nombre = str(varNombre.get())
            #sleeper = int(varEmail.get())
            date = str(datetime.now().strftime("%m-%d-%Y_%I:%M:%S_%p"))
            
            for i in range(cycles):
                print("run number:", i)
                filename = "%s-%s-%d.tiff" % (nombre, date, i)
                self.e20.run_assay(filename)
                slept = sleeper * 60
                print('sleeping for:', slept)
                sleep(slept)
                print(' done with:' ,i)
            print('finished')

        def assay():
            assay = str(varAssay.get())
            nombre = str(varNombre.get())
            date = str(datetime.now().strftime("%m-%d-%Y_%I:%M:%S_%p"))
            filename = "%s-%s-%s" % (assay, nombre, date)
            self.e20.run_assay(filename)
            msgBox=messagebox.askquestion('Assay','Did the assay run?')
            if (msgBox == 'yes'):
                assayButton["bg"] = "green"
                results[test_Idx['Assay']] = Result_T['PASS']
            else:
                assayButton["bg"] = "red"
                results[test_Idx['Assay']] = Result_T['FAIL']
            
        
        def test():
            self.e20.run_test

        def latch():
            self.e20.extend_latch()
            msgBox=messagebox.askquestion('lock','Did the lid lock?')
            if (msgBox == 'yes'):
                lockButton["bg"] = "green"
                results[test_Idx['Lock Lid']] = Result_T['PASS']
            else:
                lockButton["bg"] = "red"
                results[test_Idx['Lock Lid']] = Result_T['FAIL']
            

        def unlatch():
            self.e20.retract_latch()
            msgBox=messagebox.askquestion('unlock','Did the lid unlock?')
            if (msgBox == 'yes'):
                unlockButton["bg"] = "green"
                results[test_Idx['Unlock Lid']] = Result_T['PASS']
            else:
                unlockButton["bg"] = "red"
                results[test_Idx['Unlock Lid']] = Result_T['FAIL']
            

        def stop():
            self.e20.motor.stop()
            self.e20.motor.motor_release()

        def dondeDos():
            
            if self.e20.motor.reset_pid:
                self.e20.motor.pid_reset()

            self.e20.motor.position_abs(self.v1)
            sleep(5)
            count = self.e20.motor.controller.get_actual_encoder_count_modulo()
            msgBox=messagebox.askquestion('Is this pos. optimal?', count)
            if (msgBox == 'no'):
                messagebox.showinfo('Adjust to position')
                self.e20.motor.motor_release()
                sleep(5)
                count = self.e20.motor.controller.get_actual_encoder_count()
                messagebox.showinfo('V1 cal:', count)
                self.v1 = count    
                print('position=', self.v1)
                print('count=', count)
            else:
                return 0    
                 

        def dondeTres():
            self.e20.motor.position_settings()
            self.e20.motor.position_abs(self.v5)
            sleep(5)
            count = self.e20.motor.get_actual_encoder_count_modulo()
            msgBox=messagebox.askquestion('Is this pos. optimal?', count)
            if (msgBox == 'no'):
                messagebox.showinfo('Adjust to position')
                self.e20.motor.brake()
                sleep(3)
                count = self.e20.motor.get_actual_encoder_count_modulo()
                messagebox.showinfo('V5 cal:', count)
                self.v5 = count    
                print('position=', self.v5)
                print('count=', count)
            else:
                return 0 

        def dondeQua():
            #array = -127
            self.e20.motor.position_settings()
            self.e20.motor.position_abs(self.va)
            #messagebox.showinfo('Array=',self.va)
            sleep(2)
            count = self.e20.motor.get_actual_encoder_count_modulo()
            msgBox=messagebox.askquestion('Is this pos. optimal?', count)
            if (msgBox == 'no'):
                messagebox.showinfo('Adjust to position')
                self.e20.motor.brake()
                sleep(3)
                count = self.e20.motor.get_actual_encoder_count_modulo()
                messagebox.showinfo('Array cal:', count)
                self.va = count    
                print('position=', self.va)
                print('count=', count)
            else:
                return 0 
        
        def store():
            print('v1=', self.v1)
            print('v5=', self.v5)
            print('Array=', self.va)

            # motorSer = str(ser)
            # x = motorSer.split(",")
            # y = str(x[0]).split("=", 1)
            # motorID = y[1]
            # print('ser1=', ser)
            # print('x0=', x[0])
            # print("y=", y[1])

            # camSer = str(serB)
            # x2 = camSer.split(",")
            # y2 = str(x2[0]).split("=", 1)
            # camID = y2[1]
            # # print('canInfo=', camSer)
            

            date = str(datetime.now().strftime("%m-%d-%Y_%I:%M:%S_%p"))
            jd = {}
           # jd["Motor Serial Number"] = motorID
           # jd["Camera Serial Number"] = camID
           # jd["Device Number"] = device_num
            jd["Date Time"] = date
            jd["valve1"] = self.v1
            jd["Valve5"] = self.v5
            jd["Array"] = self.va 

            json_file = open("/data/tmp/tmp.json", "w")
            json.dump(jd, json_file)
            json_file.close()
            with open("/data/tmp/tmp.json") as json_file:
                json_object = json.load(json_file)
            json_file.close()
            print(json_object)
        
        def saveReport():
            
            date = str(datetime.now().strftime("%m-%d-%Y_%I:%M:%S_%p"))
            #device_num = cpuserial
            jd = {}
            jd["Device Number"] = device_num
            jd["Date Time"] = date
            #jd["Operator Name"] = str(varOperator.get())
            jd["Test Code Revision"] = testRev
            for i in range(0, test_Idx['Max']):
                jd[testNames[i]] = results[i]
            #jo = json.dumps(jd)
            #print(jd)
                
            json_file = open("tmp.json", "w")
            json.dump(jd, json_file)
            json_file.close()
            with open("tmp.json") as json_file:
                json_object = json.load(json_file)
            json_file.close()
            print(json_object)
            build_direction = "LEFT_TO_RIGHT"
            table_attributes = {"style" : "width:100%", "text-align" : "center", "rules" : "all", "border" : "1"}
            json_html = convert(json_object, build_direction=build_direction, table_attributes=table_attributes)
            subject = 'SN_' + device_num + '_' + date
            fname =  subject + ".html"
            f = open(fname, 'wb')
            f.write("<!DOCTYPE html>".encode())
            f.write('\n'.encode())
            f.write("<html>".encode())
            f.write('\n'.encode())
            f.write("<style>".encode())
            f.write("\n".encode())
            f.write("h1 {text-align: center;}".encode())
            f.write("\n".encode())
            f.write("</style>".encode())
            f.write("\n".encode())
            f.write("<head>".encode())
            #f.write("\n".encode())
            f.write("<title>AMDI A-20 ASSEMBLY TEST REPORT</title>".encode())
            #f.write("\n".encode())
            f.write("</head>".encode())
            f.write("\n".encode())
            f.write("<body><p>".encode())
            f.write("<h1>AMDI A-20 ASSEMBLY TEST REPORT</h1>".encode())
            f.write("\n".encode())
            f.write(json_html.encode())
            f.write("</p></body>".encode())
            f.write('\n'.encode())
            f.write("</html>".encode())

            f.close()
            
            msg = MIMEMultipart()
            #msg['Subject'] = f'AMDI test result'
            msg['Subject'] = subject
            msg['From'] = str(varEmail.get())
            msg['To'] = str(varEmail.get())

            part = MIMEBase('application', "octet-stream")
            part.set_payload(open(fname,"rb").read())
            encoders.encode_base64(part)
            s_header_attachment = 'attachment; filename={}'.format(fname)
            #part.add_header('Content-Disposition', 'attachment; filename=fname')
            part.add_header('Content-Disposition', s_header_attachment)
            msg.attach(part)
            
            #attach image
            part = MIMEBase('application', "octet-stream")
            part.set_payload(open(filename,"rb").read())
            encoders.encode_base64(part)
            s_header_attachment = 'attachment; filename={}'.format(filename)
            #part.add_header('Content-Disposition', 'attachment; filename=fname')
            part.add_header('Content-Disposition', s_header_attachment)
            msg.attach(part)

            s = smtplib.SMTP('smtp.office365.com', 587)
            s.ehlo()
            s.starttls()
            s.ehlo()
            #passwd = "!!1234REWQ"
            if (str(varGain.get()) == ""):
                passwd = "!!1234REWQ"
            else:
                passwd = str(varGain.get())
                print('p', passwd)
            s.login(str(varEmail.get()), str(passwd))
            s.send_message(msg)
            #s.sendmail(str(varEmail.get()), str(varEmail.get()), msg)
            s.close()
                            
        #GUI

        # Define title of master widget
        self.master.title("A tk_guii")

        # Allow the widget to take the full space of the root window
        self.pack(fill=BOTH, expand=2)
        
        # Create font family:
        Title = font.Font(family="Myriad Pro", size=30, weight='bold')
        SubTitle = font.Font(family = 'Myriad Pro', size = 12)
        Buttons = font.Font(family = 'Myriad Pro', size = 12)
        BigButtons = font.Font(family = 'Myriad Pro', size = 20)
        Labels = font.Font(family = 'Myriad Pro', size = 12)
        
        # Title
        self.title = Label(root, text='Autolab - 20', fg = 'Black', font = Title )
        self.title.place(x=230,y=0)
        
        self.rev = Label(root, text='Rev.' +testRev, fg= 'Black', font = SubTitle)
        self.rev.place(x=130,y=10)

        self.rev = Label(root, text='RPI#: ' + device_num, fg = 'Orange', font = SubTitle )
        self.rev.place(x=10,y=10)
        
        
        # self.rev = Label(root, text='wob [ticks]', fg = 'Black', font = Labels )
        # self.rev.place(x=10,y=50)
        # varWob = Entry(root)
        # varWob.insert(END,'2000')
        # varWob.place(x = 10, y = 50)
        
        # Logo
        path = "ui_assets/AMDI.png"
        # Creates a Tkinter-compatible photo image, which can be used everywhere Tkinter expects an image object.
        #logo_img = ImageTk.PhotoImage(Image.open(path).resize((50, 50)))

        # The Label widget is a standard Tkinter widget used to display a text or image on the screen.
        #self.logo = Label(root, image=logo_img)
        #self.logo.image = logo_img
        #self.logo.place(x=10, y=10)

        self.varassay = Label(root, text = 'Assay name', fg = 'Blue', font = Labels )
        self.varassay.place(x = 10, y = 75)
        varAssay = Entry(root)
        varAssay.insert(END,'MA1010-CD4536')
        varAssay.place(x = 120, y = 75)

        self.varoperator = Label(root, text = 'Lsr Intensity', fg = 'Blue', font = Labels )
        self.varoperator.place(x = 300, y = 150)
        varLaz = Entry(root)
        varLaz.insert(END,'100')
        varLaz.place(x = 410, y = 150)


        self.varemail = Label(root, text = 'LED intensity', fg = 'Blue', font = Labels )
        self.varemail.place(x = 300, y = 180)
        varLED = Entry(root)
        varLED.insert(END,'10')
        varLED.place(x = 410, y = 180)

        self.varOI = Label(root, text = 'Obs1 Intensity', fg = 'Blue', font = Labels )
        self.varOI.place(x = 300, y = 210)
        varoi = Entry(root, textvariable=displayVar)
        varoi.pack()

        #varoi.insert(END, str(self.gain))
        varoi.place(x = 410, y = 210)
        
        self.varvel = Label(root, text = 'Email', fg = 'Black', font = Labels )
        self.varvel.place(x = 10, y = 100)
        varEmail= Entry(root)
        varEmail.insert(END,'lab.user@amdilabs.com')
        varEmail.place(x = 120, y = 100)  
        
        ### Camera control inputs
        
        # Exposure time
        # self.varexp = Label(root, text = 'Exp time [s]', fg = 'Black', font = Labels )
        # self.varexp.place(x = 10, y = 150)
        # varExp = Entry(root)
        # varExp.insert(END,'1')
        # varExp.place(x = 120, y = 150)
        
        # Operator Name
        
        
        
        # Gain
        self.vargain = Label(root, text = 'Passwrd', fg = 'Black', font = Labels )
        self.vargain.place(x = 10, y = 125)
        varGain = Entry(root)
        varGain.insert(END,'!!1234REWQ')
        varGain.place(x = 120, y = 125)
        
        # Gamma
        # self.vargamma = Label(root, text = 'Gamma', fg = 'Black', font = Labels )
        # self.vargamma.place(x = 10, y = 200)
        # varGamma = Entry(root)
        # varGamma.insert(END,'1')
        # varGamma.place(x = 120, y = 200)
        
        # Filename
        self.varnombre = Label(root, text = 'File Name', fg = 'Black', font = Labels )
        self.varnombre.place(x = 10, y = 150)
        varNombre = Entry(root)
        varNombre.place(x = 120, y = 150)
        
        ### Hardware control inputs
        
        # Velocity for spindle motor
        self.varvel = Label(root, text = 'Velocity [rpm]', fg = 'Black', font = Labels )
        self.varvel.place(x = 300, y = 50)
        varV = Entry(root)
        varV.insert(END,'3000')
        varV.place(x = 410, y = 50)
        
        # Acceleration
        self.varacc = Label(root, text = 'Acceleration', fg = 'Black', font = Labels )
        self.varacc.place(x = 300, y = 75)
        varAcc = Entry(root)
        varAcc.insert(END,'1000')
        varAcc.place(x=410, y = 75)
        
        # Time for laser motor
        self.vartime = Label(root, text = 'Time [s]', fg = 'Black', font = Labels )
        self.vartime.place(x = 300, y = 100)
        varTime = Entry(root)
        varTime.insert(END,'2')
        varTime.place(x=410, y = 100)
        
        # Angle for disc
        self.varangle = Label(root, text = 'Angle [deg]', fg = 'Black', font = Labels )
        self.varangle.place(x = 300, y = 125)
        varAng = Entry(root)
        varAng.insert(END,'1795')
        varAng.place(x=410, y = 125)
        
        ### Buttons

        # Spin motor at set rpm
        spinButton = Button(self, text = "Spin", font = Buttons, command = spinendlessly)
        spinButton.place(x=600, y=25)
        
        # Break motor
        stopButton = Button(self, text = 'Brake', font = Buttons, fg='Red', command = stop)
        stopButton.place(x=700, y=25)
        
        # Turn laser 1 on
        laser1Button = Button(self, text = "Lsr1", font = Buttons, command = laser1)
        laser1Button.place(x=600, y=75)
        
        # Turn laser 2 on
        laser2Button = Button(self, text = "Lsr2", font = Buttons, command = laser2)
        laser2Button.place(x=700, y=75)
        
        # Turn led1 on
        led1Button = Button(self, text = "LED O", font = Buttons, command = led1)
        led1Button.place(x=600, y=125)
        
        # Turn led2 on
        led2Button = Button(self, text = "LED W", font = Buttons, command = led2)
        led2Button.place(x=700, y=125)

        # detect laser 1
        laser12Button = Button(self, text = "Dtec1", font = Buttons, command = detector1)
        laser12Button.place(x=600, y=175)
        
        # detectlaser 2
        laser22Button = Button(self, text = "Dtec2", font = Buttons, command = detector2)
        laser22Button.place(x=700, y=175)

        ledRButton = Button(self, text = "R", font = Buttons, command = ledR)
        ledRButton.place(x=600, y=225)

        ledGButton = Button(self, text = "G", font = Buttons, command = ledG)
        ledGButton.place(x=650, y=225)

        ledBButton = Button(self, text = "B", font = Buttons, command = ledB)
        ledBButton.place(x=700, y=225)



        # # Turn lid LED O on
        # laser1Button = Button(self, text = "Lid 0", font = Buttons, command = filterLED_O)
        # laser1Button.place(x=600, y=225)
        
        # # Turn lid LED W on
        # laser2Button = Button(self, text = "Lid W", font = Buttons, command = filterLED_W)
        # laser2Button.place(x=700, y=225)

        # Turn lid LED W on
        led2Button = Button(self, text = "LidLED", font = Buttons, command = lidLED)
        led2Button.place(x=600, y=275)

        lidcamButton = Button(self, text = "LidCAM", font = Buttons, command = lidCam)
        lidcamButton.place(x=600, y=325)
        
        

        BOT_ROW = 325
        
        # Encoder position for calibration
        positionButton = Button(self, text = "Position", font = Buttons, command = donde)
        positionButton.place(x = 10, y = 180)

        # View results
        resultsButton = Button(self, text = "Lsr swp", font = Buttons, command = laserSweep)
        resultsButton.place(x=10,y=250)
        
         # Capture camera image
        captureButton = Button(self, text = "Capture", font = Buttons, command = capture)
        captureButton.place(x = 10, y = 215)

        # Run assay
        assayButton = Button(self, text = "Run Assay", font = Buttons, fg='Blue', command = assay)
        assayButton.place(x = 10, y= 285)

        #home
        findButton = Button(self, text = 'Find Index', font = Buttons, command = home, activebackground="orange")
        findButton.place(x=10, y= 320)

        # Move disc a set angle
        encoderButton = Button(self, text = "Move Angle", font = Buttons, command = move_position)
        encoderButton.place(x=10, y=355)

        # Fans
        FansButton = Button(self, text = "QR scan", font = Buttons, command = scanQRCode)
        FansButton.place(x = 10, y= 390)

        BOT_ROW_2 = 375

        # QR Scanner
        # QRButton = Button(self, text = "fans", font = Buttons, command = fans)
        # QRButton.place(x = 600, y= 275)

        BOT_ROW_2 = 375
        
        

        BOT_ROW_2 = 375
        
        # Lock lid
        lockButton = Button(self, text = 'Lock Lid', font = Buttons, command = latch)
        lockButton.place(x=130, y=320)

        # Unlock lid
        unlockButton = Button(self, text = 'Unlock Lid', font = Buttons, command = unlatch)
        unlockButton.place(x=130, y=285)

        dondeDosButton =  Button(self, text = 'Store v1', font = Buttons, command = dondeDos)
        dondeDosButton.place(x=130, y=180)

        dondeTresButton =  Button(self, text = 'Store v5', font = Buttons, command = dondeTres)
        dondeTresButton.place(x=130, y=215)

        dondeQuaButton =  Button(self, text = 'Store array', font = Buttons, command = dondeQua)
        dondeQuaButton.place(x=130, y=250)
        
        #Generate Report
        reportButton = Button(self, text = "Report", font = Buttons, fg='Blue', command = saveReport)
        reportButton.place(x = 700, y= 375)

        BOT_ROW_2 = 375

global root
global testRev
global results
global testNames
global device_num
global videoOn

testRev= '3'
videoOn = False

try:
    serialFile = open('/sys/devices/virtual/dmi/id/product_serial')
    serialNumber = serialFile.readline()[-9:-1]
    serialFile.close()
except:
   serialNumber = '00000000'

device_num = serialNumber

Result_T = {
    'NO'  :  'No Result',
    'PASS':  'Pass',
    'FAIL':  'FAIL'
}

test_Idx = {
    'Laser 1': 0,
    'Laser 2': 1,
    'Capture'   : 2,
    'Move Angle': 3,
    'Find Index': 4,
    'LED Orange': 5,
    'LED White' : 6,
    'Fans'      : 7,
    'Lock Lid'  : 8,
    'Unlock Lid': 9,
    'Scan QR'   : 10,
    'Spin Motor': 11,
    'LED Red'   : 12,
    'LED Green' : 13,
    'LED Blue'  : 14,
    'Lid cam'   : 15,
    'Lid LED'   : 16,
    'Assay'     : 17,
    'lsr1 dtec' : 18,
    'lsr2 dtec' : 19,
    'Max'       : 20
}

test_names = ('Laser 1', 'Laser 2', 'Capture','Move Angle', 'Find Index', 'LED Orange',
              'LED White', 'Fans', 'Lock Lid', 'Unlock Lid', 'Scan QR Code', 'Spin Motor', 
              'LED Red','LED Green','LED Blue')

r = (Result_T['NO'],Result_T['NO'],Result_T['NO'],Result_T['NO'],Result_T['NO'],Result_T['NO'], Result_T['NO'],
     Result_T['NO'],Result_T['NO'],Result_T['NO'],Result_T['NO'],Result_T['NO'],Result_T['NO'])
results = list(r)
testNames = list(test_names)
root = Tk()
displayVar = StringVar()

#size of the window
root.geometry("800x480")

app = Window(root)
root.mainloop()
