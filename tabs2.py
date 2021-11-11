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


import cv2
import smbus
import os 
from E20 import E20
from tkinter import *
from tkinter import font
from tkinter import ttk
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
from settings import LED_ON, LED_OFF, MOVE_COMPLETED


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
        self.gainState       = 0x0b
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

    def read_gainMode(self):
        gain1 = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.gainState)

        return gain1

    def Gain1on(self):
        gain1 = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.gainState)

        if gain1==2:
            self.tc74_i2c_bus.write_byte_data(self.devaddr, self.gainState, 3)

        else:
             self.tc74_i2c_bus.write_byte_data(self.devaddr, self.gainState, 1)
       
    
    def Gain1off(self):
        gain1 = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.gainState)

        if gain1==2 or gain1==3:
            self.tc74_i2c_bus.write_byte_data(self.devaddr, self.gainState, 2)

        else:
             self.tc74_i2c_bus.write_byte_data(self.devaddr, self.gainState, 0)



    def Gain2on(self):
        gain1 = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.gainState)

        if gain1==1:
            self.tc74_i2c_bus.write_byte_data(self.devaddr, self.gainState, 3)

        else:
            self.tc74_i2c_bus.write_byte_data(self.devaddr, self.gainState, 2)


        

    def Gain2off(self):
        gain1 = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.gainState)

        if gain1==0 or gain1==1:
            print('gain 2 off')

        elif gain1==2:
            self.tc74_i2c_bus.write_byte_data(self.devaddr, self.gainState, 0)

        elif gain1==3:
            self.tc74_i2c_bus.write_byte_data(self.devaddr, self.gainState, 1)


        
        #self.tc74_i2c_bus.write_byte_data(self.devaddr, self.gainState, 1)

    
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
    count = 0
    dt1 = 'Not Detected'
    dt2 = 'Not Detected'

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
            self.count = self.e20.motor.get_actual_encoder_count()
            print('position=',self.count)
            updateP()
            msgBox=messagebox.askquestion('Position','What is the position?')
            if (msgBox == 'yes'):
                positionButton["bg"] = "green"
                results[test_Idx['Position']] = Result_T['PASS']
            else:
                positionButton["bg"] = "red"
                results[test_Idx['Position']] = Result_T['FAIL']

        def updateP():
            p = str(self.count)
            posiVar.set(p)

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
                encoderButton["bg"] = "green"
                results[test_Idx['Move Position']] = Result_T['PASS']
            else:
                encoderButton["bg"] = "red"
                results[test_Idx['Move Position']] = Result_T['FAIL']
            

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
                d1Var.set('Detected')
                #messagebox.showinfo('laser1 detected by lid')
                return False
            
            else:
                print('laser1 is NOT! detected')
                d1Var.set('NOT! Detected')
                return True


        def detect2():

            if GPIO.input(LV2_PS_PIN) == LV2_PS_ON:
                print('laser2 is detected')
                d2Var.set('Detected')
                #messagebox.showinfo('laser2 detected by lid')
                return False
            
            else:
                print('laser2 is NOT! detected')
                d2Var.set('NOT! Detected')
                return True

        def deeter1():
            detect1()
            self.e20.laser1.set_intensity(LASER_1, 100)

            start = time.time()
            t = 2
            self.e20.laser1.on()

            while True:
                ct = time.time()
                et = ct - start
                detect1()
                print('et=' , et)

                if et > t:
                    break

            self.e20.laser1.off()

        def deeter2():
            detect2()
            self.e20.laser2.set_intensity(LASER_2, 100)

            start = time.time()
            t = 2
            self.e20.laser2.on()

            while True:
                ct = time.time()
                et = ct - start
                detect2()
                print('et=' , et)

                if et > t:
                    break

            self.e20.laser2.off()



        # def detector1():

        #     detect1()
        #     self.e20.laser1.set_intensity(LASER_1, 100)
        #     self.e20.laser1.on()
        #     x = False
        #     while x == False:
        #         x = detect1()

        #     self.e20.laser1.off()
        #     sleep(1)
            
        #     detect1()
        #     msgBox=messagebox.askquestion('lsr1 detect','Was laser1 detected?')
        #     if (msgBox == 'yes'):
        #         laser12Button["bg"] = "green"
        #         results[test_Idx['lsr1 dtec']] = Result_T['PASS']
        #     else:
        #         laser12Button["bg"] = "red"
        #         results[test_Idx['lsr1 dtec']] = Result_T['FAIL']


        # def detector2():

        #     detect2()
        #     self.e20.laser2.set_intensity(LASER_2, 100)
        #     self.e20.laser2.on()
        #     x = False
        #     while x == False:
        #         x= detect2()
          
        #     self.e20.laser2.off()
        #     sleep(1)
        #     detect2()
        #     msgBox=messagebox.askquestion('lsr2 detect','Was laser2 detected?')
        #     if (msgBox == 'yes'):
        #         laser22Button["bg"] = "green"
        #         results[test_Idx['lsr2 dtec']] = Result_T['PASS']
        #     else:
        #         laser22Button["bg"] = "red"
        #         results[test_Idx['lsr2 dtec']] = Result_T['FAIL']


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
            sleep(t)
            x = mplx.channel(0, 0x01, 0)
            msgBox=messagebox.askquestion('Lid LED','Did the lid LED turn on?')
            if (msgBox == 'yes'):
                ledLButton["bg"] = "green"
                results[test_Idx['Lid LED']] = Result_T['PASS']
            else:
                ledLButton["bg"] = "red"
                results[test_Idx['Lid LED']] = Result_T['FAIL']  
           


        def updateL():
            x = str(self.gain)
            gainVar.set(x)

        def updateL2():
            x = str(self.gain2)
            gain2Var.set(x)

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
            updateL()
            msgBox=messagebox.askquestion('Laser 1','Did the laser 1 go on?')
            if (msgBox == 'yes'):
                laser1Button["bg"] = "green"
                results[test_Idx['Laser 1']] = Result_T['PASS']
                #print("rsults[{}]= Pass".format(test_Idx['Laser 1 On']))
            else:
                laser1Button["bg"] = "red"
                results[test_Idx['Laser 1']] = Result_T['FAIL']
                #print("rsults[{}]= Fail".format(test_Idx['Laser 1 On']))
            
                
        # Fires laser 2
        def laser2():
            s = int(varLaz.get())
            t = float(varTime.get())
            self.e20.laser2.set_intensity(LASER_2, s)
            self.e20.laser2.on()
            self.gain2 = gainer2()
            print('G2 = ', self.gain2)
            sleep(t)
            self.e20.laser2.off()
            updateL2()
            msgBox=messagebox.askquestion('Laser 2','Did the laser 2 go on?')
            if (msgBox == 'yes'):
                laser2Button["bg"] = "green"
                results[test_Idx['Laser 2']] = Result_T['PASS']
            else:
                laser2Button["bg"] = "red"
                results[test_Idx['Laser 2']] = Result_T['FAIL']  
            

        def lid_cal1():
            if self.e20.motor.reset_pid:
                self.e20.motor.pid_reset()

            self.e20.motor.position_abs(145)
            while not self.e20.motor.info(check_bit=MOVE_COMPLETED):
                pass
            sleep(2)

            self.e20.laser1.set_intensity(LASER_1, 0)
            self.e20.laser1.on()
            self.gain = gainer()
            updateL()
            msgBox=messagebox.askquestion('Lid','hows position?')
            if (msgBox == 'yes'):
                self.e20.laser1.on()
                posi = self.e20.motor.controller.get_actual_encoder_count_modulo()
                print('lidcal1=', posi)


            else:
                messagebox.showinfo('Adjust to position')
                self.e20.motor.motor_release()
                











        def laserSweep():
            pos = float(varAng.get())
            self.e20.laser_sweep(start_tick=pos,
                                width=17,
                                delay=1.01,
                                steps=6)



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

        def gainOut():

            LID_SENSOR_MULTIPLEXER = 0x49
            tc74_sensor = TC74(1, LID_SENSOR_MULTIPLEXER)  # temp sensor on bus 1 address 0x48
            gain = str(tc74_sensor.read_gainMode())
            gainMode.set(gain)

        def Gain1on():

            LID_SENSOR_MULTIPLEXER = 0x49
            tc74_sensor = TC74(1, LID_SENSOR_MULTIPLEXER)  # temp sensor on bus 1 address 0x48
            gain = str(tc74_sensor.Gain1on())


        def Gain1off():

            LID_SENSOR_MULTIPLEXER = 0x49
            tc74_sensor = TC74(1, LID_SENSOR_MULTIPLEXER)  # temp sensor on bus 1 address 0x48
            gain = str(tc74_sensor.Gain1off())

        def Gain2on():

            LID_SENSOR_MULTIPLEXER = 0x49
            tc74_sensor = TC74(1, LID_SENSOR_MULTIPLEXER)  # temp sensor on bus 1 address 0x48
            gain = str(tc74_sensor.Gain2on())

        def Gain2off():

            LID_SENSOR_MULTIPLEXER = 0x49
            tc74_sensor = TC74(1, LID_SENSOR_MULTIPLEXER)  # temp sensor on bus 1 address 0x48
            gain = str(tc74_sensor.Gain2off())


 
       # Fans
        def fans():
            t = float(varTime.get())
            self.e20.fans(t) 

        def lidCam():
            global nombre
            nombre = str(varNombre.get())
            nombre = '/home/autolab/Desktop/images/'+nombre
            cmd = 'v4l2-ctl --set-fmt-video=width=640,height=480,pixelformat=JPEG --stream-mmap --stream-count=1 --stream-to=%s.jpg --device /dev/video0' % nombre
            #print('p:', cmd)
            intensity = int(varLED.get())
            LID_LED_MULTIPLEXER = 0x49

            mplx=Multiplexer(1, LID_LED_MULTIPLEXER)
            x = mplx.channel(0, 0x01, intensity)
            sleep(1)
            os.system(cmd)
            x = mplx.channel(0, 0x01, 0)

            nombre = str(nombre + ".jpg")
            gray_img=cv2.imread(nombre,0) 
            windowname = "disc"
            
            cv2.namedWindow(windowname, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(windowname, (440,240))
            cv2.imshow(windowname, gray_img)
            cv2.waitKey(0) #5000
            cv2.destroyWindow(windowname)

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


            input_file=filename
            gray_img=cv2.imread(input_file,0) 
            #cv2.putText(gray_img,'Array',(500,280), cv2.FONT_HERSHEY_SIMPLEX, 12,(255,0,0),2)

            windowname = "array"
            cv2.namedWindow(windowname, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(windowname, (440,240))
            cv2.imshow(windowname, gray_img)
            cv2.waitKey(0) #5000
            cv2.destroyWindow(windowname)
            #display_image(gray_img, 'Detected circles', 5000)
            msgBox=messagebox.askquestion('Cam','Did camera capture a .tiff?')
            if (msgBox == 'yes'):
                captureButton["bg"] = "green"
                results[test_Idx['Capture']] = Result_T['PASS']
            else:
                captureButton["bg"] = "red"
                results[test_Idx['Capture']] = Result_T['FAIL']
            
                                    
            
                       
        def scanQRCode():
            process = subprocess.run('/opt/amdi/bin/QRreader',shell=True)
            msgBox=messagebox.askquestion('QR scanner','Did QR scanner work?')
            if (msgBox == 'yes'):
                FansButton["bg"] = "green"
                results[test_Idx['Scan QR']] = Result_T['PASS']
            else:
                FansButton["bg"] = "red"
                results[test_Idx['Scan QR']] = Result_T['FAIL']
            
                   

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
            while not self.e20.motor.flag_info(check_bit=MOVE_COMPLETED):
                pass
            sleep(2)
            
            goodPos = False
            count = self.e20.motor.controller.get_actual_encoder_count_modulo()
            msgBox=messagebox.askquestion('Is this pos. optimal?', count)
            while goodPos == False:

                if (msgBox == 'yes'):
                    self.v1 = count
                    print('position=', self.v1)
                    goodPos = True   

                else:
                    messagebox.showinfo('Adjust to position')
                    self.e20.motor.motor_release()
                    sleep(5)
                    count = self.e20.motor.controller.get_actual_encoder_count_modulo()
                    msgBox=messagebox.askquestion('Is this pos. optimal?', count)

                 

        def dondeTres():
            if self.e20.motor.reset_pid:
                self.e20.motor.pid_reset()

            self.e20.motor.position_abs(self.v5)
            while not self.e20.motor.flag_info(check_bit=MOVE_COMPLETED):
                pass
            sleep(2)
            
            goodPos = False
            count = self.e20.motor.controller.get_actual_encoder_count_modulo()
            msgBox=messagebox.askquestion('Is this pos. optimal?', count)
            while goodPos == False:

                if (msgBox == 'yes'):
                    self.v5 = count
                    print('position=', self.v5)
                    goodPos = True   

                else:
                    messagebox.showinfo('Adjust to position')
                    self.e20.motor.motor_release()
                    sleep(5)
                    count = self.e20.motor.controller.get_actual_encoder_count_modulo()
                    msgBox=messagebox.askquestion('Is this pos. optimal?', count)



        def dondeQua():
            if self.e20.motor.reset_pid:
                self.e20.motor.pid_reset()

            self.e20.motor.position_abs(self.va)
            while not self.e20.motor.flag_info(check_bit=MOVE_COMPLETED):
                pass
            sleep(2)
            
            goodPos = False
            count = self.e20.motor.controller.get_actual_encoder_count_modulo()
            msgBox=messagebox.askquestion('Is this pos. optimal?', count)
            while goodPos == False:

                if (msgBox == 'yes'):
                    self.va = count
                    print('position=', self.va)
                    goodPos = True   

                else:
                    messagebox.showinfo('Adjust to position')
                    self.e20.motor.motor_release()
                    sleep(5)
                    count = self.e20.motor.controller.get_actual_encoder_count_modulo()
                    msgBox=messagebox.askquestion('Is this pos. optimal?', count)
        
        def store():
            print('v1=', self.v1)
            print('v5=', self.v5)
            print('Array=', self.va)

            date = str(datetime.now().strftime("%m-%d-%Y_%I:%M:%S_%p"))
            global jd2
            jd2 = {}
           # jd["Motor Serial Number"] = motorID
           # jd["Camera Serial Number"] = camID
           # jd["Device Number"] = device_num
            #jd2["Date Time"] = date
            jd2["valve1"] = self.v1
            jd2["Valve5"] = self.v5
            jd2["Array"] = self.va 

            jsonP_file = open("/data/tmp.json", "w")
            json.dump(jd2, jsonP_file)
            jsonP_file.close()
            with open("/data/tmp.json") as jsonP_file:
                jsonP_object = json.load(jsonP_file)
            jsonP_file.close()
            #print(jsonP_object)
        
        def saveReport():
            
            date = str(datetime.now().strftime("%m-%d-%Y_%I:%M:%S_%p"))
            #device_num = cpuserial
            jd = {}
            #jd2 = {}
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

            json2_file = open("/data/pos.json", "w")
            json.dump(jd2, json2_file)
            json2_file.close()
            with open("/data/pos.json") as json2_file:
                json2_object = json.load(json2_file)
            json2_file.close()
            print(json2_object)

            build_direction = "LEFT_TO_RIGHT"
            table_attributes = {"style" : "width:100%", "text-align" : "center", "rules" : "all", "border" : "1"}
            json_html = convert(json_object, build_direction=build_direction, table_attributes=table_attributes)
            json2_html = convert(json2_object, build_direction=build_direction, table_attributes=table_attributes)

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
            f.write("\n".encode())
            f.write("\n".encode())
            f.write(json2_html.encode())
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

            part = MIMEBase('application', "octet-stream")
            part.set_payload(open(nombre,"rb").read())
            encoders.encode_base64(part)
            s_header_attachment = 'attachment; filename={}'.format(nombre)
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
        Buttons = font.Font(family = 'Myriad Pro', size = 16)
        BigButtons = font.Font(family = 'Myriad Pro', size = 20)
        Labels = font.Font(family = 'Myriad Pro', size = 16)
        
        # Title
        self.title = Label(tab2, text='Laser', fg = 'Black', font = BigButtons )
        self.title.place(x=80,y=20)

        self.title = Label(tab2, text='LED', fg = 'Black', font = BigButtons )
        self.title.place(x=550,y=20)

        # Title
        self.title = Label(tab3, text='Camera', fg = 'Black', font = BigButtons )
        self.title.place(x=80,y=20)

        self.title = Label(tab3, text='Bits', fg = 'Black', font = BigButtons )
        self.title.place(x=550,y=20)

        self.title = Label(tab3, text='Press (q) to exit img', fg = 'Black', font = SubTitle)
        self.title.place(x=190,y=220)
        
        
        self.rev = Label(tab4, text='Rev.' +testRev, fg= 'Black', font = SubTitle)
        self.rev.place(x=130,y=30)

        self.rev = Label(tab4, text='RPI#: ' + device_num, fg = 'Orange', font = SubTitle )
        self.rev.place(x=10,y=30)
        
        
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

        self.varassay = Label(tab4, text = 'Assay name', fg = 'Blue', font = Labels )
        self.varassay.place(x = 10, y = 75)
        varAssay = Entry(tab4)
        varAssay.insert(END,'MA1010-CD4536')
        varAssay.place(x = 120, y = 75)
        
        self.varvel = Label(tab4, text = 'Email', fg = 'Black', font = Labels )
        self.varvel.place(x = 10, y = 100)
        varEmail= Entry(tab4)
        varEmail.insert(END,'lab.user@amdilabs.com')
        varEmail.place(x = 120, y = 100)  
        
        # Gain
        self.vargain = Label(tab4, text = 'Passwrd', fg = 'Black', font = Labels )
        self.vargain.place(x = 10, y = 125)
        varGain = Entry(tab4)
        varGain.insert(END,'!!1234REWQ')
        varGain.place(x = 120, y = 125)
        
        # Filename
        self.varnombre = Label(tab3, text = 'File Name', fg = 'Black', font = Labels )
        self.varnombre.place(x = 10, y = 150)
        varNombre = Entry(tab3)
        varNombre.place(x = 120, y = 150)
        
        ### Motor textboxes x buttons
        
        # Velocity for spindle motor
        self.varvel = Label(tab1, text = 'Velocity [rpm]', fg = 'Black', font = Labels )
        self.varvel.place(x = 10, y = 50)
        varV = Entry(tab1)
        varV.insert(END,'3000')
        varV.place(x = 150, y = 50)
        
        # Acceleration
        self.varacc = Label(tab1, text = 'Acceleration', fg = 'Black', font = Labels )
        self.varacc.place(x = 10, y = 75)
        varAcc = Entry(tab1)
        varAcc.insert(END,'1000')
        varAcc.place(x=150, y = 75)
        
        # Time for laser motor
        self.vartime = Label(tab1, text = 'Time [s]', fg = 'Black', font = Labels )
        self.vartime.place(x = 10, y = 100)
        varTime = Entry(tab1)
        varTime.insert(END,'2')
        varTime.place(x=150, y = 100)
        
        # Angle for disc
        self.varangle = Label(tab1, text = 'Go to [ticks]', fg = 'Black', font = Labels )
        self.varangle.place(x = 10, y = 125)
        varAng = Entry(tab1)
        varAng.insert(END,'1795')
        varAng.place(x=150, y = 125)

        self.varpos = Label(tab1, text = 'Position @', fg = 'Blue', font = Labels )
        self.varpos.place(x = 10, y = 150)
        varPOS = Entry(tab1, textvariable=posiVar)
        varPOS.pack()
        varPOS.place(x = 150, y = 150)

        # Spin motor at set rpm
        spinButton = Button(tab1, text = "Spin", font = Buttons, command = spinendlessly)
        spinButton.place(x=330, y=25)
        
        # Break motor
        stopButton = Button(tab1, text = 'Brake', font = Buttons, fg='Red', command = stop)
        stopButton.place(x=330, y=70)

        # Move disc a set angle
        encoderButton = Button(tab1, text = "Move Position", font = Buttons, command = move_position)
        encoderButton.place(x=330, y=105)

        # Encoder position for calibration
        positionButton = Button(tab1, text = "Position", font = Buttons, command = donde)
        positionButton.place(x = 330, y = 150)

        #home
        findButton = Button(tab1, text = 'Find Index', font = Buttons, command = home, activebackground="orange")
        findButton.place(x=330, y= 195)

        exportButton = Button(tab1, text = 'Export positions', font = BigButtons, command = store, activebackground="orange")
        exportButton.place(x=350, y= 255)

        

        dondeDosButton =  Button(tab1, text = 'Store v1', font = Buttons, command = dondeDos)
        dondeDosButton.place(x=30, y=200)

        dondeTresButton =  Button(tab1, text = 'Store v5', font = Buttons, command = dondeTres)
        dondeTresButton.place(x=30, y=235)

        dondeQuaButton =  Button(tab1, text = 'Store array', font = Buttons, command = dondeQua)
        dondeQuaButton.place(x=30, y=270)
        

        # Lasers & lights 


        self.varoperator = Label(tab2, text = 'Lsr Intensity', fg = 'Blue', font = Labels )
        self.varoperator.place(x = 10, y = 50)
        varLaz = Entry(tab2)
        varLaz.insert(END,'100')
        varLaz.place(x = 150, y = 50)


        self.varemail = Label(tab2, text = 'LED intensity', fg = 'Blue', font = Labels )
        self.varemail.place(x = 440, y = 60)
        varLED = Entry(tab2)
        varLED.insert(END,'10')
        varLED.place(x = 575, y = 60)

        self.varOI = Label(tab2, text = 'Obs1 Intensity', fg = 'Blue', font = Labels )
        self.varOI.place(x = 110, y = 85)
        varoi = Entry(tab2, textvariable=gainVar)
        varoi.pack()
        varoi.place(x = 260, y = 85)

        self.varOI2 = Label(tab2, text = 'Obs2 Intensity', fg = 'Blue', font = Labels )
        self.varOI2.place(x = 110, y = 130)
        varoi2 = Entry(tab2, textvariable=gain2Var)
        varoi2.pack()
        varoi2.place(x = 260, y = 130)

        self.vard1= Label(tab2, text = 'L1 Detection', fg = 'Blue', font = Labels )
        self.vard1.place(x = 150, y = 180)
        
        varD1 = Entry(tab2, textvariable=d1Var)
        varD1.pack()
        varD1.place(x = 280, y = 180)
        varD1.insert(END,'Not detected')

        self.vard2 = Label(tab2, text = 'L2 Detection', fg = 'Blue', font = Labels )
        self.vard2.place(x = 150, y = 225)
        varD2 = Entry(tab2, textvariable=d2Var)
        varD2.pack()
        varD2.place(x = 280, y = 225)
        varD2.insert(END,'Not detected')

        self.gMode = Label(tab2, text = '', fg = 'Blue', font = Labels)
        self.gMode.place(x = 140, y = 305)
        gMode = Entry(tab2, textvariable=gainMode)
        gMode.pack()
        gMode.place(x = 140, y = 305)
        gMode.insert(END, 'n/a')

        # Turn laser 1 on
        laser1Button = Button(tab2, text = "Lsr1", font = Buttons, command = laser1)
        laser1Button.place(x=10, y=85)
        
        # Turn laser 2 on
        laser2Button = Button(tab2, text = "Lsr2", font = Buttons, command = laser2)
        laser2Button.place(x=10, y=130)

        # View results
        resultsButton = Button(tab2, text = "Lsr1 swp", font = Buttons, command = lid_cal1)
        resultsButton.place(x=300,y=385)

        gainButton =  Button(tab2, text = "Gain State", font = Buttons, command = gainOut)
        gainButton.place(x=10,y=305)

        gain1onButton = Button(tab2, text = "G1-0", font = SubTitle, command = Gain1on)
        gain1onButton.place(x=10, y=335)

        gain1offButton = Button(tab2, text = "G1-1", font = SubTitle, command = Gain1off)
        gain1offButton.place(x=70, y=335)

        gain2onButton = Button(tab2, text = "G2-0", font = SubTitle, command = Gain2on)
        gain2onButton.place(x=130, y=335)

        gain2offButton = Button(tab2, text = "G2-1", font = SubTitle, command = Gain2off)
        gain2offButton.place(x=190, y=335)


        
        
        # Turn led1 on
        led1Button = Button(tab2, text = "LED O", font = Buttons, command = led1)
        led1Button.place(x=540, y=105)
        
        # Turn led2 on
        led2Button = Button(tab2, text = "LED W", font = Buttons, command = led2)
        led2Button.place(x=540, y=150)

        # detect laser 1
        laser12Button = Button(tab2, text = "Detect L1", font = Buttons, command = deeter1)
        laser12Button.place(x=10, y=180)
        
        # detectlaser 2
        laser22Button = Button(tab2, text = "Detect L2", font = Buttons, command = deeter2)
        laser22Button.place(x=10, y=225)

        ledRButton = Button(tab2, text = "R", font = Buttons, command = ledR)
        ledRButton.place(x=600, y=235)

        ledGButton = Button(tab2, text = "G", font = Buttons, command = ledG)
        ledGButton.place(x=650, y=235)

        ledBButton = Button(tab2, text = "B", font = Buttons, command = ledB)
        ledBButton.place(x=700, y=235)

        # Turn lid LED W on
        ledLButton = Button(tab2, text = "LidLED", font = Buttons, command = lidLED)
        ledLButton.place(x=540, y=195)
        

        
         # Capture camera image
        captureButton = Button(tab3, text = "Capture", font = Buttons, command = capture)
        captureButton.place(x = 80, y = 215)

        lidcamButton = Button(tab3, text = "LidCAM", font = Buttons, command = lidCam)
        lidcamButton.place(x=80, y=265)
        

        # Run assay
        assayButton = Button(tab4, text = "Run Assay", font = Buttons, fg='Blue', command = assay)
        assayButton.place(x = 10, y= 285)

        

        # Fans
        FansButton = Button(tab3, text = "QR scan", font = Buttons, command = scanQRCode)
        FansButton.place(x = 500, y= 210)

        BOT_ROW_2 = 375

        # QR Scanner
        # QRButton = Button(self, text = "fans", font = Buttons, command = fans)
        # QRButton.place(x = 600, y= 275)

        BOT_ROW_2 = 375
        
        

        BOT_ROW_2 = 375
        
        # Lock lid
        lockButton = Button(tab3, text = 'Lock Lid', font = Buttons, command = latch)
        lockButton.place(x=500, y=120)

        # Unlock lid
        unlockButton = Button(tab3, text = 'Unlock Lid', font = Buttons, command = unlatch)
        unlockButton.place(x=500, y=165)

        
        
        #Generate Report
        reportButton = Button(tab4, text = "Report", font = BigButtons, fg='Blue', command = saveReport)
        reportButton.place(x = 600, y= 275)

        
        

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
    'Laser 1'   : 0,
    'Laser 2'   : 1,
    'Capture'   : 2,
    'Move Position': 3,
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
    'Position'  : 20,
    'Max'       : 21
}

test_names = ('Laser 1', 'Laser 2', 'Capture','Move Position', 'Find Index', 
              'LED Orange','LED White', 'Fans', 'Lock Lid', 'Unlock Lid', 
              'Scan QR Code', 'Spin Motor', 'LED Red','LED Green','LED Blue',
              'Lid cam', 'Lid LED', 'Assay', 'lsr1 dtec', 'lsr2 dtec', 
              'Position', 'Max')

r = (Result_T['NO'],Result_T['NO'],Result_T['NO'],Result_T['NO'],
     Result_T['NO'],Result_T['NO'], Result_T['NO'],Result_T['NO'],
     Result_T['NO'],Result_T['NO'],Result_T['NO'],Result_T['NO'],
     Result_T['NO'],Result_T['NO'],Result_T['NO'],Result_T['NO'],
     Result_T['NO'],Result_T['NO'],Result_T['NO'],Result_T['NO'],
     Result_T['NO'],Result_T['NO'])

     
results = list(r)
testNames = list(test_names)
root = Tk()


gainVar = StringVar()
gain2Var = StringVar()
posiVar = StringVar()
d1Var = StringVar()
d2Var = StringVar()
gainMode = StringVar()

#size of the window
root.geometry("800x480")

tabControl = ttk.Notebook(root, width=800, height=480)

tab1 = ttk.Frame(tabControl)
tab2 = ttk.Frame(tabControl)
tab3 = ttk.Frame(tabControl)
tab4 = ttk.Frame(tabControl)
#tab5 = ttk.Frame(tabControl)
  
tabControl.add(tab1, text ='Motor')
tabControl.add(tab2, text ='Laser/LED')
tabControl.add(tab3, text ='Camera +')
tabControl.add(tab4, text ='Assay')
#tabControl.add(tab5, text ='bits')



tabControl.pack(expand = 1, fill ="both")



app = Window(root)
root.mainloop()
