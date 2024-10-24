import cv2
import tkinter as tk
from PIL import Image, ImageTk
import threading
import time
import serial
import os
import datetime

# Global variables to hold the frames and UART data
frame1 = None
frame2 = None
lock = threading.Lock()  # To synchronize frame updates
ser = None  # For UART connection to the weighing scale
uart_error = False

# Variables to hold the video capture objects and reset state
cap1 = None
cap2 = None
device_id = "Device12345"
uart_data = "No data yet"  # Initialize UART data variable

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
            cap2 = reconnect_camera(2)  # Changed to camera index 2

        ret2, frame2_temp = cap2.read()
        if ret2:
            with lock:
                frame2 = frame2_temp
        else:
            cap2.release()
            cap2 = None  # Force reconnection if capturing fails

# Function to read weight from UART weighing scale
def read_weight():
    global ser, uart_error, uart_data
    weight = "0.0 kg"  # Default weight
    if ser and ser.is_open:
        try:
            ser.flushInput()  # Clear the input buffer
            time.sleep(0.1)  # Add small delay to allow data to be fully received
            weight_data = ser.readline().decode('utf-8').strip()
            if weight_data:
                uart_data = f"{weight_data} kg"
                weight = uart_data
                uart_error = False
                print(f"Weight data received: {weight}")  # Debug print
            else:
                print("No data received from UART")
        except Exception as e:
            uart_error = True
            print(f"Error reading from scale: {e}")
    return weight

# Function to display an error reset option
def reset_gui():
    reset_label = tk.Label(root, text="Error detected! Press reset to try again.", font=("Helvetica", 24), bg="red", fg="white")
    reset_label.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
    reset_button = tk.Button(root, text="Reset", font=("Helvetica", 20), command=reset_application)
    reset_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

# Function to update the display of both cameras and text
def update_display():
    global frame1, frame2, uart_error

    with lock:
        if uart_error or cap1 is None or cap2 is None:
            reset_gui()  # Show reset button if there's an error
        else:
            # Display Weight in Frame 1
            weight = read_weight()
            weight_label.config(text=f"Weight: {weight}")

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

# Function to save captured images with timestamp and device ID
def save_images():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if frame1 is not None:
        img1_filename = f"{device_id}_cam1_{timestamp}.jpg"
        cv2.imwrite(img1_filename, frame1)
        print(f"Image saved: {img1_filename}")
    if frame2 is not None:
        img2_filename = f"{device_id}_cam2_{timestamp}.jpg"
        cv2.imwrite(img2_filename, frame2)
        print(f"Image saved: {img2_filename}")

# Button callback to capture images when pressed
def button_callback(channel):
    print("Button Pressed, capturing images...")
    save_images()

# Full-screen toggle function
def toggle_fullscreen(event=None):
    root.attributes("-fullscreen", True)

# Exit full-screen mode
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
    cap2 = reconnect_camera(2)  # Changed to camera index 2

# Function to start camera threads
def start_camera_threads():
    # Start threads to capture frames from both cameras
    threading.Thread(target=capture_webcam, daemon=True).start()
    threading.Thread(target=capture_laptop_cam, daemon=True).start()

# Function to set up UART for the weighing scale
def setup_uart():
    global ser
    try:
        ser = serial.Serial('/dev/serial0', baudrate=115200, timeout=1)
        if ser.is_open:
            print("UART connected to weighing scale.")
    except Exception as e:
        global uart_error
        uart_error = True
        print(f"Error connecting to UART: {e}")

# Function to reset the application on error
def reset_application():
    global cap1, cap2, ser, uart_error
    uart_error = False
    if cap1:
        cap1.release()
    if cap2:
        cap2.release()
    ser = None
    setup_video_capture()
    setup_uart()
    start_camera_threads()

# Main function
def main():
    # Setup the GUI
    setup_gui()

    # Setup video capture for both cameras
    setup_video_capture()

    # Setup UART connection for weighing scale
    setup_uart()

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
