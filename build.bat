@echo off
echo DenoShark PyInstaller Derleme Araci
echo Lutfen bekleyin...

REM Eger img klasorunde icon yoksa hata vermemesi icin parametre opsiyonel birakilmistir.
REM Ekrana terminal cikmamasi icin --noconsole (veya --windowed) kullanilir.
REM Auto-update sisteminin calismasi icin --onedir (klasor) yapisi kullanilir.

pyinstaller --noconfirm --onedir --windowed ^
  --name "DenoShark" ^
  --add-data "img;img" ^
  "main.py"

echo.
echo Derleme tamamlandi!
echo Cikti dosyalari "dist\DenoShark" klasorune kaydedildi.
pause
