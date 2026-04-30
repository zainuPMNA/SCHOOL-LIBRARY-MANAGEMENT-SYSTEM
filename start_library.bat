@echo off
color 0A
echo ========================================================
echo       YES PA INAMDAR SCHOOL LIBRARY MANAGEMENT
echo ========================================================
echo.

:: Check if virtual environment exists
IF NOT EXIST "env\Scripts\activate.bat" (
    echo [!] First time setup detected on this PC.
    echo [!] Creating isolated Python environment...
    python -m venv env
    
    echo [!] Installing required dependencies...
    call env\Scripts\activate.bat
    pip install -r requirements.txt
    echo [!] Setup Complete!
    echo.
) ELSE (
    echo [i] Starting Library System...
    call env\Scripts\activate.bat
)

echo.
echo [i] Opening your web browser...
:: Wait 2 seconds to ensure server starts before browser opens
timeout /t 2 /nobreak > NUL
start http://127.0.0.1:5000

echo [i] The server is running. Keep this black window open while using the app!
echo [i] To close the library app, close this window.
echo.
python app.py

pause
