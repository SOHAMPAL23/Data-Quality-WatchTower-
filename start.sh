#!/bin/bash

# Data Quality Watchtower - Startup Script

# Exit on any error
set -e

echo "Starting Data Quality Watchtower..."

# Create necessary directories
mkdir -p logs media staticfiles

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 2

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist
echo "Creating superuser if needed..."
python manage.py shell -c "
try:
    from django.contrib.auth import get_user_model;
    User = get_user_model();
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123');
        print('Superuser created: admin/admin123');
    else:
        print('Superuser already exists');
except Exception as e:
    print(f'Could not create superuser: {e}');
"

# Seed demo data if needed
echo "Seeding demo data..."
python manage.py seed_demo_data || echo "Warning: Could not seed demo data"

# Start all services
echo "Starting development server..."
echo "Access the application at: http://localhost:8000"
echo "Admin panel at: http://localhost:8000/admin"

# Run the Django development server
python manage.py runserver 0.0.0.0:8000