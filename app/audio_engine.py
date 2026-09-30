import os, shutil, subprocess, tempfile
import numpy as np
import soundfile as sf

class AudioEngine:
    SUPPORTED_EXTENSIONS = {'.wav','.flac','.ogg','.mp3','.m4a','.aac','.opus'}
    def __init__(self):
        self.data = None; self.sample_rate = 0; self.path = ''; self.duration = 0.0; self._temp_wav = None
        self._last_t = -1.0; self._last = None

    def close(self):
        if self._temp_wav:
            try: os.unlink(self._temp_wav)
            except OSError: pass
            self._temp_wav = None
        self.data = None; self.path = ''; self.duration = 0.0

    def load(self, path):
        self.close(); path = str(path)
        try:
            data, sr = sf.read(path, dtype='float32', always_2d=False)
        except Exception:
            data, sr = self._decode_with_ffmpeg(path)
        if data is None or sr <= 0: raise ValueError('Could not decode this audio file.')
        if getattr(data, 'ndim', 1) > 1: data = np.mean(data, axis=1)
        data = np.asarray(data, dtype=np.float32)
        if not data.size: raise ValueError('The audio file is empty.')
        peak = float(np.max(np.abs(data)))
        if peak > 1: data /= peak
        self.data = np.clip(data, -1, 1); self.sample_rate = int(sr); self.path = path
        self.duration = len(data) / self.sample_rate
        self._last_t = -1; self._last = None
        return self.data

    def _decode_with_ffmpeg(self, path):
        ffmpeg = shutil.which('ffmpeg')
        if not ffmpeg: raise RuntimeError('FFmpeg is required for this audio format. Install FFmpeg and add it to PATH.')
        fd, wav = tempfile.mkstemp(prefix='pulse_audio_', suffix='.wav'); os.close(fd)
        cmd = [ffmpeg, '-y', '-loglevel', 'error', '-i', path, '-vn', '-ac', '1', '-ar', '48000', wav]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            try: os.unlink(wav)
            except OSError: pass
            raise RuntimeError('FFmpeg could not decode this audio file.\n' + r.stderr[-1800:])
        self._temp_wav = wav
        return sf.read(wav, dtype='float32')

    def frame(self, t, size=4096):
        size = max(256, int(size))
        if self.data is None: return np.zeros(size, np.float32)
        center = int(max(0, t) * self.sample_rate)
        start = center - size // 2; end = start + size
        a = max(0, start); b = min(len(self.data), end)
        chunk = self.data[a:b]
        if start < 0 or end > len(self.data):
            chunk = np.pad(chunk, (max(0,-start), max(0,end-len(self.data))))
        return chunk[:size].astype(np.float32, copy=False)

    def analyze(self, t, bands=96):
        if self.data is None:
            return dict(spectrum=np.zeros(bands,np.float32), waveform=np.zeros(1200,np.float32), energy=0., beat=0., bass=0., mid=0., treble=0., onset=0.)
        size = 4096
        x = self.frame(t, size)
        spec = np.abs(np.fft.rfft(x * np.hanning(size)))
        power = spec ** 0.65
        # Frequency buckets based on the actual sample rate.
        freqs = np.fft.rfftfreq(size, 1.0/self.sample_rate)
        def band(lo, hi):
            m = (freqs >= lo) & (freqs < hi)
            return float(np.mean(power[m])) if np.any(m) else 0.0
        bass, mid, treble = band(35, 180), band(180, 2500), band(2500, 12000)
        edges = np.geomspace(1, len(power), bands+1).astype(np.int32)
        s = np.empty(bands, np.float32)
        for i in range(bands):
            a=max(1,int(edges[i])); b=max(a+1,int(edges[i+1])); s[i]=np.mean(power[a:b])
        s=np.log1p(s*5.0); mx=float(np.percentile(s,96)); s=np.clip(s/(mx+1e-6),0,1).astype(np.float32)
        energy=float(np.sqrt(np.mean(x*x)))
        # Beat/onset: current energy against a short local history.
        prev_energy = 0.0
        if self._last is not None: prev_energy = self._last['energy']
        onset=float(np.clip((energy-max(prev_energy*1.08,0.035))*10.0,0,1))
        beat=float(np.clip((bass*0.75 + onset*0.9 + energy*1.8),0,1))
        wave=np.interp(np.linspace(0,len(x)-1,1200),np.arange(len(x)),x).astype(np.float32)
        result=dict(spectrum=s,waveform=wave,energy=energy,beat=beat,bass=float(np.clip(bass*3,0,1)),mid=float(np.clip(mid*3,0,1)),treble=float(np.clip(treble*3,0,1)),onset=onset)
        self._last_t=t; self._last=result
        return result
