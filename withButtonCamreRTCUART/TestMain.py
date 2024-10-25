import cv2
import tkinter as tk
from PIL import Image, ImageTk
import threading
import time
import RPi.GPIO as GPIO  # Import the GPIO library for button handling
import os  # For saving files to SD card

# Custom Modules
import rtc_handler_manual as rtc_handler  # Import the manual RTC handler
import uart_handler  # Import the UART handler

# Global variables to hold the frames and weight
frame1 = None
frame2 = None
weight = "Non"  # Initial weight value
lock = threading.Lock()  # To synchronize frame updates
capture_lock = threading.Lock()  # Lock for capture process

# Global screen dimensions
screen_width = 0
screen_height = 0

# Variables to hold the video capture objects
cap1 = None
cap2 = None

# GPIO Setup
BUTTON_PIN = 17  # GPIO pin number for the button
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Use pull-up resistor

# Debounce and press duration constants
DEBOUNCE_TIME = 150  # Minimum press time in milliseconds
PRESS_DURATION_THRESHOLD = 0.15  # 150 ms in seconds

# Button state
button_pressed_time = 0

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
                return cap  # Return the successfully opened camera
        except Exception as e:
            print(f"Error reconnecting to camera {camera_index}: {e}")
            time.sleep(1)  # Retry after 1 second
    return None

# Function to capture frames from the USB webcam in a separate thread
def capture_webcam():
    global frame1, cap1
    while True:
        if cap1 is None or not cap1.isOpened():
            cap1 = reconnect_camera(0)  # Camera index 0 for USB webcam
        if cap1 and cap1.isOpened():
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
            cap2 = reconnect_camera(2)  # Camera index 2 for the second USB camera
        if cap2 and cap2.isOpened():
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
        # Display Weight in the meal_label frame
        weight = uart_handler.weight  # Fetch the weight from uart_handler
        meal_label.config(text=f"\tMidday Meal\n\nTime: {rtc_handler.get_rtc_time()['time']}\n\nDate: {rtc_handler.get_rtc_time()['date']}\n\nFood Weight: {weight}")

        # Display Laptop Camera in the top-left box
        if frame1 is not None:
            frame1_resized = cv2.resize(frame1, (screen_width // 2 - 20, screen_height // 2 - 20))
            img1 = cv2.cvtColor(frame1_resized, cv2.COLOR_BGR2RGB)
            img1 = Image.fromarray(img1)
            imgtk1 = ImageTk.PhotoImage(image=img1)
            laptop_label.imgtk1 = imgtk1
            laptop_label.config(image=imgtk1)
        else:
            laptop_label.config(text="Camera 1 not available")  # Show a message if the camera is not available

        # Display USB Webcam in the bottom-left box
        if frame2 is not None:
            frame2_resized = cv2.resize(frame2, (screen_width // 2 - 20, screen_height // 2 - 20))
            img2 = cv2.cvtColor(frame2_resized, cv2.COLOR_BGR2RGB)
            img2 = Image.fromarray(img2)
            imgtk2 = ImageTk.PhotoImage(image=img2)
            webcam_label.imgtk2 = imgtk2
            webcam_label.config(image=imgtk2)
        else:
            webcam_label.config(text="Camera 2 not available")  # Show a message if the camera is not available

    # Schedule the next frame update
    root.after(50, update_display)  # Update every 50 ms for smoother display

# Function to capture images from both cameras and save to SD card
def capture_and_save_image():
    global frame1, frame2, weight

    with capture_lock:
        # Pause camera updates, UART, and RTC to reduce load
        root.after_cancel(update_display)

        # Show pop-up indicating saving process
        popup = tk.Toplevel(root)
        popup.title("Saving Image")
        popup.geometry("300x100")
        tk.Label(popup, text="Wait For Image Saving...", font=("Helvetica", 14)).pack(pady=20)

        # Capture the frames
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        device_id = "DeviceID"  # Replace with actual Device ID
        pic_number = "01"  # Update this accordingly
        filename = f"{device_id}_{timestamp}_{pic_number}.jpg"

        # Combine frames into one image
        if frame1 is not None and frame2 is not None:
            combined_image = cv2.vconcat([frame1, frame2])
            cv2.putText(combined_image, f"{timestamp} Weight: {weight}, {device_id}, {pic_number}",
                        (10, combined_image.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Save the combined image
            save_path = "/mnt/sdcard"
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            save_path = os.path.join("/mnt/sdcard", filename)  # Adjust the path to your SD card
            cv2.imwrite(save_path, combined_image)
            print(f"Image saved at {save_path}")

        # Destroy pop-up and resume operations
        popup.destroy()
        update_display()

# GPIO Button Press Handling with debouncing
def handle_button_press(channel):
    global button_pressed_time

    # Debounce check
    current_time = time.time()
    if current_time - button_pressed_time > PRESS_DURATION_THRESHOLD:
        button_pressed_time = current_time
        capture_thread = threading.Thread(target=capture_and_save_image)
        capture_thread.start()

# Set up GPIO event detection
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=handle_button_press, bouncetime=DEBOUNCE_TIME)
# Function to minimize the window when the Escape key is pressed

def minimize_window(event=None):

    root.attributes("-fullscreen", False)

    root.overrideredirect(False)

    root.iconify()  # Minimize the window

# Function to set up the GUI window for the Init Screen

def setup_init_screen():

    global root, init_status_label, screen_width, screen_height



    # Initialize the Tkinter window for the init screen

    root = tk.Tk()

    root.title("Initialization")



    # Bind the Escape key to minimize the window

    root.bind("<Escape>", minimize_window)



    # Get the screen width and height

    screen_width = root.winfo_screenwidth()

    screen_height = root.winfo_screenheight()



    # Set the window to full screen

    root.geometry(f"{screen_width}x{screen_height}+0+0")

    root.attributes("-fullscreen", True)



    # Load and display the logo

    try:

        logo = Image.open("middaymeallog.png")  # Use the file name directly if it's in the same folder

        logo = logo.resize((300, 300), Image.Resampling.LANCZOS)  # Resize logo to fit

        logo_img = ImageTk.PhotoImage(logo)

        logo_label = tk.Label(root, image=logo_img)

        logo_label.image = logo_img  # Keep a reference to prevent garbage collection

        logo_label.pack(pady=10)

    except Exception as e:

        print(f"Error loading logo: {e}")



    # Initialize a label to show status updates

    init_status_label = tk.Label(root, text="Initializing...", font=("Helvetica", 24), fg="blue", padx=20, pady=20)

    init_status_label.pack(expand=True, fill=tk.BOTH)

# Function to display status updates during initialization

def update_init_screen(status_message):

    init_status_label.config(text=status_message)

    root.update_idletasks()



# Function to perform initialization

def init_screen():

    # Display Welcome Message with Logo

    update_init_screen("Welcome to the Mid Day Meal Scheme!")

    time.sleep(2)  # Display welcome message for 3 seconds



    # Initialize and check modules one by one

    init_status = "Setting up modules...\n"

    all_success = True



    # Check RTC

    try:

        rtc_handler.get_rtc_time()

        init_status += "RTC: OK\n"

        update_init_screen(init_status)

    except Exception as e:

        init_status += f"RTC Error: {str(e)}\n"

        update_init_screen(init_status)

        all_success = False



    # Check UART

    try:

        uart_handler.setup_uart()

        init_status += "UART: OK\n"

        update_init_screen(init_status)

    except Exception as e:

        init_status += f"UART Error: {str(e)}\n"

        update_init_screen(init_status)

        all_success = False



    # Check Cameras

    global cap1, cap2

    cap1 = reconnect_camera(0)

    if cap1 and cap1.isOpened():

        init_status += "Camera 1: OK\n"

    else:

        init_status += "Camera 1: Error\n"

        all_success = False

    update_init_screen(init_status)



    cap2 = reconnect_camera(2)

    if cap2 and cap2.isOpened():

        init_status += "Camera 2: OK\n"

    else:

        init_status += "Camera 2: Error\n"

        all_success = False

    update_init_screen(init_status)



    # Display the final status for 5 seconds before moving on

    time.sleep(2)



    # If all modules are OK, proceed to the monitoring screen

    if all_success:

        setup_gui()  # Switch to the Monitoring Screen

        start_camera_threads()

        update_display()  # Start displaying the monitoring screen

    else:

        # If any error, keep displaying the Init Screen for user awareness

        init_status += "\nInitialization failed. Please check the setup."

        update_init_screen(init_status)



# Function to set up the GUI window for Monitoring Screen

def setup_gui():

    global screen_width, screen_height, weight_label, webcam_label, meal_label, laptop_label, notes_label



    # Clear the Init Screen

    for widget in root.winfo_children():

        widget.destroy()



    # Set the window to full screen

    root.geometry(f"{screen_width}x{screen_height}+0+0")

    root.attributes("-fullscreen", True)



    # Bind the Escape key to minimize the window

    root.bind("<Escape>", minimize_window)



    # Frame for the Laptop Camera (Top Left Box) - More Height and Width

    laptop_label = tk.Label(root, bd=5, relief="raised")

    laptop_label.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=10, pady=10)



    # Frame for the USB Webcam (Bottom Left Box)

    webcam_label = tk.Label(root, bd=5, relief="raised")

    webcam_label.grid(row=3, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)



    # Frame for Date, Time, and Food Weight (Right Side) - More Height

    meal_label = tk.Label(root, font=("Helvetica", 20), bg="white", fg="black", bd=5, relief="ridge", padx=10, pady=10, anchor="w", justify="left")

    meal_label.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=10, pady=10)



    # Frame for Notes (Right Side Below Date, Time, and Food Weight)

    notes_label = tk.Label(root, font=("Helvetica", 18), bg="white", fg="black", bd=5, relief="groove", padx=10, pady=10, anchor="w", justify="left", text="Notes Frame")

    notes_label.grid(row=3, column=1, rowspan=2, sticky="nsew", padx=10, pady=10)



    # Adjust the weights to give more space to specific rows and columns

    # Rows for Laptop and Meal should have more height

    root.grid_rowconfigure(0, weight=3)  # More height for the Laptop frame

    root.grid_rowconfigure(1, weight=3)  # More height for continuation if needed

    root.grid_rowconfigure(2, weight=3)  # More height for Meal frame

    root.grid_rowconfigure(3, weight=2)  # Less height for the Web Camera

    root.grid_rowconfigure(4, weight=1)  # Less height for Notes



    # Columns for Laptop and Web should have more width

    root.grid_columnconfigure(0, weight=3)  # More width for the Laptop and Web Camera frames

    root.grid_columnconfigure(1, weight=2)  # Less width for Date/Time and Notes



# Function to start camera threads

def start_camera_threads():

    # Start threads to capture frames from both cameras

    threading.Thread(target=capture_webcam, daemon=True).start()

    threading.Thread(target=capture_laptop_cam, daemon=True).start()



    # Start thread to read weight from UART

    threading.Thread(target=uart_handler.read_weight_from_uart, daemon=True).start()



# Function to initialize video capture for cameras

def setup_video_capture():

    global cap1, cap2

    cap1 = reconnect_camera(0)  # Start USB webcam (camera index 0)

    cap2 = reconnect_camera(2)  # Start second USB camera (camera index 2)



# Function to periodically attempt RTC sync with NTP server

def periodic_rtc_sync_with_ntp():

    while True:

        rtc_handler.sync_rtc_with_ntp()

        time.sleep(65)  # Retry every 10 minutes


# Main function to run the application
def main():
    global root

    # Setup the Init Screen GUI
    setup_init_screen()

    # Perform the initialization in a separate thread
    threading.Thread(target=init_screen, daemon=True).start()
    threading.Thread(target=periodic_rtc_sync_with_ntp, daemon=True).start()

    # Run the Tkinter main loop
    root.mainloop()

    # Release the video captures when the window is closed
    if cap1:
        cap1.release()
    if cap2:
        cap2.release()

    GPIO.cleanup()  # Clean up GPIO settings

    cv2.destroyAllWindows()

# Run the main function
if __name__ == "__main__":
    main()
