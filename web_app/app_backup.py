"""
Mercury Bank Web Interface
A Flask-based web application for managing Mercury Bank accounts and viewing financial data.
"""

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    make_response,
    g,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import create_engine, func, extract, text
from sqlalchemy.orm import sessionmaker, joinedload
from datetime import datetime, timedelta
from functools import wraps
import os
import json
import csv
import io
import logging
import hashlib
from collections import defaultdict
from functools import wraps

# Import models
from models.user import User
from models.user_settings import UserSettings
from models.mercury_account import MercuryAccount
from models.account import Account
from models.transaction import Transaction
from models.transaction_attachment import TransactionAttachment
from models.system_setting import SystemSetting
from models.base import Base

# Sub-category helper functions
def parse_category(category_string):
    """
    Parse a category string into main category and sub-category.
    
    Args:
        category_string (str): Category string, potentially with sub-category (e.g., "Office/Supplies")
    
    Returns:
        tuple: (main_category, sub_category) or (category, None) if no sub-category
    """
    if not category_string:
        return (None, None)
    
    if '/' in category_string:
        parts = category_string.split('/', 1)  # Split on first '/' only
        return (parts[0].strip(), parts[1].strip())
    else:
        return (category_string.strip(), None)

def get_unique_categories_and_subcategories(db_session, account_ids):
    """
    Get all unique categories and sub-categories from transactions.
    
    Returns:
        dict: {
            'categories': ['Office', 'Travel', ...],
            'subcategories': {
                'Office': ['Supplies', 'Equipment'],
                'Travel': ['Flights', 'Hotels']
            },
            'all_combinations': ['Office', 'Office/Supplies', 'Travel', ...]
        }
    """
    if not account_ids:
        return {'categories': [], 'subcategories': {}, 'all_combinations': []}
    
    # Get all category strings from transactions
    category_results = (
        db_session.query(Transaction.note)
        .filter(Transaction.account_id.in_(account_ids))
        .filter(Transaction.note.isnot(None))
        .distinct()
        .all()
    )
    
    category_strings = [cat[0] for cat in category_results if cat[0]]
    
    categories = set()
    subcategories = defaultdict(set)
    all_combinations = set()
    
    for category_string in category_strings:
        main_cat, sub_cat = parse_category(category_string)
        if main_cat:
            categories.add(main_cat)
            all_combinations.add(main_cat)
            
            if sub_cat:
                subcategories[main_cat].add(sub_cat)
                all_combinations.add(category_string)
    
    # Convert to sorted lists
    sorted_categories = sorted(categories)
    sorted_subcategories = {
        cat: sorted(list(subs)) for cat, subs in subcategories.items()
    }
    sorted_all_combinations = sorted(all_combinations)
    
    return {
        'categories': sorted_categories,
        'subcategories': sorted_subcategories,
        'all_combinations': sorted_all_combinations
    }

def format_category_display(category_string):
    """
    Format a category string for display, highlighting sub-categories.
    
    Args:
        category_string (str): Category string
    
    Returns:
        str: Formatted display string
    """
    if not category_string:
        return "Uncategorized"
    
    main_cat, sub_cat = parse_category(category_string)
    if sub_cat:
        return f"{main_cat} → {sub_cat}"
    else:
        return main_cat

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-change-this")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "mysql+pymysql://user:password@db:3306/mercury_bank"
)
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


# Define system settings initialization function
def initialize_system_settings():
    """Initialize default system settings if they don't exist."""
    db_session = Session()
    try:
        # Check if users are externally managed
        users_externally_managed = (
            os.environ.get("USERS_EXTERNALLY_MANAGED", "false").lower() == "true"
        )

        print(
            f"🔒 USERS_EXTERNALLY_MANAGED environment variable is set to: {users_externally_managed}"
        )

        # Check if users table is a view to set default signup behavior
        try:
            result = db_session.execute(
                text(
                    """
                SELECT TABLE_TYPE 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'users'
            """
                )
            ).fetchone()

            default_signup_enabled = result[0] != "VIEW" if result else True
        except Exception:
            default_signup_enabled = True

        # If users are externally managed, override these settings
        if users_externally_managed:
            print("🔒 Users are externally managed - locking user management settings")
            default_signup_enabled = False
            prevent_deletion = True
            settings_editable = False
        else:
            prevent_deletion = False
            settings_editable = True

        # Initialize default settings
        settings_to_create = [
            (
                "registration_enabled",
                str(default_signup_enabled).lower(),
                "Whether new user registration is enabled",
                settings_editable,
            ),
            (
                "prevent_user_deletion",
                str(prevent_deletion).lower(),
                "Prevent administrators from deleting user accounts",
                settings_editable,
            ),
            (
                "users_externally_managed",
                str(users_externally_managed).lower(),
                "Users are managed by an external system (locks user management settings)",
                False,  # This setting itself is never editable via UI
            ),
            # Branding settings
            (
                "app_name",
                "Mercury Bank Integration",
                "The name of the application displayed in the header and page titles",
                True,
            ),
            (
                "app_description",
                "Mercury Bank data synchronization and management platform",
                "Description of the application displayed on the login page and dashboard",
                True,
            ),
            (
                "logo_url",
                "",
                "URL to the application logo image (leave empty for default logo)",
                True,
            ),
        ]

        for key, value, description, is_editable in settings_to_create:
            existing = db_session.query(SystemSetting).filter_by(key=key).first()
            if not existing:
                setting = SystemSetting(
                    key=key,
                    value=value,
                    description=description,
                    is_editable=is_editable,
                )
                db_session.add(setting)
                print(f"✅ Created system setting: {key} = {value}")
            elif key == "users_externally_managed":
                # Always update the external management setting to match environment variable
                existing.value = value
                print(f"✅ Updated users_externally_managed setting to: {value}")

        # Apply fallback logic: if no admin users exist, enable registration regardless of settings
        from models.role import Role

        admin_count = (
            db_session.query(User)
            .filter(User.roles.any(Role.name.in_(["admin", "super-admin"])))
            .count()
        )

        print(f"🔍 Admin user count: {admin_count}")

        if admin_count == 0:
            # No admins exist - force enable registration as a safety fallback
            registration_setting = (
                db_session.query(SystemSetting)
                .filter_by(key="registration_enabled")
                .first()
            )
            if registration_setting:
                current_value = registration_setting.value
                print(f"🔍 Current registration_enabled value: {current_value}")
                if current_value == "false":
                    registration_setting.value = "true"
                    print(
                        "🚨 No admin users found - enabling registration as safety fallback"
                    )
                else:
                    print("ℹ️  Registration already enabled - no fallback action needed")
            else:
                print("⚠️  registration_enabled setting not found")
        else:
            print(f"ℹ️  Found {admin_count} admin user(s) - no fallback needed")

        db_session.commit()
    except Exception as e:
        print(f"Warning: Could not initialize system settings: {e}")
        db_session.rollback()
    finally:
        db_session.close()


# Database initialization is handled by initial_setup.py during container startup
# This ensures the schema is ready before the Flask app starts
print("ℹ️  Database initialization is handled by initial_setup.py during startup")

# Initialize system settings in case they weren't created during setup
try:
    initialize_system_settings()
    print("✅ System settings verified")
except Exception as e:
    print(f"⚠️  Warning: Could not verify system settings: {e}")

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    db_session = Session()
    try:
        # Eagerly load the user and roles to avoid DetachedInstanceError
        user = (
            db_session.query(User)
            .options(joinedload(User.roles))
            .filter(User.id == int(user_id))
            .first()
        )
        if user:
            # Make the user object detached from this session to avoid conflicts
            db_session.expunge(user)
        return user
    except Exception as e:
        print(f"Error loading user {user_id}: {e}")
        return None
    finally:
        db_session.close()


@app.before_request
def check_user_permissions():
    """
    Check if the current user still has valid permissions on every request.
    If a logged-in user loses the 'user' role or gains the 'locked' role,
    they will be automatically logged out.
    """
    # Skip permission checks for certain routes
    skip_routes = ["login", "register", "static", "logout", "health", "index"]

    # Check if we're accessing a route that should be skipped
    if request.endpoint in skip_routes:
        return

    # Only check permissions if user is logged in
    if current_user.is_authenticated:
        db_session = Session()
        try:
            # Re-query the user to get fresh data from the database
            fresh_user = db_session.query(User).get(current_user.id)

            if fresh_user:
                # Check if user has been locked
                if fresh_user.has_role("locked"):
                    logger.info(
                        f"User {fresh_user.username} has been locked - logging out"
                    )
                    logout_user()
                    flash(
                        "Your account has been locked. Please contact an administrator.",
                        "error",
                    )
                    return redirect(url_for("login"))

                # Check if user no longer has the user role
                if not fresh_user.has_role("user"):
                    logger.info(
                        f"User {fresh_user.username} no longer has 'user' role - logging out"
                    )
                    logout_user()
                    flash(
                        "Your account permissions have changed. Please contact an administrator.",
                        "error",
                    )
                    return redirect(url_for("login"))

            else:
                # User not found in database - log them out
                logger.info(
                    f"User {current_user.id} not found in database - logging out"
                )
                logout_user()
                flash(
                    "Your account could not be found. Please contact an administrator.",
                    "error",
                )
                return redirect(url_for("login"))

        except Exception as e:
            logger.error(f"Error checking user permissions: {e}")
            # In case of database errors, don't log out the user unless it's critical
            pass
        finally:
            db_session.close()


# Helper functions for account access control
def get_user_accessible_accounts(user_in_session, db_session, mercury_account_id=None):
    """
    Get all accounts that a user has access to, respecting account-level restrictions.

    Args:
        user_in_session: User object bound to the current session
        db_session: SQLAlchemy session
        mercury_account_id: Optional - filter by specific mercury account

    Returns:
        list: List of Account objects the user can access
    """
    # Use the user model's helper method
    accessible_accounts = user_in_session.get_accessible_accounts(db_session)

    # Filter by mercury account if specified
    if mercury_account_id:
        accessible_accounts = [
            account
            for account in accessible_accounts
            if account.mercury_account_id == mercury_account_id
        ]

    return accessible_accounts


def get_user_accessible_accounts_for_reports(
    user_in_session, db_session, mercury_account_id=None
):
    """
    Get all accounts that a user has access to for reports, excluding accounts marked as exclude_from_reports.

    Args:
        user_in_session: User object bound to the current session
        db_session: SQLAlchemy session
        mercury_account_id: Optional - filter by specific mercury account

    Returns:
        list: List of Account objects the user can access for reports
    """
    # Get all accessible accounts first
    accessible_accounts = get_user_accessible_accounts(
        user_in_session, db_session, mercury_account_id
    )

    # Filter out accounts that are excluded from reports
    report_accounts = [
        account for account in accessible_accounts if not account.exclude_from_reports
    ]

    return report_accounts


# Helper functions
def is_signup_enabled():
    """Check if user registration is enabled."""
    # First check environment variable directly to ensure we honor it
    users_externally_managed = (
        os.environ.get("USERS_EXTERNALLY_MANAGED", "false").lower() == "true"
    )
    if users_externally_managed:
        return False

    db_session = Session()
    try:
        # Also check system setting for externally managed users
        if SystemSetting.get_bool_value(
            db_session, "users_externally_managed", default=False
        ):
            return False

        # Check if users table is a view (MySQL specific check)
        result = db_session.execute(
            text(
                """
            SELECT TABLE_TYPE 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'users'
        """
            )
        ).fetchone()

        # If users table is a view, disable signups
        if result and result[0] == "VIEW":
            return False

        # Check system setting for signup control
        return SystemSetting.get_bool_value(
            db_session, "registration_enabled", default=True
        )
    except Exception:
        # Default to enabled if we can't check (for backwards compatibility)
        return True
    finally:
        db_session.close()


def get_gravatar_url(email, size=40, default="identicon"):
    """Generate a Gravatar URL for the given email address."""
    if not email:
        email = ""

    # Create the hash
    email_hash = hashlib.md5(email.lower().encode("utf-8")).hexdigest()

    # Build the URL
    gravatar_url = f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d={default}"

    return gravatar_url


# Template context processor to avoid DetachedInstanceError
@app.context_processor
def inject_user():
    """Inject a session-bound user object for template use."""
    if current_user.is_authenticated:
        db_session = Session()
        try:
            # Get a fresh copy of the user with all attributes loaded
            user = db_session.query(User).filter_by(id=current_user.id).first()
            if user:
                # Force load any lazy attributes we might need in templates
                _ = user.username  # This should load the attribute
                # Store the session in Flask's g object for cleanup
                g.template_db_session = db_session
                return dict(template_user=user)
        except Exception as e:
            print(f"Error in context processor: {e}")
            db_session.close()
            return dict(template_user=current_user)
        # Return the session-bound user
        return dict(template_user=user)
    return dict(template_user=None)


@app.context_processor
def inject_branding():
    """Inject branding settings for template use."""
    try:
        db_session = Session()
        app_name = SystemSetting.get_value(
            db_session, "app_name", "Mercury Bank Integration"
        )
        app_description = SystemSetting.get_value(
            db_session,
            "app_description",
            "Mercury Bank data synchronization and management platform",
        )
        logo_url = SystemSetting.get_value(db_session, "logo_url", "")
        db_session.close()

        return dict(
            app_name=app_name, app_description=app_description, logo_url=logo_url
        )
    except Exception as e:
        print(f"Error getting branding settings: {e}")
        return dict(
            app_name="Mercury Bank Integration",
            app_description="Mercury Bank data synchronization and management platform",
            logo_url="",
        )


# Register template filters
@app.template_filter("gravatar")
def gravatar_filter(email, size=40):
    """Template filter for generating Gravatar URLs."""
    return get_gravatar_url(email, size)


@app.teardown_appcontext
def close_template_db_session(error):
    """Close any database sessions opened by the context processor."""
    db_session = getattr(g, "template_db_session", None)
    if db_session:
        db_session.close()


# Export helper functions
def export_transactions(transactions, format_type, accounts):
    """Export transactions to CSV or Excel format"""
    # Create account lookup for faster access
    account_lookup = {acc.id: acc for acc in accounts}

    # Prepare data
    data = []
    for transaction in transactions:
        account = account_lookup.get(transaction.account_id)
        effective_date = transaction.posted_at or transaction.created_at

        # Get receipt status if account is available
        receipt_status = ""
        if account:
            status = account.get_receipt_status_for_transaction(
                transaction.amount, transaction.number_of_attachments > 0, transaction.posted_at
            )
            receipt_status_map = {
                "required_present": "Required (Present)",
                "required_missing": "Required (Missing)",
                "optional_present": "Optional (Present)",
                "optional_missing": "Optional (Not Present)",
            }
            receipt_status = receipt_status_map.get(status, "Unknown")

        data.append(
            {
                "Date": (
                    effective_date.strftime("%Y-%m-%d %H:%M:%S")
                    if effective_date
                    else ""
                ),
                "Account": account.nickname or account.name if account else "",
                "Description": transaction.description or "",
                "Bank Description": transaction.bank_description or "",
                "Category": transaction.note or "",
                "Type": transaction.transaction_type or "",
                "Kind": transaction.kind or "",
                "Amount": transaction.amount,
                "Currency": transaction.currency or "USD",
                "Status": transaction.status or "",
                "Counterparty": transaction.counterparty_name or "",
                "Reference": transaction.reference_number or "",
                "Posted At": (
                    transaction.posted_at.strftime("%Y-%m-%d %H:%M:%S")
                    if transaction.posted_at
                    else ""
                ),
                "Created At": (
                    transaction.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    if transaction.created_at
                    else ""
                ),
                "Has Attachments": (
                    "Yes" if transaction.number_of_attachments > 0 else "No"
                ),
                "Number of Attachments": transaction.number_of_attachments,
                "Receipt Status": receipt_status,
            }
        )

    if format_type == "csv":
        return export_csv(data, "transactions")
    elif format_type == "excel":
        return export_excel(data, "transactions")


def export_csv(data, filename):
    """Export data to CSV format"""
    if not data:
        return make_response("No data to export", 400)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{filename}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    )
    return response


def export_excel(data, filename):
    """Export data to Excel format (requires openpyxl)"""
    try:
        import pandas as pd

        if not data:
            return make_response("No data to export", 400)

        df = pd.DataFrame(data)
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Transactions", index=False)

        output.seek(0)
        response = make_response(output.getvalue())
        response.headers["Content-Type"] = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response.headers["Content-Disposition"] = (
            f'attachment; filename="{filename}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        )
        return response

    except ImportError:
        # Fallback to CSV if pandas/openpyxl not available
        return export_csv(data, filename)


def get_reports_table_data(
    db_session,
    mercury_account_id=None,
    month_filter=None,
    account_id=None,
    category=None,
    expanded_status_filter=None,
):
    """Get aggregated category data for reports table view"""
    # Get user's accessible Mercury accounts
    mercury_accounts = (
        db_session.query(MercuryAccount)
        .filter(MercuryAccount.users.contains(current_user))
        .all()
    )

    # Filter by specific Mercury account if selected
    if mercury_account_id:
        mercury_accounts = [
            ma for ma in mercury_accounts if ma.id == mercury_account_id
        ]

    account_ids = []
    account_lookup = {}
    for mercury_account in mercury_accounts:
        accounts = (
            db_session.query(Account)
            .filter_by(mercury_account_id=mercury_account.id)
            .filter_by(
                exclude_from_reports=False
            )  # Exclude accounts marked as exclude_from_reports
            .all()
        )
        for account in accounts:
            account_ids.append(account.id)
            account_lookup[account.id] = account

    # Build query for aggregation
    category_field = func.coalesce(Transaction.note, "Uncategorized")
    query = db_session.query(
        category_field.label("category"),
        func.sum(Transaction.amount).label("total_amount"),
        func.count(Transaction.id).label("transaction_count"),
    ).filter(Transaction.account_id.in_(account_ids))

    # Add account filter
    if account_id:
        query = query.filter_by(account_id=account_id)

    # Add category filter
    if category:
        query = query.filter(Transaction.note.ilike(f"%{category}%"))

    # Add status filter
    if expanded_status_filter:
        query = query.filter(Transaction.status.in_(expanded_status_filter))

    # Add month filter
    if month_filter:
        try:
            year, month = map(int, month_filter.split("-"))
            from sqlalchemy import and_, extract

            effective_date = func.coalesce(
                Transaction.posted_at, Transaction.created_at
            )
            query = query.filter(
                and_(
                    extract("year", effective_date) == year,
                    extract("month", effective_date) == month,
                )
            )
        except (ValueError, AttributeError):
            pass

    # Group by category and order by total amount (highest first)
    category_totals = (
        query.group_by(category_field)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    # Format data for table
    table_data = []
    for category_data in category_totals:
        formatted_category = format_category_display(category_data.category)
        table_data.append(
            {
                "category": category_data.category,
                "category_display": formatted_category,
                "total_amount": category_data.total_amount,
                "transaction_count": category_data.transaction_count,
                "average_amount": (
                    category_data.total_amount / category_data.transaction_count
                    if category_data.transaction_count > 0
                    else 0
                ),
            }
        )

    return table_data


def export_reports_data(table_data, format_type):
    """Export reports table data to CSV or Excel"""
    if not table_data:
        return make_response("No data to export", 400)

    # Convert to export format
    export_data = []
    for row in table_data:
        export_data.append(
            {
                "Category": row.get("category_display", row["category"]),
                "Total Amount": row["total_amount"],
                "Transaction Count": row["transaction_count"],
                "Average Amount": round(row["average_amount"], 2),
            }
        )

    if format_type == "csv":
        return export_csv(export_data, "category_reports")
    elif format_type == "excel":
        return export_excel(export_data, "category_reports")


# Decorators
def transactions_required(f):
    """Decorator to require transactions access for a route."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user from database to avoid DetachedInstanceError
        db_session = Session()
        try:
            user = db_session.query(User).get(current_user.id)
            if not user or not user.can_access_transactions():
                flash(
                    "Access denied. You don't have permission to view transactions.",
                    "error",
                )
                return redirect(url_for("dashboard"))
        finally:
            db_session.close()
        return f(*args, **kwargs)

    return decorated_function


def reports_required(f):
    """Decorator to require reports access for a route."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user from database to avoid DetachedInstanceError
        db_session = Session()
        try:
            user = db_session.query(User).get(current_user.id)
            if not user or not user.can_access_reports():
                flash(
                    "Access denied. You don't have permission to view reports.", "error"
                )
                return redirect(url_for("dashboard"))
        finally:
            db_session.close()
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Decorator to require admin access for a route."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user from database to avoid DetachedInstanceError
        db_session = Session()
        try:
            user = db_session.query(User).get(current_user.id)
            if not user or (
                not user.has_role("admin") and not user.has_role("super-admin")
            ):
                flash("Access denied. Admin privileges required.", "error")
                return redirect(url_for("dashboard"))
        finally:
            db_session.close()
        return f(*args, **kwargs)

    return decorated_function


def super_admin_required(f):
    """Decorator to require super admin access for a route."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user from database to avoid DetachedInstanceError
        db_session = Session()
        try:
            user = db_session.query(User).get(current_user.id)
            if not user or not user.is_super_admin:
                flash("Access denied. Super admin privileges required.", "error")
                return redirect(url_for("dashboard"))
        finally:
            db_session.close()
        return f(*args, **kwargs)

    return decorated_function


# Routes
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db_session = Session()
        try:
            user = db_session.query(User).filter_by(username=username).first()

            if user and user.check_password(password):
                # Check if user has the locked role
                if user.has_role("locked"):
                    flash(
                        "Your account has been locked. Please contact an administrator.",
                        "error",
                    )
                    return render_template(
                        "login.html",
                        signup_enabled=is_signup_enabled(),
                        users_externally_managed=os.environ.get(
                            "USERS_EXTERNALLY_MANAGED", "false"
                        ).lower()
                        == "true",
                    )

                # Check if user has the user role (required for basic access)
                if not user.has_role("user"):
                    flash(
                        "Your account does not have the required permissions. Please contact an administrator.",
                        "error",
                    )
                    return render_template(
                        "login.html",
                        signup_enabled=is_signup_enabled(),
                        users_externally_managed=os.environ.get(
                            "USERS_EXTERNALLY_MANAGED", "false"
                        ).lower()
                        == "true",
                    )

                login_user(user)
                flash("Logged in successfully!", "success")
                return redirect(url_for("dashboard"))
            else:
                if user and not user.has_valid_password():
                    flash(
                        "Account needs password reset. Please contact administrator.",
                        "error",
                    )
                else:
                    flash("Invalid username or password", "error")
        finally:
            db_session.close()

    # Check if users are externally managed (directly from env var)
    users_externally_managed = (
        os.environ.get("USERS_EXTERNALLY_MANAGED", "false").lower() == "true"
    )

    return render_template(
        "login.html",
        signup_enabled=is_signup_enabled(),
        users_externally_managed=users_externally_managed,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    # First check environment variable directly
    users_externally_managed = (
        os.environ.get("USERS_EXTERNALLY_MANAGED", "false").lower() == "true"
    )
    if users_externally_managed:
        flash(
            "User registration is disabled because users are externally managed.",
            "error",
        )
        return redirect(url_for("login"))

    # Check if registration is enabled via function (which checks both env var and DB settings)
    if not is_signup_enabled():
        flash("User registration is currently disabled.", "error")
        return redirect(url_for("login"))

    # Double-check if users are externally managed (for security)
    db_session = Session()
    try:
        if SystemSetting.get_bool_value(
            db_session, "users_externally_managed", default=False
        ):
            flash(
                "User registration is disabled because users are externally managed.",
                "error",
            )
            return redirect(url_for("login"))
    finally:
        db_session.close()

    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        db_session = Session()
        try:
            # Check if user already exists
            existing_user = db_session.query(User).filter_by(username=username).first()
            if existing_user:
                flash("Username already exists", "error")
                return render_template("register.html")

            # Check if this is the first user (should be admin)
            user_count = db_session.query(User).count()
            is_first_user = user_count == 0

            # Create new user
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db_session.add(new_user)
            db_session.flush()  # Flush to get the user ID

            # Assign roles to the new user
            try:
                from models.role import Role

                # All users get the basic "user" role
                user_role = Role.get_or_create(
                    db_session,
                    "user",
                    "Basic user with read access to their own data",
                    is_system_role=True,
                )
                new_user.roles.append(user_role)

                # If this is the first user, also grant admin and super-admin roles
                if is_first_user:
                    admin_role = Role.get_or_create(
                        db_session,
                        "admin",
                        "Administrator with full system access",
                        is_system_role=True,
                    )
                    super_admin_role = Role.get_or_create(
                        db_session,
                        "super-admin",
                        "Super administrator with all privileges including user management",
                        is_system_role=True,
                    )
                    new_user.roles.append(admin_role)
                    new_user.roles.append(super_admin_role)

            except Exception as role_error:
                print(f"🚨 ERROR during role assignment: {role_error}")
                import traceback

                print(f"🚨 Full traceback: {traceback.format_exc()}")
                # Continue with user creation but without roles
                flash(
                    f"User created but role assignment failed: {role_error}", "warning"
                )

            # Create user settings
            try:
                from models.user_settings import UserSettings

                user_settings = UserSettings(user_id=new_user.id)
                db_session.add(user_settings)
                db_session.commit()
            except Exception as settings_error:
                print(f"🚨 ERROR during user settings creation: {settings_error}")
                import traceback

                print(f"🚨 Full traceback: {traceback.format_exc()}")
                db_session.rollback()
                flash(f"User creation failed: {settings_error}", "error")
                return render_template("register.html")

            if is_first_user:
                flash(
                    "Registration successful! You have been granted admin privileges as the first user. Please log in.",
                    "success",
                )
            else:
                flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        finally:
            db_session.close()

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    db_session = Session()
    try:
        # Get current user from this session to avoid DetachedInstanceError
        current_user_id = current_user.id
        user = db_session.query(User).get(current_user_id)
        if not user:
            flash("User not found", "error")
            return redirect(url_for("login"))

        # Get user's Mercury accounts
        all_mercury_accounts = (
            db_session.query(MercuryAccount)
            .filter(MercuryAccount.users.contains(user))
            .all()
        )

        # Get or create user settings
        user_settings = (
            db_session.query(UserSettings).filter_by(user_id=current_user_id).first()
        )
        if not user_settings:
            user_settings = UserSettings(user_id=current_user_id)
            db_session.add(user_settings)
            db_session.commit()

        # If user has a primary Mercury account, filter to that account by default
        # unless they specifically request to see all accounts
        show_all = request.args.get("show_all", "0") == "1"

        if user_settings.primary_mercury_account_id and not show_all:
            mercury_accounts = [
                ma
                for ma in all_mercury_accounts
                if ma.id == user_settings.primary_mercury_account_id
            ]
            # Fallback to all accounts if primary account is not accessible
            if not mercury_accounts:
                mercury_accounts = all_mercury_accounts
        else:
            mercury_accounts = all_mercury_accounts

        # Get summary statistics
        total_accounts = 0
        total_balance = 0
        recent_transactions = []

        # Get accessible accounts for this user (respects account restrictions)
        accessible_accounts = get_user_accessible_accounts(user, db_session)

        # If user has a primary account set, filter to just that account (unless showing all)
        if user_settings.primary_account_id and not show_all:
            primary_account = next(
                (
                    acc
                    for acc in accessible_accounts
                    if acc.id == user_settings.primary_account_id
                ),
                None,
            )
            if primary_account:
                accessible_accounts = [primary_account]

        # Filter accessible accounts to match the selected mercury account(s)
        for mercury_account in mercury_accounts:
            mercury_account_accessible_accounts = [
                account
                for account in accessible_accounts
                if account.mercury_account_id == mercury_account.id
            ]
            total_accounts += len(mercury_account_accessible_accounts)

            for account in mercury_account_accessible_accounts:
                if account.balance:
                    total_balance += account.balance

                # Get recent transactions
                from sqlalchemy import case, desc, asc

                effective_date = case(
                    (Transaction.posted_at.isnot(None), Transaction.posted_at),
                    else_=Transaction.created_at,
                )
                transactions = (
                    db_session.query(Transaction)
                    .filter_by(account_id=account.id)
                    .order_by(
                        # Pending transactions first, then by effective date
                        asc(Transaction.posted_at.isnot(None)),
                        desc(effective_date),
                    )
                    .limit(5)
                    .all()
                )
                recent_transactions.extend(transactions)

        # Sort recent transactions by effective date (posted_at or created_at)
        recent_transactions.sort(
            key=lambda x: x.posted_at or x.created_at, reverse=True
        )
        recent_transactions = recent_transactions[:10]

        return render_template(
            "dashboard.html",
            mercury_accounts=mercury_accounts,
            all_mercury_accounts=all_mercury_accounts,
            show_all=show_all,
            has_primary_account=user_settings.primary_mercury_account_id is not None,
            has_primary_specific_account=user_settings.primary_account_id is not None,
            total_accounts=total_accounts,
            total_balance=total_balance,
            recent_transactions=recent_transactions,
        )
    finally:
        db_session.close()


@app.route("/accounts")
@login_required
def accounts():
    db_session = Session()
    try:
        user = get_current_user_in_session(db_session)
        if not user:
            flash("User not found", "error")
            return redirect(url_for("login"))

        mercury_accounts = (
            db_session.query(MercuryAccount)
            .filter(MercuryAccount.users.contains(user))
            .all()
        )

        accounts_data = []

        # Get accessible accounts for this user (respects account restrictions)
        accessible_accounts = get_user_accessible_accounts(user, db_session)

        for mercury_account in mercury_accounts:
            # Filter accessible accounts for this mercury account
            mercury_account_accessible_accounts = [
                account
                for account in accessible_accounts
                if account.mercury_account_id == mercury_account.id
            ]

            for account in mercury_account_accessible_accounts:
                transaction_count = (
                    db_session.query(Transaction)
                    .filter_by(account_id=account.id)
                    .count()
                )
                accounts_data.append(
                    {
                        "account": account,
                        "mercury_account": mercury_account,
                        "transaction_count": transaction_count,
                    }
                )

        return render_template(
            "accounts.html",
            accounts_data=accounts_data,
            mercury_accounts=mercury_accounts,
        )
    finally:
        db_session.close()


@app.route("/add_mercury_account", methods=["GET", "POST"])
@login_required
@admin_required
def add_mercury_account():
    if request.method == "POST":
        name = request.form["name"]
        api_key = request.form["api_key"]
        environment = request.form.get("environment", "sandbox")

        db_session = Session()
        try:
            user = get_current_user_in_session(db_session)
            if not user:
                flash("User not found", "error")
                return redirect(url_for("login"))

            # Create new Mercury account
            mercury_account = MercuryAccount(
                name=name, api_key=api_key, sandbox_mode=(environment == "sandbox")
            )
            mercury_account.users.append(user)

            db_session.add(mercury_account)
            db_session.commit()

            flash("Mercury account added successfully!", "success")
            return redirect(url_for("accounts"))
        finally:
            db_session.close()

    return render_template("add_mercury_account.html")


@app.route("/edit_mercury_account/<int:account_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_mercury_account(account_id):
    db_session = Session()
    try:
        user = get_current_user_in_session(db_session)
        if not user:
            flash("User not found", "error")
            return redirect(url_for("login"))

        # Get the Mercury account and ensure user has access
        mercury_account = (
            db_session.query(MercuryAccount)
            .filter(
                MercuryAccount.id == account_id,
                MercuryAccount.users.contains(user),
            )
            .first()
        )

        if not mercury_account:
            flash("Mercury account not found or access denied.", "error")
            return redirect(url_for("accounts"))

        if request.method == "POST":
            # Update Mercury account
            mercury_account.name = request.form["name"]
            mercury_account.api_key = request.form["api_key"]
            environment = request.form.get("environment", "sandbox")
            mercury_account.sandbox_mode = environment == "sandbox"
            mercury_account.description = (
                request.form.get("description", "").strip() or None
            )
            mercury_account.is_active = "is_active" in request.form
            mercury_account.sync_enabled = "sync_enabled" in request.form

            db_session.commit()
            flash("Mercury account updated successfully!", "success")
            return redirect(url_for("accounts"))

        return render_template(
            "edit_mercury_account.html", mercury_account=mercury_account
        )
    finally:
        db_session.close()


@app.route("/delete_mercury_account/<int:account_id>", methods=["POST"])
@login_required
@admin_required
def delete_mercury_account(account_id):
    db_session = Session()
    try:
        user = get_current_user_in_session(db_session)
        if not user:
            flash("User not found", "error")
            return redirect(url_for("login"))

        # Get the Mercury account and ensure user has access
        mercury_account = (
            db_session.query(MercuryAccount)
            .filter(
                MercuryAccount.id == account_id,
                MercuryAccount.users.contains(user),
            )
            .first()
        )

        if not mercury_account:
            flash("Mercury account not found or access denied.", "error")
            return redirect(url_for("accounts"))

        # Delete the Mercury account
        db_session.delete(mercury_account)
        db_session.commit()
        flash("Mercury account deleted successfully!", "success")
        return redirect(url_for("accounts"))
    finally:
        db_session.close()


@app.route("/transactions")
@login_required
@transactions_required
def transactions():
    page = request.args.get("page", 1, type=int)
    account_id = request.args.get("account_id")
    category = request.args.get("category")
    mercury_account_id = request.args.get("mercury_account_id", type=int)
    status_filter = request.args.getlist("status")  # Get list of statuses
    month_filter = request.args.get("month")  # Format: YYYY-MM
    export_format = request.args.get("export")  # csv or excel

    # Default to sent and pending if no status filter specified
    if not status_filter:
        status_filter = ["posted", "pending"]  # Use 'posted' as canonical form
    
    # Expand 'posted' to include both 'posted' and 'sent' for actual query
    expanded_status_filter = []
    for status in status_filter:
        if status == 'posted':
            expanded_status_filter.extend(['posted', 'sent'])
        else:
            expanded_status_filter.append(status)
    # Remove duplicates
    expanded_status_filter = list(set(expanded_status_filter))

    db_session = Session()
    try:
        # Get current user in session to avoid DetachedInstanceError
        user_in_session = get_current_user_in_session(db_session)
        if not user_in_session:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        # Get user's accessible Mercury accounts
        all_mercury_accounts = (
            db_session.query(MercuryAccount)
            .filter(MercuryAccount.users.contains(user_in_session))
            .all()
        )

        # Get user settings
        user_settings = (
            db_session.query(UserSettings).filter_by(user_id=user_in_session.id).first()
        )

        # If no specific Mercury account is selected but user has a primary account, use that as default
        if (
            not mercury_account_id
            and user_settings
            and user_settings.primary_mercury_account_id
        ):
            # Check if primary account is accessible to user
            primary_accessible = any(
                ma.id == user_settings.primary_mercury_account_id
                for ma in all_mercury_accounts
            )
            if primary_accessible:
                mercury_account_id = user_settings.primary_mercury_account_id

        # Filter by specific Mercury account if selected
        if mercury_account_id:
            mercury_accounts = [
                ma for ma in all_mercury_accounts if ma.id == mercury_account_id
            ]
            if not mercury_accounts:
                flash("Mercury account not found or access denied.", "error")
                return redirect(url_for("transactions"))
        else:
            mercury_accounts = all_mercury_accounts

        # Get accessible accounts for this user (respects account restrictions)
        all_accessible_accounts = get_user_accessible_accounts(
            user_in_session, db_session
        )

        # If no specific account is selected but user has a primary account, use that as default
        if not account_id and user_settings and user_settings.primary_account_id:
            # Check if primary account is accessible to user
            primary_account_accessible = any(
                acc.id == user_settings.primary_account_id
                for acc in all_accessible_accounts
            )
            if primary_account_accessible:
                account_id = user_settings.primary_account_id

        account_ids = []
        for mercury_account in mercury_accounts:
            mercury_account_accessible_accounts = [
                account
                for account in all_accessible_accounts
                if account.mercury_account_id == mercury_account.id
            ]
            account_ids.extend([acc.id for acc in mercury_account_accessible_accounts])

        # Get available months for dropdown
        available_months = (
            get_available_months(db_session, account_ids) if account_ids else []
        )

        # Build query
        query = db_session.query(Transaction).filter(
            Transaction.account_id.in_(account_ids)
        )

        if account_id:
            query = query.filter_by(account_id=account_id)

        if category:
            query = query.filter(Transaction.note.ilike(f"%{category}%"))

        # Add status filter
        if expanded_status_filter:
            query = query.filter(Transaction.status.in_(expanded_status_filter))

        # Add month filter
        if month_filter:
            try:
                year, month = map(int, month_filter.split("-"))
                from sqlalchemy import and_, extract

                # Use effective date (posted_at or created_at) for month filtering
                effective_date = func.coalesce(
                    Transaction.posted_at, Transaction.created_at
                )
                query = query.filter(
                    and_(
                        extract("year", effective_date) == year,
                        extract("month", effective_date) == month,
                    )
                )
            except (ValueError, AttributeError):
                pass  # Invalid month format, ignore filter

        # Pagination
        per_page = 50
        offset = (page - 1) * per_page
        # Order by effective date (posted_at for completed transactions, created_at for pending)
        # Put pending transactions first (they have NULL posted_at), then completed transactions
        from sqlalchemy import case, desc, asc

        effective_date = case(
            (Transaction.posted_at.isnot(None), Transaction.posted_at),
            else_=Transaction.created_at,
        )
        transactions = (
            query.order_by(
                # First sort: pending transactions first (posted_at is NULL)
                asc(Transaction.posted_at.isnot(None)),
                # Second sort: by effective date descending
                desc(effective_date),
            )
            .offset(offset)
            .limit(per_page)
            .all()
        )

        # Get all accounts for filter dropdown
        all_accounts = (
            db_session.query(Account).filter(Account.id.in_(account_ids)).all()
        )

        # Get available categories and sub-categories
        category_data = get_unique_categories_and_subcategories(db_session, account_ids)
        categories = category_data['all_combinations']

        # Available statuses
        available_statuses = ["pending", "sent", "cancelled", "failed"]

        # Get all Mercury accounts for filter dropdown
        all_mercury_accounts = (
            db_session.query(MercuryAccount)
            .filter(MercuryAccount.users.contains(current_user))
            .all()
        )

        # Handle export requests
        if export_format in ["csv", "excel"]:
            # Get all transactions for export (without pagination)
            all_transactions = query.order_by(
                # First sort: pending transactions first (posted_at is NULL)
                asc(Transaction.posted_at.isnot(None)),
                # Second sort: by effective date descending
                desc(effective_date),
            ).all()

            return export_transactions(all_transactions, export_format, all_accounts)

        return render_template(
            "transactions.html",
            transactions=transactions,
            accounts=all_accounts,
            categories=categories,
            available_statuses=available_statuses,
            mercury_accounts=all_mercury_accounts,
            available_months=available_months,
            current_account_id=account_id,
            current_category=category,
            current_status=status_filter,
            current_mercury_account_id=mercury_account_id,
            current_month=month_filter,
            page=page,
        )
    finally:
        db_session.close()


@app.route("/reports")
@login_required
@reports_required
def reports():
    month_filter = request.args.get("month")  # Format: YYYY-MM
    mercury_account_id = request.args.get("mercury_account_id", type=int)
    account_id = request.args.get("account_id")
    category = request.args.get("category")
    status_filter = request.args.getlist("status")  # Get list of statuses
    export_format = request.args.get("export")  # csv or excel

    # Default to sent and pending if no status filter specified
    if not status_filter:
        status_filter = ["sent", "pending"]

    # Expand 'posted' to include both 'posted' and 'sent' for actual query
    expanded_status_filter = []
    for status in status_filter:
        if status == 'posted':
            expanded_status_filter.extend(['posted', 'sent'])
        else:
            expanded_status_filter.append(status)
    # Remove duplicates
    expanded_status_filter = list(set(expanded_status_filter))

    db_session = Session()
    try:
        # Get current user in session to avoid DetachedInstanceError
        user_in_session = get_current_user_in_session(db_session)
        if not user_in_session:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        # Get all Mercury accounts for filter dropdown
        mercury_accounts = (
            db_session.query(MercuryAccount)
            .filter(MercuryAccount.users.contains(user_in_session))
            .all()
        )

        # Get user settings
        user_settings = (
            db_session.query(UserSettings).filter_by(user_id=user_in_session.id).first()
        )

        # Get view type, using user's preference as default if not specified in URL
        view_type = request.args.get("view")
        if view_type is None and user_settings:
            view_type = user_settings.get_report_preference("default_view", "charts")
        elif view_type is None:
            view_type = "charts"

        # If no specific Mercury account is selected but user has a primary account, use that as default
        if (
            not mercury_account_id
            and user_settings
            and user_settings.primary_mercury_account_id
        ):
            # Check if primary account is accessible to user
            primary_accessible = any(
                ma.id == user_settings.primary_mercury_account_id
                for ma in mercury_accounts
            )
            if primary_accessible:
                mercury_account_id = user_settings.primary_mercury_account_id

        # Filter by specific Mercury account if selected
        if mercury_account_id:
            accessible_mercury_accounts = [
                ma for ma in mercury_accounts if ma.id == mercury_account_id
            ]
            if not accessible_mercury_accounts:
                flash("Mercury account not found or access denied.", "error")
                return redirect(url_for("reports"))
        else:
            accessible_mercury_accounts = mercury_accounts

        # Get accessible accounts for this user (respects account restrictions and excludes accounts marked as exclude_from_reports)
        all_accessible_accounts = get_user_accessible_accounts_for_reports(
            user_in_session, db_session
        )

        # If no specific account is selected but user has a primary account, use that as default
        if not account_id and user_settings and user_settings.primary_account_id:
            # Check if primary account is accessible to user
            primary_account_accessible = any(
                acc.id == user_settings.primary_account_id
                for acc in all_accessible_accounts
            )
            if primary_account_accessible:
                account_id = user_settings.primary_account_id

        # Filter accessible accounts by selected mercury account(s)
        accounts = []
        account_ids = []
        for mercury_account in accessible_mercury_accounts:
            mercury_account_accessible_accounts = [
                account
                for account in all_accessible_accounts
                if account.mercury_account_id == mercury_account.id
            ]
            accounts.extend(mercury_account_accessible_accounts)
            account_ids.extend([acc.id for acc in mercury_account_accessible_accounts])

        # Get available months for dropdown
        available_months = (
            get_available_months(db_session, account_ids) if account_ids else []
        )

        # Get available categories and sub-categories
        category_data = get_unique_categories_and_subcategories(db_session, account_ids)
        categories = category_data['all_combinations']
        category_structure = category_data['subcategories']

        # Get available statuses
        available_statuses = []
        if account_ids:
            status_results = (
                db_session.query(Transaction.status)
                .filter(Transaction.account_id.in_(account_ids))
                .filter(Transaction.status.isnot(None))
                .distinct()
                .all()
            )
            raw_statuses = [status[0] for status in status_results if status[0]]
            
            # Consolidate sent and posted statuses (they are equivalent)
            consolidated_statuses = set()
            for status in raw_statuses:
                if status in ['sent', 'posted']:
                    consolidated_statuses.add('posted')  # Use 'posted' as the canonical form
                else:
                    consolidated_statuses.add(status)
            
            available_statuses = sorted(list(consolidated_statuses))

        # If table view or export is requested, get transaction data
        table_data = None
        hierarchical_data = None
        if view_type == "table" or export_format:
            # For export, use the flat table data
            if export_format:
                table_data = get_reports_table_data(
                    db_session,
                    mercury_account_id,
                    month_filter,
                    account_id,
                    category,
                    expanded_status_filter,
                )
                return export_reports_data(table_data, export_format)
            else:
                # For table view, use hierarchical data
                hierarchical_data = get_hierarchical_reports_data(
                    db_session,
                    mercury_account_id,
                    month_filter,
                    account_id,
                    category,
                    expanded_status_filter,
                )

        return render_template(
            "reports.html",
            mercury_accounts=mercury_accounts,
            accounts=accounts,
            available_months=available_months,
            categories=categories,
            category_structure=category_structure,
            available_statuses=available_statuses,
            view_type=view_type,
            current_month=month_filter,
            current_mercury_account_id=mercury_account_id,
            current_account_id=account_id,
            current_category=category,
            current_status=status_filter,
            table_data=table_data,
            hierarchical_data=hierarchical_data,
        )
    finally:
        db_session.close()


@app.route("/api/budget_data")
@login_required
def budget_data():
    """API endpoint for budget chart data"""
    months = request.args.get("months", 12, type=int)
    include_pending = request.args.get("include_pending", "true").lower() == "true"
    show_subcategories = request.args.get("show_subcategories", "false").lower() == "true"
    mercury_account_id = request.args.get("mercury_account_id", type=int)
    month_filter = request.args.get("month")  # Format: YYYY-MM

    db_session = Session()
    try:
        # Get user's accessible Mercury accounts
        mercury_accounts = (
            db_session.query(MercuryAccount)
            .filter(MercuryAccount.users.contains(current_user))
            .all()
        )

        # Filter by specific Mercury account if selected
        if mercury_account_id:
            mercury_accounts = [
                ma for ma in mercury_accounts if ma.id == mercury_account_id
            ]
            if not mercury_accounts:
                return (
                    jsonify({"error": "Mercury account not found or access denied"}),
                    403,
                )

        account_ids = []
        for mercury_account in mercury_accounts:
            accounts = (
                db_session.query(Account)
                .filter_by(mercury_account_id=mercury_account.id)
                .filter_by(
                    exclude_from_reports=False
                )  # Exclude accounts marked as exclude_from_reports
                .all()
            )
            account_ids.extend([acc.id for acc in accounts])

        # Calculate date range
        if month_filter:
            try:
                year, month = map(int, month_filter.split("-"))
                start_date = datetime(year, month, 1)
                if month == 12:
                    end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = datetime(year, month + 1, 1) - timedelta(days=1)
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except (ValueError, AttributeError):
                # Invalid month format, use default range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=months * 30)
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)

        # Build query filters - use created_at for pending transactions, posted_at for completed
        date_field = func.coalesce(Transaction.posted_at, Transaction.created_at)
        filters = [
            Transaction.account_id.in_(account_ids),
            date_field >= start_date,
            date_field <= end_date,
            # Transaction.note.isnot(None),
            Transaction.amount < 0,  # Only expenses (negative amounts)
        ]

        # Add status filter if not including pending
        if not include_pending:
            filters.append(Transaction.status.in_(["sent"]))
        else:
            filters.append(Transaction.status.in_(["sent", "pending"]))

        # Query transactions grouped by month and category (note field)
        # Use created_at for pending transactions (where posted_at is null), posted_at for completed
        date_for_grouping = func.coalesce(Transaction.posted_at, Transaction.created_at)
        transactions = (
            db_session.query(
                extract("year", date_for_grouping).label("year"),
                extract("month", date_for_grouping).label("month"),
                func.lower(Transaction.note).label("category"),  # Make case-insensitive
                func.sum(Transaction.amount).label("total_amount"),
            )
            .filter(*filters)
            .group_by(
                extract("year", date_for_grouping),
                extract("month", date_for_grouping),
                func.lower(Transaction.note),  # Group by lowercase category
            )
            .all()
        )

        # Organize data for chart
        budget_data = defaultdict(lambda: defaultdict(float))
        categories = set()

        for transaction in transactions:
            month_key = f"{int(transaction.year)}-{int(transaction.month):02d}"
            category = (
                transaction.category or "uncategorized"
            )  # Already lowercase from query
            category = category.title()  # Convert to title case for display
            
            # Format category for display based on show_subcategories setting
            if show_subcategories:
                formatted_category = format_category_display(category)
            else:
                # Extract main category only
                main_cat, _ = parse_category(category)
                formatted_category = main_cat if main_cat else "Uncategorized"
            
            amount = abs(transaction.total_amount)  # Convert to positive for display

            budget_data[month_key][formatted_category] += amount
            categories.add(formatted_category)

        # Format for Chart.js
        months_list = []
        datasets = []

        # Generate month labels
        current_date = start_date
        while current_date <= end_date:
            month_key = f"{current_date.year}-{current_date.month:02d}"
            months_list.append(month_key)
            current_date = current_date.replace(day=1)
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)

        # Create datasets for each category
        colors = [
            "#FF6384",
            "#36A2EB",
            "#FFCE56",
            "#4BC0C0",
            "#9966FF",
            "#FF9F40",
            "#FF6384",
            "#C9CBCF",
            "#4BC0C0",
            "#FF6384",
        ]

        for i, category in enumerate(sorted(categories)):
            data = []
            for month in months_list:
                data.append(budget_data[month].get(category, 0))

            datasets.append(
                {
                    "label": category,
                    "data": data,
                    "backgroundColor": colors[i % len(colors)],
                    "borderColor": colors[i % len(colors)],
                    "borderWidth": 1,
                }
            )

        return jsonify({"labels": months_list, "datasets": datasets})

    finally:
        db_session.close()


@app.route("/api/expense_breakdown")
@login_required
def expense_breakdown():
    """API endpoint for expense breakdown pie chart"""
    months = request.args.get("months", 3, type=int)
    include_pending = request.args.get("include_pending", "true").lower() == "true"
    show_subcategories = request.args.get("show_subcategories", "false").lower() == "true"
    mercury_account_id = request.args.get("mercury_account_id", type=int)
    month_filter = request.args.get("month")  # Format: YYYY-MM

    db_session = Session()
    try:
        # Get user's accessible Mercury accounts
        mercury_accounts = (
            db_session.query(MercuryAccount)
            .filter(MercuryAccount.users.contains(current_user))
            .all()
        )

        # Filter by specific Mercury account if selected
        if mercury_account_id:
            mercury_accounts = [
                ma for ma in mercury_accounts if ma.id == mercury_account_id
            ]
            if not mercury_accounts:
                return (
                    jsonify({"error": "Mercury account not found or access denied"}),
                    403,
                )

        account_ids = []
        for mercury_account in mercury_accounts:
            accounts = (
                db_session.query(Account)
                .filter_by(mercury_account_id=mercury_account.id)
                .filter_by(
                    exclude_from_reports=False
                )  # Exclude accounts marked as exclude_from_reports
                .all()
            )
            account_ids.extend([acc.id for acc in accounts])

        # Calculate date range
        if month_filter:
            try:
                year, month = map(int, month_filter.split("-"))
                start_date = datetime(year, month, 1)
                if month == 12:
                    end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = datetime(year, month + 1, 1) - timedelta(days=1)
                end_date = end_date.replace(hour=23, minute=59, second=59)
            except (ValueError, AttributeError):
                # Invalid month format, use default range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=months * 30)
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)

        # Build query filters - use created_at for pending transactions, posted_at for completed
        date_field = func.coalesce(Transaction.posted_at, Transaction.created_at)
        filters = [
            Transaction.account_id.in_(account_ids),
            date_field >= start_date,
            date_field <= end_date,
            Transaction.amount < 0,  # Only expenses (negative amounts)
        ]

        # Add status filter if not including pending
        if not include_pending:
            filters.append(Transaction.status.in_(["sent"]))
        else:
            filters.append(Transaction.status.in_(["sent", "pending"]))

        # Query expenses by category
        expenses = (
            db_session.query(
                func.lower(Transaction.note).label("category"),  # Make case-insensitive
                func.sum(Transaction.amount).label("total_amount"),
            )
            .filter(*filters)
            .group_by(func.lower(Transaction.note))
            .all()
        )  # Group by lowercase category

        # Format for pie chart - aggregate by main category or subcategory
        category_data = defaultdict(float)

        for expense in expenses:
            category = (
                expense.category or "uncategorized"
            )  # Already lowercase from query
            category = category.title()  # Convert to title case for display
            
            # Format category for display based on show_subcategories setting
            if show_subcategories:
                formatted_category = format_category_display(category)
            else:
                # Extract main category only
                main_cat, _ = parse_category(category)
                formatted_category = main_cat if main_cat else "Uncategorized"
            
            amount = abs(expense.total_amount)
            category_data[formatted_category] += amount

        # Convert to lists for chart
        labels = list(category_data.keys())
        data = list(category_data.values())
        colors = [
            "#FF6384",
            "#36A2EB",
            "#FFCE56",
            "#4BC0C0",
            "#9966FF",
            "#FF9F40",
            "#FF6384",
            "#C9CBCF",
            "#4BC0C0",
            "#FF6384",
        ]

        return jsonify(
            {
                "labels": labels,
                "datasets": [
                    {
                        "data": data,
                        "backgroundColor": colors[: len(data)],
                        "borderColor": "#fff",
                        "borderWidth": 2,
                    }
                ],
            }
        )

    finally:
        db_session.close()


@app.route("/admin/settings", methods=["GET", "POST"])
@login_required
@super_admin_required
def admin_settings():
    """Admin page for managing system settings."""
    db_session = Session()
    try:
        # Get current user in session to avoid DetachedInstanceError
        user_in_session = get_current_user_in_session(db_session)
        if not user_in_session:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        # Check if user is admin
        if not (
            user_in_session.has_role("admin") or user_in_session.has_role("super-admin")
        ):
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for("dashboard"))

        # Check if users are externally managed
        users_externally_managed = SystemSetting.get_bool_value(
            db_session, "users_externally_managed", default=False
        )

        if request.method == "POST":
            # Define branding settings that are always editable
            branding_settings = ["app_name", "app_description", "logo_url"]

            # Update settings
            updated_count = 0
            for key, value in request.form.items():
                if key.startswith("setting_"):
                    setting_key = key.replace("setting_", "")
                    setting = (
                        db_session.query(SystemSetting)
                        .filter_by(key=setting_key)
                        .first()
                    )
                    if setting and setting.is_editable:
                        # Allow branding settings to be changed even when users are externally managed
                        is_branding_setting = setting_key in branding_settings

                        # Block user management settings if users are externally managed
                        if users_externally_managed and not is_branding_setting:
                            continue  # Skip user management settings

                        setting.value = value
                        updated_count += 1

            if updated_count > 0:
                db_session.commit()
                flash("Settings updated successfully!", "success")
            elif users_externally_managed:
                flash(
                    "Only branding settings can be changed when users are externally managed.",
                    "warning",
                )
            else:
                flash("No settings were updated.", "info")
            return redirect(url_for("admin_settings"))

        # Get all editable settings
        settings = db_session.query(SystemSetting).filter_by(is_editable=True).all()

        return render_template(
            "admin_settings.html",
            settings=settings,
            users_externally_managed=users_externally_managed,
        )
    finally:
        db_session.close()


@app.route("/admin/mercury_access/<int:mercury_account_id>", methods=["GET", "POST"])
@login_required
@admin_required
def manage_mercury_access(mercury_account_id):
    """Admin page for managing user access to Mercury accounts and specific accounts within them."""
    db_session = Session()
    try:
        # Get current user in session to avoid DetachedInstanceError
        user_in_session = get_current_user_in_session(db_session)
        if not user_in_session:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        # Check if user is admin
        if not (
            user_in_session.has_role("admin") or user_in_session.has_role("super-admin")
        ):
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for("dashboard"))

        # Get the Mercury account
        mercury_account = db_session.query(MercuryAccount).get(mercury_account_id)
        if not mercury_account:
            flash("Mercury account not found.", "error")
            return redirect(url_for("accounts"))

        # Get all users and accounts for this Mercury account
        all_users = db_session.query(User).all()
        all_accounts = (
            db_session.query(Account)
            .filter_by(mercury_account_id=mercury_account_id)
            .all()
        )

        if request.method == "POST":
            # Handle Mercury account access updates
            if "mercury_access" in request.form:
                # Get selected users for Mercury account access
                selected_user_ids = request.form.getlist("mercury_users")
                selected_user_ids = [
                    int(uid) for uid in selected_user_ids if uid.isdigit()
                ]

                # Update Mercury account user associations
                mercury_account.users.clear()
                for user_id in selected_user_ids:
                    user = db_session.query(User).get(user_id)
                    if user:
                        mercury_account.users.append(user)

                db_session.commit()
                flash("Mercury account access updated successfully!", "success")

            # Handle account-level restrictions
            elif "account_restrictions" in request.form:
                print(
                    f"DEBUG: Processing account restrictions for mercury_account_id={mercury_account_id}"
                )
                print(f"DEBUG: Form data: {dict(request.form)}")

                # Clear all existing account restrictions for users of this Mercury account
                # Get all accounts belonging to this Mercury account
                mercury_accounts = (
                    db_session.query(Account)
                    .filter_by(mercury_account_id=mercury_account_id)
                    .all()
                )
                print(
                    f"DEBUG: Found {len(mercury_accounts)} accounts for mercury account {mercury_account_id}"
                )

                for account in mercury_accounts:
                    # Clear existing restrictions for this account
                    print(
                        f"DEBUG: Clearing restrictions for account {account.id}, had {len(account.authorized_users)} users"
                    )
                    account.authorized_users.clear()

                # Process account-level restrictions
                for user in all_users:
                    if (
                        user in mercury_account.users
                    ):  # Only process users who have Mercury account access
                        user_account_access = request.form.getlist(
                            f"user_{user.id}_accounts"
                        )
                        user_account_access = [
                            aid for aid in user_account_access if aid
                        ]
                        print(
                            f"DEBUG: User {user.username} (id={user.id}) selected accounts: {user_account_access}"
                        )

                        # If specific accounts are selected, restrict to those accounts
                        if user_account_access:
                            for account_id in user_account_access:
                                # Verify account exists and belongs to this Mercury account
                                account = (
                                    db_session.query(Account)
                                    .filter_by(
                                        id=account_id,
                                        mercury_account_id=mercury_account_id,
                                    )
                                    .first()
                                )
                                if account:
                                    if user not in account.authorized_users:
                                        print(
                                            f"DEBUG: Adding user {user.username} to account {account.id} authorized users"
                                        )
                                        account.authorized_users.append(user)
                                    else:
                                        print(
                                            f"DEBUG: User {user.username} already in account {account.id} authorized users"
                                        )
                                else:
                                    print(
                                        f"DEBUG: Account {account_id} not found or doesn't belong to mercury account {mercury_account_id}"
                                    )
                        else:
                            print(
                                f"DEBUG: User {user.username} has no account restrictions (full access)"
                            )
                        # If no accounts selected, user has access to all accounts (default behavior)
                        # We don't need to do anything in this case since empty authorized_users means full access

                try:
                    db_session.commit()
                    print("DEBUG: Successfully committed account restrictions changes")
                    flash(
                        "Account access restrictions updated successfully!", "success"
                    )
                except Exception as e:
                    print(f"DEBUG: Error committing changes: {e}")
                    db_session.rollback()
                    flash(f"Error updating account restrictions: {e}", "error")

            return redirect(
                url_for("manage_mercury_access", mercury_account_id=mercury_account_id)
            )

        return render_template(
            "manage_mercury_access.html",
            mercury_account=mercury_account,
            all_users=all_users,
            all_accounts=all_accounts,
        )
    finally:
        db_session.close()


@app.route("/admin/users", methods=["GET"])
@login_required
@super_admin_required
def admin_users():
    """Admin page for managing users."""
    db_session = Session()
    try:
        # Get current user in session to avoid DetachedInstanceError
        user_in_session = get_current_user_in_session(db_session)
        if not user_in_session:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        # Check if user is admin
        if not (
            user_in_session.has_role("admin") or user_in_session.has_role("super-admin")
        ):
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for("dashboard"))

        # Get all users
        all_users = db_session.query(User).all()

        # Get admin users (using role-based system)
        admin_users = [
            user
            for user in all_users
            if user.has_role("admin") or user.has_role("super-admin")
        ]

        # Get user deletion prevention setting
        prevent_user_deletion = SystemSetting.get_bool_value(
            db_session, "prevent_user_deletion", default=False
        )

        # Check if users are externally managed
        users_externally_managed = SystemSetting.get_bool_value(
            db_session, "users_externally_managed", default=False
        )

        return render_template(
            "admin_users.html",
            all_users=all_users,
            admin_users=admin_users,
            prevent_user_deletion=prevent_user_deletion,
            users_externally_managed=users_externally_managed,
            current_user=user_in_session,
        )
    finally:
        db_session.close()


@app.route("/admin/users/add", methods=["GET"])
@login_required
@super_admin_required
def add_user_form():
    """Display form to add a new user."""
    db_session = Session()
    try:
        # Get current user in session to avoid DetachedInstanceError
        user_in_session = get_current_user_in_session(db_session)
        if not user_in_session:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        # Check if user is admin
        if not (
            user_in_session.has_role("admin") or user_in_session.has_role("super-admin")
        ):
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for("dashboard"))

        # Check if users are externally managed
        users_externally_managed = SystemSetting.get_bool_value(
            db_session, "users_externally_managed", default=False
        )
        if users_externally_managed:
            flash(
                "User creation is not allowed when users are externally managed.",
                "error",
            )
            return redirect(url_for("admin_users"))

        # Get available roles
        from models.role import Role

        available_roles = db_session.query(Role).order_by(Role.name).all()

        return render_template("add_user.html", available_roles=available_roles)
    finally:
        db_session.close()


@app.route("/admin/users/add", methods=["POST"])
@login_required
@super_admin_required
def add_user_submit():
    """Process form submission to add a new user."""
    db_session = Session()
    try:
        # Get current user in session to avoid DetachedInstanceError
        user_in_session = get_current_user_in_session(db_session)
        if not user_in_session:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        # Check if user is admin
        if not (
            user_in_session.has_role("admin") or user_in_session.has_role("super-admin")
        ):
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for("dashboard"))

        # Check if users are externally managed
        users_externally_managed = SystemSetting.get_bool_value(
            db_session, "users_externally_managed", default=False
        )
        if users_externally_managed:
            flash(
                "User creation is not allowed when users are externally managed.",
                "error",
            )
            return redirect(url_for("admin_users"))

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        selected_roles = request.form.getlist("roles")

        # Validate inputs
        if not username or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("add_user_form"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("add_user_form"))

        # Ensure user role is selected (required for basic access)
       
        if "user" not in selected_roles:
            flash("The 'user' role is required for basic access.", "error")
            return redirect(url_for("add_user_form"))

        # Check if user already exists
        existing_user = (
            db_session.query(User)
            .filter((User.username == username) | (User.email == email))
            .first()
        )

        if existing_user:
            flash("A user with that username or email already exists.", "error")
            return redirect(url_for("add_user_form"))

        # Create new user
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db_session.add(new_user)
        db_session.flush()  # Get the user ID

        # Assign roles
        import logging
        from models.role import Role

        for role_name in selected_roles:
            role = db_session.query(Role).filter_by(name=role_name).first()
            if role:
                new_user.roles.append(role)
            else:
                logging.warning(
                    f"Requested role '{role_name}' does not exist in the database. Possible typo or misconfiguration."
                )

        # Create user settings
        user_settings = UserSettings(user_id=new_user.id)
        db_session.add(user_settings)
        db_session.commit()

        flash(
            f"User '{username}' created successfully with roles: {', '.join(selected_roles)}!",
            "success",
        )
        return redirect(url_for("admin_users"))
    except Exception as e:
        db_session.rollback()
        flash(f"Error creating user: {str(e)}", "error")
        return redirect(url_for("add_user_form"))
    finally:
        db_session.close()


@app.route("/admin/users/<int:user_id>/lock", methods=["POST"])
@login_required
@super_admin_required
def lock_user(user_id):
    """Lock a user's account."""
    db_session = Session()
    try:
        # Get current user in session to avoid DetachedInstanceError
        user_in_session = get_current_user_in_session(db_session)
        if not user_in_session:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        # Get the user to lock
        user = db_session.query(User).filter_by(id=user_id).first()
        if not user:
            flash("User not found.", "error")
            return redirect(url_for("admin_users"))

        # Don't allow locking of super admins
        if user.is_super_admin:
            flash("Cannot lock a super admin account.", "error")
            return redirect(url_for("admin_users"))

        # Don't allow locking of self
        if user.id == current_user.id:
            flash("You cannot lock your own account.", "error")
            return redirect(url_for("admin_users"))

        # Add the locked role
        if not user.has_role("locked"):
            user.add_role("locked", db_session)
            db_session.commit()
            flash(f"User '{user.username}' has been locked.", "success")
        else:
            flash(f"User '{user.username}' is already locked.", "info")
    except Exception as e:
        db_session.rollback()
        flash(f"Error locking user: {str(e)}", "error")

    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/unlock", methods=["POST"])
@login_required
@super_admin_required
def unlock_user(user_id):
    """Unlock a user's account."""
    db_session = Session()
    try:
        # Get current user in session to avoid DetachedInstanceError
        user_in_session = get_current_user_in_session(db_session)
        if not user_in_session:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        # Get the user to unlock
        user = db_session.query(User).filter_by(id=user_id).first()
        if not user:
            flash("User not found.", "error")
            return redirect(url_for("admin_users"))

        # Remove the locked role
        if user.has_role("locked"):
            user.remove_role("locked", db_session)
            db_session.commit()
            flash(f"User '{user.username}' has been unlocked.", "success")
        else:
            flash(f"User '{user.username}' is not locked.", "info")
    except Exception as e:
        db_session.rollback()
        flash(f"Error unlocking user: {str(e)}", "error")

    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@login_required
@super_admin_required
def delete_user_by_id(user_id):
    """Delete a user from the system."""
    db_session = Session()
    try:
        # Get current user in session to avoid DetachedInstanceError
        user_in_session = get_current_user_in_session(db_session)
        if not user_in_session:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        # Check if users are externally managed - if yes, always prevent deletion
        if SystemSetting.get_bool_value(
            db_session, "users_externally_managed", default=False
        ):
            flash(
                "User deletion is disabled because users are externally managed.",
                "error",
            )
            return redirect(url_for("admin_users"))

        # Check if user deletion is prevented by system settings
        if SystemSetting.get_bool_value(
            db_session, "prevent_user_deletion", default=False
        ):
            flash("User deletion is disabled by system settings.", "error")
            return redirect(url_for("admin_users"))

        # Get the user to delete
        user = db_session.query(User).get(user_id)
        if not user:
            flash("User not found.", "error")
            return redirect(url_for("admin_users"))

        # Check if trying to delete self
        if user.id == user_in_session.id:
            flash("You cannot delete your own account.", "error")
            return redirect(url_for("admin_users"))

        # Check if user is an admin
        from models.role import Role

        if user.has_role("admin") or user.has_role("super-admin"):
            # Check if this is the last admin
            admin_count = (
                db_session.query(User)
                .filter(User.roles.any(Role.name.in_(["admin", "super-admin"])))
                .count()
            )
            if admin_count <= 1:
                flash("Cannot delete the last admin user.", "error")
                return redirect(url_for("admin_users"))

        # Remember username for the success message
        username = user.username

        # Delete the user
        db_session.delete(user)
        db_session.commit()
        flash(f"User '{username}' deleted successfully.", "success")
    except Exception as e:
        db_session.rollback()
        flash(f"Error deleting user: {str(e)}", "error")

    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/roles", methods=["GET", "POST"])
@login_required
@super_admin_required
def edit_user_roles(user_id):
    """Edit roles for a user - super-admin only."""
    db_session = Session()
    try:
        # Get current user in session to avoid DetachedInstanceError
        user_in_session = get_current_user_in_session(db_session)
        if not user_in_session:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        # Check if user is super-admin
        if not user_in_session.is_super_admin:
            flash("Access denied. Super-admin privileges required.", "error")
            return redirect(url_for("dashboard"))

        # Get the user to edit
        user = db_session.query(User).get(user_id)
        if not user:
            flash("User not found.", "error")
            return redirect(url_for("admin_users"))

        # Get available roles
        from models.role import Role

        available_roles = db_session.query(Role).order_by(Role.name).all()

        if request.method == "POST":
            selected_roles = request.form.getlist("roles")

            # Validate that 'user' role is selected (required for basic access)
            if "user" not in selected_roles and not user.is_super_admin:
                flash(
                    "The 'user' role is required for basic access. Super-admin users are exempt from this requirement.",
                    "warning",
                )
                return render_template(
                    "edit_user_roles.html", user=user, available_roles=available_roles
                )

            # Clear existing roles
            user.roles.clear()

            # Assign new roles
            for role_name in selected_roles:
                role = db_session.query(Role).filter_by(name=role_name).first()
                if role:
                    user.roles.append(role)

            db_session.commit()
            flash(
                f"Roles updated successfully for user '{user.username}'. Current roles: {', '.join(selected_roles)}",
                "success",
            )
            return redirect(url_for("admin_users"))

        return render_template(
            "edit_user_roles.html", user=user, available_roles=available_roles
        )

    except Exception as e:
        db_session.rollback()
        flash(f"Error updating user roles: {str(e)}", "error")
        return redirect(url_for("admin_users"))
    finally:
        db_session.close()


@app.route("/admin/users/<int:user_id>/settings", methods=["GET", "POST"])
@login_required
@super_admin_required
def edit_user_settings(user_id):
    """Edit settings for a user - super-admin only."""
    db_session = Session()
    try:
        # Get current user in session to avoid DetachedInstanceError
        user_in_session = get_current_user_in_session(db_session)
        if not user_in_session:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        # Check if user is super-admin
        if not user_in_session.is_super_admin:
            flash("Access denied. Super-admin privileges required.", "error")
            return redirect(url_for("dashboard"))

        # Get the user to edit
        user = db_session.query(User).get(user_id)
        if not user:
            flash("User not found.", "error")
            return redirect(url_for("admin_users"))

        # Get or create user settings
        settings = db_session.query(UserSettings).filter_by(user_id=user.id).first()
        if not settings:
            settings = UserSettings(user_id=user.id)
            db_session.add(settings)
            db_session.commit()

        # Get available Mercury accounts for this user
        mercury_accounts = (
            db_session.query(MercuryAccount)
            .filter(MercuryAccount.users.contains(user))
            .all()
        )

        # Get user's accessible accounts for primary account selection
        accessible_accounts = get_user_accessible_accounts(user, db_session)

        if request.method == "POST":
            # Update primary Mercury account
            primary_mercury_account_id = request.form.get("primary_mercury_account_id")
            if primary_mercury_account_id == "":
                settings.primary_mercury_account_id = None
            else:
                primary_mercury_account_id = int(primary_mercury_account_id)
                # Verify user has access to this Mercury account
                accessible_account_ids = [ma.id for ma in mercury_accounts]
                if primary_mercury_account_id in accessible_account_ids:
                    settings.primary_mercury_account_id = primary_mercury_account_id
                else:
                    flash(
                        f"User '{user.username}' doesn't have access to the selected Mercury account.",
                        "error",
                    )
                    return render_template(
                        "edit_user_settings.html",
                        settings=settings,
                        target_user=user,
                        mercury_accounts=mercury_accounts,
                        accessible_accounts=accessible_accounts,
                    )

            # Update primary account
            primary_account_id = request.form.get("primary_account_id")
            if primary_account_id == "":
                settings.primary_account_id = None
            else:
                # Verify user has access to this account
                accessible_account_ids = [acc.id for acc in accessible_accounts]
                if primary_account_id in accessible_account_ids:
                    settings.primary_account_id = primary_account_id
                else:
                    flash(
                        f"User '{user.username}' doesn't have access to the selected account.",
                        "error",
                    )
                    return render_template(
                        "edit_user_settings.html",
                        settings=settings,
                        target_user=user,
                        mercury_accounts=mercury_accounts,
                        accessible_accounts=accessible_accounts,
                    )

            # Update other preferences
            dashboard_prefs = {}
            report_prefs = {}
            transaction_prefs = {}

            # Dashboard preferences
            if request.form.get("dashboard_show_pending") == "on":
                dashboard_prefs["show_pending"] = True
            else:
                dashboard_prefs["show_pending"] = False

            # Report preferences
            report_prefs["default_view"] = request.form.get(
                "report_default_view", "charts"
            )
            report_prefs["default_period"] = request.form.get(
                "report_default_period", "12"
            )

            # Transaction preferences
            transaction_prefs["default_page_size"] = int(
                request.form.get("transaction_page_size", "50")
            )
            transaction_prefs["default_status_filter"] = request.form.getlist(
                "transaction_default_status"
            )

            # Update settings
            settings.dashboard_preferences = dashboard_prefs
            settings.report_preferences = report_prefs
            settings.transaction_preferences = transaction_prefs

            db_session.commit()
            flash(
                f"Settings updated successfully for user '{user.username}'!", "success"
            )
            return redirect(url_for("admin_users"))

        return render_template(
            "edit_user_settings.html",
            settings=settings,
            target_user=user,
            mercury_accounts=mercury_accounts,
            accessible_accounts=accessible_accounts,
        )

    except Exception as e:
        db_session.rollback()
        flash(f"Error updating user settings: {str(e)}", "error")
        return redirect(url_for("admin_users"))
    finally:
        db_session.close()


@app.route("/health")
def health_check():
    """Health check endpoint for Docker and monitoring systems."""
    try:
        # Test database connection
        db_session = Session()
        db_session.execute(text("SELECT 1"))
        db_session.close()
        return (
            jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ),
            503,
        )


def get_available_months(db_session, account_ids):
    """Get available months from transactions data"""
    from sqlalchemy import distinct, extract, func
    from datetime import datetime

    # Use effective date (posted_at or created_at) for month extraction
    effective_date = func.coalesce(Transaction.posted_at, Transaction.created_at)

    # Query distinct year-month combinations
    months_data = (
        db_session.query(
            extract("year", effective_date).label("year"),
            extract("month", effective_date).label("month"),
        )
        .filter(Transaction.account_id.in_(account_ids))
        .distinct()
        .order_by(
            extract("year", effective_date).desc(),
            extract("month", effective_date).desc(),
        )
        .all()
    )

    # Format as YYYY-MM strings
    available_months = []
    for year, month in months_data:
        if year and month:
            month_str = f"{int(year)}-{int(month):02d}"
            available_months.append(
                {
                    "value": month_str,
                    "label": datetime(int(year), int(month), 1).strftime("%B %Y"),
                }
            )

    return available_months


def get_current_month():
    """Get current month in YYYY-MM format"""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m")


@app.route("/settings", methods=["GET", "POST"])
@login_required
def user_settings():
    """User settings page for managing preferences including primary Mercury account."""
    db_session = Session()
    try:
        # Get current user in session to avoid DetachedInstanceError
        user_in_session = get_current_user_in_session(db_session)
        if not user_in_session:
            flash("User session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        # Get or create user settings
        settings = (
            db_session.query(UserSettings).filter_by(user_id=user_in_session.id).first()
        )
        if not settings:
            settings = UserSettings(user_id=user_in_session.id)
            db_session.add(settings)
            db_session.commit()

        # Get user's accessible Mercury accounts
        mercury_accounts = (
            db_session.query(MercuryAccount)
            .filter(MercuryAccount.users.contains(user_in_session))
            .all()
        )

        # Get user's accessible accounts for primary account selection
        accessible_accounts = get_user_accessible_accounts(user_in_session, db_session)

        if request.method == "POST":
            # Update primary Mercury account
            primary_mercury_account_id = request.form.get("primary_mercury_account_id")
            if primary_mercury_account_id == "":
                settings.primary_mercury_account_id = None
            else:
                primary_mercury_account_id = int(primary_mercury_account_id)
                # Verify user has access to this Mercury account
                accessible_account_ids = [ma.id for ma in mercury_accounts]
                if primary_mercury_account_id in accessible_account_ids:
                    settings.primary_mercury_account_id = primary_mercury_account_id
                else:
                    flash(
                        "You don't have access to the selected Mercury account.",
                        "error",
                    )
                    return redirect(url_for("user_settings"))

            # Update primary account
            primary_account_id = request.form.get("primary_account_id")
            if primary_account_id == "":
                settings.primary_account_id = None
            else:
                # Verify user has access to this account
                accessible_account_ids = [acc.id for acc in accessible_accounts]
                if primary_account_id in accessible_account_ids:
                    settings.primary_account_id = primary_account_id
                else:
                    flash("You don't have access to the selected account.", "error")
                    return redirect(url_for("user_settings"))

            # Update other preferences
            dashboard_prefs = {}
            report_prefs = {}
            transaction_prefs = {}

            # Dashboard preferences
            if request.form.get("dashboard_show_pending") == "on":
                dashboard_prefs["show_pending"] = True
            else:
                dashboard_prefs["show_pending"] = False

            # Report preferences
            report_prefs["default_view"] = request.form.get(
                "report_default_view", "charts"
            )
            report_prefs["default_period"] = request.form.get(
                "report_default_period", "12"
            )

            # Transaction preferences
            transaction_prefs["default_page_size"] = int(
                request.form.get("transaction_page_size", "50")
            )
            transaction_prefs["default_status_filter"] = request.form.getlist(
                "transaction_default_status"
            )

            # Update settings
            settings.dashboard_preferences = dashboard_prefs
            settings.report_preferences = report_prefs
            settings.transaction_preferences = transaction_prefs

            db_session.commit()
            flash("Settings updated successfully!", "success")
            return redirect(url_for("user_settings"))

        return render_template(
            "user_settings.html",
            settings=settings,
            mercury_accounts=mercury_accounts,
            accessible_accounts=accessible_accounts,
        )
    finally:
        db_session.close()


def get_current_user_in_session(db_session):
    """Get the current user from the provided session to avoid DetachedInstanceError."""
    if not current_user.is_authenticated:
        return None
    return db_session.query(User).get(current_user.id)


@app.route("/edit_account/<account_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_account(account_id):
    db_session = Session()
    try:
        user = get_current_user_in_session(db_session)
        if not user:
            flash("User not found", "error")
            return redirect(url_for("login"))

        # Get accessible accounts for this user (respects account restrictions)
        accessible_accounts = get_user_accessible_accounts(user, db_session)

        # Find the specific account
        account = None
        for acc in accessible_accounts:
            if acc.id == account_id:
                account = acc
                break

        if not account:
            flash("Account not found or access denied.", "error")
            return redirect(url_for("accounts"))

        # Get the mercury account for display
        mercury_account = (
            db_session.query(MercuryAccount)
            .filter_by(id=account.mercury_account_id)
            .first()
        )

        if request.method == "POST":
            # Get receipt requirement settings from form
            receipt_required_deposits = request.form.get("receipt_required_deposits", "none")
            receipt_required_charges = request.form.get("receipt_required_charges", "none")
            
            # Check if this is a future-dated policy change
            use_future_date = "use_future_date" in request.form
            start_date = None
            
            if use_future_date:
                future_start_date_str = request.form.get("future_start_date", "")
                if future_start_date_str:
                    try:
                        # Parse the date string from the form
                        start_date = datetime.strptime(future_start_date_str, "%Y-%m-%d")
                        
                        # Set the time to beginning of day to ensure consistent behavior
                        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        
                        # Ensure the date is not in the past
                        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                        if start_date < today:
                            flash("Start date cannot be in the past.", "error")
                            return render_template(
                                "edit_account.html",
                                account=account,
                                mercury_account=mercury_account,
                                today_date=datetime.now().strftime('%Y-%m-%d')
                            )
                    except ValueError:
                        flash("Invalid start date format.", "error")
                        return render_template(
                            "edit_account.html",
                            account=account,
                            mercury_account=mercury_account,
                            today_date=datetime.now().strftime('%Y-%m-%d')
                        )
            
            # Parse threshold values
            threshold_deposits_str = request.form.get("receipt_threshold_deposits", "").strip()
            threshold_deposits = None
            if receipt_required_deposits == "threshold" and threshold_deposits_str:
                try:
                    threshold_deposits = float(threshold_deposits_str)
                except ValueError:
                    flash("Invalid deposit receipt threshold amount.", "error")
                    return render_template(
                        "edit_account.html",
                        account=account,
                        mercury_account=mercury_account,
                    )

            threshold_charges_str = request.form.get("receipt_threshold_charges", "").strip()
            threshold_charges = None
            if receipt_required_charges == "threshold" and threshold_charges_str:
                try:
                    threshold_charges = float(threshold_charges_str)
                except ValueError:
                    flash("Invalid charge receipt threshold amount.", "error")
                    return render_template(
                        "edit_account.html",
                        account=account,
                        mercury_account=mercury_account,
                    )
            
            # Update receipt policy - this creates a historical record
            account.update_receipt_policy(
                receipt_required_deposits=receipt_required_deposits,
                receipt_threshold_deposits=threshold_deposits,
                receipt_required_charges=receipt_required_charges,
                receipt_threshold_charges=threshold_charges,
                start_date=start_date
            )

            # Handle exclude from reports setting
            account.exclude_from_reports = "exclude_from_reports" in request.form

            db_session.commit()
            
            # Customize success message based on whether this is a future change
            if use_future_date and start_date:
                formatted_date = start_date.strftime("%B %d, %Y")
                flash(f"Account updated and receipt policy scheduled to change on {formatted_date}!", "success")
            else:
                flash("Account updated successfully and receipt policy updated immediately!", "success")
                
            return redirect(url_for("accounts"))

        return render_template(
            "edit_account.html", 
            account=account, 
            mercury_account=mercury_account,
            today_date=datetime.now().strftime('%Y-%m-%d')
        )
    finally:
        db_session.close()


@app.route("/api/transaction/<string:transaction_id>/attachments")
@login_required
def get_transaction_attachments(transaction_id):
    """Get attachments for a specific transaction."""
    try:
        db_session = Session()

        # Get the current user from the session to avoid DetachedInstanceError
        user = get_current_user_in_session(db_session)
        if not user:
            return jsonify({"error": "User not found"}), 401

        # Get the transaction first
        transaction = (
            db_session.query(Transaction)
            .filter(Transaction.id == transaction_id)
            .first()
        )
        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404

        # Check if user has access to this transaction's account
        user_accounts = get_user_accessible_accounts(user, db_session)
        account_ids = [acc.id for acc in user_accounts]

        if transaction.account_id not in account_ids:
            return jsonify({"error": "Access denied"}), 403

        # Get attachments for the transaction
        attachments = (
            db_session.query(TransactionAttachment)
            .filter(TransactionAttachment.transaction_id == transaction_id)
            .all()
        )

        # Convert to JSON format
        attachments_data = []
        for attachment in attachments:
            attachments_data.append(
                {
                    "id": attachment.id,
                    "filename": attachment.filename,
                    "content_type": attachment.content_type,
                    "file_size": attachment.file_size,
                    "file_size_formatted": attachment.file_size_formatted,
                    "description": attachment.description,
                    "mercury_url": attachment.mercury_url,
                    "thumbnail_url": attachment.thumbnail_url,
                    "upload_date": (
                        attachment.upload_date.isoformat()
                        if attachment.upload_date
                        else None
                    ),
                    "url_expires_at": (
                        attachment.url_expires_at.isoformat()
                        if attachment.url_expires_at
                        else None
                    ),
                    "is_url_expired": attachment.is_url_expired,
                    "is_image": attachment.is_image,
                    "is_pdf": attachment.is_pdf,
                    "file_extension": attachment.file_extension,
                    "created_at": (
                        attachment.created_at.isoformat()
                        if attachment.created_at
                        else None
                    ),
                }
            )

        return jsonify(
            {
                "transaction_id": transaction_id,
                "attachments": attachments_data,
                "count": len(attachments_data),
            }
        )

    except Exception as e:
        logger.error("Error fetching transaction attachments: %s", e)
        return jsonify({"error": "Internal server error"}), 500
    finally:
        if "db_session" in locals():
            db_session.close()


def get_hierarchical_reports_data(
    db_session,
    mercury_account_id=None,
    month_filter=None,
    account_id=None,
    category=None,
    expanded_status_filter=None,
):
    """Get aggregated category data grouped by main categories with expandable sub-categories"""
    # Get user's accessible Mercury accounts
    mercury_accounts = (
        db_session.query(MercuryAccount)
        .filter(MercuryAccount.users.contains(current_user))
        .all()
    )

    # Filter by specific Mercury account if selected
    if mercury_account_id:
        mercury_accounts = [
            ma for ma in mercury_accounts if ma.id == mercury_account_id
        ]

    account_ids = []
    for mercury_account in mercury_accounts:
        accounts = (
            db_session.query(Account)
            .filter_by(mercury_account_id=mercury_account.id)
            .filter_by(exclude_from_reports=False)
            .all()
        )
        account_ids.extend([acc.id for acc in accounts])

    # Build query for aggregation
    category_field = func.coalesce(Transaction.note, "Uncategorized")
    query = db_session.query(
        category_field.label("category"),
        func.sum(Transaction.amount).label("total_amount"),
        func.count(Transaction.id).label("transaction_count"),
    ).filter(Transaction.account_id.in_(account_ids))

    # Add filters
    if account_id:
        query = query.filter_by(account_id=account_id)
    if category:
        query = query.filter(Transaction.note.ilike(f"%{category}%"))
    if expanded_status_filter:
        query = query.filter(Transaction.status.in_(expanded_status_filter))

    # Add month filter
    if month_filter:
        try:
            year, month = map(int, month_filter.split("-"))
            from sqlalchemy import and_, extract
            effective_date = func.coalesce(Transaction.posted_at, Transaction.created_at)
            query = query.filter(
                and_(
                    extract("year", effective_date) == year,
                    extract("month", effective_date) == month,
                )
            )
        except (ValueError, AttributeError):
            pass

    # Get all category data
    category_totals = query.group_by(category_field).all()

    # Group by main categories
    main_categories = {}
    
    for category_data in category_totals:
        main_cat, sub_cat = parse_category(category_data.category)
        if not main_cat:
            main_cat = "Uncategorized"
        
        # Initialize main category if not exists
        if main_cat not in main_categories:
            main_categories[main_cat] = {
                "main_category": main_cat,
                "total_amount": 0,
                "transaction_count": 0,
                "subcategories": []
            }
        
        # Add to main category totals
        main_categories[main_cat]["total_amount"] += category_data.total_amount
        main_categories[main_cat]["transaction_count"] += category_data.transaction_count
        
        # Add subcategory data if it exists
        if sub_cat:
            main_categories[main_cat]["subcategories"].append({
                "subcategory": sub_cat,
                "full_category": category_data.category,
                "total_amount": category_data.total_amount,
                "transaction_count": category_data.transaction_count,
                "average_amount": (
                    category_data.total_amount / category_data.transaction_count
                    if category_data.transaction_count > 0
                    else 0
                ),
            })

    # Calculate averages for main categories
    for main_cat_data in main_categories.values():
        main_cat_data["average_amount"] = (
            main_cat_data["total_amount"] / main_cat_data["transaction_count"]
            if main_cat_data["transaction_count"] > 0
            else 0
        )
        # Sort subcategories by amount
        main_cat_data["subcategories"].sort(
            key=lambda x: x["total_amount"], reverse=True
        )

    # Convert to list and sort by total amount
    hierarchical_data = list(main_categories.values())
    hierarchical_data.sort(key=lambda x: x["total_amount"], reverse=True)

    return hierarchical_data


# Initialize settings on app startup

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
