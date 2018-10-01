#!/usr/bin/env python3

# Copyright 2018 John Bailey
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

# Based on API information found at http://www.smartofthehome.com/2016/05/hive-rest-api-v6/

import requests
import json
import time

class HiveAPI:

    baseUrl = "https://api.prod.bgchprod.info:443/omnia"
    authUrl = baseUrl + "/auth/sessions"
    nodesUrl = baseUrl + "/nodes"
    channelsUrl = baseUrl + "/channels"

    headers = { "Content-Type": "application/vnd.alertme.zoo-6.6+json",
                "Accept": "application/vnd.alertme.zoo-6.6+json",
                "X-Omnia-Client": "Hive Web Dashboard" }

    def __init__(self,):
        self.channels = {}
        self.sessionId = ""
        self.nodes = None

    def connectExistingSession(self, sessionId):
        self.sessionId = sessionId
        self.loggedInHeaders = { "X-Omnia-Access-Token": self.sessionId } 
        self.allHeaders = {**self.headers, **self.loggedInHeaders}

    def connectNewSession(self,username,password):
        payload = { "sessions": [{
                        "username": username,
                        "password": password,
                        "caller": "WEB" }]
                  }
        r = requests.post(self.authUrl, headers=self.headers, data=json.dumps(payload))
        if r.status_code == requests.codes.ok:
            data = json.loads(r.text)
            self.connectExistingSession( data["sessions"][0]["id"] )
        else:
            r.raise_for_status()

    def clearAllCachedData(self):
        self.nodes = None
        self.channels = {}

    def getNodes(self):
        if self.nodes is None:
            r = requests.get(self.nodesUrl, headers=self.allHeaders)
            if r.status_code == requests.codes.ok:
                content = json.loads(r.text)
                self.nodes = content["nodes"]
            else:
                r.raise_for_status()

    def isHeatingEnabled(self):
        self.getNodes()
        for node in self.nodes:
            if "attributes" in node:
                if "stateHeatingRelay" in node["attributes"]:
                    if node["attributes"]["stateHeatingRelay"]["reportedValue"] == "ON":
                        return True
        return False

    def isHotWaterEnabled(self):
        self.getNodes()
        for node in self.nodes:
            if "attributes" in node:
                if "stateHotWaterRelay" in node["attributes"]:
                    if node["attributes"]["stateHotWaterRelay"]["reportedValue"] == "ON":
                        return True
        return False

    def getChannels(self):
        r = requests.get(self.channelsUrl, headers=self.allHeaders)
        if r.status_code == requests.codes.ok:
            content = json.loads(r.text)
            self.channels = {}
            for channel in content["channels"]:
                ch = channel["id"].split("@")
                if ch[0] not in self.channels:
                    self.channels[ch[0]] = set()
                self.channels[ch[0]].add(channel["id"]) 
        else:
            r.raise_for_status()
     
    def getTemperature(self, channel):
        epoch_time_before = str(int(time.time()-600)*1000)
        epoch_time_now = str(int(time.time()-1)*1000)
        url = self.channelsUrl + "/" + channel + "?start="+epoch_time_before+"&end="+epoch_time_now+"&rate=5&timeUnit=MINUTES&operation=AVG"
        r = requests.get(url, headers=self.allHeaders)
        if r.status_code == requests.codes.ok:
            data = json.loads(r.text)
            tempValues = data["channels"][0]["values"]
            return next(iter(tempValues.values()))
        else:
            r.raise_for_status()

    def getControllerState(self, channel):
        epoch_time_before = str(int(time.time()-600)*1000)
        epoch_time_now = str(int(time.time()-1)*1000)
        url = self.channelsUrl + "/" + channel + "?start="+epoch_time_before+"&end="+epoch_time_now+"&rate=5&timeUnit=MINUTES&operation=DATASET"
        r = requests.get(url, headers=self.allHeaders)
        if r.status_code == requests.codes.ok:
            data = json.loads(r.text)
            tempValues = data["channels"][0]["values"]
            return next(iter(tempValues.values()))
        else:
            r.raise_for_status()

    def getTemperatures(self):
        temps = []
        if len( self.channels ) == 0:
            self.getChannels()
        for channel in self.channels["temperature"]:
            temps.append( self.getTemperature( channel ) )
        return temps

    def getControllerStates(self):
        temps = []
        if len( self.channels ) == 0:
            self.getChannels()
        for channel in self.channels["controllerState"]:
            temps.append( self.getControllerState( channel ) )
        return temps
