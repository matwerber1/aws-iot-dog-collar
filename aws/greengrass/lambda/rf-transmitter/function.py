import greengrasssdk
import platform
from threading import Timer
import time
import RPi.GPIO as GPIO
from numpy import binary_repr
import sys
import logging

# initialize the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Creating a greengrass core sdk client
client = greengrasssdk.client('iot-data')

# Retrieving platform information to send from Greengrass Core
my_platform = platform.platform()

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
        return binary_repr(int(power), 8)
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

def get_raw_command(channel, mode, power):    

    byte_1 = get_byte_1(channel, mode)
    byte_2 = get_byte_2()
    byte_3 = get_byte_3()
    byte_4 = get_byte_4(power, mode)
    byte_5 = get_byte_5(channel, mode)

    message = byte_1 + byte_2 + byte_3 + byte_4 + byte_5

    return message 

def add_encoding(message):

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

    PREAMBLE             = '1111111100001'
    raw_command          = get_raw_command(channel, mode, power)    
    encoded_command      = PREAMBLE + add_encoding(raw_command)
    return encoded_command

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

def lambda_handler(event, context):

    logger.info(event)

    channel = event["channel"]
    mode    = event["mode"]
    power   = event["power"]
    
    TRANSMIT_PIN = 17
    
    encoded_command = get_encoded_command(channel, mode, power)
    msg = "\nTransmitting channel {}, mode {}, power {}:\n{}\n".format(channel, mode, power, encoded_command)
    client.publish(topic='dog_collar', payload=msg)
    transmit_code(TRANSMIT_PIN, encoded_command)
    client.publish(topic='dog_collar', payload='transmission complete.')

    return
