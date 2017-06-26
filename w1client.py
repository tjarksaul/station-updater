# -*- coding: utf-8 -*-


class W1Client(object):
    """docstring for W1Client"""

    def __init__(self, w1_id):
        # type: (str) -> W1Client
        self.id = w1_id

    def read(self):
        # type: () -> float
        f = open('/sys/bus/w1/devices/' + self.id + '/w1_slave')
        content = f.read()
        f.close()

        string = content.split("\n")[1].split(" ")[9]
        temperature = float(string[2:]) / 1000

        return temperature
