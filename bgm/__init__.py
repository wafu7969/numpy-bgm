"""numpy-bgm：只用 numpy 合成的 BGM 工具包。"""

from . import notation, synth
from .notation import chord, hz, midi, scale
from .synth import SR, Track, echo, render, reverb

__all__ = ["SR", "Track", "synth", "notation", "chord", "hz", "midi", "scale",
           "reverb", "echo", "render"]
__version__ = "0.1.0"
