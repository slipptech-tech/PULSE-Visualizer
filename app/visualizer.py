import math
import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QLinearGradient, QRadialGradient, QPainterPath

class Visualizer:
    PRESETS = [
        'Neon Spectrum','Beat Reactor','Cyber Bars','Liquid Neon','Orbital Pulse','Neon Tunnel','Galaxy Bloom','Audio DNA',
        'Laser Wave','Radial Core','Pulse Rings','Spectrum Globe','Aurora Flow','Particles Storm','Vortex','Lissajous Pro',
        'Digital Rain','Hex Grid','Fireworks Beat','Energy Mountain','Wave Ribbon','Radar Pulse','Plasma Core','Mirror Energy',
        'Frequency Spiral','Cosmic Equalizer','Electric Web','Neon Flower','Bass Reactor','Oscilloscope Pro'
    ]
    LAYERS=[('Grid','grid'),('Glow','glow'),('Stars','stars'),('Particles','particles'),('Scanlines','scanlines'),('Vignette','vignette'),('Frame','frame')]
    def color(self,v,a=255):
        c=QColor(v); c.setAlpha(max(0,min(255,int(a)))); return c
    def features(self, s, pr, e):
        s=np.asarray(s,dtype=np.float32); n=len(s)
        bass=float(np.mean(s[:max(2,n//10)])); mid=float(np.mean(s[n//10:max(3,n//2)])); treble=float(np.mean(s[n//2:]))
        return bass*pr.bass_amount, mid*pr.mid_amount, treble*pr.treble_amount
    def draw(self,p,r,s,w,t,pr,energy=0,beat=0,bass=0,mid=0,treble=0,onset=0):
        # Preview/export quality controls the number of expensive primitives.
        q={'Draft':0.55,'Balanced':0.8,'High':1.0}.get(pr.quality,0.8)
        p.setRenderHint(QPainter.Antialiasing, q>=0.8)
        self.background(p,r,pr)
        enabled={x.kind for x in pr.layers if x.enabled}
        if 'grid' in enabled:self.grid(p,r,pr)
        if 'stars' in enabled:self.stars(p,r,t,pr,q,beat)
        if 'glow' in enabled:self.glow(p,r,energy,beat,pr)
        fn=getattr(self,'v_'+pr.preset.lower().replace(' ','_'),self.v_neon_spectrum)
        fn(p,r,s,w,t,pr,energy,beat,bass,mid,treble,onset,q)
        if 'particles' in enabled:self.particles(p,r,t,pr,q,energy,beat)
        if 'scanlines' in enabled:self.scanlines(p,r,q)
        if 'vignette' in enabled:self.vignette(p,r)
        if 'frame' in enabled:
            p.setPen(QPen(self.color(pr.accent,130),2));p.setBrush(Qt.NoBrush);p.drawRoundedRect(r.adjusted(7,7,-7,-7),16,16)
    def background(self,p,r,pr):
        g=QLinearGradient(r.topLeft(),r.bottomRight());g.setColorAt(0,self.color(pr.background));g.setColorAt(.5,self.color(pr.background));g.setColorAt(1,self.color(pr.accent,45));p.fillRect(r,g)
    def glow(self,p,r,e,b,pr):
        rad=min(r.width(),r.height())*(.25+.12*b);g=QRadialGradient(r.center(),rad);g.setColorAt(0,self.color(pr.accent,50+70*b));g.setColorAt(.55,self.color(pr.accent2,18));g.setColorAt(1,self.color(pr.accent,0));p.setBrush(g);p.setPen(Qt.NoPen);p.drawEllipse(r.center(),r.width()*.5,r.height()*.5)
    def grid(self,p,r,pr):
        p.setPen(QPen(self.color(pr.accent,25),1));step=max(42,int(min(r.width(),r.height())/15));
        for x in range(int(r.left()),int(r.right()),step):p.drawLine(x,r.top(),x,r.bottom())
        for y in range(int(r.top()),int(r.bottom()),step):p.drawLine(r.left(),y,r.right(),y)
    def stars(self,p,r,t,pr,q,beat):
        n=int(55*q)
        for i in range(n):
            a=i*2.37;z=(math.sin(i*9.17)*.5+.5);x=.5+math.sin(a+t*(.02+z*.05))*.48;y=.5+math.cos(a*1.4+t*(.02+z*.05))*.46;sz=.5+z*1.8+beat*1.8;p.setPen(Qt.NoPen);p.setBrush(self.color(pr.accent2 if i%5==0 else pr.accent,70+int(z*130)));p.drawEllipse(QPointF(r.left()+x*r.width(),r.top()+y*r.height()),sz,sz)
    def particles(self,p,r,t,pr,q,e,b):
        n=int(100*q);c=r.center()
        for i in range(n):
            a=i*2.399+t*(.15+(i%5)*.01);rad=((i*47)%1000)/1000;rad=(rad+e*.07)%1;x=c.x()+math.cos(a)*rad*r.width()*.47;y=c.y()+math.sin(a)*rad*r.height()*.47;sz=.8+(i%3)*.45+b*2;p.setPen(Qt.NoPen);p.setBrush(self.color(pr.accent2 if i%3==0 else pr.accent,100+int(90*(1-rad))));p.drawEllipse(QPointF(x,y),sz,sz)
    def scanlines(self,p,r,q):
        p.setPen(QPen(QColor(255,255,255,10),1)); step=5 if q<1 else 4
        for y in range(int(r.top()),int(r.bottom()),step):p.drawLine(r.left(),y,r.right(),y)
    def vignette(self,p,r):
        g=QRadialGradient(r.center(),max(r.width(),r.height())*.7);g.setColorAt(.55,QColor(0,0,0,0));g.setColorAt(1,QColor(0,0,0,185));p.fillRect(r,g)
    def vals(self,s,n): return np.resize(np.asarray(s,dtype=np.float32),n)
    def polyline(self,p,pts,color,width):
        if len(pts)<2:return
        path=QPainterPath(pts[0]);
        for pt in pts[1:]:path.lineTo(pt)
        p.setPen(QPen(color,width));p.setBrush(Qt.NoBrush);p.drawPath(path)
    def reactive_scale(self,base,pr,b,amount=1):return base*(1+pr.beat_amount*amount*b)
    def v_neon_spectrum(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        v=self.vals(s,max(32,min(pr.bar_count,160)));cw=r.width()/len(v);base=r.bottom();
        for i,x in enumerate(v):
            h=min(r.height()*.88,float(x)*r.height()*.82*pr.sensitivity*(1+b*pr.beat_amount*.35));xx=r.left()+i*cw+1;g=QLinearGradient(xx,base,xx,base-h);g.setColorAt(0,self.color(pr.accent,230));g.setColorAt(.5,self.color(pr.accent2,235));g.setColorAt(1,self.color(pr.accent3,230));p.setBrush(g);p.setPen(Qt.NoPen);p.drawRoundedRect(QRectF(xx,base-h,max(2,cw-2),h),4,4)
    def v_beat_reactor(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();rad=min(r.width(),r.height())*.18*(1+b*.8);p.setBrush(self.color(pr.accent,70+int(b*70)));p.setPen(QPen(self.color(pr.accent2,230),3+b*6));p.drawEllipse(c,rad,rad)
        v=self.vals(s,64);R=min(r.width(),r.height())*.34
        for i,x in enumerate(v):
            a=i/64*math.tau;rr=R+float(x)*R*.55*pr.sensitivity+b*R*.15; p.setPen(QPen(self.color(pr.accent2 if i%2 else pr.accent3,180),2.5));p.drawLine(QPointF(c.x()+math.cos(a)*R,c.y()+math.sin(a)*R),QPointF(c.x()+math.cos(a)*rr,c.y()+math.sin(a)*rr))
    v_beat_reactor=v_beat_reactor
    def v_cyber_bars(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        v=self.vals(s,64);cw=r.width()/64
        for i,x in enumerate(v):
            h=float(x)*r.height()*.75*pr.sensitivity*(1+b*.35);xx=r.left()+i*cw;p.setBrush(self.color(pr.accent2 if i%3 else pr.accent3,180));p.setPen(Qt.NoPen);p.drawRect(QRectF(xx+1,r.bottom()-h,max(2,cw-3),h));p.setBrush(self.color(pr.accent,35));p.drawRect(QRectF(xx+1,r.bottom()-h-8,max(2,cw-3),5))
    def v_liquid_neon(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        v=self.vals(s,100)
        for j in range(4):
            pts=[]
            for i,x in enumerate(v):
                xx=r.left()+i/99*r.width();yy=r.center().y()+(j-1.5)*r.height()*.13+math.sin(i*.09+t*(.65+j*.08)+j)*r.height()*.07*(1+float(x)*.9+ b*.3);pts.append(QPointF(xx,yy))
            self.polyline(p,pts,self.color(pr.accent2 if j%2 else pr.accent3,150),4)
    def v_orbital_pulse(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();R=min(r.width(),r.height())*.24*(1+b*.12)
        for j in range(4):
            rr=R*(.65+j*.32);p.setPen(QPen(self.color(pr.accent if j%2 else pr.accent2,150),2));p.drawEllipse(c,rr,rr*.58)
            a=t*(.35+j*.13);pt=QPointF(c.x()+math.cos(a)*rr,c.y()+math.sin(a)*rr*.58);p.setBrush(self.color(pr.accent3,230));p.setPen(Qt.NoPen);p.drawEllipse(pt,5+b*5,5+b*5)
    def v_neon_tunnel(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();n=18
        for i in range(n):
            z=((i/n+t*.22*(1+b*.5))%1);scale=.05+z*1.15;rr=QRectF(c.x()-r.width()*scale/2,c.y()-r.height()*scale/2,r.width()*scale,r.height()*scale);p.setPen(QPen(self.color(pr.accent if i%2 else pr.accent2,int(210*(1-z))),2+b*2));p.setBrush(Qt.NoBrush);p.drawRoundedRect(rr,18,18)
    def v_galaxy_bloom(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();n=int(260*q);v=self.vals(s,n)
        for i in range(n):
            a=i*.19+t*(.15+(i%8)*.004);rad=(i/n)**.72*min(r.width(),r.height())*.46*(.75+float(v[i])*.25+b*.08);x=c.x()+math.cos(a+rad*.004)*rad;y=c.y()+math.sin(a+rad*.004)*rad*.55;sz=.7+(i%3)*.4+b*1.4;p.setPen(Qt.NoPen);p.setBrush(self.color(pr.accent2 if i%7==0 else pr.accent,70+int(100*(1-i/n))));p.drawEllipse(QPointF(x,y),sz,sz)
    def v_audio_dna(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        v=self.vals(s,72);x0=r.left()+r.width()*.12
        for i,x in enumerate(v):
            xx=x0+i/71*r.width()*.76;ph=i*.25+t*1.7;y1=r.center().y()+math.sin(ph)*r.height()*.25*(1+float(x)*.3);y2=r.center().y()-math.sin(ph)*r.height()*.25*(1+float(x)*.3);p.setPen(QPen(self.color(pr.accent2,190),1.5));p.drawLine(QPointF(xx,y1),QPointF(xx,y2));p.setPen(Qt.NoPen);p.setBrush(self.color(pr.accent3,220));p.drawEllipse(QPointF(xx,y1),3+b*2,3+b*2);p.drawEllipse(QPointF(xx,y2),3+b*2,3+b*2)
    def v_laser_wave(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        v=self.vals(s,180);pts=[QPointF(r.left()+i/179*r.width(),r.center().y()+math.sin(i*.08+t*1.2)*r.height()*.06-float(v[i])*r.height()*.22*pr.sensitivity) for i in range(180)];self.polyline(p,pts,self.color(pr.accent2,240),2.5+b*2)
        self.polyline(p,[QPointF(x.x(),2*r.center().y()-x.y()) for x in pts],self.color(pr.accent3,130),2)
    def v_radial_core(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();v=self.vals(s,72);R=min(r.width(),r.height())*.13
        for i,x in enumerate(v):
            a=i/72*math.tau+t*.1;rr=R+float(x)*min(r.width(),r.height())*.34*pr.sensitivity+b*20;p.setPen(QPen(self.color(pr.accent2 if i%2 else pr.accent3,210),2));p.drawLine(QPointF(c.x()+math.cos(a)*R,c.y()+math.sin(a)*R),QPointF(c.x()+math.cos(a)*rr,c.y()+math.sin(a)*rr))
        p.setBrush(self.color(pr.accent,100));p.setPen(QPen(self.color(pr.accent2,220),3));p.drawEllipse(c,R*(1+b),R*(1+b))
    def v_pulse_rings(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();m=min(r.width(),r.height())
        for i in range(11):
            phase=(t*.18+i*.075)%1;rr=m*(.04+i*.055+phase*.025+b*.025);p.setPen(QPen(self.color(pr.accent if i%2 else pr.accent2,int(160*(1-phase))),2+b*2));p.drawEllipse(c,rr,rr)
    def v_spectrum_globe(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();R=min(r.width(),r.height())*.23;v=self.vals(s,96)
        p.setBrush(self.color(pr.accent,45));p.setPen(QPen(self.color(pr.accent2,170),2));p.drawEllipse(c,R,R)
        for i,x in enumerate(v):
            a=i/96*math.tau+t*.18;rr=R+float(x)*R*.9+b*12;p.setPen(QPen(self.color(pr.accent3 if i%3==0 else pr.accent2,180),2));p.drawLine(QPointF(c.x()+math.cos(a)*R,c.y()+math.sin(a)*R),QPointF(c.x()+math.cos(a)*rr,c.y()+math.sin(a)*rr))
    def v_aurora_flow(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        v=self.vals(s,90)
        for j in range(5):
            pts=[]
            for i,x in enumerate(v):pts.append(QPointF(r.left()+i/89*r.width(),r.top()+r.height()*.25+j*r.height()*.12+math.sin(i*.08+t*(.45+j*.06))*r.height()*.06-float(x)*r.height()*.1))
            self.polyline(p,pts,self.color(pr.accent2 if j%2 else pr.accent3,100),5)
    def v_particles_storm(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):self.particles(p,r,t*1.5,pr,q,e*1.3,b*1.2)
    def v_vortex(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();v=self.vals(s,120);pts=[]
        for i,x in enumerate(v):
            z=i/119;a=i*.15+t*.7;rr=min(r.width(),r.height())*(.03+z*.43)*(1+float(x)*.25+b*.1);pts.append(QPointF(c.x()+math.cos(a)*rr,c.y()+math.sin(a)*rr*.65))
        self.polyline(p,pts,self.color(pr.accent2,220),2.5)
    def v_lissajous_pro(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();pts=[]
        for i in range(260):
            a=i/259*math.tau*2;x=math.sin(3*a+t)*r.width()*.32*(.75+b*.12);y=math.sin(2*a+t*1.31)*r.height()*.30*(.75+b*.12);pts.append(QPointF(c.x()+x,c.y()+y))
        self.polyline(p,pts,self.color(pr.accent2,220),2.5)
    def v_digital_rain(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        n=34
        for i in range(n):
            x=r.left()+i/(n-1)*r.width();phase=(i*.17+t*(.25+(i%4)*.03))%1;length=r.height()*(.08+.3*((i*13)%7)/7);y=r.top()+phase*r.height();p.setPen(QPen(self.color(pr.accent2 if i%3 else pr.accent3,130),2));p.drawLine(x,y,x,y+length*(1+b*.5))
    def v_hex_grid(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        size=min(r.width(),r.height())*.055*(1+b*.06);p.setPen(QPen(self.color(pr.accent2,70),1.2));
        for row in range(-8,9):
            for col in range(-14,15):
                x=r.center().x()+col*size*1.7+(row%2)*size*.85;y=r.center().y()+row*size*1.5;p.drawPolygon([QPointF(x+math.cos(k*math.pi/3)*size,y+math.sin(k*math.pi/3)*size) for k in range(6)])
    def v_fireworks_beat(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();R=min(r.width(),r.height())*(.12+b*.22)
        for i in range(54):
            a=i/54*math.tau;rr=R*(.4+((i*17)%10)/10);p.setPen(QPen(self.color(pr.accent2 if i%2 else pr.accent3,180),2));p.drawLine(c,QPointF(c.x()+math.cos(a)*rr,c.y()+math.sin(a)*rr))
    def v_energy_mountain(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        v=self.vals(s,110);pts=[QPointF(r.left(),r.bottom())]
        for i,x in enumerate(v):pts.append(QPointF(r.left()+i/109*r.width(),r.bottom()-float(x)*r.height()*.78*pr.sensitivity*(1+b*.25)))
        pts += [QPointF(r.right(),r.bottom())];path=QPainterPath(pts[0]);
        for pt in pts[1:]:path.lineTo(pt)
        path.closeSubpath();g=QLinearGradient(0,r.top(),0,r.bottom());g.setColorAt(0,self.color(pr.accent2,190));g.setColorAt(1,self.color(pr.accent3,25));p.setBrush(g);p.setPen(QPen(self.color(pr.accent2,220),2));p.drawPath(path)
    def v_wave_ribbon(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):self.v_liquid_neon(p,r,s,w,t,pr,e,b,ba,mi,tr,on,q)
    def v_radar_pulse(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();R=min(r.width(),r.height())*.38;p.setPen(QPen(self.color(pr.accent,70),1));
        for k in range(1,5):p.drawEllipse(c,R*k/4,R*k/4)
        a=t*.8; p.setPen(QPen(self.color(pr.accent2,230),3+b*3));p.drawLine(c,QPointF(c.x()+math.cos(a)*R,c.y()+math.sin(a)*R))
    def v_plasma_core(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();R=min(r.width(),r.height())*.2*(1+b*.25);p.setBrush(self.color(pr.accent,75));p.setPen(QPen(self.color(pr.accent2,230),4+b*5));p.drawEllipse(c,R,R)
        for j in range(5):
            pts=[QPointF(r.left()+i/80*r.width(),r.center().y()+math.sin(i*.11+t*(.5+j*.08)+j)*r.height()*.05*(1+b)+ (j-2)*r.height()*.07) for i in range(81)];self.polyline(p,pts,self.color(pr.accent3 if j%2 else pr.accent2,75),3)
    def v_mirror_energy(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        v=self.vals(s,70);cw=r.width()/70;mid=r.center().y()
        for i,x in enumerate(v):
            h=min(r.height()*.38,float(x)*r.height()*.42*pr.sensitivity*(1+b*.3));xx=r.left()+i*cw;p.setBrush(self.color(pr.accent2 if i%2 else pr.accent3,210));p.setPen(Qt.NoPen);p.drawRoundedRect(QRectF(xx+1,mid-h,max(2,cw-2),h),3,3);p.drawRoundedRect(QRectF(xx+1,mid,max(2,cw-2),h),3,3)
    def v_frequency_spiral(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();v=self.vals(s,180);pts=[]
        for i,x in enumerate(v):
            z=i/179;a=i*.16+t*.55;rr=min(r.width(),r.height())*(.02+z*.42)*(1+float(x)*.35+b*.08);pts.append(QPointF(c.x()+math.cos(a)*rr,c.y()+math.sin(a)*rr))
        self.polyline(p,pts,self.color(pr.accent2,220),2.5)
    def v_cosmic_equalizer(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        self.v_neon_spectrum(p,r,s,w,t,pr,e,b,ba,mi,tr,on,q);p.setPen(QPen(self.color(pr.accent3,110),1));p.drawEllipse(r.center(),min(r.width(),r.height())*.23*(1+b*.2),min(r.width(),r.height())*.23*(1+b*.2))
    def v_electric_web(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        v=self.vals(s,30);pts=[QPointF(r.left()+i/29*r.width(),r.center().y()+math.sin(i*.45+t)*r.height()*.22*float(v[i])) for i in range(30)];
        for i in range(29):p.setPen(QPen(self.color(pr.accent2 if i%2 else pr.accent3,100),1.5));p.drawLine(pts[i],pts[i+1])
        for i in range(0,29,3):
            for j in range(i+3,30,5):p.setPen(QPen(self.color(pr.accent,35),1));p.drawLine(pts[i],pts[j])
    def v_neon_flower(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();v=self.vals(s,80)
        for i,x in enumerate(v):
            a=i/80*math.tau+t*.12;rr=min(r.width(),r.height())*(.12+float(x)*.27)*(1+b*.15);p.setPen(QPen(self.color(pr.accent2 if i%2 else pr.accent3,180),2));p.drawLine(c,QPointF(c.x()+math.cos(a)*rr,c.y()+math.sin(a)*rr))
    def v_bass_reactor(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        c=r.center();R=min(r.width(),r.height())*.12+ba*min(r.width(),r.height())*.22+b*25;p.setBrush(self.color(pr.accent,70));p.setPen(QPen(self.color(pr.accent2,230),4+ba*5));p.drawEllipse(c,R,R)
        for i in range(6):
            rr=R*(1.25+i*.23);p.setPen(QPen(self.color(pr.accent3 if i%2 else pr.accent2,100),2));p.drawEllipse(c,rr,rr*.7)
    def v_oscilloscope_pro(self,p,r,s,w,t,pr,e,b,ba,mi,tr,on,q):
        w=self.vals(w,900);pts=[QPointF(r.left()+i/899*r.width(),r.center().y()-float(v)*r.height()*.36*(1+b*.15)) for i,v in enumerate(w)];self.polyline(p,pts,self.color(pr.accent2,230),2.5)
