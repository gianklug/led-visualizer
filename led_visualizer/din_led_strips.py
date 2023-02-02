#!/usr/bin/python3
import os
import struct
import subprocess
import tempfile

import board
import neopixel

#import colorama
#from colorama import Fore, Style

pixels = neopixel.NeoPixel(board.D18, 60, auto_write=False, pixel_order=neopixel.RGB, brightness=0.2)

SAMPLE_PIXEL = 0
GREEN_RANGE = 150
ORANGE_RANGE = 210

MAX_RED_PIXEL = 59

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

def calc_pixel(calc_in):
    calc_out = ((59/255))*calc_in
    calc_out = int(calc_out)
    return calc_out

def set_pixel(s_sample, s_max_pixel, s_pixels, green, red, range_pixel):
    s_calc_pixel = calc_pixel(s_sample)
    while s_max_pixel > s_calc_pixel:
        s_pixels[s_max_pixel] = (0, 0, 0)
        s_max_pixel -= 1
    s_max_pixel = calc_pixel(range_pixel)
    while s_max_pixel <= s_calc_pixel:
        s_pixels[s_max_pixel] = (green, red, 0)
        s_max_pixel += 1

def define_pixel(d_sample, d_low, d_mid, d_max_pixel):
    # BASS
    # 60 pixels / 3 = 20 pixels per color
    # sample 255 / 3 = 85
    # sample_bass = int(sample[0]+sample[1]/2)
    if d_sample < d_low:
        set_pixel(d_sample, d_max_pixel, pixels, d_sample, 0, 0)
  
    elif d_sample >= d_low and d_sample < d_mid:
        set_pixel(d_sample, d_max_pixel, pixels, int(d_sample/2), d_sample, d_low)
              
    elif d_sample >= d_mid and d_sample < 255:
        set_pixel(d_sample, d_max_pixel, pixels, 0, d_sample, d_mid)

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
            define_pixel(int(sample[0]), GREEN_RANGE, ORANGE_RANGE, MAX_RED_PIXEL)
            pixels.show()
  
if __name__ == "__main__":
    run()
