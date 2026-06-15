import wave
import struct
import math
import os
import platform
import subprocess

class SoundManager:
    def __init__(self, folder="sounds"):
        self.folder = folder
        os.makedirs(folder, exist_ok=True)
        self.files = {
            "move": os.path.join(folder, "move.wav"),
            "eat": os.path.join(folder, "eat.wav"),
            "wall": os.path.join(folder, "wall.wav"),
            "gameover": os.path.join(folder, "gameover.wav")
        }
        self._generate_sounds()

    def _generate_sine(self, filename, freq, duration, volume=0.4):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = []
        for i in range(n_samples):
            val = int(32767 * volume * math.sin(2 * math.pi * freq * i / sample_rate))
            buf.append(struct.pack('<h', val))
        with wave.open(filename, 'wb') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sample_rate)
            f.writeframes(b''.join(buf))

    def _generate_sounds(self):
        if not os.path.exists(self.files["move"]):
            self._generate_sine(self.files["move"], 350, 0.03, 0.2)  # Короткий щелчок
        if not os.path.exists(self.files["eat"]):
            self._generate_sine(self.files["eat"], 700, 0.15, 0.5)  # Приятный "пик"
        if not os.path.exists(self.files["wall"]):
            self._generate_sine(self.files["wall"], 120, 0.3, 0.6)  # Низкий гул
        if not os.path.exists(self.files["gameover"]):
            self._generate_sine(self.files["gameover"], 250, 0.6, 0.5)  # Затухающий тон

    def play(self, event_type):
        if event_type not in self.files: return
        file = self.files[event_type]
        sys = platform.system()
        try:
            if sys == "Windows":
                import winsound
                winsound.PlaySound(file, winsound.SND_ASYNC | winsound.SND_FILENAME)
            elif sys == "Darwin":
                subprocess.Popen(["afplay", file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif sys == "Linux":
                subprocess.Popen(["aplay", "-q", file], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                print(f"[Sound] {event_type} (fallback)")
        except Exception:
            pass  # Тихий фоллбэк, если аудиоподсистема недоступна