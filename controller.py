import pyautogui
import time

class Controller:
    def __init__(self):
        self.prev_hand = None
        self.prev_scroll_time = time.time()
        self.scroll_speed = 10  # Small increments for smooth scrolling
        self.scroll_acceleration = 10.2  # Adjusts speed dynamically
        self.scroll_direction = 0  # +1 for up, -1 for down, 0 for no scroll
        self.smooth_scroll_factor = 100  # Determines smoothness of movement
        self.prev_x, self.prev_y = None, None
        self.left_clicked = False
        self.right_clicked = False
        self.double_clicked = False
        self.click_delay = 0.3  # 300ms delay to prevent rapid unintended clicks
        self.last_click_time = time.time()
        self.dragging = False
        self.hand_landmarks = None
        self.screen_width, self.screen_height = pyautogui.size()
        self.scaled_width = int(self.screen_width * 2)   # Expand area by 1.5x
        self.scaled_height = int(self.screen_height * 2)
    
    def set_hand_landmarks(self, hand_landmarks):
        """ Sets hand landmarks detected by MediaPipe """
        self.hand_landmarks = hand_landmarks

    def update_finger_status(self):
        """ Updates the status of finger positions """
        if self.hand_landmarks is None:
            return
        
        landmarks = self.hand_landmarks.landmark
        self.little_finger_down = landmarks[20].y > landmarks[17].y
        self.index_finger_down = landmarks[8].y > landmarks[5].y
        self.middle_finger_down = landmarks[12].y > landmarks[9].y
        self.ring_finger_down = landmarks[16].y > landmarks[13].y
        self.thumb_finger_down = landmarks[4].y > landmarks[13].y

        self.all_fingers_down = (
            self.index_finger_down and self.middle_finger_down and 
            self.ring_finger_down and self.little_finger_down
        )
    
    def get_position(self, hand_x, hand_y):
        """ Maps hand coordinates to a scaled screen position """

        # Get current cursor position
        old_x, old_y = pyautogui.position()

        # Scale the hand tracking to a larger virtual screen area
        current_x = int(hand_x * self.scaled_width)
        current_y = int(hand_y * self.scaled_height)

        # Initialize previous hand position if none exists
        if self.prev_hand is None:
            self.prev_hand = (current_x, current_y)

        # Calculate cursor movement delta
        delta_x = current_x - self.prev_hand[0]
        delta_y = current_y - self.prev_hand[1]

        # Update previous position
        self.prev_hand = (current_x, current_y)

        # Smooth cursor movement and prevent abrupt jumps
        new_x = max(5, min(self.screen_width - 5, old_x + delta_x))
        new_y = max(5, min(self.screen_height - 5, old_y + delta_y))

        return new_x, new_y
    
    def move_cursor(self):
        """ Moves cursor based on hand position smoothly """
        if self.hand_landmarks is None:
            return
        
        point = 9  # Middle fingertip
        hand_x, hand_y = self.hand_landmarks.landmark[point].x, self.hand_landmarks.landmark[point].y
        x, y = self.get_position(hand_x, hand_y)

        if not (self.all_fingers_down and self.thumb_finger_down):
            pyautogui.moveTo(x, y, duration=0.05)

    def detect_scrolling(self):
        """ Detects scrolling gestures with smoother motion """
        current_time = time.time()
        time_diff = current_time - self.prev_scroll_time

        # Adjust scrolling speed based on how long the gesture is held
        if self.little_finger_down and not self.index_finger_down:
            self.scroll_direction = 1  # Scroll up
        elif not self.little_finger_down and self.index_finger_down:
            self.scroll_direction = -1  # Scroll down
        else:
            self.scroll_direction = 0  # Stop scrolling smoothly

        if time_diff > 0.000001:  # 20ms delay for ultra-smooth updates
            if self.scroll_direction != 0:
                # Apply gradual acceleration and smooth interpolation
                scroll_amount = self.scroll_speed * self.scroll_direction
                pyautogui.scroll(int(scroll_amount))

                # Gradually increase scrolling speed for fluid motion
                self.scroll_speed *= self.scroll_acceleration
                if self.scroll_speed > self.smooth_scroll_factor:
                    self.scroll_speed = self.smooth_scroll_factor  # Prevent excessive speed
            else:
                # Slow down scrolling when fingers are released
                self.scroll_speed = 5  # Reset to initial speed

            self.prev_scroll_time = current_time  # Update last scroll time

    def fingers_touching(self, finger_tip, thumb_tip, threshold=0.02):
        """
        Check if a finger tip is touching the thumb tip.
        - threshold: Adjusts sensitivity (lower = more precise)
        """
        distance = ((finger_tip.x - thumb_tip.x) ** 2 + (finger_tip.y - thumb_tip.y) ** 2) ** 0.5
        return distance < threshold

    def detect_clicking(self):
        """ Detects clicking gestures when fingers touch the thumb """
        if self.hand_landmarks is None:
            return

        current_time = time.time()

        # Get landmark positions
        index_tip = self.hand_landmarks.landmark[8]   # Index finger tip
        middle_tip = self.hand_landmarks.landmark[12]  # Middle finger tip
        ring_tip = self.hand_landmarks.landmark[16]   # Ring finger tip
        thumb_tip = self.hand_landmarks.landmark[4]   # Thumb tip

        # Detect Left Click (Index Finger touches Thumb)
        if self.fingers_touching(index_tip, thumb_tip) and not self.left_clicked:
            pyautogui.click()
            self.left_clicked = True
            self.last_click_time = current_time

        elif not self.fingers_touching(index_tip, thumb_tip):
            self.left_clicked = False  # Reset when fingers separate

        # Detect Right Click (Middle Finger touches Thumb)
        if self.fingers_touching(middle_tip, thumb_tip) and not self.right_clicked:
            pyautogui.rightClick()
            self.right_clicked = True
            self.last_click_time = current_time

        elif not self.fingers_touching(middle_tip, thumb_tip):
            self.right_clicked = False  # Reset when fingers separate

        # Detect Double Click (Ring Finger touches Thumb)
        if self.fingers_touching(ring_tip, thumb_tip) and not self.double_clicked:
            pyautogui.doubleClick()
            self.double_clicked = True
            self.last_click_time = current_time

        elif not self.fingers_touching(ring_tip, thumb_tip):
            self.double_clicked = False  # Reset when fingers separate

    def detect_dragging(self):
        """ Detects dragging gestures """
        if self.all_fingers_down and not self.dragging:
            pyautogui.mouseDown(button='left')
            self.dragging = True
        elif not self.all_fingers_down and self.dragging:
            pyautogui.mouseUp(button='left')
            self.dragging = False
