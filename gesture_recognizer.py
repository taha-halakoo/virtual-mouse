import math
import time
from collections import deque
import numpy as np

class GestureRecognizer:
    """
    Virtual Mouse v3.0: Trackpad & Relative Tracking Engine
    """
    def __init__(self, config=None, **kwargs):
        self.config = config or {}
        self.results = None
        self.frame_shape = None
        
        self.pinching_left = False
        self.last_action_time = 0
        self.action_cooldown = 0.3 
        
        self.PINCH_ON_THRESH = self.config.get('gestures', {}).get('click_pinch_distance', 0.15)
        self.PINCH_OFF_THRESH = self.PINCH_ON_THRESH + 0.05
        
        self.mode = "Trackpad"
        self.last_scroll_y = None

    def update_result(self, results, frame_shape):
        self.results = results
        self.frame_shape = frame_shape

    def recognize(self):
        if not self.results: return []
        actions = []
        
        primary_hand = None
        if self.results.hand_landmarks and self.results.handedness:
            primary_hand = self.results.hand_landmarks[0]

        if not primary_hand:
            self.mode = "Paused"
            return [('pause_tracking', None)]

        h, w, _ = self.frame_shape
        fingers = self._get_precise_fingers(primary_hand)
        
        current_time = time.time()
        
        thumb_index_dist = self._get_rel_dist(primary_hand, 4, 8)
        thumb_middle_dist = self._get_rel_dist(primary_hand, 4, 12)
        thumb_ring_dist = self._get_rel_dist(primary_hand, 4, 16)
        
        up_fingers = sum(fingers[1:]) # index, middle, ring, pinky
        
        # Clutch Check (Fist or Open Palm)
        if up_fingers == 0 or up_fingers == 4:
            self.mode = "Clutch"
            actions.append(('pause_tracking', None))
            actions.append(('set_mode', 'Clutch (Paused)'))
            return actions

        # Use Index Finger MCP (Base) for stable tracking, not the tip!
        # This prevents the cursor from jerking when pinching.
        tracking_point = primary_hand[5] 
        base_x, base_y = int(tracking_point.x * w), int(tracking_point.y * h)

        # Sniper Mode Toggle (Quick pinch Ring + Thumb)
        if not hasattr(self, 'sniper_toggled'):
            self.sniper_toggled = False
            self.last_sniper_toggle_time = 0

        if thumb_ring_dist < self.PINCH_ON_THRESH:
            if current_time - self.last_sniper_toggle_time > 0.5:
                self.sniper_toggled = not self.sniper_toggled
                self.last_sniper_toggle_time = current_time

        if self.sniper_toggled:
            actions.append(('precision_mode', True))
            self.mode = "Sniper"
        else:
            actions.append(('precision_mode', False))
            if self.mode == "Sniper": self.mode = "Moving"
            
        # Drag-Lock Toggle Feature
        drag_lock = self.config.get('mouse', {}).get('drag_lock', False)

        # Left Click / Drag Check
        if drag_lock:
            if thumb_index_dist < self.PINCH_ON_THRESH and not self.pinching_left:
                self.pinching_left = True
                if current_time - self.last_action_time > self.action_cooldown:
                    if getattr(self, 'drag_locked', False):
                        self.drag_locked = False
                        actions.append(('mouse_up', None))
                    else:
                        self.drag_locked = True
                        actions.append(('mouse_down', None))
                    self.last_action_time = current_time
            elif thumb_index_dist > self.PINCH_OFF_THRESH:
                self.pinching_left = False
        else:
            if thumb_index_dist < self.PINCH_ON_THRESH:
                if not self.pinching_left:
                    self.pinching_left = True
                    actions.append(('mouse_down', None))
            elif thumb_index_dist > self.PINCH_OFF_THRESH:
                if self.pinching_left:
                    self.pinching_left = False
                    actions.append(('mouse_up', None))
                    self.last_action_time = current_time

        # Right Click Check
        if thumb_middle_dist < self.PINCH_ON_THRESH and (current_time - self.last_action_time > self.action_cooldown):
            actions.append(('right_click', None))
            self.last_action_time = current_time

        # Scroll Check (Two Fingers Pointing)
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
            wrist_y = int(primary_hand[0].y * h)
            if self.last_scroll_y is None: self.last_scroll_y = wrist_y
            delta_y = self.last_scroll_y - wrist_y
            
            scroll_mult = self.config.get('mouse', {}).get('smooth_scroll_mult', 1.2)
            if abs(delta_y) > 2:
                actions.append(('scroll', int(delta_y * scroll_mult)))
                self.last_scroll_y = wrist_y
            self.mode = "Scrolling"
            actions.append(('set_mode', 'Scrolling'))
            actions.append(('pause_tracking', None)) # pause pointer movement
        else:
            self.last_scroll_y = None
            if self.mode != "Sniper": self.mode = "Moving"
            actions.append(('set_mode', self.mode))
            
            # Pass hand scale for Z-Axis Depth Scaling
            hand_scale = self._get_hand_scale(primary_hand)
            actions.append(('move', (base_x, base_y, hand_scale)))

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
        return dist / scale

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
