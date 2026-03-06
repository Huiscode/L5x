@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"
set "VENV_PY=%BACKEND%\.venv\Scripts\python.exe"
set "PY_CMD="

where py >nul 2>nul
if not errorlevel 1 set "PY_CMD=py"
if not defined PY_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PY_CMD=python"
)

if not defined PY_CMD (
  echo [ERROR] Python was not found in PATH.
  echo Install Python 3.11+ and reopen terminal.
  pause
  exit /b 1
)

if not exist "%VENV_PY%" (
  echo [INFO] Backend virtual environment not found. Creating it now...
  pushd "%BACKEND%"
  call %PY_CMD% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create backend virtual environment.
    popd
    pause
    exit /b 1
  )

  call .venv\Scripts\python.exe -m pip install --upgrade pip
  call .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Failed to install backend requirements.
    popd
    pause
    exit /b 1
  )
  popd
)

if not exist "%FRONTEND%\node_modules" (
  echo [INFO] Installing frontend dependencies...
  pushd "%FRONTEND%"
  call npm install
  if errorlevel 1 (
    echo [ERROR] npm install failed.
    popd
    pause
    exit /b 1
  )
  popd
)

echo Starting backend on http://127.0.0.1:8000 ...
start "app-L5x Backend" /D "%BACKEND%" cmd /k ""%VENV_PY%" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo Starting frontend on http://127.0.0.1:5173 ...
start "app-L5x Frontend" /D "%FRONTEND%" cmd /k "npm run dev -- --host 127.0.0.1 --port 5173"

timeout /t 2 >nul
start "" "http://127.0.0.1:5173"

echo.
echo Both services launched in separate windows.
echo Frontend: http://127.0.0.1:5173
echo Backend:  http://127.0.0.1:8000
echo.
