"""示例 11 音效合集 ——

包含鼓组、金属、自然声、电子声，以及用共振峰合成的五个元音（a/e/i/o/u）。
全部由 numpy 现场算出来，本次重点优化了声音的“物理真实感”。

### 核心编曲与声音设计
1. 物理真实感的打击乐与金属：
   - 木鱼加入了短促的高频敲击喀嚓声与特定的共鸣泛音。
   - 硬币通过非整数次泛音（4500Hz/6200Hz/8900Hz）模拟金属共振，并加入基于重力加速度的弹跳速度递增。
2. 自然声与环境：
   - 水滴增加了极速上滑的频率曲线以及表面张力破裂时的气泡底噪。
   - 海浪与风声加入了动态呼吸包络，立体感更强。
3. 电子与科幻：
   - 爆炸加入了极低频冲击波的快速下滑，并对碎片噪音做了严重的过载（软削波）失真处理。
   - 引擎利用包络调制低频锯齿波，模拟了发动机活塞加速转动的爆缸感。
4. 人声元音（Vowels）：
   - 在共振峰合成的基础上，加入了滑音（Portamento）、颤音（Vibrato）以及轻微的脉冲冲激，听感上更像人的声带。
"""

from pathlib import Path
import numpy as np

from bgm import hz, render
from bgm.synth import (SR, Track, adsr, bandpass, bell, bird, clap, gong, hat,
                       highpass, kick, lowpass, osc, reverb, samples, snare,
                       timeline, tom)

SLOT = 1.7
COUNT = 28
DUR = COUNT * SLOT + 3.0

def norm(x: np.ndarray) -> np.ndarray:
    return x / (np.max(np.abs(x)) + 1e-9)

def level(x: np.ndarray, target_rms: float = 0.18) -> np.ndarray:
    """按能量而不是峰值对齐响度，短促的音效才不会被长音压过去。"""
    rms = np.sqrt(np.mean(x ** 2)) + 1e-9
    g = target_rms / rms
    peak = np.max(np.abs(x)) * g
    if peak > 0.98:
        g *= 0.98 / peak
    return x * g

def place(out: np.ndarray, audio: np.ndarray, at: float, gain: float = 1.0) -> np.ndarray:
    """把一段声音放到缓冲区指定秒数处（自动裁掉越界部分）。"""
    i = samples(at)
    chunk = audio[:len(out) - i] * gain
    out[i:i + len(chunk)] += chunk
    return out

def noise_burst(dur: float, seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).standard_normal(samples(dur))

def woodblock(dur: float = 0.15) -> np.ndarray:
    # 木鱼：带共鸣的清脆打击。主频 800Hz，泛音 1900Hz，极短的咔哒声
    t = timeline(dur)
    x = np.sin(2 * np.pi * 800 * t) * np.exp(-t / 0.03)
    x += 0.4 * np.sin(2 * np.pi * 1900 * t) * np.exp(-t / 0.015)
    click = lowpass(noise_burst(dur, 1), 3000) * np.exp(-t / 0.003) * 0.8
    return norm(x + click)

def phone_ring(dur: float = 1.5) -> np.ndarray:
    # 老式电话铃：两个接近的铃铛频率产生拍音，再用 20Hz 的机械敲击调制
    t = timeline(dur)
    out = np.zeros_like(t)
    for start in (0.0, 0.6):
        i = samples(start)
        tt = t[:len(t) - i]
        gate = (np.sin(2 * np.pi * 20 * tt) > 0).astype(float)
        # 两个高频金属音
        tone = np.sin(2 * np.pi * 1400 * tt) + np.sin(2 * np.pi * 1440 * tt)
        # 加入一点谐波
        tone += 0.4 * np.sin(2 * np.pi * 2800 * tt)
        out[i:] += (tone * gate * np.exp(-tt / 0.4))[:len(out) - i]
    return norm(out)

def doorbell() -> np.ndarray:
    # 门铃：经典的 叮-咚 (E5 - C5)，加入非整数泛音更像金属管
    dur = 2.0
    out = np.zeros(samples(dur))
    for m, start in ((76, 0.0), (72, 0.5)):
        # 主频 + 金属泛音
        t_bell = timeline(1.5)
        f0 = hz(m)
        tone = np.sin(2 * np.pi * f0 * t_bell) * np.exp(-t_bell / 0.6)
        tone += 0.5 * np.sin(2 * np.pi * f0 * 2.76 * t_bell) * np.exp(-t_bell / 0.2)
        tone += 0.2 * np.sin(2 * np.pi * f0 * 5.4 * t_bell) * np.exp(-t_bell / 0.1)
        place(out, tone, start, 0.8)
    return norm(out)

def heartbeat() -> np.ndarray:
    # 心跳：Lub-dub。两次低频冲击，第二次略高、略重。
    dur = 1.0
    out = np.zeros(samples(dur))
    # 第一次：低沉
    place(out, lowpass(kick(tune=32, dur=0.4), 100), 0.0, 0.7)
    # 第二次：稍微用力，频率略高
    place(out, lowpass(kick(tune=38, dur=0.4), 120), 0.32, 1.0)
    return norm(out)

def typewriter(dur: float = 1.4) -> np.ndarray:
    # 打字机：密集的机械按键声 + 回车铃 + 换行拉链声
    rng = np.random.default_rng(5)
    out = np.zeros(samples(dur))
    pos = 0.0
    # 按键
    while pos < dur - 0.6:
        t_click = timeline(0.04)
        click = highpass(noise_burst(0.04, int(pos * 1000)), 1500)
        click *= np.exp(-t_click / 0.003)
        # 加入机械部件碰撞的短频
        click += 0.3 * np.sin(2 * np.pi * 3000 * t_click) * np.exp(-t_click / 0.005)
        place(out, click, pos, 0.8)
        pos += rng.uniform(0.06, 0.12)
    # 叮！
    place(out, bell(hz(96), 0.6), dur - 0.5, 0.6)
    # 咔嚓换行 (Zip声)
    zip_t = timeline(0.2)
    zip_noise = bandpass(noise_burst(0.2, 99), 1000, 3000)
    zip_env = np.sin(np.pi * zip_t / 0.2) ** 2
    place(out, zip_noise * zip_env, dur - 0.3, 0.4)
    return norm(out)

def coin() -> np.ndarray:
    # 硬币掉落：高频非整数金属共振 + 弹跳逐渐变快(重力加速度)
    dur = 1.4
    out = np.zeros(samples(dur))
    t_drop = 0.0
    velocity = 0.3
    restitution = 0.65  # 恢复系数
    for _ in range(12):
        if velocity < 0.01: break
        t_hit = timeline(0.3)
        # 硬币典型的 3 个高频共振峰
        tone = np.sin(2 * np.pi * 4500 * t_hit) * np.exp(-t_hit / 0.1)
        tone += 0.6 * np.sin(2 * np.pi * 6200 * t_hit) * np.exp(-t_hit / 0.08)
        tone += 0.4 * np.sin(2 * np.pi * 8900 * t_hit) * np.exp(-t_hit / 0.05)
        # 碰撞噪音
        tone += noise_burst(0.3, int(t_drop*1000)) * np.exp(-t_hit / 0.002) * 0.5
        place(out, tone, t_drop, velocity * 2.5)
        
        t_drop += velocity * 1.2
        velocity *= restitution
    return norm(out)

def water_drop(dur: float = 0.5) -> np.ndarray:
    # 水滴：频率极快上滑的短促音
    t = timeline(dur)
    # 频率从 400 快速滑到 1200
    f = 400 + 800 * (1.0 - np.exp(-t / 0.015))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.05)
    # 水面张力破裂的微小气泡声
    x += noise_burst(dur) * np.exp(-t / 0.002) * 0.15
    return norm(x)

def bubble(dur: float = 0.6) -> np.ndarray:
    # 泡泡：连续几个低频、圆润的快速上滑音
    out = np.zeros(samples(dur))
    for start, f_base in ((0.0, 300), (0.12, 450), (0.2, 250)):
        t_b = timeline(0.15)
        f = f_base + 300 * (1.0 - np.exp(-t_b / 0.02))
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t_b / 0.04)
        place(out, x, start, 1.0)
    return norm(out)

def laser(dur: float = 0.45) -> np.ndarray:
    # 激光：科幻感。快速下滑的方波，带一点脉冲宽度调制(PWM)
    t = timeline(dur)
    f = 3000 * np.exp(-t / 0.08) + 100
    ph = 2 * np.pi * np.cumsum(f) / SR
    # 用组合正弦近似方波
    x = np.sin(ph) + 0.33 * np.sin(3 * ph) + 0.2 * np.sin(5 * ph)
    env = adsr(dur, a=0.005, d=0.1, s=0.0, r=0.1)
    return norm(x * env)

def riser(dur: float = 1.6) -> np.ndarray:
    # 上升音：电子舞曲里的 Build-up，白噪加超级锯齿波上滑
    t = timeline(dur)
    noise = bandpass(noise_burst(dur, 11), 1000, 8000) * 0.4
    f = 100 * np.exp(t * 1.5)  # 指数上升
    tone = osc("saw", f, dur, harmonics=15)
    # 加一点合唱失谐
    tone += 0.5 * osc("saw", f * 1.01, dur, harmonics=15)
    env = (t / dur) ** 2.0  # 越来越响
    return norm((noise + tone) * env)

def siren(dur: float = 1.6) -> np.ndarray:
    # 警笛：用三角波/方波加多普勒频移，刺耳
    t = timeline(dur)
    f = 900 + 350 * np.sin(2 * np.pi * 2.5 * t)
    # 用类似方波的音色，更具警报感
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.3 * np.sin(3 * ph)
    env = adsr(dur, a=0.1, d=0.1, s=0.9, r=0.3)
    return norm(x * env)

def wind(dur: float = 1.7) -> np.ndarray:
    # 风声：用带通滤波器扫描白噪声
    t = timeline(dur)
    noise = noise_burst(dur, 13)
    # 模拟风的呼啸（滤波器中心频率随时间起伏）
    out = np.zeros_like(noise)
    fc = 400 + 300 * np.sin(2 * np.pi * 0.5 * t) + 200 * np.sin(2 * np.pi * 1.2 * t)
    # 手动简单带通 (通过多次低通高通近似)
    # 这里我们用分段处理或者直接用现成滤波。为简便，将噪声分为多段频带叠加
    x1 = lowpass(highpass(noise, 300), 800) * (1.0 + 0.5 * np.sin(2 * np.pi * 0.8 * t))
    x2 = lowpass(highpass(noise, 800), 1500) * (1.0 + 0.8 * np.sin(2 * np.pi * 0.4 * t - 1.0))
    env = np.sin(np.pi * t / dur) ** 1.5
    return norm((x1 + x2) * env)

def rain(dur: float = 1.7) -> np.ndarray:
    # 雨声：高频白噪打底 + 随机粒子的低通雨滴
    t = timeline(dur)
    # 背景沙沙声
    base = bandpass(noise_burst(dur, 17), 1500, 6000) * 0.15
    drops = np.zeros_like(base)
    rng = np.random.default_rng(19)
    # 近处大颗雨滴
    for _ in range(60):
        i = int(rng.integers(0, len(base) - 1000))
        t_d = timeline(1000/SR)
        drop = lowpass(noise_burst(1000/SR, i), rng.uniform(2000, 5000))
        drops[i:i + 1000] += drop * np.exp(-t_d / 0.005) * rng.uniform(0.3, 1.0)
    env = np.sin(np.pi * t / dur) ** 1.2
    return norm((base + drops) * env)

def wave(dur: float = 1.7) -> np.ndarray:
    # 海浪：粉噪特征，呼吸包络，深邃的低频
    t = timeline(dur)
    noise = noise_burst(dur, 23)
    # 多次低通压暗
    x = lowpass(lowpass(noise, 800), 800)
    # 高频浪花声随包络浮现
    splash = highpass(noise, 2000) * np.sin(np.pi * t / dur)
    env = np.sin(np.pi * t / dur) ** 2
    return norm((x * 1.5 + splash * 0.3) * env)

def explosion(dur: float = 1.7) -> np.ndarray:
    # 爆炸：起振极快，含有超低频的快速下滑，以及被严重过载的噪声
    t = timeline(dur)
    # 低频冲击波 (Sub boom)
    f_boom = 120 * np.exp(-t / 0.1) + 30
    boom = np.sin(2 * np.pi * np.cumsum(f_boom) / SR) * np.exp(-t / 0.4)
    # 爆炸碎片噪音 (失真)
    noise = noise_burst(dur, 29)
    rumble = lowpass(noise, 600) * np.exp(-t / 0.6) * 1.5
    crackle = highpass(noise, 1500) * np.exp(-t / 0.2) * 0.8
    # 混合并软削波(模拟过载)
    mix = boom + rumble + crackle
    mix = np.tanh(mix * 3.0) 
    return norm(mix)

def engine(dur: float = 1.7) -> np.ndarray:
    # 引擎：低频锯齿波，用类似活塞的包络去调制它
    t = timeline(dur)
    rpm = 30 + 20 * np.sin(np.pi * t / dur)  # 转速逐渐加快
    # 活塞爆动感
    piston = (np.sin(2 * np.pi * rpm * t) > 0.5).astype(float)
    piston = lowpass(piston, 800)
    # 引擎轰鸣
    rumble = lowpass(osc("saw", rpm, dur, harmonics=20), 400)
    x = rumble + 0.5 * piston * noise_burst(dur, 9)
    env = adsr(dur, a=0.1, d=0.1, s=0.9, r=0.3)
    return norm(x * env)

FORMANTS = {
    "a": ((800, 1.0), (1200, 0.6), (2500, 0.2)),
    "e": ((500, 1.0), (1800, 0.5), (2500, 0.2)),
    "i": ((300, 1.0), (2300, 0.4), (3000, 0.1)),
    "o": ((500, 1.0), (900,  0.6), (2400, 0.2)),
    "u": ((320, 1.0), (800,  0.5), (2300, 0.1)),
}

def vowel(name: str, f0: float = 110.0, dur: float = 1.2) -> np.ndarray:
    """共振峰合成的元音，加入人声颤音（Vibrato）与滑音（Portamento），更加拟真。"""
    t = timeline(dur)
    # 音高曲线：起音略微上滑，中段加入颤音
    f = f0 * (1.0 - 0.05 * np.exp(-t / 0.1)) 
    f *= (1.0 + 0.015 * np.sin(2 * np.pi * 5.5 * t) * (1.0 - np.exp(-t / 0.4)))
    
    src = osc("saw", f, dur, harmonics=40)
    # 人声声带并不全是锯齿波，加一点脉冲冲激感
    src += 0.2 * osc("square", f, dur, harmonics=30)
    
    out = np.zeros_like(src)
    for fc, amp in FORMANTS[name]:
        bw = max(80.0, fc * 0.1)
        out += amp * bandpass(src, fc - bw, fc + bw)
        
    env = adsr(dur, a=0.08, d=0.1, s=0.9, r=0.3)
    return norm(out * env)

def main(out: Path) -> Path:
    track = Track(DUR)

    items = [
        ("大鼓", kick(tune=42)),
        ("军鼓", snare()),
        ("踩镲", hat(open_=True, dur=0.35)),
        ("拍手", clap()),
        ("木鱼", woodblock()),
        ("锣", gong(tune=76, dur=1.7)),
        ("铃声", bell(hz(84), 1.4)),
        ("电话铃", phone_ring()),
        ("门铃", doorbell()),
        ("心跳", heartbeat()),
        ("打字机", typewriter()),
        ("硬币", coin()),
        ("水滴", water_drop()),
        ("泡泡", bubble()),
        ("激光", laser()),
        ("上升音", riser()),
        ("警笛", siren()),
        ("风声", wind()),
        ("雨声", rain()),
        ("海浪", wave()),
        ("爆炸", explosion()),
        ("引擎", engine()),
        ("鸟叫", bird(1400, 0.22, rise=1.9, seed=3)),
        ("配音 a", vowel("a")),
        ("配音 e", vowel("e")),
        ("配音 i", vowel("i")),
        ("配音 o", vowel("o")),
        ("配音 u", vowel("u")),
    ]

    for i, (name, audio) in enumerate(items):
        pan = (-0.35, 0.35, 0.0)[i % 3]
        track.add(level(audio), at=i * SLOT, pan_=pan)

    # 给所有音效一点轻微的房间混响，避免过于干瘪
    mix = reverb(track.buf, dur=1.2, mix=0.15, damp=5000)
    return render(out / "11_sfx_showcase.wav", mix, fade=(0.01, 1.5))


if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1] / "output")