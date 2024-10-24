import cv2
import tkinter as tk
from PIL import Image, ImageTk
import threading
import time
import numpy as np

# Global variables to hold the frames
frame1 = None
frame2 = None
lock = threading.Lock()  # To synchronize frame updates
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')  # Eye detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')  # Face detection

# Load OpenCV's DNN-based face detection model
net = cv2.dnn.readNetFromCaffe(
    "E:/projects/pythonCodes/Midday meals/deploy.prototxt",  # Full path to prototxt file
    "E:/projects/pythonCodes/Midday meals/res10_300x300_ssd_iter_140000.caffemodel"  # Full path to caffemodel file
)

# Variables to hold the video capture objects
cap1 = None
cap2 = None

# Global variables to keep track of eye blink state
blink_counter = 0
blink_threshold = 3  # Number of consecutive frames where eyes must be closed to register as a blink
blink_detected = False

def reconnect_camera(camera_index):
    """Try to reconnect to the specified camera index."""
    cap = None
    while cap is None or not cap.isOpened():
        try:
            cap = cv2.VideoCapture(camera_index)
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

# Function to capture frames from the laptop camera in a separate thread
def capture_laptop_cam():
    global frame2, cap2
    while True:
        if cap2 is None or not cap2.isOpened():
            cap2 = reconnect_camera(1)  # Camera index 1 for laptop camera

        ret2, frame2_temp = cap2.read()
        if ret2:
            with lock:
                frame2 = frame2_temp
        else:
            cap2.release()
            cap2 = None  # Force reconnection if capturing fails

# Function to perform fast face detection using OpenCV's DNN model
def detect_face_dnn(frame):
    blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()

    faces = []
    (h, w) = frame.shape[:2]

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:  # Confidence threshold
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (x, y, x1, y1) = box.astype("int")
            faces.append((x, y, x1 - x, y1 - y))

    return faces

# Function to detect eyes within a face and determine if the person is blinking
def detect_blinks(frame, faces):
    global blink_counter, blink_detected
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    for (x, y, w, h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = frame[y:y+h, x:x+w]
        
        eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=10, minSize=(30, 30))
        
        if len(eyes) == 0:
            blink_counter += 1
        else:
            blink_counter = 0

        if blink_counter >= blink_threshold:
            blink_detected = True
        else:
            blink_detected = False
        
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)

    return blink_detected

# Function to update the display of both cameras and text
def update_display():
    global frame1, frame2

    with lock:
        # Display Weight in Frame 1
        weight_label.config(text="Weight: 0.0 kg")

        # Display USB webcam in Frame 2
        if frame1 is not None:
            frame1_resized = cv2.resize(frame1, (screen_width // 2 - 20, screen_height // 2 - 20))

            # Detect face using DNN model
            faces = detect_face_dnn(frame1_resized)

            # Detect blinks for live face detection
            if detect_blinks(frame1_resized, faces):
                cv2.putText(frame1_resized, "Live Face Detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(frame1_resized, "Blink to Verify", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame1_resized, (x, y), (x + w, y + h), (255, 0, 0), 2)

            img1 = cv2.cvtColor(frame1_resized, cv2.COLOR_BGR2RGB)
            img1 = Image.fromarray(img1)
            imgtk1 = ImageTk.PhotoImage(image=img1)
            webcam_label.imgtk1 = imgtk1
            webcam_label.config(image=imgtk1)

        # Display text "Midday Meal" in Frame 3
        meal_label.config(text="Midday Meal")

        # Display laptop camera in Frame 4
        if frame2 is not None:
            frame2_resized = cv2.resize(frame2, (screen_width // 2 - 20, screen_height // 2 - 20))
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
    cap2 = reconnect_camera(1)  # Start laptop camera (camera index 1)

# Function to start camera threads
def start_camera_threads():
    # Start threads to capture frames from both cameras
    threading.Thread(target=capture_webcam, daemon=True).start()
    threading.Thread(target=capture_laptop_cam, daemon=True).start()

# Main function
def main():
    # Setup the GUI
    setup_gui()

    # Setup video capture for both cameras
    setup_video_capture()

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
