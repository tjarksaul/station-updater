#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import signal
import sys
import time
from os.path import join, dirname
from threading import Thread

import RPi.GPIO as GPIO
from dotenv import load_dotenv

import display
import dlrgclient
import poticlient
import switch
import w1todisplay


def init_dotenv():
    print "Initiating dotenv"
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)


init_dotenv()


class Main(object):
    """docstring for Main"""
    STATE_LED = int(os.environ.get("STATE_LED_PIN"))
    GREEN_LED = int(os.environ.get("GREEN_LED_PIN"))
    RED_LED = int(os.environ.get("RED_LED_PIN"))
    AVAIL_TOGGLE_PIN = int(os.environ.get("AVAIL_TOGGLE_PIN"))
    STATE_SWITCH_PIN = int(os.environ.get("STATE_SWITCH_PIN"))

    def __init__(self):
        # Instance attributes to be assigned later
        self.poticlient = None
        self.w1client = None
        self.pushbutton = None
        self.toggleswitch = None
        self.refreshthread = None
        self.just_toggled = False

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.STATE_LED, GPIO.OUT)
        GPIO.setup(self.GREEN_LED, GPIO.OUT)
        GPIO.setup(self.RED_LED, GPIO.OUT)

        self.state = False
        GPIO.output(self.STATE_LED, self.state)

        self.push_button()
        self.toggle_switch()
        self.toggle = not bool(GPIO.input(self.AVAIL_TOGGLE_PIN))
        self.dlrgclient = dlrgclient.DLRGClient(username=os.environ.get("DLRG_USER"),
                                                password=os.environ.get("DLRG_PASS"),
                                                org_id=os.environ.get("DLRG_GLIE"),
                                                station_id=int(os.environ.get("DLRG_STAT")))
        self.w1_thread()
        self.poti_thread()
        self.refresh_thread()
        Thread(target=self.dlrgclient.login, name="LoginThread").start()

    def exit(self):
        self.poticlient.__exit__(1, 1, 1)
        self.w1client.__exit__(1, 1, 1)
        GPIO.cleanup()

    def poti_thread(self):
        dis = display.Display(int(os.environ.get("WATER_DISPLAY_ADDRESS"), 0))
        self.poticlient = poticlient.PotiClient(potentiometer_adc=int(os.environ.get("POTENTIOMETER_ADC")),
                                                clockpin=int(os.environ.get("CLOCKPIN")),
                                                mosipin=int(os.environ.get("MOSIPIN")),
                                                misopin=int(os.environ.get("MISOPIN")),
                                                cspin=int(os.environ.get("CSPIN")),
                                                dis=dis, low=float(os.environ.get("WATER_LOW")),
                                                high=float(os.environ.get("WATER_HIGH")),
                                                step=float(os.environ.get("WATER_STEP")))
        self.poticlient.start()

    def w1_thread(self):
        self.w1client = w1todisplay.W1ToDisplay(os.environ.get("AIR_W1_ID"))
        self.w1client.start()

    def refresh_thread(self):
        self.refreshthread = Thread(target=self.refresh_loop, name="Refresh")
        self.refreshthread.daemon = True
        self.refreshthread.start()

    def push_button_pressed(self, _):
        self.just_toggled = True
        print "Push button pressed"
        self.update_status(True)

    def update_status(self, local, state=None):
        if state is None:
            self.state = not self.state
        else:
            self.state = state
        GPIO.output(self.STATE_LED, self.state)
        if local:
            states = dlrgclient.DLRGClient.States
            state = states.NOT_ON_DUTY
            if self.state:
                if self.toggle:
                    state = states.BATHING_ALLOWED
                else:
                    state = states.BATHING_PROHIBITED
            status = dlrgclient.DLRGClient.Status(status=state, air_measured=self.w1client.read(),
                                                  water_temp=self.poticlient.get_value())
            Thread(target=self.set_status, name="UpdateThread", args=[status]).start()
            print "current status:\n", status

    def set_status(self, status):
        if not self.dlrgclient.check_login():
            self.dlrgclient.login()
        self.dlrgclient.set_status(status)
        self.just_toggled = False

    def push_button(self):
        self.pushbutton = switch.Switch(self.STATE_SWITCH_PIN)
        self.pushbutton.start(self.push_button_pressed)

    def toggle_switch_changed(self, channel):
        print "Toggle changed to ", not GPIO.input(channel)
        self.toggle = not bool(GPIO.input(channel))
        GPIO.output(self.GREEN_LED, not self.toggle)
        GPIO.output(self.RED_LED, self.toggle)
        self.update_status(local=True, state=self.state)

    def toggle_switch(self):
        self.toggleswitch = switch.Switch(self.AVAIL_TOGGLE_PIN)
        self.toggleswitch.start(self.toggle_switch_changed)

    def refresh_loop(self):
        print "Starting refresh loop..."
        while True:
            time.sleep(1)
            self.refresh_from_dlrg_status()
            time.sleep(float(os.environ.get("DLRG_REFRESH_INTERVAL")) * 60)

    def refresh_from_dlrg_status(self):
        if self.just_toggled:
            print "Status has been changed via push button. Not refreshing."
            return
        status = self.dlrgclient.get_status()
        print "Loaded status from dlrg.net:\n", status
        if (status.status == dlrgclient.DLRGClient.States.NOT_ON_DUTY and self.state) \
                or (not (status.status == dlrgclient.DLRGClient.States.NOT_ON_DUTY) and not self.state):
            print "Setting status from dlrg.net"
            self.update_status(False)
            # todo: Eventuell die Lampen am Toggle umschalten
        if not (status.status == dlrgclient.DLRGClient.States.NOT_ON_DUTY):
            water_diff = abs(
                status.water_temp - self.poticlient.get_value()) if status.water_temp is not None else sys.maxint
            air_diff = abs(
                status.air_measured - self.w1client.read()) if status.air_measured is not None else sys.maxint
            if air_diff > 0.5 or water_diff > 0.5:
                # a temp did change > 0.5 degrees. We update the remote side
                print "water temp did change ", water_diff, " degrees. Air temp did change ", air_diff, \
                    " degrees. Updating the remote side."
                self.update_status(local=True, state=self.state)


def exit_gracefully(*_):
    signal.signal(signal.SIGINT, original_sigint)
    main.exit()
    sys.exit(0)


if __name__ == '__main__':
    main = Main()
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, exit_gracefully)
    while True:
        time.sleep(1)
