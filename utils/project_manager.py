import json
import os
from pathlib import Path
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer

class ProjectManager:
    """Handles serialization and loading of DenoShark (.deno) projects."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_project_path = None
        self.last_used_directory = str(Path.home())

    def save_project(self, file_path: str):
        """Serializes the workspace state and saves to a .deno file."""
        state = {
            "version": "1.0",
            "settings": self._get_settings(),
            "media_pool": self._get_media_pool(),
            "timeline": self._get_timeline()
        }
        
        # Projenin bir küçük resmini (thumbnail/logo) base64 olarak JSON'a ekle ve yanına resim olarak çıkar
        thumbnail_data = self._generate_project_thumbnail()
        if thumbnail_data:
            state["thumbnail_base64"] = thumbnail_data
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=4)
                
            # Eğer kullanıcı klasörde görmek isterse diye proje dosyasının yanına .png olarak logoyu da kaydedelim
            if thumbnail_data:
                try:
                    import base64
                    png_path = str(Path(file_path).with_suffix('.png'))
                    with open(png_path, "wb") as img_file:
                        img_file.write(base64.b64decode(thumbnail_data))
                except Exception as e:
                    print(f"Error saving thumbnail image: {e}")
                    
            self.current_project_path = file_path
            self.last_used_directory = str(Path(file_path).parent)
            return True
        except Exception as e:
            print(f"Error saving project: {e}")
            return False

    def _generate_project_thumbnail(self) -> str:
        """Kullanıcının isteği üzerine img/logo-small.png dosyasını projenin küçük resmi (logo) olarak ayarlar."""
        import base64
        import os
        from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
        from PyQt6.QtGui import QPixmap
        
        try:
            # Projedeki varsayılan logoyu yükle
            logo_path = os.path.join(os.getcwd(), 'img', 'logo-small.png')
            if not os.path.exists(logo_path):
                 return ""
                 
            pixmap = QPixmap(logo_path)
            
            # Base64 string'e dönüştür
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(buffer, "PNG")
            return base64.b64encode(byte_array.data()).decode('utf-8')
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return ""

    def load_project(self, file_path: str):
        """Loads a .deno project and reconstructs the workspace."""
        if not os.path.exists(file_path):
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                
            # Clear current workspace
            self._clear_workspace()
            
            # Apply settings
            self._apply_settings(state.get("settings", {}))
            
            # Load Media Pool
            for media_path in state.get("media_pool", []):
                if os.path.exists(media_path):
                    self.main_window.media_pool.add_file(media_path)
                else:
                    print(f"Warning: Media file not found: {media_path}")
            
            # Load Timeline
            for clip_data in state.get("timeline", []):
                filepath = clip_data.get("file_path")
                if os.path.exists(filepath):
                    self._add_to_timeline(clip_data)
                else:
                    print(f"Warning: Timeline media not found: {filepath}")

            # Sync main video clip with preview players
            self._sync_preview_from_timeline()
            
            # Emit changes for audio engine updates
            self.main_window.multi_track_timeline.timeline_changed.emit(
                self.main_window.multi_track_timeline.get_mix_data()
            )
            
            self.current_project_path = file_path
            self.last_used_directory = str(Path(file_path).parent)
            return True
        except Exception as e:
            print(f"Error loading project: {e}")
            return False

    def _sync_preview_from_timeline(self):
        """Load primary video clip into preview players and show first frame."""
        timeline = self.main_window.multi_track_timeline
        primary_clip = timeline.main_video_clip

        if not primary_clip:
            video_clips = [c for c in timeline.clips if c.clip_type == 'video']
            if video_clips:
                primary_clip = sorted(video_clips, key=lambda c: (c.track_idx, c.start_time))[0]

        if not primary_clip:
            return

        video_path = primary_clip.file_path
        if not video_path or not os.path.exists(video_path):
            return

        self.main_window.current_video_path = video_path
        if hasattr(self.main_window, 'timeline_widget'):
            self.main_window.timeline_widget.load_video(video_path)

        if hasattr(self.main_window, 'audio_timeline_widget'):
            self.main_window.audio_video_path = video_path
            self.main_window.audio_timeline_widget.load_video(video_path)

        # Force first frame render
        if hasattr(self.main_window, 'timeline_widget'):
            player = self.main_window.timeline_widget.media_player
            QTimer.singleShot(200, lambda: self._force_preview_frame(player))

    def _force_preview_frame(self, player):
        try:
            player.setPosition(0)
            player.pause()
        except Exception:
            pass

    def auto_save(self, temp_dir: str):
        """Performs a silent background save to a temporary file."""
        import tempfile
        temp_file = os.path.join(temp_dir, ".denoshark_autosave.deno")
        self.save_project(temp_file)

    def _get_settings(self):
        settings = {
            "last_used_directory": self.last_used_directory,
        }
        if hasattr(self.main_window, 'denoise_strength'):
            settings["denoise_strength"] = self.main_window.denoise_strength.value()
        if hasattr(self.main_window, 'extract_audio_checkbox'):
            settings["extract_audio"] = self.main_window.extract_audio_checkbox.isChecked()
        if hasattr(self.main_window, 'extract_video_checkbox'):
            settings["extract_video"] = self.main_window.extract_video_checkbox.isChecked()
        return settings

    def _apply_settings(self, settings):
        self.last_used_directory = settings.get("last_used_directory", str(Path.home()))
        
        if hasattr(self.main_window, 'denoise_strength') and "denoise_strength" in settings:
            self.main_window.denoise_strength.setValue(settings["denoise_strength"])
        if hasattr(self.main_window, 'extract_audio_checkbox') and "extract_audio" in settings:
            self.main_window.extract_audio_checkbox.setChecked(settings["extract_audio"])
        if hasattr(self.main_window, 'extract_video_checkbox') and "extract_video" in settings:
            self.main_window.extract_video_checkbox.setChecked(settings["extract_video"])

    def _get_media_pool(self):
        media_pool_widget = self.main_window.media_pool
        from PyQt6.QtCore import Qt
        files = []
        for i in range(media_pool_widget.list_widget.count()):
            item = media_pool_widget.list_widget.item(i)
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                files.append(file_path)
        return files

    def _get_timeline(self):
        timeline_widget = self.main_window.multi_track_timeline
        clips_data = []
        for clip in timeline_widget.clips:
            # We don't save AudioClipItem directly, we save its properties
            clip_dict = {
                "file_path": clip.file_path,
                "start_time": clip.start_time,
                "duration": clip.duration,
                "media_start": clip.media_start,
                "track_idx": clip.track_idx,
                "clip_type": clip.clip_type,
                "is_main": clip.is_main
            }
            clips_data.append(clip_dict)
        return clips_data

    def _clear_workspace(self):
        # Clear Media Pool
        self.main_window.media_pool.list_widget.clear()
        
        # Clear Timeline
        timeline = self.main_window.multi_track_timeline
        for clip in timeline.clips:
            timeline.scene.removeItem(clip)
        timeline.clips.clear()
        timeline.main_video_clip = None
        timeline.main_audio_clip = None

    def _add_to_timeline(self, clip_data):
        from ui.widgets import AudioClipItem
        timeline = self.main_window.multi_track_timeline
        
        clip_item = AudioClipItem(
            file_path=clip_data["file_path"],
            start_time=clip_data["start_time"],
            duration=clip_data["duration"],
            pixels_per_second=timeline.pixels_per_second,
            track_idx=clip_data["track_idx"],
            clip_type=clip_data["clip_type"],
            is_main=clip_data.get("is_main", False),
            media_start=clip_data.get("media_start", 0.0)
        )
        
        timeline.scene.addItem(clip_item)
        timeline.clips.append(clip_item)
        
        if clip_item.is_main:
            if clip_item.clip_type == 'video':
                timeline.main_video_clip = clip_item
            elif clip_item.clip_type == 'audio':
                timeline.main_audio_clip = clip_item
