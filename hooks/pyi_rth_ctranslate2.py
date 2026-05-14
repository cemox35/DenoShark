"""
Runtime hook: ctranslate2 DLL'lerini frozen ortamda doğru sırayla yükle.

PyInstaller'ın bootloader'ı _MEIPASS'ı AddDllDirectory ile PATH'e ekler,
ama ctranslate2/__init__.py kendi dizinini (ctranslate2/) importlib.resources
üzerinden buluyor. Frozen ortamda bu yol bazen doğru resolve edilmiyor;
burada DLL'leri önceden _internal/ctranslate2/ konumundan yüklüyoruz.
"""
import os
import sys
import ctypes

if hasattr(sys, '_MEIPASS'):
    ct2_dir = os.path.join(sys._MEIPASS, 'ctranslate2')

    # ctranslate2 alt dizinini DLL arama yoluna ekle
    if os.path.isdir(ct2_dir):
        try:
            os.add_dll_directory(ct2_dir)
        except (OSError, AttributeError):
            pass

        # PATH'e de ekle (eski Windows fallback)
        os.environ['PATH'] = ct2_dir + os.pathsep + os.environ.get('PATH', '')

        # Doğru dep sırası: önce OpenMP, sonra ctranslate2 core
        # cudnn64_9.dll kasıtlı olarak atlanıyor — CPU-only modda gerekli değil
        # ve bazı sistemlerde DllMain'i 0xC0000005 ile crash yapıyor.
        for dll_name in ('libiomp5md.dll', 'ctranslate2.dll'):
            dll_path = os.path.join(ct2_dir, dll_name)
            if os.path.exists(dll_path):
                try:
                    ctypes.CDLL(dll_path)
                except OSError:
                    pass
