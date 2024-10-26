#rtc_handler_manual.py
import time
import smbus2
import ntplib  # NTP client for time sync
from datetime import datetime, timedelta
import threading
# I2C address for PCF8523
PCF8523_ADDRESS = 0x68

# Register addresses for PCF8523 (Using the previous working version's addresses)
SECONDS_REGISTER = 0x03
MINUTES_REGISTER = 0x04
HOURS_REGISTER = 0x05
DAYS_REGISTER = 0x06
MONTHS_REGISTER = 0x08
YEARS_REGISTER = 0x09
# Initialize I2C bus
bus = smbus2.SMBus(1)  # Use I2C bus 1 (common for Raspberry Pi)
# Event to manage pause/resume
pause_event = threading.Event()  
# Function to convert BCD to decimal
def bcd_to_dec(bcd):
    return (bcd // 16) * 10 + (bcd % 16)

# Function to convert decimal to BCD
def dec_to_bcd(dec):
    return (dec // 10) * 16 + (dec % 10)

# Function to read the current date and time from the PCF8523 RTC
def get_rtc_time():
    try:
        seconds = bcd_to_dec(bus.read_byte_data(PCF8523_ADDRESS, SECONDS_REGISTER) & 0x7F)
        minutes = bcd_to_dec(bus.read_byte_data(PCF8523_ADDRESS, MINUTES_REGISTER) & 0x7F)
        hours = bcd_to_dec(bus.read_byte_data(PCF8523_ADDRESS, HOURS_REGISTER) & 0x3F)
        day = bcd_to_dec(bus.read_byte_data(PCF8523_ADDRESS, DAYS_REGISTER) & 0x3F)
        month = bcd_to_dec(bus.read_byte_data(PCF8523_ADDRESS, MONTHS_REGISTER) & 0x1F)
        year = 2000 + bcd_to_dec(bus.read_byte_data(PCF8523_ADDRESS, YEARS_REGISTER))  # PCF8523 returns years since 2000

        rtc_time = {
            "time": f"{hours:02}:{minutes:02}:{seconds:02}",
            "date": f"{day:02}/{month:02}/{year % 100:02}"
        }
        return rtc_time

    except OSError as e:
        print(f"RTC Communication Error: {e}")
        # Fallback to a default time or handle the error as necessary
        return {
            "time": "00:00:00",
            "date": "01/01/2000"
        }

# Function to set the time and date on the PCF8523 RTC
def set_rtc_time(hour, minute, second, day, month, year):
    try:
        bus.write_byte_data(PCF8523_ADDRESS, SECONDS_REGISTER, dec_to_bcd(second))
        bus.write_byte_data(PCF8523_ADDRESS, MINUTES_REGISTER, dec_to_bcd(minute))
        bus.write_byte_data(PCF8523_ADDRESS, HOURS_REGISTER, dec_to_bcd(hour))
        bus.write_byte_data(PCF8523_ADDRESS, DAYS_REGISTER, dec_to_bcd(day))
        bus.write_byte_data(PCF8523_ADDRESS, MONTHS_REGISTER, dec_to_bcd(month))
        bus.write_byte_data(PCF8523_ADDRESS, YEARS_REGISTER, dec_to_bcd(year - 2000))  # Store year since 2000
    except OSError as e:
        print(f"Error setting RTC time: {e}")

# Function to get the server time using NTP, adjusted for IST (UTC +5:30)
def get_ntp_time(ntp_server='pool.ntp.org'):
    try:
        client = ntplib.NTPClient()
        response = client.request(ntp_server, version=3)
        # Apply IST offset directly (UTC + 5:30)
        ntp_time = datetime.utcfromtimestamp(response.tx_time) + timedelta(hours=5, minutes=30)
        return ntp_time
    except Exception as e:
        print(f"Failed to fetch NTP time: {e}")
        return None

# Function to sync RTC with NTP server time (Adjusted for IST)
def sync_rtc_with_ntp():
    while True:
        pause_event.wait()  # Wait here if operations are paused
        ntp_time = get_ntp_time()

        if ntp_time:
            current_rtc = get_rtc_time()

            rtc_time_parts = current_rtc['time'].split(":")
            if len(rtc_time_parts) == 3:
                rtc_hour, rtc_minute, rtc_second = map(int, rtc_time_parts)
            elif len(rtc_time_parts) == 2:
                rtc_hour, rtc_minute = map(int, rtc_time_parts)
                rtc_second = 0  # Default to 0 seconds if not provided
            else:
                print("Invalid RTC time format.")
                return

            rtc_day, rtc_month, rtc_year = map(int, current_rtc['date'].split("/"))

            if (rtc_hour != ntp_time.hour or
                rtc_minute != ntp_time.minute or
                rtc_second != ntp_time.second or
                rtc_day != ntp_time.day or
                rtc_month != ntp_time.month or
                rtc_year != ntp_time.year % 100):

                print(f"Updating RTC time from NTP server: {ntp_time}")
                set_rtc_time(ntp_time.hour, ntp_time.minute, ntp_time.second,
                             ntp_time.day, ntp_time.month, ntp_time.year)
            else:
                print("RTC time is already synchronized with NTP server.")
        else:
            print("NTP time fetch failed. Continuing with RTC time.")
        
        time.sleep(600)  # Retry every 10 minutes