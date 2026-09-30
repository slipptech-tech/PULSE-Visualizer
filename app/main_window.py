import os
from pathlib import Path
from PySide6.QtCore import Qt,QTimer,QUrl
from PySide6.QtGui import QColor
from PySide6.QtMultimedia import QAudioOutput,QMediaPlayer
from PySide6.QtWidgets import *
from .audio_engine import AudioEngine
from .project import Project,Layer
from .render_widget import RenderWidget
from .visualizer import Visualizer
from .exporter import ExportWorker
AUDIO_EXT='Audio (*.wav *.flac *.ogg *.mp3 *.m4a *.aac *.opus)'
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('Pulse Visualizer Studio 4');self.resize(1600,950);self.setAcceptDrops(True);self.audio=AudioEngine();self.project=self.default_project();self.worker=None;self.smooth_spec=None
        self.player=QMediaPlayer(self);self.out=QAudioOutput(self);self.out.setVolume(.85);self.player.setAudioOutput(self.out);self.player.positionChanged.connect(self.pos_changed);self.player.durationChanged.connect(self.dur_changed);self.player.errorOccurred.connect(self.player_error)
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.build_ui();self.apply_theme();self.timer.start(33)
    def default_project(self):return Project(layers=[Layer('Grid','grid',True,.25),Layer('Glow','glow',True,.8),Layer('Stars','stars',True,.6),Layer('Particles','particles',False,.7),Layer('Scanlines','scanlines',False,.3),Layer('Vignette','vignette',True,.8),Layer('Frame','frame',True,.8)])
    def apply_theme(self):self.setStyleSheet('''QMainWindow,QWidget{background:#070910;color:#edf0f8;font-family:"Segoe UI";}QGroupBox{border:1px solid #252c40;border-radius:10px;margin-top:12px;padding:10px;font-weight:700;}QGroupBox::title{left:12px;padding:0 6px;color:#a996ff;}QPushButton{background:#121824;border:1px solid #2a3348;border-radius:8px;padding:8px 12px;}QPushButton:hover{background:#1b2232;border-color:#7c5cff;}QComboBox,QLineEdit,QSpinBox,QDoubleSpinBox,QListWidget{background:#0d1119;border:1px solid #252d40;border-radius:7px;padding:6px;}QSlider::groove:horizontal{height:5px;background:#252c3c;}QSlider::sub-page:horizontal{background:#7c5cff;}QProgressBar{background:#0d1119;border:1px solid #252d40;border-radius:6px;height:8px;}QProgressBar::chunk{background:#7c5cff;}''')
    def build_ui(self):
        c=QWidget();self.setCentralWidget(c);root=QVBoxLayout(c);top=QHBoxLayout();title=QLabel('PULSE VISUALIZER STUDIO');title.setStyleSheet('font-size:22px;font-weight:800;');top.addWidget(title);top.addStretch()
        for n,s in [('Open Audio',self.open_audio),('New',self.new_project),('Save',self.save_project),('Load',self.load_project)]:b=QPushButton(n);b.clicked.connect(s);top.addWidget(b)
        self.export_btn=QPushButton('EXPORT');self.export_btn.clicked.connect(self.export_menu);top.addWidget(self.export_btn);root.addLayout(top)
        split=QSplitter(Qt.Horizontal);root.addWidget(split,1)
        left=QWidget();ll=QVBoxLayout(left);ll.addWidget(QLabel('VISUALS / LAYERS'));self.layers=QListWidget();self.layers.itemChanged.connect(self.layer_changed);ll.addWidget(self.layers,1)
        rr=QHBoxLayout();b=QPushButton('+ Layer');b.clicked.connect(self.add_layer);rr.addWidget(b);b=QPushButton('Remove');b.clicked.connect(self.remove_layer);rr.addWidget(b);ll.addLayout(rr)
        g=QGroupBox('Audio Reactive');f=QFormLayout(g);self.preset=QComboBox();self.preset.addItems(Visualizer.PRESETS);self.preset.currentTextChanged.connect(lambda x:self.setp('preset',x));f.addRow('Visual',self.preset)
        self.reactivity=QComboBox();self.reactivity.addItems(['Balanced','Beat / Kick','Bass Heavy','Melody / Mid','Treble / Hi-hat','Smooth']);self.reactivity.currentTextChanged.connect(lambda x:self.setp('reactivity',x));f.addRow('Reaction',self.reactivity)
        self.sens=self.spin(.2,3,.05,1);self.sens.valueChanged.connect(lambda x:self.setp('sensitivity',x));f.addRow('Sensitivity',self.sens);self.beat=self.spin(0,3,.05,1);self.beat.valueChanged.connect(lambda x:self.setp('beat_amount',x));f.addRow('Beat punch',self.beat);self.bass=self.spin(0,3,.05,1);self.bass.valueChanged.connect(lambda x:self.setp('bass_amount',x));f.addRow('Bass',self.bass);self.mid=self.spin(0,3,.05,.75);self.mid.valueChanged.connect(lambda x:self.setp('mid_amount',x));f.addRow('Mid',self.mid);self.treble=self.spin(0,3,.05,.65);self.treble.valueChanged.connect(lambda x:self.setp('treble_amount',x));f.addRow('Treble',self.treble);self.bars=QSpinBox();self.bars.setRange(32,192);self.bars.setValue(96);self.bars.valueChanged.connect(lambda x:self.setp('bar_count',x));f.addRow('Detail',self.bars);self.quality=QComboBox();self.quality.addItems(['Draft','Balanced','High']);self.quality.currentTextChanged.connect(lambda x:self.setp('quality',x));f.addRow('Quality',self.quality);self.glow=QSlider(Qt.Horizontal);self.glow.setRange(0,100);self.glow.setValue(75);self.glow.valueChanged.connect(lambda x:self.setp('glow',x/100));f.addRow('Glow',self.glow);ll.addWidget(g)
        g2=QGroupBox('Canvas / Export');f2=QFormLayout(g2);self.aspect=QComboBox();self.aspect.addItems(['16:9','21:9','4:3','1:1','4:5','9:16','3:2','Custom']);self.aspect.currentTextChanged.connect(self.change_aspect);f2.addRow('Aspect',self.aspect);self.res=QComboBox();self.res.addItems(['1280x720','1920x1080','2560x1440','3840x2160','1080x1920','1080x1080']);self.res.currentTextChanged.connect(lambda x:self.setp('resolution',x));f2.addRow('Resolution',self.res);self.fps=QComboBox();self.fps.addItems(['24','30','60']);self.fps.setCurrentText('30');self.fps.currentTextChanged.connect(lambda x:self.setp('fps',int(x)));f2.addRow('FPS',self.fps);bg=QPushButton('Background');bg.clicked.connect(self.choose_bg);f2.addRow(bg);a=QPushButton('Primary');a.clicked.connect(self.choose_accent);f2.addRow(a);a=QPushButton('Secondary');a.clicked.connect(self.choose_accent2);f2.addRow(a);a=QPushButton('Accent 3');a.clicked.connect(self.choose_accent3);f2.addRow(a);ll.addWidget(g2);split.addWidget(left)
        center=QWidget();cl=QVBoxLayout(center);self.status=QLabel('Drop a song here — visuals react to bass, melody and hits');cl.addWidget(self.status);self.preview=RenderWidget();self.preview.project=self.project;cl.addWidget(self.preview,1);ctl=QHBoxLayout();self.time_label=QLabel('0:00 / 0:00');ctl.addWidget(self.time_label);self.position=QSlider(Qt.Horizontal);self.position.sliderMoved.connect(self.seek);ctl.addWidget(self.position,1);cl.addLayout(ctl);pb=QHBoxLayout();self.play=QPushButton('▶ Play');self.play.clicked.connect(self.toggle_play);pb.addWidget(self.play);stop=QPushButton('■ Stop');stop.clicked.connect(self.stop);pb.addWidget(stop);self.volume=QSlider(Qt.Horizontal);self.volume.setRange(0,100);self.volume.setValue(85);self.volume.valueChanged.connect(lambda x:self.out.setVolume(x/100));pb.addWidget(QLabel('Volume'));pb.addWidget(self.volume);cl.addLayout(pb);self.pbar=QProgressBar();self.pbar.setValue(0);self.pbar.setVisible(False);cl.addWidget(self.pbar);self.cancel=QPushButton('Cancel export');self.cancel.setVisible(False);self.cancel.clicked.connect(self.cancel_export);cl.addWidget(self.cancel);split.addWidget(center);split.setSizes([360,1100])
    def spin(self,a,b,step,val):w=QDoubleSpinBox();w.setRange(a,b);w.setSingleStep(step);w.setValue(val);return w
    def setp(self,k,v):setattr(self.project,k,v);self.preview.update()
    def populate(self):
        self.layers.blockSignals(True);self.layers.clear();
        for L in self.project.layers:
            it=QListWidgetItem(L.name);it.setFlags(it.flags()|Qt.ItemIsUserCheckable);it.setCheckState(Qt.Checked if L.enabled else Qt.Unchecked);self.layers.addItem(it)
        self.layers.blockSignals(False)
    def layer_changed(self,it):
        i=self.layers.row(it)
        if 0<=i<len(self.project.layers):self.project.layers[i].enabled=it.checkState()==Qt.Checked;self.preview.update()
    def add_layer(self):
        names=[x[0] for x in Visualizer.LAYERS];name,ok=QInputDialog.getItem(self,'Add layer','Layer:',names,0,False)
        if ok:self.project.layers.append(Layer(name,dict(Visualizer.LAYERS)[name],True,.7));self.populate()
    def remove_layer(self):
        i=self.layers.currentRow()
        if i>=0:self.project.layers.pop(i);self.populate()
    def open_audio(self):
        path,_=QFileDialog.getOpenFileName(self,'Open audio','',AUDIO_EXT)
        if path:self.load_audio(path)
    def load_audio(self,path):
        try:
            self.audio.load(path);self.player.setSource(QUrl.fromLocalFile(path));self.status.setText(Path(path).name);self.position.setRange(0,max(1,int(self.audio.duration*1000)));self.player.play()
        except Exception as e:QMessageBox.critical(self,'Audio error',str(e))
    def tick(self):
        if not self.audio.path:return
        t=self.player.position()/1000; a=self.audio.analyze(t,self.project.bar_count);self.preview.time=t;self.preview.spectrum=a['spectrum'];self.preview.waveform=a['waveform'];self.preview.energy=a['energy'];self.preview.beat=a['beat'];self.preview.bass=a['bass'];self.preview.mid=a['mid'];self.preview.treble=a['treble'];self.preview.onset=a['onset'];self.preview.update()
    def toggle_play(self):
        if self.player.playbackState()==QMediaPlayer.PlayingState:self.player.pause();self.play.setText('▶ Play')
        else:self.player.play();self.play.setText('❚❚ Pause')
    def stop(self):self.player.stop();self.play.setText('▶ Play')
    def pos_changed(self,p):self.position.blockSignals(True);self.position.setValue(p);self.position.blockSignals(False);self.time_label.setText(f'{p//60000}:{(p//1000)%60:02d} / {int(self.audio.duration)//60}:{int(self.audio.duration)%60:02d}')
    def dur_changed(self,p):self.position.setRange(0,max(1,p))
    def seek(self,p):self.player.setPosition(p)
    def player_error(self,e,msg):
        if msg:self.status.setText('Player: '+msg)
    def new_project(self):self.project=self.default_project();self.preview.project=self.project;self.populate();self.sync_controls();self.preview.update()
    def sync_controls(self):
        self.preset.setCurrentText(self.project.preset);self.aspect.setCurrentText(self.project.aspect_ratio);self.res.setCurrentText(self.project.resolution);self.fps.setCurrentText(str(self.project.fps));self.quality.setCurrentText(self.project.quality);self.reactivity.setCurrentText(self.project.reactivity);self.sens.setValue(self.project.sensitivity);self.beat.setValue(self.project.beat_amount);self.bass.setValue(self.project.bass_amount);self.mid.setValue(self.project.mid_amount);self.treble.setValue(self.project.treble_amount);self.bars.setValue(self.project.bar_count);self.glow.setValue(int(self.project.glow*100))
    def save_project(self):
        path,_=QFileDialog.getSaveFileName(self,'Save project','visual.pulse.json','Pulse Project (*.pulse.json)')
        if path:self.project.save(path)
    def load_project(self):
        path,_=QFileDialog.getOpenFileName(self,'Load project','','Pulse Project (*.pulse.json *.json)')
        if path:
            try:self.project=Project.load(path);self.preview.project=self.project;self.populate();self.sync_controls();self.preview.update()
            except Exception as e:QMessageBox.critical(self,'Project error',str(e))
    def change_aspect(self,x):
        self.project.aspect_ratio=x
        if x!='Custom':
            ratios={'16:9':(16,9),'21:9':(21,9),'4:3':(4,3),'1:1':(1,1),'4:5':(4,5),'9:16':(9,16),'3:2':(3,2)};a,b=ratios[x];w,h=map(int,self.project.resolution.split('x'));self.project.resolution=f'{w}x{max(1,round(w*b/a))}'
        self.preview.update()
    def selected_size(self):
        try:return tuple(map(int,self.project.resolution.split('x')))
        except:return (1920,1080)
    def export_menu(self):
        if self.worker:return
        mode,ok=QInputDialog.getItem(self,'Export','Type:',['MP4 video','PNG frame','PNG sequence'],0,False)
        if not ok:return
        if mode=='PNG frame':
            out,_=QFileDialog.getSaveFileName(self,'Save PNG','visual.png','PNG (*.png)');m='frame'
        elif mode=='PNG sequence':
            out=QFileDialog.getExistingDirectory(self,'Select frame folder');m='sequence'
        else:
            out,_=QFileDialog.getSaveFileName(self,'Save MP4','visual.mp4','MP4 (*.mp4)');m='video'
        if not out:return
        w,h=self.selected_size();self.pbar.setVisible(True);self.cancel.setVisible(True);self.cancel.setEnabled(True);self.export_btn.setEnabled(False);self.pbar.setValue(0);self.worker=ExportWorker(m,self.project,self.audio.path,out,w,h,self.project.fps,self.audio.duration if self.audio.path else 5);self.worker.progress.connect(self.pbar.setValue);self.worker.status.connect(self.status.setText);self.worker.done.connect(self.export_done);self.worker.failed.connect(self.export_failed);self.worker.start()
    def cancel_export(self):
        if self.worker:self.worker.cancel();self.status.setText('Cancelling…')
    def export_done(self,path):self.pbar.setVisible(False);self.cancel.setVisible(False);self.export_btn.setEnabled(True);self.worker=None;self.status.setText('Export complete: '+str(path));
    def export_failed(self,msg):self.pbar.setVisible(False);self.cancel.setVisible(False);self.export_btn.setEnabled(True);self.worker=None;QMessageBox.critical(self,'Export failed',msg);self.status.setText('Export failed')
    def choose_bg(self):c=QColorDialog.getColor(QColor(self.project.background),self);c.isValid() and self.setp('background',c.name())
    def choose_accent(self):c=QColorDialog.getColor(QColor(self.project.accent),self);c.isValid() and self.setp('accent',c.name())
    def choose_accent2(self):c=QColorDialog.getColor(QColor(self.project.accent2),self);c.isValid() and self.setp('accent2',c.name())
    def choose_accent3(self):c=QColorDialog.getColor(QColor(self.project.accent3),self);c.isValid() and self.setp('accent3',c.name())
    def dragEnterEvent(self,e):
        if any(u.isLocalFile() and Path(u.toLocalFile()).suffix.lower() in self.audio.SUPPORTED_EXTENSIONS for u in e.mimeData().urls()):e.acceptProposedAction()
    def dropEvent(self,e):
        for u in e.mimeData().urls():
            if u.isLocalFile() and Path(u.toLocalFile()).suffix.lower() in self.audio.SUPPORTED_EXTENSIONS:self.load_audio(u.toLocalFile());e.acceptProposedAction();return
    def closeEvent(self,e):
        if self.worker and self.worker.isRunning():self.worker.cancel();self.worker.wait(3000)
        self.player.stop();self.audio.close();e.accept()
