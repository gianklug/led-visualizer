#!/usr/bin/python3
import os
import struct
import subprocess
import tempfile

import board
import neopixel

import signal
import time
import readchar


### Configuration ###

MAX_GREEN = 140
MAX_ORANGE = 210

NUMBER_OF_PIXELS_PER_BAR = 60
NUMBER_OF_BARS = 4

BRIGHTNESS = 0.1

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
noise_reduction = 30
[eq]
1 = 1
2 = 0.9
3 = 0.9
4 = 0.9
"""

MAX_PIXEL = (NUMBER_OF_PIXELS_PER_BAR*NUMBER_OF_BARS)

pixels = neopixel.NeoPixel(board.D18, MAX_PIXEL, auto_write=False, pixel_order=neopixel.RGB, brightness=BRIGHTNESS)

config = conpat % (NUMBER_OF_BARS, RAW_TARGET, OUTPUT_BIT_FORMAT)
bytetype, bytesize, bytenorm = ("H", 2, 65535) if OUTPUT_BIT_FORMAT == "16bit" else ("B", 1, 255)

def exit(signum, frame):
    pixels.fill((0,0,0))
    pixels.show()
    res = readchar.readchar()
    exit(0)

signal.signal(signal.SIGINT, exit)

def calc(calc_in):
    calc_out = (((NUMBER_OF_PIXELS_PER_BAR-1)/255)*calc_in)
    calc_out = int(calc_out)
    return calc_out

def pixel_define(pd_sample, pd_count_bar, pd_low, pd_max):
    pd_set_pixel = calc(pd_low) # 35
    pd_set_pixel = pd_set_pixel+((pd_count_bar-1)*NUMBER_OF_PIXELS_PER_BAR) # 35 / 95 / 155
    pd_calc_sample = calc(pd_sample) # 58
    pd_calc_sample = (pd_calc_sample+((pd_count_bar-1)*NUMBER_OF_PIXELS_PER_BAR)) # 58 / 118 / 178
    pd_end_pixel = calc(pd_max-1) # 49
    pd_end_pixel = pd_end_pixel+((pd_count_bar-1)*NUMBER_OF_PIXELS_PER_BAR) # 49 / 109 / 169
    return pd_set_pixel, pd_calc_sample, pd_end_pixel

def set_dark(sd_sample, sd_count_bar, sd_pixels):
    sd_calc_sample = calc(sd_sample)
    sd_calc_sample = (sd_calc_sample+((sd_count_bar-1)*NUMBER_OF_PIXELS_PER_BAR))
    sd_max_pixel = ((sd_count_bar*NUMBER_OF_PIXELS_PER_BAR)-1)
    while sd_max_pixel > sd_calc_sample:
        sd_pixels[sd_max_pixel] = (0, 0, 0)
        sd_max_pixel -= 1

def set_green(g_sample, g_pixels, g_count_bar):
    g_set_pixel, g_calc_sample, g_end_pixel = pixel_define(g_sample, g_count_bar, 0, MAX_GREEN)
    while g_set_pixel <= g_calc_sample and g_set_pixel <= g_end_pixel:
        g_pixels[g_set_pixel] = (g_sample, 0, 0)
        g_set_pixel += 1

def set_orange(o_sample, o_pixels, o_count_bar):
    o_set_pixel, o_calc_sample, o_end_pixel = pixel_define(o_sample, o_count_bar, MAX_GREEN, MAX_ORANGE)
    while o_set_pixel <= o_calc_sample and o_set_pixel <= o_end_pixel:
        o_pixels[o_set_pixel] = (int(o_sample/2), o_sample, 0)
        o_set_pixel += 1

def set_red(r_sample, r_pixels, r_count_bar):
    r_set_pixel, r_calc_sample, r_end_pixel = pixel_define(r_sample, r_count_bar, MAX_ORANGE, 255)
    while r_set_pixel <= r_calc_sample and r_set_pixel <= r_end_pixel:
        r_pixels[r_set_pixel] = (0, r_sample, 0)
        r_set_pixel += 1

def band_split(d_sample, d_count_bar):
    print(d_sample)
    set_dark(d_sample, d_count_bar, pixels)
    if d_sample < MAX_GREEN:
        set_green(d_sample, pixels, d_count_bar)
  
    elif d_sample >= MAX_GREEN and d_sample < MAX_ORANGE:
        set_green(d_sample, pixels, d_count_bar)
        set_orange(d_sample, pixels, d_count_bar)
              
    elif d_sample >= MAX_ORANGE and d_sample < 255:
        set_green(d_sample, pixels, d_count_bar)
        set_orange(d_sample, pixels, d_count_bar)
        set_red(d_sample, pixels, d_count_bar)

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
            print("---------------")
            while count_bar <= NUMBER_OF_BARS:
                print("BAR[" + str(count_bar) + "]: " , end = '')
                band_split(int(sample[(count_bar-1)]), count_bar)
                count_bar += 1
            pixels.show()
  
if __name__ == "__main__":
    run()
