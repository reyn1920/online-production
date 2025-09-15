#!/usr / bin / env python3
""""""
TRAE.AI Secrets Management CLI

Command - line interface for managing encrypted secrets in the TRAE.AI system.
Provides secure operations for adding, retrieving, listing, and deleting secrets.

Usage:
    python scripts / secrets_cli.py add <key_name> <secret_value>
    python scripts / secrets_cli.py get <key_name>
    python scripts / secrets_cli.py list
    python scripts / secrets_cli.py delete <key_name>
    python scripts / secrets_cli.py exists <key_name>
    python scripts / secrets_cli.py backup <backup_path>

Environment Variables:
    TRAE_MASTER_KEY: Master password for encryption (required)
    TRAE_SECRETS_DB: Path to secrets database (optional,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     defaults to data / secrets.sqlite)

Author: TRAE.AI System
Version: 1.0.0
""""""

import argparse
import getpass
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.secret_store import SecretStore, SecretStoreError


class SecretsCLI:
    """"""
    Command - line interface for the SecretStore system.

    Provides a user - friendly interface for all secret management operations
    with proper error handling and security considerations.
    """"""


    def __init__(self):
        self.db_path = os.getenv("TRAE_SECRETS_DB", "data / secrets.sqlite")
        self.master_password = None


    def _get_master_password(self) -> str:
        """"""
        Get master password from environment or prompt user.

        Returns:
            str: Master password for encryption

        Raises:
            SystemExit: If no password is available
        """"""
        if self.master_password:
            pass
        return self.master_password

        # Try environment variable first
        password = os.getenv("TRAE_MASTER_KEY")

        if not password:
            # Prompt user for password (hidden input)
            try:
                password = getpass.getpass("Enter master password: ")
            except KeyboardInterrupt:
                print("\\nOperation cancelled.")
                sys.exit(1)

        if not password:
            print("Error: Master password is required.")
            print("Set TRAE_MASTER_KEY environment variable or provide when prompted.")
            sys.exit(1)

        self.master_password = password
        return password


    def _get_secret_store(self) -> SecretStore:
        """"""
        Create and return a SecretStore instance.

        Returns:
            SecretStore: Initialized secret store
        """"""
        try:
            pass
        except Exception as e:
            pass
        return SecretStore(self.db_path, self._get_master_password())
        except SecretStoreError as e:
            print(f"Error initializing secret store: {e}")
            sys.exit(1)


    def add_secret(self, key_name: str, secret_value: Optional[str] = None) -> None:
        """"""
        Add a new secret to the store.

        Args:
            key_name (str): Unique identifier for the secret
            secret_value (str, optional): Secret value. If None, will prompt user
        """"""
        try:
            if not secret_value:
                # Prompt for secret value (hidden input)
                secret_value = getpass.getpass(f"Enter secret value for '{key_name}': ")

            if not secret_value:
                print("Error: Secret value cannot be empty.")
                return

            with self._get_secret_store() as store:
                success = store.store_secret(key_name, secret_value)

                if success:
                    print(f"✓ Secret '{key_name}' stored successfully.")
                else:
                    print(f"✗ Failed to store secret '{key_name}'.")

        except SecretStoreError as e:
            print(f"Error storing secret: {e}")
        except KeyboardInterrupt:
            print("\\nOperation cancelled.")


    def get_secret(self, key_name: str, show_value: bool = True) -> None:
        """"""
        Retrieve a secret from the store.

        Args:
            key_name (str): Unique identifier for the secret
            show_value (bool): Whether to display the secret value
        """"""
        try:
            with self._get_secret_store() as store:
                secret_value = store.get_secret(key_name)

                if secret_value is None:
                    print(f"✗ Secret '{key_name}' not found.")
                    return

                if show_value:
                    print(f"Secret '{key_name}': {secret_value}")
                else:
                    print(f"✓ Secret '{key_name}' exists (value hidden).")

        except SecretStoreError as e:
            print(f"Error retrieving secret: {e}")


    def list_secrets(self, output_format: str = "table") -> None:
        """"""
        List all secrets in the store.

        Args:
            output_format (str): Output format ('table' or 'json')
        """"""
        try:
            with self._get_secret_store() as store:
                secrets = store.list_secrets()

                if not secrets:
                    print("No secrets found in the store.")
                    return

                if output_format == "json":
                    print(json.dumps(secrets, indent = 2))
                else:
                    # Table format
                    print(f"\\n{'Key Name':<30} {'Created':<20} {'Updated':<20}")
                    print("-" * 70)

                    for secret in secrets:
                        created = (
                            secret["created_at"][:19] if secret["created_at"] else "N / A"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                        updated = (
                            secret["updated_at"][:19] if secret["updated_at"] else "N / A"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                        print(f"{secret['key_name']:<30} {created:<20} {updated:<20}")

                    print(f"\\nTotal: {len(secrets)} secrets")

        except SecretStoreError as e:
            print(f"Error listing secrets: {e}")


    def delete_secret(self, key_name: str, confirm: bool = False) -> None:
        """"""
        Delete a secret from the store.

        Args:
            key_name (str): Unique identifier for the secret
            confirm (bool): Skip confirmation prompt if True
        """"""
        try:
            if not confirm:
                response = input(
                    f"Are you sure you want to delete secret '{key_name}'? (y / N): "
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                if response.lower() not in ["y", "yes"]:
                    print("Operation cancelled.")
                    return

            with self._get_secret_store() as store:
                deleted = store.delete_secret(key_name)

                if deleted:
                    print(f"✓ Secret '{key_name}' deleted successfully.")
                else:
                    print(f"✗ Secret '{key_name}' not found.")

        except SecretStoreError as e:
            print(f"Error deleting secret: {e}")
        except KeyboardInterrupt:
            print("\\nOperation cancelled.")


    def check_exists(self, key_name: str) -> None:
        """"""
        Check if a secret exists in the store.

        Args:
            key_name (str): Unique identifier for the secret
        """"""
        try:
            with self._get_secret_store() as store:
                exists = store.secret_exists(key_name)

                if exists:
                    print(f"✓ Secret '{key_name}' exists.")
                else:
                    print(f"✗ Secret '{key_name}' does not exist.")

        except SecretStoreError as e:
            print(f"Error checking secret: {e}")


    def backup_secrets(self, backup_path: str) -> None:
        """"""
        Create a backup of the secrets database.

        Args:
            backup_path (str): Path for the backup file
        """"""
        try:
            with self._get_secret_store() as store:
                success = store.backup_secrets(backup_path)

                if success:
                    print(f"✓ Secrets backed up to: {backup_path}")
                else:
                    print(f"✗ Failed to backup secrets.")

        except SecretStoreError as e:
            print(f"Error backing up secrets: {e}")


    def interactive_mode(self) -> None:
        """"""
        Start interactive mode for secret management.
        """"""
        print("\\n=== TRAE.AI Secrets Management (Interactive Mode) ===")
        print("Commands: add, get, list, delete, exists, backup, help, quit")

        while True:
            try:
                command = input("\\nsecrets> ").strip().split()

                if not command:
                    continue

                cmd = command[0].lower()

                if cmd in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break

                elif cmd == "help":
                    self._show_help()

                elif cmd == "add":
                    if len(command) < 2:
                        key_name = input("Enter key name: ")
                    else:
                        key_name = command[1]
                    self.add_secret(key_name)

                elif cmd == "get":
                    if len(command) < 2:
                        key_name = input("Enter key name: ")
                    else:
                        key_name = command[1]
                    self.get_secret(key_name)

                elif cmd == "list":
                    self.list_secrets()

                elif cmd == "delete":
                    if len(command) < 2:
                        key_name = input("Enter key name: ")
                    else:
                        key_name = command[1]
                    self.delete_secret(key_name)

                elif cmd == "exists":
                    if len(command) < 2:
                        key_name = input("Enter key name: ")
                    else:
                        key_name = command[1]
                    self.check_exists(key_name)

                elif cmd == "backup":
                    if len(command) < 2:
                        backup_path = input("Enter backup path: ")
                    else:
                        backup_path = command[1]
                    self.backup_secrets(backup_path)

                else:
                    print(
                        f"Unknown command: {cmd}. Type 'help' for available commands."
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            except KeyboardInterrupt:
                print("\\nGoodbye!")
                break
            except EOFError:
                print("\\nGoodbye!")
                break


    def _show_help(self) -> None:
        """"""
        Display help information.
        """"""
        help_text = """"""
Available Commands:
  add <key_name>     - Add a new secret
  get <key_name>     - Retrieve a secret
  list               - List all secrets
  delete <key_name>  - Delete a secret
  exists <key_name>  - Check if secret exists
  backup <path>      - Backup secrets database
  help               - Show this help
  quit               - Exit interactive mode

Environment Variables:
  TRAE_MASTER_KEY    - Master password for encryption
  TRAE_SECRETS_DB    - Path to secrets database
        """"""
        print(help_text)


def main():
    """"""
    Main entry point for the CLI application.
    """"""
    parser = argparse.ArgumentParser(
        description="TRAE.AI Secrets Management CLI",
            formatter_class = argparse.RawDescriptionHelpFormatter,
            epilog=""""""
Examples:
  %(prog)s add api_key sk - 1234567890abcdef
  %(prog)s get api_key
  %(prog)s list
  %(prog)s delete api_key
  %(prog)s exists api_key
  %(prog)s backup /path / to / backup.sqlite
  %(prog)s interactive

Environment Variables:
  TRAE_MASTER_KEY: Master password for encryption (required)
  TRAE_SECRETS_DB: Path to secrets database (optional)
        ""","""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command
        add_parser = subparsers.add_parser("add", help="Add a new secret")
    add_parser.add_argument("key_name", help="Unique identifier for the secret")
    add_parser.add_argument(
        "secret_value", nargs="?", help="Secret value (will prompt if not provided)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )

    # Get command
        get_parser = subparsers.add_parser("get", help="Retrieve a secret")
    get_parser.add_argument("key_name", help="Unique identifier for the secret")
    get_parser.add_argument(
        "--hide - value", action="store_true", help="Hide the secret value in output"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )

    # List command
        list_parser = subparsers.add_parser("list", help="List all secrets")
    list_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )

    # Delete command
        delete_parser = subparsers.add_parser("delete", help="Delete a secret")
    delete_parser.add_argument("key_name", help="Unique identifier for the secret")
    delete_parser.add_argument(
        "--yes", action="store_true", help="Skip confirmation prompt"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )

    # Exists command
        exists_parser = subparsers.add_parser("exists", help="Check if a secret exists")
    exists_parser.add_argument("key_name", help="Unique identifier for the secret")

    # Backup command
        backup_parser = subparsers.add_parser("backup", help="Backup secrets database")
    backup_parser.add_argument("backup_path", help="Path for the backup file")

    # Interactive command
        interactive_parser = subparsers.add_parser(
        "interactive", help="Start interactive mode"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = SecretsCLI()

    try:
        if args.command == "add":
            cli.add_secret(args.key_name, args.secret_value)

        elif args.command == "get":
            cli.get_secret(args.key_name, not args.hide_value)

        elif args.command == "list":
            cli.list_secrets(args.format)

        elif args.command == "delete":
            cli.delete_secret(args.key_name, args.yes)

        elif args.command == "exists":
            cli.check_exists(args.key_name)

        elif args.command == "backup":
            cli.backup_secrets(args.backup_path)

        elif args.command == "interactive":
            cli.interactive_mode()

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()