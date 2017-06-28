# -*- coding: utf-8 -*-
import datetime
import os

import astral
from Adafruit_LED_Backpack import SevenSegment


class Display(object):
    """docstring for Display"""

    def __init__(self, address):
        # type: (int) -> Display
        self.address = address
        self.display = SevenSegment.SevenSegment(address=address)
        self.display.begin()
        self.display.clear()

        self.DARKER_AT_NIGHT = bool(os.environ.get('DISPLAY_DARKER_AT_NIGHT'))
        if self.DARKER_AT_NIGHT:
            self.loc = astral.Location(('ClientLocation', 'ClientRegion', float(os.environ.get('LATITUDE')),
                                        float(os.environ.get('LONGITUDE')), 'UTC',
                                        int(os.environ.get('ELEVATION'))))

    def is_day(self):
        sunrise = self.loc.sunrise()
        sunset = self.loc.sunset()
        now = datetime.datetime.now(sunrise.tzinfo)
        return sunrise < now < sunset

    def write_temperature(self, value):
        # type: (float) -> None
        value = float(value)
        prefix = ""
        if 10.0 > value >= 0.0:
            prefix = " "
        string_value = prefix + str(value)

        self.display.set_digit(0, string_value[0])
        self.display.set_digit(1, string_value[1])
        if value <= -10.0 or value >= 100.0:
            self.display.set_decimal(1, False)
            self.display.set_digit(2, string_value[2])
        else:
            self.display.set_decimal(1, True)
            self.display.set_digit(2, string_value[3])
        self.display.set_digit_raw(3, 0x63)  # degree sign

        if not self.DARKER_AT_NIGHT or self.is_day():
            self.display.set_brightness(15)
        else:
            self.display.set_brightness(0)

        self.display.write_display()

    def exit(self):
        self.display.clear()
        self.display.write_display()
