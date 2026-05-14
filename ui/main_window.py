"""
Main Window - Ana arayüz
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QSpinBox, QDoubleSpinBox,
    QFileDialog, QProgressBar, QStackedWidget, QTableWidget,
    QTableWidgetItem, QGroupBox, QComboBox, QCheckBox, QFrame,
    QSpacerItem, QSizePolicy, QSplitter, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QAction, QKeySequence

from utils.logger import setup_logger
from utils.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, APP_NAME, APP_VERSION, TEMP_DIR, resource_path
)
from utils.project_manager import ProjectManager
from utils.updater import check_for_updates, download_file_from_google_drive, apply_update_and_restart
from video_processor import (
    VideoHandler, VideoTrimmer, AudioExtractor,
    NoiseReducer, AudioMixer, VideoExporter
)
from .widgets import MediaPoolWidget, AdvancedVideoTrimmer, AudioTimelineWidget

logger = setup_logger(__name__)

# Premium Dark Theme QSS
PREMIUM_DARK_THEME = """
/* Ana Pencere */
QMainWindow {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}

QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}

/* Sidebar */
#sidebar {
    background-color: #181818;
    border-right: 1px solid #262626;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #a0a0a0;
    text-align: left;
    padding: 14px 20px;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    margin: 4px 12px;
}

#sidebar QPushButton:hover {
    background-color: #242424;
    color: #ffffff;
}

#sidebar QPushButton:checked {
    background-color: #292929;
    color: #00a8ff; /* Accent color */
    font-weight: bold;
    border-left: 4px solid #00a8ff;
    border-top-left-radius: 4px;
    border-bottom-left-radius: 4px;
}

/* Content Area */
#content_area {
    background-color: #121212;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    margin-top: 25px;
    padding-top: 15px;
    font-weight: bold;
    color: #ffffff;
    background-color: #1a1a1a;
    font-size: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 15px;
    color: #00a8ff;
    background-color: #1a1a1a;
    border-radius: 4px;
}

/* Splitter */
QSplitter::handle {
    background-color: #1e1e1e;
}
QSplitter::handle:horizontal {
    width: 2px;
}
QSplitter::handle:vertical {
    height: 2px;
}
QSplitter::handle:hover {
    background-color: #00a8ff;
}
QSplitter::handle:horizontal:hover {
    cursor: split-h;
}
QSplitter::handle:vertical:hover {
    cursor: split-v;
}

/* Buttons */
QPushButton {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 10px 18px;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #383838;
    border: 1px solid #4d4d4d;
}

QPushButton:pressed {
    background-color: #252525;
}

/* Primary Action Button */
QPushButton#primary_action {
    background-color: #0078d7;
    color: white;
    border: none;
    font-weight: bold;
    font-size: 14px;
}

QPushButton#primary_action:hover {
    background-color: #1084ea;
}

QPushButton#primary_action:pressed {
    background-color: #0060ad;
}

/* SpinBox */
QDoubleSpinBox, QSpinBox {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 6px;
    font-size: 13px;
}

QDoubleSpinBox:focus, QSpinBox:focus {
    border: 1px solid #00a8ff;
}

/* Labels */
QLabel {
    color: #cccccc;
}

/* CheckBox */
QCheckBox {
    color: #cccccc;
    spacing: 8px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 1px solid #444;
    background-color: #1e1e1e;
}
QCheckBox::indicator:hover {
    border: 1px solid #00a8ff;
}
QCheckBox::indicator:checked {
    background-color: #00a8ff;
    border: 1px solid #00a8ff;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    text-align: center;
    background-color: #1a1a1a;
    color: white;
    height: 18px;
}
QProgressBar::chunk {
    background-color: #00a8ff;
    border-radius: 3px;
}
"""

class ProcessingThread(QThread):
    """Arka planda işlem yapan thread"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)
    
    def __init__(self, task_func, *args):
        super().__init__()
        self.task_func = task_func
        self.args = args
    
    def run(self):
        try:
            self.task_func(*self.args)
            self.finished.emit(True)
        except Exception as e:
            logger.error(f"İşlem hatası: {e}")
            self.finished.emit(False)

class DenoiseWorker(QThread):
    finished = pyqtSignal(object)
    
    def __init__(self, audio_path, output_path, strength):
        super().__init__()
        self.audio_path = audio_path
        self.output_path = output_path
        self.strength = strength
        
    def run(self):
        from video_processor.noise_reducer import NoiseReducer
        reducer = NoiseReducer()
        result = reducer.reduce_noise(
            self.audio_path,
            self.output_path,
            reduction_strength=self.strength,
            get_metrics=True
        )
        self.finished.emit(result)

class WhisperWorker(QThread):
    """
    faster-whisper transkripsiyon worker.

    Bu exe'yi `--whisper-worker` bayrağıyla subprocess olarak başlatır.
    Çocuk process PyQt / UI yüklemez; yalnızca Whisper çalışır.
    ctranslate2 native crash yaparsa sadece o process ölür, ana uygulama
    hayatta kalır ve stderr'den alınan hata popup olarak gösterilir.
    """
    status_changed = pyqtSignal(str)
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str, str)  # success, output_path, error_msg

    def __init__(self, audio_path: str, output_srt: str, model_size: str = "base", language: str = None):
        super().__init__()
        self.audio_path = audio_path
        self.output_srt = output_srt
        self.model_size = model_size
        self.language = language
        self._proc = None

    def run(self):
        import subprocess
        import json

        cmd = [
            sys.executable,
            "--whisper-worker",
            self.audio_path,
            self.output_srt,
            self.model_size,
            str(self.language) if self.language else "None",
        ]

        try:
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except Exception as e:
            import traceback
            self.finished.emit(False, "", f"Subprocess başlatılamadı:\n{traceback.format_exc()}")
            return

        error_msg = ""
        success = False

        # stdout'tan gerçek zamanlı JSON ilerleme mesajları oku
        for raw_line in self._proc.stdout:
            line = raw_line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                msg_type = msg.get("type", "")
                value = msg.get("value")

                if msg_type == "progress":
                    self.progress.emit(int(value))
                elif msg_type == "status":
                    self.status_changed.emit(str(value))
                elif msg_type == "error":
                    error_msg = str(value)
                    logger.error(f"Whisper worker hatası:\n{error_msg}")
                    self.status_changed.emit(f"❌ Hata: {str(value)[:120]}")
                elif msg_type == "done":
                    success = bool(value)
            except json.JSONDecodeError:
                # JSON dışı satır (ctranslate2 uyarısı vb.) — yoksay
                logger.debug(f"Whisper worker stdout (non-JSON): {line[:200]}")

        stderr_output = self._proc.stderr.read()
        self._proc.wait()
        rc = self._proc.returncode
        self._proc = None

        if success:
            self.finished.emit(True, self.output_srt, "")
            return

        # Başarısız — anlamlı hata mesajı oluştur
        if not error_msg:
            if rc != 0:
                error_msg = (
                    f"Whisper process beklenmedik şekilde kapandı "
                    f"(exit code: {rc}).\n\n"
                )
                if stderr_output.strip():
                    error_msg += f"Detay:\n{stderr_output[:800]}"
                else:
                    error_msg += (
                        "Olası nedenler:\n"
                        "  • ctranslate2.dll yüklenemiyor\n"
                        "  • Yetersiz RAM\n"
                        "  • Antivirus engeli\n"
                    )
            else:
                error_msg = "Transkripsiyon başarısız oldu."

        self.finished.emit(False, "", error_msg)

    def stop(self):
        if self._proc is not None:
            try:
                self._proc.terminate()
            except Exception:
                pass

class ExportWorker(QThread):
    """Video export ve altyazı gömme işlemleri thread'i"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

class UpdateCheckWorker(QThread):
    finished = pyqtSignal(bool, str, str)  # has_update, latest_version, zip_drive_id
    
    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version
        
    def run(self):
        try:
            has_update, latest, zip_id = check_for_updates(self.current_version)
            self.finished.emit(has_update, latest, zip_id)
        except Exception:
            self.finished.emit(False, "", "")
            
class UpdateDownloadWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, drive_id, destination):
        super().__init__()
        self.drive_id = drive_id
        self.destination = destination
        
    def run(self):
        try:
            success = download_file_from_google_drive(self.drive_id, self.destination, self.progress.emit)
            self.finished.emit(success, self.destination)
        except Exception as e:
            self.finished.emit(False, str(e))

    
    def __init__(self, input_video: str, output_video: str, quality: str, subtitle_file: str = None, subtitle_opts: dict = None):
        super().__init__()
        self.input_video = input_video
        self.output_video = output_video
        self.quality = quality
        self.subtitle_file = subtitle_file
        self.subtitle_opts = subtitle_opts or {}

    def run(self):
        try:
            self.progress.emit(30)
            
            if self.subtitle_file:
                # Altyazı gömülecekse ffmpeg (imageio_ffmpeg) kullanarak hardcode ederiz.
                import os
                # Ffmpeg'in Windows'ta ':' (colon) karakterinden dolayı hata vermesini önlemek için 
                # yolu relative path'e çevirip ters slash'ları düz slash yapıyoruz.
                try:
                    sub_path = os.path.relpath(self.subtitle_file).replace('\\', '/')
                except ValueError:
                    # Farklı disk sürücüsü durumu için fallback
                    sub_path = Path(self.subtitle_file).resolve().as_posix()
                    sub_path = sub_path.replace(":", "\\\\:")
                
                import subprocess
                import imageio_ffmpeg
                # quality string'ine göre bitrate/fps seçilebilir, şimdilik sabit
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                
                # Stil ayarlarını hazırla
                fontsize = self.subtitle_opts.get("fontsize", 24)
                margin_v = self.subtitle_opts.get("margin_v", 30)
                force_style = f"FontSize={fontsize},MarginV={margin_v},FontName=Arial,PrimaryColour=&H00FFFFFF"
                
                cmd = [
                    ffmpeg_exe, "-y", 
                    "-i", self.input_video,
                    "-vf", f"subtitles={sub_path}:force_style='{force_style}'",
                    "-c:v", "libx264",
                    "-preset", "fast",
                    "-c:a", "aac",
                    self.output_video
                ]
                logger.info(f"Video (altyazılı) export ediliyor: {' '.join(cmd)}")
                self.progress.emit(50)
                
                # subprocess ile çalıştır
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    self.progress.emit(100)
                    self.finished.emit(True, self.output_video)
                else:
                    logger.error(f"FFmpeg Hatası:\n{stderr}")
                    self.finished.emit(False, str(stderr[-500:])) # Sadece son hataları göster
            else:
                # Altyazı gömme yoksa normal VideoExporter'ı kullanıyoruz
                from video_processor.exporter import VideoExporter
                self.progress.emit(50)
                success = VideoExporter.export(self.input_video, self.output_video, self.quality)
                if success:
                    self.progress.emit(100)
                    self.finished.emit(True, self.output_video)
                else:
                    self.finished.emit(False, "VideoExporter işleminde Hata Oluştu!")
                    
        except Exception as e:
            logger.error(f"ExportWorker Hatası: {e}")
            self.finished.emit(False, str(e))

class MainWindow(QMainWindow):
    """Ana pencere"""
    
    def __init__(self):
        super().__init__()
        self.current_video_path = None
        self.current_audio_path = None
        
        self.init_ui()
        
        # Initialize Project Manager and Auto-save
        self.project_manager = ProjectManager(self)
        self._init_menu_bar()
        self._init_auto_save()
        
        # Check for updates automatically roughly 2 seconds after startup
        QTimer.singleShot(2000, self.check_for_updates_auto)
        
    def _init_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #121212; 
                color: #e0e0e0; 
                border-bottom: 1px solid #2a2a2a;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 10px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #252525;
                color: #00a8ff;
            }
            QMenuBar::item:pressed {
                background-color: #333333;
            }
            QMenu {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                padding: 4px 0px;
            }
            QMenu::item {
                padding: 6px 24px 6px 24px;
            }
            QMenu::item:selected {
                background-color: #00a8ff;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background-color: #2a2a2a;
                margin: 4px 0px;
            }
        """)
        
        # File Menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Project", self)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open Project", self)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save As...", self)
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Import Menu
        import_menu = menubar.addMenu("Import")
        import_media_action = QAction("Add Media to Pool", self)
        import_media_action.triggered.connect(self.import_media)
        import_menu.addAction(import_media_action)
        
        # Help Menu
        help_menu = menubar.addMenu("Help")
        update_action = QAction("Check for Updates", self)
        update_action.triggered.connect(self.check_for_updates_manual)
        help_menu.addAction(update_action)
        
    def _init_auto_save(self):
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self._perform_auto_save)
        self.auto_save_timer.start(300000) # 5 minutes
        
        # We can also connect timeline changes to auto_save if needed later
        
    def _perform_auto_save(self):
        self.project_manager.auto_save(str(TEMP_DIR))
        logger.info("Auto-save completed.")
        
    def _on_timeline_changed(self, mix_data):
        """Called when timeline changes. Save to current project if set, otherwise autosave."""
        try:
            if hasattr(self, 'project_manager') and self.project_manager and self.project_manager.current_project_path:
                # Save silently to the existing project file
                self.project_manager.save_project(self.project_manager.current_project_path)
                logger.info("Timeline change saved to current project.")
                try:
                    self.statusBar().showMessage("Project saved.", 1500)
                except Exception:
                    pass
            else:
                self._perform_auto_save()
        except Exception as e:
            logger.error(f"Error saving project on timeline change: {e}")
        
    def new_project(self):
        reply = QMessageBox.question(self, 'New Project', 'Are you sure you want to clear current workspace?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.project_manager._clear_workspace()
            self.project_manager.current_project_path = None
            
    def open_project(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open DenoShark Project", self.project_manager.last_used_directory, "DenoShark Projects (*.deno)")
        if file_path:
            if self.project_manager.load_project(file_path):
                QMessageBox.information(self, "Success", "Project loaded successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to load project.")
                
    def save_project(self):
        if self.project_manager.current_project_path:
            if self.project_manager.save_project(self.project_manager.current_project_path):
                self.statusBar().showMessage("Project saved successfully.", 3000)
        else:
            self.save_project_as()
            
    def save_project_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save DenoShark Project As", self.project_manager.last_used_directory, "DenoShark Projects (*.deno)")
        if file_path:
            if not file_path.endswith(".deno"):
                file_path += ".deno"
            if self.project_manager.save_project(file_path):
                QMessageBox.information(self, "Success", "Project saved successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to save project.")
                
    def import_media(self):
        # Already handled by media pool, but we can trigger it directly
        self.media_pool.browse_files()
        
    def check_for_updates_manual(self):
        self.statusBar().showMessage("Checking for updates...")
        self.update_checker = UpdateCheckWorker(APP_VERSION)
        self.update_checker.finished.connect(self._on_update_checked_manual)
        self.update_checker.start()
        
    def _on_update_checked_manual(self, has_update, latest_version, zip_drive_id):
        if has_update:
            reply = QMessageBox.question(
                self, "Update Available",
                f"A new version (v{latest_version}) is available!\nDo you want to download and install it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.start_downloading_update(zip_drive_id, latest_version)
        else:
            QMessageBox.information(self, "Up to Date", "You are using the latest version of DenoShark.")
            self.statusBar().showMessage("Up to date.", 3000)
            
    def check_for_updates_auto(self):
        self.auto_update_checker = UpdateCheckWorker(APP_VERSION)
        self.auto_update_checker.finished.connect(self._on_update_checked_auto)
        self.auto_update_checker.start()
        
    def _on_update_checked_auto(self, has_update, latest_version, zip_drive_id):
        if has_update:
            reply = QMessageBox.question(
                self, "Update Available",
                f"A new version (v{latest_version}) is available!\nDo you want to download and install it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.start_downloading_update(zip_drive_id, latest_version)
                
    def start_downloading_update(self, zip_drive_id, latest_version):
        from utils.config import PROJECT_ROOT
        import os
        zip_path = os.path.join(PROJECT_ROOT, f"update_v{latest_version}.zip")
        
        self.progress_dialog = QProgressDialog("Downloading update...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowTitle("DenoShark Updater")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.show()
        
        self.update_downloader = UpdateDownloadWorker(zip_drive_id, zip_path)
        self.update_downloader.progress.connect(self.progress_dialog.setValue)
        self.update_downloader.finished.connect(lambda success, path: self._on_download_finished(success, path, zip_path))
        self.update_downloader.start()
        
        self.progress_dialog.canceled.connect(self.update_downloader.terminate)

    def _on_download_finished(self, success, path_or_err, zip_path):
        self.progress_dialog.close()
        if success:
            QMessageBox.information(self, "Ready", "Update downloaded! The application will now restart to apply the update.")
            from utils.config import PROJECT_ROOT
            apply_update_and_restart(zip_path, PROJECT_ROOT)
        else:
            QMessageBox.error(self, "Update Failed", f"Failed to download update:\n{path_or_err}")

    def init_ui(self):
        """Arayüzü oluştur"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        
        # Pencere ikonu ayarla
        icon_path = resource_path("img/logo-small.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(800, 560)
        self.setStyleSheet(PREMIUM_DARK_THEME)
        
        # Ana widget
        central_widget = QWidget()
        central_widget.setObjectName("central_widget")
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMinimumWidth(180)
        self.sidebar.setMaximumWidth(280)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 30, 0, 20)
        sidebar_layout.setSpacing(5)
        
        # App Title / Logo in Sidebar
        logo_label = QLabel()
        logo_path = resource_path("img/logo.png")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            scaled_pixmap = pixmap.scaledToHeight(125, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setStyleSheet("padding-left: 10px; margin-bottom: 30px;")
        else:
            logo_label.setText("🦈 " + APP_NAME)
            logo_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
            logo_label.setStyleSheet("color: #ffffff; padding-left: 15px; margin-bottom: 30px;")
        
        sidebar_layout.addWidget(logo_label)
        
        # Navigation Buttons
        self.nav_buttons = []
        
        self.btn_video = QPushButton("📹 Video İşleme")
        self.btn_audio = QPushButton("🔊 Ses İşleme")
        self.btn_ai = QPushButton("🤖 AI Araçları")
        self.btn_settings = QPushButton("⚙️ Ayarlar")
        self.btn_export = QPushButton("💾 İndir / Dışa Aktar")
        
        for btn in [self.btn_video, self.btn_audio, self.btn_ai, self.btn_settings, self.btn_export]:
            btn.setCheckable(True)
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            
        sidebar_layout.addStretch()
        
        # Version Label
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet("color: #666666; padding-left: 20px;")
        sidebar_layout.addWidget(version_label)
        
        # Main Splitter (3 Columns)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Add Column 1: Sidebar
        self.main_splitter.addWidget(self.sidebar)
        
        # Add Column 2: Media Pool
        self.media_pool = MediaPoolWidget()
        self.media_pool.media_selected.connect(self.on_media_selected)
        self.media_pool.setMinimumWidth(250)
        self.main_splitter.addWidget(self.media_pool)
        
        # Add Column 3: Workspace (Content Area)
        self.content_area = QWidget()
        self.content_area.setObjectName("content_area")
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        self.main_splitter.addWidget(self.content_area)
        
        # Set Proportions
        self.main_splitter.setStretchFactor(0, 0) # Sidebar fixed
        self.main_splitter.setStretchFactor(1, 1) # Media Pool stretches slightly
        self.main_splitter.setStretchFactor(2, 4) # Workspace gets max stretch
        self.main_splitter.setSizes([220, 260, 900])
        
        main_layout.addWidget(self.main_splitter)
        
        # Add Pages
        self.stacked_widget.addWidget(self._create_video_tab())
        self.stacked_widget.addWidget(self._create_audio_tab())
        self.stacked_widget.addWidget(self._create_ai_tab())
        self.stacked_widget.addWidget(self._create_settings_tab())
        self.stacked_widget.addWidget(self._create_export_tab())
        
        # Connections
        self.btn_video.clicked.connect(lambda: self.switch_page(0))
        self.btn_audio.clicked.connect(lambda: self.switch_page(1))
        self.btn_ai.clicked.connect(lambda: self.switch_page(2))
        self.btn_settings.clicked.connect(lambda: self.switch_page(3))
        self.btn_export.clicked.connect(lambda: self.switch_page(4))
        
        # Init state
        self.switch_page(0)
        
        # Status bar styling
        self.statusBar().setStyleSheet("background-color: #181818; color: #a0a0a0; padding-left: 10px; border-top: 1px solid #262626;")
        self.statusBar().showMessage("Hazır")

    def switch_page(self, index):
        """Sayfa değiştir ve sidebar buton state'ini güncelle"""
        self.stacked_widget.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setChecked(True)
            else:
                btn.setChecked(False)

    def _on_media_error(self, error, error_string: str):
        from PyQt6.QtMultimedia import QMediaPlayer
        if error == QMediaPlayer.Error.NoError:
            return
        logger.error(f"Medya oynatıcı hatası: {error_string}")
        QMessageBox.warning(
            self,
            "Medya Oynatıcı Hatası",
            f"Video/ses oynatılırken bir hata oluştu:\n\n{error_string}\n\n"
            "Olası nedenler:\n"
            "• Video formatı desteklenmiyor\n"
            "• Windows Media bileşeni eksik\n"
            "• Dosya bozuk veya erişilemiyor"
        )
    
    def _create_video_tab(self):
        """Video işleme sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        title = QLabel("Video İşleme")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Video kırpma (timeline preview ile)
        trim_group = QGroupBox("1. Video Kırpma")
        trim_layout = QVBoxLayout()
        trim_layout.setSpacing(15)
        
        # Advanced Timeline and Preview widget
        self.timeline_widget = AdvancedVideoTrimmer()
        self.timeline_widget.media_player.errorOccurred.connect(self._on_media_error)
        trim_layout.addWidget(self.timeline_widget)
        
        trim_btn = QPushButton("✂️ Video Kırp")
        trim_btn.setObjectName("primary_action")
        trim_btn.clicked.connect(self.trim_video)
        trim_layout.addWidget(trim_btn)
        
        trim_group.setLayout(trim_layout)
        layout.addWidget(trim_group)
        
        # Progress bar
        self.video_progress = QProgressBar()
        self.video_progress.hide()
        layout.addWidget(self.video_progress)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _on_player_position_changed(self, pos_ms):
        sec = pos_ms / 1000.0
        self.multi_track_timeline.update_playhead(sec)
        if hasattr(self, 'audio_engine'):
            self.audio_engine.update_position(sec)

    def _on_player_state_changed(self, state):
        from PyQt6.QtMultimedia import QMediaPlayer
        is_playing = (state == QMediaPlayer.PlaybackState.PlayingState)
        if hasattr(self, 'audio_engine') and hasattr(self, 'audio_timeline_widget'):
            sec = self.audio_timeline_widget.media_player.position() / 1000.0
            self.audio_engine.set_playing(is_playing, sec)

    def _create_audio_tab(self):
        """Ses işleme sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        title = QLabel("Ses İşleme")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Ses İşlemleri Başlangıcı
        
        # Advanced Timeline and Preview widget
        self.audio_timeline_widget = AdvancedVideoTrimmer()
        layout.addWidget(self.audio_timeline_widget)
        
        # DaVinci Style Multitrack Timeline
        self.multi_track_timeline = AudioTimelineWidget()
        layout.addWidget(self.multi_track_timeline)
        
        # Real-time audio engine
        from ui.widgets import RealTimeAudioEngine
        self.audio_engine = RealTimeAudioEngine()
        self.multi_track_timeline.timeline_changed.connect(self.audio_engine.sync_clips)
        # Ensure timeline edits persist to the open project file when available;
        # fallback to auto-save to temp if no project file yet.
        self.multi_track_timeline.timeline_changed.connect(self._on_timeline_changed)
        
        # Mute original video
        self.audio_timeline_widget.audio_output.setVolume(0.0)
        
        # Sync playhead and audio engine
        self.audio_timeline_widget.media_player.positionChanged.connect(
            lambda pos: self._on_player_position_changed(pos)
        )
        self.audio_timeline_widget.media_player.playbackStateChanged.connect(
            lambda state: self._on_player_state_changed(state)
        )
        self.audio_timeline_widget.media_player.durationChanged.connect(
            lambda dur: self.multi_track_timeline.set_duration(dur / 1000.0)
        )
        self.multi_track_timeline.seek_requested.connect(
            lambda sec: self.audio_timeline_widget.media_player.setPosition(int(sec * 1000))
        )
        
        # Horizontal Layout for Tools
        tools_layout = QHBoxLayout()
        tools_layout.setSpacing(20)
        
        # Ses çıkarma
        extract_group = QGroupBox("1. Ses İşlemleri")
        extract_layout = QVBoxLayout()
        extract_layout.setSpacing(15)
        
        # Checkbox'lar
        checkbox_layout = QVBoxLayout()
        self.extract_audio_checkbox = QCheckBox("📢 Sesi İndir (WAV/MP3)")
        self.extract_audio_checkbox.setChecked(True)
        self.extract_video_checkbox = QCheckBox("🎬 Sessiz Videoyu İndir")
        checkbox_layout.addWidget(self.extract_audio_checkbox)
        checkbox_layout.addWidget(self.extract_video_checkbox)
        extract_layout.addLayout(checkbox_layout)
        
        extract_btn = QPushButton("📥 Seçilenleri İndir")
        extract_btn.setObjectName("primary_action")
        extract_btn.clicked.connect(self.extract_audio_video)
        extract_layout.addWidget(extract_btn)
        
        extract_group.setLayout(extract_layout)
        tools_layout.addWidget(extract_group)
        
        # Gürültü azaltma
        right_tools_layout = QVBoxLayout()
        
        denoise_group = QGroupBox("2. Gürültü Azaltma")
        denoise_layout = QVBoxLayout()
        denoise_layout.setSpacing(15)
        
        strength_layout = QHBoxLayout()
        strength_layout.addWidget(QLabel("Filtre Gücü:"))
        self.denoise_strength = QDoubleSpinBox()
        self.denoise_strength.setMinimum(0)
        self.denoise_strength.setMaximum(1)
        self.denoise_strength.setValue(0.8)
        self.denoise_strength.setSingleStep(0.1)
        strength_layout.addWidget(self.denoise_strength)
        denoise_layout.addLayout(strength_layout)

        auto_strength_btn = QPushButton("🤖 Otomatik Güç Algıla")
        auto_strength_btn.clicked.connect(self.auto_set_denoise_strength)
        denoise_layout.addWidget(auto_strength_btn)

        self.denoise_metrics_label = QLabel("SNR: - dB | Kalite: -/5")
        self.denoise_metrics_label.setStyleSheet("color: #888;")
        denoise_layout.addWidget(self.denoise_metrics_label)
        
        # A/B Toggle Switch
        self.ab_toggle_layout = QHBoxLayout()
        self.btn_original = QPushButton("Orijinal")
        self.btn_denoised = QPushButton("Temizlenmiş")
        self.btn_original.setCheckable(True)
        self.btn_denoised.setCheckable(True)
        self.btn_original.setChecked(True)
        self.btn_denoised.setEnabled(False) # Disabled until processed
        
        segmented_style = """
            QPushButton {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                padding: 5px 10px;
                color: #888;
                border-radius: 4px;
                font-weight: normal;
            }
            QPushButton:checked {
                background-color: #00a8ff;
                color: white;
                border: 1px solid #00a8ff;
                font-weight: bold;
            }
        """
        self.btn_original.setStyleSheet(segmented_style)
        self.btn_denoised.setStyleSheet(segmented_style)
        
        self.btn_original.clicked.connect(lambda: self.toggle_ab_mode(False))
        self.btn_denoised.clicked.connect(lambda: self.toggle_ab_mode(True))
        
        self.ab_toggle_layout.addWidget(self.btn_original)
        self.ab_toggle_layout.addWidget(self.btn_denoised)
        denoise_layout.addLayout(self.ab_toggle_layout)
        
        self.btn_denoise = QPushButton("🔇 Gürültüyü Temizle")
        self.btn_denoise.setObjectName("primary_action")
        self.btn_denoise.clicked.connect(self.reduce_noise)
        denoise_layout.addWidget(self.btn_denoise)
        
        denoise_group.setLayout(denoise_layout)
        right_tools_layout.addWidget(denoise_group)
        
        right_tools_layout.addStretch()
        tools_layout.addLayout(right_tools_layout)
        
        layout.addLayout(tools_layout)
        
        self.audio_progress = QProgressBar()
        self.audio_progress.hide()
        layout.addWidget(self.audio_progress)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_ai_tab(self):
        """AI araçları sekmesi (faster-whisper ile transkripsiyon)"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        title = QLabel("🤖 AI Araçları - Otomatik Altyazı")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Otomatik altyazı (faster-whisper)
        subtitle_group = QGroupBox("Otomatik Altyazı Oluşturma (faster-whisper)")
        subtitle_layout = QVBoxLayout()
        subtitle_layout.setSpacing(15)
        
        subtitle_info = QLabel(
            "Ses dosyasını transkribe etip SRT formatında altyazı dosyası oluşturun.\n"
            "Model boyutu küçüldükçe işlem hızlanır (tiny: en hızlı, medium: en doğru)."
        )
        subtitle_info.setWordWrap(True)
        subtitle_info.setStyleSheet("color: #cccccc; font-size: 13px;")
        subtitle_layout.addWidget(subtitle_info)
        
        # Model seçimi
        model_layout = QHBoxLayout()
        model_label = QLabel("📦 Model Boyutu:")
        model_label.setFixedWidth(120)
        self.whisper_model_combo = QComboBox()
        self.whisper_model_combo.addItems(["tiny", "base", "small", "medium"])
        self.whisper_model_combo.setCurrentText("base")
        self.whisper_model_combo.setStyleSheet("padding: 5px;")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.whisper_model_combo)
        model_layout.addStretch()
        subtitle_layout.addLayout(model_layout)
        
        # Dil seçimi
        lang_layout = QHBoxLayout()
        lang_label = QLabel("🌐 Dil:")
        lang_label.setFixedWidth(120)
        self.whisper_lang_combo = QComboBox()
        self.whisper_lang_combo.addItems(["Otomatik", "Türkçe (tr)", "İngilizce (en)", "Arapça (ar)"])
        self.whisper_lang_combo.setStyleSheet("padding: 5px;")
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.whisper_lang_combo)
        lang_layout.addStretch()
        subtitle_layout.addLayout(lang_layout)
        
        # Console çıktısı
        console_label = QLabel("📋 İşlem Günlüğü:")
        console_label.setStyleSheet("color: #00a8ff; font-weight: bold;")
        subtitle_layout.addWidget(console_label)
        
        self.whisper_console = QTextEdit()
        self.whisper_console.setReadOnly(True)
        self.whisper_console.setMaximumHeight(150)
        self.whisper_console.setStyleSheet("""
            QTextEdit {
                background-color: #0d0d0d;
                color: #00ff00;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
            }
        """)
        self.whisper_console.setText("➤ Hazır. Ses dosyası seçip 'Altyazı Oluştur' butonuna basın.\n")
        subtitle_layout.addWidget(self.whisper_console)
        
        # İlerleme çubuğu
        self.whisper_progress = QProgressBar()
        self.whisper_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                background-color: #1a1a1a;
                color: #00a8ff;
            }
            QProgressBar::chunk {
                background-color: #00a8ff;
                border-radius: 3px;
            }
        """)
        self.whisper_progress.setValue(0)
        self.whisper_progress.setVisible(False)
        subtitle_layout.addWidget(self.whisper_progress)
        
        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_generate_subtitles = QPushButton("📝 Altyazı Oluştur")
        self.btn_generate_subtitles.setObjectName("primary_action")
        self.btn_generate_subtitles.setMinimumHeight(40)
        self.btn_generate_subtitles.clicked.connect(self.start_subtitle_generation)
        button_layout.addWidget(self.btn_generate_subtitles)
        
        button_layout.addStretch()
        subtitle_layout.addLayout(button_layout)
        
        subtitle_group.setLayout(subtitle_layout)
        layout.addWidget(subtitle_group)
        
        # Gelecek: XTTS ve Voicecraft (placeholder)
        future_group = QGroupBox("🚀 Yakında Gelecek Özellikler")
        future_layout = QVBoxLayout()
        future_layout.setSpacing(10)
        
        tts_info = QLabel("🎤 Metin-Ses (XTTS v2): Metninizi doğal sesle okutun (Geliştirilmekte)")
        tts_info.setWordWrap(True)
        tts_info.setStyleSheet("color: #cccccc;")
        future_layout.addWidget(tts_info)
        
        vc_info = QLabel("🎧 Ses Klonlama (Voicecraft): Sesinizi klonlayın (Geliştirilmekte)")
        vc_info.setWordWrap(True)
        vc_info.setStyleSheet("color: #cccccc;")
        future_layout.addWidget(vc_info)
        
        future_group.setLayout(future_layout)
        layout.addWidget(future_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _get_audio_for_transcription(self) -> tuple:
        """
        Altyazı oluşturmak için gerekli ses dosyasını otomatik olarak bul.
        Öncelik: Mevcut ses > Medya Pool seçimi > Zaman çizelgesi > Video'dan ses çıkarma
        
        Returns: (audio_path: str, source_name: str) or (None, error_msg) if failed
        """
        try:
            # 1. Mevcut ses dosyası var mı?
            if self.current_audio_path and Path(self.current_audio_path).exists():
                source_name = Path(self.current_audio_path).name
                logger.info(f"Ses bulundu (current): {source_name}")
                return self.current_audio_path, source_name
            
            # 2. Medya Pool'da seçili ses dosyası var mı?
            if hasattr(self, 'media_pool') and self.media_pool:
                selected_file = self.media_pool.get_selected_file()
                if selected_file and Path(selected_file).exists():
                    ext = Path(selected_file).suffix.lower()
                    audio_extensions = {'.mp3', '.wav', '.aac', '.ogg', '.m4a', '.flac', '.wma'}
                    if ext in audio_extensions:
                        source_name = Path(selected_file).name
                        logger.info(f"Ses bulundu (Media Pool): {source_name}")
                        return selected_file, source_name
            
            # 3. Zaman çizelgesinde ana video var mı?
            if hasattr(self, 'multi_track_timeline') and self.multi_track_timeline:
                if self.multi_track_timeline.main_video_path:
                    video_path = self.multi_track_timeline.main_video_path
                    if Path(video_path).exists():
                        logger.info(f"Video bulundu (Timeline): {Path(video_path).name}, ses çıkarılıyor...")
                        return self._auto_extract_audio(video_path), Path(video_path).name
            
            # 4. Mevcut video var mı? Ses çıkar
            if self.current_video_path and Path(self.current_video_path).exists():
                logger.info(f"Video bulundu (current): {Path(self.current_video_path).name}, ses çıkarılıyor...")
                return self._auto_extract_audio(self.current_video_path), Path(self.current_video_path).name
            
            # 5. Ses sekmesindeki video var mı?
            if hasattr(self, 'audio_video_path') and self.audio_video_path and Path(self.audio_video_path).exists():
                logger.info(f"Video bulundu (Audio Tab): {Path(self.audio_video_path).name}, ses çıkarılıyor...")
                return self._auto_extract_audio(self.audio_video_path), Path(self.audio_video_path).name
            
            # Hiçbir kaynak bulunamadı
            return None, "❌ Ses veya video dosyası bulunamadı. Lütfen önce bir medya yükleyin."
            
        except Exception as e:
            logger.error(f"Ses algılama hatası: {e}")
            return None, f"❌ Hata: {str(e)[:80]}"
    
    def _auto_extract_audio(self, video_path: str) -> str:
        """Video'dan geçici ses dosyası çıkar"""
        try:
            TEMP_DIR.mkdir(exist_ok=True)
            video_name = Path(video_path).stem
            temp_audio = str(TEMP_DIR / f"whisper_temp_{video_name}.wav")
            
            # Video'nun sadece ilk 30 saniyesini kullan (preview), full transkripsiyon için tüm videoyu kullan
            extractor = AudioExtractor()
            self.statusBar().showMessage("🎤 Ses dosyası otomatik olarak çıkarılıyor...")
            
            success = extractor.extract(video_path, temp_audio, start_time=0, end_time=None)
            
            if success and Path(temp_audio).exists():
                logger.info(f"Ses başarıyla çıkarıldı: {temp_audio}")
                return temp_audio
            else:
                raise Exception("Ses çıkarma başarısız")
                
        except Exception as e:
            logger.error(f"Ses çıkarma hatası: {e}")
            raise
    
    def start_subtitle_generation(self):
        """Whisper worker'ı başlat (akıllı ses algılama ile)"""
        # Ses dosyasını otomatik olarak bul
        audio_path, source_info = self._get_audio_for_transcription()
        
        if not audio_path:
            QMessageBox.warning(
                self, 
                "Ses Bulunamadı", 
                source_info  # source_info hata mesajı içeriyor
            )
            return
        
        audio_file = Path(audio_path)
        default_output = str(Path("output") / f"{audio_file.stem}.srt")
        
        output_srt, _ = QFileDialog.getSaveFileName(
            self,
            "Altyazıyı Kaydet",
            default_output,
            "SRT Dosyası (*.srt)"
        )
        
        if not output_srt:
            return
        
        # Dil parametresini ayarla
        lang_text = self.whisper_lang_combo.currentText()
        language = None
        if "Türkçe" in lang_text:
            language = "tr"
        elif "İngilizce" in lang_text:
            language = "en"
        elif "Arapça" in lang_text:
            language = "ar"
        
        model_size = self.whisper_model_combo.currentText()
        
        # UI'yi devre dışı bırak
        self.btn_generate_subtitles.setEnabled(False)
        self.whisper_model_combo.setEnabled(False)
        self.whisper_lang_combo.setEnabled(False)
        self.whisper_progress.setVisible(True)
        self.whisper_progress.setValue(0)
        
        # Console'u temizle ve başlangıç mesajı
        self.whisper_console.clear()
        self.whisper_console.append(f"📌 Kaynak: {source_info}")
        self.whisper_console.append(f"📁 Ses: {audio_file.name}")
        self.whisper_console.append(f"Model: {model_size} | Dil: {lang_text}\n")
        self.whisper_console.append("▶ İşlem başlatılıyor...\n")
        
        # Worker başlat
        self.whisper_worker = WhisperWorker(
            audio_path,
            output_srt,
            model_size=model_size,
            language=language
        )
        self.whisper_worker.status_changed.connect(self._on_whisper_status)
        self.whisper_worker.progress.connect(self._on_whisper_progress)
        self.whisper_worker.finished.connect(self._on_whisper_finished)
        self.whisper_worker.start()
    
    def _on_whisper_status(self, message: str):
        """Whisper worker'dan durum mesajı al"""
        self.whisper_console.append(message)
        # Scroll down
        self.whisper_console.verticalScrollBar().setValue(
            self.whisper_console.verticalScrollBar().maximum()
        )
    
    def _on_whisper_progress(self, value: int):
        """İlerleme güncellemesi"""
        self.whisper_progress.setValue(value)
    
    def _on_whisper_finished(self, success: bool, output_path: str, error_msg: str):
        """Whisper worker tamamlandı"""
        self.btn_generate_subtitles.setEnabled(True)
        self.whisper_model_combo.setEnabled(True)
        self.whisper_lang_combo.setEnabled(True)
        self.whisper_progress.setVisible(False)

        if success:
            self.statusBar().showMessage(f"✅ Altyazılar başarıyla oluşturuldu: {Path(output_path).name}", 5000)
            self.whisper_console.append(f"\n✅ Altyazılar başarıyla kaydedildi!")
            QMessageBox.information(
                self,
                "Başarılı",
                f"Altyazılar başarıyla oluşturuldu!\n\n📁 {output_path}"
            )
        else:
            self.statusBar().showMessage("❌ Altyazı oluşturma başarısız oldu.", 5000)
            self.whisper_console.append(f"\n❌ Altyazı oluşturma başarısız!")
            err_box = QMessageBox(self)
            err_box.setIcon(QMessageBox.Icon.Critical)
            err_box.setWindowTitle("Whisper Hatası")
            err_box.setText("Altyazı oluşturma işlemi başarısız oldu.")
            if error_msg:
                err_box.setInformativeText("Detaylar için 'Show Details' butonuna tıklayın.")
                err_box.setDetailedText(error_msg)
            err_box.exec()
    
    def _create_settings_tab(self):
        """Ayarlar sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        title = QLabel("Hakkında & Ayarlar")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        info_group = QGroupBox("Uygulama Bilgileri")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(15)
        
        info_label = QLabel(
            f"<h2 style='color:#00a8ff; margin:0;'>{APP_NAME}</h2>"
            f"<p style='color:#888; margin:0;'>Versiyon {APP_VERSION}</p><br>"
            "<p>Nişanlın için yapılmış profesyonel video düzenleme aracı. Modern, hızlı ve kullanışlı.</p>"
            "<ul>"
            "<li>Gelişmiş video kırpma</li>"
            "<li>Hızlı ses çıkarma ve karıştırma</li>"
            "<li>AI destekli gürültü azaltma</li>"
            "<li>Whisper ile otomatik altyazı üretimi</li>"
            "</ul>"
            "<br><p><i>Geliştirilmekte: XTTS v2 ve Voicecraft entegrasyonu</i></p>"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 14px; line-height: 1.5;")
        info_layout.addWidget(info_label)
        info_group.setLayout(info_layout)
        
        layout.addWidget(info_group)
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def _create_export_tab(self):
        """Videoyu İndir / Dışa Aktar sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        title = QLabel("💾 Videoyu Dışa Aktar")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        export_group = QGroupBox("Dışa Aktarma Gelişmiş Ayarları")
        export_layout = QVBoxLayout()
        export_layout.setSpacing(15)
        
        # Format
        format_layout = QHBoxLayout()
        format_label = QLabel("📥 Çıktı Formatı:")
        format_label.setFixedWidth(120)
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems([".mp4", ".mov", ".avi", ".mkv"])
        self.export_format_combo.setStyleSheet("padding: 5px;")
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.export_format_combo)
        export_layout.addLayout(format_layout)
        
        # Çözünürlük
        res_layout = QHBoxLayout()
        res_label = QLabel("🖥️ Çözünürlük:")
        res_label.setFixedWidth(120)
        self.export_res_combo = QComboBox()
        self.export_res_combo.setEditable(True)
        self.export_res_combo.addItems(["Orijinal", "1920x1080 (Yatay FHD)", "1080x1920 (Dikey FHD/Tiktok)", "1280x720 (Yatay HD)", "720x1280 (Dikey HD/Tiktok)", "3840x2160 (4K UHD)"])
        self.export_res_combo.lineEdit().setPlaceholderText("Veya özel değer yazın (örn: 1080x1920)")
        self.export_res_combo.setStyleSheet("""
            QComboBox { padding: 5px; }
            QComboBox QLineEdit { color: #e0e0e0; background-color: transparent; }
        """)
        res_layout.addWidget(res_label)
        res_layout.addWidget(self.export_res_combo)
        export_layout.addLayout(res_layout)
        
        # Kalite / Bitrate
        quality_layout = QHBoxLayout()
        quality_label = QLabel("✨ Çıktı Kalitesi:")
        quality_label.setFixedWidth(120)
        self.export_quality_combo = QComboBox()
        self.export_quality_combo.addItems(["Yüksek Kalite (Yavaş)", "Orta (Dengeli)", "Düşük (Hızlı Çıktı)"])
        self.export_quality_combo.setStyleSheet("padding: 5px;")
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.export_quality_combo)
        export_layout.addLayout(quality_layout)
        
        # Altyazı Ekleme
        subtitle_layout = QHBoxLayout()
        self.export_add_subtitle_cmd = QCheckBox("Videoya Altyazı Göm (SRT Dosyası Seç)")
        self.export_add_subtitle_cmd.setStyleSheet("padding: 5px;")
        
        self.export_subtitle_path = QLabel("Seçilen Dosya: Yok")
        self.export_subtitle_path.setStyleSheet("color: #aaaaaa; font-style: italic;")
        
        btn_select_srt = QPushButton("SRT Seç")
        btn_select_srt.clicked.connect(self.select_subtitle_for_export)
        btn_select_srt.setFixedWidth(100)
        
        subtitle_layout.addWidget(self.export_add_subtitle_cmd)
        subtitle_layout.addWidget(btn_select_srt)
        subtitle_layout.addWidget(self.export_subtitle_path)
        subtitle_layout.addStretch()
        
        export_layout.addLayout(subtitle_layout)
        
        # Altyazı stil ayarları (Boyut ve Yükseklik)
        self.subtitle_style_layout = QHBoxLayout()
        
        lbl_fontsize = QLabel("Altyazı Büyüklüğü:")
        self.spin_fontsize = QSpinBox()
        self.spin_fontsize.setRange(10, 150)
        self.spin_fontsize.setValue(24)
        
        lbl_margin_v = QLabel("Yükseklik (Aşağıdan Yukarı):")
        self.spin_margin_v = QSpinBox()
        self.spin_margin_v.setRange(0, 500)
        self.spin_margin_v.setValue(30)
        self.spin_margin_v.setToolTip("Değer arttıkça altyazı videonun yukarısına doğru çıkar.")
        
        self.subtitle_style_layout.addWidget(lbl_fontsize)
        self.subtitle_style_layout.addWidget(self.spin_fontsize)
        self.subtitle_style_layout.addSpacing(20)
        self.subtitle_style_layout.addWidget(lbl_margin_v)
        self.subtitle_style_layout.addWidget(self.spin_margin_v)
        self.subtitle_style_layout.addStretch()
        
        export_layout.addLayout(self.subtitle_style_layout)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        # İlerleme çubuğu
        self.export_progress = QProgressBar()
        self.export_progress.setValue(0)
        self.export_progress.hide()
        layout.addWidget(self.export_progress)
        
        # Buton kısmı
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self.btn_action_export = QPushButton("🚀 VİDEOYU İNDİR")
        self.btn_action_export.setObjectName("primary_action")
        self.btn_action_export.setMinimumSize(250, 50)
        self.btn_action_export.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.btn_action_export.clicked.connect(self.process_export_action)
        
        action_layout.addWidget(self.btn_action_export)
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        layout.addStretch()
        widget.setLayout(layout)
        return widget
        
    def select_subtitle_for_export(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "SRT Seç", self.project_manager.last_used_directory, "Subtitle Files (*.srt)")
        if file_path:
            self.export_subtitle_path_value = file_path
            self.export_subtitle_path.setText(f"Seçilen: {Path(file_path).name}")
            self.export_add_subtitle_cmd.setChecked(True)
    
    def process_export_action(self):
        """Kullanıcı videoyu indir butonuna tıkladığında çalışacak alan"""
        if not hasattr(self, 'current_video_path') or not self.current_video_path:
            QMessageBox.warning(self, "Hata", "Lütfen önce dışa aktarılacak bir video veya proje yükleyin!")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Videoyu İndir", self.project_manager.last_used_directory, f"Video Files (*{self.export_format_combo.currentText()})")
        
        if file_path:
            # Butonu devre dışı bırak
            self.btn_action_export.setEnabled(False)
            self.btn_action_export.setText("Yükleniyor...")
            
            # Parametreleri hazırla
            input_video = self.current_video_path
            quality_text = self.export_quality_combo.currentText()
            quality_map = {"Yüksek Kalite (Yavaş)": "fhd", "Orta (Dengeli)": "hd", "Düşük (Hızlı Çıktı)": "standard"}
            quality = quality_map.get(quality_text, "hd")
            
            subtitle_file = getattr(self, 'export_subtitle_path_value', None) if self.export_add_subtitle_cmd.isChecked() else None
            
            # Altyazı opsiyonları
            subtitle_opts = {
                "fontsize": self.spin_fontsize.value(),
                "margin_v": self.spin_margin_v.value()
            }
            
            self.statusBar().showMessage(f"Dışa aktarma başlatıldı: {file_path}")
            self.export_progress.show()
            self.export_progress.setValue(10)
            
            # Thread başlat
            self.export_thread = ExportWorker(input_video, file_path, quality, subtitle_file, subtitle_opts)
            self.export_thread.progress.connect(self.export_progress.setValue)
            self.export_thread.finished.connect(self.on_export_finished)
            self.export_thread.start()

    def on_export_finished(self, success, message):
        self.btn_action_export.setEnabled(True)
        self.btn_action_export.setText("🚀 VİDEOYU İNDİR")
        self.export_progress.setValue(100)
        
        if success:
            QMessageBox.information(self, "Başarılı", f"Video başarıyla kaydedildi:\n\n{message}")
            self.statusBar().showMessage("Video başarıyla dışa aktarıldı.", 4000)
        else:
            QMessageBox.critical(self, "Hata", f"Dışa aktarma işlemi başarısız oldu!\n\nDetay: {message}")
            self.statusBar().showMessage("Video dışa aktarılamadı.", 4000)
        
        # ProgressBar'ı biraz bekletip gizle
        QTimer.singleShot(2000, self.export_progress.hide)
    
    def on_media_selected(self, file_path: str):
        """Media Pool'dan dosya seçildiğinde aktif sekmeye yükle"""
        current_tab = self.stacked_widget.currentIndex()
        from pathlib import Path
        ext = Path(file_path).suffix.lower()
        is_audio = ext in ['.mp3', '.wav', '.aac', '.ogg', '.m4a']
        
        if current_tab == 0: # Video İşleme
            self.load_video_internal(file_path, is_audio)
        elif current_tab == 1: # Ses İşleme
            if is_audio:
                if hasattr(self, 'multi_track_timeline'):
                    self.multi_track_timeline.add_clip(file_path)
                    self.statusBar().showMessage(f"✅ Ses klibi eklendi: {Path(file_path).name}")
            else:
                self.load_video_audio_internal(file_path)
        else:
            self.statusBar().showMessage("Medya eklemek için Video veya Ses İşleme sekmesine gidin.")
    
    def load_video_internal(self, file_path: str, is_audio: bool = False):
        """Video'yu iç olarak yükle"""
        try:
            self.current_video_path = file_path
            
            if is_audio:
                from utils.media_manager import MediaManager
                mm = MediaManager()
                info = mm.add_media(file_path)
                duration = info.get('duration', 0.0) if info else 10.0
            else:
                handler = VideoHandler(file_path)
                info = handler.get_info()
                duration = info['duration_seconds']
            
            # Load video into advanced trimmer
            self.timeline_widget.load_video(file_path)
            
            if hasattr(self, 'multi_track_timeline') and not is_audio:
                self.multi_track_timeline.set_main_video(file_path, duration)
            
            # Status mesajı
            type_str = "Ses" if is_audio else "Video"
            self.statusBar().showMessage(f"✅ {type_str} yüklendi: {Path(file_path).name} ({duration:.1f}s)")
            logger.info(f"{type_str} yüklendi: {file_path}")
        
        except Exception as e:
            logger.error(f"Medya yükleme hatası: {e}")
            self.statusBar().showMessage(f"❌ Hata: {str(e)[:50]}")
    
    def load_video_audio_internal(self, file_path: str):
        """Ses işleme sekmesi için video'yu iç olarak yükle"""
        try:
            self.audio_video_path = file_path
            handler = VideoHandler(file_path)
            info = handler.get_info()
            
            duration = info['duration_seconds']
            
            # Load video into advanced trimmer
            self.audio_timeline_widget.load_video(file_path)
            
            if hasattr(self, 'multi_track_timeline'):
                self.multi_track_timeline.set_main_video(file_path, duration)
            
            # Status mesajı
            self.statusBar().showMessage(f"✅ Video yüklendi (Ses): {Path(file_path).name} ({duration:.1f}s)")
            logger.info(f"Ses sekmesi için video yüklendi: {file_path}")
        
        except Exception as e:
            logger.error(f"Video yükleme hatası (Ses): {e}")
            self.statusBar().showMessage(f"❌ Hata: {str(e)[:50]}")
    
    def trim_video(self):
        """Video kırp"""
        if not self.current_video_path:
            self.statusBar().showMessage("Lütfen önce bir video seçin")
            return
        
        # Timeline'dan değerleri al
        start_time, end_time = self.timeline_widget.get_start_end_seconds()
        
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Kırpılmış Videoyu Kaydet",
            "",
            "MP4 Dosyası (*.mp4);;MOV Dosyası (*.mov)"
        )
        
        if output_path:
            logger.info(f"Video kırpma başlatılıyor: {start_time}s - {end_time}s")
            self.statusBar().showMessage("Video kırpılıyor... (biraz zaman alabilir)")
            
            trimmer = VideoTrimmer()
            success = trimmer.trim(
                self.current_video_path,
                output_path,
                start_time,
                end_time
            )
            
            if success:
                self.statusBar().showMessage(f"✅ Video başarıyla kırpıldı: {Path(output_path).name}")
            else:
                self.statusBar().showMessage("❌ Video kırpılamadı")
    
    def extract_audio_video(self):
        """Ses ve/veya video'yu indir (checkbox'a göre)"""
        current_tab = self.stacked_widget.currentIndex()
        
        # Ses sekmesi (index 1) ise audio timeline'ını kullan
        if current_tab == 1 and self.audio_timeline_widget:
            video_path = self.audio_video_path if hasattr(self, 'audio_video_path') else None
            start_time, end_time = self.audio_timeline_widget.get_start_end_seconds()
        elif self.timeline_widget:
            video_path = self.current_video_path
            start_time, end_time = self.timeline_widget.get_start_end_seconds()
        else:
            self.statusBar().showMessage("Lütfen önce bir video seçin")
            return
        
        download_audio = self.extract_audio_checkbox.isChecked()
        download_video = self.extract_video_checkbox.isChecked()
        
        if not download_audio and not download_video:
            self.statusBar().showMessage("Lütfen indirmek istediğiniz dosya türünü seçin")
            return
        
        # Ses indir
        if download_audio:
            video_name = Path(video_path).stem
            default_path = str(Path.home() / "Desktop" / f"{video_name}_audio.wav")
            
            output_audio_path, _ = QFileDialog.getSaveFileName(
                self,
                "Ses Dosyasını Kaydet",
                default_path,
                "WAV Dosyası (*.wav);;MP3 Dosyası (*.mp3)"
            )
            
            if output_audio_path:
                logger.info(f"Ses çıkarma başlatılıyor: {video_path} ({start_time:.1f}s - {end_time:.1f}s)")
                self.statusBar().showMessage("Ses çıkarılıyor... (biraz zaman alabilir)")
                
                extractor = AudioExtractor()
                success = extractor.extract(video_path, output_audio_path, start_time, end_time)
                
                if success:
                    self.current_audio_path = output_audio_path
                    self.statusBar().showMessage(f"✅ Ses başarıyla çıkarıldı: {Path(output_audio_path).name}")
                else:
                    self.statusBar().showMessage("❌ Ses çıkarılamadı")
        
        # Video indir
        if download_video:
            video_name = Path(video_path).stem
            default_path = str(Path.home() / "Desktop" / f"{video_name}_trimmed.mp4")
            
            output_video_path, _ = QFileDialog.getSaveFileName(
                self,
                "Video Dosyasını Kaydet",
                default_path,
                "MP4 Dosyası (*.mp4);;MOV Dosyası (*.mov)"
            )
            
            if output_video_path:
                logger.info(f"Sessiz video kırpması başlatılıyor: {video_path} ({start_time:.1f}s - {end_time:.1f}s)")
                self.statusBar().showMessage("Sessiz video kırpılıyor... (biraz zaman alabilir)")
                
                trimmer = VideoTrimmer()
                success = trimmer.trim_silent(video_path, output_video_path, start_time, end_time)
                
                if success:
                    self.statusBar().showMessage(f"✅ Sessiz video başarıyla kırpıldı: {Path(output_video_path).name}")
                else:
                    self.statusBar().showMessage("❌ Video kırpılamadı")

    def _ensure_current_audio_path(self) -> bool:
        """Gerekirse seçili videodan geçici ses çıkarıp current_audio_path set eder."""
        if self.current_audio_path:
            return True

        video_path = None
        start_time = 0.0
        end_time = None

        # Öncelik: Ses sekmesinde yüklü video
        if hasattr(self, 'audio_video_path') and self.audio_video_path:
            video_path = self.audio_video_path
            if self.audio_timeline_widget:
                start_time, end_time = self.audio_timeline_widget.get_start_end_seconds()
        elif self.current_video_path:
            video_path = self.current_video_path
            if self.timeline_widget:
                start_time, end_time = self.timeline_widget.get_start_end_seconds()

        if not video_path:
            return False

        try:
            TEMP_DIR.mkdir(exist_ok=True)
            tmp_audio_path = str(TEMP_DIR / f"{Path(video_path).stem}_auto_audio.wav")
            self.statusBar().showMessage("Ses çıkarılıyor... (gürültü azaltma için)")
            extractor = AudioExtractor()
            success = extractor.extract(video_path, tmp_audio_path, float(start_time), end_time)
            if success:
                self.current_audio_path = tmp_audio_path
                return True
            return False
        except Exception as e:
            logger.error(f"Otomatik ses çıkarma hatası: {e}")
            return False
    
    def reduce_noise(self):
        """Gürültü azalt (Arka planda)"""
        if not self._ensure_current_audio_path():
            self.statusBar().showMessage("Lütfen önce bir video seçin")
            return
        
        default_path = str(TEMP_DIR / f"preview_denoised.wav")
        
        self.statusBar().showMessage("Gürültü azaltılıyor... (biraz zaman alabilir)")
        self.btn_denoise.setText("⏳ İşleniyor...")
        self.btn_denoise.setEnabled(False)
        self.btn_original.setEnabled(False)
        self.btn_denoised.setEnabled(False)
        
        self.denoise_worker = DenoiseWorker(
            self.current_audio_path,
            default_path,
            self.denoise_strength.value()
        )
        self.denoise_worker.finished.connect(lambda res: self.on_denoise_finished(res, default_path))
        self.denoise_worker.start()

    def on_denoise_finished(self, result, output_path):
        self.btn_denoise.setText("🔇 Gürültüyü Temizle")
        self.btn_denoise.setEnabled(True)
        
        if isinstance(result, dict) and result.get("success"):
            metrics = result.get("metrics") or {}
            if metrics:
                snr_db = metrics.get("snr_db")
                quality = metrics.get("quality_score")
                self.denoise_metrics_label.setText(f"SNR: {snr_db:.1f} dB | Kalite: {quality:.2f}/5")
            self.statusBar().showMessage(f"✅ Gürültü azaltıldı! A/B modunu kullanarak karşılaştırabilirsiniz.")
            
            # Enable A/B testing
            self.btn_original.setEnabled(True)
            self.btn_denoised.setEnabled(True)
            self.btn_denoised.setChecked(True)
            self.toggle_ab_mode(True, output_path)
        else:
            error_msg = result.get("error") if isinstance(result, dict) else None
            self.statusBar().showMessage("❌ Gürültü azaltılamadı" + (f": {error_msg}" if error_msg else ""))
            self.btn_original.setChecked(True)
            self.toggle_ab_mode(False)

    def toggle_ab_mode(self, use_denoised, alt_path=None):
        if not hasattr(self, 'audio_timeline_widget'): return
        
        if use_denoised:
            self.btn_denoised.setChecked(True)
            self.btn_original.setChecked(False)
            if alt_path:
                self.audio_timeline_widget.enable_ab_mode(alt_path)
            self.audio_timeline_widget.switch_audio(True)
        else:
            self.btn_original.setChecked(True)
            self.btn_denoised.setChecked(False)
            self.audio_timeline_widget.switch_audio(False)

    def auto_set_denoise_strength(self):
        """Gürültü azaltma gücünü otomatik ayarla"""
        if not self._ensure_current_audio_path():
            self.statusBar().showMessage("Lütfen önce bir video seçin")
            return

        try:
            strength = NoiseReducer.auto_detect_strength(self.current_audio_path)
            self.denoise_strength.setValue(float(strength))
            self.statusBar().showMessage(f"🤖 Otomatik güç ayarlandı: {strength:.2f}")
        except Exception as e:
            logger.error(f"Otomatik güç ayarı UI hata: {e}")
            self.statusBar().showMessage("❌ Otomatik güç ayarlanamadı")
    
    def mix_audio(self):
        """Ses karıştır (Klip Ekle)"""
        if not hasattr(self, 'audio_timeline_widget') or not self.audio_timeline_widget.video_path:
            self.statusBar().showMessage("Lütfen önce bir ana medya yükleyin")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Arka Plan Sesi Seç",
            "",
            "Ses Dosyaları (*.wav *.mp3 *.aac *.m4a *.flac);;Tüm Dosyalar (*)"
        )
        
        if file_path:
            try:
                import soundfile as sf
                try:
                    duration = sf.info(file_path).duration
                except Exception:
                    # Fallback if soundfile fails
                    import cv2
                    cap = cv2.VideoCapture(file_path)
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    duration = frames / fps if fps > 0 else 10.0
                    cap.release()
                    
                self.multi_track_timeline.add_clip(file_path, duration)
                self.statusBar().showMessage(f"✅ Zaman çizelgesine eklendi: {Path(file_path).name}")
            except Exception as e:
                logger.error(f"Ses ekleme hatası: {e}")
                self.statusBar().showMessage("❌ Ses dosyası eklenemedi")
    
    
    # (generate_subtitles method removed - replaced with start_subtitle_generation)
