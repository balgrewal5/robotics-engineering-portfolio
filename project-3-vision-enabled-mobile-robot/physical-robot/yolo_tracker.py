import time

import cv2
import serial
from ultralytics import YOLO


PORT = "/dev/ttyACM0"
TARGET = "person"

DEADBAND = 90
CONFIDENCE = 0.4

TURN_TIME = 0.15
SETTLE_TIME = 0.25


model = YOLO("yolo11n.pt")

arduino = serial.Serial(PORT, 115200, timeout=0.1)
time.sleep(3)
arduino.write(b'S')

camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)


try:
    if not camera.isOpened():
        raise RuntimeError("Camera failed to open")

    print("Pulse-based tracking started. Press Ctrl+C to stop.")

    while True:
        # Discard buffered frames before each correction
        for _ in range(3):
            camera.grab()

        success, frame = camera.read()

        if not success:
            arduino.write(b'S')
            time.sleep(0.2)
            continue

        image_center = frame.shape[1] // 2

        results = model.predict(
            frame,
            imgsz=320,
            conf=CONFIDENCE,
            verbose=False
        )

        target_center = None
        best_confidence = -1.0

        # Track the highest-confidence person
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            confidence = float(box.conf[0])

            if class_name != TARGET:
                continue

            if confidence > best_confidence:
                best_confidence = confidence

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                target_center = (x1 + x2) // 2

        command = 'S'

        if target_center is not None:
            error = target_center - image_center

            if error < -DEADBAND:
                command = 'L'
            elif error > DEADBAND:
                command = 'R'

            print(f"Error: {error} px | Command: {command}")
        else:
            print("Target lost - STOP")

        # Apply a short rotation, then stop and observe again
        if command != 'S':
            arduino.write(command.encode())
            time.sleep(TURN_TIME)

            arduino.write(b'S')
            time.sleep(SETTLE_TIME)
        else:
            arduino.write(b'S')
            time.sleep(0.1)

except KeyboardInterrupt:
    print("Tracking stopped")

finally:
    try:
        arduino.write(b'S')
        time.sleep(0.1)
    finally:
        camera.release()
        arduino.close()

    print("Robot stopped")
