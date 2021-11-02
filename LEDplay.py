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

import os 
import time 
import smbus
from E20 import E20
from tkinter import *
from tkinter import font
import tkinter.messagebox as messagebox
from datetime import datetime
from PIL import Image, ImageTk
from time import sleep
import json
import subprocess
import serial
import RPi.GPIO as GPIO
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
        self.shutdown_bit    = 7
        self.data_ready_bit  = 6
        self.tc74_i2c_bus    = smbus.SMBus(bus)

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

        def filterLED_O():

            intensity = int(varEmail.get())
            LID_SENSOR_MULTIPLEXER = 0x59

            mplx=Multiplexer(1, LID_SENSOR_MULTIPLEXER)
            x = mplx.channel(0, 0x01, intensity)

        def filterLED_W():

            intensity = int(varEmail.get())
            LID_SENSOR_MULTIPLEXER = 0x59

            mplx=Multiplexer(1, LID_SENSOR_MULTIPLEXER)
            x = mplx.channel(0, 0x02, intensity)


        # Keeps spinning forever at given rpm
        def spinendlessly():
            #self.e20.motor.spin_settings()
            acc = int(varAcc.get())
            vel = int(varV.get())
            self.e20.motor.set_acceleration(acc)
            #self.e20.motor.stop()
            self.e20.motor.spin(vel)

        # Move disc at given angle
        def move_position():
            #self.e20.motor.position_settings()
            pos =float(varAng.get())
            self.e20.motor.position_abs(int(pos))
            

        # Spins disc until index position is found 
        def home():
            #self.e20.motor.position_settings()
            #self.e20.motor.set_acceleration(10)
            #self.e20.motor.spin(500, 3)
            #self.e20.motor.position_abs(0)
            self.e20.motor.home()
            self.e20.motor.position_abs(0)

        def detect1():

            if GPIO.input(LV1_PS_PIN) == LV1_PS_ON:
                print('laser1 is detected')
                messagebox.showinfo('laser1 detected by lid')
            
            else:
                print('laser1 is NOT! detected')

        def detect2():

            if GPIO.input(LV2_PS_PIN) == LV2_PS_ON:
                print('laser2 is detected')
                messagebox.showinfo('laser2 detected by lid')
            
            else:
                print('laser2 is NOT! detected')

        def detector1():

            detect1()
            self.e20.laser1.set_intensity(LASER_1, 200)
            self.e20.laser1.on()
            detect1()
            self.e20.laser1.off()
            sleep(1)
            detect1()


        def detector2():

            detect2()
            self.e20.laser2.set_intensity(LASER_2, 200)
            self.e20.laser2.on()
            detect2()
            self.e20.laser2.off()
            sleep(1)
            detect2()

                

            

        # Fires laser 1
        # def laser1():
        #     t = float(varTime.get())
        #     self.e20.laser1.on_time(t)

        def laser1():
            t = float(varTime.get())
            self.e20.laser1.set_intensity(LASER_1, 800)
            self.e20.laser1.on()
            sleep(t)
            self.e20.laser1.off()
            
                
        # Fires laser 2
        def laser2():
            t = float(varTime.get())
            self.e20.laser2.set_intensity(LASER_2, 800)
            self.e20.laser2.on()
            sleep(t)
            self.e20.laser2.off()
            
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
            #t = float(varTime.get())
            #self.e20.led1(t)
            self.e20.camera.flash_on()
            sleep(4)
            self.e20.camera.flash_off()
           
        # LED 2
        # def led2():
        #     t = float(varTime.get())
        #     self.e20.led2(t)

        def led2():
            #t = float(varTime.get())
            GPIO.output(WHITE_LED, LED_ON)
            #logging.info("LED on.")
            sleep(4)
            GPIO.output(WHITE_LED, LED_OFF)
           
 
       # Fans
        def fans():
            t = float(varTime.get())
            self.e20.fans(t) 
            
 
        # Captures image with given input settings    
        def capture():
            exposure = float(varExp.get())*1000000
            gain = float(varGain.get())
            gamma = float(varGamma.get())
            nombre = str(varNombre.get())
            date = str(datetime.now().strftime("%m-%d-%Y_%I:%M:%S_%p"))
            global filename
            filename = "/home/autolab/Desktop/images/%s-%s.tiff" % (nombre, date)
            print("filename=", filename)
            self.e20.camera.capture(
                                    flash=True,
                                    filename=filename)
                                    
            
                       
        def scanQRCode():
            process = subprocess.run('/opt/amdi/bin/QRreader',shell=True)
            
                   
        def assay():
            cycles = int(varOperator.get())
            nombre = str(varNombre.get())
            sleeper = int(varEmail.get())
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
            
        
        def test():
            self.e20.run_test

        def latch():
            self.e20.lock_lid()
            

        def unlatch():
            self.e20.unlock_lid()
            

        def stop():
            self.e20.motor.stop()
            self.e20.motor.motor_release()

        def dondeDos():
            self.e20.motor.position_settings()
            self.e20.motor.position_abs(self.v1)
            sleep(5)
            count = self.e20.motor.get_actual_encoder_count_modulo()
            msgBox=messagebox.askquestion('Is this pos. optimal?', count)
            if (msgBox == 'no'):
                messagebox.showinfo('Adjust to position')
                self.e20.motor.brake()
                sleep(5)
                count = self.e20.motor.get_actual_encoder_count_modulo()
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
        
       
                            
        #GUI

        # Define title of master widget
        self.master.title("LED play POW!")

        # Allow the widget to take the full space of the root window
        self.pack(fill=BOTH, expand=2)
        
        # Create font family:
        Title = font.Font(family="Myriad Pro", size=30, weight='bold')
        SubTitle = font.Font(family = 'Myriad Pro', size = 10)
        Buttons = font.Font(family = 'Myriad Pro', size = 16)
        BigButtons = font.Font(family = 'Myriad Pro', size = 20)
        Labels = font.Font(family = 'Myriad Pro', size = 12)
        
        # Title
        self.title = Label(root, text='Autolab - 20', fg = 'Black', font = Title )
        self.title.place(x=230,y=0)
        
        self.rev = Label(root, text='Rev.' +testRev, fg= 'Black', font = SubTitle)
        self.rev.place(x=300,y=50)
        
        
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

        self.varemail = Label(root, text = 'Intensity', fg = 'Blue', font = Labels )
        self.varemail.place(x = 10, y = 100)
        varEmail = Entry(root)
        varEmail.insert(END,'1')
        varEmail.place(x = 120, y = 100)
        
        self.varvel = Label(root, text = 'Password', fg = 'Black', font = Labels )
        self.varvel.place(x = 10, y = 125)
        varPasswd = Entry(root)
        varPasswd.insert(END,'')
        varPasswd.place(x = 120, y = 125)  
        
        ### Camera control inputs
        
        # Exposure time
        self.varexp = Label(root, text = 'Exp time [s]', fg = 'Black', font = Labels )
        self.varexp.place(x = 10, y = 150)
        varExp = Entry(root)
        varExp.insert(END,'1')
        varExp.place(x = 120, y = 150)
        
        # Operator Name
        self.varoperator = Label(root, text = 'Cycles', fg = 'Blue', font = Labels )
        self.varoperator.place(x = 10, y = 75)
        varOperator = Entry(root)
        varOperator.insert(END,'3')
        varOperator.place(x = 120, y = 75)
        
        
        # Gain
        self.vargain = Label(root, text = 'Gain [db]', fg = 'Black', font = Labels )
        self.vargain.place(x = 10, y = 175)
        varGain = Entry(root)
        varGain.insert(END,'0.2')
        varGain.place(x = 120, y = 175)
        
        # Gamma
        self.vargamma = Label(root, text = 'Gamma', fg = 'Black', font = Labels )
        self.vargamma.place(x = 10, y = 200)
        varGamma = Entry(root)
        varGamma.insert(END,'1')
        varGamma.place(x = 120, y = 200)
        
        # Filename
        self.varnombre = Label(root, text = 'File Name', fg = 'Black', font = Labels )
        self.varnombre.place(x = 10, y = 225)
        varNombre = Entry(root)
        varNombre.place(x = 120, y = 225)
        
        ### Hardware control inputs
        
        
        
        ### Buttons

        # Capture camera image
        captureButton = Button(self, text = "Capture", font = Buttons, command = capture)
        captureButton.place(x = 10, y = 275)

        # Spin motor at set rpm
        spinButton = Button(self, text = "Spin", font = Buttons, command = spinendlessly)
        spinButton.place(x=600, y=25)
        
        # Break motor
        stopButton = Button(self, text = 'Brake', font = Buttons, fg='Red', command = stop)
        stopButton.place(x=700, y=25)
        
        # Turn laser 1 on
        laser1Button = Button(self, text = "0 dim", font = Buttons, command = filterLED_O)
        laser1Button.place(x=600, y=75)
        
        # Turn laser 2 on
        laser2Button = Button(self, text = "W dim", font = Buttons, command = filterLED_W)
        laser2Button.place(x=700, y=75)
        
        # Turn led1 on
        led1Button = Button(self, text = "LED O", font = Buttons, command = led1)
        led1Button.place(x=600, y=125)
        
        # Turn led2 on
        led2Button = Button(self, text = "LED W", font = Buttons, command = led2)
        led2Button.place(x=700, y=125)

       

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
    'Max'       : 11
}

test_names = ('Laser 1', 'Laser 2', 'Capture','Move Angle', 'Find Index', 'LED Orange',
              'LED White', 'Fans', 'Lock Lid', 'Unlock Lid', 'Scan QR Code')

r = (Result_T['NO'],Result_T['NO'],Result_T['NO'],Result_T['NO'],Result_T['NO'],Result_T['NO'], Result_T['NO'],
     Result_T['NO'],Result_T['NO'],Result_T['NO'],Result_T['NO'],)
results = list(r)
testNames = list(test_names)
root = Tk()

#size of the window
root.geometry("800x480")

app = Window(root)
root.mainloop()
