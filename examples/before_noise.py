"""示例 4 · 白噪音之前 —— 氛围环境音，无明显 BPM。

情绪：早上六点，房间还没醒。
没有鼓，没有清晰的旋律。极慢的低通合成器 Pad 模拟天光渐亮。
深沉的持续低频（Drone）像大楼的呼吸。
偶尔传来的几声清脆金属声（像远处的风铃或风吹过的窗框）。
环境里充满了房间底噪（Room Tone）和轻微的低频隆隆声。
"""

from pathlib import Path
import numpy as np

from bgm import hz, render
from bgm.synth import (SR, Track, bell, highpass, lowpass, pad, reverb, samples, timeline)

# 总长 60 秒
DUR = 60.0

# 极简的和声进行（只有根音、五音和九音，避免色彩过于浓烈），换得很慢
CHORDS = [
    (0.0,  [37, 44, 49]), # Db2, Ab2, Db3
    (15.0, [39, 46, 51]), # Eb2, Bb2, Eb3
    (30.0, [42, 49, 54]), # Gb2, Db3, Gb3
    (45.0, [37, 44, 49]), # 回到 Db2
]

# 散落的金属风铃声 (时间, MIDI)
BELLS = [
    (8.2, 73), (11.5, 80), (14.0, 75),
    (24.3, 77), (28.1, 75), 
    (36.5, 82), (39.0, 85), (42.2, 80),
    (52.1, 73), (56.0, 68)
]

def room_tone(dur: float) -> np.ndarray:
    """模拟绝对安静房间里空气的流动底噪"""
    t = timeline(dur)
    noise = np.random.default_rng(99).standard_normal(len(t))
    # 极低频的建筑物/管道共振 (Rumble)
    rumble = lowpass(noise, 60) * 0.4
    # 空气嘶沙声
    hiss = lowpass(highpass(noise, 800), 3000) * 0.05
    # 呼吸感包络
    breath = 0.7 + 0.3 * np.sin(2 * np.pi * 0.04 * t)
    return (rumble + hiss) * breath

def main(out: Path) -> Path:
    pads = Track(DUR)
    bells = Track(DUR)
    env = Track(DUR)

    # ---------- 1. 房间底噪 (Room Tone)
    env.add(room_tone(DUR), 0.0, gain=0.6, pan_=0.0)

    # ---------- 2. 像天光一样的极慢 Pad
    for i, (start_time, notes) in enumerate(CHORDS):
        # 每一段长达 18 秒，与下一段交叠
        section_dur = 18.0
        # 随着时间推移，低通滤波器（天光）慢慢打开
        progress = start_time / DUR
        cutoff = 200 + 400 * progress 
        
        for j, m in enumerate(notes):
            # 极长的 Attack 和 Release，像雾气一样涌入涌出
            p = pad(hz(m), section_dur, voices=2, detune=0.003, cutoff=cutoff, attack=4.0)
            pads.add(p, start_time, gain=0.12, pan_=(-0.3 + 0.3 * j))

    # ---------- 3. 远处的金属风铃 (Bells)
    for start, m in BELLS:
        # 风铃声不需要很长，但要有清脆感
        b = bell(hz(m), 3.0)
        bells.add(b, start, gain=0.1, pan_=(-0.4 if m % 2 == 0 else 0.4))

    # ---------- 4. 混音总线
    # 氛围音乐（Ambient）需要极大、极宽的空间混响
    pad_bus = reverb(pads.buf, dur=8.0, mix=0.6, damp=2000)
    bell_bus = reverb(bells.buf, dur=5.0, mix=0.4, damp=6000)
    
    # 混合，再整体切掉一点刺耳的高频，保持清晨的柔和
    mix = pad_bus + bell_bus + env.buf
    mix = lowpass(mix, 8000)
    
    return render(out / "04_before_noise.wav", mix, fade=(2.0, 5.0))

if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
