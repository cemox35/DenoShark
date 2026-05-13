@echo off
echo DenoShark PyInstaller Derleme Araci
echo Lutfen bekleyin...

REM Ekrana terminal cikmamasi icin --windowed kullanilir.
REM Auto-update ve tasinabilir calisma icin --onedir (klasor) yapisi kullanilir.

pyinstaller --noconfirm --clean --windowed --onedir DenoShark.spec

echo.
echo Derleme tamamlandi!
echo Cikti dosyalari "dist\DenoShark" klasorune kaydedildi.
pause
