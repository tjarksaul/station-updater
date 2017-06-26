# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO


class Switch(object):
    """docstring for Switch"""

    def __init__(self, gpio):
        # type: (int) -> Switch
        self.gpio = gpio
        self.setup_gpio()

    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def start(self, callback):
        GPIO.add_event_detect(self.gpio, GPIO.RISING, callback=callback, bouncetime=1000)

    def stop(self):
        GPIO.remove_event_detect(self.gpio)
