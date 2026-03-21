@echo off
echo ========================================
echo Running Database Migrations
echo ========================================
echo.

echo [1/2] Migrating Learning Platform Database...
cd learning
python manage.py migrate
cd ..
echo ✓ Learning platform migrated!
echo.

echo [2/2] Migrating Cree Eisenhower Matrix Database...
cd cree-eisenhower_matrix\backend
python manage.py migrate
cd ..\..
echo ✓ Cree Eisenhower migrated!
echo.

echo ========================================
echo ✓ ALL MIGRATIONS COMPLETE!
echo ========================================
echo.
pause
