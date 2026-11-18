"""音名、音阶、和弦与节奏的小工具。

用 midi 编号作为内部统一表示：C4 = 60，A4 = 69，频率按十二平均律换算。
"""

from __future__ import annotations

import numpy as np

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_PITCH_CLASS = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

# 和弦配方（相对根音的半音数）
CHORDS = {
    "maj": (0, 4, 7),
    "min": (0, 3, 7),
    "maj7": (0, 4, 7, 11),
    "min7": (0, 3, 7, 10),
    "dom7": (0, 4, 7, 10),
    "min9": (0, 3, 7, 10, 14),
    "add9": (0, 4, 7, 14),
    "sus2": (0, 2, 7),
    "sus4": (0, 5, 7),
    "dim": (0, 3, 6),
    "aug": (0, 4, 8),
}

SCALES = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "pentatonic_major": (0, 2, 4, 7, 9),
    "pentatonic_minor": (0, 3, 5, 7, 10),
}


def _pitch_class(name: str) -> int:
    pc = _PITCH_CLASS[name[0].upper()]
    for ch in name[1:]:
        if ch == "#":
            pc += 1
        elif ch in ("b", "B"):
            pc -= 1
        else:
            break
    return pc % 12


def midi(name) -> int:
    """把 "C#4" / "Db3" / "A4" 这样的音名转成 midi 编号。"""
    if isinstance(name, (int, np.integer)):
        return int(name)
    name = name.strip()
    i = 1
    while i < len(name) and name[i] in "#b":
        i += 1
    pc = _pitch_class(name)
    octave = int(name[i:])
    return 12 * (octave + 1) + pc


def hz(m) -> float:
    """midi 编号 -> 频率（A4 = 440Hz）。"""
    return 440.0 * 2.0 ** ((midi(m) - 69) / 12.0)


def chord(root: str, quality: str = "maj", octave: int = 3,
          inversion: int = 0) -> list[int]:
    """返回和弦的 midi 列表，例如 chord("C", "maj7", 3) -> [48, 52, 55, 59]。"""
    root = root.strip()
    if any(ch.isdigit() for ch in root):
        base = midi(root)
    else:
        base = 12 * (octave + 1) + _pitch_class(root)

    notes = [base + step for step in CHORDS[quality]]
    for _ in range(inversion % len(notes)):
        notes.append(notes.pop(0) + 12)
    return notes


def scale(root: str, name: str = "major", octave: int = 4, octaves: int = 1) -> list[int]:
    """返回音阶上的 midi 列表（包含高八度的收尾音）。"""
    base = 12 * (octave + 1) + _pitch_class(root)
    steps = SCALES[name]
    notes = []
    for o in range(octaves):
        notes.extend(base + o * 12 + s for s in steps)
    notes.append(base + octaves * 12)
    return notes


def beat_seconds(bpm: float, beats: float = 1.0) -> float:
    """一拍的秒数。"""
    return 60.0 / bpm * beats


def swing_offset(bpm: float, ratio: float = 0.62) -> float:
    """反拍相对正拍的延迟（秒），用来做 Lo-Fi 的摇摆感。"""
    return (ratio - 0.5) * beat_seconds(bpm)


def voice(notes: list[int], octave_shift: int = 0) -> list[int]:
    return [n + 12 * octave_shift for n in notes]
