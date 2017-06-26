# -*- coding: utf-8 -*-

import time
from threading import Thread

import RPi.GPIO as GPIO

import display


class PotiClient(Thread):
    """docstring for PotiClient"""

    def __init__(self, potentiometer_adc, clockpin, mosipin, misopin,
                 cspin, dis=display.Display(0x70), low=0.0,
                 high=30.0, step=0.5):
        # type: (int, int, int, int, int, display.Display, float, float, float) -> PotiClient
        super(PotiClient, self).__init__(name="PotiClient")
        if potentiometer_adc > 7 or potentiometer_adc < 0:
            raise ValueError("We only have 7 adc pins")
        self.potentiometer_adc = potentiometer_adc
        self.clockpin = clockpin
        self.mosipin = mosipin
        self.misopin = misopin
        self.cspin = cspin
        self.low = low
        self.high = high - low
        self.step = 1 / step
        self.display = dis
        self.killed = False

        self.setup_gpio()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.killed = True

    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.mosipin, GPIO.OUT)
        GPIO.setup(self.misopin, GPIO.IN)
        GPIO.setup(self.clockpin, GPIO.OUT)
        GPIO.setup(self.cspin, GPIO.OUT)

    def readadc(self):
        # type: () -> int
        GPIO.output(self.cspin, True)

        GPIO.output(self.clockpin, False)  # start clock low
        GPIO.output(self.cspin, False)  # bring CS low

        commandout = self.potentiometer_adc
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3  # we only need to send 5 bits here
        for i in range(5):
            if commandout & 0x80:
                GPIO.output(self.mosipin, True)
            else:
                GPIO.output(self.mosipin, False)
            commandout <<= 1
            GPIO.output(self.clockpin, True)
            GPIO.output(self.clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
            GPIO.output(self.clockpin, True)
            GPIO.output(self.clockpin, False)
            adcout <<= 1
            if GPIO.input(self.misopin):
                adcout |= 0x1

        GPIO.output(self.cspin, True)

        adcout >>= 1  # first bit is 'null' so drop it
        return adcout

    def get_value(self, low=None, high=None, step=None):
        # type: (float, float, float) -> float
        if low is None:
            low = self.low
        if high is None:
            high = self.high
        else:
            high = high - low
        if step is None:
            step = self.step
        else:
            step = 1 / step
        trim_pot = self.readadc()
        value = round(((trim_pot / 1023.0 * high) + low) * step) / step
        return value

    def run(self):
        print "Starting PotiClient..."
        while True:
            if self.killed:
                print "Exiting PotiClient..."
                GPIO.cleanup()
                self.display.exit()
                break
            value = self.get_value()
            self.display.write_temperature(value)
            time.sleep(0.5)
