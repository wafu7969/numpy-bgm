"""示例 10 战鼓 ——

情绪：大鼓与排鼓层层叠加，像鼓声从远处逼近，适合开场、运动、宣传片。
通过空间混响的干湿比调整、低通滤波的逐渐打开，以及各频段鼓组的依次加入，
营造出极其明显的“从远到近”、“从小到大”的逼近感与压迫感。

### 核心编曲与声音设计
1. “逼近感”的空间混响魔法 (Reverb & LPF)：
   - 全曲被划分为 4 个推进阶段。随着小节推移，混响的“湿声”比例从 40% 压缩到了 15%。
   - 同时，所有鼓声挂了一个动态低通滤波器 (LPF)，频段被逐渐撕开，最终达到全频段无损爆发。
2. 极具层次的战鼓方阵 (Layering)：
   - 设计了 big（底盘大鼓）、mid（中频排鼓）、high（高频排鼓）三个频段的太鼓音色，配合鼓边敲击声（Rim），形成类似军队行进的行军节奏。
3. 毁天灭地的贴脸爆发 (Climax & Outro)：
   - 歌曲最后 8 小节，加入极其暴力的连续低音滚奏（Roll）和撕裂空气的镲片（Crash）与大锣（Gong）。混音总线刻意增加了过载（Drive）软削波，产生震撼的轰鸣效果。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import (SR, Track, bandpass, crash, gong, lowpass, pad, reverb, swirl,
                       taiko, timeline)

BPM = 116
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 32
DUR = BARS * BAR + 6.0

# 三面鼓按 D–G–D 调音，形成低、中、高三个声部
TUNE = {"big": 50.0, "mid": 75.0, "high": 112.0}
DECAY = {"big": 1.2, "mid": 0.8, "high": 0.4}

CHORDS = {
    "Dm": [50, 57, 62],
    "Bb": [46, 53, 58],
    "F": [41, 48, 53],
    "C": [48, 55, 60],
}
PROGRESSION = ["Dm", "Bb", "F", "C"] * 8

def main(out: Path) -> Path:
    drums = Track(DUR)
    air = Track(DUR)

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    def hit(kind: str, bar: int, beat: float, gain: float, pan_: float = 0.0, lpf: float = 20000) -> None:
        note = taiko(TUNE[kind], dur=DECAY[kind] * 3.2, decay=DECAY[kind],
                     skin=0.5 if kind == "big" else 0.4,
                     seed=int(bar * 20 + beat * 7))
        if lpf < 20000:
            note = lowpass(note, lpf)
        drums.add(note, at(bar, beat), gain=gain, pan_=pan_)

    def rim(bar: int, beat: float, gain: float, lpf: float = 20000) -> None:
        t = timeline(0.10)
        noise = bandpass(np.random.default_rng(int(bar * 17 + beat * 11)).standard_normal(len(t)),
                         700, 3500)
        click = np.sin(2 * np.pi * 1250 * t) * np.exp(-t / 0.012)
        wood = (click + 0.7 * noise * np.exp(-t / 0.006))
        wood = wood / (np.max(np.abs(wood)) + 1e-9)
        if lpf < 20000:
            wood = lowpass(wood, lpf)
        drums.add(wood, at(bar, beat), gain=gain, pan_=0.35)

    def roll(bar: int, start: float, step: float, count: int, gain0: float,
             gain1: float, kind: str = "big", lpf: float = 20000) -> None:
        for k in range(count):
            g = gain0 + (gain1 - gain0) * k / max(count - 1, 1)
            hit(kind, bar, start + k * step, g, pan_=-0.15 + 0.3 * (k % 2), lpf=lpf)

    # 核心设计：随着小节推进，逐渐拉大音量并打开低通滤波器，制造“逼近感”
    # Stage 1: 0-7 (远处的沉闷)
    # Stage 2: 8-15 (中距离的行进)
    # Stage 3: 16-23 (近在咫尺)
    # Stage 4: 24-31 (贴脸爆发)
    
    for bar in range(BARS):
        # 动态计算当前的距离感参数
        progress = bar / BARS
        lpf_freq = 400 + 8000 * (progress ** 1.5)  # 频段从极其沉闷到打开
        vol_scale = 0.3 + 0.7 * (progress ** 1.2)  # 音量从远到近
        
        # 基础节奏框架
        # 大鼓底盘
        hit("big", bar, 0.0, 0.8 * vol_scale, lpf=lpf_freq)
        hit("big", bar, 2.0, 0.6 * vol_scale, lpf=lpf_freq)
        
        if bar >= 4:
            # 鼓边加入
            rim(bar, 1.0, 0.12 * vol_scale, lpf=lpf_freq)
            rim(bar, 3.0, 0.12 * vol_scale, lpf=lpf_freq)

        if bar >= 8:
            # 中高鼓组加入，形成行军节奏
            hit("mid", bar, 0.75, 0.4 * vol_scale, pan_=-0.2, lpf=lpf_freq)
            hit("high", bar, 1.25, 0.3 * vol_scale, pan_=0.2, lpf=lpf_freq)
            hit("mid", bar, 2.75, 0.4 * vol_scale, pan_=-0.2, lpf=lpf_freq)
            hit("high", bar, 3.25, 0.3 * vol_scale, pan_=0.2, lpf=lpf_freq)
            
            # 过门滚奏
            if bar % 4 == 3:
                roll(bar, 3.0, 0.25, 4, 0.3 * vol_scale, 0.6 * vol_scale, "mid", lpf=lpf_freq)

        if bar >= 16:
            # 节奏加密，层层叠加
            hit("big", bar, 1.5, 0.5 * vol_scale, lpf=lpf_freq)
            hit("big", bar, 3.5, 0.5 * vol_scale, lpf=lpf_freq)
            for k in range(4):
                rim(bar, 1.75 + k * 0.25, (0.05 + 0.01 * k) * vol_scale, lpf=lpf_freq)
                
            if bar % 4 == 0:
                drums.add(crash(dur=1.4), at(bar), gain=0.1 * vol_scale)
                drums.add(gong(tune=68, dur=6.0), at(bar), gain=0.3 * vol_scale, pan_=0.0)

        if bar >= 24:
            # 贴脸的高潮，全编制齐奏
            hit("mid", bar, 0.0, 0.5 * vol_scale, pan_=-0.1, lpf=lpf_freq)
            hit("high", bar, 0.0, 0.4 * vol_scale, pan_=0.1, lpf=lpf_freq)
            
            # 持续的低音轰炸
            roll(bar, 2.5, 0.25, 6, 0.4 * vol_scale, 0.8 * vol_scale, "big", lpf=lpf_freq)

    # ---------- 最后的终结一击
    drums.add(crash(dur=3.0), at(BARS), gain=0.25)
    drums.add(gong(tune=55, dur=10.0), at(BARS), gain=0.45)
    hit("big", BARS, 0.0, 1.0)
    hit("mid", BARS, 0.0, 0.6)
    hit("high", BARS, 0.0, 0.4)
    # 余震滚奏
    roll(BARS, 0.5, 0.25, 8, 0.8, 0.1, "big")

    # ---------- 铺底：烘托气势的暗流
    n = int(DUR * 44100)
    t = np.arange(n) / 44100
    breath = 0.6 + 0.4 * np.sin(2 * np.pi * 0.06 * t - 1.1)
    
    # 极低的轰鸣音
    for m, level in ((38, 0.12), (45, 0.06)):
        air.add(np.sin(2 * np.pi * hz(m) * t) * breath, 0.0, gain=level)
        
    for bar, name in enumerate(PROGRESSION):
        if bar < 8:
            continue
        vol_scale = min(1.0, (bar - 8) / 16.0)
        for m in CHORDS[name]:
            air.add(pad(hz(m - 12), BAR * 1.15, voices=2, detune=0.004,
                        cutoff=400 + 400 * vol_scale, attack=0.5),
                    at(bar), gain=0.035 * vol_scale)

    # ---------- 总线：混响的距离感设计
    pads = swirl(air.buf.mean(axis=1), rate=0.05, depth=0.4)
    
    # 将鼓组拆分为干湿声，通过时间线逐渐减小湿声比例（越来越近）
    t_env = np.linspace(0.0, 1.0, len(drums.buf))[:, None]
    reverb_mix = 0.4 - 0.25 * t_env  # 混响比例从 40% (极远) 降到 15% (极近)
    
    wet_drums = reverb(drums.buf, dur=3.5, mix=1.0, damp=3000)
    mixed_drums = drums.buf * (1.0 - reverb_mix) + wet_drums * reverb_mix
    
    mix = mixed_drums + reverb(pads, dur=4.0, mix=0.4, damp=2600)
    mix = lowpass(mix, 14000)
    
    # 增加过载(drive)让结尾的鼓声更加暴力
    return render(out / "10_war_drums.wav", mix, fade=(0.01, 4.0), drive=0.35)


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")