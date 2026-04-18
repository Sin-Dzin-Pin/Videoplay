import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QFileDialog, QStyle, QMessageBox,
    QSizePolicy
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import Qt, QUrl, QTimer, QEvent # Добавили QTimer и QEvent
from PyQt6.QtGui import QAction


class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Видеоплеер на PyQt6")
        self.resize(800, 600)
        
        # Настройка медиаплеера
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.video_widget = QVideoWidget()
        
        # --- ТАЙМЕР И СОБЫТИЯ ---
        self.hide_timer = QTimer()
        self.hide_timer.setInterval(4000) # Исчезновение через 3 секунды
        self.hide_timer.timeout.connect(self.hide_controls)
        
        # Устанавливаем фильтр, чтобы ловить движения мыши над видео
        self.video_widget.installEventFilter(self)
        self.video_widget.setMouseTracking(True)
        self.setMouseTracking(True)

        self.setup_ui()
        self.setup_menu()
        
        # Подключение сигналов
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)
        self.media_player.playbackStateChanged.connect(self.update_buttons)
        self.media_player.errorOccurred.connect(self.handle_error)
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0) # Убрали отступы для чистого вида
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)
        
        main_layout.addWidget(self.video_widget, 1)
        
        # --- КОНТЕЙНЕР ПАНЕЛИ УПРАВЛЕНИЯ ---
        # Мы помещаем всё нижнее управление в один виджет
        self.controls_panel = QWidget()
        self.controls_panel.setObjectName("ControlsPanel")
        # Небольшая стилизация, чтобы панель была видна поверх черного фона
        self.controls_panel.setStyleSheet("background-color: rgba(60, 60, 60, 120);")
        
        panel_layout = QVBoxLayout(self.controls_panel)
        panel_layout.setContentsMargins(5, 5, 5, 5)

        # Ползунок прогресса и время
        progress_layout = QVBoxLayout()
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("color: white;")
        
        progress_layout.addWidget(self.position_slider)
        progress_layout.addWidget(self.time_label)
        panel_layout.addLayout(progress_layout)
        
        # Кнопки управления
        control_layout = QHBoxLayout()
        self.open_button = QPushButton("📂")
        self.open_button.setFixedSize(35, 35)
        self.open_button.clicked.connect(self.open_file)

        self.back_button = QPushButton()
        self.back_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipBackward))
        self.back_button.setFixedSize(35, 35)
        self.back_button.clicked.connect(self.rewind)

        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_button.setFixedSize(40, 40)
        self.play_button.clicked.connect(self.play_pause)

        self.fwd_button = QPushButton()
        self.fwd_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaSkipForward))
        self.fwd_button.setFixedSize(35, 35)
        self.fwd_button.clicked.connect(self.forward)
        
        self.stop_button = QPushButton()
        self.stop_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.stop_button.setFixedSize(35, 35)
        self.stop_button.clicked.connect(self.stop)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        control_layout.addWidget(self.open_button)
        control_layout.addStretch()
        control_layout.addWidget(self.back_button)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.fwd_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addStretch()
        lbl_vol = QLabel("🔊")
        lbl_vol.setStyleSheet("color: white;")
        control_layout.addWidget(lbl_vol)
        control_layout.addWidget(self.volume_slider)
        
        panel_layout.addLayout(control_layout)
        
        # Добавляем панель в основной макет
        main_layout.addWidget(self.controls_panel)
        
        self.media_player.setVideoOutput(self.video_widget)

    # --- ЛОГИКА СКРЫТИЯ ---
    def eventFilter(self, obj, event):
        # Если мышь двигается над видео-виджетом — показываем панель
        if obj == self.video_widget and event.type() == QEvent.Type.MouseMove:
            self.show_controls()
        return super().eventFilter(obj, event)

    def mouseMoveEvent(self, event):
        self.show_controls()
        super().mouseMoveEvent(event)

    def show_controls(self):
        self.controls_panel.show()
        self.setCursor(Qt.CursorShape.ArrowCursor) # Показываем курсор
        # Запускаем/сбрасываем таймер только если видео проигрывается
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.hide_timer.start()
        else:
            self.hide_timer.stop()

    def hide_controls(self):
        # Скрываем только если видео идет и мы не в меню
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.controls_panel.hide()
            self.setCursor(Qt.CursorShape.BlankCursor) # Скрываем курсор

    # --- ВАШИ ОРИГИНАЛЬНЫЕ ФУНКЦИИ ---
    def setup_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        open_action = QAction("Открыть", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def rewind(self):
        new_pos = max(0, self.media_player.position() - 5000)
        self.media_player.setPosition(new_pos)
        self.show_controls()

    def forward(self):
        new_pos = min(self.media_player.duration(), self.media_player.position() + 5000)
        self.media_player.setPosition(new_pos)
        self.show_controls()

    def open_file(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Видео (*.mp4 *.avi *.mkv *.mov)")
        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            if files:
                url = QUrl.fromLocalFile(files[0])
                self.media_player.setSource(url)
                self.setWindowTitle(f"Плеер - {Path(files[0]).name}")
                self.media_player.play()
                self.show_controls()
    
    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.show_controls() # Панель должна остаться, если пауза
        else:
            self.media_player.play()
            self.hide_timer.start()
            
    def stop(self):
        self.media_player.stop()
        self.show_controls()

    def set_position(self, position):
        self.media_player.setPosition(position)

    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100)

    def update_position(self, position):
        self.position_slider.setValue(position)
        duration = self.media_player.duration()
        if duration > 0:
            self.time_label.setText(f"{self.format_time(position)} / {self.format_time(duration)}")

    def update_duration(self, duration):
        self.position_slider.setRange(0, duration)

    def update_buttons(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            self.hide_timer.start()
        else:
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
            self.show_controls()

    def format_time(self, ms):
        s = ms // 1000
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"

    def handle_error(self):
        err = self.media_player.errorString()
        if err:
            QMessageBox.critical(self, "Ошибка", f"Проблема с видео: {err}")

    def keyPressEvent(self, event):
        self.show_controls()
        if event.key() == Qt.Key.Key_Space:
            self.play_pause()
        elif event.key() == Qt.Key.Key_Right:
            self.forward()
        elif event.key() == Qt.Key.Key_Left:
            self.rewind()
        elif event.key() == Qt.Key.Key_S:
            self.stop()
        elif event.key() == Qt.Key.Key_F11:
            if self.isFullScreen(): self.showNormal()
            else: self.showFullScreen()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec())