import cv2

import tkinter as tk

from PIL import Image, ImageTk

import threading

import time



# Custom Modules

import rtc_handler_manual as rtc_handler  # Import the manual RTC handler

import uart_handler  # Import the UART handler





# Global variables to hold the frames and weight

frame1 = None

frame2 = None

weight = "Non"  # Initial weight value

lock = threading.Lock()  # To synchronize frame updates

# Global screen dimensions

screen_width = 0

screen_height = 0

allow_escape_fullscreen = True  # Set this to True if you want to allow the Escape key to exit fu

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

        # Display Weight in Frame 1

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

        else:

            webcam_label.config(text="Camera 1 not available")  # Show a message if the camera is not available



        # Always display current date and time from the RTC

        try:

            current_rtc = rtc_handler.get_rtc_time()

            current_time = current_rtc["time"]

            current_date = current_rtc["date"]

            meal_label.config(text=f"Midday Meal\nTime: {current_time}\nDate: {current_date}")

        except Exception as e:

            meal_label.config(text=f"RTC Error: {str(e)}")



        # Display second USB camera in Frame 4

        if frame2 is not None:

            frame2_resized = cv2.resize(frame2, (screen_width // 2 - 20, screen_height // 2 - 20))

            img2 = cv2.cvtColor(frame2_resized, cv2.COLOR_BGR2RGB)

            img2 = Image.fromarray(img2)

            imgtk2 = ImageTk.PhotoImage(image=img2)

            laptop_label.imgtk2 = imgtk2

            laptop_label.config(image=imgtk2)

        else:

            laptop_label.config(text="Camera 2 not available")  # Show a message if the camera is not available



    # Schedule the next frame update

    root.after(50, update_display)  # Update every 50 ms for smoother display

# Function to toggle full-screen mode

def toggle_fullscreen(enable_fullscreen):

    if enable_fullscreen:

        root.attributes("-fullscreen", True)

        root.overrideredirect(True)  # Make the window borderless/full-screen

    else:

        root.attributes("-fullscreen", False)

        root.overrideredirect(False)  # Restore window decorations

# Function to minimize the window when the Escape key is pressed

def minimize_window(event=None):

    global allow_escape_fullscreen

    if allow_escape_fullscreen:

        root.attributes("-fullscreen", False)

        root.overrideredirect(False)

        root.iconify()  # Minimize the window

# Function to enable/disable Escape key for minimizing the window

def set_escape_fullscreen(enable):

    global allow_escape_fullscreen

    allow_escape_fullscreen = enable

    if allow_escape_fullscreen:

        root.bind("<Escape>", minimize_window)  # Bind Escape to minimize the window

    else:

        root.unbind("<Escape>")  # Unbind Escape to prevent minimizing the window

# Function to set up the GUI window for the Init Screen

def setup_init_screen():

    global root, init_status_label, screen_width, screen_height



    # Initialize the Tkinter window for the init screen

    root = tk.Tk()

    root.title("Initialization")



    # Bind the 'q' key to exit the application

    root.bind('q', lambda event: exit_application())



    # Get the screen width and height

    screen_width = root.winfo_screenwidth()

    screen_height = root.winfo_screenheight()



    # Set the window to full screen

    root.geometry(f"{screen_width}x{screen_height}+0+0")

    toggle_fullscreen(True)  # Enable full screen mode

    set_escape_fullscreen(allow_escape_fullscreen)  # Control Escape key behavior



    # Load and display the logo

    try:

        logo = Image.open("middaymeallog.png")  # Use the file name directly if it's in the same folder

        logo = logo.resize((200, 200), Image.Resampling.LANCZOS)  # Resize logo to fit

        logo_img = ImageTk.PhotoImage(logo)

        logo_label = tk.Label(root, image=logo_img)

        logo_label.image = logo_img  # Keep a reference to prevent garbage collection

        logo_label.pack(pady=10)

    except Exception as e:

        print(f"Error loading logo: {e}")



    # Initialize a label to show status updates

    init_status_label = tk.Label(root, text="Initializing...", font=("Helvetica", 24), fg="blue", padx=20, pady=20)

    init_status_label.pack(expand=True, fill=tk.BOTH)

# Function to display status updates during initializatio
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

# Function to set up the GUI window for the Init Screen

def setup_init_screen():

    global root, init_status_label, screen_width, screen_height



    # Initialize the Tkinter window for the init screen

    root = tk.Tk()

    root.title("Initialization")



    # Get the screen width and height

    screen_width = root.winfo_screenwidth()

    screen_height = root.winfo_screenheight()



    # Set the window to full screen

    root.geometry(f"{screen_width}x{screen_height}+0+0")

    toggle_fullscreen(True)  # Enable full screen mode

    set_escape_fullscreen(allow_escape_fullscreen)  # Control Escape key behavior



    # Load and display the logo

    try:

        logo = Image.open("middaymeallog.png")  # Use the file name directly if it's in the same folder

        logo = logo.resize((400, 400), Image.Resampling.LANCZOS)  # Resize logo to fit

        logo_img = ImageTk.PhotoImage(logo)

        logo_label = tk.Label(root, image=logo_img)

        logo_label.image = logo_img  # Keep a reference to prevent garbage collection

        logo_label.pack(pady=10)

    except Exception as e:

        print(f"Error loading logo: {e}")



    # Initialize a label to show status updates

    init_status_label = tk.Label(root, text="Initializing...", font=("Helvetica", 24), fg="blue", padx=20, pady=20)

    init_status_label.pack(expand=True, fill=tk.BOTH)

# Function to set up the GUI window for Monitoring Screen
def setup_gui():

    global screen_width, screen_height, weight_label, webcam_label, meal_label, laptop_label



    # Clear the Init Screen

    for widget in root.winfo_children():

        widget.destroy()



    # Set the window to full screen

    root.geometry(f"{screen_width}x{screen_height}+0+0")

    toggle_fullscreen(True)  # Enable full screen mode

    set_escape_fullscreen(allow_escape_fullscreen)  # Control Escape key behavior



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

    root.grid_columnconfigure(1, weight=1) Function to start camera threads

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

        time.sleep(600)  # Retry every 10 minutes



# Main function

def main():

    global root



    # Setup the Init Screen GUI

    setup_init_screen()



    # Perform the initialization in a separate thread

    threading.Thread(target=init_screen, daemon=True).start()



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

