import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QStyle, QMessageBox,
    QMenu
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, QUrl, QTimer, QEvent, QPoint


class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Style Player")
        self.resize(1100, 750)
        
      
        self.subs_data = []         
        self.subs_visible = False   
        
        # Настройка медиа движка
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.video_widget = QVideoWidget()
        
        # Таймер для автоскрытия интерфейса
        self.hide_timer = QTimer()
        self.hide_timer.setInterval(4000) 
        self.hide_timer.timeout.connect(self.hide_controls)
        
        # Включение отслеживания мыши
        self.setMouseTracking(True)
        self.video_widget.setMouseTracking(True)
        QApplication.instance().installEventFilter(self)

        self.setup_ui()
        self.setup_custom_header() 
        self.menuBar().hide() 

        # Сигналы
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.playbackStateChanged.connect(self.update_buttons)

    def setup_ui(self):
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: black;")
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
      
        self.main_layout.addWidget(self.video_widget, 1)
        
     
        self.subtitle_label = QLabel(self.video_widget) 
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setWordWrap(True)
       
        self.subtitle_label.setStyleSheet("""
            color: white; 
            font-size: 24px; 
            font-weight: bold; 
            background-color: rgba(0, 0, 0, 160);
            border-radius: 4px;
            padding: 10px;
        """)
        self.subtitle_label.hide()

     
        self.controls_panel = QWidget()
      
        self.controls_panel.setStyleSheet("""
            QWidget {
                background-color: rgba(44, 44, 54, 220); 
                border-top: 1px solid rgba(255, 255, 255, 30);
            }
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                border-radius: 8px;
                color: white;
                border: none;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 40); }
        """)
        
        panel_layout = QVBoxLayout(self.controls_panel)
        
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.sliderMoved.connect(self.set_position)
        panel_layout.addWidget(self.position_slider)

        bottom_row = QHBoxLayout()
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #ccc; border: none; background: transparent;")
        bottom_row.addWidget(self.time_label)
        bottom_row.addStretch()

        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_button.setFixedSize(50, 40)
        self.play_button.clicked.connect(self.play_pause)
        bottom_row.addWidget(self.play_button)
        
        bottom_row.addStretch()
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        bottom_row.addWidget(QLabel("🔊"))
        bottom_row.addWidget(self.volume_slider)

        panel_layout.addLayout(bottom_row)
        self.main_layout.addWidget(self.controls_panel)

        self.media_player.setVideoOutput(self.video_widget)

    def resizeEvent(self, event):
        """Обновляем позицию субтитров при изменении размера окна"""
        super().resizeEvent(event)
        w = self.video_widget.width()
        h = self.video_widget.height()
        
      
        sub_w = int(w * 0.8)
        self.subtitle_label.setFixedWidth(sub_w)
        self.subtitle_label.adjustSize()
        
        new_x = (w - self.subtitle_label.width()) // 2
        new_y = h - self.subtitle_label.height() - 30 
        self.subtitle_label.move(new_x, new_y)

    def setup_custom_header(self):
        self.header_panel = QWidget()
        self.header_panel.setStyleSheet("background-color: rgba(34, 34, 44, 220); color: white;")
        layout = QHBoxLayout(self.header_panel)
        
        self.btn_sub = QPushButton("Субтитры: Выкл")
        self.btn_sub.clicked.connect(self.toggle_subtitles)
        self.btn_open = QPushButton("Открыть")
        self.btn_open.clicked.connect(self.open_file)
        
        layout.addWidget(QLabel("PRO Player"))
        layout.addStretch()
        layout.addWidget(self.btn_sub)
        layout.addWidget(self.btn_open)
        
        self.main_layout.insertWidget(0, self.header_panel)

    def toggle_subtitles(self):
        self.subs_visible = not self.subs_visible
        self.btn_sub.setText(f"Субтитры: {'Вкл' if self.subs_visible else 'Выкл'}")
        if not self.subs_visible: self.subtitle_label.hide()

    def load_subtitles_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "SRT", "", "SRT (*.srt)")
        if file:
            self.parse_srt(file)
            self.subs_visible = True
            self.btn_sub.setText("Субтитры: Вкл")

    def parse_srt(self, path):
        self.subs_data = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip().replace('\r\n', '\n')
                blocks = content.split('\n\n')
                for block in blocks:
                    lines = block.split('\n')
                    if len(lines) >= 3:
                        time_line = next((l for l in lines if " --> " in l), None)
                        if time_line:
                            t = time_line.split(' --> ')
                            self.subs_data.append((self.to_ms(t[0]), self.to_ms(t[1]), '\n'.join(lines[lines.index(time_line)+1:])))
        except: pass

    def to_ms(self, s):
        s = s.replace(',', '.')
        h, m, sec = s.split(':')
        return int((int(h)*3600 + int(m)*60 + float(sec)) * 1000)

    def open_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Video", "", "Video (*.mp4 *.mkv *.avi)")
        if file:
            self.media_player.setSource(QUrl.fromLocalFile(file))
            self.media_player.play()

    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else: self.media_player.play()

    def set_position(self, p): self.media_player.setPosition(p)
    def set_volume(self, v): self.audio_output.setVolume(v/100)

    def update_position(self, pos):
        self.position_slider.setValue(pos)
        dur = self.media_player.duration()
        if dur > 0:
            self.time_label.setText(f"{self.fmt(pos)} / {self.fmt(dur)}")
        
        if self.subs_visible:
            txt = next((t for s, e, t in self.subs_data if s <= pos <= e), "")
            if txt:
                self.subtitle_label.setText(txt)
                self.subtitle_label.show()
                self.subtitle_label.raise_()
            else:
                self.subtitle_label.hide()

    def update_duration(self, d): self.position_slider.setRange(0, d)
    def update_buttons(self, s):
        icon = QStyle.StandardPixmap.SP_MediaPause if s == QMediaPlayer.PlaybackState.PlayingState else QStyle.StandardPixmap.SP_MediaPlay
        self.play_button.setIcon(self.style().standardIcon(icon))

    def fmt(self, ms):
        s = ms // 1000
        return f"{s//60:02d}:{s%60:02d}"

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseMove: self.show_controls()
        return False

    def show_controls(self):
        self.controls_panel.show()
        self.header_panel.show()
        self.setCursor(Qt.CursorShape.ArrowCursor)
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.hide_timer.start()

    def hide_controls(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.controls_panel.hide()
            self.header_panel.hide()
            self.setCursor(Qt.CursorShape.BlankCursor)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())