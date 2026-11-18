"""numpy-bgm 合成引擎。

整个引擎只依赖 numpy 和 Python 标准库：把波形、包络、滤波、混响拼成一段
可以直接写成 WAV 的 BGM。所有函数内部都是向量化运算，一段 60 秒的曲子通常
在一秒到十几秒内渲染完成。
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 44100


# ------------------------------------------------------------------ 基础工具

def samples(dur: float, sr: int = SR) -> int:
    """秒 -> 采样点数量（至少 1 个点）。"""
    return max(1, int(round(dur * sr)))


def timeline(dur: float, sr: int = SR) -> np.ndarray:
    """返回 [0, dur) 的时间轴，单位秒。"""
    return np.arange(samples(dur, sr)) / sr


def phase(freq, dur: float, sr: int = SR, phase0: float = 0.0) -> np.ndarray:
    """相位轴。

    freq 既可以是标量，也可以是与时间轴等长的数组，后者用来做滑音、
    颤音、鼓的瞬时降调。数组频率用 cumsum 积分，保证相位连续。
    """
    n = samples(dur, sr)
    if np.isscalar(freq):
        return 2 * np.pi * float(freq) * np.arange(n) / sr + phase0
    f = np.asarray(freq, dtype=float)
    if len(f) < n:
        f = np.pad(f, (0, n - len(f)), mode="edge")
    return 2 * np.pi * np.cumsum(f[:n]) / sr + phase0


def _fit(x: np.ndarray, gain: float = 1.0) -> np.ndarray:
    """把单音归一化到固定峰值，再乘上力度，避免低音比高音响太多。"""
    peak = float(np.max(np.abs(x))) or 1.0
    return x / peak * gain


# ------------------------------------------------------------------ 振荡器

def osc(waveform: str, freq, dur: float, sr: int = SR, phase0: float = 0.0,
        harmonics: int = 24) -> np.ndarray:
    """带限振荡器：sine / saw / square / triangle / noise。"""
    ph = phase(freq, dur, sr, phase0)

    if waveform == "sine":
        return np.sin(ph)
    if waveform == "noise":
        return np.random.default_rng(0).standard_normal(len(ph))

    out = np.zeros_like(ph)
    nyq = sr * 0.45
    max_h = min(harmonics, 64)
    for k in range(1, max_h + 1):
        if np.isscalar(freq) and float(freq) * k > nyq:
            break
        if waveform == "saw":
            out += np.sin(k * ph) / k
        elif waveform == "square":
            if k % 2 == 1:
                out += np.sin(k * ph) / k
        elif waveform == "triangle":
            if k % 2 == 1:
                out += ((-1) ** ((k - 1) // 2)) * np.sin(k * ph) / (k * k)
        else:
            raise ValueError(f"未知波形: {waveform}")

    if waveform == "saw":
        return out * (2 / np.pi)
    if waveform == "square":
        return out * (4 / np.pi)
    return out * (8 / np.pi ** 2)


# ------------------------------------------------------------------ 包络

def adsr(dur: float, a: float = 0.01, d: float = 0.1, s: float = 0.7,
         r: float = 0.2, sr: int = SR, curve: float = 2.5) -> np.ndarray:
    """经典 ADSR 包络，指数曲线让起音和收尾更自然。"""
    n = samples(dur, sr)
    env = np.full(n, s, dtype=float)

    a_n = min(samples(a, sr) if a > 0 else 0, n)
    d_n = min(samples(d, sr) if d > 0 else 0, max(0, n - a_n))
    r_n = min(samples(r, sr) if r > 0 else 0, max(0, n - a_n - d_n))
    s_n = n - a_n - d_n - r_n

    i = 0
    if a_n:
        env[:a_n] = np.linspace(0.0, 1.0, a_n) ** 0.75
        i += a_n
    if d_n:
        u = np.linspace(0.0, 1.0, d_n)
        env[i:i + d_n] = 1 - (1 - s) * (1 - np.exp(-curve * u)) / (1 - np.exp(-curve))
        i += d_n
    if s_n:
        env[i:i + s_n] = s
        i += s_n
    if r_n:
        u = np.linspace(0.0, 1.0, r_n)
        env[i:i + r_n] = s * (np.exp(-curve * u) - np.exp(-curve)) / (1 - np.exp(-curve))
    return env


def decay_env(dur: float, tau: float, sr: int = SR, attack: float = 0.002) -> np.ndarray:
    """打击乐式的指数衰减包络。"""
    t = timeline(dur, sr)
    env = np.exp(-t / tau)
    a_n = min(samples(attack, sr), len(env))
    if a_n > 1:
        env[:a_n] *= np.linspace(0.0, 1.0, a_n)
    return env


# ------------------------------------------------------------------ 滤波

def _spectral(x: np.ndarray, gain_fn, sr: int) -> np.ndarray:
    if x.ndim == 2:
        return np.stack([_spectral(x[:, c], gain_fn, sr) for c in range(x.shape[1])], axis=1)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / sr)
    return np.fft.irfft(X * gain_fn(f), n=len(x))


def lowpass(x: np.ndarray, cutoff: float, sr: int = SR, order: int = 2) -> np.ndarray:
    """零相位 Butterworth 型低通，用 FFT 一次性完成，无逐样本循环。"""
    return _spectral(x, lambda f: 1.0 / np.sqrt(1.0 + (f / max(cutoff, 1.0)) ** (2 * order)), sr)


def highpass(x: np.ndarray, cutoff: float, sr: int = SR, order: int = 2) -> np.ndarray:
    return _spectral(x, lambda f: 1.0 / np.sqrt(1.0 + (max(cutoff, 1.0) / np.maximum(f, 1e-6)) ** (2 * order)), sr)


def bandpass(x: np.ndarray, low: float, high: float, sr: int = SR, order: int = 2) -> np.ndarray:
    return lowpass(highpass(x, low, sr, order), high, sr, order)


# ------------------------------------------------------------------ 音色

def piano(freq: float, dur: float, sr: int = SR, vel: float = 1.0) -> np.ndarray:
    """钢琴：叠加衰减谐波 + 极短的击弦噪声。"""
    t = timeline(dur, sr)
    out = np.zeros_like(t)
    for k in range(1, 13):
        if freq * k > sr * 0.45:
            break
        amp = 1.0 / k ** 1.35
        tau = 2.6 / (1 + 0.45 * (k - 1))
        out += amp * np.sin(2 * np.pi * freq * k * t + 0.13 * k) * np.exp(-t / tau)
    out *= np.exp(-t * 0.35)
    out += 0.12 * np.exp(-t / 0.006) * np.sin(2 * np.pi * freq * 3 * t)
    return _fit(out, vel)


def bell(freq: float, dur: float, sr: int = SR, vel: float = 1.0) -> np.ndarray:
    """钟 / 音铃：非整数倍泛音，适合氛围曲的远景点缀。"""
    t = timeline(dur, sr)
    out = np.zeros_like(t)
    for ratio, amp, tau in ((1, 1.0, 1.7), (2.0, 0.5, 1.1), (2.76, 0.38, 0.8),
                            (4.07, 0.22, 0.55), (5.43, 0.15, 0.4)):
        out += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t / tau)
    out += 0.05 * np.exp(-t / 0.004) * np.random.default_rng(int(freq)).standard_normal(len(t))
    return _fit(out, vel)


def pluck(freq: float, dur: float, sr: int = SR, vel: float = 1.0,
          bright: float = 0.62) -> np.ndarray:
    """拨弦（古筝/吉他）：谐波按 bright 衰减，高次谐波衰减更快。"""
    t = timeline(dur, sr)
    out = np.zeros_like(t)
    for k in range(1, 20):
        if freq * k > sr * 0.45:
            break
        amp = bright ** (k - 1) / k ** 0.5
        tau = 1.9 / (1 + 0.75 * (k - 1))
        out += amp * np.sin(2 * np.pi * freq * k * t + 0.2 * k) * np.exp(-t / tau)
    out += 0.18 * np.exp(-t / 0.008) * np.random.default_rng(int(freq) + 1).standard_normal(len(t))
    out = lowpass(out, 5200, sr)
    return _fit(out, vel)


def ep(freq: float, dur: float, sr: int = SR, vel: float = 1.0, index: float = 2.8) -> np.ndarray:
    """电钢琴：两算子 FM，调制指数快速衰减，得到 Rhodes 式的“叮”。"""
    t = timeline(dur, sr)
    modulator = index * np.exp(-t * 3.4) * np.sin(2 * np.pi * freq * 2.0 * t)
    out = np.sin(2 * np.pi * freq * t + modulator)
    out += 0.15 * np.sin(2 * np.pi * freq * 2.0 * t + modulator)
    out *= np.exp(-t * 1.15) * (1 + 0.05 * np.sin(2 * np.pi * 4.8 * t))
    out += 0.18 * np.exp(-t / 0.008) * np.sin(2 * np.pi * freq * 4 * t)
    return _fit(out, vel)


def pad(freq: float, dur: float, sr: int = SR, vel: float = 1.0, voices: int = 3,
        detune: float = 0.004, cutoff: float = 1500, attack: float = 0.8) -> np.ndarray:
    """铺底 Pad：多个失谐锯齿叠加后低通，慢慢出现、慢慢消失。"""
    out = np.zeros(samples(dur, sr))
    for i in range(voices):
        ratio = 1.0 + detune * (i - (voices - 1) / 2)
        out += osc("saw", freq * ratio, dur, sr, phase0=i * 1.7, harmonics=16)
    out /= voices
    out = lowpass(out, cutoff, sr)
    env = adsr(dur, a=attack, d=0.4, s=0.86, r=min(2.0, dur * 0.4), curve=3.0)
    return _fit(out * env, vel)


def bass(freq: float, dur: float, sr: int = SR, vel: float = 1.0,
         cutoff: float = 420, sub: float = 0.6) -> np.ndarray:
    """锯齿贝斯 + 正弦超低音，电子曲的低频骨架。"""
    out = lowpass(osc("saw", freq, dur, sr, harmonics=20), cutoff, sr)
    out += sub * np.sin(phase(freq, dur, sr))
    env = adsr(dur, a=0.006, d=0.09, s=0.85, r=0.05)
    return _fit(out * env, vel)


def supersaw(freq: float, dur: float, sr: int = SR, vel: float = 1.0, voices: int = 5,
             detune: float = 0.009, cutoff: float = 3200) -> np.ndarray:
    """超级锯齿：EDM 里那种又宽又亮的和弦音色。"""
    out = np.zeros(samples(dur, sr))
    for i in range(voices):
        ratio = 1.0 + detune * (i - (voices - 1) / 2)
        out += osc("saw", freq * ratio, dur, sr, phase0=i * 2.1, harmonics=18)
    out /= voices
    out = lowpass(out, cutoff, sr)
    env = adsr(dur, a=0.008, d=0.14, s=0.55, r=min(0.3, dur * 0.5), curve=3.5)
    return _fit(out * env, vel)


def lead(freq: float, dur: float, sr: int = SR, vel: float = 1.0) -> np.ndarray:
    """主旋律音色：锯齿 + 方波，短促但有延音。"""
    out = 0.7 * osc("saw", freq, dur, sr, harmonics=16) + 0.3 * osc("square", freq, dur, sr, harmonics=9)
    out = lowpass(out, 4600, sr)
    env = adsr(dur, a=0.006, d=0.1, s=0.62, r=min(0.22, dur * 0.5), curve=3.0)
    return _fit(out * env, vel)


# ------------------------------------------------------------------ 鼓组

def kick(sr: int = SR, dur: float = 0.45, tune: float = 48, vel: float = 1.0) -> np.ndarray:
    """底鼓：正弦从 120Hz 快速滑到 tune，再叠一点点击。"""
    t = timeline(dur, sr)
    f = tune + 72 * np.exp(-t / 0.028)
    body = np.sin(phase(f, dur, sr)) * np.exp(-t / 0.22)
    click = np.exp(-t / 0.004) * np.sin(2 * np.pi * 1800 * t) * 0.25
    return _fit(body + click, vel)


def snare(sr: int = SR, dur: float = 0.3, vel: float = 1.0, seed: int = 11) -> np.ndarray:
    """军鼓：两个正弦“鼓腔” + 高通噪声。"""
    t = timeline(dur, sr)
    tone = 0.6 * np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.06)
    tone += 0.3 * np.sin(2 * np.pi * 330 * t) * np.exp(-t / 0.04)
    noise = np.random.default_rng(seed).standard_normal(len(t))
    noise = bandpass(noise, 900, 7500, sr) * np.exp(-t / 0.11)
    return _fit(tone + noise, vel)


def clap(sr: int = SR, dur: float = 0.25, vel: float = 1.0, seed: int = 23) -> np.ndarray:
    """拍手：几段错开的噪声爆发。"""
    t = timeline(dur, sr)
    noise = np.random.default_rng(seed).standard_normal(len(t))
    env = np.zeros(len(t))
    for start in (0.0, 0.011, 0.022, 0.034):
        i = samples(start, sr)
        env[i:] += np.exp(-(t[:len(t) - i]) / (0.03 if start < 0.03 else 0.12))
    return _fit(bandpass(noise * env, 1200, 6000, sr), vel)


def hat(sr: int = SR, dur: float = 0.09, vel: float = 1.0, open_: bool = False,
        seed: int = 5) -> np.ndarray:
    """踩镲：高通噪声 + 极短衰减。"""
    t = timeline(dur, sr)
    noise = np.random.default_rng(seed).standard_normal(len(t))
    noise = highpass(noise, 6800, sr)
    env = np.exp(-t / (0.075 if open_ else 0.018))
    a_n = min(samples(0.002, sr), len(env))
    env[:a_n] *= np.linspace(0, 1, a_n)
    return _fit(noise * env, vel)


def shaker(sr: int = SR, dur: float = 0.12, vel: float = 1.0, seed: int = 31) -> np.ndarray:
    t = timeline(dur, sr)
    noise = highpass(np.random.default_rng(seed).standard_normal(len(t)), 4200, sr)
    env = np.exp(-t / 0.04)
    a_n = min(samples(0.008, sr), len(env))
    env[:a_n] *= np.linspace(0, 1, a_n)
    return _fit(bandpass(noise * env, 4000, 11000, sr), vel)


def tom(sr: int = SR, dur: float = 0.5, tune: float = 92, vel: float = 1.0) -> np.ndarray:
    """低音鼓（中国风里的“鼓”）：比底鼓更低更长。"""
    t = timeline(dur, sr)
    f = tune + 40 * np.exp(-t / 0.06)
    body = np.sin(phase(f, dur, sr)) * np.exp(-t / 0.32)
    return _fit(body, vel)


def crash(sr: int = SR, dur: float = 1.8, vel: float = 1.0, seed: int = 17) -> np.ndarray:
    """吊镲：长衰减的高通噪声，用来标记段落起点。"""
    t = timeline(dur, sr)
    noise = np.random.default_rng(seed).standard_normal(len(t))
    noise = bandpass(noise, 2600, 14000, sr)
    env = np.exp(-t / 0.5)
    a_n = min(samples(0.003, sr), len(env))
    env[:a_n] *= np.linspace(0.0, 1.0, a_n)
    return _fit(noise * env, vel)


# ------------------------------------------------------------------ 空间与混音

def _convolve(x: np.ndarray, ir: np.ndarray) -> np.ndarray:
    n = len(x) + len(ir) - 1
    nfft = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)
    return y[:len(x)]


def _make_ir(dur: float, sr: int, seed: int, damp: float) -> np.ndarray:
    n = samples(dur, sr)
    t = np.arange(n) / sr
    ir = np.random.default_rng(seed).standard_normal(n) * np.exp(-6.9 * t / dur)
    ir = lowpass(ir, damp, sr)
    pre = samples(0.012, sr)
    ir[:pre] *= np.linspace(0.0, 1.0, pre)
    return ir / (np.sqrt(np.sum(ir ** 2)) + 1e-12)


def reverb(x: np.ndarray, dur: float = 2.4, mix: float = 0.3, damp: float = 5200,
           seed: int = 7, sr: int = SR) -> np.ndarray:
    """卷积混响：用指数衰减噪声当脉冲响应，左右声道换种子得到宽度。"""
    mono = x.ndim == 1
    data = x[:, None] if mono else x
    wet = np.stack([
        _convolve(data[:, 0], _make_ir(dur, sr, seed, damp)),
        _convolve(data[:, 1] if data.shape[1] > 1 else data[:, 0],
                  _make_ir(dur, sr, seed + 1, damp)),
    ], axis=1)
    out = data * (1.0 - mix) + wet * mix
    return out[:, 0] if mono else out


def echo(x: np.ndarray, delay: float = 0.3, feedback: float = 0.35, mix: float = 0.25,
         taps: int = 4, sr: int = SR) -> np.ndarray:
    """多抽头延迟，给旋律加“山谷回声”。"""
    wet = np.zeros_like(x)
    step = samples(delay, sr)
    for i in range(1, taps + 1):
        shift = i * step
        if shift >= len(x):
            break
        wet[shift:] += (feedback ** i) * x[:len(x) - shift]
    return x + wet * mix


def pan(audio: np.ndarray, p: float, sr: int = SR) -> np.ndarray:
    """等功率声像：p 从 -1（左）到 1（右）。"""
    if audio.ndim == 2:
        return audio
    ang = (np.clip(p, -1.0, 1.0) + 1.0) * np.pi / 4.0
    return np.stack([audio * np.cos(ang), audio * np.sin(ang)], axis=1)


def swirl(audio: np.ndarray, rate: float = 0.25, depth: float = 0.9,
          phase: float = 0.0, sr: int = SR) -> np.ndarray:
    """自动声像：让声音以 rate 圈/秒 的速度在左右声道之间环绕。

    depth 控制绕圈半径（0 居中，1 贴耳）；phase 用来让不同声部错开位置。
    """
    mono = audio if audio.ndim == 1 else np.asarray(audio).mean(axis=1)
    t = np.arange(len(mono)) / sr
    p = np.clip(depth, 0.0, 1.0) * np.sin(2 * np.pi * rate * t + phase)
    ang = (p + 1.0) * np.pi / 4.0
    return np.stack([mono * np.cos(ang), mono * np.sin(ang)], axis=1)


class Track:
    """一条多轨时间线：把声音按秒“放”到对应位置，最后一次性写出。"""

    def __init__(self, duration: float, sr: int = SR):
        self.sr = sr
        self.buf = np.zeros((samples(duration, sr), 2), dtype=float)

    @property
    def duration(self) -> float:
        return len(self.buf) / self.sr

    def add(self, audio, at: float = 0.0, gain: float = 1.0, pan_: float = 0.0) -> "Track":
        audio = np.asarray(audio, dtype=float)
        if audio.ndim == 1:
            audio = pan(audio, pan_, self.sr)
        start = int(round(at * self.sr))
        if start < 0:
            audio = audio[-start:]
            start = 0
        if start >= len(self.buf):
            return self
        chunk = audio[:len(self.buf) - start]
        self.buf[start:start + len(chunk)] += chunk * gain
        return self

    def write(self, path: str | Path, peak: float = 0.89, fade: tuple = (0.01, 1.5),
              drive: float = 0.0) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        audio = master(self.buf, self.sr, peak=peak, fade=fade, drive=drive)
        write_wav(path, audio, self.sr)
        print(f"✓ {path}  ({self.duration:.1f}s)")
        return path


def master(x: np.ndarray, sr: int = SR, peak: float = 0.89,
           fade: tuple = (0.01, 1.5), drive: float = 0.0) -> np.ndarray:
    """母线处理：淡入淡出 -> 可选软削波 -> 归一化到 -1dBFS 附近。"""
    x = np.asarray(x, dtype=float).copy()
    squeeze = x.ndim == 1
    if squeeze:
        x = x[:, None]
    n = len(x)
    peak_now = float(np.max(np.abs(x))) or 1.0
    x /= peak_now

    if drive > 0:
        x = np.tanh(x * (1.0 + drive * 4.0))
        x /= float(np.max(np.abs(x))) or 1.0

    fade_in = min(samples(fade[0], sr), n // 2)
    fade_out = min(samples(fade[1], sr), n // 2)
    if fade_in > 1:
        x[:fade_in] *= np.linspace(0.0, 1.0, fade_in)[:, None] ** 0.5
    if fade_out > 1:
        x[-fade_out:] *= np.linspace(1.0, 0.0, fade_out)[:, None] ** 1.2

    x *= peak
    return x[:, 0] if squeeze else x


def render(path: str | Path, audio: np.ndarray, sr: int = SR, peak: float = 0.89,
           fade: tuple = (0.01, 1.5), drive: float = 0.0) -> Path:
    """母线处理 + 导出，示例脚本里直接调用这一行即可。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_wav(path, master(audio, sr, peak=peak, fade=fade, drive=drive), sr)
    print(f"✓ {path.name}  {len(audio) / sr:.1f}s")
    return path


def write_wav(path: str | Path, audio: np.ndarray, sr: int = SR) -> None:
    """16bit PCM 立体声 WAV，用标准库写入，不需要 soundfile。"""
    audio = np.asarray(audio, dtype=float)
    if audio.ndim == 1:
        audio = np.stack([audio, audio], axis=1)
    pcm = np.clip(audio * 32767.0, -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(pcm.tobytes())


# ------------------------------------------------------------------ 质感小工具

def vinyl(dur: float, sr: int = SR, density: float = 55, level: float = 0.55,
          seed: int = 3) -> np.ndarray:
    """黑胶底噪：低通噪声 + 稀疏爆音。"""
    n = samples(dur, sr)
    rng = np.random.default_rng(seed)
    hiss = rng.standard_normal(n) * 0.012
    hiss = lowpass(highpass(hiss, 500, sr), 7000, sr)
    clicks = rng.random(n) < density / sr
    hiss[clicks] += rng.standard_normal(int(clicks.sum())) * 0.22
    return hiss * level


def swell(dur: float, sr: int = SR, cutoff: float = 7000, seed: int = 9) -> np.ndarray:
    """反向镲片式的声音膨胀，用来连接段落。"""
    n = samples(dur, sr)
    noise = highpass(np.random.default_rng(seed).standard_normal(n), 1200, sr)
    env = np.linspace(0.0, 1.0, n) ** 3
    return _fit(lowpass(noise * env, cutoff, sr))


def tape(x: np.ndarray, sr: int = SR, wow: float = 0.0014, flutter: float = 0.0004) -> np.ndarray:
    """磁带抖动：给整体加一点缓慢的音高摆动，Lo-Fi 的灵魂。"""
    data = x if x.ndim == 2 else x[:, None]
    n = len(data)
    t = np.arange(n) / sr
    delay = (wow / 0.35) * np.sin(2 * np.pi * 0.35 * t) + (flutter / 6.0) * np.sin(2 * np.pi * 6.0 * t)
    pos = np.clip(np.arange(n) + delay * sr, 0, n - 1)
    grid = np.arange(n)
    out = np.stack([np.interp(pos, grid, data[:, c]) for c in range(data.shape[1])], axis=1)
    return out[:, 0] if x.ndim == 1 else out


def rms(x: np.ndarray) -> float:
    """均方根电平，用来快速检查每一段的响度是否合理。"""
    x = np.asarray(x, dtype=float)
    return float(np.sqrt(np.mean(x ** 2)) + 1e-12)
