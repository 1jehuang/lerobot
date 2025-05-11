import cv2
import os

def check_available_cameras():
    """Check which camera indices are available on the system"""
    print("Checking available cameras...")
    
    available_cameras = []
    # Try cameras with indices 0 to 5
    for i in range(6):
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"Camera index {i} is available.")
                    available_cameras.append(i)
                    # Save a test frame to verify the camera
                    os.makedirs("camera_test", exist_ok=True)
                    cv2.imwrite(f"camera_test/camera_{i}.jpg", frame)
                    print(f"Saved test image from camera {i} to camera_test/camera_{i}.jpg")
                cap.release()
            else:
                print(f"Camera index {i} is not available or cannot be opened.")
        except Exception as e:
            print(f"Error checking camera {i}: {e}")
    
    return available_cameras

if __name__ == "__main__":
    available_cameras = check_available_cameras()
    print(f"Available camera indices: {available_cameras}")
