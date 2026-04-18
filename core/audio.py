import soundfile as sf
import numpy as np
from scipy.signal import butter, lfilter
def process_audio_file(in_wav, out_wav, is_decrypt=False, carrier_freq=8000):
    try:
        y, sr = sf.read(in_wav)
        if len(y.shape) > 1:
            y_mono = np.mean(y, axis=1)
        else:
            y_mono = y
        t = np.arange(len(y_mono)) / sr
        carrier = np.cos(2 * np.pi * carrier_freq * t)
        processed = y_mono * carrier
        if is_decrypt:
            nyquist = 0.5 * sr
            cutoff = min(carrier_freq, nyquist * 0.9)
            b, a = butter(5, cutoff / nyquist, btype='low')
            processed = lfilter(b, a, processed) * 2.0
        out_audio = np.vstack((processed, processed)).T
        sf.write(out_wav, out_audio, sr)
        return True
    except Exception as e:
        print("Audio Error:", e)
        return False