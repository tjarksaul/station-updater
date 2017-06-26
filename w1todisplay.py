# -*- coding: utf-8 -*-
import os
import time
from threading import Thread

import display
import w1client


class W1ToDisplay(Thread):
    """docstring for W1ToDisplay"""

    def __init__(self, w1_id):
        # type: (str) -> W1ToDisplay
        super(W1ToDisplay, self).__init__()
        self.id = w1_id
        self.display = display.Display(int(os.environ.get("AIR_DISPLAY_ADDRESS"), 0))
        self.killed = False
        self.client = w1client.W1Client(w1_id)

    def __exit__(self, exc_type, exc_value, traceback):
        self.killed = True

    def read(self):
        # type: () -> float
        return self.client.read()

    def run(self):
        while True:
            if self.killed:
                self.display.exit()
                break
            temperature = self.client.read()
            self.display.write_temperature(temperature)
            time.sleep(0.5)
