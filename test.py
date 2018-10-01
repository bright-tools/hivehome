#!/usr/bin/env python3

# Example to retrieve the current temperature from the first Hive Home connected
#  temperature sensor & store the result in a database
#
# To use:
# 1. Create a file called `hive_credentials.json`, with the fields "username" and "password" - these should be the username and password for your Hive account
# 1. Create a file called `db_credentials.json`, with the fields "username", "password" and "database" - these should correspond to the username & password and name of the database to connect to
# 1. Create an appropriately named database and create a table with something like the following:
# ```
# CREATE TABLE `temperature` (
#  `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
#  `hive_temp` float NOT NULL,
#  `central_heating` timyint(1) NOT NULL,
#  `water_heating` timyint(1) NOT NULL,
# )
# ```

# TODO: Don't bomb out the second a 404 is encountered

import hivehome.hiveapi
import json
import mysql.connector

def getHiveStatus():
    with open('hive_credentials.json') as f:
        credentials = json.load(f)
    hive = hivehome.hiveapi.HiveAPI()
    hive.connectNewSession(credentials["username"], credentials["password"])
    temp = hive.getTemperatures()[0]
    ht = hive.isHeatingEnabled()
    hw = hive.isHotWaterEnabled()
    return [ temp, ht, hw ]

def storeHiveStatus(statusVal):
    with open('db_credentials.json') as f:
        credentials = json.load(f)
    mydb = mysql.connector.connect(
      host="localhost",
      user=credentials["username"],
      passwd=credentials["password"],
      database=credentials["database"],
      port=3307
    )
    mycursor = mydb.cursor()
    sql = "INSERT INTO temperature (hive_temp,central_heating,water_heating) VALUES ({}, {}, {})".format(statusVal[0],int(statusVal[1]),int(statusVal[2]))
    mycursor.execute(sql)
    mydb.commit()

def main():
    storeHiveStatus(getHiveStatus())

if __name__ == "__main__":
    main()

