#uart_handler.py
import serial
import time
import re

# Global variables
ser = None
weight = "Non"  # Initialize the weight as a global variable
SerialFailCount = 0
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
    global ser, weight,SerialFailCount  # Declare weight as global so it can be accessed and modified
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
                    SerialFailCount = 0
                    # Extract the matched weight
                    weight = match.group(1).strip()
                    #print(f"Extracted Weight: {weight}")

                    # Remove the processed part from the buffer
                    buffer = buffer[match.end():].strip()
                    #print(f"Updated Buffer After Extraction: {buffer}")
                else:
                    SerialFailCount += 1
            else:
                SerialFailCount += 1
            if SerialFailCount > 10:
                weight = "Non" 
                SerialFailCount = 0 
        except Exception as e:
            print(f"Error reading from UART: {e}")

        time.sleep(1)  # Poll every second
