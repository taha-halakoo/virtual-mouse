import math
import threading
import numpy as np
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

def smoothing_factor(t_e, cutoff):
    r = 2 * math.pi * cutoff * t_e
    return r / (r + 1)

def exponential_smoothing(a, x, x_prev):
    return a * x + (1 - a) * x_prev

class AcousticEnvironmentSync:
    """
    Feature 5: Acoustic Environment Syncing
    Listens to microphone to detect typing or high-frequency vibrations
    and dynamically outputs a jitter penalty to the One-Euro filter.
    """
    def __init__(self, enabled=False):
        self.enabled = enabled and HAS_PYAUDIO
        self.jitter_penalty = 0.0
        self._running = False
        self._thread = None
        if self.enabled:
            self.start()

    def start(self):
        if not self.enabled or self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _listen_loop(self):
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        
        p = pyaudio.PyAudio()
        try:
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            while self._running:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    np_data = np.frombuffer(data, dtype=np.int16)
                    rms = np.sqrt(np.mean(np_data.astype(np.float32)**2))
                    
                    # If room noise (like typing) is loud, increase the penalty (lowers beta/responsiveness to kill jitter)
                    if rms > 500:
                        self.jitter_penalty = min(0.5, (rms - 500) / 20000.0)
                    else:
                        self.jitter_penalty = max(0.0, self.jitter_penalty - 0.05)
                except Exception:
                    pass
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
        finally:
            p.terminate()

class OneEuroFilter:
    def __init__(self, mincutoff=1.0, beta=0.0, dcutoff=1.0, parkinsons_assist=False, acoustic_sync=None):
        self.mincutoff = mincutoff
        self.beta = beta
        self.dcutoff = dcutoff
        self.x_prev = None
        self.dx_prev = None
        self.t_prev = None
        
        # Feature 44: Parkinson's Assist Mode
        self.parkinsons_assist = parkinsons_assist
        if self.parkinsons_assist:
            # Extreme low pass for rhythmic tremors
            self.mincutoff = 0.001
            self.beta = 0.005 

        self.acoustic_sync = acoustic_sync

    def __call__(self, t, x):
        if self.t_prev is None:
            self.x_prev = x
            self.dx_prev = 0.0
            self.t_prev = t
            return x

        t_e = t - self.t_prev
        if t_e <= 0.0:
            return x

        a_d = smoothing_factor(t_e, self.dcutoff)
        dx = (x - self.x_prev) / t_e
        dx_hat = exponential_smoothing(a_d, dx, self.dx_prev)

        # Apply acoustic penalty if active (reduces beta to increase smoothing during noise/typing)
        effective_beta = self.beta
        if self.acoustic_sync and self.acoustic_sync.enabled:
            effective_beta = max(0.0, self.beta - self.acoustic_sync.jitter_penalty)

        # Feature 8: Subconscious Tremor Profiling (Dynamic cutoff manipulation)
        cutoff = self.mincutoff + effective_beta * abs(dx_hat)
        
        a = smoothing_factor(t_e, cutoff)
        x_hat = exponential_smoothing(a, x, self.x_prev)

        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t

        return x_hat
