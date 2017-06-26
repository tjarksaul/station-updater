# -*- coding: utf-8 -*-

from Adafruit_LED_Backpack import SevenSegment


class Display(object):
    """docstring for Display"""

    def __init__(self, address):
        # type: (int) -> Display
        self.address = address
        self.display = SevenSegment.SevenSegment(address=address)
        self.display.begin()
        self.display.clear()

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

        self.display.write_display()

    def exit(self):
        self.display.clear()
        self.display.write_display()
