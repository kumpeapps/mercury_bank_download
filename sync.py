#!/usr/bin/env python3
"""
Mercury Bank Data Synchronization Service

This script synchronizes accounts and transactions from Mercury Bank API
to a local database using SQLAlchemy.
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime, timedelta

from mercury_bank_api import MercuryBankAPIClient  # type: ignore[import]
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from models import Account, Transaction, MercuryAccount
from models.base import create_engine_and_session, init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/app/logs/sync.log"),
    ],
)

logger = logging.getLogger(__name__)


class MercuryBankSyncer:
    """
    Mercury Bank API synchronization service.

    This class handles synchronization of accounts and transactions from the Mercury Bank API
    to a local database. It iterates through all active Mercury account groups and syncs
    data for each one. It provides methods to sync accounts, transactions, and run complete
    synchronization cycles.

    Attributes:
        engine: SQLAlchemy database engine
        session_local: SQLAlchemy session factory
    """

    def __init__(self):
        """
        Initialize the Mercury Bank syncer.

        Sets up the database connection and initializes database tables.
        No longer requires a single API key as it will iterate through all
        Mercury account groups stored in the database.
        """
        # Initialize database
        self.engine, self.session_local = create_engine_and_session()
        init_db()

        logger.info("Mercury Bank Syncer initialized")

    def _safe_get(self, obj, key, default=None):
        """
        Safely get a value from either a dictionary or an object.

        Args:
            obj: Dictionary or object to extract value from
            key: Key/attribute name to extract
            default: Default value if key/attribute not found

        Returns:
            The value or default if not found
        """
        if hasattr(obj, "get") and callable(getattr(obj, "get")):
            # It's a dictionary-like object
            return obj.get(key, default)
        elif hasattr(obj, key):
            # It's an object with attributes
            return getattr(obj, key, default)
        else:
            return default

    def get_db_session(self) -> Session:
        """
        Get a database session.

        Returns:
            Session: SQLAlchemy database session instance
        """
        return self.session_local()

    def sync_accounts(self) -> int:
        """
        Sync accounts from Mercury Bank API to database for all active Mercury account groups.

        Iterates through all active MercuryAccount groups, fetches accounts from each
        Mercury Bank API, and synchronizes them with the local database. Creates new 
        accounts if they don't exist, or updates existing accounts with the latest data.

        Returns:
            int: Total number of accounts successfully synchronized across all groups

        Raises:
            SQLAlchemyError: If database operations fail
            Exception: If API calls or other operations fail
        """
        logger.info("Starting account synchronization for all Mercury account groups...")

        db = self.get_db_session()
        total_synced_count = 0

        try:
            # Get all active Mercury account groups
            mercury_accounts = db.query(MercuryAccount).filter(
                MercuryAccount.is_active == True,
                MercuryAccount.sync_enabled == True
            ).all()

            if not mercury_accounts:
                logger.warning("No active Mercury account groups found for synchronization")
                return 0

            logger.info("Found %d active Mercury account groups", len(mercury_accounts))

            for mercury_account in mercury_accounts:
                logger.info("Syncing accounts for group: %s", mercury_account.name)
                
                try:
                    # Create API client for this Mercury account group
                    mercury_api = MercuryBankAPIClient(
                        api_token=mercury_account.api_key,
                        sandbox=mercury_account.sandbox_mode
                    )

                    # Fetch accounts from Mercury API
                    accounts_data = mercury_api.get_accounts()
                    synced_count = 0

                    for account_data in accounts_data:
                        account_id = self._safe_get(account_data, "id")
                        if not account_id:
                            logger.warning("Skipping account without ID: %s", account_data)
                            continue

                        # Check if account exists
                        existing_account = (
                            db.query(Account).filter(Account.id == account_id).first()
                        )

                        if existing_account:
                            # Update existing account
                            existing_account.mercury_account_id = mercury_account.id
                            existing_account.name = self._safe_get(
                                account_data, "name", existing_account.name
                            )
                            existing_account.account_number = (
                                self._safe_get(account_data, "accountNumber")
                                or existing_account.account_number
                            )
                            existing_account.routing_number = self._safe_get(
                                account_data,
                                "routingNumber",
                                existing_account.routing_number,
                            )
                            existing_account.account_type = self._safe_get(
                                account_data, "type", existing_account.account_type
                            )
                            existing_account.status = self._safe_get(
                                account_data, "status", existing_account.status
                            )
                            existing_account.balance = self._safe_get(
                                account_data, "currentBalance", existing_account.balance
                            )
                            existing_account.available_balance = self._safe_get(
                                account_data,
                                "availableBalance",
                                existing_account.available_balance,
                            )
                            existing_account.currency = self._safe_get(
                                account_data, "currency", existing_account.currency
                            )
                            existing_account.kind = self._safe_get(
                                account_data, "kind", existing_account.kind
                            )
                            existing_account.nickname = self._safe_get(
                                account_data, "nickname", existing_account.nickname
                            )
                            existing_account.legal_business_name = self._safe_get(
                                account_data,
                                "legalBusinessName",
                                existing_account.legal_business_name,
                            )

                            logger.info("Updated account: %s", account_id)
                        else:
                            # Create new account
                            new_account = Account(
                                id=account_id,
                                mercury_account_id=mercury_account.id,
                                name=self._safe_get(account_data, "name", ""),
                                account_number=self._safe_get(
                                    account_data, "accountNumber"
                                ),
                                routing_number=self._safe_get(
                                    account_data, "routingNumber"
                                ),
                                account_type=self._safe_get(account_data, "type"),
                                status=self._safe_get(account_data, "status"),
                                balance=self._safe_get(account_data, "currentBalance"),
                                available_balance=self._safe_get(
                                    account_data, "availableBalance"
                                ),
                                currency=self._safe_get(account_data, "currency", "USD"),
                                kind=self._safe_get(account_data, "kind"),
                                nickname=self._safe_get(account_data, "nickname"),
                                legal_business_name=self._safe_get(
                                    account_data, "legalBusinessName"
                                ),
                            )
                            db.add(new_account)
                            logger.info("Created new account: %s", account_id)

                        synced_count += 1

                    total_synced_count += synced_count
                    
                    logger.info("Successfully synced %d accounts for group: %s", synced_count, mercury_account.name)

                except (ValueError, SQLAlchemyError) as e:
                    logger.error("Error syncing accounts for group %s: %s", mercury_account.name, e)
                    continue  # Continue with next Mercury account group

            db.commit()
            logger.info("Total accounts synced across all groups: %d", total_synced_count)
            return total_synced_count

        except SQLAlchemyError as e:
            db.rollback()
            logger.error("Database error during account sync: %s", e)
            raise
        except Exception as e:
            db.rollback()
            logger.error("Unexpected error during account sync: %s", e)
            raise
        finally:
            db.close()

    def sync_transactions(self, days_back: int = 30) -> int:
        """
        Sync transactions from Mercury Bank API to database.

        Fetches transactions for all accounts within the specified date range and
        synchronizes them with the local database. Creates new transactions if they
        don't exist, or updates existing transactions with the latest data from the API.

        Args:
            days_back (int, optional): Number of days back from today to sync transactions.
                Defaults to 30.

        Returns:
            int: Total number of transactions successfully synchronized across all accounts

        Raises:
            SQLAlchemyError: If database operations fail
            ValueError: If date parsing or other value operations fail
            Exception: If API calls or other operations fail
        """
        logger.info(
            "Starting transaction synchronization for last %d days...", days_back
        )

        try:
            # Get date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)

            # Get all accounts from database
            db = self.get_db_session()
            accounts = db.query(Account).all()
            total_synced = 0

            try:
                for account in accounts:
                    logger.info("Syncing transactions for account: %s", account.id)

                    # Skip accounts without a mercury_account_id
                    if not account.mercury_account_id:
                        logger.warning("Account %s has no mercury_account_id, skipping", account.id)
                        continue

                    # Get the Mercury account group for this account
                    mercury_account = db.query(MercuryAccount).filter(
                        MercuryAccount.id == account.mercury_account_id,
                        MercuryAccount.is_active == True,
                        MercuryAccount.sync_enabled == True
                    ).first()

                    if not mercury_account:
                        logger.warning("No active Mercury account group found for account %s", account.id)
                        continue

                    try:
                        # Create API client for this Mercury account group
                        mercury_api = MercuryBankAPIClient(
                            api_token=mercury_account.api_key,
                            sandbox=mercury_account.sandbox_mode
                        )

                        # Try to get transactions using the library first
                        try:
                            transactions_data_raw = mercury_api.get_transactions(
                                account_id=account.id,
                                start_date=start_date.isoformat(),
                                end_date=end_date.isoformat(),
                            )

                            # Handle case where transactions_data_raw has transactions attribute
                            if hasattr(transactions_data_raw, "transactions"):
                                transactions_data = transactions_data_raw.transactions
                            else:
                                transactions_data = transactions_data_raw

                        except (ValueError, SQLAlchemyError) as lib_error:
                            logger.warning(
                                "Mercury library failed for account %s: %s. Skipping account.",
                                account.id,
                                str(lib_error),
                            )
                            continue

                        # Ensure transactions_data is iterable
                        if not isinstance(transactions_data, (list, tuple)):
                            logger.warning(
                                "Transactions data is not iterable for account %s",
                                account.id,
                            )
                            continue

                        account_synced = 0

                        # Process each transaction
                        # pylint: disable=not-an-iterable
                        for transaction_data in transactions_data:
                            transaction_id = self._safe_get(transaction_data, "id")
                            if not transaction_id:
                                logger.warning(
                                    "Skipping transaction without ID: %s",
                                    transaction_data,
                                )
                                continue

                            # Check if transaction exists
                            existing_transaction = (
                                db.query(Transaction)
                                .filter(Transaction.id == transaction_id)
                                .first()
                            )

                            # Parse dates - using correct camelCase field names from Mercury API
                            posted_at = None
                            estimated_delivery_date = None
                            failed_at = None
                            created_at = None

                            # Handle postedAt field
                            posted_at_raw = self._safe_get(transaction_data, "postedAt")
                            if posted_at_raw:
                                try:
                                    if isinstance(posted_at_raw, datetime):
                                        posted_at = posted_at_raw
                                    else:
                                        posted_at = datetime.fromisoformat(
                                            str(posted_at_raw).replace("Z", "+00:00")
                                        )
                                except (ValueError, TypeError):
                                    logger.warning(
                                        "Invalid postedAt date format for transaction %s: %s",
                                        transaction_id,
                                        posted_at_raw,
                                    )

                            # Handle estimatedDeliveryDate field
                            delivery_date_raw = self._safe_get(
                                transaction_data, "estimatedDeliveryDate"
                            )
                            if delivery_date_raw:
                                try:
                                    if isinstance(delivery_date_raw, datetime):
                                        estimated_delivery_date = delivery_date_raw
                                    else:
                                        estimated_delivery_date = (
                                            datetime.fromisoformat(
                                                str(delivery_date_raw).replace(
                                                    "Z", "+00:00"
                                                )
                                            )
                                        )
                                except (ValueError, TypeError):
                                    logger.warning(
                                        "Invalid estimatedDeliveryDate format for transaction %s: %s",
                                        transaction_id,
                                        delivery_date_raw,
                                    )

                            # Handle failedAt field
                            failed_at_raw = self._safe_get(transaction_data, "failedAt")
                            if failed_at_raw:
                                try:
                                    if isinstance(failed_at_raw, datetime):
                                        failed_at = failed_at_raw
                                    else:
                                        failed_at = datetime.fromisoformat(
                                            str(failed_at_raw).replace("Z", "+00:00")
                                        )
                                except (ValueError, TypeError):
                                    logger.warning(
                                        "Invalid failedAt date format for transaction %s: %s",
                                        transaction_id,
                                        failed_at_raw,
                                    )

                            # Handle createdAt field
                            created_at_raw = self._safe_get(
                                transaction_data, "createdAt"
                            )
                            if created_at_raw:
                                try:
                                    if isinstance(created_at_raw, datetime):
                                        created_at = created_at_raw
                                    else:
                                        created_at = datetime.fromisoformat(
                                            str(created_at_raw).replace("Z", "+00:00")
                                        )
                                except (ValueError, TypeError):
                                    logger.warning(
                                        "Invalid createdAt date format for transaction %s: %s",
                                        transaction_id,
                                        created_at_raw,
                                    )

                            if existing_transaction:
                                # Update existing transaction with correct Mercury API field names
                                existing_transaction.amount = self._safe_get(
                                    transaction_data,
                                    "amount",
                                    existing_transaction.amount,
                                )
                                existing_transaction.currency = self._safe_get(
                                    transaction_data,
                                    "currency",
                                    existing_transaction.currency,
                                )
                                existing_transaction.description = self._safe_get(
                                    transaction_data,
                                    "description",
                                    existing_transaction.description,
                                )
                                existing_transaction.bank_description = self._safe_get(
                                    transaction_data,
                                    "bankDescription",
                                    existing_transaction.bank_description,
                                )
                                existing_transaction.external_memo = self._safe_get(
                                    transaction_data,
                                    "externalMemo",
                                    existing_transaction.external_memo,
                                )
                                existing_transaction.note = self._safe_get(
                                    transaction_data, "note", existing_transaction.note
                                )
                                existing_transaction.transaction_type = self._safe_get(
                                    transaction_data,
                                    "type",
                                    existing_transaction.transaction_type,
                                )
                                existing_transaction.kind = self._safe_get(
                                    transaction_data, "kind", existing_transaction.kind
                                )
                                existing_transaction.status = self._safe_get(
                                    transaction_data,
                                    "status",
                                    existing_transaction.status,
                                )
                                existing_transaction.category = self._safe_get(
                                    transaction_data,
                                    "category",
                                    existing_transaction.category,
                                )
                                existing_transaction.mercury_category = self._safe_get(
                                    transaction_data,
                                    "mercuryCategory",
                                    existing_transaction.mercury_category,
                                )
                                existing_transaction.counterparty_name = self._safe_get(
                                    transaction_data,
                                    "counterpartyName",
                                    existing_transaction.counterparty_name,
                                )
                                existing_transaction.counterparty_nickname = (
                                    self._safe_get(
                                        transaction_data,
                                        "counterpartyNickname",
                                        existing_transaction.counterparty_nickname,
                                    )
                                )
                                existing_transaction.counterparty_account = (
                                    self._safe_get(
                                        transaction_data,
                                        "counterpartyAccount",
                                        existing_transaction.counterparty_account,
                                    )
                                )
                                existing_transaction.reference_number = self._safe_get(
                                    transaction_data,
                                    "referenceNumber",
                                    existing_transaction.reference_number,
                                )
                                existing_transaction.reason_for_failure = (
                                    self._safe_get(
                                        transaction_data,
                                        "reasonForFailure",
                                        existing_transaction.reason_for_failure,
                                    )
                                )
                                existing_transaction.has_generated_receipt = bool(  # type: ignore[assignment]
                                    self._safe_get(
                                        transaction_data,
                                        "hasGeneratedReceipt",
                                        existing_transaction.has_generated_receipt,
                                    )
                                )
                                existing_transaction.number_of_attachments = int(  # type: ignore[assignment]
                                    self._safe_get(
                                        transaction_data,
                                        "numberOfAttachments",
                                        existing_transaction.number_of_attachments,
                                    )
                                    or 0
                                )

                                # Update dates if provided
                                if posted_at:
                                    existing_transaction.posted_at = posted_at  # type: ignore[assignment]
                                if estimated_delivery_date:
                                    existing_transaction.estimated_delivery_date = estimated_delivery_date  # type: ignore[assignment]
                                if failed_at:
                                    existing_transaction.failed_at = failed_at  # type: ignore[assignment]
                                if created_at:
                                    existing_transaction.created_at = created_at  # type: ignore[assignment]

                                logger.debug("Updated transaction: %s", transaction_id)
                            else:
                                # Create new transaction
                                new_transaction = Transaction(
                                    id=transaction_id,
                                    account_id=account.id,
                                    amount=float(
                                        self._safe_get(transaction_data, "amount") or 0
                                    ),
                                    currency=self._safe_get(
                                        transaction_data, "currency"
                                    )
                                    or "USD",
                                    description=self._safe_get(
                                        transaction_data, "description"
                                    )
                                    or "",
                                    bank_description=self._safe_get(
                                        transaction_data, "bankDescription"
                                    ),
                                    external_memo=self._safe_get(
                                        transaction_data, "externalMemo"
                                    ),
                                    note=self._safe_get(transaction_data, "note"),
                                    transaction_type=self._safe_get(
                                        transaction_data, "type"
                                    ),
                                    kind=self._safe_get(transaction_data, "kind"),
                                    status=self._safe_get(transaction_data, "status"),
                                    category=self._safe_get(
                                        transaction_data, "category"
                                    ),
                                    mercury_category=self._safe_get(
                                        transaction_data, "mercuryCategory"
                                    ),
                                    counterparty_name=self._safe_get(
                                        transaction_data, "counterpartyName"
                                    ),
                                    counterparty_nickname=self._safe_get(
                                        transaction_data, "counterpartyNickname"
                                    ),
                                    counterparty_account=self._safe_get(
                                        transaction_data, "counterpartyAccount"
                                    ),
                                    reference_number=self._safe_get(
                                        transaction_data, "referenceNumber"
                                    ),
                                    reason_for_failure=self._safe_get(
                                        transaction_data, "reasonForFailure"
                                    ),
                                    has_generated_receipt=bool(
                                        self._safe_get(
                                            transaction_data, "hasGeneratedReceipt"
                                        )
                                    ),
                                    number_of_attachments=int(
                                        self._safe_get(
                                            transaction_data, "numberOfAttachments"
                                        )
                                        or 0
                                    ),
                                    posted_at=posted_at,
                                    estimated_delivery_date=estimated_delivery_date,
                                    failed_at=failed_at,
                                    created_at=created_at,
                                )
                                db.add(new_transaction)
                                logger.debug(
                                    "Created new transaction: %s", transaction_id
                                )

                            account_synced += 1

                        logger.info(
                            "Synced %d transactions for account %s",
                            account_synced,
                            account.id,
                        )
                        total_synced += account_synced

                    except (SQLAlchemyError, ValueError) as e:
                        logger.error(
                            "Error syncing transactions for account %s: %s",
                            account.id,
                            e,
                        )
                        continue

                db.commit()
                logger.info("Successfully synced %d transactions total", total_synced)
                return total_synced

            except SQLAlchemyError as e:
                db.rollback()
                logger.error("Database error during transaction sync: %s", e)
                raise
            except Exception as e:
                db.rollback()
                logger.error("Unexpected error during transaction sync: %s", e)
                raise
            finally:
                db.close()

        except Exception as e:
            logger.error("Failed to sync transactions: %s", e)
            raise

    def run_sync(self, days_back: int = 30):
        """
        Run complete synchronization process.

        Executes a full synchronization cycle by first syncing accounts, then syncing
        transactions for the specified number of days back. This is the main method
        to perform a complete data synchronization.

        Args:
            days_back (int, optional): Number of days back from today to sync transactions.
                Defaults to 30.

        Raises:
            Exception: If either account or transaction synchronization fails
        """
        logger.info("Starting complete Mercury Bank synchronization...")

        try:
            # Sync accounts first
            accounts_synced = self.sync_accounts()

            # Then sync transactions
            transactions_synced = self.sync_transactions(days_back=days_back)

            logger.info(
                "Synchronization completed successfully. "
                "Accounts: %d, Transactions: %d",
                accounts_synced,
                transactions_synced,
            )

        except Exception as e:
            logger.error("Synchronization failed: %s", e)
            raise


def main():
    """
    Main entry point for the Mercury Bank synchronization service.

    Configures the synchronization service based on environment variables and runs
    either a one-time sync or continuous sync loop. Handles graceful shutdown on
    interrupt signals and implements retry logic for transient errors.

    Environment Variables:
        SYNC_DAYS_BACK (str): Number of days back to sync transactions (default: 30)
        SYNC_INTERVAL_MINUTES (str): Interval between sync runs in minutes (default: 60)
        RUN_ONCE (str): If 'true', runs sync once and exits (default: false)

    Raises:
        SystemExit: Exits with code 1 if syncer initialization fails
    """
    try:
        # Get configuration from environment
        days_back = int(os.getenv("SYNC_DAYS_BACK", "30"))
        sync_interval = int(os.getenv("SYNC_INTERVAL_MINUTES", "60"))
        run_once = os.getenv("RUN_ONCE", "false").lower() == "true"

        syncer = MercuryBankSyncer()

        if run_once:
            logger.info("Running synchronization once...")
            syncer.run_sync(days_back=days_back)
        else:
            logger.info("Starting continuous sync every %d minutes...", sync_interval)
            while True:
                try:
                    syncer.run_sync(days_back=days_back)
                    logger.info("Sleeping for %d minutes...", sync_interval)
                    time.sleep(sync_interval * 60)
                except (KeyboardInterrupt, SystemExit):
                    logger.info("Received interrupt signal, shutting down...")
                    break
                except (ValueError, SQLAlchemyError) as e:
                    logger.error("Sync error: %s", e)
                    logger.info("Waiting 5 minutes before retry...")
                    time.sleep(5 * 60)
                except Exception as e:
                    logger.error("Unexpected error during sync: %s", e)
                    logger.info("Waiting 5 minutes before retry...")
                    time.sleep(5 * 60)

    except (ValueError, OSError) as e:
        logger.error("Failed to start syncer: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
