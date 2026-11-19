"""示例 03 霓虹夜行 ——

情绪：夜路、车灯、肾上腺素。四拍底鼓 + 锯齿贝斯 + 超级锯齿和弦，
中段留一个没有鼓的呼吸口，再冲进最后一次副歌。

### 核心编曲与声音设计
1. 经典的四四拍底鼓 (Four-on-the-floor) 与反拍踩镲：
   - 这是电子舞曲的心跳。底鼓沉重，踩镲在每一拍的后半拍出现，提供强烈的推进感。
2. 锯齿波贝斯 (Saw Bass) 与超级锯齿波 (Supersaw) 和弦：
   - 贝斯极具攻击性，和弦使用了多重失谐的锯齿波叠加，营造出宽广且充满合成器波普（Synthpop）色彩的听感，像城市霓虹灯的光晕。
3. 动态的呼吸与爆发：
   - 中段刻意抽离了底鼓，仅保留琶音与和弦，像是在空旷的高架桥上短暂滑行，随后底鼓再次砸下，形成强烈的释放感。
"""

from pathlib import Path

from bgm import hz, render
from bgm.synth import (Track, bell, clap, echo, hat, kick, lead, pad, reverb,
                       snare, supersaw, swell, bass)

BPM = 122
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 32
DUR = BARS * BAR + 3.0

CHORDS = [
    ("A", "min", [57, 60, 64, 69]),
    ("F", "maj", [53, 57, 60, 65]),
    ("C", "maj", [55, 60, 64, 67]),
    ("G", "maj", [55, 59, 62, 67]),
]
ROOTS = [45, 41, 48, 43]  # A2 F2 C3 G2

ARP_STEPS = [0, 1, 2, 3, 2, 1, 2, 3, 0, 1, 2, 3, 2, 1, 2, 3]

MELODY = [
    [(0, .5, 76), (.5, .5, 74), (1, 1, 72), (2, .5, 74), (2.5, 1.5, 76)],
    [(0, 1, 72), (1, .5, 69), (1.5, .5, 72), (2, 2, 74)],
    [(0, .5, 79), (.5, .5, 76), (1, 1, 74), (2, .5, 72), (2.5, 1.5, 74)],
    [(0, 2, 67), (2, 1, 69), (3, 1, 72)],
    [(0, .5, 76), (.5, .5, 79), (1, 1, 81), (2, .5, 79), (2.5, 1.5, 76)],
    [(0, 1, 74), (1, .5, 72), (1.5, .5, 74), (2, 2, 77)],
    [(0, .5, 76), (.5, .5, 74), (1, 1, 72), (2, 2, 69)],
    [(0, 2, 71), (2, 2, 72)],
]


def main(out: Path) -> Path:
    drums = Track(DUR)
    low = Track(DUR)
    stabs = Track(DUR)
    arp_bus = Track(DUR)
    lead_bus = Track(DUR)
    air = Track(DUR)

    def at(bar: int, beat: float = 0.0) -> float:
        return bar * BAR + beat * BEAT

    bars = list(range(BARS))

    # ---------- 铺底 Pad：几乎全程都在，断奏段落靠它撑住
    for bar in bars:
        name, quality, notes = CHORDS[bar % 4]
        level = 0.030 if 4 <= bar < 20 or bar >= 24 else 0.045
        for j, m in enumerate(notes[:3]):
            air.add(pad(hz(m), BAR * 1.15, voices=3, cutoff=900, attack=0.4),
                    at(bar), gain=level, pan_=(-0.3 + 0.3 * j))

    # ---------- 16 分音符琶音：前奏从轻到响
    for bar in bars:
        name, quality, notes = CHORDS[bar % 4]
        tones = [n + 12 for n in notes[:3]]
        for step in range(16):
            idx = ARP_STEPS[step]
            m = tones[idx % len(tones)] + (12 if idx >= len(tones) else 0)
            if bar < 4:
                gain = 0.045 + 0.018 * bar
            elif bar < 20:
                gain = 0.070
            elif bar < 24:
                gain = 0.085
            else:
                gain = 0.075
            arp_bus.add(supersaw(hz(m), BEAT * 0.42, voices=2, detune=0.004,
                                 cutoff=2600),
                        at(bar, step * 0.25), gain=gain,
                        pan_=0.35 if step % 2 else -0.35)

    # ---------- 鼓组
    for bar in bars:
        full = (4 <= bar < 20) or bar >= 24
        if full:
            for beat in (0, 1, 2, 3):
                drums.add(kick(), at(bar, beat), gain=0.52)
            for beat in (1, 3):
                drums.add(clap(), at(bar, beat), gain=0.28)
            for i in range(8):
                drums.add(hat(open_=False), at(bar, i * 0.5),
                          gain=0.085 if i % 2 == 0 else 0.06,
                          pan_=0.18 if i % 2 else -0.18)
            if bar % 2 == 1:
                drums.add(hat(open_=True, dur=0.22), at(bar, 3.5), gain=0.10)
        elif bar < 4:
            for i in range(4):
                drums.add(hat(open_=False), at(bar, i), gain=0.045)

    # 段落连接处的军鼓滚奏
    for bar in (7, 11, 19, 27, 30):
        for k in range(4):
            drums.add(snare(), at(bar, 3 + k * 0.25), gain=0.10 + 0.05 * k)

    # ---------- 可循环的切线膨胀
    for bar, beat, dur in ((3, 2, 1.4), (11, 2.5, 1.2), (23, 2, 1.6), (30, 0, 3.0)):
        air.add(swell(dur), at(bar, beat), gain=0.22, pan_=0.0)

    # ---------- 贝斯：八分音符，反拍跳八度
    pattern = [0, 0, 12, 0, 0, 12, 0, 12]
    for bar in bars:
        if not ((4 <= bar < 20) or bar >= 24):
            continue
        root = ROOTS[bar % 4]
        for i, offset in enumerate(pattern):
            low.add(bass(hz(root + offset), BEAT * 0.46, cutoff=360 + 60 * (bar >= 24)),
                    at(bar, i * 0.5), gain=0.26)

    # ---------- 副歌和弦短音（反拍）
    for bar in bars:
        if not ((12 <= bar < 20) or (24 <= bar < 31)):
            continue
        name, quality, notes = CHORDS[bar % 4]
        for beat in (0.5, 1.5, 2.5, 3.5):
            for m in notes[:3]:
                stabs.add(supersaw(hz(m), BEAT * 0.22, voices=4, cutoff=4200),
                          at(bar, beat), gain=0.055, pan_=0.0)

    # ---------- 主旋律：两次副歌，第二次叠高八度与钟琴
    for section, start in ((1, 12), (2, 24)):
        limit = len(MELODY) if start == 12 else len(MELODY) - 1
        for i in range(limit):
            bar = start + i
            for beat, dur, m in MELODY[i]:
                note = lead(hz(m), dur * BEAT * 0.95)
                lead_bus.add(echo(note, delay=BEAT * 0.75, feedback=0.28, mix=0.22),
                             at(bar, beat), gain=0.17, pan_=0.05)
                if section == 2:
                    shim = bell(hz(m + 12), dur * BEAT * 0.9)
                    lead_bus.add(shim, at(bar, beat), gain=0.055, pan_=-0.25)

    # ---------- 间奏：没有鼓，只留钟琴与 Pad
    for bar in range(20, 24):
        name, quality, notes = CHORDS[bar % 4]
        for i in range(4):
            m = notes[i % len(notes)] + 12
            lead_bus.add(reverb(bell(hz(m), BEAT * 2.2), dur=4.0, mix=0.4),
                         at(bar, i), gain=0.075, pan_=0.3 if i % 2 else -0.3)

    # ---------- 收尾：一个长和弦 + 高音钟
    for m in CHORDS[3][2]:
        stabs.add(supersaw(hz(m), BEAT * 2.4, voices=5, cutoff=3600),
                  at(31), gain=0.075)
    lead_bus.add(bell(hz(81), 3.5), at(31, 0.1), gain=0.12, pan_=0.0)
    drums.add(kick(), at(31), gain=0.55)
    drums.add(hat(open_=True, dur=0.6), at(31), gain=0.12)

    # ---------- 总线
    mix = (drums.buf * 0.95
           + low.buf
           + stabs.buf
           + reverb(arp_bus.buf, dur=2.0, mix=0.25, damp=6000) * 0.9
           + reverb(lead_bus.buf, dur=2.4, mix=0.30, damp=5200)
           + reverb(air.buf, dur=3.5, mix=0.42, damp=3200))
    return render(out / "03_neon_night.wav", mix, fade=(0.01, 2.0), drive=0.15)


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")
