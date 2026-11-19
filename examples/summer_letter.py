"""示例 2 · 夏日信笺 —— 62 BPM，C 大调。

情绪：下午四点的教室，风扇停了，有人在写信。
极度克制的独奏钢琴，搭配环境音（逐渐停下的风扇声与偶尔的铅笔沙沙声）。
没有打击乐，没有华丽的合成器，只有琴键和纸笔的对话。
"""

from pathlib import Path
import numpy as np

from bgm import hz, render
from bgm.synth import (SR, Track, bandpass, lowpass, piano, reverb, timeline)

BPM = 62
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 16
DUR = BARS * BAR + 4.0

VOICING = {
    "Fmaj7": [41, 57, 60, 65],
    "Em7":   [40, 55, 59, 62],
    "Dm7":   [38, 53, 57, 60],
    "Cmaj7": [36, 52, 55, 59],
}

PROGRESSION = ["Fmaj7", "Em7", "Dm7", "Cmaj7"] * 4

MELODY = [
    # 第一段 (Bar 0-3)
    [(0, 1.5, 69), (1.5, 0.5, 72), (2, 2, 76)],
    [(0, 2, 74), (2.5, 0.5, 72), (3, 1, 71)],
    [(0, 1.5, 69), (1.5, 0.5, 65), (2, 2, 69)],
    [(0, 4, 67)],

    # 第二段 (Bar 4-7)
    [(0, 1.5, 69), (1.5, 0.5, 72), (2, 2, 76)],
    [(0, 2, 79), (2.5, 0.5, 77), (3, 1, 76)],
    [(0, 1.5, 74), (1.5, 0.5, 72), (2, 2, 74)],
    [(0, 4, 72)],

    # 第三段 (Bar 8-11) (情绪微起)
    [(0, 1.5, 81), (1.5, 0.5, 84), (2, 2, 81)],
    [(0, 2, 79), (2, 1, 76), (3, 1, 74)],
    [(0, 1.5, 77), (1.5, 0.5, 76), (2, 2, 74)],
    [(0, 4, 72)],
    
    # 第四段 (Bar 12-15) (渐弱收尾)
    [(0, 2, 69), (2.5, 0.5, 72), (3, 1, 76)],
    [(0, 2, 74), (2, 2, 71)],
    [(0, 2, 69), (2, 2, 65)],
    [(0, 4, 60)],
]

def fan_stopping(dur: float) -> np.ndarray:
    """模拟老旧吊扇慢慢停下的声音"""
    t = timeline(dur)
    f = 15 * np.exp(-t / 3.0)  # 转速逐渐变慢
    amp = np.exp(-t / 4.0)     # 音量逐渐消失
    
    noise = np.random.default_rng(42).standard_normal(len(t))
    # 风声呼啸随转速变化
    blade = lowpass(noise, 400) * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR))
    
    return blade * amp * 0.15

def pencil_scratch(dur: float, seed: int) -> np.ndarray:
    """模拟铅笔在纸上写字的沙沙声"""
    t = timeline(dur)
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(len(t))
    
    scratch = bandpass(noise, 1500, 4500)
    # 模拟书写的顿挫感
    strokes = np.sin(2 * np.pi * rng.uniform(3, 6) * t) ** 2
    env = strokes * np.exp(-t / (dur * 0.6))
    return scratch * env * 0.06

def main(out: Path) -> Path:
    keys = Track(DUR)
    env = Track(DUR)

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    # ---------- 1. 环境音 (Ambience)
    # 歌曲开头：风扇慢慢停下
    env.add(fan_stopping(BAR * 3), at(0, 0), pan_=0.0)
    
    # 偶尔出现的写字声，填补旋律的空白
    write_points = [
        (3, 1.0, 2.0), (7, 1.5, 1.5), (11, 2.0, 1.5), (15, 1.0, 3.0)
    ]
    for i, (bar, beat, dur) in enumerate(write_points):
        env.add(pencil_scratch(dur * BEAT, seed=10+i), at(bar, beat), pan_=0.2)

    # ---------- 2. 钢琴伴奏 (Accompaniment)
    for bar, name in enumerate(PROGRESSION):
        notes = VOICING[name]
        # 左手分解和弦，像缓缓流淌的思绪，力度极轻
        for i, idx in enumerate([0, 1, 2, 3, 2, 1, 2, 3]):
            if bar == BARS - 1 and i > 0:
                break # 最后一小节只弹一个根音
            m = notes[idx % len(notes)] + (12 if idx >= len(notes) else 0)
            # 轻微的错位增加人情味
            offset = np.random.default_rng(bar * 8 + i).uniform(-0.02, 0.02)
            keys.add(piano(hz(m), BEAT * 1.5, vel=0.35), at(bar, i * 0.5) + offset, gain=0.35, pan_=-0.1)

    # ---------- 3. 钢琴旋律 (Melody)
    for bar, phrase in enumerate(MELODY):
        for beat, dur, m in phrase:
            offset = np.random.default_rng(bar * 10 + int(beat)).uniform(-0.015, 0.03)
            note = piano(hz(m), dur * BEAT * 1.2, vel=0.45)
            keys.add(note, at(bar, beat) + offset, gain=0.45, pan_=0.1)

    # ---------- 4. 总线混音
    # 给钢琴加上低通滤波器，模拟毛毡钢琴（Felt Piano）温暖闷沉的听感
    warm_keys = lowpass(keys.buf, 1800)
    
    # 极具空间感的房间混响，但不要太大，保持私密感
    piano_bus = reverb(warm_keys, dur=2.5, mix=0.25, damp=3000)
    env_bus = reverb(env.buf, dur=1.5, mix=0.1, damp=6000)

    mix = piano_bus + env_bus
    
    # 压一点底噪，模拟旧磁带或安静房间的空气声
    air_noise = np.random.default_rng(99).standard_normal(mix.shape)
    mix += lowpass(air_noise, 800) * 0.001
    
    return render(out / "02_summer_letter.wav", mix, fade=(0.02, 4.0))

if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
