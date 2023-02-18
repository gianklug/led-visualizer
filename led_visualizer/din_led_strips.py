#!/usr/bin/python3
import os
import struct
import subprocess
import tempfile

import board
import platform

# If no raspberry pi, use virtual
if platform.machine() == "x86_64":
    virtual = True
else:
    import neopixel
    virtual = False


import signal
import readchar

### Configuration ###

MAX_GREEN = 140
MAX_ORANGE = 210

NUMBER_OF_PIXELS_PER_BAR = 60
NUMBER_OF_BARS = 10

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
framerate = 20
[output]
method = raw
raw_target = %s
bit_format = %s
channels = mono
[smoothing]
noise_reduction = 20
"""

MAX_PIXEL = (NUMBER_OF_PIXELS_PER_BAR*NUMBER_OF_BARS)

if virtual:
    PIXEL_COM = [(0,0,0)]*MAX_PIXEL
else:
    PIXEL_COM = neopixel.NeoPixel(board.D18, MAX_PIXEL, auto_write=False, pixel_order=neopixel.RGB, brightness=BRIGHTNESS)

config = conpat % (NUMBER_OF_BARS, RAW_TARGET, OUTPUT_BIT_FORMAT)
bytetype, bytesize, bytenorm = ("H", 2, 65535) if OUTPUT_BIT_FORMAT == "16bit" else ("B", 1, 255)


# print color
def color_encode(pixel):
    return f"\033[38;2;{pixel[0]};{pixel[1]};{pixel[2]}m*\033[0m"

def exit(signum, frame):
    if not virtual:
        PIXEL_COM.fill((0,0,0))
        PIXEL_COM.show()
    res = readchar.readchar()
    exit(0)

signal.signal(signal.SIGINT, exit)

def cache_pixels():
    cache = {}
    for number in range(1+(NUMBER_OF_PIXELS_PER_BAR*NUMBER_OF_BARS)):
        current_bar = number // NUMBER_OF_PIXELS_PER_BAR 
        if (current_bar % 2 == 1 and current_bar != 0) and not virtual:
            real_number = abs(number - ((NUMBER_OF_PIXELS_PER_BAR-1) + current_bar*NUMBER_OF_PIXELS_PER_BAR))+current_bar*NUMBER_OF_PIXELS_PER_BAR
            cache[number] = real_number
        else:
            cache[number] = number
    return cache

cache = cache_pixels()

def set_pixel(PIXEL_COM, number, value):
    PIXEL_COM[cache[number]] = value

def calc(calc_in):
    calc_out = int(((NUMBER_OF_PIXELS_PER_BAR-1)/255)*calc_in)
    return calc_out

def pixel_define(pd_sample, pd_count_bar, pd_low, pd_max):
    pd_set_pixel = calc(pd_low)+((pd_count_bar-1)*NUMBER_OF_PIXELS_PER_BAR)
    pd_calc_sample = calc(pd_sample)+((pd_count_bar-1)*NUMBER_OF_PIXELS_PER_BAR)
    pd_end_pixel = calc(pd_max-1)+((pd_count_bar-1)*NUMBER_OF_PIXELS_PER_BAR)
    return pd_set_pixel, pd_calc_sample, pd_end_pixel

def set_dark(sd_sample, sd_count_bar):
    sd_calc_sample = calc(sd_sample)+((sd_count_bar-1)*NUMBER_OF_PIXELS_PER_BAR)
    sd_max_pixel = ((sd_count_bar*NUMBER_OF_PIXELS_PER_BAR)-1)
    while sd_max_pixel > sd_calc_sample:
        set_pixel(PIXEL_COM, sd_max_pixel, (0, 0, 0))
        sd_max_pixel -= 1

def set_green(g_sample, g_count_bar):
    g_set_pixel, g_calc_sample, g_end_pixel = pixel_define(g_sample, g_count_bar, 0, MAX_GREEN)
    while g_set_pixel <= g_calc_sample and g_set_pixel <= g_end_pixel:
        set_pixel(PIXEL_COM, g_set_pixel, (g_sample, 0, 0))
        g_set_pixel += 1

def set_orange(o_sample, o_count_bar):
    global OUTPUT
    o_set_pixel, o_calc_sample, o_end_pixel = pixel_define(o_sample, o_count_bar, MAX_GREEN, MAX_ORANGE)
    while o_set_pixel <= o_calc_sample and o_set_pixel <= o_end_pixel:
        set_pixel(PIXEL_COM, o_set_pixel, (int(o_sample/2), o_sample, 0))
        o_set_pixel += 1

def set_red(r_sample, r_count_bar):
    r_set_pixel, r_calc_sample, r_end_pixel = pixel_define(r_sample, r_count_bar, MAX_ORANGE, 255)
    while r_set_pixel <= r_calc_sample and r_set_pixel <= r_end_pixel:
        set_pixel(PIXEL_COM, r_set_pixel, (0, r_sample, 0))
        r_set_pixel += 1

def band_split(d_sample, d_count_bar):
    #print(d_sample)
    set_dark(d_sample, d_count_bar)
    if d_sample < MAX_GREEN:
        set_green(d_sample, d_count_bar)
  
    elif d_sample >= MAX_GREEN and d_sample < MAX_ORANGE:
        set_green(d_sample, d_count_bar)
        set_orange(d_sample, d_count_bar)
              
    elif d_sample >= MAX_ORANGE and d_sample < 255:
        set_green(d_sample, d_count_bar)
        set_orange(d_sample, d_count_bar)
        set_red(d_sample, d_count_bar)

def show_virtual():
    print("\033c", end="")
    for i in range(0, NUMBER_OF_BARS):
        for j in range(0, NUMBER_OF_PIXELS_PER_BAR):
            pixel = PIXEL_COM[(i*NUMBER_OF_PIXELS_PER_BAR)+j]
            print(color_encode(pixel), end="")
        print("\n", end="")
    print()
    

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

        while 1:
            data = source.read(chunk)
            if len(data) < chunk:
                break
            sample = struct.unpack(fmt, data)

            count_bar = 1
            while count_bar <= NUMBER_OF_BARS:
                band_split(int(sample[(count_bar-1)]), count_bar)
                count_bar += 1

            if virtual:
                show_virtual()
            else:
                PIXEL_COM.show()

  
if __name__ == "__main__":
    run()
