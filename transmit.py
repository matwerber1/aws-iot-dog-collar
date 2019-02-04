import time
import sys
import RPi.GPIO as GPIO
from numpy import binary_repr
import sys
import argparse

def get_byte_1(channel, mode):
    mode_codes = {
        'beep':    '0100',
        'light':   '1000',
        'shock':   '0001',
        'vibrate': '0010'
    }
    channel_codes = {
        '1': '1000',
        '2': '1111'
    }
    byte1 =  channel_codes[channel] + mode_codes[mode]
    return byte1

def get_byte_2():
    return '10000000'

def get_byte_3():
    return '11100110'

def get_byte_4(power, mode):
    if mode in ['shock', 'vibrate']:
        return binary_repr(power, 8)
    else:
        # byte4 is power and is not applicable unless mode is shock or vibrate
        return '00000000'

def get_byte_5(channel, mode):
    mode_codes = {
        'beep':    '1101',
        'light':   '1110',
        'shock':   '0111',
        'vibrate': '1011'
    }
    channel_codes = {
        '1': '1110',
        '2': '0000'
    }
    byte5 = mode_codes[mode] + channel_codes[channel]
    return byte5

def get_command_message(channel, mode, power):    

    byte_1 = get_byte_1(channel, mode)
    byte_2 = get_byte_2()
    byte_3 = get_byte_3()
    byte_4 = get_byte_4(power, mode)
    byte_5 = get_byte_5(channel, mode)

    #message = "{} {} {} {} {}".format(byte_1, byte_2, byte_3, byte_4, byte_5)
    message = byte_1 + byte_2 + byte_3 + byte_4 + byte_5

    return message 

def get_encoded_message(message):

    CARRIER_SIGNAL = '01'
    encoded_message = ''
    for x in message:
        if x == '0':
            encoded_message += '000'
        elif x == '1':
            encoded_message += '111'
        else:
            print('unexpected character {} in message!'.format(x))
            exit()
        encoded_message += CARRIER_SIGNAL
    return encoded_message

def get_encoded_command(channel, mode, power): 
    # all messages start with this preamble
    PREAMBLE = '1111111100001'
    raw_command = get_command_message(channel, mode, power)    
    encoded_command = get_encoded_message(raw_command)
    full_encoded_message = PREAMBLE + encoded_command
    return full_encoded_message

def transmit_code(pin, code):
    
    # time between 1s and 0s in a single message...
    # 200 microseconds based on analysis of signal from remote in URH
    short_delay = 0.000200

    # time between repeating the same message...
    # 13 milliseconds based analysis of signal from remote in URH
    extended_delay = 0.013

    NUM_ATTEMPTS = 3
    TRANSMIT_PIN = pin

    '''Transmit a chosen code string using the GPIO transmitter'''
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRANSMIT_PIN, GPIO.OUT)
    for t in range(NUM_ATTEMPTS):
        for i in code:
            if i == '1':
                GPIO.output(TRANSMIT_PIN, 1)
            elif i == '0':
                GPIO.output(TRANSMIT_PIN, 0)
            else:
                continue
            time.sleep(short_delay)

        GPIO.output(TRANSMIT_PIN, 0)
        time.sleep(extended_delay)
    GPIO.cleanup()

def main():
    
    parser = argparse.ArgumentParser(description='Test DynamoDB query API speed.')
    parser.add_argument('--channel', type=str, required=True, help='channel to transmit [0,1]')
    parser.add_argument('--mode',    type=str, required=True, help='collar mode [beep,shock,vibrate,light]')
    parser.add_argument('--power',   type=int, default=20,    help='power [0 to 100] (only for shock or vibrate mode)')
    parser.add_argument('--pin',     type=int, default=17,    help='GPIO pin to transmit code on Raspberri Pi')
    args = parser.parse_args()
    
    channel      = args.channel
    mode         = args.mode
    power        = args.power
    transmit_pin = args.pin
    
    encoded_command = get_encoded_command(channel, mode, power)
    print("\nMessage for channel {}, mode {}, power {}:\n{}\n".format(channel, mode, power, encoded_command))
    
    transmit_code(transmit_pin, encoded_command)
    
if __name__ == "__main__":
   main()