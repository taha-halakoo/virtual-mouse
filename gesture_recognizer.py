import math
import time
from collections import deque
import numpy as np

class GestureRecognizer:
    """
    Virtual Mouse v10: Advanced Multi-Modal Gesture Engine
    Features: Bimanual Choreography, OCR Triggers, CAD Orbit, Jedi Mode
    """
    def __init__(self, config=None, **kwargs):
        self.config = config or {}
        self.gestures = self.config.get('gestures', {})
        
        self.results = None
        self.frame_shape = None
        
        self.pinching_left = False
        self.pinching_right = False
        self.last_action_time = 0
        self.action_cooldown = 0.3 
        
        self.PINCH_ON_THRESH = self.gestures.get('click_pinch_distance', 0.15)
        self.PINCH_OFF_THRESH = self.PINCH_ON_THRESH + 0.05
        
        self.mode = "Trackpad"
        
        self.x_history = deque(maxlen=20)
        self.y_history = deque(maxlen=20)
        
        # For Bimanual/CAD Orbit
        self.last_orbit_dist = None
        self.last_orbit_angle = None

    def update_result(self, results, frame_shape):
        self.results = results
        self.frame_shape = frame_shape

    def recognize(self):
        if not self.results: return []
        actions = []
        
        # Bimanual Setup
        left_hand, right_hand = None, None
        if self.results.hand_landmarks and self.results.handedness:
            for i, handedness_list in enumerate(self.results.handedness):
                hand_label = handedness_list[0].category_name
                if hand_label == 'Left':
                    left_hand = self.results.hand_landmarks[i]
                elif hand_label == 'Right':
                    right_hand = self.results.hand_landmarks[i]

        current_time = time.time()

        # --- Bimanual (Two-Handed) Choreography & CAD Orbit ---
        if left_hand and right_hand:
            # Feature 27: CAD "Orbit" Mode (Pinch both hands and rotate)
            left_thumb_idx = self._get_rel_dist(left_hand, 4, 8)
            right_thumb_idx = self._get_rel_dist(right_hand, 4, 8)
            
            if left_thumb_idx < self.PINCH_ON_THRESH and right_thumb_idx < self.PINCH_ON_THRESH:
                self.mode = "CAD Orbit"
                l_pt = (left_hand[8].x, left_hand[8].y)
                r_pt = (right_hand[8].x, right_hand[8].y)
                
                dist = math.hypot(l_pt[0] - r_pt[0], l_pt[1] - r_pt[1])
                angle = math.atan2(r_pt[1] - l_pt[1], r_pt[0] - l_pt[0])
                
                if self.last_orbit_dist is not None:
                    zoom_delta = dist - self.last_orbit_dist
                    angle_delta = angle - self.last_orbit_angle
                    actions.append(('cad_orbit', (zoom_delta, angle_delta)))
                
                self.last_orbit_dist = dist
                self.last_orbit_angle = angle
                return actions # Exclusive mode
            else:
                self.last_orbit_dist = None
                self.last_orbit_angle = None
                
            # Feature 30: Screen-Tearing Screenshots (Left Peace Sign + Right Swipe)
            l_fingers = self._get_precise_fingers(left_hand)
            r_fingers = self._get_precise_fingers(right_hand)
            if l_fingers == [0, 1, 1, 0, 0] and r_fingers == [0, 1, 1, 1, 1]:
                 if current_time - self.last_action_time > 2.0:
                      actions.append(('trigger_screenshot', None))
                      self.last_action_time = current_time
                      return actions

            # Feature 39: IDE Code Collapse (Crushing both hands into fists)
            if sum(l_fingers) <= 1 and sum(r_fingers) <= 1:
                 if current_time - self.last_action_time > 2.0:
                      actions.append(('ide_collapse', None))
                      self.last_action_time = current_time
                      return actions
                      
            # Feature 33: Presentation Jedi Mode (Swipe right hand while left hand is up)
            if sum(l_fingers) >= 4 and sum(r_fingers) >= 4:
                 dx = self.x_history[-1] - self.x_history[0] if len(self.x_history) > 10 else 0
                 if abs(dx) > 0.3 * self.frame_shape[1] and current_time - self.last_action_time > 1.0:
                      actions.append(('jedi_swipe', 'next' if dx > 0 else 'prev'))
                      self.last_action_time = current_time
                      self.x_history.clear()
                      return actions

        # --- Single Hand (Dominant Trackpad Logic) ---
        primary_hand = right_hand or left_hand
        if not primary_hand:
            self.x_history.clear()
            self.mode = "Paused"
            return [('pause_tracking', None)]

        h, w, _ = self.frame_shape
        fingers = self._get_precise_fingers(primary_hand)
        
        # Feature 24: Semantic Text Highlighting (Point with index only)
        if fingers == [0, 1, 0, 0, 0]:
             if current_time - self.last_action_time > 2.0:
                  actions.append(('semantic_highlight', None))
                  self.last_action_time = current_time
                  # Do not return, allow moving cursor

        # --- Movement ---
        tracking_point = primary_hand[5] # Index finger base
        base_x, base_y = int(tracking_point.x * w), int(tracking_point.y * h)
        actions.append(('move', (base_x, base_y)))
        
        self.x_history.append(base_x)
        self.y_history.append(base_y)

        # --- Pinches (Clicks & Clicks) ---
        thumb_index_dist = self._get_rel_dist(primary_hand, 4, 8)
        thumb_middle_dist = self._get_rel_dist(primary_hand, 4, 12)
        thumb_ring_dist = self._get_rel_dist(primary_hand, 4, 16)
        thumb_pinky_dist = self._get_rel_dist(primary_hand, 4, 20)

        # Feature 40: Terminal Air-Commands (Thumb + Pinky pinch + movement)
        if thumb_pinky_dist < self.PINCH_ON_THRESH:
            actions.append(('terminal_command', None))
            return actions

        # Sniper Mode
        if thumb_ring_dist < self.PINCH_ON_THRESH:
            actions.append(('precision_mode', True))
            self.mode = "Sniper"
        else:
            actions.append(('precision_mode', False))
            self.mode = "Moving"

        # Left Click / Drag
        if not self.pinching_left and thumb_index_dist < self.PINCH_ON_THRESH:
            self.pinching_left = True
            actions.append(('mouse_down', None))
            
        elif self.pinching_left and thumb_index_dist > self.PINCH_OFF_THRESH:
            self.pinching_left = False
            actions.append(('mouse_up', None))
            
        # Right Click
        if thumb_middle_dist < self.PINCH_ON_THRESH and (current_time - self.last_action_time > self.action_cooldown):
            actions.append(('right_click', None))
            self.last_action_time = current_time

        # Scroll
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
            wrist_y = int(primary_hand[0].y * h)
            if not hasattr(self, 'last_scroll_y'): self.last_scroll_y = wrist_y
            delta_y = self.last_scroll_y - wrist_y
            
            scroll_mult = self.config.get('mouse', {}).get('smooth_scroll_mult', 1.2)
            if abs(delta_y) > 5:
                actions.append(('scroll', int(delta_y * scroll_mult)))
                self.last_scroll_y = wrist_y
            self.mode = "Scrolling"
            actions.append(('set_mode', 'Scrolling'))
        else:
            if hasattr(self, 'last_scroll_y'): del self.last_scroll_y
            actions.append(('set_mode', self.mode))

        return actions

    def _get_hand_scale(self, hand_landmarks):
        p1 = hand_landmarks[0]
        p2 = hand_landmarks[5]
        return math.hypot(p1.x - p2.x, p1.y - p2.y)

    def _get_rel_dist(self, hand_landmarks, id1, id2):
        scale = self._get_hand_scale(hand_landmarks)
        if scale == 0: return 1.0
        p1 = hand_landmarks[id1]
        p2 = hand_landmarks[id2]
        dist = math.hypot(p1.x - p2.x, p1.y - p2.y)
        if self.config.get('advanced', {}).get('hand_size_normalization', True):
            return dist / scale
        return dist

    def _get_precise_fingers(self, hand_landmarks):
        if not hand_landmarks: return [0, 0, 0, 0, 0]
        fingers = []
        thumb_dist_tip = math.hypot(hand_landmarks[4].x - hand_landmarks[17].x, hand_landmarks[4].y - hand_landmarks[17].y)
        thumb_dist_base = math.hypot(hand_landmarks[2].x - hand_landmarks[17].x, hand_landmarks[2].y - hand_landmarks[17].y)
        fingers.append(1 if thumb_dist_tip > thumb_dist_base else 0)
        
        for tip_id in [8, 12, 16, 20]:
            is_raised = hand_landmarks[tip_id].y < hand_landmarks[tip_id - 2].y
            fingers.append(1 if is_raised else 0)
        return fingers
