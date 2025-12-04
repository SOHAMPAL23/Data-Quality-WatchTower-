#!/usr/bin/env bash
# Exit on error
set -o errexit

# Setup Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install Python dependencies
pip install -r requirements.txt

# Wait for database to be ready
echo "Waiting for database to be ready..."
for i in {1..30}; do
  if python -c "import django; django.setup(); from django.db import connection; connection.cursor()" > /dev/null 2>&1; then
    echo "Database is ready!"
    break
  fi
  echo "Database not ready yet, retrying in 2 seconds... ($i/30)"
  sleep 2
done

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser if it doesn't exist..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell