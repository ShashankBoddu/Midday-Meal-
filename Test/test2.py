import cv2
import tkinter as tk
from PIL import Image, ImageTk
import threading

# Global variables to hold the frames
frame1 = None
frame2 = None
lock = threading.Lock()  # To synchronize frame updates

# Function to capture frames from the USB webcam in a separate thread
def capture_webcam():
    global frame1
    while True:
        ret1, frame1_temp = cap1.read()
        if ret1:
            with lock:
                frame1 = frame1_temp

# Function to capture frames from the laptop camera in a separate thread
def capture_laptop_cam():
    global frame2
    while True:
        ret2, frame2_temp = cap2.read()
        if ret2:
            with lock:
                frame2 = frame2_temp

# Function to update the display of both cameras
def update_display():
    global frame1, frame2

    with lock:
        if frame1 is not None:
            # Resize and display the webcam frame
            frame1_resized = cv2.resize(frame1, (screen_width // 2, screen_height))
            cv2.putText(frame1_resized, "Weight: 0.0 kg", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
            img1 = cv2.cvtColor(frame1_resized, cv2.COLOR_BGR2RGB)
            img1 = Image.fromarray(img1)
            imgtk1 = ImageTk.PhotoImage(image=img1)
            webcam_label.imgtk1 = imgtk1
            webcam_label.config(image=imgtk1)

        if frame2 is not None:
            # Resize and display the laptop camera frame
            frame2_resized = cv2.resize(frame2, (screen_width // 2, screen_height))
            img2 = cv2.cvtColor(frame2_resized, cv2.COLOR_BGR2RGB)
            img2 = Image.fromarray(img2)
            imgtk2 = ImageTk.PhotoImage(image=img2)
            laptop_label.imgtk2 = imgtk2
            laptop_label.config(image=imgtk2)

    # Schedule the next frame update
    root.after(10, update_display)

# Full-screen toggle function
def toggle_fullscreen(event=None):
    root.attributes("-fullscreen", True)

# Exit full-screen mode
def end_fullscreen(event=None):
    root.attributes("-fullscreen", False)

# Initialize the Tkinter window
root = tk.Tk()
root.title("Two Cameras with Weight Display")

# Get the screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Set the window to full screen
root.attributes("-fullscreen", True)

# Bind the Escape key to exit full screen
root.bind("<Escape>", end_fullscreen)

# Create labels for the webcam and laptop camera
webcam_label = tk.Label(root)
webcam_label.grid(row=0, column=0)

laptop_label = tk.Label(root)
laptop_label.grid(row=0, column=1)

# Open the USB webcam (camera index 0 for most USB webcams)
cap1 = cv2.VideoCapture(0)  # Change to the correct index if needed

# Open the laptop's built-in camera (camera index 1)
cap2 = cv2.VideoCapture(1)

# Set video capture dimensions (optional, depends on camera's native resolution)
cap1.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap1.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap2.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Start threads to capture frames from both cameras
threading.Thread(target=capture_webcam, daemon=True).start()
threading.Thread(target=capture_laptop_cam, daemon=True).start()

# Start the video updates in the Tkinter window
update_display()

# Run the Tkinter main loop
root.mainloop()

# Release the video captures when the window is closed
cap1.release()
cap2.release()
cv2.destroyAllWindows()
