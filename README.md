# Data Quality Watchtower

A Django web application for monitoring data quality in tabular datasets (CSV files and database tables) using rule-based validations, incident tracking, and automated remediation.

## Features

- **Dataset Management**: Upload CSV datasets or reference database tables
- **Rule Engine**: Define data quality rules using a DSL (NOT_NULL, UNIQUE, RANGE, FK)
- **Automated Scheduling**: Run rules periodically using Celery and Redis
- **Incident Management**: Track data quality issues with lifecycle management
- **Dashboards**: Visualize data quality metrics with Chart.js
- **Role-Based Access Control**: Admin, Data Steward, and Viewer roles
- **Audit Logs**: Immutable record of all system actions
- **Auto-Remediation**: Webhooks and SQL scripts for automatic fixes
- **Export Functionality**: Export incidents, rule runs, and audit logs
- **User Authentication**: Registration, login, and profile management
- **Enhanced File Upload**: Drag-and-drop CSV file upload interface

## Prerequisites

- Python 3.9+
- Redis (for Celery)
- PostgreSQL (optional, SQLite used by default for development)

## Installation Options

### Option 1: Docker Installation (Recommended)

**Note**: Make sure Docker Desktop is installed and running on your system.

```bash
# On Windows:
start.bat

# Or manually:
docker-compose up --build
```

This will:
1. Build all required Docker images
2. Start all services (web, worker, beat, redis, db)
3. Automatically run database migrations
4. Create a default admin user (admin/admin123)
5. Seed demo data
6. Start the application stack

Access the application at `http://localhost:8000`

### Option 2: Local Installation

1. Run the setup script:
   ```bash
   setup.bat
   ```

2. Start the application:
   ```bash
   start_server.bat
   ```

3. In separate terminals, start Celery services:
   ```bash
   start_celery.bat
   start_beat.bat
   ```

## Manual Installation (Alternative)

### Prerequisites
- Python 3.9+
- Redis
- PostgreSQL (or SQLite for development)

### Installation Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd data-quality-watchtower
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the database:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123')"
   ```

6. Setup permissions:
   ```bash
   python manage.py setup_permissions
   python manage.py assign_role admin Admin
   ```

7. Seed demo data:
   ```bash
   python manage.py seed_demo_data
   ```

8. Start the development server:
   ```bash
   python manage.py runserver
   ```

9. In a separate terminal, start the Celery worker:
   ```bash
   celery -A data_quality_watchtower worker -l info
   ```

10. In another terminal, start the Celery beat scheduler:
    ```bash
    celery -A data_quality_watchtower beat -l info
    ```

## Usage

1. Access the main application at `http://localhost:8000/`
2. Log in with admin credentials: admin / admin123
3. Register new users or assign roles using management commands
4. Navigate to Datasets to upload CSV files using the drag-and-drop interface
5. Create rules to validate your data
6. Monitor incidents and dashboards for data quality insights

## User Authentication

The application provides a complete user authentication system:
- **Admin Login**: username `admin`, password `admin123`
- **Registration**: New users can create accounts at `/users/register/`
- **Login**: Users can sign in at `/users/login/`
- **Profile Management**: Users can view and update their profiles
- **Logout**: Users can securely sign out

## Role-Based Access Control

- **Admin**: Full access to all features
- **Data Steward**: Manage datasets and rules
- **Viewer**: View-only access

Assign roles using:
```bash
python manage.py assign_role <username> <role>
```

## File Upload

The enhanced file upload interface provides:
- Drag-and-drop CSV file upload
- File size display
- Visual feedback during upload
- Support for both CSV files and database connections

To upload a dataset:
1. Navigate to the Datasets section
2. Click "Add Dataset"
3. Select "CSV File" as the source type
4. Drag and drop your CSV file or click to browse
5. Enter a name for your dataset
6. Save the dataset

## Commands

### Database Management
```bash
# Run migrations
python manage.py migrate

# Create migrations for model changes
python manage.py makemigrations

# Collect static files
python manage.py collectstatic
```

### User Management
```bash
# Create superuser with default credentials
python manage.py create_superuser

# Create superuser with custom credentials
python manage.py create_superuser --username myuser --email myuser@example.com --password mypassword

# Assign role to user
python manage.py assign_role <username> <role>

# Setup permissions
python manage.py setup_permissions

# Seed demo users
python manage.py seed_demo_data
```

### Data Seeding
```bash
# Seed all demo data (datasets, rules, rule runs, incidents)
python manage.py seed_demo_data
```

### Celery Tasks
```bash
# Start Celery worker
celery -A data_quality_watchtower worker -l info

# Start Celery beat scheduler
celery -A data_quality_watchtower beat -l info

# Run a specific rule
python manage.py run_rule <rule_id>

# Run all active rules
python manage.py run_all_rules
```

### Testing
```bash
# Run tests
python manage.py test

# Test dashboard API
python test_dashboard_api.py
```

## Seeding Demo Data

To populate the database with sample data:
```bash
python manage.py seed_demo_data
```

This will create:
- 3 datasets (Customer Data, Order Data, Product Data)
- 8 rules (NOT_NULL, UNIQUE, RANGE, FK)
- 50 rule runs
- 15 incidents

## Project Structure

```
data_quality_watchtower/
├── data_quality_watchtower/    # Main Django project
│   ├── settings.py             # Django settings
│   ├── urls.py                 # Main URL configuration
│   └── celery.py               # Celery configuration
├── rules/                      # Rule engine and dataset management
├── incidents/                  # Incident tracking and management
├── dashboards/                 # Dashboard views and visualizations
├── audits/                     # Audit logging
├── users/                      # User management and authentication
├── templates/                  # HTML templates
├── static/                     # Static files (CSS, JS, images)
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
└── docker-compose.yml          # Docker Compose configuration
```

## DSL Rules

The application supports the following rule types:

1. **NOT_NULL**: Ensures a column has no null values
   ```
   NOT_NULL("email")
   ```

2. **UNIQUE**: Ensures all values in a column are unique
   ```
   UNIQUE("id")
   ```

3. **RANGE**: Ensures numeric values are within a specified range
   ```
   RANGE("age", min=18, max=65)
   ```

4. **FK**: Ensures foreign key relationships are valid
   ```
   FK("customer_id", "customers.id")
   ```

## Troubleshooting

### Common Issues

1. **Chart not rendering**: Ensure JavaScript is enabled and check browser console for errors
2. **Empty JSON response**: Verify that demo data has been seeded
3. **Celery not running**: Check Redis connection and Celery logs
4. **Database connection failure**: Verify database credentials and connectivity
5. **Static files missing**: Run `python manage.py collectstatic`
6. **Docker issues**: Make sure Docker Desktop is running

### Debugging Steps

1. Check Django server logs for errors
2. Verify Celery worker is running
3. Ensure Redis is accessible
4. Confirm database connectivity
5. Check browser developer tools for frontend errors

## Technologies Used

- **Backend**: Django 4.2
- **Task Queue**: Celery with Redis
- **Database**: PostgreSQL (with SQLite support)
- **Frontend**: Bootstrap 5, Chart.js
- **Forms**: django-crispy-forms
- **Data Processing**: pandas
- **Deployment**: Docker, Docker Compose

## License

This project is licensed under the MIT License - see the LICENSE file for details.