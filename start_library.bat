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

:: Get local IPv4 Address using PowerShell
for /f "tokens=*" %%a in ('powershell -Command "Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias 'Wi-Fi*','Ethernet*' | Where-Object {$_.IPAddress -notlike '169.254*'} | Select-Object -ExpandProperty IPAddress | Select-Object -First 1"') do set LOCAL_IP=%%a

if "%LOCAL_IP%"=="" set LOCAL_IP=127.0.0.1

echo.
echo ========================================================
echo   [i] LOCAL SERVER RUNNING!
echo   ------------------------------------------------------
echo   [+] Access on THIS PC:       http://localhost:5000
echo   [+] Access from OTHER DEVICES (Wi-Fi/LAN):
echo       http://%LOCAL_IP%:5000
echo ========================================================
echo.

echo [i] Opening your web browser...
:: Wait 2 seconds to ensure server starts before browser opens
timeout /t 2 /nobreak > NUL
start http://localhost:5000

echo [i] Keep this window open while using the app!
echo [i] To stop the server, close this window or press Ctrl+C.
echo.
python app.py

pause
