import os, shutil, subprocess, tempfile
from pathlib import Path
from copy import deepcopy
import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage, QPainter
from .visualizer import Visualizer

class ExportWorker(QThread):
    progress=Signal(int); status=Signal(str); done=Signal(str); failed=Signal(str)
    def __init__(self,mode,project,audio_path,out_path,width,height,fps,duration):
        super().__init__(); self.mode=mode; self.project=deepcopy(project); self.audio_path=audio_path; self.out_path=out_path; self.width=width; self.height=height; self.fps=fps; self.duration=duration; self.cancelled=False; self.data=None; self.sr=0
    def cancel(self): self.cancelled=True
    def analyze(self,t):
        if self.data is None:return dict(spectrum=np.zeros(self.project.bar_count,np.float32),waveform=np.zeros(1200,np.float32),energy=0,beat=0,bass=0,mid=0,treble=0,onset=0)
        size=4096; center=int(max(0,t)*self.sr); start=center-size//2; end=start+size; a=max(0,start); b=min(len(self.data),end); x=self.data[a:b]
        if start<0 or end>len(self.data):x=np.pad(x,(max(0,-start),max(0,end-len(self.data))))
        x=x[:size].astype(np.float32); spec=np.abs(np.fft.rfft(x*np.hanning(size)))**.65; freqs=np.fft.rfftfreq(size,1/self.sr)
        def band(lo,hi):
            m=(freqs>=lo)&(freqs<hi);return float(np.mean(spec[m])) if np.any(m) else 0
        bass,mid,treble=band(35,180),band(180,2500),band(2500,12000);edges=np.geomspace(1,len(spec),self.project.bar_count+1).astype(np.int32);s=np.empty(self.project.bar_count,np.float32)
        for i in range(self.project.bar_count):
            aa=max(1,int(edges[i]));bb=max(aa+1,int(edges[i+1]));s[i]=np.mean(spec[aa:bb])
        s=np.log1p(s*5);mx=float(np.percentile(s,96));s=np.clip(s/(mx+1e-6),0,1);energy=float(np.sqrt(np.mean(x*x)));wave=np.interp(np.linspace(0,len(x)-1,1200),np.arange(len(x)),x)
        beat=float(np.clip(bass*2.2+energy*2.0,0,1));return dict(spectrum=s.astype(np.float32),waveform=wave.astype(np.float32),energy=energy,beat=beat,bass=float(np.clip(bass*3,0,1)),mid=float(np.clip(mid*3,0,1)),treble=float(np.clip(treble*3,0,1)),onset=beat)
    def make_frame(self,vis,t):
        a=self.analyze(t); img=QImage(self.width,self.height,QImage.Format.Format_RGB32);img.fill(0);p=QPainter(img);vis.draw(p,img.rect(),a['spectrum'],a['waveform'],t,self.project,**{k:a[k] for k in ('energy','beat','bass','mid','treble','onset')});p.end();return img
    def ffmpeg(self):
        f=shutil.which('ffmpeg')
        if not f: raise RuntimeError('FFmpeg was not found in PATH. Install FFmpeg and restart the program.')
        return f
    def load_audio(self):
        if not self.audio_path or not os.path.exists(self.audio_path):return
        import soundfile as sf
        try:
            d,sr=sf.read(self.audio_path,dtype='float32',always_2d=False)
        except Exception:
            ff=self.ffmpeg(); fd,wav=tempfile.mkstemp(suffix='.wav');os.close(fd);r=subprocess.run([ff,'-y','-loglevel','error','-i',self.audio_path,'-ac','1','-ar','48000',wav],capture_output=True,text=True)
            if r.returncode:raise RuntimeError(r.stderr[-1800:])
            d,sr=sf.read(wav,dtype='float32');os.unlink(wav)
        if getattr(d,'ndim',1)>1:d=np.mean(d,axis=1)
        self.data=np.asarray(d,np.float32);self.sr=int(sr)
    def run(self):
        try:
            self.load_audio();total=max(1,int(round(self.duration*self.fps)));vis=Visualizer()
            if self.mode=='frame':
                if not self.make_frame(vis,0).save(self.out_path,'PNG'):raise RuntimeError('Could not write PNG file.')
                self.done.emit(self.out_path);return
            if self.mode=='sequence':
                out=Path(self.out_path);out.mkdir(parents=True,exist_ok=True)
                for i in range(total):
                    if self.cancelled:self.done.emit('Cancelled');return
                    self.make_frame(vis,i/self.fps).save(str(out/f'frame_{i:06d}.png'),'PNG');self.progress.emit(int((i+1)/total*100))
                self.done.emit(str(out));return
            ff=self.ffmpeg();tmp=Path(tempfile.mkdtemp(prefix='pulse_render_'));self.status.emit('Rendering frames…')
            for i in range(total):
                if self.cancelled:shutil.rmtree(tmp,ignore_errors=True);self.done.emit('Cancelled');return
                self.make_frame(vis,i/self.fps).save(str(tmp/f'frame_{i:06d}.png'),'PNG');self.progress.emit(int((i+1)/total*75))
            cmd=[ff,'-y','-loglevel','error','-framerate',str(self.fps),'-i',str(tmp/'frame_%06d.png')]
            if self.audio_path and os.path.exists(self.audio_path):cmd += ['-i',self.audio_path,'-map','0:v:0','-map','1:a:0','-c:a','aac','-b:a','192k','-shortest']
            cmd += ['-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',self.out_path]
            self.status.emit('Encoding MP4…');r=subprocess.run(cmd,capture_output=True,text=True)
            shutil.rmtree(tmp,ignore_errors=True)
            if r.returncode:raise RuntimeError('FFmpeg export failed:\n'+r.stderr[-3000:])
            self.progress.emit(100);self.done.emit(self.out_path)
        except (BrokenPipeError, OSError) as e:
            self.failed.emit('Export process stopped unexpectedly.\n\n'+str(e))
        except Exception as e:self.failed.emit(str(e))
