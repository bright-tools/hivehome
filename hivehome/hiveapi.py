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

import requests
import json
import time

class HiveAPI:

    baseUrl = "https://api.prod.bgchprod.info:443/omnia"
    authUrl = baseUrl + "/auth/sessions"
    nodesUrl = baseUrl + "/nodes"
    channelsUrl = baseUrl + "/channels"

    headers = { "Content-Type": "application/vnd.alertme.zoo-6.1+json",
                "Accept": "application/vnd.alertme.zoo-6.1+json",
                "X-Omnia-Client": "Hive Web Dashboard" }

    def __init__(self,):
        self.channels = {}
        self.sessionId = ""

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
        epoch_time_now = str(int(time.time())*1000)
        url = self.channelsUrl + "/" + channel + "?start="+epoch_time_before+"&end="+epoch_time_now+"&rate=5&timeUnit=MINUTES&operation=AVG"
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