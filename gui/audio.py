"""
audio.py  --  sons et musique du jeu
Tous les sons sont générés par code (style 8-bit). Pour utiliser tes propres sons,
dépose des fichiers dans assets/sounds/ : music click move push target bump undo ding win
(.wav, .ogg ou .mp3). Sans carte son, le jeu fonctionne sans son.
"""
import array
import os
import random
import threading

import pygame

SFX_VOLUME = 0.55
MUSIC_VOLUME = 0.30
EXTENSIONS = (".wav", ".ogg", ".mp3")

_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def note_freq(name):
    """'C6' -> 1046.5 Hz   (La4 = 440 Hz)"""
    n = _SEMITONES[name[0]] - 9 + 12 * (int(name[1:]) - 4)
    return 440.0 * 2 ** (n / 12)


def tone(rate, f0, dur, wave="square", vol=0.3, f1=None, duty=0.5, decay=True):
    n = max(1, int(rate * dur))
    out, phase = [], 0.0
    attack = max(1.0, rate * 0.003)
    for i in range(n):
        k = i / n
        f = f0 if f1 is None else f0 + (f1 - f0) * k
        phase += f / rate
        p = phase % 1.0
        if wave == "square":
            s = 1.0 if p < duty else -1.0
        elif wave == "triangle":
            s = 4 * abs(p - 0.5) - 1
        else:
            s = random.uniform(-1, 1)
        env = min(1.0, i / attack) * ((1 - k) if decay else (1.0 if k < 0.85 else (1 - k) / 0.15))
        out.append(s * vol * env)
    return out


def mix(*tracks):
    out = [0.0] * max(len(t) for t in tracks)
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return out


def concat(*tracks):
    out = []
    for t in tracks:
        out.extend(t)
    return out


def to_bytes(samples, channels=1):
    data = array.array("h")
    for s in samples:
        v = int(max(-1.0, min(1.0, s)) * 32767)
        data.append(v)
        if channels == 2:
            data.append(v)
    return data.tobytes()


def build_sfx(rate):
    f = note_freq
    return {
        "click": tone(rate, 880, 0.05, "square", 0.25, f1=1320),
        "move": tone(rate, 300, 0.035, "triangle", 0.30, f1=200),
        "push": mix(tone(rate, 170, 0.09, "square", 0.30, f1=90, duty=0.25),
                    tone(rate, 1, 0.05, "noise", 0.12)),
        "target": concat(tone(rate, f("C6"), 0.06, "square", 0.22),
                         tone(rate, f("E6"), 0.06, "square", 0.22),
                         tone(rate, f("G6"), 0.06, "square", 0.22),
                         tone(rate, f("C7"), 0.16, "square", 0.22)),
        "bump": tone(rate, 120, 0.09, "square", 0.25, f1=80, duty=0.25),
        "undo": concat(tone(rate, 660, 0.05, "square", 0.22),
                       tone(rate, 440, 0.08, "square", 0.22)),
        "ding": concat(tone(rate, f("C6"), 0.08, "square", 0.2),
                       tone(rate, f("G6"), 0.18, "square", 0.2)),
        "win": concat(tone(rate, f("C5"), 0.12, "square", 0.22),
                      tone(rate, f("E5"), 0.12, "square", 0.22),
                      tone(rate, f("G5"), 0.12, "square", 0.22),
                      tone(rate, f("C6"), 0.14, "square", 0.22),
                      mix(tone(rate, f("C6"), 0.7, "triangle", 0.22),
                          tone(rate, f("E6"), 0.7, "square", 0.10),
                          tone(rate, f("G6"), 0.7, "square", 0.10))),
    }


MELODY = [
    "E5 G5 C6 G5 E5 G5 A5 G5",
    "E5 A5 C6 A5 E5 A5 G5 E5",
    "F5 A5 C6 A5 F5 A5 G5 F5",
    "D5 G5 B5 G5 D5 G5 A5 B5",
    "E5 G5 C6 E6 C6 G5 E5 G5",
    "E5 A5 C6 A5 E5 C6 B5 A5",
    "F5 A5 C6 F6 C6 A5 F5 A5",
    "G5 B5 D6 B5 G5 D5 G5 -",
]
BASS = ["C3", "A2", "F2", "G2"] * 2


def build_music(rate, bpm=112):
    eighth = 60.0 / bpm / 2
    bar_len = int(rate * eighth * 8)
    buf = [0.0] * (bar_len * len(MELODY))
    for bar, (line, bass) in enumerate(zip(MELODY, BASS)):
        base = bar * bar_len
        for i, name in enumerate(line.split()):
            if name == "-":
                continue
            start = base + int(rate * eighth * i)
            for j, v in enumerate(tone(rate, note_freq(name), eighth * 0.95, "square",
                                       0.10, duty=0.25)):
                buf[start + j] += v
        for beat in range(4):
            start = base + int(rate * eighth * 2 * beat)
            for j, v in enumerate(tone(rate, note_freq(bass), eighth * 1.9, "triangle", 0.22)):
                buf[start + j] += v
    return buf


class Audio:
    NAMES = ("click", "move", "push", "target", "bump", "undo", "ding", "win")

    def __init__(self, sound_dir):
        self.dir = sound_dir
        self.enabled = False
        self.muted = False
        self.sounds = {}
        self.music = None
        self.music_file = False
        self._music_data = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            self.rate, fmt, self.channels = pygame.mixer.get_init()
            self.can_synth = fmt == -16
            self.enabled = True
        except pygame.error:
            return
        self._load_sfx()
        self._start_music()

    def _find_file(self, name):
        for ext in EXTENSIONS:
            path = os.path.join(self.dir, name + ext)
            if os.path.exists(path):
                return path
        return None

    def _load_sfx(self):
        synth = build_sfx(self.rate) if self.can_synth else {}
        for name in self.NAMES:
            sound = None
            path = self._find_file(name)
            if path:
                try:
                    sound = pygame.mixer.Sound(path)
                except pygame.error:
                    sound = None
            if sound is None and name in synth:
                sound = pygame.mixer.Sound(buffer=to_bytes(synth[name], self.channels))
            if sound is not None:
                sound.set_volume(SFX_VOLUME)
                self.sounds[name] = sound

    def _start_music(self):
        path = self._find_file("music")
        if path:
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play(-1)
                self.music_file = True
                self._apply_volume()
                return
            except pygame.error:
                pass
        if self.can_synth:
            def work():
                self._music_data = to_bytes(build_music(self.rate), self.channels)
            threading.Thread(target=work, daemon=True).start()

    def update(self):
        if self.enabled and self._music_data is not None and self.music is None:
            self.music = pygame.mixer.Sound(buffer=self._music_data)
            self._music_data = None
            self._apply_volume()
            self.music.play(loops=-1)

    def play(self, name):
        if self.enabled and not self.muted and name in self.sounds:
            self.sounds[name].play()

    def toggle(self):
        self.muted = not self.muted
        self._apply_volume()
        return self.muted

    def _apply_volume(self):
        volume = 0.0 if self.muted else MUSIC_VOLUME
        if self.music is not None:
            self.music.set_volume(volume)
        if self.music_file:
            pygame.mixer.music.set_volume(volume)