"""示例 1 · 向光而行 —— 100 BPM，D 大调。

情绪：清晨出发前的一次深呼吸。钢琴与弦乐渐强。
前四小节极度安静，仅有微弱的呼吸声与钢琴单音。
随后弦乐如晨光般逐层亮起，频段逐渐打开。
第 12 小节如同推开大门，全编制齐奏，最后收于宁静。
"""

from pathlib import Path

import numpy as np

from bgm import hz, render
from bgm.synth import (SR, Track, bass, bell, crash, echo, kick, pad, piano,
                       reverb, snare, swell, tom, hat)

BPM = 100
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 20
DUR = BARS * BAR + 5.0

VOICING = {
    "D": [50, 57, 62, 66],
    "A/C#": [49, 57, 61, 64],
    "Bm": [47, 54, 59, 62],
    "G": [43, 50, 55, 59],
}
BASS = {"D": 38, "A/C#": 37, "Bm": 35, "G": 31}

PROGRESSION = ["D", "A/C#", "Bm", "G"] * 4 + ["D", "D", "D", "D"]

def main(out: Path) -> Path:
    keys = Track(DUR)
    strings = Track(DUR)
    low = Track(DUR)
    drums = Track(DUR)
    breath = Track(DUR)

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    # ---------- 0. 深呼吸 (Breath / Swell)
    # 像人在清晨深吸一口气，带有逐渐变亮的白噪声
    breath.add(swell(dur=BAR * 1.5, cutoff=3000), at(0, 0), gain=0.15, pan_=0.0)
    breath.add(swell(dur=BAR * 1.0, cutoff=4000), at(7, 3), gain=0.25, pan_=0.0)
    breath.add(swell(dur=BAR * 1.0, cutoff=5000), at(11, 3), gain=0.35, pan_=0.0)

    # ---------- 1. 钢琴 (Piano)
    for bar, name in enumerate(PROGRESSION):
        notes = VOICING[name]
        if bar < 4:
            # 极简：每小节只有安静的长音，像破晓
            keys.add(piano(hz(notes[2]), BAR, vel=0.5), at(bar, 0), gain=0.12)
            keys.add(piano(hz(notes[3]), BAR, vel=0.6), at(bar, 2), gain=0.14)
        elif bar < 8:
            # 分解和弦，开始流动
            for i, idx in enumerate([0, 1, 2, 3, 2, 1, 2, 3]):
                keys.add(piano(hz(notes[idx]), BEAT * 1.5, vel=0.7), at(bar, i * 0.5), gain=0.16, pan_=-0.1)
        elif bar < 12:
            # 八分音符推进，力度增大，积蓄力量
            for i in range(8):
                idx = [0, 1, 2, 3][i % 4]
                keys.add(piano(hz(notes[idx]), BEAT, vel=0.8), at(bar, i * 0.5), gain=0.18, pan_=-0.15)
        elif bar < 16:
            # 柱式和弦齐奏 (高潮)，充满阳光感
            for beat in (0.0, 1.5, 2.5):
                for j, m in enumerate(notes):
                    keys.add(piano(hz(m), BEAT * 2, vel=0.95), at(bar, beat), gain=0.22 / np.sqrt(len(notes)))
                # 叠加一个高八度的明亮旋律音
                keys.add(piano(hz(notes[-1] + 12), BEAT * 2, vel=1.0), at(bar, beat), gain=0.12)
        elif bar == 16:
            # 结尾长和弦，回归平静
            for j, m in enumerate(notes):
                keys.add(piano(hz(m), BAR * 2, vel=0.6), at(bar, 0), gain=0.12)
            keys.add(piano(hz(notes[-1] + 12), BAR * 2, vel=0.6), at(bar, 0), gain=0.08)

    # ---------- 2. 弦乐渐强 (Strings / Pad)
    for bar, name in enumerate(PROGRESSION):
        if bar >= 16:
            if bar == 16:
                strings.add(pad(hz(VOICING["D"][0]), BAR * 2, voices=4, detune=0.008, cutoff=1500, attack=0.5), at(bar), gain=0.08)
            continue
            
        # 每一段的低通滤波截止频率（Cutoff）和音量逐渐打开，形成极致的 Crescendo
        if bar < 4:
            cutoff, level, attack = 600, 0.03, 2.0
        elif bar < 8:
            cutoff, level, attack = 1200, 0.06, 1.5
        elif bar < 12:
            cutoff, level, attack = 2400, 0.09, 1.0
        else:
            cutoff, level, attack = 5000, 0.14, 0.5

        for j, m in enumerate(VOICING[name][:3]):
            strings.add(pad(hz(m), BAR * 1.1, voices=3, detune=0.006, cutoff=cutoff, attack=attack),
                        at(bar), gain=level, pan_=(-0.3 + 0.3 * j))

    # ---------- 3. 低音 (Bass)
    for bar, name in enumerate(PROGRESSION):
        if bar < 4 or bar >= 16:
            continue
        root = BASS[name]
        if bar < 8:
            # 缓慢而深沉的低音
            low.add(bass(hz(root), BAR * 0.9, cutoff=300), at(bar, 0), gain=0.18)
        elif bar < 12:
            # 脉搏般的心跳低音
            low.add(bass(hz(root), BEAT * 1.5, cutoff=400), at(bar, 0), gain=0.22)
            low.add(bass(hz(root), BEAT * 1.5, cutoff=400), at(bar, 2), gain=0.22)
        else:
            # 密集的 8 分音符推动
            for i in range(8):
                low.add(bass(hz(root), BEAT * 0.5, cutoff=600), at(bar, i * 0.5), gain=0.25)

    # ---------- 4. 鼓组 (Drums)
    for bar in range(8, 16):
        if bar < 12:
            # 只有底鼓如心跳
            drums.add(kick(tune=45), at(bar, 0), gain=0.3)
            drums.add(kick(tune=45), at(bar, 2), gain=0.3)
        else:
            # 全编制：阳光铺满
            drums.add(kick(tune=50), at(bar, 0), gain=0.4)
            drums.add(kick(tune=50), at(bar, 2), gain=0.4)
            drums.add(snare(dur=0.4), at(bar, 1), gain=0.25)
            drums.add(snare(dur=0.4), at(bar, 3), gain=0.25)
            for i in range(8):
                drums.add(hat(open_=False), at(bar, i * 0.5), gain=0.08, pan_=0.15)
            
    # 过门加花与镲片
    for bar in (11, 15):
        for k in range(4):
            drums.add(snare(), at(bar, 3 + k * 0.25), gain=0.1 + 0.04 * k)
    drums.add(crash(), at(12), gain=0.25, pan_=0.0)
    drums.add(crash(), at(16), gain=0.3, pan_=0.0)

    # ---------- 5. 旋律点缀 (Lead / Bell)
    melody = [
        # 积蓄
        (8, 0, 74), (8, 2, 73), (9, 0, 71), (9, 2, 69),
        (10, 0, 74), (10, 2, 76), (11, 0, 78), (11, 2, 81),
        
        # 绽放
        (12, 0, 81), (12, 1.5, 78), (12, 2.5, 74),
        (13, 0, 76), (13, 1.5, 74), (13, 2.5, 71),
        (14, 0, 74), (14, 1.5, 76), (14, 2.5, 78),
        (15, 0, 81), (15, 2, 86)
    ]
    for bar, beat, m in melody:
        note = piano(hz(m), BEAT * 1.5, vel=0.9)
        keys.add(echo(note, delay=BEAT * 0.75, feedback=0.3, mix=0.2), at(bar, beat), gain=0.25)
        if bar >= 12:
            # 高潮部分叠加上清脆的钟声
            keys.add(bell(hz(m + 12), BEAT * 2), at(bar, beat), gain=0.1, pan_=0.25)

    # ---------- 6. 总线混音
    piano_bus = reverb(keys.buf, dur=3.0, mix=0.25, damp=4500)
    strings_bus = reverb(strings.buf + breath.buf, dur=4.5, mix=0.5, damp=3000)
    
    mix = piano_bus + strings_bus + low.buf + drums.buf
    return render(out / "01_toward_the_light.wav", mix, fade=(0.02, 4.0))


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")