# Data Quality Watchtower

A comprehensive web application for monitoring data quality for CSV datasets and database tables using customizable rules.

## Features

- **Dataset Management**: Upload CSV files or connect to database tables with automatic schema inference
- **Rule Engine**: Create data quality rules with an enhanced DSL (NOT NULL, UNIQUE, RANGE, MATCHES, FOREIGN KEY, CUSTOM PYTHON)
- **Auto Rule Generation**: Automatic rule recommendations based on data analysis
- **Incident Management**: Track data quality violations with workflow states (OPEN → ACK → MUTED/RESOLVED)
- **Dashboard**: Visualize data quality metrics with trend charts and heatmaps
- **Evidence Storage**: Store sample failed records for incident investigation
- **Audit Logging**: Immutable logs of all system activities
- **API Layer**: RESTful API for integration with external systems
- **Export Functionality**: Export incidents and dashboards as CSV and PDF
- **RBAC**: Role-based access control (Admin, DataEngineer, Analyst)
- **Celery Integration**: Background task processing for rule execution with idempotency
- **Modern UI**: Responsive interface with glassmorphism design

## Technology Stack

### Backend
- Django 4.2+
- Django ORM
- Celery + Redis
- PostgreSQL (with SQLite fallback)
- pandas for data processing

### Frontend
- Django Templates
- Modern CSS (gradient backgrounds, glassmorphism, animations)
- D3.js for charts
- Bootstrap 5

### Utilities
- pandas for CSV parsing and analysis
- django-filter
- crispy-forms
- reportlab for PDF generation

### Deployment
- Docker + docker-compose
- Celery worker + beat
- PostgreSQL + Redis containers

## Project Structure

```
project_root/
 ├── manage.py
 ├── data_quality_watchtower/
 │     ├── settings.py
 │     ├── urls.py
 │     ├── celery.py
 │     └── __init__.py
 ├── apps/
 │     ├── datasets/
 │     ├── rules/
 │     ├── incidents/
 │     ├── dashboard/
 │     ├── api/
 │     ├── users/
 │     ├── audit/
 ├── templates/
 │     ├── base.html
 │     ├── dashboard.html
 │     ├── datasets.html
 │     ├── rules.html
 │     ├── incidents.html
 │     └── evidence.html
 ├── static/
 │     └── css/
 │           └── style.css
 ├── requirements.txt
 ├── docker-compose.yml
 ├── Dockerfile
```

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd DataQualityWatchTowers
   ```

2. Start the application:
   ```bash
   docker-compose up --build
   ```

3. Access the application:
   - Web UI: http://localhost:8000
   - Admin Panel: http://localhost:8000/admin
   - API Endpoints: http://localhost:8000/api/

4. Run database migrations:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

6. Seed demo data:
   ```bash
   docker-compose exec web python manage.py seed_demo_data
   ```

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up the database:
   ```bash
   python manage.py migrate
   ```

3. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

4. Seed demo data:
   ```bash
   python manage.py seed_demo_data
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

6. In a separate terminal, start Celery worker:
   ```bash
   celery -A data_quality_watchtower worker --loglevel=info
   ```

7. In another terminal, start Celery beat:
   ```bash
   celery -A data_quality_watchtower beat --loglevel=info
   ```

## API Endpoints

- `GET /api/dashboard/stats/` - Get dashboard statistics
- `POST /api/rules/run/` - Trigger rule execution
- `GET /api/incidents/` - Get incidents with filtering options
- `GET /api/datasets/{id}/recommendations/` - Get rule recommendations for a dataset

## Rule DSL

The application supports the following rule types:

- `NOT_NULL("column_name")` - Check for non-null values
- `UNIQUE("column_name")` - Check for unique values
- `IN_RANGE("column_name", min, max)` - Check values within range
- `MATCHES("column_name", "pattern")` - Check values match regex pattern
- `FK("column_name", "table", "column")` - Check foreign key constraints
- `CUSTOM_PYTHON(lambda df: ...)` - Custom Python validation functions

## Auto Rule Generation

When a dataset is uploaded, the system automatically analyzes the data and suggests rules:

- For columns with < 2% nulls: suggest NOT_NULL(column)
- For numeric columns with known ranges: suggest IN_RANGE(column, min, max)
- For columns with mostly unique values: suggest UNIQUE(column)
- For columns resembling foreign keys: suggest FK(...)

## Default Demo Credentials

- Username: `demo`
- Password: `demo12345`

## License

This project is licensed under the MIT License.