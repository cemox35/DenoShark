@echo off
echo DenoShark PyInstaller Derleme Araci
echo Lutfen bekleyin...
echo.

REM Venv icindeki pyinstaller'i dogrudan calistir (activate'e gerek yok)
.venv\Scripts\pyinstaller.exe --noconfirm --clean DenoShark.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] Derleme basarisiz oldu! Hata kodu: %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Derleme tamamlandi!
echo Cikti: dist\DenoShark\DenoShark.exe
pause
