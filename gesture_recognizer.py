import math
import time
from collections import deque
import numpy as np

class GestureRecognizer:
    """
    Omni-Sense Gesture Recognizer (Face + Hands + Eyes).
    Adapted to correctly parse the modern MediaPipe Tasks API objects.
    """
    MODE_MOVING = "Moving"
    MODE_SCROLLING = "Scrolling"
    
    def __init__(self, click_pinch_distance=0.15, control_mode="two_handed", handedness_swap=True, **kwargs):
        self.mode = self.MODE_MOVING
        self.control_mode = control_mode 
        self.results = None
        self.frame_shape = None
        self.handedness_swap = handedness_swap
        
        # State Tracking
        self.pinching = False
        self.last_action_time = 0
        self.action_cooldown = 0.4 
        
        self.PINCH_ON_THRESH = click_pinch_distance 
        self.PINCH_OFF_THRESH = click_pinch_distance + 0.05
        
        self.mode_history = deque(maxlen=8)

    def update_result(self, results, frame_shape):
        self.results = results
        self.frame_shape = frame_shape

    def recognize(self):
        if not self.results: return []
        
        if self.control_mode == "face_and_eyes":
            return self._recognize_face_eyes()
        elif self.control_mode == "one_handed":
            return self._recognize_one_handed()
        return self._recognize_two_handed()

    # --- Face & Eye Logic ---
    def _get_ear(self, face_landmarks, eye_indices):
        """Calculates Eye Aspect Ratio to detect blinks."""
        # face_landmarks is a list of NormalizedLandmark
        p_left = face_landmarks[eye_indices[0]]
        p_top = face_landmarks[eye_indices[1]]
        p_right = face_landmarks[eye_indices[2]]
        p_bottom = face_landmarks[eye_indices[3]]
        
        width = math.hypot(p_right.x - p_left.x, p_right.y - p_left.y)
        height = math.hypot(p_top.x - p_bottom.x, p_top.y - p_bottom.y)
        if width == 0: return 0
        return height / width

    def _recognize_face_eyes(self):
        actions = []
        if not self.results.face_landmarks: return actions
        
        h, w, _ = self.frame_shape
        # self.results.face_landmarks is a list of faces. Grab the first face.
        face_lm = self.results.face_landmarks[0] 

        # 1. Nose Pointer (Super stable tracking point)
        nose_tip = face_lm[1]
        
        # Amplify movement relative to screen center
        center_x, center_y = 0.5, 0.5
        head_move_x = (nose_tip.x - center_x) * 3.0 
        head_move_y = (nose_tip.y - center_y) * 3.0
        
        target_x = int((center_x + head_move_x) * w)
        target_y = int((center_y + head_move_y) * h)
        actions.append(('move', (target_x, target_y)))

        # 2. Eye Blinks (Clicks)
        left_ear = self._get_ear(face_lm, [33, 159, 133, 145])
        right_ear = self._get_ear(face_lm, [362, 386, 263, 374])
        
        BLINK_THRESH = 0.2
        current_time = time.time()
        
        if current_time - self.last_action_time > self.action_cooldown:
            if left_ear < BLINK_THRESH and right_ear > BLINK_THRESH: # Wink Left
                actions.append(('left_click', None))
                self.last_action_time = current_time
            elif right_ear < BLINK_THRESH and left_ear > BLINK_THRESH: # Wink Right
                actions.append(('right_click', None))
                self.last_action_time = current_time

        # 3. Mouth Open (Drag)
        mouth_dist = math.hypot(face_lm[13].x - face_lm[14].x, 
                                face_lm[13].y - face_lm[14].y)
        
        face_height = math.hypot(face_lm[152].x - face_lm[10].x, 
                                 face_lm[152].y - face_lm[10].y)
        
        if face_height > 0:
            rel_mouth_open = mouth_dist / face_height
            if rel_mouth_open > 0.1: # Mouth is open
                if not self.pinching:
                    actions.append(('mouse_down', None))
                    self.pinching = True
            else:
                if self.pinching:
                    actions.append(('mouse_up', None))
                    self.pinching = False

        return actions

    # --- Hand Logic ---
    def _get_hands(self):
        left_hand, right_hand = None, None
        if self.results.hand_landmarks and self.results.handedness:
            for i, handedness_list in enumerate(self.results.handedness):
                hand_label = handedness_list[0].category_name
                if self.handedness_swap:
                    hand_label = 'Right' if hand_label == 'Left' else 'Left'

                if hand_label == 'Left':
                    left_hand = self.results.hand_landmarks[i]
                elif hand_label == 'Right':
                    right_hand = self.results.hand_landmarks[i]
        return left_hand, right_hand

    def _get_hand_scale(self, hand_landmarks):
        # hand_landmarks is a list of NormalizedLandmark
        p1 = hand_landmarks[0]
        p2 = hand_landmarks[5]
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def _get_rel_dist(self, hand_landmarks, id1, id2):
        scale = self._get_hand_scale(hand_landmarks)
        if scale == 0: return 1.0
        p1 = hand_landmarks[id1]
        p2 = hand_landmarks[id2]
        return math.hypot(p1.x - p2.x, p1.y - p2.y) / scale

    def _get_precise_fingers(self, hand_landmarks):
        if not hand_landmarks: return [0, 0, 0, 0, 0]
        fingers = []
        thumb_dist_tip = math.hypot(hand_landmarks[4].x - hand_landmarks[17].x, 
                                   hand_landmarks[4].y - hand_landmarks[17].y)
        thumb_dist_base = math.hypot(hand_landmarks[2].x - hand_landmarks[17].x, 
                                    hand_landmarks[2].y - hand_landmarks[17].y)
        fingers.append(1 if thumb_dist_tip > thumb_dist_base else 0)
        for tip_id in [8, 12, 16, 20]:
            is_raised = (hand_landmarks[tip_id].y < hand_landmarks[tip_id - 1].y < hand_landmarks[tip_id - 2].y)
            fingers.append(1 if is_raised else 0)
        return fingers

    def _recognize_one_handed(self):
        actions = []
        left_hand, right_hand = self._get_hands()
        # In one-handed mode, we just grab whatever hand is visible. 
        # Prefer right hand, fallback to left.
        hand = right_hand or left_hand
        if not hand: return actions

        h, w, _ = self.frame_shape
        current_time = time.time()
        
        # Move
        index_tip = hand[8]
        actions.append(('move', (int(index_tip.x * w), int(index_tip.y * h))))

        # Clicks
        lp_dist = self._get_rel_dist(hand, 4, 8)
        rp_dist = self._get_rel_dist(hand, 4, 12)
        
        if not self.pinching and lp_dist < self.PINCH_ON_THRESH:
            self.pinching = True
            actions.append(('mouse_down', None))
        elif self.pinching and lp_dist > self.PINCH_OFF_THRESH:
            self.pinching = False
            actions.append(('mouse_up', None))
            
        if rp_dist < self.PINCH_ON_THRESH and (current_time - self.last_action_time > self.action_cooldown):
            actions.append(('right_click', None))
            self.last_action_time = current_time

        return actions

    def _recognize_two_handed(self):
        actions = []
        left_hand, right_hand = self._get_hands()
        current_time = time.time()
        cooldown_ok = current_time - self.last_action_time > self.action_cooldown

        if right_hand:
            h, w, _ = self.frame_shape
            if self.mode == self.MODE_SCROLLING:
                wrist_y = int(right_hand[0].y * h)
                if not hasattr(self, 'last_wrist_y'): self.last_wrist_y = wrist_y
                delta_y = self.last_wrist_y - wrist_y
                if abs(delta_y) > 10:
                    actions.append(('scroll', int(delta_y * 0.8)))
                    self.last_wrist_y = wrist_y
            else:
                if hasattr(self, 'last_wrist_y'): del self.last_wrist_y
                index_tip = right_hand[8]
                actions.append(('move', (int(index_tip.x * w), int(index_tip.y * h))))

        if left_hand:
            left_fingers = self._get_precise_fingers(left_hand)
            
            # Mode Toggle: V sign
            v_sign = (left_fingers == [0, 1, 1, 0, 0])
            self.mode_history.append(v_sign)
            if len(self.mode_history) == self.mode_history.maxlen and all(self.mode_history) and cooldown_ok:
                self.mode = self.MODE_SCROLLING if self.mode == self.MODE_MOVING else self.MODE_MOVING
                actions.append(('set_mode', self.mode))
                self.last_action_time = current_time
                self.mode_history.clear()

            if self.mode == self.MODE_MOVING:
                lp_dist = self._get_rel_dist(left_hand, 4, 8)
                rp_dist = self._get_rel_dist(left_hand, 4, 12)

                if not self.pinching and lp_dist < self.PINCH_ON_THRESH:
                    self.pinching = True
                    actions.append(('mouse_down', None))
                elif self.pinching and lp_dist > self.PINCH_OFF_THRESH:
                    self.pinching = False
                    actions.append(('mouse_up', None))

                if rp_dist < self.PINCH_ON_THRESH and cooldown_ok:
                    actions.append(('right_click', None))
                    self.last_action_time = current_time
        else:
            if self.pinching:
                actions.append(('mouse_up', None))
                self.pinching = False
                
        return actions