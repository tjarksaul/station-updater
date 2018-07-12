#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import unittest

import dlrgclient


class DLRGClientTest(unittest.TestCase):
    def setUp(self):
        self.user = os.environ.get("TEST_DLRG_USER")
        self.password = os.environ.get("TEST_DLRG_PASS_VALID")
        self.org_id = os.environ.get("TEST_DLRG_GLIE")
        self.station_id = int(os.environ.get("TEST_DLRG_STAT"))
        self.dlrgclient = dlrgclient.DLRGClient(username=self.user, password=self.password,
                                                org_id=self.org_id, station_id=self.station_id)

    def testLogin(self):
        self.assertTrue(self.dlrgclient.login())

    def testLoginWithInvalidPassword(self):
        self.password = os.environ.get("TEST_DLRG_PASS_INVALID")
        self.dlrgclient = dlrgclient.DLRGClient(username=self.user, password=self.password,
                                                org_id=self.org_id, station_id=self.station_id)
        self.assertFalse(self.dlrgclient.login())

    def testYSetStatus(self):
        self.dlrgclient.login()
        status = dlrgclient.DLRGClient.Status(status=dlrgclient.DLRGClient.States.BATHING_ALLOWED,
                                              wind_hose=False, wind_kmh=42,
                                              wind_direction=dlrgclient.DLRGClient.WindDirections.ALL,
                                              air_measured=23, air_felt=21, water_temp=23.42)
        self.assertTrue(self.dlrgclient.set_status(status))

    def testZGetStatus(self):
        self.dlrgclient.login()
        response = self.dlrgclient.get_status_testable()
        self.assertIsInstance(response, dlrgclient.DLRGClient.Status)
        self.assertEqual(response.status, dlrgclient.DLRGClient.States.BATHING_ALLOWED)

    def testLoginHaelt15Minuten(self):
        import time
        print "Login at ", time.ctime()
        self.dlrgclient.login()
        time.sleep(15 * 60)
        print "Check at ", time.ctime()
        self.assertTrue(self.dlrgclient.check_login(time_check=False))


if __name__ == '__main__':
    unittest.main()
