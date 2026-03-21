@echo off
echo Starting all projects...
echo.

start "Learning Backend" cmd /k "cd learning && python manage.py runserver 8000"
timeout /t 2 /nobreak >nul

start "Frontend" cmd /k "cd frontend && npm run dev"
timeout /t 2 /nobreak >nul

start "Cree Backend" cmd /k "cd cree-eisenhower_matrix\backend && python manage.py runserver 8001"
timeout /t 2 /nobreak >nul

start "Cree Frontend" cmd /k "cd cree-eisenhower_matrix\frontend && npm run dev"

echo.
echo All projects started in separate windows!
echo.
echo Services running on:
echo - Learning Backend: http://localhost:8000
echo - Frontend: http://localhost:5173
echo - Cree Backend: http://localhost:8001
echo - Cree Frontend: http://localhost:5174
echo.
pause
