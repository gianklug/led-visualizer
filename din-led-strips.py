#!/usr/bin/python3
import os
import struct
import subprocess
import tempfile

import sys
import termios
import tty
import time

import board
import neopixel

import colorama
from colorama import Fore, Style

pixels = neopixel.NeoPixel(board.D18, 60, auto_write=False, pixel_order=neopixel.RGB, brightness=0.2)

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
noise_reduction = 40
[eq]
1 = 1
2 = 1.1
3 = 0.9
4 = 0.9
"""

config = conpat % (BARS_NUMBER, RAW_TARGET, OUTPUT_BIT_FORMAT)
bytetype, bytesize, bytenorm = ("H", 2, 65535) if OUTPUT_BIT_FORMAT == "16bit" else ("B", 1, 255)

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
            # 60 pixels / 3 = 20 pixels per color
            # out 255 / 3 = 85
            #sampleBass = int(sample[0]+sample[1]/2)
            sampleBass = int(sample[0])
            lowRange = 100
            midRange = 200
            if sampleBass < lowRange:
                count = 59
                pix = ((59/255))*sampleBass
                pix = int(pix)
                while count > pix:
                    pixels[count] = (0, 0, 0)
                    count -= 1
                count = 0
                while count <= pix:
                    pixels[count] = (sampleBass, 0, 0)
                    count += 1

            elif sampleBass >= lowRange and sampleBass < midRange:
                count = 59
                pix = ((59/255))*sampleBass
                pix = int(pix)
                while count > pix:
                    pixels[count] = (0, 0, 0)
                    count -= 1
                count = 20
                while count <= pix:
                    pixels[count] = (int(sampleBass/2), sampleBass, 0)
                    count += 1
                    
            elif sampleBass >= midRange and sampleBass < 255:
                count = 59
                pix = ((59/255))*sampleBass
                pix = int(pix)
                while count > pix:
                    pixels[count] = (0, 0, 0)
                    count -= 1
                count = 40
                while count <= pix:
                    pixels[count] = (0, sampleBass, 0)
                    count += 1
                    
            pixels.show()

if __name__ == "__main__":
    run()
