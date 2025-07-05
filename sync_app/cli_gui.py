#!/usr/bin/env python3
"""
Command-Line GUI for Mercury Bank Sync Service

This provides a text-based menu interface for managing the sync service
when the web GUI is not available or installed.
"""

import os
import sys
import time
import getpass
import signal
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from models.base import Base
from models.user import User
from models.role import Role
from models.user_settings import UserSettings
from models.mercury_account import MercuryAccount
from models.account import Account
from models.transaction import Transaction
from models.system_setting import SystemSetting
from utils.encryption import encrypt_api_key, decrypt_api_key


class CLIColors:
    """ANSI color codes for terminal output."""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class MercurySyncCLI:
    """Command-line interface for Mercury Bank sync service."""

    def __init__(self):
        self.session = None
        self.engine = None
        self.current_user = None
        self.running = True

        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        print(f"\n{CLIColors.WARNING}Exiting...{CLIColors.ENDC}")
        self.running = False
        sys.exit(0)

    def _print_header(self, title: str):
        """Print a formatted header."""
        print(f"\n{CLIColors.HEADER}{CLIColors.BOLD}{'='*60}{CLIColors.ENDC}")
        print(f"{CLIColors.HEADER}{CLIColors.BOLD}{title.center(60)}{CLIColors.ENDC}")
        print(f"{CLIColors.HEADER}{CLIColors.BOLD}{'='*60}{CLIColors.ENDC}")

    def _print_success(self, message: str):
        """Print a success message."""
        print(f"{CLIColors.OKGREEN}✓ {message}{CLIColors.ENDC}")

    def _print_error(self, message: str):
        """Print an error message."""
        print(f"{CLIColors.FAIL}✗ {message}{CLIColors.ENDC}")

    def _print_warning(self, message: str):
        """Print a warning message."""
        print(f"{CLIColors.WARNING}⚠ {message}{CLIColors.ENDC}")

    def _print_info(self, message: str):
        """Print an info message."""
        print(f"{CLIColors.OKBLUE}ℹ {message}{CLIColors.ENDC}")

    def _get_input(self, prompt: str) -> str:
        """Get user input with colored prompt."""
        return input(f"{CLIColors.OKCYAN}{prompt}{CLIColors.ENDC}")

    def _get_password(self, prompt: str) -> str:
        """Get password input with colored prompt."""
        return getpass.getpass(f"{CLIColors.OKCYAN}{prompt}{CLIColors.ENDC}")

    def _select_user(self) -> Optional[User]:
        """Display list of users and allow selection of one."""
        try:
            from sqlalchemy.orm import joinedload

            users = self.session.query(User).options(joinedload(User.roles)).all()

            if not users:
                self._print_error("No users found in the database")
                return None

            print(f"\n{CLIColors.BOLD}Select User:{CLIColors.ENDC}")
            print(f"{'ID':<4} {'Username':<20} {'Email':<30} {'Roles'}")
            print("-" * 80)

            for user in users:
                roles = [role.name for role in user.roles]
                roles_str = ", ".join(roles) if roles else "None"
                print(
                    f"{user.id:<4} {user.username[:19]:<20} {user.email[:29]:<30} {roles_str}"
                )

            while True:
                try:
                    user_input = self._get_input(
                        "\nEnter user ID (or 'cancel' to cancel): "
                    )
                    if user_input.lower() == "cancel":
                        return None

                    user_id = int(user_input)
                    selected_user = next((u for u in users if u.id == user_id), None)

                    if selected_user:
                        return selected_user
                    else:
                        self._print_error("Invalid user ID. Please try again.")

                except ValueError:
                    self._print_error("Please enter a valid user ID or 'cancel'.")

        except Exception as e:
            self._print_error(f"Error selecting user: {str(e)}")
            return None

    def _pause(self):
        """Pause and wait for user input."""
        input(f"\n{CLIColors.OKBLUE}Press Enter to continue...{CLIColors.ENDC}")

    def _connect_database(self) -> bool:
        """Connect to the database."""
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            self._print_error("DATABASE_URL environment variable is not set")
            return False

        try:
            self.engine = create_engine(database_url)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()

            # Test connection
            self.session.execute(text("SELECT 1"))
            self._print_success("Connected to database successfully")
            return True

        except SQLAlchemyError as e:
            self._print_error(f"Database connection failed: {str(e)}")
            return False

    def _get_admin_user_context(self) -> Optional[User]:
        """Get an admin user context for operations (no authentication required)."""
        if not self.session:
            return None

        try:
            # First try to get super admin from environment variable
            super_admin_username = os.environ.get("SUPER_ADMIN_USERNAME")
            if super_admin_username:
                from sqlalchemy.orm import joinedload

                user = (
                    self.session.query(User)
                    .options(joinedload(User.roles))
                    .filter_by(username=super_admin_username)
                    .first()
                )
                if user:
                    self._print_info(
                        f"Operating as super admin: {super_admin_username}"
                    )
                    return user

            # Otherwise, find any admin user
            from sqlalchemy.orm import joinedload

            admin_role = self.session.query(Role).filter_by(name="admin").first()
            super_admin_role = (
                self.session.query(Role).filter_by(name="super-admin").first()
            )

            admin_user = None
            if super_admin_role:
                admin_user = (
                    self.session.query(User)
                    .options(joinedload(User.roles))
                    .filter(User.roles.contains(super_admin_role))
                    .first()
                )

            if not admin_user and admin_role:
                admin_user = (
                    self.session.query(User)
                    .options(joinedload(User.roles))
                    .filter(User.roles.contains(admin_role))
                    .first()
                )

            # Fallback to admin role
            if not admin_user:
                admin_users = (
                    self.session.query(User)
                    .join(User.roles)
                    .filter(Role.name == "admin")
                    .all()
                )
                if admin_users:
                    admin_user = admin_users[0]

            if admin_user:
                self._print_info(f"Operating as admin user: {admin_user.username}")
                return admin_user
            else:
                self._print_warning(
                    "No admin users found - operating with direct database access"
                )
                return None

        except Exception as e:
            self._print_warning(
                f"Error getting admin context: {str(e)} - operating with direct database access"
            )
            return None

    def _show_system_status(self):
        """Display system status information."""
        self._print_header("System Status")

        try:
            # Database info
            print(f"{CLIColors.BOLD}Database:{CLIColors.ENDC}")
            database_url = os.environ.get("DATABASE_URL", "Not configured")
            if "password" in database_url.lower():
                # Mask password in URL
                parts = database_url.split("@")
                if len(parts) > 1:
                    masked_url = parts[0].split(":")[:-1] + ["****@"] + parts[1:]
                    database_url = ":".join(masked_url)
            print(f"  URL: {database_url}")

            # User count
            user_count = self.session.query(User).count()
            print(f"  Users: {user_count}")

            # Mercury accounts
            mercury_account_count = self.session.query(MercuryAccount).count()
            active_mercury_accounts = (
                self.session.query(MercuryAccount).filter_by(is_active=True).count()
            )
            print(
                f"  Mercury Accounts: {active_mercury_accounts}/{mercury_account_count} active"
            )

            # Bank accounts
            account_count = self.session.query(Account).count()
            print(f"  Bank Accounts: {account_count}")

            # Transactions
            transaction_count = self.session.query(Transaction).count()
            recent_transactions = (
                self.session.query(Transaction)
                .filter(Transaction.posted_at >= datetime.now() - timedelta(days=7))
                .count()
            )
            print(
                f"  Transactions: {transaction_count} total, {recent_transactions} in last 7 days"
            )

            # Environment variables
            print(f"\n{CLIColors.BOLD}Environment:{CLIColors.ENDC}")
            print(
                f"  API URL: {os.environ.get('MERCURY_API_URL', 'https://api.mercury.com')}"
            )
            print(f"  Sandbox Mode: {os.environ.get('MERCURY_SANDBOX_MODE', 'false')}")
            print(
                f"  Sync Interval: {os.environ.get('SYNC_INTERVAL_MINUTES', '60')} minutes"
            )
            print(f"  Sync Days Back: {os.environ.get('SYNC_DAYS_BACK', '30')} days")

        except Exception as e:
            self._print_error(f"Error retrieving system status: {str(e)}")

    def _manage_mercury_accounts(self):
        """Manage Mercury accounts."""
        admin_context = self._get_admin_user_context()

        while True:
            self._print_header("Mercury Account Management")
            print("1. List Mercury accounts")
            print("2. Add Mercury account")
            print("3. Edit Mercury account")
            print("4. Enable/Disable account")
            print("5. Test API connection")
            print("6. Manage user access")
            print("7. Back to main menu")

            choice = self._get_input("\nSelect option (1-7): ")

            if choice == "1":
                self._list_mercury_accounts()
            elif choice == "2":
                self._add_mercury_account()
            elif choice == "3":
                self._edit_mercury_account()
            elif choice == "4":
                self._toggle_mercury_account()
            elif choice == "5":
                self._test_api_connection()
            elif choice == "6":
                self._manage_mercury_account_users()
            elif choice == "7":
                break
            else:
                self._print_error("Invalid choice")

            if choice != "7":
                self._pause()

    def _list_mercury_accounts(self):
        """List all Mercury accounts."""
        try:
            accounts = self.session.query(MercuryAccount).all()

            if not accounts:
                self._print_info("No Mercury accounts configured")
                return

            print(f"\n{CLIColors.BOLD}Mercury Accounts:{CLIColors.ENDC}")
            print(
                f"{'ID':<4} {'Name':<25} {'Status':<10} {'Sandbox':<8} {'Users':<6} {'Last Sync'}"
            )
            print("-" * 80)

            for account in accounts:
                status = "Active" if account.is_active else "Inactive"
                sandbox = "Yes" if account.sandbox_mode else "No"
                user_count = len(account.users)
                last_sync = (
                    account.last_sync_at.strftime("%Y-%m-%d %H:%M")
                    if account.last_sync_at
                    else "Never"
                )

                print(
                    f"{account.id:<4} {account.name[:24]:<25} {status:<10} {sandbox:<8} {user_count:<6} {last_sync}"
                )

            # Option to view account details
            while True:
                detail_input = self._get_input(
                    "\nEnter account ID to view details (or press Enter to skip): "
                )
                if not detail_input:
                    break

                try:
                    account_id = int(detail_input)
                    account = next((a for a in accounts if a.id == account_id), None)

                    if account:
                        self._view_mercury_account_details(account)
                        break
                    else:
                        self._print_error("Invalid account ID")
                except ValueError:
                    self._print_error("Please enter a valid ID or press Enter to skip")

        except Exception as e:
            self._print_error(f"Error listing Mercury accounts: {str(e)}")

    def _view_mercury_account_details(self, account: MercuryAccount):
        """View detailed information about a Mercury account."""
        try:
            self._print_header(f"Mercury Account: {account.name}")

            # Account information
            print(f"{CLIColors.BOLD}Account Information:{CLIColors.ENDC}")
            print(f"ID:              {account.id}")
            print(f"Name:            {account.name}")
            print(f"Status:          {'Active' if account.is_active else 'Inactive'}")
            print(f"Sync Enabled:    {'Yes' if account.sync_enabled else 'No'}")
            print(f"Sandbox Mode:    {'Yes' if account.sandbox_mode else 'No'}")
            print(f"Description:     {account.description or 'None'}")
            print(
                f"Created:         {account.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print(
                f"Last Sync:       {account.last_sync_at.strftime('%Y-%m-%d %H:%M:%S') if account.last_sync_at else 'Never'}"
            )
            print(f"Last Sync Status: {account.last_sync_status or 'N/A'}")

            # Associated users
            print(f"\n{CLIColors.BOLD}Associated Users:{CLIColors.ENDC}")
            if not account.users:
                print(
                    f"{CLIColors.WARNING}No users have access to this account{CLIColors.ENDC}"
                )
            else:
                print(f"{'ID':<4} {'Username':<20} {'Email':<30} {'Roles'}")
                print("-" * 80)
                for user in account.users:
                    roles = [role.name for role in user.roles]
                    roles_str = ", ".join(roles) if roles else "None"
                    print(
                        f"{user.id:<4} {user.username[:19]:<20} {user.email[:29]:<30} {roles_str}"
                    )

            # Mercury bank accounts
            print(f"\n{CLIColors.BOLD}Bank Accounts:{CLIColors.ENDC}")
            bank_accounts = (
                self.session.query(Account)
                .filter(Account.mercury_account_id == account.id)
                .all()
            )
            if not bank_accounts:
                print(
                    f"{CLIColors.WARNING}No bank accounts synchronized yet{CLIColors.ENDC}"
                )
            else:
                print(
                    f"{'ID':<4} {'Name':<25} {'Account Number':<20} {'Balance':<15} {'Currency':<8}"
                )
                print("-" * 80)
                for bank_account in bank_accounts:
                    # Mask account number for security
                    masked_account = (
                        f"{'*' * (len(bank_account.account_number) - 4)}{bank_account.account_number[-4:]}"
                        if bank_account.account_number
                        else "N/A"
                    )
                    balance = (
                        f"{bank_account.current_balance:.2f}"
                        if bank_account.current_balance is not None
                        else "N/A"
                    )
                    print(
                        f"{bank_account.id:<4} {bank_account.name[:24]:<25} {masked_account:<20} {balance:<15} {bank_account.currency_code or 'USD':<8}"
                    )

            # Get transaction counts
            transaction_count = (
                self.session.query(Transaction)
                .join(Account)
                .filter(Account.mercury_account_id == account.id)
                .count()
            )
            print(f"\nTotal transactions: {transaction_count}")

        except Exception as e:
            self._print_error(f"Error viewing account details: {str(e)}")

    def _add_mercury_account(self):
        """Add a new Mercury account."""
        print(f"\n{CLIColors.BOLD}Add Mercury Account{CLIColors.ENDC}")

        try:
            # First, select which user to add the account to
            selected_user = self._select_user()
            if not selected_user:
                self._print_info("Account creation cancelled")
                return

            print(
                f"\n{CLIColors.OKGREEN}Adding Mercury account for user: {selected_user.username}{CLIColors.ENDC}"
            )

            name = self._get_input("Account name: ")
            if not name:
                self._print_error("Account name is required")
                return

            api_key = self._get_password("API key: ")
            if not api_key:
                self._print_error("API key is required")
                return

            sandbox = self._get_input("Sandbox mode? (y/n): ").lower() == "y"
            description = self._get_input("Description (optional): ")

            # Create new Mercury account
            mercury_account = MercuryAccount(
                name=name,
                api_key=api_key,  # Will be encrypted automatically
                sandbox_mode=sandbox,
                description=description if description else None,
                is_active=True,
                sync_enabled=True,
            )

            # Associate the Mercury account with the selected user
            mercury_account.users.append(selected_user)

            self.session.add(mercury_account)
            self.session.commit()

            self._print_success(
                f"Mercury account '{name}' added successfully for user '{selected_user.username}'"
            )

        except Exception as e:
            self.session.rollback()
            self._print_error(f"Error adding Mercury account: {str(e)}")

    def _edit_mercury_account(self):
        """Edit an existing Mercury account."""
        self._list_mercury_accounts()

        try:
            account_id = int(self._get_input("\nEnter account ID to edit: "))
            account = (
                self.session.query(MercuryAccount)
                .filter(MercuryAccount.id == account_id)
                .first()
            )

            if not account:
                self._print_error("Account not found")
                return

            print(f"\n{CLIColors.BOLD}Editing: {account.name}{CLIColors.ENDC}")
            print(f"Current name: {account.name}")
            print(f"Current sandbox mode: {'Yes' if account.sandbox_mode else 'No'}")
            print(f"Current status: {'Active' if account.is_active else 'Inactive'}")

            # Update fields
            new_name = self._get_input(f"New name (current: {account.name}): ")
            if new_name:
                account.name = new_name

            new_api_key = self._get_password(
                "New API key (leave empty to keep current): "
            )
            if new_api_key:
                account.api_key = new_api_key

            sandbox_input = self._get_input(
                f"Sandbox mode (y/n, current: {'y' if account.sandbox_mode else 'n'}): "
            )
            if sandbox_input.lower() in ["y", "n"]:
                account.sandbox_mode = sandbox_input.lower() == "y"

            new_description = self._get_input(
                f"Description (current: {account.description or 'None'}): "
            )
            if new_description:
                account.description = new_description

            self.session.commit()
            self._print_success("Mercury account updated successfully")

        except ValueError:
            self._print_error("Invalid account ID")
        except Exception as e:
            self.session.rollback()
            self._print_error(f"Error editing Mercury account: {str(e)}")

    def _toggle_mercury_account(self):
        """Enable or disable a Mercury account."""
        self._list_mercury_accounts()

        try:
            account_id = int(self._get_input("\nEnter account ID to toggle: "))
            account = (
                self.session.query(MercuryAccount)
                .filter(MercuryAccount.id == account_id)
                .first()
            )

            if not account:
                self._print_error("Account not found")
                return

            old_status = "Active" if account.is_active else "Inactive"
            account.is_active = not account.is_active
            new_status = "Active" if account.is_active else "Inactive"

            self.session.commit()
            self._print_success(
                f"Account '{account.name}' changed from {old_status} to {new_status}"
            )

        except ValueError:
            self._print_error("Invalid account ID")
        except Exception as e:
            self.session.rollback()
            self._print_error(f"Error toggling Mercury account: {str(e)}")

    def _test_api_connection(self):
        """Test API connection for a Mercury account."""
        self._list_mercury_accounts()

        try:
            account_id = int(self._get_input("\nEnter account ID to test: "))
            account = (
                self.session.query(MercuryAccount)
                .filter(MercuryAccount.id == account_id)
                .first()
            )

            if not account:
                self._print_error("Account not found")
                return

            print(
                f"\n{CLIColors.BOLD}Testing API connection for: {account.name}{CLIColors.ENDC}"
            )

            # This would normally test the actual API connection
            # For now, just check if we can decrypt the API key
            try:
                api_key = account.get_decrypted_api_key()
                if api_key:
                    self._print_success("API key is properly encrypted and accessible")
                    self._print_info(
                        "Note: Full API connectivity test requires sync service"
                    )
                else:
                    self._print_error("Failed to decrypt API key")

            except Exception as e:
                self._print_error(f"API key test failed: {str(e)}")

        except ValueError:
            self._print_error("Invalid account ID")
        except Exception as e:
            self._print_error(f"Error testing API connection: {str(e)}")

    def _manage_mercury_account_users(self):
        """Manage user access to Mercury accounts."""
        try:
            # First, select which account to manage
            mercury_account = self._select_mercury_account()
            if not mercury_account:
                return

            while True:
                self._print_header(f"Manage Users for '{mercury_account.name}'")

                # Display current users
                print(f"\n{CLIColors.BOLD}Current Users:{CLIColors.ENDC}")
                if not mercury_account.users:
                    print(
                        f"{CLIColors.WARNING}No users have access to this account{CLIColors.ENDC}"
                    )
                else:
                    print(f"{'ID':<4} {'Username':<20} {'Email':<30}")
                    print("-" * 60)
                    for user in mercury_account.users:
                        print(
                            f"{user.id:<4} {user.username[:19]:<20} {user.email[:29]:<30}"
                        )

                print("\n1. Add user access")
                print("2. Remove user access")
                print("3. Back to Mercury account management")

                subchoice = self._get_input("\nSelect option (1-3): ")

                if subchoice == "1":
                    self._add_user_to_mercury_account(mercury_account)
                elif subchoice == "2":
                    self._remove_user_from_mercury_account(mercury_account)
                elif subchoice == "3":
                    break
                else:
                    self._print_error("Invalid choice")

        except Exception as e:
            self.session.rollback()
            self._print_error(f"Error managing user access: {str(e)}")

    def _select_mercury_account(self) -> Optional[MercuryAccount]:
        """Display list of Mercury accounts and allow selection of one."""
        try:
            self._list_mercury_accounts()

            while True:
                try:
                    account_input = self._get_input(
                        "\nEnter account ID (or 'cancel' to cancel): "
                    )
                    if account_input.lower() == "cancel":
                        return None

                    account_id = int(account_input)
                    account = (
                        self.session.query(MercuryAccount)
                        .filter(MercuryAccount.id == account_id)
                        .first()
                    )

                    if account:
                        return account
                    else:
                        self._print_error("Invalid account ID. Please try again.")

                except ValueError:
                    self._print_error("Please enter a valid account ID or 'cancel'.")

        except Exception as e:
            self._print_error(f"Error selecting account: {str(e)}")
            return None

    def _add_user_to_mercury_account(self, mercury_account: MercuryAccount):
        """Add a user to a Mercury account."""
        try:
            # First, get users who don't already have access
            current_user_ids = [user.id for user in mercury_account.users]
            available_users = (
                self.session.query(User).filter(User.id.notin_(current_user_ids)).all()
            )

            if not available_users:
                self._print_warning("All users already have access to this account")
                return

            print(f"\n{CLIColors.BOLD}Available Users:{CLIColors.ENDC}")
            print(f"{'ID':<4} {'Username':<20} {'Email':<30}")
            print("-" * 60)
            for user in available_users:
                print(f"{user.id:<4} {user.username[:19]:<20} {user.email[:29]:<30}")

            while True:
                try:
                    user_input = self._get_input(
                        "\nEnter user ID to add (or 'cancel' to cancel): "
                    )
                    if user_input.lower() == "cancel":
                        return

                    user_id = int(user_input)
                    selected_user = next(
                        (u for u in available_users if u.id == user_id), None
                    )

                    if selected_user:
                        # Add user to Mercury account
                        mercury_account.users.append(selected_user)
                        self.session.commit()
                        self._print_success(
                            f"User '{selected_user.username}' added to '{mercury_account.name}'"
                        )
                        return
                    else:
                        self._print_error("Invalid user ID. Please try again.")

                except ValueError:
                    self._print_error("Please enter a valid user ID or 'cancel'.")

        except Exception as e:
            self.session.rollback()
            self._print_error(f"Error adding user to account: {str(e)}")

    def _remove_user_from_mercury_account(self, mercury_account: MercuryAccount):
        """Remove a user from a Mercury account."""
        try:
            if not mercury_account.users:
                self._print_warning("No users have access to this account")
                return

            print(f"\n{CLIColors.BOLD}Current Users:{CLIColors.ENDC}")
            print(f"{'ID':<4} {'Username':<20} {'Email':<30}")
            print("-" * 60)
            for user in mercury_account.users:
                print(f"{user.id:<4} {user.username[:19]:<20} {user.email[:29]:<30}")

            while True:
                try:
                    user_input = self._get_input(
                        "\nEnter user ID to remove (or 'cancel' to cancel): "
                    )
                    if user_input.lower() == "cancel":
                        return

                    user_id = int(user_input)
                    selected_user = next(
                        (u for u in mercury_account.users if u.id == user_id), None
                    )

                    if selected_user:
                        # Check if this is the last user
                        if len(mercury_account.users) <= 1:
                            confirm = self._get_input(
                                f"{CLIColors.WARNING}This is the last user with access. Removing will leave the account inaccessible. Continue? (y/n): {CLIColors.ENDC}"
                            )
                            if confirm.lower() != "y":
                                self._print_info("Operation cancelled")
                                return

                        # Remove user from Mercury account
                        mercury_account.users.remove(selected_user)
                        self.session.commit()
                        self._print_success(
                            f"User '{selected_user.username}' removed from '{mercury_account.name}'"
                        )
                        return
                    else:
                        self._print_error("Invalid user ID. Please try again.")

                except ValueError:
                    self._print_error("Please enter a valid user ID or 'cancel'.")

        except Exception as e:
            self.session.rollback()
            self._print_error(f"Error removing user from account: {str(e)}")

    def _manage_users(self):
        """Manage users and roles."""
        admin_context = self._get_admin_user_context()

        while True:
            self._print_header("User Management")
            print("1. List users")
            print("2. Add user")
            print("3. Manage user roles")
            print("4. Reset user password")
            print("5. Lock/Unlock user")
            print("6. Back to main menu")

            choice = self._get_input("\nSelect option (1-6): ")

            if choice == "1":
                self._list_users()
            elif choice == "2":
                self._add_user()
            elif choice == "3":
                self._manage_user_roles()
            elif choice == "4":
                self._reset_user_password()
            elif choice == "5":
                self._toggle_user_lock()
            elif choice == "6":
                break
            else:
                self._print_error("Invalid choice")

            if choice != "6":
                self._pause()

    def _list_users(self):
        """List all users with their roles."""
        try:
            # Eagerly load users with their roles to avoid DetachedInstanceError
            from sqlalchemy.orm import joinedload

            users = self.session.query(User).options(joinedload(User.roles)).all()

            if not users:
                self._print_info("No users found")
                return

            print(f"\n{CLIColors.BOLD}Users:{CLIColors.ENDC}")
            print(f"{'ID':<4} {'Username':<20} {'Email':<30} {'Roles'}")
            print("-" * 80)

            for user in users:
                roles = [role.name for role in user.roles]
                roles_str = ", ".join(roles) if roles else "None"

                print(
                    f"{user.id:<4} {user.username[:19]:<20} {user.email[:29]:<30} {roles_str}"
                )

        except Exception as e:
            self._print_error(f"Error listing users: {str(e)}")

    def _add_user(self):
        """Add a new user."""
        print(f"\n{CLIColors.BOLD}Add User{CLIColors.ENDC}")

        try:
            username = self._get_input("Username: ")
            if not username:
                self._print_error("Username is required")
                return

            # Check if username exists
            existing_user = (
                self.session.query(User).filter_by(username=username).first()
            )
            if existing_user:
                self._print_error("Username already exists")
                return

            email = self._get_input("Email: ")
            if not email:
                self._print_error("Email is required")
                return

            password = self._get_password("Password: ")
            if not password:
                self._print_error("Password is required")
                return

            confirm_password = self._get_password("Confirm password: ")
            if password != confirm_password:
                self._print_error("Passwords do not match")
                return

            first_name = self._get_input("First name (optional): ")
            last_name = self._get_input("Last name (optional): ")

            # Create user
            new_user = User(
                username=username,
                email=email,
                first_name=first_name if first_name else None,
                last_name=last_name if last_name else None,
                is_active=True,
            )
            new_user.set_password(password)

            self.session.add(new_user)
            self.session.flush()  # Get user ID

            # Add basic user role
            user_role = self.session.query(Role).filter_by(name="user").first()
            if user_role:
                new_user.roles.append(user_role)

            # Create user settings
            user_settings = UserSettings(user_id=new_user.id)
            self.session.add(user_settings)

            self.session.commit()
            self._print_success(f"User '{username}' created successfully")

        except Exception as e:
            self.session.rollback()
            self._print_error(f"Error creating user: {str(e)}")

    def _manage_user_roles(self):
        """Manage roles for a specific user."""
        self._list_users()

        try:
            user_id = int(self._get_input("\nEnter user ID to manage: "))

            # Eagerly load user with roles to avoid DetachedInstanceError
            from sqlalchemy.orm import joinedload

            user = (
                self.session.query(User)
                .options(joinedload(User.roles))
                .filter(User.id == user_id)
                .first()
            )

            if not user:
                self._print_error("User not found")
                return

            print(
                f"\n{CLIColors.BOLD}Managing roles for: {user.username}{CLIColors.ENDC}"
            )

            # Show current roles
            current_roles = [role.name for role in user.roles]
            print(
                f"Current roles: {', '.join(current_roles) if current_roles else 'None'}"
            )

            # Show available roles
            all_roles = self.session.query(Role).all()
            print(f"\nAvailable roles:")
            for i, role in enumerate(all_roles, 1):
                status = "✓" if role.name in current_roles else " "
                print(f"  {i}. [{status}] {role.name} - {role.description}")

            print(f"\nActions:")
            print(f"  a. Add role")
            print(f"  r. Remove role")
            print(f"  q. Quit")

            action = self._get_input("Select action: ").lower()

            if action == "a":
                role_name = self._get_input("Enter role name to add: ")
                role = self.session.query(Role).filter_by(name=role_name).first()
                if role and role not in user.roles:
                    user.roles.append(role)
                    self.session.commit()
                    self._print_success(f"Role '{role_name}' added to {user.username}")
                else:
                    self._print_error("Role not found or already assigned")

            elif action == "r":
                role_name = self._get_input("Enter role name to remove: ")
                role = self.session.query(Role).filter_by(name=role_name).first()
                if role and role in user.roles:
                    user.roles.remove(role)
                    self.session.commit()
                    self._print_success(
                        f"Role '{role_name}' removed from {user.username}"
                    )
                else:
                    self._print_error("Role not found or not assigned")

        except ValueError:
            self._print_error("Invalid user ID")
        except Exception as e:
            self.session.rollback()
            self._print_error(f"Error managing user roles: {str(e)}")

    def _reset_user_password(self):
        """Reset a user's password."""
        self._list_users()

        try:
            user_id = int(self._get_input("\nEnter user ID for password reset: "))
            user = self.session.query(User).filter(User.id == user_id).first()

            if not user:
                self._print_error("User not found")
                return

            print(
                f"\n{CLIColors.BOLD}Reset password for: {user.username}{CLIColors.ENDC}"
            )

            new_password = self._get_password("New password: ")
            if not new_password:
                self._print_error("Password cannot be empty")
                return

            confirm_password = self._get_password("Confirm password: ")
            if new_password != confirm_password:
                self._print_error("Passwords do not match")
                return

            user.set_password(new_password)
            self.session.commit()

            self._print_success(f"Password reset for user '{user.username}'")

        except ValueError:
            self._print_error("Invalid user ID")
        except Exception as e:
            self.session.rollback()
            self._print_error(f"Error resetting password: {str(e)}")

    def _toggle_user_lock(self):
        """Lock or unlock a user account."""
        self._list_users()

        try:
            user_id = int(self._get_input("\nEnter user ID to lock/unlock: "))

            # Eagerly load user with roles to avoid DetachedInstanceError
            from sqlalchemy.orm import joinedload

            user = (
                self.session.query(User)
                .options(joinedload(User.roles))
                .filter(User.id == user_id)
                .first()
            )

            if not user:
                self._print_error("User not found")
                return

            # Check if user has locked role
            locked_role = self.session.query(Role).filter_by(name="locked").first()
            if not locked_role:
                self._print_error("Locked role not found in system")
                return

            is_locked = locked_role in user.roles

            if is_locked:
                user.roles.remove(locked_role)
                action = "unlocked"
            else:
                user.roles.append(locked_role)
                action = "locked"

            self.session.commit()
            self._print_success(f"User '{user.username}' has been {action}")

        except ValueError:
            self._print_error("Invalid user ID")
        except Exception as e:
            self.session.rollback()
            self._print_error(f"Error toggling user lock: {str(e)}")

    def _view_sync_logs(self):
        """View recent sync activity and logs."""
        self._print_header("Sync Activity")

        try:
            # Show recent transactions
            recent_transactions = (
                self.session.query(Transaction)
                .order_by(Transaction.posted_at.desc())
                .limit(10)
                .all()
            )

            if recent_transactions:
                print(f"{CLIColors.BOLD}Recent Transactions (Last 10):{CLIColors.ENDC}")
                print(
                    f"{'Date':<12} {'Amount':<12} {'Description'[:30]:<32} {'Account'}"
                )
                print("-" * 80)

                for txn in recent_transactions:
                    date_str = (
                        txn.posted_at.strftime("%Y-%m-%d")
                        if txn.posted_at
                        else "Unknown"
                    )
                    amount_str = f"${txn.amount:.2f}" if txn.amount else "N/A"
                    desc = (
                        (txn.description[:29] + "...")
                        if txn.description and len(txn.description) > 29
                        else (txn.description or "")
                    )
                    account_name = txn.account.name if txn.account else "Unknown"

                    print(f"{date_str:<12} {amount_str:<12} {desc:<32} {account_name}")
            else:
                self._print_info("No transactions found")

            # Show Mercury account sync status
            print(f"\n{CLIColors.BOLD}Mercury Account Sync Status:{CLIColors.ENDC}")
            mercury_accounts = self.session.query(MercuryAccount).all()

            for account in mercury_accounts:
                status = "Active" if account.is_active else "Inactive"
                last_sync = (
                    account.last_sync_at.strftime("%Y-%m-%d %H:%M")
                    if account.last_sync_at
                    else "Never"
                )
                print(f"  {account.name}: {status}, Last sync: {last_sync}")

            # Check for log files
            log_dir = "/app/logs"
            if os.path.exists(log_dir):
                print(f"\n{CLIColors.BOLD}Log Files:{CLIColors.ENDC}")
                log_files = [f for f in os.listdir(log_dir) if f.endswith(".log")]
                for log_file in log_files:
                    log_path = os.path.join(log_dir, log_file)
                    size = os.path.getsize(log_path)
                    modified = datetime.fromtimestamp(os.path.getmtime(log_path))
                    print(
                        f"  {log_file}: {size} bytes, modified {modified.strftime('%Y-%m-%d %H:%M')}"
                    )

        except Exception as e:
            self._print_error(f"Error viewing sync logs: {str(e)}")

    def _show_main_menu(self):
        """Display the main menu."""
        self._print_header("Mercury Bank Sync Service - CLI")
        print("1. System Status")
        print("2. Manage Mercury Accounts")
        print("3. Manage Bank Accounts")
        print("4. Manage Users")
        print("5. View Sync Activity")
        print("6. Database Tools")
        print("7. Exit")

    def _database_tools(self):
        """Database management tools."""
        admin_context = self._get_admin_user_context()

        while True:
            self._print_header("Database Tools")
            print("1. Create/update database schema")
            print("2. Check database schema")
            print("3. Backup database")
            print("4. View database statistics")
            print("5. Back to main menu")

            choice = self._get_input("\nSelect option (1-5): ")

            if choice == "1":
                self._create_schema()
            elif choice == "2":
                self._check_schema()
            elif choice == "3":
                self._backup_database()
            elif choice == "4":
                self._database_statistics()
            elif choice == "5":
                break
            else:
                self._print_error("Invalid choice")

            if choice != "5":
                self._pause()

    def _create_schema(self):
        """Create or update database schema using SQLAlchemy."""
        self._print_info("Creating/updating database schema...")

        try:
            from models.base import Base
            from sqlalchemy import create_engine
            import os

            database_url = os.environ.get("DATABASE_URL")
            if not database_url:
                self._print_error("DATABASE_URL environment variable not set")
                return

            engine = create_engine(database_url)
            Base.metadata.create_all(engine)

            self._print_success("Database schema created/updated successfully")

        except Exception as e:
            self._print_error(f"Error creating schema: {str(e)}")

    def _check_schema(self):
        """Check database schema."""
        try:
            # Check if all required tables exist
            required_tables = [
                "users",
                "user_settings",
                "roles",
                "user_role_association",
                "mercury_accounts",
                "accounts",
                "transactions",
                "system_settings",
                "receipt_policies",
            ]

            print(f"\n{CLIColors.BOLD}Database Schema Check:{CLIColors.ENDC}")

            for table in required_tables:
                try:
                    result = self.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    self._print_success(f"Table '{table}': {count} records")
                except Exception:
                    self._print_error(f"Table '{table}': Missing or inaccessible")

        except Exception as e:
            self._print_error(f"Error checking schema: {str(e)}")

    def _backup_database(self):
        """Create a database backup."""
        self._print_info("Database backup functionality would be implemented here")
        self._print_info("For now, use your database's native backup tools")

    def _database_statistics(self):
        """Show database statistics."""
        try:
            print(f"\n{CLIColors.BOLD}Database Statistics:{CLIColors.ENDC}")

            # Table row counts
            tables = {
                "users": User,
                "mercury_accounts": MercuryAccount,
                "accounts": Account,
                "transactions": Transaction,
                "roles": Role,
            }

            for table_name, model_class in tables.items():
                count = self.session.query(model_class).count()
                print(f"  {table_name}: {count:,} records")

            # Date ranges
            oldest_txn = (
                self.session.query(Transaction)
                .order_by(Transaction.posted_at.asc())
                .first()
            )
            newest_txn = (
                self.session.query(Transaction)
                .order_by(Transaction.posted_at.desc())
                .first()
            )

            if oldest_txn and newest_txn:
                print(f"\nTransaction date range:")
                print(f"  Oldest: {oldest_txn.posted_at.strftime('%Y-%m-%d')}")
                print(f"  Newest: {newest_txn.posted_at.strftime('%Y-%m-%d')}")

        except Exception as e:
            self._print_error(f"Error getting database statistics: {str(e)}")

    def _manage_bank_accounts(self):
        """Manage individual bank accounts within Mercury accounts."""
        admin_context = self._get_admin_user_context()

        while True:
            self._print_header("Bank Account Management")
            print("1. List all bank accounts")
            print("2. Edit bank account settings")
            print("3. Manage receipt policies")
            print("4. View receipt policy history")
            print("5. Back to main menu")

            choice = self._get_input("\nSelect option (1-5): ")

            if choice == "1":
                self._list_bank_accounts()
            elif choice == "2":
                self._edit_bank_account()
            elif choice == "3":
                self._manage_receipt_policy()
            elif choice == "4":
                self._view_receipt_policy_history()
            elif choice == "5":
                break
            else:
                self._print_error("Invalid choice")

            if choice != "5":
                self._pause()

    def _list_bank_accounts(self):
        """List all bank accounts from all Mercury accounts."""
        try:
            accounts = self.session.query(Account).all()

            if not accounts:
                self._print_info("No bank accounts found")
                return

            print(f"\n{CLIColors.BOLD}Bank Accounts:{CLIColors.ENDC}")
            print(
                f"{'ID':<32} {'Name':<25} {'Type':<12} {'Balance':<12} {'Receipt Policy'}"
            )
            print("-" * 100)

            for account in accounts:
                # Format receipt policy display
                if account.receipt_required_deposits == "none" and account.receipt_required_charges == "none":
                    receipt_policy = "None required"
                elif account.receipt_required_deposits == "always" and account.receipt_required_charges == "always":
                    receipt_policy = "Always required"
                else:
                    deposit_policy = "None"
                    charge_policy = "None"
                    
                    if account.receipt_required_deposits == "always":
                        deposit_policy = "Always"
                    elif account.receipt_required_deposits == "threshold":
                        deposit_policy = f">${account.receipt_threshold_deposits}"
                    
                    if account.receipt_required_charges == "always":
                        charge_policy = "Always"
                    elif account.receipt_required_charges == "threshold":
                        charge_policy = f">${account.receipt_threshold_charges}"
                        
                    receipt_policy = f"Deposits: {deposit_policy}, Charges: {charge_policy}"
                
                print(
                    f"{account.id:<32} {account.name[:24]:<25} {account.account_type or 'N/A':<12} "
                    f"${account.balance or 0:<11.2f} {receipt_policy}"
                )

        except Exception as e:
            self._print_error(f"Error listing bank accounts: {str(e)}")
            
    def _edit_bank_account(self):
        """Edit basic bank account settings."""
        try:
            self._list_bank_accounts()
            
            account_id = self._get_input("\nEnter account ID to edit (or 'cancel'): ")
            if account_id.lower() == "cancel":
                return
                
            account = self.session.query(Account).filter_by(id=account_id).first()
            if not account:
                self._print_error("Account not found")
                return
                
            self._print_header(f"Edit Bank Account: {account.name}")
            
            # Allow editing basic account settings
            new_name = self._get_input(f"Name (current: {account.name}): ")
            if new_name:
                account.name = new_name
                
            new_nickname = self._get_input(f"Nickname (current: {account.nickname or 'None'}): ")
            if new_nickname:
                account.nickname = new_nickname
                
            exclude_input = self._get_input(
                f"Exclude from reports (y/n, current: {'y' if account.exclude_from_reports else 'n'}): "
            )
            if exclude_input.lower() in ["y", "n"]:
                account.exclude_from_reports = exclude_input.lower() == "y"
                
            self.session.commit()
            self._print_success(f"Bank account '{account.name}' updated successfully")
            
        except Exception as e:
            self.session.rollback()
            self._print_error(f"Error editing bank account: {str(e)}")
            
    def _manage_receipt_policy(self):
        """Update receipt policy for a bank account."""
        try:
            self._list_bank_accounts()
            
            account_id = self._get_input("\nEnter account ID to manage receipt policy (or 'cancel'): ")
            if account_id.lower() == "cancel":
                return
                
            account = self.session.query(Account).filter_by(id=account_id).first()
            if not account:
                self._print_error("Account not found")
                return
                
            self._print_header(f"Manage Receipt Policy: {account.name}")
            
            # Show current settings
            print(f"\n{CLIColors.BOLD}Current Receipt Settings:{CLIColors.ENDC}")
            print(f"  Deposits: {account.receipt_required_deposits} "
                  f"({f'${account.receipt_threshold_deposits}' if account.receipt_threshold_deposits else 'N/A'})")
            print(f"  Charges: {account.receipt_required_charges} "
                  f"({f'${account.receipt_threshold_charges}' if account.receipt_threshold_charges else 'N/A'})")
            
            print(f"\n{CLIColors.BOLD}Update Receipt Policy:{CLIColors.ENDC}")
            print("Receipt Requirements: 'none', 'always', or 'threshold'")
            
            # Get new deposit receipt settings
            new_deposit_policy = self._get_input("Deposit receipt requirement (none/always/threshold): ")
            if new_deposit_policy not in ["none", "always", "threshold"]:
                self._print_error("Invalid deposit receipt requirement")
                return
                
            new_deposit_threshold = None
            if new_deposit_policy == "threshold":
                threshold_input = self._get_input("Deposit threshold amount ($): ")
                try:
                    new_deposit_threshold = float(threshold_input)
                except ValueError:
                    self._print_error("Invalid threshold amount")
                    return
            
            # Get new charge receipt settings
            new_charge_policy = self._get_input("Charge receipt requirement (none/always/threshold): ")
            if new_charge_policy not in ["none", "always", "threshold"]:
                self._print_error("Invalid charge receipt requirement")
                return
                
            new_charge_threshold = None
            if new_charge_policy == "threshold":
                threshold_input = self._get_input("Charge threshold amount ($): ")
                try:
                    new_charge_threshold = float(threshold_input)
                except ValueError:
                    self._print_error("Invalid threshold amount")
                    return
            
            # Create a new receipt policy history record
            account.update_receipt_policy(
                receipt_required_deposits=new_deposit_policy,
                receipt_threshold_deposits=new_deposit_threshold,
                receipt_required_charges=new_charge_policy,
                receipt_threshold_charges=new_charge_threshold
            )
            
            self.session.commit()
            self._print_success("Receipt policy updated successfully")
            
        except Exception as e:
            self.session.rollback()
            self._print_error(f"Error updating receipt policy: {str(e)}")
            
    def _view_receipt_policy_history(self):
        """View the history of receipt policies for a bank account."""
        try:
            self._list_bank_accounts()
            
            account_id = self._get_input("\nEnter account ID to view receipt policy history (or 'cancel'): ")
            if account_id.lower() == "cancel":
                return
                
            account = self.session.query(Account).filter_by(id=account_id).first()
            if not account:
                self._print_error("Account not found")
                return
                
            # Import here to avoid circular imports
            from models.receipt_policy import ReceiptPolicy
            
            # Get all receipt policies for this account, ordered by date
            policies = (
                self.session.query(ReceiptPolicy)
                .filter_by(account_id=account.id)
                .order_by(ReceiptPolicy.start_date.desc())
                .all()
            )
            
            if not policies:
                self._print_info(f"No receipt policy history found for '{account.name}'")
                return
                
            self._print_header(f"Receipt Policy History: {account.name}")
            
            print(f"\n{'Start Date':<20} {'End Date':<20} {'Deposits':<30} {'Charges':<30}")
            print("-" * 100)
            
            for policy in policies:
                # Format policy display
                deposit_policy = policy.receipt_required_deposits
                if deposit_policy == "threshold":
                    deposit_policy = f"threshold (${policy.receipt_threshold_deposits})"
                    
                charge_policy = policy.receipt_required_charges
                if charge_policy == "threshold":
                    charge_policy = f"threshold (${policy.receipt_threshold_charges})"
                
                end_date = policy.end_date.strftime("%Y-%m-%d %H:%M") if policy.end_date else "Current"
                
                print(
                    f"{policy.start_date.strftime('%Y-%m-%d %H:%M'):<20} "
                    f"{end_date:<20} "
                    f"{deposit_policy:<30} "
                    f"{charge_policy:<30}"
                )
                
        except Exception as e:
            self._print_error(f"Error viewing receipt policy history: {str(e)}")

    def run(self):
        """Main application loop."""
        # Print welcome message
        self._print_header("Mercury Bank Sync Service")
        self._print_info("Command-Line Interface")
        print(
            f"{CLIColors.OKCYAN}Use this interface when the web GUI is not available{CLIColors.ENDC}"
        )

        # Connect to database
        if not self._connect_database():
            self._print_error("Cannot continue without database connection")
            return

        # Main loop
        while self.running:
            try:
                self._show_main_menu()
                choice = self._get_input("\nSelect option (1-7): ")

                if choice == "1":
                    self._show_system_status()
                    self._pause()
                elif choice == "2":
                    self._manage_mercury_accounts()
                elif choice == "3":
                    self._manage_bank_accounts()
                elif choice == "4":
                    self._manage_users()
                elif choice == "5":
                    self._view_sync_logs()
                    self._pause()
                elif choice == "6":
                    self._database_tools()
                elif choice == "7":
                    self._print_info("Goodbye!")
                    break
                else:
                    self._print_error("Invalid choice. Please select 1-7.")
                    self._pause()

            except KeyboardInterrupt:
                print(f"\n{CLIColors.WARNING}Exiting...{CLIColors.ENDC}")
                break
            except Exception as e:
                self._print_error(f"Unexpected error: {str(e)}")
                self._pause()

        # Cleanup
        if self.session:
            self.session.close()


def main():
    """Main entry point."""
    cli = MercurySyncCLI()
    cli.run()


if __name__ == "__main__":
    main()
