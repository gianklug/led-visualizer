#!/usr/bin/python3
import os
import struct
import subprocess
import tempfile

import sys
import termios
import tty
import pigpio
import time

import colorama
from colorama import Fore, Style

bright = 255


# The Pins. Use Broadcom numbers.
B_RED_PIN   = 17
B_GREEN_PIN = 22
B_BLUE_PIN  = 24

M_RED_PIN   = 18
M_GREEN_PIN = 4
M_BLUE_PIN  = 23

H_RED_PIN   = 27
H_GREEN_PIN = 5
H_BLUE_PIN  = 26

BARS_NUMBER = 4
OUTPUT_BIT_FORMAT = "8bit"
#OUTPUT_BIT_FORMAT = "16bit"
# RAW_TARGET = "/tmp/cava.fifo"
RAW_TARGET = "/dev/stdout"

conpat = """
[general]
bars = %d
[output]
method = raw
raw_target = %s
bit_format = %s
channels = mono
[smoothing]
noise_reduction = 15
[eq]
1 = 1
2 = 1.1
3 = 0.9
4 = 0.9
"""

pi = pigpio.pi()


config = conpat % (BARS_NUMBER, RAW_TARGET, OUTPUT_BIT_FORMAT)
bytetype, bytesize, bytenorm = ("H", 2, 65535) if OUTPUT_BIT_FORMAT == "16bit" else ("B", 1, 255)

def setLights(pin, brightness):
    realBrightness = int(int(brightness) * (float(bright) / 255.0))
    pi.set_PWM_dutycycle(pin, realBrightness)

def output(space, band):
    if band == "    High":
        if space < 10:
            print(Fore.GREEN + band +":   " + str(space))
        elif space < 100:
            print(Fore.GREEN + band +":  " + str(space))
        else:
            print(Fore.GREEN + band +": " + str(space))
    else:
        if space < 10:
            print(Fore.GREEN + band +":   " + str(space), end = '')
        elif space < 100:
            print(Fore.GREEN + band +":  " + str(space), end = '')
        else:
            print(Fore.GREEN + band +": " + str(space), end = '')

def run():
    with tempfile.NamedTemporaryFile() as config_file:
        config_file.write(config.encode())
        config_file.flush()

        process = subprocess.Popen(["cava", "-p", config_file.name], stdout=subprocess.PIPE)
        chunk = bytesize * BARS_NUMBER
        fmt = bytetype * BARS_NUMBER

        if RAW_TARGET != "/dev/stdout":
            if not os.path.exists(RAW_TARGET):
                os.mkfifo(RAW_TARGET)
            source = open(RAW_TARGET, "rb")
        else:
            source = process.stdout

        while True:
            data = source.read(chunk)
            if len(data) < chunk:
                break
            sample = struct.unpack(fmt, data)

            # BASS
            sampleBass = sample[0]+sample[1]/2
            if sampleBass < 90:
                setLights(B_RED_PIN, 0)
                setLights(B_GREEN_PIN, sampleBass)
                output(sampleBass, "Bass")
            elif sampleBass >= 90 and sampleBass < 140:
                gruenPegel = (sampleBass/140)*255
                setLights(B_RED_PIN, 0)
                setLights(B_GREEN_PIN, gruenPegel)
                output(sampleBass, "Bass")
            elif sampleBass >= 140 and sampleBass < 210:
                # 210-140 = 70
                # ((relatives level) / max relatives level)*255
                rotPegel = ((sampleBass - 140) / 70) * 255
                setLights(B_RED_PIN, rotPegel)
                setLights(B_GREEN_PIN, 255)
                print(Fore.YELLOW + "Bass: " + str(sampleBass), end = '')
            elif sampleBass >= 210:
                # 140 = 0 rot; 255 = 255 rot
                # 140 = 255 grün; 255 = 0 grün
                
                # 255-140 = 115
                # ((relatives level) / max relatives level)*255
                rotPegel = ((sampleBass - 140) / 115) * 255
                gruenPegel = 255-rotPegel
                
                if gruenPegel < 5:
                    gruenPegel = 0
                
                setLights(B_RED_PIN, 255)
                setLights(B_GREEN_PIN, gruenPegel)
                print(Fore.RED + "Bass: " + str(sampleBass), end = '')

            # MIDDLE
            if sample[2] < 90:
                setLights(M_RED_PIN, 0)
                setLights(M_GREEN_PIN, sample[2])
                output(sample[2], "    Midd")
            elif sample[2] >= 90 and sample[2] < 140:
                gruenPegel = (sample[2]/140)*255
                setLights(M_RED_PIN, 0)
                setLights(M_GREEN_PIN, gruenPegel)
                output(sample[2], "    Midd")
            elif sample[2] >= 140 and sample[2] < 210:
                # 210-140 = 70
                # ((relatives level) / max relatives level)*255
                rotPegel = ((sample[2] - 140) / 70) * 255
                setLights(M_RED_PIN, rotPegel)
                setLights(M_GREEN_PIN, 255)
                print(Fore.YELLOW + "    Midd: " + str(sample[2]), end = '')
            elif sample[2] >= 210:
                # 140 = 0 rot; 255 = 255 rot
                # 140 = 255 grün; 255 = 0 grün
                
                # 255-140 = 115
                # ((relatives level) / max relatives level)*255
                rotPegel = ((sample[2] - 140) / 115) * 255
                gruenPegel = 255-rotPegel
                
                if gruenPegel < 5:
                    gruenPegel = 0
                
                setLights(M_RED_PIN, 255)
                setLights(M_GREEN_PIN, gruenPegel)
                print(Fore.RED + "    Midd: " + str(sample[2]), end = '')

            # HIGH
            if sample[3] < 90:
                setLights(H_RED_PIN, 0)
                setLights(H_GREEN_PIN, sample[3])
                output(sample[3], "    High")
            elif sample[3] >= 90 and sample[3] < 140:
                gruenPegel = (sample[3]/140)*255
                setLights(H_RED_PIN, 0)
                setLights(H_GREEN_PIN, gruenPegel)
                output(sample[3], "    High")
            elif sample[3] >= 140 and sample[3] < 210:
                # 210-140 = 70
                # ((relatives level) / max relatives level)*255
                rotPegel = ((sample[3] - 140) / 70) * 255
                setLights(H_RED_PIN, rotPegel)
                setLights(H_GREEN_PIN, 255)
                print(Fore.YELLOW + "    High: " + str(sample[3]))
            elif sample[3] >= 210:
                # 140 = 0 rot; 255 = 255 rot
                # 140 = 255 grün; 255 = 0 grün
                
                # 255-140 = 115
                # ((relatives level) / max relatives level)*255
                rotPegel = ((sample[3] - 140) / 115) * 255
                gruenPegel = 255-rotPegel
                
                if gruenPegel < 0:
                    gruenPegel = 0
                
                setLights(H_RED_PIN, 255)
                setLights(H_GREEN_PIN, gruenPegel)
                print(Fore.RED + "    High: " + str(sample[3]))

if __name__ == "__main__":
    run()
