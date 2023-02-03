#!/usr/bin/python3
import os
import struct
import subprocess
import tempfile

import board
import neopixel

#import colorama
#from colorama import Fore, Style

### Configuration ###

GREEN_RANGE = 150
ORANGE_RANGE = 210

NUMBER_OF_PIXELS_PER_BAR = 60
NUMBER_OF_BARS = 1

### DO NOT EDIT ###

SAMPLE_PIXEL = 0

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

MAX_PIXEL = (NUMBER_OF_PIXELS_PER_BAR*NUMBER_OF_BARS)

pixels = neopixel.NeoPixel(board.D18, MAX_PIXEL, auto_write=False, pixel_order=neopixel.RGB, brightness=1)

config = conpat % (NUMBER_OF_BARS, RAW_TARGET, OUTPUT_BIT_FORMAT)
bytetype, bytesize, bytenorm = ("H", 2, 65535) if OUTPUT_BIT_FORMAT == "16bit" else ("B", 1, 255)

def calc_pixel(calc_in):
    # BAR-1:  65, r = 15
    # BAR-2: 178, r = 41
    # BAR-3:  10, r =  2
    calc_out = (((NUMBER_OF_PIXELS_PER_BAR-1)/255))*calc_in
    calc_out = int(calc_out)
    return calc_out

def set_pixel(s_sample, s_max_pixel, s_pixels,    green, red, range_pixel, s_count_bar):
    # BAR-1:        65,          59,  command,       67,   0,           0,  1
    # BAR-2:       178,         119,  command, 178/2=89, 178,         150,  2
    # BAR-3:        10,         179,  command,        0,  10,         210,  3

    s_calc_pixel = calc_pixel(s_sample)
    # BAR-1: 15
    # BAR-2: 41
    # BAR-3:  2

    s_calc_pixel = (s_calc_pixel+((s_count_bar-1)*NUMBER_OF_PIXELS_PER_BAR))
    # BAR-1: 15+((1-1)*60) =  15
    # BAR-2: 41+((2-1)*60) = 101
    # BAR-3:  2+((3-1)*60) = 122

    while s_max_pixel > s_calc_pixel:
    # BAR-1:       59 > 15
    # BAR-2:      119 > 101
    # BAR-3:      179 > 122
        s_pixels[s_max_pixel] = (0, 0, 0)
        s_max_pixel -= 1

    s_calc_pixel = calc_pixel(range_pixel)
    # BAR-1: ((60-1)/255)*0   =  0  (green)
    # BAR-2: ((60-1)/255)*150 = 35  (orange)
    # BAR-3: ((60-1)/255)*210 = 49  (red)

    s_start_pixel = ((s_count_bar-1)*NUMBER_OF_PIXELS_PER_BAR)
    while s_start_pixel <= s_calc_pixel:
        print(str(s_start_pixel) + " <= " + str(s_calc_pixel))
    # BAR-1:          0 <=  15
    # BAR-2:         60 <= 101
    # BAR-3:        120 <= 122
        s_pixels[s_start_pixel] = (green, red, 0)
        s_start_pixel += 1

def define_pixel(d_sample, GREEN_RANGE, GREEN_ORANGE, d_max_pixel, d_count_bar):
    # BAR-1:           67,         150,          210,          59, 1
    # BAR-2:          178,         150,          210,         119, 2
    # BAR-3:           10,         150,          210,         179, 3
    if d_sample < GREEN_RANGE:
#        print("GREEN  - bar: " + str(d_count_bar) + " input: " + str(d_sample))
        set_pixel(d_sample, d_max_pixel, pixels, d_sample, 0, 0, d_count_bar)
  
    elif d_sample >= GREEN_RANGE and d_sample < GREEN_ORANGE:
#        print("ORANGE - bar: " + str(d_count_bar) + " input: " + str(d_sample))
        set_pixel(d_sample, d_max_pixel, pixels, int(d_sample/2), d_sample, GREEN_RANGE, d_count_bar)
              
    elif d_sample >= GREEN_ORANGE and d_sample < 255:
#        print("RED    - bar: " + str(d_count_bar) + " input: " + str(d_sample))
        set_pixel(d_sample, d_max_pixel, pixels, 0, d_sample, GREEN_ORANGE, d_count_bar)

def run():
    with tempfile.NamedTemporaryFile() as config_file:
        config_file.write(config.encode())
        config_file.flush()
  
        process = subprocess.Popen(["cava", "-p", config_file.name], stdout=subprocess.PIPE)
        chunk = bytesize * NUMBER_OF_BARS
        fmt = bytetype * NUMBER_OF_BARS

  
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

            count_bar = 1
            while count_bar <= NUMBER_OF_BARS:
                max_pixel = ((NUMBER_OF_PIXELS_PER_BAR*count_bar)-1)
                # BAR-1: (60*1)-1 =  59
                # BAR-2: (60*2)-1 = 119
                # BAR-3: (60*3)-1 = 179
                define_pixel(int(sample[(count_bar-1)]), GREEN_RANGE, ORANGE_RANGE, max_pixel, count_bar)
                count_bar += 1
            pixels.show()
  
if __name__ == "__main__":
    run()
