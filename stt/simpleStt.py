# stt/sttApp.py
#================================================================
# STT App
# Two-stage: wake word detection -> active transcription
# Sends transcribed text via FakeIpc
#================================================================
import time
import struct
import subprocess
import numpy as np
import threading
import pyaudio

#=================================================================
# Configuration
#=================================================================
RATE = 16000
CHUNK = 1600                    # 100ms frames
WAKE_WORDS = {"next song."}
SILENCE_TIMEOUT = 1.5           # seconds of silence = end of utterance
ACTIVE_TIMEOUT = 10.0           # max listen window
WAKE_CHECK_INTERVAL = 1.0       # check wake word every 1s
RMS_THRESHOLD = 600             # tune to servo noise floor

WHISPER_BIN             = "/path/to/whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL           = "/path/to/models/ggml-base.en.bin"
PYAUDIO_DEVICE_INDEX    = 2
WHISPER_THREADS         = 2

#=================================================================
# STT Manager
#=================================================================
class SimpleStt:

    def __init__(self, whisper_bin=WHISPER_BIN, model_path=WHISPER_MODEL, threads=WHISPER_THREADS):
        print("CTOR STT Manager")
        self.whisper_bin = whisper_bin
        self.model_path = model_path
        self.threads = threads
        self._state = "IDLE"
        self._processing = False

        self._wake_buf = bytearray()
        self._speech_buf = bytearray()
        self._last_voice = 0
        self._active_start = 0

        self._pa = pyaudio.PyAudio()
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=RATE,
            input=True,
            input_device_index=PYAUDIO_DEVICE_INDEX,
            frames_per_buffer=CHUNK
        )

        self._stop = threading.Event()
        self._listener = threading.Thread(target=self._listen_loop, daemon=True)
        self._listener.start()

    def _rms(self, data):
        s = np.frombuffer(data, dtype=np.int16).astype(np.float32)
        return np.sqrt(np.mean(s ** 2))

    def _write_wav(self, pcm, path="/tmp/_stt.wav"):
        with open(path, "wb") as f:
            n = len(pcm)
            f.write(b"RIFF")
            f.write(struct.pack("<I", 36 + n))
            f.write(b"WAVEfmt ")
            f.write(struct.pack("<IHHIIHH", 16, 1, 1, RATE, RATE * 2, 2, 16))
            f.write(b"data")
            f.write(struct.pack("<I", n))
            f.write(pcm)

    def transcribe(self, pcm_bytes):

        self._processing = True
        self._write_wav(pcm_bytes)
        result = subprocess.run(
            [self.whisper_bin,
             "-m", self.model_path,
             "-f", "/tmp/_stt.wav",
             "--no-timestamps",
             "-t", str(self.threads),
             "--no-prints"],
            capture_output=True, text=True, timeout=30
        )
        self._processing = False
        return result.stdout.strip().lower()

    def _listen_loop(self):
        print("STT: IDLE - listening for wake word")

        while not self._stop.is_set():
            data = self._stream.read(CHUNK, exception_on_overflow=False)
            rms = self._rms(data)
            now = time.monotonic()

            if self._state == "IDLE":
                if rms > RMS_THRESHOLD:
                    if len(self._wake_buf) == 0:
                        print(f"STT: voice start rms={rms:.0f}")
                    self._wake_buf.extend(data)
                    self._last_voice = now
                elif len(self._wake_buf) > 0:
                    # Keep buffering for a bit after voice stops
                    if now - self._last_voice < 1.0:
                        self._wake_buf.extend(data)
                    else:
                        self._wake_buf.clear()

                if len(self._wake_buf) >= RATE * 2 * WAKE_CHECK_INTERVAL:
                    text = self.transcribe(bytes(self._wake_buf))
                    print(f"STT: wake check got '{text}'")
                    self._wake_buf.clear()

                    if any(w in text for w in WAKE_WORDS):
                        print(f"STT: WAKE detected!")
                        self._state = "ACTIVE"
                        self._active_start = now
                        self._last_voice = now
                        self._speech_buf.clear()
                        if hasattr(self, '_on_wake') and self._on_wake:
                            self._on_wake()

            elif self._state == "ACTIVE":
                self._speech_buf.extend(data)

                if rms > RMS_THRESHOLD:
                    self._last_voice = now

                timed_out = (now - self._active_start) > ACTIVE_TIMEOUT
                silence_ended = (now - self._last_voice) > SILENCE_TIMEOUT and len(self._speech_buf) > RATE * 2 * 0.5

                if timed_out or silence_ended:
                    if len(self._speech_buf) > RATE * 2 * 0.3:
                        text = self.transcribe(bytes(self._speech_buf))
                        if text and hasattr(self, '_on_speech') and self._on_speech:
                            self._on_speech(text)

                    self._speech_buf.clear()
                    self._wake_buf.clear()
                    self._state = "IDLE"
                    print("STT: IDLE - listening for wake word")

    def close(self):
        self._stop.set()
        self._listener.join(timeout=2.0)
        self._stream.stop_stream()
        self._stream.close()
        self._pa.terminate()
        print("STT: closed")