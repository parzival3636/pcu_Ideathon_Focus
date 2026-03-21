@echo off
echo ========================================
echo Installing All Project Dependencies
echo ========================================
echo.

echo [1/7] Installing Learning Platform (Django Backend)...
cd learning
pip install -r requirements.txt
if exist adaptive_learning_requirements.txt (
    pip install -r adaptive_learning_requirements.txt
)
cd ..
echo ✓ Learning platform dependencies installed!
echo.

echo [2/7] Installing Frontend (React + Vite)...
cd frontend
call npm install
cd ..
echo ✓ Frontend dependencies installed!
echo.

echo [3/7] Installing Web Scraping Module...
cd webscrappingmodule
pip install -r requirements.txt
cd ..
echo ✓ Web scraping module dependencies installed!
echo.

echo [4/7] Installing Course Recommender...
pip install jupyter pandas numpy scikit-learn matplotlib seaborn
echo ✓ Course recommender dependencies installed!
echo.

echo [5/7] Installing Cree Eisenhower Matrix Backend...
cd cree-eisenhower_matrix\backend
pip install -r requirements.txt
cd ..\..
echo ✓ Cree Eisenhower backend dependencies installed!
echo.

echo [6/7] Installing Cree Eisenhower Matrix Frontend...
cd cree-eisenhower_matrix\frontend
call npm install
cd ..\..
echo ✓ Cree Eisenhower frontend dependencies installed!
echo.

echo [7/7] Installing Study Content Recommender...
cd study-content-recommender
pip install -r requirements.txt
cd ..
echo ✓ Study content recommender dependencies installed!
echo.

echo ========================================
echo ✓ ALL DEPENDENCIES INSTALLED SUCCESSFULLY!
echo ========================================
echo.
pause
