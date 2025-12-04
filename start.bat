@echo off
setlocal enabledelayedexpansion
title Data Quality Watchtower

echo Starting Data Quality Watchtower...

:: Create necessary directories
if not exist "logs" mkdir logs
if not exist "media" mkdir media
if not exist "staticfiles" mkdir staticfiles

:: Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

:: Wait for database to be ready
echo Waiting for database to be ready...
timeout /t 2 /nobreak >nul

:: Run migrations
echo Running database migrations...
python manage.py migrate --noinput

:: Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput --clear

:: Create superuser if it doesn't exist
echo Creating superuser if needed...
python manage.py shell -c "try: from django.contrib.auth import get_user_model; User = get_user_model(); print('Superuser already exists') if User.objects.filter(username='admin').exists() else (User.objects.create_superuser('admin', 'admin@example.com', 'admin123'), print('Superuser created: admin/admin123'))[1]; except Exception as e: print(f'Could not create superuser: {e}')"

:: Seed demo data if needed
echo Seeding demo data...
python manage.py seed_demo_data || echo Warning: Could not seed demo data

:: Start all services
echo Starting development server...
echo Access the application at: http://localhost:8000
echo Admin panel at: http://localhost:8000/admin

:: Run the Django development server
python manage.py runserver 0.0.0.0:8000

pause