# rtc_handler.py

import time
import board
import busio
import adafruit_pcf8523
import requests
from datetime import datetime

# Initialize I2C and the RTC
i2c = busio.I2C(board.SCL, board.SDA)
rtc = adafruit_pcf8523.PCF8523(i2c)

# Function to get the current time from the RTC
def get_rtc_time():
    t = rtc.datetime
    return f"{t.tm_hour:02}:{t.tm_min:02}:{t.tm_sec:02}"

# Function to set the RTC time
def set_rtc_time(hour, minute, second):
    rtc.datetime = time.struct_time((2024, 1, 1, hour, minute, second, 0, -1, -1))

# Function to get the server time
def get_server_time():
    try:
        response = requests.get("http://worldtimeapi.org/api/timezone/Etc/UTC")
        server_time_str = response.json()["datetime"]
        server_time = datetime.fromisoformat(server_time_str[:-1])
        return server_time
    except Exception as e:
        print(f"Failed to fetch server time: {e}")
        return None

# Function to sync RTC with server time
def sync_rtc_with_server():
    server_time = get_server_time()
    
    if server_time:
        rtc_time = rtc.datetime
        if (rtc_time.tm_hour != server_time.hour or
            rtc_time.tm_min != server_time.minute or
            rtc_time.tm_sec != server_time.second):
            print(f"Updating RTC time from server: {server_time}")
            set_rtc_time(server_time.hour, server_time.minute, server_time.second)
        else:
            print("RTC time is already synchronized.")
