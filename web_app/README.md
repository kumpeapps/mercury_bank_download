# Mercury Bank Web Interface

A modern, responsive web application for managing Mercury Bank accounts and analyzing financial data with beautiful charts and reports.

## Features

- **🔐 User Authentication**: Secure login system with user registration
- **🏦 Multi-Account Management**: Connect and manage multiple Mercury Bank accounts
- **📊 Interactive Reports**: Beautiful charts showing spending patterns and budget analysis
- **💳 Transaction Management**: View, filter, and categorize transactions
- **📈 Month-over-Month Analysis**: Track budget trends by category over time
- **🎨 Modern UI**: Responsive design with Bootstrap 5 and Font Awesome icons
- **🐳 Docker Support**: Easy deployment with Docker and Docker Compose

## Screenshots

### Dashboard
- Overview of all accounts and recent transactions
- Quick stats on total balance and account counts
- Recent transaction history

### Reports
- Interactive budget trend charts (Month-over-Month)
- Expense breakdown pie charts
- Customizable time periods
- Category-based analysis using transaction notes

### Account Management
- Add new Mercury Bank accounts
- View account balances and details
- Transaction counts and activity tracking

## Quick Start with Docker

1. **Clone and navigate to the web app directory:**
   ```bash
   cd web_app
   ```

2. **Start the application:**
   ```bash
   docker-compose up -d
   ```

3. **Setup the database (first time only):**
   ```bash
   # Wait for containers to start, then run setup
   docker-compose exec web python setup.py
   ```

4. **Access the application:**
   - Web Interface: http://localhost:5000
   - Database Admin (Adminer): http://localhost:8080

## Manual Installation

### Prerequisites

- Python 3.11+
- MySQL 8.0+
- Git

### Installation Steps

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure database:**
   ```bash
   # Set environment variables
   export DATABASE_URL="mysql+pymysql://user:password@localhost:3306/mercury_bank"
   export SECRET_KEY="your-secret-key-here"
   ```

3. **Setup database:**
   ```bash
   python setup.py
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | MySQL connection string | `mysql+pymysql://mercury_user:mercury_password@db:3306/mercury_bank` |
| `SECRET_KEY` | Flask secret key for sessions | `your-secret-key-change-this` |
| `FLASK_ENV` | Flask environment | `production` |

### Database Schema

The web application uses the same database schema as the main Mercury Bank sync application, with additional user management tables:

- `users` - User accounts and authentication
- `user_mercury_accounts` - Many-to-many relationship between users and Mercury accounts
- `mercury_accounts` - Mercury Bank API connections
- `accounts` - Individual bank accounts
- `transactions` - Transaction records

## Usage

### Adding Mercury Accounts

1. Click "Add Mercury Account" from the dashboard or accounts page
2. Enter a friendly name for the account
3. Provide your Mercury API key (get this from Mercury dashboard → Settings → API)
4. Choose environment (Sandbox for testing, Production for live data)
5. Click "Add Account"

### Viewing Reports

1. Navigate to the Reports page
2. Choose time periods for budget analysis (6, 12, or 24 months)
3. Choose time periods for expense breakdown (1, 3, or 6 months)
4. Charts will automatically update based on your selections

### Transaction Categories

The application uses the `note` field of transactions as categories for reporting. To get meaningful reports:

1. Add descriptive notes to your transactions (e.g., "Office Supplies", "Marketing", "Travel")
2. Use consistent naming for better categorization
3. The reports will group expenses by these categories

## Security Features

- Password hashing with Werkzeug
- Session-based authentication with Flask-Login
- Encrypted API key storage
- CSRF protection
- Input validation and sanitization

## Development

### Project Structure

```
web_app/
├── app.py                 # Main Flask application
├── setup.py              # Database setup script
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container definition
├── docker-compose.yml    # Docker Compose configuration
└── templates/            # HTML templates
    ├── base.html         # Base template with navigation
    ├── index.html        # Landing page
    ├── login.html        # Login form
    ├── register.html     # Registration form
    ├── dashboard.html    # Main dashboard
    ├── accounts.html     # Account management
    ├── add_mercury_account.html
    ├── transactions.html # Transaction listing
    └── reports.html      # Charts and reports
```

### API Endpoints

- `GET /api/budget_data?months=12` - Budget trend data for charts
- `GET /api/expense_breakdown?months=3` - Expense breakdown data for pie charts

### Adding New Features

1. **New Routes**: Add routes to `app.py`
2. **Templates**: Create HTML templates in `templates/`
3. **Static Files**: Add CSS/JS to template `<style>` or `<script>` blocks
4. **Database Changes**: Update models and run migrations

## Troubleshooting

### Common Issues

1. **Database Connection Error:**
   ```
   Error: Can't connect to MySQL server
   ```
   - Check if MySQL is running
   - Verify DATABASE_URL environment variable
   - Ensure database exists and user has permissions

2. **Flask-Login Import Error:**
   ```
   ImportError: No module named 'flask_login'
   ```
   - Install requirements: `pip install -r requirements.txt`

3. **Permission Denied on Docker:**
   ```
   Permission denied: '/app/logs'
   ```
   - Check volume permissions in docker-compose.yml
   - Ensure logs directory exists and is writable

### Performance Optimization

- Enable query caching for large transaction datasets
- Implement pagination for transaction lists
- Use database indexes on frequently queried fields
- Consider Redis for session storage in production

## License

This project is licensed under the same license as the main Mercury Bank Download project.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the main project's README.md
3. Check Docker logs: `docker-compose logs`
4. Verify database connectivity and table creation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Note**: This web interface is an optional module for the Mercury Bank Download project. It provides a user-friendly way to manage accounts and view reports, but the core sync functionality works independently.
