from time import sleep
import logging
import inspect
import smbus
import RPi.GPIO as GPIO
from settings import LOGGING_FILE


logging.basicConfig(filename=LOGGING_FILE, level=logging.INFO, format='%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


def lineno():  # returns string
    """Returns the current line number in our program."""
    return (__file__.split('/')[len(__file__.split('/'))-1]
            + ': '
            + str(inspect.currentframe().f_back.f_code.co_name)
            + '() +'
            + str(inspect.currentframe().f_back.f_lineno))

class Multiplexer:

    def __init__(self, bus, devaddress):
        self.bus = smbus.SMBus(bus)
        self.devaddress = devaddress

    def __enter__(self):
        self.bus = smbus.SMBus(self.bus)
        return self.bus

    def __exit__(self, *args):
        raise Exception("Error with i2c")

    def channel(self, channel):
      
        # Turn on blue light
        # self.bus.write_byte_data(self.devaddress,  
        #                          0x06,
        #                          255  )


        #01 - orange
        #02 - white
                self.bus.write_byte_data(self.devaddress,  
                                 0x01,
                                 0  )


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
        self.shutdown_bit    = 8
        self.data_ready_bit  = 6
        self.tc74_i2c_bus    = smbus.SMBus(bus)

    def read_gain1(self):
        gain1M = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.ADC0MSB)
        gain1L = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.ADC0LSB)

        
        Gain = 0
        if gain1M != 0:
            gain1M = gain1M << self.shutdown_bit
            Gain = gain1M + gain1L

        return (Gain)
    
    def read_gain2(self):
        gain1M = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.ADC1MSB)
        gain1L = self.tc74_i2c_bus.read_byte_data(self.devaddr, self.ADC1LSB)

        
        Gain = 0
        if gain1M != 0:
            gain1M = gain1M << self.shutdown_bit
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


if __name__ == '__main__':
    import os
    import time
    # from settings import LASER_1_OUT_PIN, LASER_2_OUT_PIN
    # from settings import LASER_1, LASER_2

    #lid LED
    LID_SENSOR_MULTIPLEXER = 0x49

    #filter LED
    #LID_SENSOR_MULTIPLEXER = 0x59



    # bit of borrowed code
    import threading
    LASER_PROFILE_LOG = '/data/laser-profile.txt'

    mplx=Multiplexer(1, LID_SENSOR_MULTIPLEXER)
    x = mplx.channel(0)
    tc74_sensor = TC74(1, LID_SENSOR_MULTIPLEXER)  # temp sensor on bus 1 address 0x48
    gain = tc74_sensor.read_gain()  


    # laser1=Laser(LASER_1_OUT_PIN, LASER_1, 0)
    # laser2=Laser(LASER_2_OUT_PIN, LASER_2, 0)

    # mplx=Multiplexer(1, LASER_TEMP_MULTIPLEXER)    # Multiplexer on bus 1 address 0x70
    # mplx.channel(0)                                # Select laser0 temperature sensor
    # tc74_sensor = TC74(1, LASER_TEMP_SENSOR_ADDR)  # temp sensor on bus 1 address 0x48
    # temp = tc74_sensor.read_temp()     



    print(gain)

