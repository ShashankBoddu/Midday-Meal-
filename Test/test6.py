import cv2
import tkinter as tk
from PIL import Image, ImageTk
import threading
import time

# Global variables to hold the frames
frame1 = None
frame2 = None
lock = threading.Lock()  # To synchronize frame updates
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')  # Load Haar Cascade for face detection

# Variable for live face detection (time difference between consecutive detections)
last_face_time = 0
face_detected = False

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

# Function to check if face is detected and if it's a live face
def detect_and_verify_face(frame):
    global last_face_time, face_detected

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

    if len(faces) > 0:
        current_time = time.time()
        # Check if it's a live face by measuring the time difference
        if current_time - last_face_time > 1:  # At least 1 second between face detections
            face_detected = True
        last_face_time = current_time
    else:
        face_detected = False
    
    return faces

# Function to update the display of both cameras and text
def update_display():
    global frame1, frame2

    with lock:
        # Display Weight in Frame 1
        weight_label.config(text="Weight: 0.0 kg")

        # Display USB webcam in Frame 2
        if frame1 is not None:
            frame1_resized = cv2.resize(frame1, (screen_width // 2 - 20, screen_height // 2 - 20))
            
            # Detect face and check if it's live
            faces = detect_and_verify_face(frame1_resized)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame1_resized, (x, y), (x+w, y+h), (255, 0, 0), 2)
                # Display if live face is detected
                if face_detected:
                    cv2.putText(frame1_resized, "Live Face Detected", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

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
    
    # Open the USB webcam (camera index 0 for most USB webcams)
    cap1 = cv2.VideoCapture(0)  # Change to the correct index if needed

    # Open the laptop's built-in camera (camera index 1)
    cap2 = cv2.VideoCapture(1)

    # Set video capture dimensions (optional)
    cap1.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap1.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap2.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

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
    cap1.release()
    cap2.release()
    cv2.destroyAllWindows()

# Run the main function
if __name__ == "__main__":
    main()
