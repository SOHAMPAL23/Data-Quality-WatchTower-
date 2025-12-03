# Data Quality Watchtower

A comprehensive data quality monitoring platform built with Django, Celery, and modern web technologies.

## 🚀 Features

- **Modern Authentication**: Vibrant UI with gradients, animations, and OAuth
- **Dataset Management**: Upload, profile, and monitor data quality
- **Rule Engine**: Create and execute custom data quality rules
- **Incident Tracking**: Track and manage data quality issues
- **Dashboard Analytics**: Real-time charts and metrics
- **Notification System**: Real-time and email alerts
- **Activity Logging**: Comprehensive audit trail
- **Rule Templates**: Predefined rule patterns for common use cases
- **Rule Execution Timeline**: Beautiful timeline UI for tracking executions
- **Dataset Profiling**: Automatic quality scoring and statistics
- **Industry Realistic Scheduling**: Rule execution only on weekdays (Mon-Fri), no weekends

## 🏗️ Architecture

```
DataQualityWatchtower/
├── apps/
│   ├── datasets/       # Dataset management
│   ├── rules/          # Rule engine and execution
│   ├── incidents/      # Incident tracking
│   ├── dashboard/      # Analytics dashboard
│   ├── api/           # REST API endpoints
│   ├── audit/         # Activity logging
│   ├── users/         # User management
│   └── notifications/ # Notification system
├── static/            # CSS, JS, images
├── templates/         # HTML templates
└── media/             # Uploaded files
```

## 🛠️ Technology Stack

- **Backend**: Django 4.2, Django REST Framework, Celery
- **Frontend**: Bootstrap 5, Chart.js, Modern CSS
- **Database**: SQLite (development), PostgreSQL (production)
- **Task Queue**: Celery with Redis/RabbitMQ
- **Data Processing**: Pandas, NumPy

## 📋 Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

## 🚀 Quick Start

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd DataQualityWatchtower
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
   python manage.py createsuperuser
   ```

6. Seed demo data:
   ```bash
   python manage.py seed_demo_data
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

## 📅 Industry Realistic Scheduling

To make the system more realistic for industry on-the-job learning (OJL), rule executions and automated tasks only run on weekdays (Monday through Friday), excluding weekends. This simulates real-world business environments where data processing typically occurs only during business days.

This restriction applies to:
- Scheduled rule executions
- SLA breach checks
- All automated Celery tasks
- Management commands

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/register/` - User registration

### Datasets
- `GET /api/datasets/` - List datasets
- `POST /api/datasets/` - Create dataset
- `GET /api/datasets/{id}/` - Get dataset details
- `PUT /api/datasets/{id}/` - Update dataset
- `DELETE /api/datasets/{id}/` - Delete dataset

### Rules
- `GET /api/rules/` - List rules
- `POST /api/rules/` - Create rule
- `GET /api/rules/{id}/` - Get rule details
- `PUT /api/rules/{id}/` - Update rule
- `DELETE /api/rules/{id}/` - Delete rule
- `POST /api/rules/{id}/run/` - Execute rule

### Incidents
- `GET /api/incidents/` - List incidents
- `POST /api/incidents/` - Create incident
- `GET /api/incidents/{id}/` - Get incident details
- `PUT /api/incidents/{id}/` - Update incident
- `DELETE /api/incidents/{id}/` - Delete incident

## 🎨 UI Components

### Authentication Pages
- Modern login with gradients and animations
- Register with password strength indicator
- OAuth integration (Google)

### Dashboard
- Dynamic charts using Chart.js
- Real-time stats cards with count-up animations
- Dark/light mode toggle
- Date range and dataset filters

### Dataset Management
- Dataset listing with search and pagination
- Enhanced upload with drag-and-drop
- Dataset profiling with quality scores
- Rule recommendations based on data patterns

### Rule Management
- Rule templates for common patterns
- Rule execution timeline
- Custom DSL rule creation
- Rule activation/deactivation

### Incident Management
- Severity levels (LOW, MEDIUM, HIGH, CRITICAL)
- Assignment to users
- Comment system
- Resolution tracking

## 📊 Data Quality Metrics

The platform calculates comprehensive quality scores based on:
- **Completeness**: Missing value percentage
- **Uniqueness**: Duplicate record detection
- **Consistency**: Data type adherence
- **Validity**: Schema validation
- **Accuracy**: Business rule compliance

## 🔧 Customization

### Rule DSL
The platform supports a custom DSL for rule creation:
- `NOT_NULL("column")` - Check for null values
- `UNIQUE("column")` - Check for unique values
- `IN_RANGE("column", min, max)` - Check value range
- `REGEX("column", "pattern")` - Pattern matching
- `CUSTOM_PYTHON("expression")` - Custom Python expressions

### Notification Preferences
Users can configure:
- Email notifications for different event types
- In-app notifications
- Notification frequency

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, please open an issue on the GitHub repository or contact the maintainers.