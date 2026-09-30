import json
from dataclasses import dataclass, asdict, field, fields

@dataclass
class Layer:
    name: str
    kind: str
    enabled: bool = True
    opacity: float = 1.0

@dataclass
class Project:
    title: str = 'Untitled Visual'
    preset: str = 'Neon Spectrum'
    background: str = '#050711'
    accent: str = '#7c5cff'
    accent2: str = '#00e5ff'
    accent3: str = '#ff3cac'
    sensitivity: float = 1.0
    smoothing: float = 0.55
    bar_count: int = 96
    fps: int = 30
    resolution: str = '1920x1080'
    aspect_ratio: str = '16:9'
    glow: float = 0.75
    reactivity: str = 'Balanced'
    beat_amount: float = 1.0
    bass_amount: float = 1.0
    mid_amount: float = 0.75
    treble_amount: float = 0.65
    quality: str = 'Balanced'
    layers: list = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d['layers'] = [asdict(x) if isinstance(x, Layer) else dict(x) for x in self.layers]
        return d

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError('Project file must contain a JSON object.')
        allowed = {f.name for f in fields(cls)}
        clean = {k: v for k, v in data.items() if k in allowed}
        layer_allowed = {f.name for f in fields(Layer)}
        clean['layers'] = [Layer(**{k:v for k,v in x.items() if k in layer_allowed})
                           for x in clean.get('layers', []) if isinstance(x, dict) and 'name' in x and 'kind' in x]
        return cls(**clean)

    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path):
        with open(path, 'r', encoding='utf-8') as f:
            return cls.from_dict(json.load(f))
