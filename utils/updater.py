import os
import sys
import shutil
import zipfile
import requests
import subprocess
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Kendi Google Drive'ınıza koyduğunuz version.txt'nin doğrudan indirme linkini buraya ekleyin.
# Şimdilik örnek bir yapı kuruyoruz, burayı daha sonra kendi linkinizle değiştirmelisiniz.
VERSION_TXT_URL = "https://docs.google.com/uc?export=download&id=1lfmRvoyclkXA8B2wqLT-hGaqpMvfxslP"

def check_for_updates(current_version):
    """
    Drive üzerindeki version.txt dosyasını okuyarak güncellemeleri kontrol eder.
    Version.txt formatı şöyle olmalıdır:
    1.0.1
    1X_DRiVe_iD_oF_ZIp_fILe_H3r3
    
    Yani ilk satır versiyon numarası, ikinci satır ise yeni sürümün ZIP dosyasının Drive ID'si.
    """
    try:
        if "BURAYA_VERSION_TXT_DRIVE_ID_GELECEK" in VERSION_TXT_URL:
            logger.warning("Version URL ayarlanmamis, guncelleme atlandi.")
            # We removed the early return since we have a real URL now.

        response = requests.get(VERSION_TXT_URL, timeout=10)
        response.raise_for_status()
        
        lines = response.text.strip().splitlines()
        if len(lines) >= 2:
            latest_version = lines[0].strip()
            zip_drive_id = lines[1].strip()
            
            # Basit versiyon karsilastirmasi
            # Ornegin "1.0.1" > "1.0.0"
            if parse_version(latest_version) > parse_version(current_version):
                return True, latest_version, zip_drive_id
            
        return False, None, None
    except Exception as e:
        logger.error(f"Guncelleme kontrolunde hata: {e}")
        return False, None, None

def parse_version(version_str):
    """'1.0.1' stringini (1, 0, 1) tuple'ına çevirir"""
    try:
        return tuple(map(int, version_str.split(".")))
    except:
        return (0, 0, 0)

def download_file_from_google_drive(id, destination, progress_callback=None):
    """
    Drive'daki buyuk/kucuk dosyalari (virus taramasi uyarisi ciksa bile) indirir.
    """
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()

    try:
        response = session.get(URL, params={'id': id}, stream=True)
        token = _get_confirm_token(response)

        if token:
            params = {'id': id, 'confirm': token}
            response = session.get(URL, params=params, stream=True)

        total_length = response.headers.get('content-length')
        
        with open(destination, "wb") as f:
            if total_length is None: # contentLength yoksa yuzde hesaplayamayiz
                f.write(response.content)
            else:
                total_length = int(total_length)
                downloaded = 0
                for chunk in response.iter_content(32768):
                    if chunk: 
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            percent = int((downloaded / total_length) * 100)
                            progress_callback(percent)
        return True
    except Exception as e:
        logger.error(f"Dosya indirme hatasi: {e}")
        return False

def _get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None

def apply_update_and_restart(zip_path, root_dir):
    """
    Zip dosyasını diske açıp, kendi üzerine yazmayı bypass edebilmek için 
    gecici bir "update.bat" betigi olusturur.
    PyQt gibi arayuzleri uzerine acarken sorun yasamamak icin arayuzu kapatmamiz gerekir.
    """
    # Root dizini string olarak al
    root_str = str(Path(root_dir).resolve())
    temp_extract_dir = os.path.join(root_str, "temp", "update_extract")
    
    # 1. Zip dosyasini temp'e cikar
    if os.path.exists(temp_extract_dir):
        shutil.rmtree(temp_extract_dir)
    os.makedirs(temp_extract_dir, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_dir)

    # 2. update.bat olustur
    bat_path = os.path.join(root_str, 'update.bat')
    
    # Eger PyInstaller ile .exe yapilmisa sys.executable exe'nin kendisidir. Yoksa python.exe'dir.
    import sys
    if getattr(sys, 'frozen', False):
        # Exe formatinda calisiyorsa
        exe_name = os.path.basename(sys.executable)
        restart_cmd = f'start /b "" "{os.path.join(root_str, exe_name)}"'
    else:
        # Script formatinda calisiyorsa
        restart_cmd = f'start /b python "{os.path.join(root_str, "main.py")}"'

    bat_content = f"""@echo off
echo DenoShark Guncelleniyor... Lutfen bekleyin.
timeout /t 2 /nobreak > NUL
xcopy /E /Y /C "{temp_extract_dir}\\*" "{root_str}\\"
rmdir /S /Q "{temp_extract_dir}"
del /Q "{zip_path}"
{restart_cmd}
del "%~f0"
"""
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)
        
    # 3. BAT dosyasini calistir (bagimsiz pencerede)
    subprocess.Popen([bat_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
    
    # Programi sonlandir (PyQt kapanacak ve bat dosyasi ustune yazma islemine baslayacak)
    sys.exit(0)
