import cv2
import tkinter as tk
from PIL import Image, ImageTk
import threading
import time
import serial
import re
import rtc_handler  # Import the RTC handler module

# Global variables to hold the frames and weight
frame1 = None
frame2 = None
weight = "0.0"  # Initial weight value
lock = threading.Lock()  # To synchronize frame updates

# Variables to hold the video capture objects
cap1 = None
cap2 = None

# Setup UART (modify this according to your UART parameters)
def setup_uart():
    global ser
    try:
        ser = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=2)
        if ser.is_open:
            print("UART connected to weighing scale.")
    except Exception as e:
        global uart_error
        uart_error = True
        print(f"Error connecting to UART: {e}")

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

# Function to read weight from the UART-connected weighing scale
def read_weight_from_uart():
    global weight
    buffer = ""
    ignore_bytes = 20  # Number of bytes to ignore at the beginning

    while True:
        try:
            # Read raw data from UART in chunks (100 bytes)
            chunk = ser.read(100).decode('utf-8', errors='ignore')  # Ignore decoding errors for incomplete chunks
            if chunk:
                buffer = chunk  # Append new data to the buffer
                print(f"Raw Data Chunk: {chunk}")
                print(f"Data Buffer: {buffer}")
                
                # Ignore the first 20 bytes only once
                if len(buffer) > ignore_bytes:
                    buffer = buffer[ignore_bytes:]
                    ignore_bytes = 0  # Reset, as we've ignored the first 20 bytes
                    print(f"Buffer After Ignoring First 20 Bytes: {buffer}")
                
                # Regular expression to match the first valid weight format (number + unit)
                match = re.search(r'\d+\.\d+[a-zA-Z]+', buffer)
                
                if match:
                    # Extract the matched weight
                    weight = match.group().strip()
                    print(f"Extracted Weight: {weight}")
                    
                    # Remove the processed part from the buffer
                    buffer = buffer[match.end():].strip()
                    print(f"Updated Buffer After Extraction: {buffer}")
                
        except Exception as e:
            print(f"Error reading from UART: {e}")
        
        time.sleep(1)  # Poll every second

# Function to update the display of both cameras and text
def update_display():
    global frame1, frame2, weight

    with lock:
        # Display Weight in Frame 1
        weight_label.config(text=f"Weight: {weight}")  # Update the label with the weight

        # Display USB webcam in Frame 2
        if frame1 is not None:
            frame1_resized = cv2.resize(frame1, (screen_width // 2 - 20, screen_height // 2 - 20))
            img1 = cv2.cvtColor(frame1_resized, cv2.COLOR_BGR2RGB)
            img1 = Image.fromarray(img1)
            imgtk1 = ImageTk.PhotoImage(image=img1)
            webcam_label.imgtk1 = imgtk1
            webcam_label.config(image=imgtk1)

        # Display text "Midday Meal" in Frame 3
        meal_label.config(text="Midday Meal")

        # Display second USB camera in Frame 4
        if frame2 is not None:
            frame2_resized = cv2.resize(frame2, (screen_width // 2 - 20, screen_height // 2 - 20))
            img2 = cv2.cvtColor(frame2_resized, cv2.COLOR_BGR2RGB)
            img2 = Image.fromarray(img2)
            imgtk2 = ImageTk.PhotoImage(image=img2)
            laptop_label.imgtk2 = imgtk2
            laptop_label.config(image=imgtk2)

    # Schedule the next frame update
    root.after(10, update_display)

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
    threading.Thread(target=read_weight_from_uart, daemon=True).start()

# Main function
def main():
    # Setup the GUI
    setup_gui()

    # Setup video capture for both cameras
    setup_video_capture()

    # Setup UART connection for weighing scale
    setup_uart()

    # Sync RTC time with server periodically
    threading.Thread(target=rtc_handler.sync_rtc_with_server, daemon=True).start()

    # Start the threads for continuous camera capture
    start_camera_threads()

    # Start the video updates in the Tkinter window
    update_display()

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
