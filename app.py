import cv2
import mediapipe as mp
from controller import Controller

# Initialize video capture
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_draw = mp.solutions.drawing_utils

# Initialize Controller instance
controller = Controller()

try:
    while True:
        success, img = cap.read()
        if not success:
            print("Error: Failed to capture image.")
            break

        img = cv2.flip(img, 1)  # Mirror image
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                controller.set_hand_landmarks(hand_landmarks)
                mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Execute controller functions
                controller.update_finger_status()
                controller.move_cursor()
                controller.detect_scrolling()
                controller.detect_clicking()
                controller.detect_dragging()

        # Show the output frame
        cv2.imshow('Hand Tracker', img)

        # Exit if 'q' is pressed OR window is closed
        if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('Hand Tracker', cv2.WND_PROP_VISIBLE) < 1:
            print("\nClosing application...")
            break

except KeyboardInterrupt:
    print("\nInterrupted! Closing...")

finally:
    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    print("Resources released. Program exited.")
