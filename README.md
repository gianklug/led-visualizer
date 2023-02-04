# led-strips.py

* `modprobe snd_aloop`
* `pigpiod`
* `systemctl start snapclient.service`

# din-led-strips.py

* For NeoPixel Strip Rolle
* And any Rasperry pi

## Dependency
### Linux (Input)
* cava: https://github.com/karlstav/cava
* snapclient (optional): https://github.com/badaix/snapcast
* alsa

### Python3
* `pip3 inatall board neopixel readchar`

### run
* `modprobe snd_aloop`
* `systemctl start snapclient.service`
* `python din-led-strips.py`

## Raspberry
you need a 5V DC power supply with at least 1.5A (4 bars).  
Connect the red wires of the strips to the 5V DC, the white wires (black) to GND.  
The thorough (DIN) must be looped through from the beginning to the last strip.  
This cable is connected to GPIO18 on the Raspberry.  
Connect one GND of the Raspberry also with the GND of the 5V DC power supply.  

## configure
* define up to where the green range goes (0 - 255)
`MAX_GREEN = 140`  

* define up to where the orange range goes (0 - 255)
`MAX_ORANGE = 210`

* define how many pixels (LED) a bar has
`NUMBER_OF_PIXELS_PER_BAR = 60`

* define how many bars you have
`NUMBER_OF_BARS = 4`

* Preset the brightness of the LED
`BRIGHTNESS = 0.1`
