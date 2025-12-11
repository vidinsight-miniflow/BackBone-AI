@echo off
REM BackBone-AI Quick Install Script for Windows

echo ==================================
echo BackBone-AI Kurulum
echo ==================================
echo.

REM Check Python
echo [*] Python kontrol ediliyor...
python --version
if errorlevel 1 (
    echo [!] Python bulunamadi! Python 3.8+ yuklemeniz gerekiyor.
    pause
    exit /b 1
)
echo.

REM Create virtual environment
if not exist "venv" (
    echo [*] Virtual environment olusturuluyor...
    python -m venv venv
    echo [+] Virtual environment olusturuldu
) else (
    echo [+] Virtual environment zaten mevcut
)
echo.

REM Activate virtual environment
echo [*] Virtual environment aktif ediliyor...
call venv\Scripts\activate.bat
echo.

REM Upgrade pip
echo [*] pip guncelleniyor...
python -m pip install --upgrade pip >nul 2>&1
echo [+] pip guncellendi
echo.

REM Install dependencies
echo [*] Bagimlilaklar yukleniyor...
echo    (Bu birkac dakika surebilir...)
pip install -r requirements.txt >nul 2>&1
echo [+] Tum bagimlilaklar yuklendi
echo.

REM Create .env
if not exist ".env" (
    echo [*] .env dosyasi olusturuluyor...
    copy .env.example .env >nul
    echo [+] .env dosyasi olusturuldu
    echo.
    echo [!] DIKKAT: .env dosyasini duzenleyip API anahtarinizi ekleyin!
    echo.
) else (
    echo [+] .env dosyasi zaten mevcut
    echo.
)

echo ==================================
echo [+] Kurulum tamamlandi!
echo ==================================
echo.
echo Sonraki adimlar:
echo.
echo 1. API anahtarinizi ekleyin:
echo    notepad .env
echo.
echo 2. Kodu test edin:
echo    venv\Scripts\activate
echo    backbone-ai generate --schema examples\simple_schema.json
echo.
echo 3. API modunda calistirin:
echo    uvicorn app.api.main:app --reload
echo.
echo Daha fazla bilgi: README.md veya QUICKSTART.md
echo.
pause
