from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import QRectF
from .visualizer import Visualizer
class RenderWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent); self.visualizer=Visualizer(); self.project=None; self.spectrum=[]; self.waveform=[]; self.time=0; self.energy=0; self.beat=0; self.bass=0; self.mid=0; self.treble=0; self.onset=0
    def paintEvent(self,event):
        p=QPainter(self); p.fillRect(self.rect(),QColor('#02040a'))
        if self.project:
            try:
                rw,rh=map(int,self.project.resolution.split('x')); ar=rw/rh; w=self.width(); h=int(w/ar)
                if h>self.height(): h=self.height(); w=int(h*ar)
                r=QRectF((self.width()-w)/2,(self.height()-h)/2,w,h)
                self.visualizer.draw(p,r,self.spectrum,self.waveform,self.time,self.project,self.energy,self.beat,self.bass,self.mid,self.treble,self.onset)
            except Exception:
                self.visualizer.draw(p,self.rect(),self.spectrum,self.waveform,self.time,self.project,self.energy,self.beat,self.bass,self.mid,self.treble,self.onset)
        p.end()
