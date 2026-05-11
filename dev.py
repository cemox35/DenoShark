import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        self.last_restart = time.time()
        
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            # Debounce (Peş peşe gelen değişiklikleri tekilleştir)
            if time.time() - self.last_restart > 1.0:
                self.last_restart = time.time()
                self.callback()

class AppReloader:
    def __init__(self):
        self.process = None
        self.cmd = [sys.executable, "main.py"]
        
    def start_app(self):
        if self.process:
            print("\n[DEV] Değişiklik algılandı. Uygulama yeniden başlatılıyor...")
            self.process.terminate()
            self.process.wait()
        else:
            print("[DEV] DenoShark Geliştirici Modu Başlatıldı. Değişiklikler izleniyor...\n")
            
        self.process = subprocess.Popen(self.cmd)
        
    def run(self):
        self.start_app()
        
        event_handler = ChangeHandler(self.start_app)
        observer = Observer()
        
        # İzlenecek klasörleri ekle
        root_dir = Path(__file__).parent
        dirs_to_watch = [root_dir, root_dir / "ui", root_dir / "utils", root_dir / "video_processor"]
        
        for d in dirs_to_watch:
            if d.exists():
                observer.schedule(event_handler, str(d), recursive=False)
                
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            if self.process:
                self.process.terminate()
            print("\n[DEV] Geliştirici Modu Kapatıldı.")
        observer.join()

if __name__ == "__main__":
    reloader = AppReloader()
    reloader.run()
