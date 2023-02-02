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
sample_pixel = 0

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

def set_pixel(sample_bass, max_pixel, pixels, g, r, range_pixel):
    sample_pixel = calc_pixel(sample_bass)
    while max_pixel > sample_pixel:
        pixels[max_pixel] = (0, 0, 0)
        max_pixel -= 1
    max_pixel = calc_pixel(range_pixel)
    while max_pixel <= sample_pixel:
        pixels[max_pixel] = (g, r, 0)
        max_pixel += 1

def run_bass(sample):
    # BASS
    # 60 pixels / 3 = 20 pixels per color
    # sample 255 / 3 = 85
    # sample_bass = int(sample[0]+sample[1]/2)
    sample_bass = int(sample[0])
    low_range = 100
    mid_range = 200
    if sample_bass < low_range:
        set_pixel(sample_bass, 59, pixels, sample_bass, 0, 0)
  
    elif sample_bass >= low_range and sample_bass < mid_range:
        set_pixel(sample_bass, 59, pixels, int(sample_bass/2), sample_bass, low_range)
              
    elif sample_bass >= mid_range and sample_bass < 255:
        set_pixel(sample_bass, 59, pixels, 0, sample_bass, mid_range)

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
            run_bass(sample)
            pixels.show()
  
if __name__ == "__main__":
    run()
