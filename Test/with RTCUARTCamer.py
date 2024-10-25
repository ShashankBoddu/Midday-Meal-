import cv2

import tkinter as tk

from PIL import Image, ImageTk

import threading

import time



#Custom Modules

import rtc_handler_manual as rtc_handler  # Import the manual RTC handler

import uart_handler  # Import the UART handler



# Global variables to hold the frames and weight

frame1 = None

frame2 = None

weight = "Non"  # Initial weight value

lock = threading.Lock()  # To synchronize frame updates



# Variables to hold the video capture objects

cap1 = None

cap2 = None



# Function to reconnect camera

def reconnect_camera(camera_index):

    cap = None

    while cap is None or not cap.isOpened():

        try:

            cap = cv2.VideoCapture(camera_index)

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Reduce resolution for performance

            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

            if cap.isOpened():

                print(f"Camera {camera_index} reconnected successfully.")

        except Exception as e:

            print(f"Error reconnecting to camera {camera_index}: {e}")

            time.sleep(1)  # Retry after 1 second

    return cap



# Function to capture frames from the USB webcam in a separate thread

def capture_webcam():

    global frame1, cap1

    while True:

        if cap1 is None or not cap1.isOpened():

            cap1 = reconnect_camera(0)  # Camera index 0 for USB webcam

        ret1, frame1_temp = cap1.read()

        if ret1:

            with lock:

                frame1 = frame1_temp

        else:

            cap1.release()

            cap1 = None  # Force reconnection if capturing fails

# Function to capture frames from the second USB camera in a separate thread

def capture_laptop_cam():

    global frame2, cap2

    while True:

        if cap2 is None or not cap2.isOpened():

            cap2 = reconnect_camera(2)  # Change camera index to 2 for the second USB camera

        ret2, frame2_temp = cap2.read()

        if ret2:

            with lock:

                frame2 = frame2_temp

        else:

            cap2.release()

            cap2 = None  # Force reconnection if capturing fails



# Function to update the display of both cameras and text

def update_display():

    global frame1, frame2, weight

    with lock:

        # Display Weight in Frame 1

        weight = "Non"

        weight = uart_handler.weight  # Fetch the weight from uart_handler

        weight_label.config(text=f"Weight: {weight}")  # Update the label with the weight



        # Display USB webcam in Frame 2

        if frame1 is not None:

            frame1_resized = cv2.resize(frame1, (screen_width // 2 - 20, screen_height // 2 - 20))

            img1 = cv2.cvtColor(frame1_resized, cv2.COLOR_BGR2RGB)

            img1 = Image.fromarray(img1)

            imgtk1 = ImageTk.PhotoImage(image=img1)

            webcam_label.imgtk1 = imgtk1

            webcam_label.config(image=imgtk1)



        # Always display current date and time from the RTC

        current_rtc = rtc_handler.get_rtc_time()

        current_time = current_rtc["time"]

        current_date = current_rtc["date"]

        meal_label.config(text=f"Midday Meal\nTime: {current_time}\nDate: {current_date}")



        # Display second USB camera in Frame 4

        if frame2 is not None:

            frame2_resized = cv2.resize(frame2, (screen_width // 2 - 20, screen_height // 2 - 20))

            img2 = cv2.cvtColor(frame2_resized, cv2.COLOR_BGR2RGB)

            img2 = Image.fromarray(img2)

            imgtk2 = ImageTk.PhotoImage(image=img2)

            laptop_label.imgtk2 = imgtk2

            laptop_label.config(image=imgtk2)



    # Schedule the next frame update

    root.after(50, update_display)  # Update every second (1000 ms)



# Function to exit full-screen mode

def end_fullscreen(event=None):

    root.attributes("-fullscreen", False)



# Function to set up the GUI window

def setup_gui():

    global root, screen_width, screen_height, weight_label, webcam_label, meal_label, laptop_label



    # Initialize the Tkinter window

    root = tk.Tk()

    root.title("Four Frames with Weight, Cameras, and Text")



    # Get the screen width and height

    screen_width = root.winfo_screenwidth()

    screen_height = root.winfo_screenheight()



    # Set the window to full screen

    root.attributes("-fullscreen", True)



    # Bind the Escape key to exit full screen

    root.bind("<Escape>", end_fullscreen)



    # Frame 1: Display Weight with border and styling

    weight_label = tk.Label(root, font=("Helvetica", 24), bg="white", fg="black", bd=5, relief="solid", padx=10, pady=10)

    weight_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)



    # Frame 2: Display USB Webcam with border and styling

    webcam_label = tk.Label(root, bd=5, relief="solid")

    webcam_label.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)



    # Frame 3: Display "Midday Meal" text with border and styling

    meal_label = tk.Label(root, font=("Helvetica", 24), bg="white", fg="black", bd=5, relief="solid", padx=10, pady=10)

    meal_label.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)



    # Frame 4: Display Laptop Camera with border and styling

    laptop_label = tk.Label(root, bd=5, relief="solid")

    laptop_label.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)



    # Make sure the grid expands properly when the window is resized

    root.grid_rowconfigure(0, weight=1)

    root.grid_rowconfigure(1, weight=1)

    root.grid_columnconfigure(0, weight=1)

    root.grid_columnconfigure(1, weight=1)



# Function to initialize video capture for cameras

def setup_video_capture():

    global cap1, cap2

    cap1 = reconnect_camera(0)  # Start USB webcam (camera index 0)

    cap2 = reconnect_camera(2)  # Start second USB camera (camera index 2)



# Function to start camera threads

def start_camera_threads():

    # Start threads to capture frames from both cameras

    threading.Thread(target=capture_webcam, daemon=True).start()

    threading.Thread(target=capture_laptop_cam, daemon=True).start()



    # Start thread to read weight from UART

    threading.Thread(target=uart_handler.read_weight_from_uart, daemon=True).start()

# Function to periodically attempt RTC sync with NTP server

def periodic_rtc_sync_with_ntp():

    while True:

        rtc_handler.sync_rtc_with_ntp()

        time.sleep(600)  # Retry every 10 minutes



# Main function

def main():

    # Setup the GUI

    setup_gui()



    # Setup video capture for both cameras

    setup_video_capture()



    # Setup UART connection for weighing scale

    uart_handler.setup_uart()



    # Start the threads for continuous camera capture

    start_camera_threads()



    # Start the video updates in the Tkinter window

    update_display()



    # Periodically try to sync RTC with NTP server in a separate thread

    threading.Thread(target=periodic_rtc_sync_with_ntp, daemon=True).start()



    # Run the Tkinter main loop

    root.mainloop()



    # Release the video captures when the window is closed

    if cap1:

        cap1.release()

    if cap2:

        cap2.release()



    cv2.destroyAllWindows()



# Run the main function

if __name__ == "__main__":

    main()

import serial
import time
import re

# Global variables
ser = None
weight = "0.0"  # Initialize the weight as a global variable

# Function to set up UART
def setup_uart():
    global ser
    try:
        ser = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=2)
        if ser.is_open:
            print("UART connected to weighing scale.")
    except Exception as e:
        print(f"Error connecting to UART: {e}")

# Function to read weight from the UART-connected weighing scale
def read_weight_from_uart():
    global ser, weight  # Declare weight as global so it can be accessed and modified
    buffer = ""
    ignore_bytes = 20  # Number of bytes to ignore at the beginning

    while True:
        try:
            # Read raw data from UART in chunks (100 bytes)
            chunk = ser.read(100).decode('utf-8', errors='ignore')  # Ignore decoding errors for incomplete chunks
            if chunk:
                buffer = chunk  # Append new data to the buffer
                # Ignore the first 20 bytes only once
                if len(buffer) > ignore_bytes:
                    buffer = buffer[ignore_bytes:]
                    ignore_bytes = 0  # Reset, as we've ignored the first 20 bytes
                    #print(f"Buffer After Ignoring First 20 Bytes: {buffer}")

                # Regular expression to match the first valid weight format (number + unit)
                # and extract until the next occurrence of a unit.
                match = re.search(r'([ \t]*\d+\.\d+[a-zA-Z]+)[^a-zA-Z]*', buffer)

                if match:
                    # Extract the matched weight
                    weight = match.group(1).strip()
                    #print(f"Extracted Weight: {weight}")

                    # Remove the processed part from the buffer
                    buffer = buffer[match.end():].strip()
                    #print(f"Updated Buffer After Extraction: {buffer}")

        except Exception as e:
            print(f"Error reading from UART: {e}")

        time.sleep(1)  # Poll every second

import time

import smbus2

import ntplib  # NTP client for time sync

from datetime import datetime, timedelta



# I2C address for PCF8523

PCF8523_ADDRESS = 0x68



# Register addresses for PCF8523

SECONDS_REGISTER = 0x03

MINUTES_REGISTER = 0x04

HOURS_REGISTER = 0x05

DAYS_REGISTER = 0x06

MONTHS_REGISTER = 0x08

YEARS_REGISTER = 0x09



# Initialize I2C bus

bus = smbus2.SMBus(1)  # Use I2C bus 1 (common for Raspberry Pi)



# Function to convert BCD to decimal

def bcd_to_dec(bcd):

    return (bcd // 16) * 10 + (bcd % 16)



# Function to convert decimal to BCD

def dec_to_bcd(dec):

    return (dec // 10) * 16 + (dec % 10)



# Function to read the current date and time from the PCF8523 RTC

def get_rtc_time():

    seconds = bcd_to_dec(bus.read_byte_data(PCF8523_ADDRESS, SECONDS_REGISTER) & 0x7F)

    minutes = bcd_to_dec(bus.read_byte_data(PCF8523_ADDRESS, MINUTES_REGISTER) & 0x7F)

    hours = bcd_to_dec(bus.read_byte_data(PCF8523_ADDRESS, HOURS_REGISTER) & 0x3F)

    day = bcd_to_dec(bus.read_byte_data(PCF8523_ADDRESS, DAYS_REGISTER) & 0x3F)

    month = bcd_to_dec(bus.read_byte_data(PCF8523_ADDRESS, MONTHS_REGISTER) & 0x1F)

    year = 2000 + bcd_to_dec(bus.read_byte_data(PCF8523_ADDRESS, YEARS_REGISTER))  # PCF8523 returns years since 2000

    

    return {

        "time": f"{hours:02}:{minutes:02}",

        "date": f"{day:02}/{month:02}/{year % 100:02}"

    }



# Function to set the time and date on the PCF8523 RTC

def set_rtc_time(hour, minute, second, day, month, year):

    bus.write_byte_data(PCF8523_ADDRESS, SECONDS_REGISTER, dec_to_bcd(second))

    bus.write_byte_data(PCF8523_ADDRESS, MINUTES_REGISTER, dec_to_bcd(minute))

    bus.write_byte_data(PCF8523_ADDRESS, HOURS_REGISTER, dec_to_bcd(hour))

    bus.write_byte_data(PCF8523_ADDRESS, DAYS_REGISTER, dec_to_bcd(day))

    bus.write_byte_data(PCF8523_ADDRESS, MONTHS_REGISTER, dec_to_bcd(month))

    bus.write_byte_data(PCF8523_ADDRESS, YEARS_REGISTER, dec_to_bcd(year - 2000))  # Store year since 2000



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

    ntp_time = get_ntp_time()



    if ntp_time:

        current_rtc = get_rtc_time()



        # Safely unpack the time components with a fallback for missing seconds

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



        # Update RTC if needed

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
