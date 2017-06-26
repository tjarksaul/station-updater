# -*- coding: utf-8 -*-
import json
import os

import requests


class DLRGClient(object):
    """docstring for DLRGClient"""
    DEBUG = os.environ.get("DEBUG")

    class States(object):
        NOT_ON_DUTY = "nn"
        BATHING_ALLOWED = "rotgelb"
        BATHING_DANGEROUS = "gelb"
        BATHING_PROHIBITED = "rot"

    class WindDirections(object):
        NONE = ""
        NORTH = "n"
        NORTH_NORTH_WEST = "nnw"
        NORTH_WEST = "nw"
        WEST_NORTH_WEST = "wnw"
        WEST = "w"
        WEST_SOUTH_WEST = "wsw"
        SOUTH_WEST = "sw"
        SOUTH_SOUTH_WEST = "ssw"
        SOUTH = "s"
        SOUTH_SOUTH_EAST = "sso"
        SOUTH_EAST = "so"
        EAST_SOUTH_EAST = "oso"
        EAST = "o"
        EAST_NORTH_EAST = "ono"
        NORTH_EAST = "no"
        NORTH_NORTH_EAST = "nno"
        ALL = "Umlaufend"

    class Status(object):
        def __init__(self, status=None, wind_hose=False,
                     wind_kmh=None, wind_bft=None, wind_direction=None,
                     air_measured=None, air_felt=None, water_temp=None):
            self.status = status
            self.wind_hose = wind_hose
            self.wind_kmh = wind_kmh
            self.wind_bft = wind_bft
            self.wind_direction = wind_direction
            self.air_measured = air_measured
            self.air_felt = air_felt
            self.water_temp = water_temp

        @classmethod
        def from_json(cls, obj):
            # type: (dict) -> DLRGClient.Status
            try:
                obj = obj["WRS"]["status"]
                status = cls(status=obj['status'], wind_hose=obj["windsack"],
                             wind_kmh=float(obj.get("windKmh")) if obj.get("windKmh") is not None else None,
                             wind_direction=obj.get('windRichtung'),
                             air_measured=float(obj.get("tempLuftGem")) if obj.get("tempLuftGem") is not None else None,
                             air_felt=float(obj.get("tempLuftGef")) if obj.get("tempLuftGef") is not None else None,
                             water_temp=float(obj.get("tempWasser")) if obj.get("tempWasser") is not None else None)
                if obj.get("windBft") is None:
                    if obj.get("windKmh") is not None:
                        status.wind_bft = cls.calculate_bft(float(obj.get("windKmh")))
                return status
            except KeyError:
                return DLRGClient.Status(status=DLRGClient.States.NOT_ON_DUTY)

        @staticmethod
        def calculate_bft(wind_kmh):
            # type: (float) -> int
            if wind_kmh < 0:
                raise ValueError("Wind speed must be at least 0.")
            if wind_kmh <= 1:
                return 0
            if wind_kmh <= 5:
                return 1
            if wind_kmh <= 11:
                return 2
            if wind_kmh <= 19:
                return 3
            if wind_kmh <= 28:
                return 4
            if wind_kmh <= 38:
                return 5
            if wind_kmh <= 49:
                return 6
            if wind_kmh <= 61:
                return 7
            if wind_kmh <= 74:
                return 8
            if wind_kmh <= 88:
                return 9
            if wind_kmh <= 102:
                return 10
            if wind_kmh <= 117:
                return 11
            return 12

    def __init__(self, username, password, org_id, station_id):
        self.username = username
        self.password = password
        self.stationId = station_id
        self.orgId = org_id
        self.sessionId = ""

    def login(self, set_org=True):
        try:
            response = requests.post(
                url="https://www.dlrg.net/index.php?doc=auth",
                params={
                    "doc": "auth",
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                },
                data={
                    "auth[user]": self.username,
                    "auth[pass]": self.password,
                    "url_params": "",
                },
                verify=not self.DEBUG,
            )
            self.sessionId = response.cookies['PHPSESSID']
            if self.username not in response.content:
                return False
            else:
                if not set_org:
                    return True
                else:
                    return self.set_org()
        except requests.exceptions.RequestException as e:
            print('HTTP Request failed: ' + e.message)
            return False

    def check_login(self):
        try:
            response = requests.get(
                url="https://www.dlrg.net/index.php",
                params={
                    "index",
                },
                headers={
                    "Referer": "https://www.dlrg.net/index.php?doc=auth",
                    "Cookie": "PHPSESSID=" + self.sessionId,
                },
                verify=not self.DEBUG,
            )
            if self.username not in response.content:
                return False
            else:
                return True
        except requests.exceptions.RequestException as e:
            print('HTTP Request failed: ' + e.message)
            return False

    def set_org(self):
        try:
            response = requests.post(
                url="https://www.dlrg.net/index.php",
                params={
                    "doc": "index",
                },
                headers={
                    "Cookie": "PHPSESSID=" + self.sessionId,
                    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                },
                data={
                    "constr": self.orgId + "#gld",
                },
                verify=not self.DEBUG,
            )
            if "(" + self.orgId + ")" in response.content:
                return True
            else:
                return False
        except requests.exceptions.RequestException as e:
            print('HTTP Request failed: ' + e.message)
            return False

    def set_status(self, status=None, wind_hose=False,
                   wind_kmh=None, wind_bft=None, wind_direction=None,
                   air_measured=None, air_felt=None, water_temp=None):
        # type: (self.States, bool, float, int, self.WindDirections, float, float, float) -> bool
        if status is None:
            status = self.States.BATHING_ALLOWED
        if wind_direction is None:
            wind_direction = self.WindDirections.NONE
        if wind_kmh is not None and wind_bft is not None:
            raise ValueError("you can only set wind speed in km/h or Bft, not both!")
        if wind_kmh is None:
            wind_kmh = ""
        if wind_bft is None:
            if wind_kmh == "":
                wind_bft = "-1"
            else:
                wind_bft = self.Status.calculate_bft(float(wind_kmh))
        if air_measured is None:
            air_measured = ""
        if air_felt is None:
            air_felt = ""
        if water_temp is None:
            water_temp = ""

        data = {
            "STATUS": status,
            "save": "Status melden",
            "STATIONID": self.stationId,
            "TEMP_LUFT_GEM": air_measured,
            "TEMP_WASSER": water_temp,
            "WIND_KMH": wind_kmh,
            "WIND_BFT": wind_bft,
            "TEMP_LUFT_GEF": air_felt,
            "ID": "",
            "WINDRICHTUNG": wind_direction,
        }
        if wind_hose:
            data["WINDSACK"] = "1"

        try:
            response = requests.post(
                url="https://www.dlrg.net/index.php",
                params={
                    "doc": "apps/wachstation/wachstationStatus",
                },
                headers={
                    "Cookie": "PHPSESSID=" + self.sessionId,
                    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                },
                data=data,
                verify=not self.DEBUG,
            )
            if "Status erfolgreich" in response.content:
                return True
            else:
                return False
        except requests.exceptions.RequestException as e:
            print('HTTP Request failed: ' + e.message)
            return False

    def get_status(self):
        # type: () -> DLRGClient.Status
        try:
            response = requests.get(
                url="https://services.dlrg.net/service.php",
                params={
                    "doc": "poi",
                    "strict": "1",  # strict means plain json
                    "id": self.stationId,
                    "typ": "WRS"  # means life guard station
                },
                headers={
                    "Referer": "https://www.dlrg.net/index.php?doc=auth",
                    "Cookie": "PHPSESSID=" + self.sessionId,
                },
                verify=not self.DEBUG,
            )
            return self.Status.from_json(json.loads(response.content))
        except requests.exceptions.RequestException as e:
            print('HTTP Request failed: ' + e.message)
            return self.Status(status=self.States.NOT_ON_DUTY)
