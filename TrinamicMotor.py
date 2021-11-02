'''
#
#  This work is protected under applicable local and international
#  copyright laws.  Copying, transmitting, using, or any other activity
#  is expressly forbidden without prior signed written approval from
#  the copyright owner.
#
#  Copyright(c) 2019, 2020 Autonomous Medical Device, Incorporated,
#  ALL RIGHTS RESERVED.
#
'''

from time import sleep
from settings import SI_COUNT
import inspect  # for line numbers
import logging
from settings import LOGGING_FILE

DEBUGGING = 1

logging.basicConfig(
        filename=LOGGING_FILE,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

# command code values, used to verify command completions
SAP = 5   # Set Axis Paramater
GAP = 6   # Get Axis Paramater
SGP = 9   # Set Global Paramater
GGP = 10  # Get Global Paramater
cmds = {  1: 'ROR',
          2: 'ROL',
          3: 'MST',
          4: 'MVP',
          5: 'SAP',
          6: 'GAP',
          7: 'STAP',
          8: 'RSAP',
          9: 'SGP',
         10: 'GGP',
         11: 'STGP',
         12: 'RSGP',
         13: '---',
         14: 'SIO',
         15: 'GIO',
         16: '---',
         17: '---',
         18: '---',
         19: 'CALC',
         20: 'COMP',
         21: 'JC',
         22: 'JA',
         23: 'CSUB',
         24: 'RSUB',
         25: '---',
         26: '---',
         27: 'WAIT',
         28: 'STOP',
         29: '---',
         30: '---',
         31: '---',
         32: '---',
         33: 'CALCX',
         34: 'AAP',
         35: 'AGP',
       }

paramater_info = { 'Short desc': ( 'Long description',
                                   'Value ranges') }

def lineno():  # returns string
    """Returns the current line number in our program."""
    return (__file__.split('/')[len(__file__.split('/'))-1]
            + ': '
            + str(inspect.currentframe().f_back.f_code.co_name)
            + '() +'
            + str(inspect.currentframe().f_back.f_lineno))

class TrinamicMotor:
    cmd_buffer = ""
    rcv_instruction = 0
    rcv_data = 0
    rcv_checksum_passed = False

    def __init__(self, ser, command_delay=0):
        self.ser = ser
        self.command_delay = command_delay

    def __cmd_buffer(self, cmd):
        self.cmd_buffer = self.cmd_buffer + cmd

    def send(self):
        if (self.ser is not None) and (self.ser.is_open == True):
            global paramater_info
            if DEBUGGING:
                # Awkward as sin... just to figure out whats going on
                def convert_twos_complement_to_decimal(bits):
                    return -int(bits[0]) << len(bits) | int(bits, 2)
                byte_str = repr(self.cmd_buffer)
                byte_str = byte_str[1:-1]
                hex_val = byte_str[8:16]
                value = convert_twos_complement_to_decimal(bin(int('1' + byte_str[8:16], 16))[3:])
                cmd = int(byte_str[3:5], 16)  # HEX string to decimal
                byte_str = '.'.join(byte_str[i:i+2] for i in range(0, len(byte_str), 2))
                byte_str = byte_str.replace(byte_str[3:5],cmds[int(byte_str[3:5])])
                msg = 'send = %s - %s - 0x%s (%d)' % (byte_str,
                                          next(iter(paramater_info.values()))[0],  # short description
                                          hex_val,   # 32 bit!
                                          value)
                logging.info(msg)

            # Try to send command message up a few times before giving up
            tries = 3
            ok = 0
            for tried in range(tries):
                try:
                    wrote = self.ser.write(bytes.fromhex(self.cmd_buffer))
                    if wrote > 0:
                        ok = 1
                        break  # everything was ok,.. bail out of the retry loop
                    else:
                        continue
                except SerialTimeoutException as e:
                    import pdb; pdb.set_trace()
                    msg = 'Serial line write exception: %d %s' % (e.error_code, e.message)
                    logging.info(msg)
                    if tried < tries:
                        sleep(0.5)  # just circle around and retry
                        continue
                    else:
                        break
                except SerialException as e:
                    msg = 'An unexpected exception occurred while writing to the serial: %d %s' \
                          % (e.error_code, e.message)
                    logging.info(msg)
                    if tried < tries:
                        sleep(0.5)  # just circle around and retry
                        continue
                    else:
                        break
                break

            # reset the command buffer
            self.cmd_buffer = ''

            # clear the paramater info dictionary just in case we add a command
            # and forget to fill in the descriptions
            paramater_info = { 'Short desc': ( 'Long description',
                                               'Value ranges') }
            sleep(self.command_delay)
            # ~ sleep(0.05)

            if ok == 1:
                return wrote  # might as well return how many bytes we wrote
            else:
                msg = 'DISASTER. unable to send command after %d tries. UNSENT' % tries
                print(msg)
                return -2  # Negative number to indicate a retry timeout error
        else:
            print('Serial line is dead. Unable to send.')
            return -1  # Negative number to indicate a generic catastrophic error

    def receive(self):
        rtn_codes = { 100: 'Successfully executed, no error (100)',
                      101: 'Command loaded into TMCL program EEPROM (101)',
                        1: 'Wrong checksum (1)',
                        2: 'Invalid command (2)',
                        3: 'Wrong type (3)',
                        4: 'Invalid value (4)',
                        5: 'Configuration EEPROM locked (5)',
                        6: 'Command not available (6)'
                    }
        ok = 0
        while not ok:  # har har,.. trickery...
            if (self.ser is not None) and (self.ser.is_open == True):
                res = self.ser.read(9)
                sleep(self.command_delay)
                # ~ print("rcv  = ", res.hex()) ####

                rcv_status = res[2]                    # 100
                self.rcv_instruction = res[3]          # 3
                #self.rcv_data = bytearray(res[4:6])    # res[4:7] = b'\xff\xff\xf1'
                self.rcv_data = int.from_bytes(res[4:8], byteorder='big', signed=True)
                rcv_checksum = res[8]

                checksum = sum(bytearray(res[0:8]))
                checksum1 = checksum & 0xFF
                self.rcv_checksum_passed = False         # Fail

                if checksum1 == rcv_checksum:
                    if rcv_status == 0x64:               # 100 - command completed ok
                        self.rcv_checksum_passed = True  # Success
                        ok = 1
                        break  # break out of the while loop
                    else:
                        msg = 'receive (status error) = ', rtn_codes[rcv_status]
                        logging.info(msg)
                        # lets deal with errors (1-6),.. umm I think we can only handle 1 and 4 sanely
                        if str(rcv_status) in '1,4': # we can retry these
                            if DEBUGGING:
                                byte_str = repr(self.cmd_buffer)
                                byte_str = byte_str[1:-1]
                                cmd = int(byte_str[3:5], 16)  # HEX string to decimal
                                byte_str = '.'.join(byte_str[i:i+2] for i in range(0, len(byte_str), 2))
                                byte_str = byte_str.replace(byte_str[3:5],cmds[int(byte_str[3:5])])
                                msg = 'RETRYING = [%s]' % byte_str
                                logging.info(msg)
                            self.send()  # retry
                            continue
                else:
                    msg = 'checksum error'
                    logging.info(msg)
                    print(msg)
            else:
                 msg = 'Serial line is dead. Unable to recieve'
                 logging.info(msg)
                 print(msg)
                 break  # give up, we're going to get nowhere if the line is dead

    def get_status_info(self):
        header_get_status_info = '01069c00'  # GAP 156 return errors and flags
        global paramater_info
        paramater_info = { 'Get status flags': ( 'Get status flags',
                                                 'see manual for bitfield meanings' ) }
        self.format_command(header_get_status_info, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    def get_target_speed(self):
        header_get_target_speed = '01060200'  # GAP 2 return TARGET speed
        global paramater_info
        paramater_info = { 'Target speed': ('Set/get the desired target velocity.',
                                            '-200000...  +200000 [rpm]') }
        self.format_command(header_get_target_speed, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    def get_actual_speed(self):
        header_get_actual_speed = '01060300'  # GAP 3 return ACTUAL speed
        global paramater_info
        paramater_info = { 'Actual speed': ('The actual velocity of the motor',
                                            '-2147483648... +2147483647 [rpm]' ) }
        self.format_command(header_get_actual_speed, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    def rotate_right(self, velo):
        header_ROR = '01010000'
        global paramater_info
        paramater_info = { 'Rotate right': ('Rotate Right',
                                   '-2147483648... +2147483647 [rpm]') }
        self.format_command(header_ROR, velo)
        self.send()
        self.receive()
        return self

    def rotate_left(self, velo):
        header_ROL = '01020000'
        global paramater_info
        paramater_info = { 'Rotate left': ('Rotate Left',
                                   '-2147483648... +2147483647 [rpm]') }
        self.format_command(header_ROL, velo)
        self.send()
        self.receive()
        return self

    def stop(self):  # NOTE: sets target velocity to 0
        header_MST = '01030000'
        global paramater_info
        paramater_info = { 'MST': ('Motor stop',
                                   '' ) }
        self.format_command(header_MST, 0)
        self.send()
        self.receive()
        return self

    def position_abs(self, ticks):  # ticks
        header_MVP_ABS = '01040000'
        global paramater_info
        paramater_info = { 'Move to position': ('ABS – absolute',
                                                'position -2147483648... +2147483647') }
        self.format_command(header_MVP_ABS, -ticks)
        self.send()
        self.receive()
        return self

    def position_rel(self, ticks):  # ticks
        header_MVP_REL = '01040100'
        global paramater_info
        paramater_info = { 'Move to position': ('REL - Relative',
                                                'position -2147483648... +2147483647') }
        self.format_command(header_MVP_REL, -ticks)
        self.send()
        self.receive()
        return self

    # ------------------------------------------------------------------
    def set_velocity_ramp_generator(self, value):  # 0:off 1:on
        header_set_velocity_ramp_generator = '01059200' # SAP 146
        global paramater_info
        paramater_info = { 'Activate ramp': ('Activate velocity ramp generator for position and velocity mode',
                                             '0/1') }
        self.format_command(header_set_velocity_ramp_generator, value)
        self.send()
        self.receive()
        return self

    def get_velocity_ramp_generator(self):
        header_get_velocity_ramp_generator = '01069200'  # GAP 146
        global paramater_info
        paramater_info = { 'Activate ramp': ('Activate velocity ramp generator for position and velocity mode',
                                             '0/1') }
        self.format_command(header_get_velocity_ramp_generator, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def set_max_abs_ramp_velocity(self, velo_max):
        header_set_max_abs_ramp_velocity = '01050400'  # SAP 4
        global paramater_info
        paramater_info = { 'Max. absolute ramp velocity': ('The maximum velocity used for velocity ramp in velocity mode and positioning mode',
                                                           '0 +200000  [rpm] ') }
        self.format_command(header_set_max_abs_ramp_velocity, velo_max)
        self.send()
        self.receive()
        return self

    def get_max_abs_ramp_velocity(self):
        header_get_max_abs_ramp_velocity = '01060400'  # GAP 4
        global paramater_info
        paramater_info = { 'Max. absolute ramp velocity': ('The maximum velocity used for velocity ramp in velocity mode and positioning mode',
                                                           '0 +200000  [rpm] ') }
        self.format_command(header_get_max_abs_ramp_velocity, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def set_mvp_target_reached_velocity(self, velo_max):
        header_set_mvp_target_reached_velo = '01050700'  # SAP 7
        global paramater_info
        paramater_info = { 'MVP Target reached velocity': ('Maximum velocity at which end position flag can be set',
                                                           '0 +200000 [rpm]') }
        self.format_command(header_set_mvp_target_reached_velo, velo_max)
        self.send()
        self.receive()
        return self

    def get_mvp_target_reached_velocity(self):
        header_get_mvp_target_reached_velocity = '01060700'  # GAP 7
        global paramater_info
        paramater_info = { 'MVP Target reached velocity': ('Maximum velocity at which end position flag can be set',
                                                           '0 +200000 [rpm]') }
        self.format_command(header_get_mvp_target_reached_velocity, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def set_mvp_target_reached_distance(self, distance):
        header_set_mvp_target_reached_distance = '01050A00'  # SAP 10
        global paramater_info
        paramater_info = { 'MVP target reached distance': ('Maximum distance at which the position end flag is set.',
                                                           '0... +100000') }
        self.format_command(header_set_mvp_target_reached_distance, distance)
        self.send()
        self.receive()
        return self

    def get_mvp_target_reached_distance(self):
        header_get_mvp_target_reached_distance = '01060A00'  # GAP 10
        global paramater_info
        paramater_info = { 'MVP target reached distance': ('Maximum distance at which the position end flag is set.',
                                                           '0... +100000') }
        self.format_command(header_get_mvp_target_reached_distance, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def set_acceleration(self, accel):
        header_set_accel = '01050B00'  # SAP 11
        global paramater_info
        paramater_info = { 'Acceleration': ('Acceleration parameter for ROL, ROR and the velocity ramp of MVP',
                                            '0... +100000  [RPM/s]') }
        self.format_command(header_set_accel, accel)
        self.send()
        self.receive()
        return self

    def get_acceleration(self):
        header_get_acceleration = '01060B00'  # GAP 11
        global paramater_info
        paramater_info = { 'Acceleration': ('Acceleration parameter for ROL, ROR and the velocity ramp of MVP',
                                            '0... +100000  [RPM/s]') }
        self.format_command(header_get_acceleration, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def get_ramp_generator_speed(self):
        header_get_ramp_generator_speed = '01060D00'  # GAP 13 (no SAP pairing)
        global paramater_info
        paramater_info = { 'Ramp generator speed': ('The actual speed of the velocity ramp used for positioning and velocity mode.',
                                                    '-2147483648... +2147483647 [rpm]') }
        self.format_command(header_get_ramp_generator_speed, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def get_velocity_pid_error_sum(self):
        header_get_velocity_pid_error_sum = '0106E500'  # GAP 229 (no SAP pairing)
        global paramater_info
        paramater_info = { 'Velocity PID error sum': ('Sum of errors of velocity PID regulator',
                                                      '-2147483648... +2147483647') }
        self.format_command(header_get_velocity_pid_error_sum, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def set_position_p(self, pos_P):
        header_set_position_P = '0105E600'  # SAP 230
        global paramater_info
        paramater_info = { 'P parameter for position PID': ('P parameter of position PID regulator.',
                                                            '0... 65535') }
        self.format_command(header_set_position_P, pos_P)
        self.send()
        self.receive()
        return self

    def get_position_p(self):
        header_get_position_P = '0106E600'  # GAP 230
        global paramater_info
        paramater_info = { 'P parameter for position PID': ('P parameter of position PID regulator.',
                                                            '0... 65535') }
        self.format_command(header_get_position_P, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def set_velocity(self, velo):
        header_set_velocity = '01050200'  # SAP 2
        global paramater_info
        paramater_info = { 'Target speed': ('Set/get the desired target velocity.',
                                            '-200000...  +200000 [rpm]') }
        self.format_command(header_set_velocity, velo)
        self.send()
        self.receive()
        return self

    def get_velocity(self):
        header_get_velocity = '01060200'  # GAP 2
        global paramater_info
        paramater_info = { 'Target speed': ('Set/get the desired target velocity.',
                                            '-200000...  +200000 [rpm]') }
        self.format_command(header_get_velocity, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def set_velocity_p(self, velo_P):
        header_set_velocity_P = '0105EA00'  # SAP 234
        global paramater_info
        paramater_info = { 'P parameter for velocity PID': ('P parameter of velocity PID regulator.',
                                                            '0... 65535') }
        self.format_command(header_set_velocity_P, velo_P)
        self.send()
        self.receive()
        return self

    def get_velocity_p(self):
        header_get_velocity_P = '0106EA00'  # GAP 234
        global paramater_info
        paramater_info = { 'P parameter for velocity PID': ('P parameter of velocity PID regulator.',
                                                            '0... 65535') }
        self.format_command(header_get_velocity_P, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def set_velocity_i(self, velo_I):
        header_set_velocity_I = '0105EB00'  # SAP 235
        global paramater_info
        paramater_info = { 'Set I parameter for velocity PID': ('I parameter of velocity PID regulator.',
                                                                '0... 65535') }
        self.format_command(header_set_velocity_I, velo_I)
        self.send()
        self.receive()
        return self

    def get_velocity_i(self):  # I parameter
        header_get_velocity_I = '0106EB00'  # GAP 235
        global paramater_info
        paramater_info = { 'Get I parameter for velocity PID': ('I parameter of velocity PID regulator.',
                                                                '0... 65535') }
        self.format_command(header_get_velocity_I, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def set_torque_p(self, torque_P):
        header_set_torque_P = '0105AC00'  # SAP 172
        global paramater_info
        paramater_info = { 'Set P parameter for current PID': ('P parameter of current PID regulator.',
                                                               '0... 65535') }
        self.format_command(header_set_torque_P, torque_P)
        self.send()
        self.receive()
        return self

    def get_torque_p(self):  # P parameter
        header_get_torque_P = '0106AC00'  # GAP 172
        global paramater_info
        paramater_info = { 'Get P parameter for current PID': ('P parameter of current PID regulator.',
                                                               '0... 65535') }
        self.format_command(header_get_torque_P, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def set_torque_i(self, torque_I):
        header_set_torque_I = '0105AD00'  # SAP 173
        global paramater_info
        paramater_info = { 'Set I parameter for current PID': ('I parameter of current PID regulator.',
                                                               '0... 65535') }
        self.format_command(header_set_torque_I, torque_I)
        self.send()
        self.receive()
        return self

    def get_torque_i(self):
        header_get_torque_I = '0106AD00'  # GAP 173
        global paramater_info
        paramater_info = { 'Get I parameter for current PID': ('I parameter of current PID regulator.',
                                                               '0... 65535') }
        self.format_command(header_get_torque_I, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def set_encoder_set_null(self, zeorOrOne):
        header_set_encoder_set_null = '0105A100'  # SAP 161
        global paramater_info
        paramater_info = { 'Encoder set NULL': ('set position counter to zero at next N channel event.',
                                                '0/1') }
        self.format_command(header_set_encoder_set_null, zeorOrOne)
        self.send()
        self.receive()
        return self

    def get_encoder_set_null(self):
        header_get_encoder_set_null = '0106A100'  # GAP 161
        global paramater_info
        paramater_info = { 'Encoder set NULL': ('get \'position set counter NULL\' state.',
                                                '0/1') }
        self.format_command(header_get_encoder_set_null, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def set_encoder_clear_set_null(self, zeorOrOne):
        header_set_encoder_clear_set_null = '0105A300'  # SAP 163
        global paramater_info
        paramater_info = { 'Encoder clear set NULL': ('set \'Encoder clear set NULL\' state (0. Always 1. zero only the once',
                                                      '0/1') }
        self.format_command(header_set_encoder_clear_set_null, zeorOrOne)
        self.send()
        self.receive()
        return self

    def get_encoder_clear_set_null(self):
        header_get_encoder_clear_set_null = '0106A300'  # GAP 163
        global paramater_info
        paramater_info = { 'Encoder clear set NULL': ('get \'Encoder clear set NULL\' state (0. Always 1. zero only the once',
                                                      '0/1') }
        self.format_command(header_get_encoder_clear_set_null, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def set_communication_mode(self):
        header_set_commun_mode = '01059F00'  # SAP 159
        global paramater_info
        paramater_info = { 'Commutation mode': ('0: Block based on hall sensor 6: FOC based on hall sensor 7: FOC based on encoder 8: FOC controlled (velocity mode only)',
                                                '0, 6, 7, 8') }
        self.format_command(header_set_commun_mode, 7)  # FOC based on encoder
        self.send()
        self.receive()
        return self

    # ------------------------------------------------------------------
    def set_max_current(self, max_current):
        header_max_current = '01050600'  # SAP 6
        global paramater_info
        paramater_info = { 'Max current': ('Set the max allowed motor current.',
                                           '0... +20000 [mA]' ) }
        self.format_command(header_max_current, max_current)  # max 1000mA peak
        self.send()
        self.receive()
        return self

    def get_max_current(self):
        header_get_max_current = '01060600'  # GAP 6
        global paramater_info
        paramater_info = { 'Max current': ('Get the max allowed motor current.',
                                           '0... +20000 [mA]' ) }
        self.format_command(header_get_max_current, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def set_number_of_motor_poles(self, number_of_poles):
        header_number_of_motor_poles = '0105FD00'  # SAP 253
        global paramater_info
        paramater_info = { 'Number of motor poles.': ('Number of motor poles.',
                                                      '2... +254' ) }
        self.format_command(header_number_of_motor_poles, number_of_poles)
        self.send()
        self.receive()
        return self

    def set_hall_sensor_invert(self):
        header_clear_hall_sensor_invert = '0105FE00'  # SAP 254
        global paramater_info
        paramater_info = { 'Hall sensor invert': ('1: Hall sensor invert. Invert the hall scheme',
                                                  '0/1') }
        self.format_command(header_clear_hall_sensor_invert, 0)
        self.send()
        self.receive()
        return self

    def set_encoder_direction(self, direction=1):
        header_set_encoder_direction = '0105FB00'  # SAP 251
        global paramater_info
        paramater_info = { 'Encoder  direction': ( 'Set the encoder direction in a way, that ROR increases position counter',
                                                   '0/1') }
        self.format_command(header_set_encoder_direction, direction)  # 1 = go right
        self.send()
        self.receive()
        return self

    def set_encoder_steps(self, encoder_steps):
        header_set_encoder_steps = '0105FA00'  # SAP 250
        global paramater_info
        paramater_info = { 'Encoder steps': ( 'Encoder steps per rotation',
                                              '0... +65535' ) }
        self.format_command(header_set_encoder_steps, encoder_steps)
        self.send()
        self.receive()
        return self

    def set_encoder_init_mode(self):
        header_set_encoder_init_mode = '0105F900'  # SAP 249
        global paramater_info
        paramater_info = { 'Init sine mode ': ( '0: Initialization in controlled sine commutation (determines the encoder offset) ' + \
                                                '1: Initialization in block commutation using hall sensors ' + \
                                                '2: Initialization in controlled sine commutation (use the previous set encoder offset)',
                                                '0, 1, 2' ) }
        self.format_command(header_set_encoder_init_mode, 1)  # Use hall sensor
        self.send()
        self.receive()
        return self

    def set_target_current_to_zero(self):
        header_set_target_current = '01059B00'  # SAP 155
        global paramater_info
        paramater_info = { 'Target current': ( 'Set/get desired target current to activate current regulation mode.',
                                               '-20000... +20000 [mA]`' ) }
        self.format_command(header_set_target_current, 0)
        self.send()
        self.receive()
        return self

    def wait_for_event(self, condition, timeout=0):  # NOT FOR DIRECT MODE!!
        if condition == 1:
            # Wait for target position reached
            header_wait_for_event = '011B0100'
        elif condition == 2:
            # Wait for reference switch
            header_wait_for_event = '011B0200'
        elif condition == 3:
            # Wait for limit switch
            header_wait_for_event = '011B0300'
        self.format_command(header_wait_for_event, timeout)
        self.send()
        self.receive()
        return self

    # ------------------------------------------------------------------
    def set_target_position(self, ticks):  # SAP 0 (in TICKS)
        header_set_target_position = '01050000'
        global paramater_info
        paramater_info = { 'Target position': ( 'Set the target position of a currently executed ramp.',
                                                '-2147483648... +2147483647' ) }
        self.format_command(header_set_target_position, ticks)
        self.send()
        self.receive()
        return self

    def get_target_position(self):  # GAP 0 (in TICKS)
        header_get_target_position = '01060000'
        global paramater_info
        paramater_info = { 'Target position': ( 'Get the target position of currently executed ramp.',
                                                '-2147483648... +2147483647' ) }
        self.format_command(header_get_target_position, 0)
        self.send()
        self.receive()  # 9 bytes
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                position = -self.rcv_data % SI_COUNT
                return position

    # ------------------------------------------------------------------
    def get_actual_encoder_angle(self):  # GAP 1 (in degrees)
        header_get_actual_encoder_angle = '01060100'
        global paramater_info
        paramater_info = { 'Actual position': ( 'get the position counter without moving the motor',
                                                '-2147483648... +2147483647' ) }
        self.format_command(header_get_actual_encoder_angle, 0)
        self.send()
        self.receive()  # 9 bytes
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == 6:
                #angle = -(360*self.rcv_data/SI_COUNT)%360
                angle = -360 * self.rcv_data / SI_COUNT
                #print("DBG: ANG=%f" % angle)
                return angle

    def get_actual_encoder_angle_modulo(self):  # GAP 1 (in degrees)
        header_get_actual_encoder_angle = '01060100'
        global paramater_info
        paramater_info = { 'Actual position': ( 'get the position counter in deg without moving the motor',
                                                '-360... +360' ) }
        self.format_command(header_get_actual_encoder_angle, 0)
        self.send()
        self.receive()  # 9 bytes
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                angle = -(360*self.rcv_data/SI_COUNT)%360
                return angle

    def get_actual_encoder_count(self):  # GAP 1 (in TICKS)
        header_get_actual_encoder_angle = '01060100'
        global paramater_info
        paramater_info = { 'Actual position': ( 'Get the position counter in ticks without moving the motor',
                                                'Modulo %d' % SI_COUNT ) }
        self.format_command(header_get_actual_encoder_angle, 0)
        self.send()
        self.receive()  # 9 bytes
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                #position = -self.rcv_data % SI_COUNT
                return -self.rcv_data

    # ------------------------------------------------------------------
    def set_actual_encoder_count(self, ticks):  # SAP 1
        header_set_actual_encoder_count = '01050100'
        global paramater_info
        paramater_info = { 'Actual position': ( 'Set the position counter in ticks without moving the motor',
                                                '-2147483648... +2147483647' ) }
        self.format_command(header_set_actual_encoder_count, ticks)
        self.send()
        self.receive()
        return self

    def get_actual_encoder_count_modulo(self):  # GAP 1 (in TICKS)
        header_get_actual_encoder_angle = '01060100'
        global paramater_info
        paramater_info = { 'Actual position': ( 'Get the position counter in ticks without moving the motor',
                                                'Modulo %d' % SI_COUNT ) }
        self.format_command(header_get_actual_encoder_angle, 0)
        self.send()
        self.receive()  # 9 bytes
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                position = -self.rcv_data % SI_COUNT
                return position

    # ------------------------------------------------------------------
    def get_actual_current(self):
        header_get_actual_current = '01069600'  # GAP 150 (no SAP pairing)
        global paramater_info
        paramater_info = { 'Actual motor current': ( 'Get actual motor current.',
                                                     '-2147483648... +2147483647 [mA]' ) }
        self.format_command(header_get_actual_current, 0)
        bad = 1
        while bad == 1:
            self.send()
            self.receive()
            if self.rcv_checksum_passed == True:
                if self.rcv_instruction == GAP:
                    result = self.rcv_data
                    if result is None:
                       bad = 1
                       print("Bad data? <None>")
                       import pdb; pdb.set_trace()
                    else:
                       bad = 0
                       break
        return result

    # ------------------------------------------------------------------
    def set_target_current(self, current):
        header_set_target_current = '01059B00'  # SAP 155
        global paramater_info
        paramater_info = { 'Target current': ( 'Set desired target current to activate current regulation mode.',
                                               '-20000... +20000 [mA]`' ) }
        self.format_command(header_set_target_current, current)
        self.send()
        self.receive()
        return self

    def get_target_current(self):
        header_get_target_current = '01069B00'  # GAP 155
        global paramater_info
        paramater_info = { 'Target current': ( 'Get desired target current to activate current regulation mode.',
                                               '-20000... +20000 [mA]`' ) }
        self.format_command(header_get_target_current, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def get_encoder_set_null(self):
        header_get_encoder_set_null = '0106A100'  # GAP 161
        global paramater_info
        paramater_info = { 'Encoder set NULL': ( 'Get \'Encoder set NULL\' state',
                                                 '0/1') }
        self.format_command(header_get_encoder_set_null, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result
        #else:

    def BLDC_reinitialization(self):
        header_BLDC_reinitialization = '01051F00'  # SAP 31 (write only)
        # restart the timer and initialize encoder.
        global paramater_info
        paramater_info = { 'BLDC  re-initialization': ( 'Restart the timer and initialize encoder',
                                                        '(ignored)' ) }
        self.format_command(header_BLDC_reinitialization,0)
        self.send()
        self.receive()
        return self

    # ------------------------------------------------------------------
    def set_telegram_pause_time(self, pause, bank=0):
        '''
        There are three banks, 0,1 are for globals and 2 is for user params
        typically only 0 and 2 are used
        '''
        header_set_telegram_pause_time= '01094b' + "{:0>2}".format(bank) # SGP(9) 75
        global paramater_info
        paramater_info = { 'Telegram pause time': ( 'Set the telegram pause time before the reply via RS485 is sent.',
                                                    '0... 255' ) }
        self.format_command(header_set_telegram_pause_time, pause)
        self.send()
        self.receive()
        return self

    def get_telegram_pause_time(self, bank=0):
        header_get_telegram_pause_time = '010a4b' + "{:0>2}".format(bank) # GGP(10) 75
        global paramater_info
        paramater_info = { 'Telegram pause time': ( 'Get the telegram pause time before the reply via RS485 is sent.',
                                                    '0... 255' ) }
        self.format_command(header_get_telegram_pause_time, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GGP:  # remember this is the command used (10)
                result = self.rcv_data
                return result  # (eeprom default seems to be 0 )

    # ------------------------------------------------------------------
    def set_sine_initialization_speed(self, rpm):
        header_set_sine_initialization_speed = '0105F100'  # SAP 241
        global paramater_info
        paramater_info = { 'Sine initialization speed ': ( 'Velocity during initialization in init sine mode 2',
                                                           '-200000...  +200000 [rpm]' ) }
        self.format_command(header_set_sine_initialization_speed, rpm)
        self.send()
        self.receive()
        return self

    def get_sine_initialization_speed(self):
        header_get_sine_initialization_speed = '0106F100'  # GAP 241
        global paramater_info
        paramater_info = { 'Sine initialization speed ': ( 'Velocity during initialization in init sine mode 2',
                                                           '-200000...  +200000 [rpm]' ) }
        self.format_command(header_get_sine_initialization_speed, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result  # (eeprom default is +200)

    # ------------------------------------------------------------------
    def get_current_pid_error_sum(self):
        header_get_current_pid_error_sum = '0106C900'  # GAP 201
        global paramater_info
        paramater_info = { 'Current PID error sum': ( 'Sum of errors of current PID regulator ',
                                                      '-2147483648... +2147483647' ) }
        self.format_command(header_get_current_pid_error_sum, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result
    # ------------------------------------------------------------------
    def set_encoder_commutation_offset(self, rpm):
        header_set_encoder_commutation_offset = '0105a500'  # SAP 165
        global paramater_info
        paramater_info = { 'Actual encoder commutation offset': ( 'Set the internal commutation offset.',
                                                                  '0... 65535' ) }
        self.format_command(header_set_encoder_commutation_offset, rpm)
        self.send()
        self.receive()
        return self

    def get_encoder_commutation_offset(self):
        header_get_encoder_commutation_offset = '0106a500'  # GAP 165
        global paramater_info
        paramater_info = { 'Actual encoder commutation offset': ( 'Get the internal commutation offset.',
                                                                  '0... 65535' ) }
        self.format_command(header_get_encoder_commutation_offset, 0)
        self.send()
        self.receive()
        if self.rcv_checksum_passed == True:
            if self.rcv_instruction == GAP:
                result = self.rcv_data
                return result

    # ------------------------------------------------------------------
    def format_command(self, header, data):
        if data < 0:
            dataHex = hex((1 << 32) + data)[2:]
        else:
            dataHex = hex(data)[2:]

        dataLen = len(dataHex)
        if dataLen == 1:
            dataBytes = '0000000' + dataHex
        elif dataLen == 2:
            dataBytes = '000000' + dataHex
        elif dataLen == 3:
            dataBytes = '00000' + dataHex
        elif dataLen == 4:
            dataBytes = '0000' + dataHex
        elif dataLen == 5:
            dataBytes = '000' + dataHex
        elif dataLen == 6:
            dataBytes = '00' + dataHex
        elif dataLen == 7:
            dataBytes = '0' + dataHex
        elif dataLen == 8:
            dataBytes = dataHex

        headerAndData = header + dataBytes
        headerAndDataHex = bytes.fromhex(headerAndData)
        checksum = sum(bytearray(headerAndDataHex))
        checksumHex = format(checksum, 'x')

        if len(checksumHex) == 1:
            checksumFinal = '0' + checksumHex
        elif len(checksumHex) > 2:
            checksumFinal = checksumHex[-2:]
        else:
            checksumFinal = checksumHex

        cmd = headerAndData + checksumFinal

        self.__cmd_buffer(cmd)
        return self
