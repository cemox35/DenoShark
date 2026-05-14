@echo off
echo DenoShark PyInstaller Derleme Araci
echo Lutfen bekleyin...

REM .spec dosyasi kullanilirken --onedir/--windowed gibi makespec opsiyonlari verilmez.

pyinstaller --noconfirm --clean DenoShark.spec

echo.
echo Derleme tamamlandi!
echo Cikti dosyalari "dist\DenoShark" klasorune kaydedildi.
pause
