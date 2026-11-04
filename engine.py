"""Sintesi, effetti e clock: tutto gira nel processo Python."""
from __future__ import annotations

import math
import json
import os
import queue
import threading
import time
import wave
from pathlib import Path

import numpy as np

try:
    import sounddevice as sd
except (ImportError, OSError):
    sd = None

RATE = 44100
PAD_COUNT = 16
BPM_MIN = 40
BPM_MAX = 240
SCALE = [0, 3, 5, 7, 10]
DEFAULTS = {
    "volume": .7, "input_level": .5, "sample": .5, "pitch": .5,
    "cutoff": .75, "resonance": .2, "filter_type": 0,
    "lfo_rate": .3, "lfo_depth": 0, "lfo_shape": 0,
    "level": .8, "pan": .5, "attack": 0, "decay": .45,
    "fx_depth": .2, "fx_time": .35, "distortion": 0, "bpm": .4,
    "swing": 0,
}
MENU_FIELDS = [
    ("BPM", "bpm"), ("SWING", "swing"), ("CUTOFF", "cutoff"),
    ("RESONANCE", "resonance"), ("FILTER TYPE", "filter_type"),
    ("LFO RATE", "lfo_rate"), ("LFO DEPTH", "lfo_depth"),
    ("LFO SHAPE", "lfo_shape"), ("LEVEL", "level"),
    ("PAN", "pan"), ("ATTACK", "attack"), ("DECAY", "decay"),
    ("FX DEPTH", "fx_depth"), ("FX TIME", "fx_time"),
]
MENU_INDEX = {key: i for i, (_, key) in enumerate(MENU_FIELDS)}


def bpm_from_value(value: float) -> int:
    return BPM_MIN + math.floor(value * (BPM_MAX - BPM_MIN) + .5)


def value_from_bpm(bpm: int) -> float:
    return (bpm - BPM_MIN) / (BPM_MAX - BPM_MIN)


class Engine:
    def __init__(self, sample_dir: Path) -> None:
        self.sample_dir = sample_dir
        self.pattern_dir = sample_dir.parent / "patterns"
        self.pattern_dir.mkdir(exist_ok=True)
        self.lock = threading.RLock()
        self.values = DEFAULTS.copy()
        self.bpm = 120
        self.step = -1
        self.part = 0
        self.steps = [[False] * 16 for _ in range(16)]
        self.muted = [False] * 16
        self.copy_buffer: list[bool] | None = None
        self.motion_enabled = False
        self.motion: list[dict[str, float]] = [{} for _ in range(16)]
        self.motion_override: dict[str, float] = {}
        self.shift = False
        self.pad_mode = "trigger"
        self.menu_open = False
        self.menu_index = 0
        self.pattern_select = False
        self.pattern_index = 1
        self.selected_pattern = 1
        self.playing = False
        self.recording = False
        self.powered = True
        self.fx_kind = "delay"
        self.mode = "touch_scale"
        self.sequencer = False
        self.hold = False
        self.touch = None
        self.display = ["001  INIT PATTERN", "PART 01  KICK"]
        self.display_until = 0.0
        self.revision = 0
        self.voices: list[dict] = []
        self.audio_listeners: set[queue.Queue[bytes]] = set()
        self.audio_pending: list[np.ndarray] = []
        self.audio_pending_frames = 0
        self.assignments: dict[int, np.ndarray] = {}
        self.assignment_names: dict[int, str] = {}
        self.delay = np.zeros(RATE * 2, dtype=np.float32)
        self.delay_pos = 0
        self.filter_z1 = 0.0
        self.filter_z2 = 0.0
        self.samples_rendered = 0
        self.last_touch_note = -1
        self.last_touch_time = 0.0
        self.last_taps: list[float] = []
        self.running = False
        self.stream = None
        self.audio_error = ""
        self.next_step = 0.0
        self.last_arp = 0.0

    def start(self) -> None:
        self.running = True
        threading.Thread(target=self._clock, daemon=True).start()
        if sd is None:
            self.audio_error = "sounddevice non disponibile"
            return
        try:
            try:
                self.stream = sd.Stream(samplerate=RATE, channels=(1, 2), blocksize=512,
                                        dtype="float32", callback=self._duplex_callback)
                self.input_enabled = True
            except Exception:
                self.stream = sd.OutputStream(samplerate=RATE, channels=2, blocksize=512,
                                              dtype="float32", callback=self._audio_callback)
                self.input_enabled = False
            self.stream.start()
        except Exception as exc:
            self.audio_error = f"Uscita audio non disponibile: {exc}"

    def close(self) -> None:
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()

    def subscribe_audio(self) -> queue.Queue[bytes]:
        """Un flusso PCM stereo indipendente per ogni browser in ascolto."""
        listener: queue.Queue[bytes] = queue.Queue(maxsize=12)
        with self.lock:
            self.audio_listeners.add(listener)
        return listener

    def unsubscribe_audio(self, listener: queue.Queue[bytes]) -> None:
        with self.lock:
            self.audio_listeners.discard(listener)

    def _publish_audio(self, outdata: np.ndarray) -> None:
        if not self.audio_listeners:
            self.audio_pending.clear()
            self.audio_pending_frames = 0
            return
        self.audio_pending.append(outdata.copy())
        self.audio_pending_frames += len(outdata)
        if self.audio_pending_frames < 2048:
            return
        block = np.concatenate(self.audio_pending)
        self.audio_pending.clear()
        self.audio_pending_frames = 0
        pcm = (np.clip(block, -1, 1) * 32767).astype("<i2").tobytes()
        for listener in self.audio_listeners:
            if listener.full():
                try:
                    listener.get_nowait()
                except queue.Empty:
                    pass
            listener.put_nowait(pcm)

    def _show(self, first: str, second: str, seconds: float = 1.2) -> None:
        self.display = [first[:20], second[:20]]
        self.display_until = time.monotonic() + seconds if seconds > 0 else None
        self.revision += 1

    def snapshot(self) -> dict:
        with self.lock:
            if self.display_until and time.monotonic() > self.display_until:
                self.display_until = 0
                self.display = [f"{self.pattern_index:03d}  {self.bpm:03d} BPM", f"PART {self.part+1:02d}  {self._voice_name(self.part)}"]
                self.revision += 1
            return {"type": "state", "revision": self.revision, "bpm": self.bpm,
                    "step": self.step, "part": self.part, "playing": self.playing,
                    "recording": self.recording, "powered": self.powered,
                    "fx_kind": self.fx_kind, "mode": self.mode,
                    "sequencer": self.sequencer, "pad_mode": self.pad_mode,
                    "hold": self.hold, "shift": self.shift,
                    "muted": self.muted[:], "motion_enabled": self.motion_enabled,
                    "menu_open": self.menu_open, "menu_index": self.menu_index,
                    "pattern_select": self.pattern_select,
                    "pattern_index": self.pattern_index,
                    "selected_pattern": self.selected_pattern,
                    "input_enabled": getattr(self, "input_enabled", False),
                    "steps": self.steps[self.part][:], "display": self.display[:],
                    "values": self.values.copy(), "audio_error": self.audio_error}

    def _voice_name(self, index: int) -> str:
        return ("KICK", "SNARE", "HAT", "CLAP")[index % 4]

    def assign_sample(self, index: int, filename: str) -> None:
        if not 0 <= index < PAD_COUNT or Path(filename).name != filename or not filename.lower().endswith(".wav"):
            raise ValueError("Pad o nome WAV non valido")
        path = self.sample_dir / filename
        if not path.is_file():
            raise ValueError("File WAV non trovato in samples/")
        try:
            with wave.open(str(path), "rb") as wav:
                if wav.getcomptype() != "NONE" or wav.getsampwidth() not in (1, 2, 4):
                    raise ValueError("Usa WAV PCM a 8, 16 o 32 bit")
                rate, channels = wav.getframerate(), wav.getnchannels()
                if wav.getnframes() == 0 or wav.getnframes() / rate > 20:
                    raise ValueError("Il WAV deve durare da 0 a 20 secondi")
                raw = wav.readframes(wav.getnframes())
                width = wav.getsampwidth()
        except wave.Error as exc:
            raise ValueError(f"File WAV non valido: {exc}") from exc
        dtype = {1: np.uint8, 2: np.int16, 4: np.int32}[width]
        data = np.frombuffer(raw, dtype=dtype).astype(np.float32)
        data = (data - 128) / 128 if width == 1 else data / float(1 << (width * 8 - 1))
        data = data.reshape(-1, channels).mean(axis=1)
        if rate != RATE:
            positions = np.linspace(0, len(data) - 1, max(1, round(len(data) * RATE / rate)))
            data = np.interp(positions, np.arange(len(data)), data).astype(np.float32)
        with self.lock:
            self.assignments[index] = data
            self.assignment_names[index] = filename
            self._show("SAMPLE ASSIGNED", f"PAD {index+1:02d} {filename[:11]}")

    def handle(self, msg: dict) -> None:
        if not isinstance(msg, dict):
            raise ValueError("Messaggio JSON non valido")
        kind = msg.get("type")
        with self.lock:
            if kind == "knob":
                key = str(msg["id"])
                if key not in self.values:
                    raise ValueError(f"Manopola sconosciuta: {key}")
                value = float(msg["value"])
                if not math.isfinite(value):
                    raise ValueError("Valore non finito")
                self.values[key] = min(1., max(0., value))
                if key == "bpm":
                    self.bpm = bpm_from_value(self.values[key])
                if self.motion_enabled and self.playing and self.step >= 0 and key not in ("volume", "input_level", "bpm", "swing"):
                    self.motion[self.step][key] = self.values[key]
                    self.motion_override[key] = self.values[key]
                shown = f"{self.bpm:03d} BPM" if key == "bpm" else f"{round(self.values[key]*127):03d}"
                self._show(key.replace("_", " ").upper(), shown)
            elif kind == "pad":
                index = int(msg["index"])
                if not 0 <= index < PAD_COUNT:
                    raise ValueError("Indice pad fuori intervallo")
                down = bool(msg.get("down", True))
                if down:
                    if self.pad_mode == "part_select":
                        self.part = index
                        self._show("SELECT PART", f"{self.part+1:02d} {self._voice_name(self.part)}")
                    elif self.sequencer:
                        self.steps[self.part][index] = not self.steps[self.part][index]
                        self._show(f"PART {self.part+1:02d} STEP {index+1:02d}",
                                   "ON" if self.steps[self.part][index] else "OFF")
                    else:
                        velocity = min(1., max(.05, float(msg.get("velocity", 1))))
                        self._trigger(index, velocity)
                        if self.recording and self.playing and self.step >= 0:
                            self.steps[index][self.step] = True
                        self._show(f"PAD {index+1:02d} {self._voice_name(index)}", f"VEL {round(velocity*127):03d}")
            elif kind == "touch":
                down = bool(msg.get("down"))
                x = float(msg.get("x", 0))
                y = float(msg.get("y", 0))
                if not math.isfinite(x) or not math.isfinite(y):
                    raise ValueError("Coordinate touch non finite")
                x = min(1., max(0., x))
                y = min(1., max(0., y))
                was_touching = self.touch is not None
                self.touch = (x, y) if down else (self.touch if self.hold and self.mode == "master_fx" else None)
                if down:
                    if self.mode == "touch_scale":
                        index = min(14, int(x * 15))
                        now = time.monotonic()
                        if index != self.last_touch_note or now - self.last_touch_time > .22:
                            self._note(x, y)
                            self.last_touch_note = index
                            self.last_touch_time = now
                    elif self.mode == "gate_arp":
                        if not was_touching:
                            self.last_arp = 0
                    self._show(f"X {x:.2f}  Y {y:.2f}", self.mode.replace("_", " ").upper(), .4)
                else:
                    self.revision += 1
            elif kind == "button":
                self._button(str(msg["id"]))
            else:
                raise ValueError("Tipo evento sconosciuto")

    def _pattern_path(self, index: int) -> Path:
        return self.pattern_dir / f"pattern_{index:02d}.json"

    def _save_pattern(self, index: int) -> None:
        payload = {
            "version": 1, "steps": self.steps, "muted": self.muted,
            "values": self.values, "fx_kind": self.fx_kind,
            "motion": self.motion, "assignments": self.assignment_names,
        }
        path = self._pattern_path(index)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, path)
        self.pattern_index = index
        self.selected_pattern = index
        self.pattern_select = False
        self.menu_open = False
        self._show(f"PATTERN {index:02d}", "SAVED")

    def _load_pattern(self, index: int) -> None:
        path = self._pattern_path(index)
        if not path.is_file():
            self._show(f"PATTERN {index:02d}", "EMPTY SLOT")
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            steps = data["steps"]
            muted = data["muted"]
            values = data["values"]
            if len(steps) != 16 or any(len(row) != 16 for row in steps) or len(muted) != 16:
                raise ValueError("Dimensioni pattern non valide")
            if not isinstance(values, dict) or any(key not in values or not math.isfinite(float(values[key])) for key in DEFAULTS):
                raise ValueError("Parametri pattern non validi")
            motion = data.get("motion", [{} for _ in range(16)])
            if len(motion) != 16 or any(not isinstance(row, dict) for row in motion):
                raise ValueError("Motion pattern non valida")
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Pattern {index:02d} non leggibile: {exc}") from exc
        self.steps = [[bool(cell) for cell in row] for row in steps]
        self.muted = [bool(cell) for cell in muted]
        self.values = {key: min(1., max(0., float(values[key]))) for key in DEFAULTS}
        self.bpm = bpm_from_value(self.values["bpm"])
        self.fx_kind = data.get("fx_kind") if data.get("fx_kind") in ("delay", "distortion") else "delay"
        self.motion = [{key: min(1., max(0., float(value))) for key, value in row.items()
                        if key in DEFAULTS and isinstance(value, (int, float))} for row in motion]
        self.motion_override.clear()
        self.assignments.clear()
        self.assignment_names.clear()
        missing = 0
        for raw_index, filename in data.get("assignments", {}).items():
            try:
                self.assign_sample(int(raw_index), str(filename))
            except (ValueError, OSError):
                missing += 1
        self.pattern_index = index
        self.selected_pattern = index
        self.pattern_select = False
        self.menu_open = False
        self._show(f"PATTERN {index:02d}", f"LOADED; {missing} WAV MISSING" if missing else "LOADED")

    def _show_menu(self) -> None:
        name, key = MENU_FIELDS[self.menu_index]
        if key == "filter_type":
            value = ("LPF", "HPF", "BPF")[round(self.values[key] * 2)]
        elif key == "lfo_shape":
            value = ("SINE", "TRIANGLE", "SQUARE")[round(self.values[key] * 2)]
        elif key == "bpm":
            value = f"{self.bpm} BPM"
        else:
            value = str(round(self.values[key] * 127))
        self._show(f"{self.menu_index+1:02d}/{len(MENU_FIELDS):02d} {name}", f"VALUE {value}", 0)

    def _show_pattern_select(self) -> None:
        state = "SAVED" if self._pattern_path(self.selected_pattern).is_file() else "EMPTY"
        self._show("SELECT PATTERN", f"{self.selected_pattern:02d} {state}", 0)

    def _move(self, delta: int) -> None:
        if self.pattern_select:
            self.selected_pattern = 1 + (self.selected_pattern - 1 + delta) % 16
            self._show_pattern_select()
            return
        if not self.menu_open:
            self.menu_open = True
        self.menu_index = (self.menu_index + delta) % len(MENU_FIELDS)
        self._show_menu()

    def _adjust(self, direction: int = 1) -> None:
        if self.pattern_select:
            self._move(direction)
            return
        if not self.menu_open:
            self.menu_open = True
        _, key = MENU_FIELDS[self.menu_index]
        step = 1 / (BPM_MAX - BPM_MIN) if key == "bpm" else (.5 if key in ("filter_type", "lfo_shape") else .05)
        self.values[key] = min(1., max(0., self.values[key] + step * direction))
        if key == "bpm":
            self.bpm = bpm_from_value(self.values[key])
        if self.motion_enabled and self.playing and self.step >= 0 and key not in ("bpm", "swing"):
            self.motion[self.step][key] = self.values[key]
            self.motion_override[key] = self.values[key]
        self._show_menu()

    def _button(self, key: str) -> None:
        if key == "power":
            self.powered = not self.powered
            if not self.powered:
                self.voices.clear()
                self.playing = False
                self.step = -1
                self.motion_override.clear()
            self._show("POWER", "ON" if self.powered else "OFF")
        elif key == "play":
            self.playing = not self.playing
            if self.playing:
                self.next_step = time.monotonic()
            else:
                self.step = -1
                self.motion_override.clear()
            self._show("SEQUENCER", "PLAY" if self.playing else "PAUSE")
        elif key == "stop":
            self.playing = False
            self.step = -1
            self.motion_override.clear()
            self._show("SEQUENCER", "STOP")
        elif key == "rec":
            self.recording = not self.recording
            self._show("RECORD", "ON" if self.recording else "OFF")
        elif key == "tap":
            now = time.monotonic()
            self.last_taps = [t for t in self.last_taps if now - t < 3] + [now]
            if len(self.last_taps) > 1:
                gaps = np.diff(self.last_taps[-5:])
                self.bpm = round(min(BPM_MAX, max(BPM_MIN, 60 / float(np.median(gaps)))))
                self.values["bpm"] = value_from_bpm(self.bpm)
            self._show("TAP TEMPO", f"{self.bpm:03d} BPM")
        elif key in ("gate_arp", "touch_scale", "master_fx"):
            self.mode = key
            self.touch = None
            self._show("TOUCH PAD", key.replace("_", " ").upper())
        elif key == "mfx_hold":
            self.hold = not self.hold
            if not self.hold:
                self.touch = None
            self._show("MFX HOLD", "ON" if self.hold else "OFF")
        elif key == "sequencer":
            self.sequencer = not self.sequencer
            self.pad_mode = "sequencer" if self.sequencer else "trigger"
            self._show("PAD MODE", "SEQUENCER" if self.sequencer else "TRIGGER")
        elif key == "trigger":
            self.sequencer = False
            self.pad_mode = "trigger"
            self._show("PAD MODE", "TRIGGER")
        elif key == "shift_mode":
            self.sequencer = False
            self.pad_mode = "trigger" if self.pad_mode == "part_select" else "part_select"
            self._show("PAD MODE", "PART SELECT" if self.pad_mode == "part_select" else "TRIGGER")
        elif key == "fx":
            self.fx_kind = "distortion" if self.fx_kind == "delay" else "delay"
            self._show("INSERT FX", self.fx_kind.upper())
        elif key == "part_mute":
            self.muted[self.part] = not self.muted[self.part]
            self._show(f"PART {self.part+1:02d}", "MUTED" if self.muted[self.part] else "UNMUTED")
        elif key == "part_erase":
            if self.shift:
                self.steps = [[False] * 16 for _ in range(16)]
                self.motion = [{} for _ in range(16)]
                self.motion_override.clear()
                self._show("ALL PARTS", "STEPS ERASED")
            else:
                self.steps[self.part] = [False] * 16
                self._show(f"PART {self.part+1:02d}", "STEPS ERASED")
        elif key == "part_copy":
            self.copy_buffer = self.steps[self.part][:]
            self._show(f"PART {self.part+1:02d}", "STEPS COPIED")
        elif key == "part_paste":
            if self.copy_buffer is None:
                self._show("PASTE", "COPY A PART FIRST")
            else:
                self.steps[self.part] = self.copy_buffer[:]
                self._show(f"PART {self.part+1:02d}", "STEPS PASTED")
        elif key == "motion":
            self.motion_enabled = not self.motion_enabled
            if not self.motion_enabled:
                self.motion_override.clear()
            self._show("MOTION RECORD", "ON" if self.motion_enabled else "OFF")
        elif key == "shift":
            self.shift = not self.shift
            self._show("SHIFT", "ON" if self.shift else "OFF")
        elif key == "write":
            self._save_pattern(self.selected_pattern if self.pattern_select else self.pattern_index)
        elif key == "pattern":
            self.pattern_select = True
            self.menu_open = False
            self.selected_pattern = self.pattern_index
            self._show_pattern_select()
        elif key == "enter":
            if self.pattern_select:
                self._load_pattern(self.selected_pattern)
            elif self.menu_open:
                self.menu_open = False
                self._show("PARAMETER", "CONFIRMED")
            else:
                self.menu_open = True
                self._show_menu()
        elif key == "exit":
            self.pattern_select = False
            self.menu_open = False
            self.shift = False
            self._show("MENU", "CLOSED")
        elif key == "menu":
            self.pattern_select = False
            self.menu_open = not self.menu_open
            if self.menu_open:
                self._show_menu()
            else:
                self._show("MENU", "CLOSED")
        elif key in ("cursor", "cursor_down"):
            self._move(1)
        elif key == "cursor_up":
            self._move(-1)
        elif key == "value":
            self._adjust(-1 if self.shift else 1)
        elif key in ("filter", "mod", "amp"):
            self.pattern_select = False
            self.menu_open = True
            self.menu_index = {"filter": 2, "mod": 5, "amp": 8}[key]
            self._show_menu()
        elif key == "part_prev":
            self.part = (self.part - 1) % 16
            self._show("SELECT PART", f"{self.part+1:02d} {self._voice_name(self.part)}")
        elif key == "part_next":
            self.part = (self.part + 1) % 16
            self._show("SELECT PART", f"{self.part+1:02d} {self._voice_name(self.part)}")
        elif key.startswith("part_") and key[5:].isdigit():
            self.part = int(key[5:]) % 16
            self._show("SELECT PART", f"{self.part+1:02d} {self._voice_name(self.part)}")
        else:
            raise ValueError(f"Pulsante sconosciuto: {key}")

    def _clock(self) -> None:
        while self.running:
            with self.lock:
                now = time.monotonic()
                if self.playing and now >= self.next_step:
                    self.step = (self.step + 1) % 16
                    self.motion_override = self.motion[self.step].copy() if self.motion_enabled else {}
                    for part in range(16):
                        if self.steps[part][self.step] and not self.muted[part]:
                            self._trigger(part, .8)
                    interval = 60 / self.bpm / 4
                    swing = self.values["swing"] * .4
                    self.next_step = now + interval * (1 + (swing if self.step % 2 == 0 else -swing))
                    self.revision += 1
                if self.touch and self.mode == "gate_arp":
                    x, y = self.touch
                    interval = 60 / self.bpm / (2 + round(y * 6))
                    if now - self.last_arp >= interval:
                        self._note(x, .75)
                        self.last_arp = now
            time.sleep(.003)

    def _note(self, x: float, velocity: float) -> None:
        if not self.powered:
            return
        index = min(14, int(x * 15))
        midi = 48 + 12 * (index // 5) + SCALE[index % 5]
        frequency = 440 * 2 ** ((midi - 69) / 12)
        self.voices.append({"kind": "note", "position": 0, "frequency": frequency,
                            "velocity": max(.05, velocity), "index": self.part})

    def _trigger(self, index: int, velocity: float) -> None:
        if not self.powered:
            return
        self.voices.append({"kind": "sample" if index in self.assignments else self._voice_name(index).lower(),
                            "position": 0, "velocity": velocity, "index": index})

    def _duplex_callback(self, indata, outdata, frames, timing, status) -> None:
        self._audio_callback(outdata, frames, timing, status, indata)

    def _audio_callback(self, outdata, frames, _time, status, input_data=None) -> None:
        with self.lock:
            if not self.powered:
                outdata.fill(0)
                self._publish_audio(outdata)
                return
            values = self.values.copy()
            values.update(self.motion_override)
            output = np.zeros(frames, dtype=np.float32)
            if input_data is not None:
                output += np.mean(input_data, axis=1) * values["input_level"] * .5
            remaining = []
            for voice in self.voices:
                pos = voice["position"]
                t = (np.arange(frames) + pos) / RATE
                kind = voice["kind"]
                decay = .08 + values["decay"] * 1.8
                if kind == "sample":
                    data = self.assignments.get(voice["index"])
                    if data is None:
                        continue
                    fragment = np.zeros(frames, dtype=np.float32)
                    n = min(frames, len(data) - pos)
                    if n > 0:
                        fragment[:n] = data[pos:pos+n] * (.2 + values["sample"]*.8)
                    duration = len(data)
                elif kind == "kick":
                    phase = 2*np.pi*(55*t + 110*(1-np.exp(-t*25))/25)
                    fragment = np.sin(phase) * np.exp(-t*10)
                    duration = RATE
                elif kind == "snare":
                    fragment = (np.random.uniform(-1, 1, frames)*.7 + np.sin(2*np.pi*180*t)*.3)*np.exp(-t*16)
                    duration = RATE // 2
                elif kind == "hat":
                    noise = np.random.uniform(-1, 1, frames)
                    fragment = np.r_[noise[0], np.diff(noise)] * .35 * np.exp(-t*36)
                    duration = RATE // 4
                elif kind == "clap":
                    bursts = (np.sin(2*np.pi*32*t) > -.25).astype(float)
                    fragment = np.random.uniform(-1, 1, frames)*bursts*.45*np.exp(-t*19)
                    duration = RATE // 2
                else:
                    attack = .002 + values["attack"] * .4
                    env = np.minimum(1, t/attack) * np.exp(-t / decay)
                    freq = voice["frequency"] * 2 ** ((values["pitch"]-.5)*2)
                    lfo = np.sin(2*np.pi*(.2+values["lfo_rate"]*12)*t)*values["lfo_depth"]*.04
                    fragment = np.sin(2*np.pi*freq*t + lfo) * env
                    duration = int(RATE * min(3, decay * 5))
                output += fragment.astype(np.float32) * voice["velocity"] * .28
                voice["position"] += frames
                if voice["position"] < duration:
                    remaining.append(voice)
            self.voices = remaining
            cutoff = values["cutoff"]
            if self.touch and self.mode == "master_fx":
                cutoff = self.touch[0]
            lfo_phase = (self.samples_rendered / RATE * (.2+values["lfo_rate"]*12)) % 1
            shape = round(values["lfo_shape"]*2)
            lfo_value = (math.sin(2*math.pi*lfo_phase) if shape == 0 else
                         1-4*abs(lfo_phase-.5) if shape == 1 else
                         (1 if lfo_phase < .5 else -1))
            cutoff = min(1., max(0., cutoff + lfo_value*values["lfo_depth"]*.25))
            frequency = min(RATE*.45, 70 + cutoff**2*17000)
            omega = 2*math.pi*frequency/RATE
            cosine, sine = math.cos(omega), math.sin(omega)
            q = .5 + values["resonance"]*9
            alpha = sine/(2*q)
            filter_type = round(values["filter_type"]*2)
            if filter_type == 0:  # LPF
                b0,b1,b2 = (1-cosine)/2, 1-cosine, (1-cosine)/2
            elif filter_type == 1:  # HPF
                b0,b1,b2 = (1+cosine)/2, -(1+cosine), (1+cosine)/2
            else:  # BPF
                b0,b1,b2 = alpha, 0, -alpha
            a0,a1,a2 = 1+alpha,-2*cosine,1-alpha
            b0,b1,b2,a1,a2 = b0/a0,b1/a0,b2/a0,a1/a0,a2/a0
            filtered = np.empty_like(output)
            z1,z2 = self.filter_z1,self.filter_z2
            for i, sample in enumerate(output):
                result = b0*float(sample)+z1
                z1 = b1*float(sample)-a1*result+z2
                z2 = b2*float(sample)-a2*result
                filtered[i] = result
            self.filter_z1,self.filter_z2 = z1,z2
            self.samples_rendered += frames
            signal = filtered
            drive = 1 + (values["fx_depth"] if self.fx_kind == "distortion" else values["distortion"])*12
            signal = np.tanh(signal*drive) / max(1, drive*.35)
            delay_mix = values["fx_depth"]*.5 if self.fx_kind == "delay" else 0
            if self.touch and self.mode == "master_fx":
                delay_mix = self.touch[1]*.7
            delay_length = max(1, int(RATE * (.08 + values["fx_time"]*.65)))
            for i in range(frames):
                delayed = self.delay[(self.delay_pos-delay_length) % len(self.delay)]
                self.delay[self.delay_pos] = signal[i] + delayed*.35
                signal[i] += delayed*delay_mix
                self.delay_pos = (self.delay_pos+1) % len(self.delay)
            signal *= values["volume"] * values["level"]
            pan = values["pan"]
            outdata[:, 0] = signal * math.sqrt(1-pan)
            outdata[:, 1] = signal * math.sqrt(pan)
            self._publish_audio(outdata)
