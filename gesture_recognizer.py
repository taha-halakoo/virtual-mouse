import math
import time
from collections import deque

class GestureRecognizer:
    """
    ULTIMATE PRECISION Gesture Recognizer with One-Handed & Two-Handed support.
    """
    MODE_MOVING = "Moving"
    MODE_SCROLLING = "Scrolling"
    
    # Landmark IDs
    WRIST = 0
    THUMB_TIP = 4
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_TIP = 16
    PINKY_TIP = 20
    
    INDEX_MCP = 5
    PINKY_MCP = 17

    def __init__(self, click_pinch_distance=0.15, handedness_swap=True, control_mode="two_handed", **kwargs):
        self.mode = self.MODE_MOVING
        self.control_mode = control_mode # "one_handed" or "two_handed"
        self.detection_result = None
        self.frame_shape = None
        self.handedness_swap = handedness_swap
        
        # State Tracking
        self.pinching = False # Unified pinch state
        self.last_action_time = 0
        self.action_cooldown = 0.4 
        
        # Relative Pinch Threshold
        self.CLICK_THRESHOLD_REL = click_pinch_distance 
        
        # Mode Toggle Buffer
        self.mode_history = deque(maxlen=8)

    def update_result(self, detection_result, frame_shape):
        self.detection_result = detection_result
        self.frame_shape = frame_shape
        
    def _get_hands(self):
        left_hand, right_hand = None, None
        if self.detection_result and self.detection_result.hand_landmarks:
            for i, handedness in enumerate(self.detection_result.handedness):
                hand_label = handedness[0].category_name
                if self.handedness_swap:
                    hand_label = 'Right' if hand_label == 'Left' else 'Left'

                if hand_label == 'Left':
                    left_hand = self.detection_result.hand_landmarks[i]
                elif hand_label == 'Right':
                    right_hand = self.detection_result.hand_landmarks[i]
        return left_hand, right_hand

    def _get_hand_scale(self, hand_landmarks):
        p1 = hand_landmarks[self.WRIST]
        p2 = hand_landmarks[self.INDEX_MCP]
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def _get_precise_fingers(self, hand_landmarks):
        if not hand_landmarks: return [0, 0, 0, 0, 0]
        fingers = []
        # Thumb
        thumb_dist_tip = math.hypot(hand_landmarks[self.THUMB_TIP].x - hand_landmarks[self.PINKY_MCP].x, 
                                   hand_landmarks[self.THUMB_TIP].y - hand_landmarks[self.PINKY_MCP].y)
        thumb_dist_base = math.hypot(hand_landmarks[self.THUMB_TIP - 2].x - hand_landmarks[self.PINKY_MCP].x, 
                                    hand_landmarks[self.THUMB_TIP - 2].y - hand_landmarks[self.PINKY_MCP].y)
        fingers.append(1 if thumb_dist_tip > thumb_dist_base else 0)
        # Other 4
        for tip_id in [8, 12, 16, 20]:
            is_raised = (hand_landmarks[tip_id].y < hand_landmarks[tip_id - 1].y < hand_landmarks[tip_id - 2].y)
            fingers.append(1 if is_raised else 0)
        return fingers

    def _get_rel_dist(self, hand_landmarks, id1, id2):
        scale = self._get_hand_scale(hand_landmarks)
        if scale == 0: return 1.0
        p1 = hand_landmarks[id1]
        p2 = hand_landmarks[id2]
        return math.hypot(p1.x - p2.x, p1.y - p2.y) / scale

    def recognize(self):
        if self.control_mode == "one_handed":
            return self._recognize_one_handed()
        return self._recognize_two_handed()

    def _recognize_two_handed(self):
        actions = []
        left_hand, right_hand = self._get_hands()
        current_time = time.time()
        cooldown_ok = current_time - self.last_action_time > self.action_cooldown

        if right_hand:
            h, w, _ = self.frame_shape
            if self.mode == self.MODE_SCROLLING:
                wrist_y = int(right_hand[self.WRIST].y * h)
                if not hasattr(self, 'last_wrist_y'): self.last_wrist_y = wrist_y
                delta_y = self.last_wrist_y - wrist_y
                if abs(delta_y) > 10:
                    actions.append(('scroll', int(delta_y * 0.8)))
                    self.last_wrist_y = wrist_y
            else:
                if hasattr(self, 'last_wrist_y'): del self.last_wrist_y
                index_tip = right_hand[self.INDEX_FINGER_TIP]
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
                lp_dist = self._get_rel_dist(left_hand, self.THUMB_TIP, self.INDEX_FINGER_TIP)
                rp_dist = self._get_rel_dist(left_hand, self.THUMB_TIP, self.MIDDLE_FINGER_TIP)
                trigger_thresh = 0.4 
                lp_active = lp_dist < trigger_thresh
                rp_active = rp_dist < trigger_thresh

                if cooldown_ok:
                    if lp_active and not self.pinching:
                        actions.append(('left_click', None))
                        self.last_action_time = current_time
                    elif rp_active:
                        actions.append(('right_click', None))
                        self.last_action_time = current_time

                if lp_active and not self.pinching:
                    actions.append(('mouse_down', None))
                    self.pinching = True
                elif not lp_active and self.pinching:
                    actions.append(('mouse_up', None))
                    self.pinching = False
        else:
            if self.pinching:
                actions.append(('mouse_up', None))
                self.pinching = False
        return actions

    def _recognize_one_handed(self):
        actions = []
        _, right_hand = self._get_hands() # Use right hand for everything in one-handed
        current_time = time.time()
        cooldown_ok = current_time - self.last_action_time > self.action_cooldown

        if right_hand:
            h, w, _ = self.frame_shape
            fingers = self._get_precise_fingers(right_hand)
            
            # 1. Mode Toggle: V Sign
            v_sign = (fingers == [0, 1, 1, 0, 0])
            self.mode_history.append(v_sign)
            if len(self.mode_history) == self.mode_history.maxlen and all(self.mode_history) and cooldown_ok:
                self.mode = self.MODE_SCROLLING if self.mode == self.MODE_MOVING else self.MODE_MOVING
                actions.append(('set_mode', self.mode))
                self.last_action_time = current_time
                self.mode_history.clear()

            # 2. Movement / Scrolling
            if self.mode == self.MODE_SCROLLING:
                wrist_y = int(right_hand[self.WRIST].y * h)
                if not hasattr(self, 'last_wrist_y'): self.last_wrist_y = wrist_y
                delta_y = self.last_wrist_y - wrist_y
                if abs(delta_y) > 10:
                    actions.append(('scroll', int(delta_y * 0.8)))
                    self.last_wrist_y = wrist_y
            else:
                if hasattr(self, 'last_wrist_y'): del self.last_wrist_y
                index_tip = right_hand[self.INDEX_FINGER_TIP]
                actions.append(('move', (int(index_tip.x * w), int(index_tip.y * h))))

            # 3. Actions: Pinch
            lp_dist = self._get_rel_dist(right_hand, self.THUMB_TIP, self.INDEX_FINGER_TIP)
            rp_dist = self._get_rel_dist(right_hand, self.THUMB_TIP, self.MIDDLE_FINGER_TIP)
            trigger_thresh = 0.4
            lp_active = lp_dist < trigger_thresh
            rp_active = rp_dist < trigger_thresh

            if cooldown_ok:
                if lp_active and not self.pinching:
                    actions.append(('left_click', None))
                    self.last_action_time = current_time
                elif rp_active:
                    actions.append(('right_click', None))
                    self.last_action_time = current_time

            if lp_active and not self.pinching:
                actions.append(('mouse_down', None))
                self.pinching = True
            elif not lp_active and self.pinching:
                actions.append(('mouse_up', None))
                self.pinching = False
        else:
            if self.pinching:
                actions.append(('mouse_up', None))
                self.pinching = False
        return actions
