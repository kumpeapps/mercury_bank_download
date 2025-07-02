# Mercury Bank Web Interface - Complete Module

## Overview

This is a complete Docker-based web interface module for the Mercury Bank Download project. It provides a modern, user-friendly way to manage Mercury Bank accounts and visualize financial data with interactive charts and reports.

## What's Included

### 🚀 Quick Start
```bash
cd web_app
./start.sh
```
Then visit: http://localhost:5000

### 📁 Module Structure
```
web_app/
├── 🐳 Docker Configuration
│   ├── Dockerfile                    # Web app container
│   ├── docker-compose.yml           # Complete stack (web + database)
│   └── .env.example                 # Environment template
│
├── 🐍 Python Application
│   ├── app.py                       # Main Flask application
│   ├── setup.py                     # Database initialization
│   └── requirements.txt             # Python dependencies
│
├── 🎨 Web Templates
│   ├── base.html                    # Base layout with navigation
│   ├── index.html                   # Landing page
│   ├── login.html                   # User authentication
│   ├── register.html                # User registration
│   ├── dashboard.html               # Main dashboard
│   ├── accounts.html                # Account management
│   ├── add_mercury_account.html     # Add new accounts
│   ├── transactions.html            # Transaction listing
│   └── reports.html                 # Charts and analytics
│
└── 📚 Documentation
    ├── README.md                    # Detailed documentation
    └── start.sh                     # Easy startup script
```

## Key Features

### 🔐 User Management
- Secure registration and login system
- Multi-user support with role-based access
- Password hashing and session management
- Admin user creation during setup

### 🏦 Account Management
- Connect multiple Mercury Bank accounts
- Support for both sandbox and production environments
- Secure API key storage and encryption
- Account balance and status monitoring

### 📊 Financial Analytics
- **Budget Trends**: Month-over-month spending analysis by category
- **Expense Breakdown**: Interactive pie charts showing spending distribution
- **Transaction Categorization**: Uses transaction notes as categories
- **Customizable Time Periods**: 1-24 months of historical analysis

### 💳 Transaction Management
- Advanced filtering by account and category
- Pagination for large transaction sets
- Real-time transaction status monitoring
- Detailed transaction information display

### 🎨 Modern UI/UX
- Responsive Bootstrap 5 design
- Interactive Chart.js visualizations
- Font Awesome icons throughout
- Mobile-friendly interface
- Dark/light theme support

## Technical Stack

### Backend
- **Flask 2.3+**: Web framework
- **SQLAlchemy**: Database ORM
- **Flask-Login**: User session management
- **Werkzeug**: Password hashing
- **PyMySQL**: MySQL database connector

### Frontend
- **Bootstrap 5**: CSS framework
- **Chart.js**: Interactive charts
- **Font Awesome**: Icon library
- **Vanilla JavaScript**: Client-side interactions

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **MySQL 8.0**: Database
- **Adminer**: Database administration interface

## Security Features

### Authentication & Authorization
- Secure password hashing with Werkzeug
- Session-based authentication with Flask-Login
- CSRF protection on all forms
- Input validation and sanitization

### Data Protection
- Encrypted API key storage
- Secure database connections
- Environment-based configuration
- Non-root container execution

## API Endpoints

### Web Routes
- `GET /` - Landing page
- `GET|POST /login` - User authentication
- `GET|POST /register` - User registration
- `GET /dashboard` - Main dashboard
- `GET /accounts` - Account management
- `GET|POST /add_mercury_account` - Add new Mercury accounts
- `GET /transactions` - Transaction listing with filters
- `GET /reports` - Analytics and charts

### API Routes
- `GET /api/budget_data?months=N` - Budget trend data for charts
- `GET /api/expense_breakdown?months=N` - Expense distribution data

## Database Integration

### Existing Schema Compatibility
The web interface uses the existing Mercury Bank Download database schema:
- `users` - Web interface user accounts
- `user_mercury_accounts` - User-to-account relationships
- `mercury_accounts` - Mercury API connections
- `accounts` - Individual bank accounts
- `transactions` - Transaction records

### No Data Duplication
The web interface reads from the same database used by the sync process, ensuring:
- Real-time data access
- No synchronization issues
- Consistent reporting
- Efficient storage usage

## Deployment Options

### 🐳 Docker (Recommended)
```bash
cd web_app
./start.sh
```
- Complete stack with MySQL database
- Automatic setup and initialization
- Includes database admin interface
- Production-ready configuration

### 🔧 Manual Installation
```bash
pip install -r requirements.txt
export DATABASE_URL="mysql+pymysql://user:pass@host:3306/db"
python setup.py
python app.py
```

## Configuration

### Environment Variables
- `DATABASE_URL` - MySQL connection string
- `SECRET_KEY` - Flask session secret
- `FLASK_ENV` - Development/production mode

### Customization
- Modify templates in `templates/` directory
- Update styling in template `<style>` blocks
- Add new routes in `app.py`
- Extend database models as needed

## Integration with Main Project

### Shared Database
The web interface connects to the same MySQL database used by the main sync application, allowing:
- Immediate access to synced transaction data
- Real-time balance updates
- Consistent categorization across systems

### Independent Operation
- Web interface runs independently of sync process
- Can be deployed on different servers
- Separate container for isolation
- Optional component - main sync works without it

## Maintenance & Monitoring

### Logging
- Application logs in `logs/` directory
- Docker container logs via `docker-compose logs`
- Error tracking and debugging information

### Health Monitoring
- Built-in health check endpoint
- Database connection monitoring
- Container health checks in Docker Compose

### Updates
- Update Python dependencies in `requirements.txt`
- Rebuild containers: `docker-compose up --build`
- Database migrations handled automatically

## Use Cases

### Personal Finance Management
- Individual users tracking personal Mercury accounts
- Budget analysis and spending pattern identification
- Expense categorization and reporting

### Business Financial Dashboards
- Multiple team members accessing business accounts
- Department-based spending analysis
- Monthly financial reporting and budgeting

### Multi-Account Management
- Businesses with multiple Mercury accounts
- Consolidated view across all accounts
- Cross-account transaction analysis

## Getting Started Checklist

1. **Prerequisites Check**
   - [ ] Docker and Docker Compose installed
   - [ ] Mercury Bank API access
   - [ ] Port 5000 available

2. **Initial Setup**
   - [ ] Clone/download the web_app directory
   - [ ] Run `./start.sh` to start the application
   - [ ] Create admin user during setup
   - [ ] Access web interface at http://localhost:5000

3. **Connect Mercury Accounts**
   - [ ] Log in with admin credentials
   - [ ] Click "Add Mercury Account"
   - [ ] Enter API key and account details
   - [ ] Verify connection and account data

4. **Configure Categories**
   - [ ] Review existing transaction notes
   - [ ] Update transaction notes for better categorization
   - [ ] View reports to verify category breakdown

5. **Explore Features**
   - [ ] Dashboard overview and statistics
   - [ ] Account management and balances
   - [ ] Transaction filtering and search
   - [ ] Interactive reports and charts

---

**Note**: This web interface is designed as an optional enhancement to the Mercury Bank Download project. The core synchronization functionality operates independently, and this module provides a user-friendly way to interact with the collected data.
