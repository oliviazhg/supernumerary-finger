'''
Hand Position Detection using XGBoost

Training Mode:
1. Run with TRAINING_MODE = True
2. Press '0' while hand is RELAXED (neutral resting position, minimal tension)
3. Press '1' while making a CLOSED FIST (fully clenched)
4. Exit when enough data collected (saved to data/vals0.dat, vals1.dat)

Training Tips:
- RELAXED: Let hand hang naturally, no muscle tension
- CLOSED FIST: Tight fist, thumb over fingers
- Collect 250-300 samples per class (hold each pose for 5-6 seconds)
- Vary hand position slightly during collection for robustness

Classification Mode:
1. Set TRAINING_MODE = False
2. Call get_hand_position() to get current hand state
   Returns: 0 = relaxed, 1 = closed fist
'''

import pygame
from pygame.locals import *
import numpy as np
from collections import deque
import threading
import time
import struct

from pyomyo import Myo, emg_mode
from pyomyo.Classifier import Live_Classifier, MyoClassifier, EMGHandler
from xgboost import XGBClassifier

TRAINING_MODE = False

# Sliding window parameters
WINDOW_DURATION_MS = 200  # 200ms windows
OVERLAP_PERCENT = 0.40    # 40% overlap
EMG_SAMPLE_RATE = 200     # 200Hz for FILTERED mode

# Calculate window parameters
SAMPLES_PER_WINDOW = int((WINDOW_DURATION_MS / 1000.0) * EMG_SAMPLE_RATE)  # 10 samples
STRIDE_SAMPLES = int(SAMPLES_PER_WINDOW * (1 - OVERLAP_PERCENT))  # 6 samples (60% stride)


class SlidingWindowClassifier:
    '''Applies classification on sliding windows of EMG data'''

    def __init__(self, window_size, stride):
        self.window_size = window_size
        self.stride = stride
        self.emg_buffer = deque(maxlen=window_size)
        self.current_position = 0  # 0 = open, 1 = fist
        self.samples_since_classify = 0
        self.classifier = None
        self.lock = threading.Lock()

    def set_classifier(self, classifier):
        '''Set the trained classifier'''
        self.classifier = classifier

    def add_emg_sample(self, emg):
        '''Add new EMG sample and classify if window is ready'''
        with self.lock:
            self.emg_buffer.append(emg)
            self.samples_since_classify += 1

            # Check if we have enough samples and reached stride
            if len(self.emg_buffer) >= self.window_size and \
               self.samples_since_classify >= self.stride:
                self._classify_window()
                self.samples_since_classify = 0

    def _classify_window(self):
        '''Classify the current window'''
        if self.classifier is None or self.classifier.model is None:
            return

        # Convert buffer to numpy array and flatten
        window_data = np.array(list(self.emg_buffer)).flatten()

        # Classify the window
        try:
            prediction = self.classifier.classify(window_data)
            self.current_position = int(prediction)
        except Exception as e:
            print(f"Classification error: {e}")

    def get_position(self):
        '''Get current hand position (0=open, 1=fist)'''
        with self.lock:
            return self.current_position


# Global sliding window classifier
sliding_classifier = SlidingWindowClassifier(SAMPLES_PER_WINDOW, STRIDE_SAMPLES)


class WindowedClassifier(Live_Classifier):
    '''XGBoost binary classifier for relaxed vs fist'''

    def __init__(self):
        model = XGBClassifier(
            eval_metric='mlogloss',
            num_class=2,
            objective='multi:softmax'
        )
        super().__init__(model, name="Fist_Detector", color=(50, 150, 255))

    def classify(self, emg):
        '''Override to handle both single samples and windows'''
        if self.X.shape[0] == 0 or self.model is None:
            return 0

        # Reshape appropriately
        if len(emg) == 8:
            # Single EMG sample
            x = np.array(emg).reshape(1, -1)
        else:
            # Already a flattened window
            x = np.array(emg).reshape(1, -1)

        try:
            pred = self.model.predict(x)
            return int(pred[0])
        except:
            return 0


class WindowedEMGHandler(EMGHandler):
    '''EMG handler that updates the global position tracker'''

    def __call__(self, emg, moving):
        # Store training data if in recording mode
        if self.recording >= 0:
            self.m.cls.store_data(self.recording, emg)

        # Keep for GUI display
        self.emg = emg


# Global position tracker - updated by pose handler
_current_hand_position = 0  # Default to relaxed


def _pose_handler(pose):
    '''Internal handler that updates global hand position'''
    global _current_hand_position
    _current_hand_position = pose

    # Write to file for external server polling
    try:
        with open('hand_position.txt', 'w') as f:
            f.write(str(pose))
    except:
        pass  # Silently fail if file write fails


def get_hand_position():
    '''
    Returns the current hand position based on EMG classification.

    Returns:
        int: 0 = relaxed, 1 = closed fist
    '''
    return _current_hand_position


def run_training_mode():
    '''Run in training mode - collect labeled data'''
    print("=== TRAINING MODE ===")
    print("Press '0' while hand is RELAXED (neutral rest, no tension)")
    print("Press '1' while making a CLOSED FIST (fully clenched)")
    print()
    print("TIP: Hold each pose for 5-6 seconds to collect ~250-300 samples")
    print("TIP: Relax completely between collecting samples")
    print()
    print("Press 'q' to quit and save data")
    print("Press 'e' to erase existing data")

    pygame.init()
    w, h = 800, 320
    scr = pygame.display.set_mode((w, h))
    font = pygame.font.Font(None, 30)

    # Create classifier
    clr = WindowedClassifier()
    m = MyoClassifier(clr, mode=emg_mode.FILTERED, hist_len=6)

    hnd = WindowedEMGHandler(m)
    m.add_emg_handler(hnd)
    m.connect()

    # Set LED color
    m.set_leds(m.cls.color, m.cls.color)
    pygame.display.set_caption(m.cls.name + " - TRAINING MODE")

    try:
        while True:
            try:
                m.run()
            except struct.error:
                # Ignore packet unpack errors in FILTERED mode (known pyomyo issue)
                pass
            m.run_gui(hnd, scr, font, w, h)

    except KeyboardInterrupt:
        pass
    finally:
        try:
            m.disconnect()
        except:
            pass  # Ignore disconnect errors
        print("\nTraining data saved!")
        pygame.quit()


def run_classification_mode():
    '''Run in classification mode - use trained model'''
    print("=== CLASSIFICATION MODE ===")
    print("Model loaded. Call get_hand_position() to get current state.")
    print("0 = Relaxed, 1 = Closed fist")
    print("Press Ctrl+C to quit")

    # Create classifier and load training data
    clr = WindowedClassifier()
    m = MyoClassifier(clr, mode=emg_mode.FILTERED, hist_len=6)  # Reduced for lower latency

    # Add pose handler to track position
    m.add_raw_pose_handler(_pose_handler)

    hnd = WindowedEMGHandler(m)
    m.add_emg_handler(hnd)
    m.connect()

    # Set LED color
    m.set_leds([0, 255, 0], [0, 255, 0])  # Green = ready

    print("\nStarting classification...")
    print("Hand position updates using smoothed predictions (6-sample history @ 200Hz = ~30ms latency)")

    try:
        last_position = -1
        position_names = {0: "RELAXED", 1: "CLOSED FIST"}

        while True:
            try:
                m.run()
            except struct.error:
                # Ignore packet unpack errors in FILTERED mode
                pass

            # Print position when it changes
            current_pos = get_hand_position()
            status = position_names.get(current_pos, "UNKNOWN")
            print(f"Hand position: {current_pos} ({status})")
            # if current_pos != last_position:
            #     status = position_names.get(current_pos, "UNKNOWN")
            #     print(f"Hand position: {current_pos} ({status})")
            #     last_position = current_pos

            time.sleep(0.01)  # Small delay to prevent CPU spinning

    except KeyboardInterrupt:
        pass
    finally:
        m.disconnect()
        print("\nDisconnected.")


def run_classification_mode_with_shared_value(shared_position):
    '''
    Run classification mode with multiprocessing shared value.
    Used when running as a background process.

    Args:
        shared_position: multiprocessing.Value to update with hand position
    '''
    print("=== CLASSIFICATION MODE (Background Process) ===")
    print("Model loaded. Updating shared memory with hand position.")
    print("0 = Relaxed, 1 = Closed fist")

    # Create custom pose handler that updates shared value
    def shared_pose_handler(pose):
        global _current_hand_position
        _current_hand_position = pose
        shared_position.value = pose  # Update shared memory

    # Create classifier and load training data
    clr = WindowedClassifier()
    m = MyoClassifier(clr, mode=emg_mode.FILTERED, hist_len=6)  # Reduced for lower latency

    # Add shared pose handler
    m.add_raw_pose_handler(shared_pose_handler)

    hnd = WindowedEMGHandler(m)
    m.add_emg_handler(hnd)
    m.connect()

    # Set LED color
    m.set_leds([0, 255, 0], [0, 255, 0])  # Green = ready

    print("\nStarting classification...")
    print("Hand position updates using smoothed predictions (6-sample history @ 200Hz = ~30ms latency)")

    try:
        last_position = -1
        position_names = {0: "RELAXED", 1: "CLOSED FIST"}

        while True:
            try:
                m.run()
            except struct.error:
                # Ignore packet unpack errors in FILTERED mode
                pass

            # Print position when it changes (in background process)
            current_pos = get_hand_position()
            status = position_names.get(current_pos, "UNKNOWN")
            print(f"[Classifier] Hand position: {current_pos} ({status})")


            # if current_pos != last_position:
            #     status = position_names.get(current_pos, "UNKNOWN")
            #     print(f"[Classifier] Hand position: {current_pos} ({status})")
            #     last_position = current_pos

            time.sleep(0.01)

    except KeyboardInterrupt:
        pass
    finally:
        m.disconnect()
        print("[Classifier] Disconnected")


if __name__ == '__main__':
    if TRAINING_MODE:
        run_training_mode()
    else:
        run_classification_mode()
