#!/usr/bin/env python3
""""""
TRAE.AI Secrets Management CLI

Command - line interface for managing encrypted secrets in the TRAE.AI system.
Provides secure operations for adding, retrieving, listing, and deleting secrets.

Usage:
    python scripts/secrets_cli.py add <key_name> <secret_value>
    python scripts/secrets_cli.py get <key_name>
    python scripts/secrets_cli.py list
    python scripts/secrets_cli.py delete <key_name>
    python scripts/secrets_cli.py exists <key_name>
    python scripts/secrets_cli.py backup <backup_path>

Environment Variables:
    TRAE_MASTER_KEY: Master password for encryption (required)
    TRAE_SECRETS_DB: Path to secrets database (optional,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     defaults to data/secrets.sqlite)

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

from backend.secret_store import SecretStore, SecretStoreError

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class SecretsCLI:
    """"""
    Command - line interface for the SecretStore system.

    Provides a user - friendly interface for all secret management operations
    with proper error handling and security considerations.
    """"""


    def __init__(self):
        self.db_path = os.getenv("TRAE_SECRETS_DB", "data/secrets.sqlite")
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
                            secret["created_at"][:19] if secret["created_at"] else "N/A"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                        updated = (
                            secret["updated_at"][:19] if secret["updated_at"] else "N/A"
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
                    f"Are you sure you want to delete secret '{key_name}'? (y/N): "
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


    def export_secrets(self, export_path: str, format_type: str = "json") -> None:
        """"""
        Export secrets to a file in specified format.

        Args:
            export_path (str): Path where the export will be saved
            format_type (str): Export format ('json' or 'env')
        """"""
        try:
            with self._get_secret_store() as store:
                secrets = store.list_secrets()

                if not secrets:
                    print("No secrets to export.")
                    return

                export_data = {}
                for secret in secrets:
                    # Get the actual secret value
                    secret_value = store.get_secret(secret["key_name"])
                    export_data[secret["key_name"]] = secret_value

                Path(export_path).parent.mkdir(parents = True, exist_ok = True)

                if format_type == "json":
                    with open(export_path, "w") as f:
                        json.dump(export_data, f, indent = 2)
                elif format_type == "env":
                    with open(export_path, "w") as f:
                        for key, value in export_data.items():
                            f.write(f"{key}={value}\\n")
                else:
                    raise ValueError(f"Unsupported format: {format_type}")

                print(f"✓ {len(export_data)} secrets exported to: {export_path}")
                print(
                    f"⚠️  WARNING: Exported file contains unencrypted secrets. Handle with care!"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        except SecretStoreError as e:
            print(f"Error exporting secrets: {e}")
        except Exception as e:
            print(f"Error writing export file: {e}")


    def import_secrets(
        self, import_path: str, format_type: str = "json", overwrite: bool = False
# BRACKET_SURGEON: disabled
#     ) -> None:
        """"""
        Import secrets from a file.

        Args:
            import_path (str): Path to the import file
            format_type (str): Import format ('json' or 'env')
            overwrite (bool): Whether to overwrite existing secrets
        """"""
        try:
            if not Path(import_path).exists():
                print(f"Import file not found: {import_path}")
                return

            import_data = {}

            if format_type == "json":
                with open(import_path, "r") as f:
                    import_data = json.load(f)
            elif format_type == "env":
                with open(import_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and "=" in line and not line.startswith("#"):"
                            key, value = line.split("=", 1)
                            import_data[key.strip()] = value.strip()
            else:
                raise ValueError(f"Unsupported format: {format_type}")

            if not import_data:
                print("No secrets found in import file.")
                return

            with self._get_secret_store() as store:
                imported_count = 0
                skipped_count = 0

                for key_name, secret_value in import_data.items():
                    if store.secret_exists(key_name) and not overwrite:
                        print(f"⚠️  Skipping existing secret: {key_name}")
                        skipped_count += 1
                        continue

                    store.store_secret(key_name, secret_value)
                    imported_count += 1

                print(
                    f"✓ Import completed: {imported_count} secrets imported, {skipped_count} skipped"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        except SecretStoreError as e:
            print(f"Error importing secrets: {e}")
        except Exception as e:
            print(f"Error reading import file: {e}")


    def batch_add_secrets(self, secrets_dict: dict) -> None:
        """"""
        Add multiple secrets in batch.

        Args:
            secrets_dict (dict): Dictionary of key - value pairs to add
        """"""
        try:
            with self._get_secret_store() as store:
                added_count = 0
                failed_count = 0

                for key_name, secret_value in secrets_dict.items():
                    try:
                        store.store_secret(key_name, secret_value)
                        print(f"✓ Added: {key_name}")
                        added_count += 1
                    except SecretStoreError as e:
                        print(f"✗ Failed to add {key_name}: {e}")
                        failed_count += 1

                print(
                    f"\\nBatch operation completed: {added_count} added, {failed_count} failed"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        except SecretStoreError as e:
            print(f"Error in batch operation: {e}")


    def batch_delete_secrets(self, key_names: list, force: bool = False) -> None:
        """"""
        Delete multiple secrets in batch.

        Args:
            key_names (list): List of secret keys to delete
            force (bool): Skip confirmation prompts
        """"""
        try:
            if not force:
                print(f"You are about to delete {len(key_names)} secrets:")
                for key_name in key_names:
                    print(f"  - {key_name}")

                confirm = input("\\nAre you sure? (yes/no): ").lower()
                if confirm not in ["yes", "y"]:
                    print("Operation cancelled.")
                    return

            with self._get_secret_store() as store:
                deleted_count = 0
                failed_count = 0

                for key_name in key_names:
                    try:
                        if store.secret_exists(key_name):
                            store.delete_secret(key_name)
                            print(f"✓ Deleted: {key_name}")
                            deleted_count += 1
                        else:
                            print(f"⚠️  Secret not found: {key_name}")
                    except SecretStoreError as e:
                        print(f"✗ Failed to delete {key_name}: {e}")
                        failed_count += 1

                print(
                    f"\\nBatch deletion completed: {deleted_count} deleted, {failed_count} failed"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        except SecretStoreError as e:
            print(f"Error in batch deletion: {e}")


    def configure_store(self, config_option: str, value: str = None) -> None:
        """"""
        Configure SecretStore settings.

        Args:
            config_option (str): Configuration option to set
            value (str): Value to set (if None, shows current value)
        """"""
        config_file = Path(self.db_path).parent/"secrets_config.json"

        # Load existing config
        config = {}
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")

        if value is None:
            # Show current value
            current_value = config.get(config_option, "Not set")
            print(f"{config_option}: {current_value}")
            return

        # Set new value
        config[config_option] = value

        try:
            config_file.parent.mkdir(parents = True, exist_ok = True)
            with open(config_file, "w") as f:
                json.dump(config, f, indent = 2)
            print(f"✓ Configuration updated: {config_option} = {value}")
        except Exception as e:
            print(f"Error saving configuration: {e}")


    def interactive_mode(self) -> None:
        """"""
        Start interactive mode for secret management.
        """"""
        print("\\n=== TRAE.AI Secrets Management (Interactive Mode) ===")
        print(
            "Commands: add, get, list, delete, exists, backup, export, import, batch - add, batch - delete, config, help, quit"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

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

                elif cmd == "export":
                    if len(command) < 2:
                        export_path = input("Enter export path: ")
                    else:
                        export_path = command[1]
                    format_type = command[2] if len(command) > 2 else "json"
                    self.export_secrets(export_path, format_type)

                elif cmd == "import":
                    if len(command) < 2:
                        import_path = input("Enter import path: ")
                    else:
                        import_path = command[1]
                    format_type = command[2] if len(command) > 2 else "json"
                    overwrite = "--overwrite" in command
                        self.import_secrets(import_path, format_type, overwrite)

                elif cmd == "batch - add":
                    print("Enter secrets in key = value format (empty line to finish):")
                    secrets_dict = {}
                    while True:
                        line = input("  ").strip()
                        if not line:
                            break
                        if "=" in line:
                            key, value = line.split("=", 1)
                            secrets_dict[key.strip()] = value.strip()
                    if secrets_dict:
                        self.batch_add_secrets(secrets_dict)

                elif cmd == "batch - delete":
                    keys_input = input(
                        "Enter secret keys to delete (comma - separated): "
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                    key_names = [k.strip() for k in keys_input.split(",") if k.strip()]
                    if key_names:
                        force = "--force" in command
                            self.batch_delete_secrets(key_names, force)

                elif cmd == "config":
                    if len(command) < 2:
                        option = input("Enter config option: ")
                    else:
                        option = command[1]
                    value = command[2] if len(command) > 2 else None
                    self.configure_store(option, value)

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
  add <key_name>        - Add a new secret
  get <key_name>        - Retrieve a secret
  list                  - List all secrets
  delete <key_name>     - Delete a secret
  exists <key_name>     - Check if secret exists
  backup <path>         - Backup secrets database
  export <path> [fmt]   - Export secrets (json/env format)

  import <path> [fmt]   - Import secrets (json/env format)

  batch - add             - Add multiple secrets interactively
  batch - delete          - Delete multiple secrets
  config <opt> [val]    - Configure settings
  help                  - Show this help
  quit                  - Exit interactive mode

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
  %(prog)s backup/path/to/backup.sqlite
  %(prog)s export/path/to/secrets.json --format json
  %(prog)s import/path/to/secrets.env --format env --overwrite
  %(prog)s batch - add/path/to/secrets.json
  %(prog)s batch - delete key1 key2 key3 --force
  %(prog)s config backup_retention 30
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

    # Export command
        export_parser = subparsers.add_parser("export", help="Export secrets to file")
    export_parser.add_argument("export_path", help="Path for the export file")
    export_parser.add_argument(
        "--format", choices=["json", "env"], default="json", help="Export format"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )

    # Import command
        import_parser = subparsers.add_parser("import", help="Import secrets from file")
    import_parser.add_argument("import_path", help="Path to the import file")
    import_parser.add_argument(
        "--format", choices=["json", "env"], default="json", help="Import format"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )
    import_parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing secrets"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )

    # Batch add command
        batch_add_parser = subparsers.add_parser(
        "batch - add", help="Add multiple secrets from JSON file"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )
    batch_add_parser.add_argument("secrets_file", help="JSON file containing secrets")

    # Batch delete command
        batch_delete_parser = subparsers.add_parser(
        "batch - delete", help="Delete multiple secrets"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )
    batch_delete_parser.add_argument(
        "key_names", nargs="+", help="Secret keys to delete"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )
    batch_delete_parser.add_argument(
        "--force", action="store_true", help="Skip confirmation"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )

    # Config command
        config_parser = subparsers.add_parser("config", help="Configure settings")
    config_parser.add_argument("option", help="Configuration option")
    config_parser.add_argument(
        "value", nargs="?", help="Value to set (omit to show current value)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )

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

        elif args.command == "export":
            cli.export_secrets(args.export_path, args.format)

        elif args.command == "import":
            cli.import_secrets(args.import_path, args.format, args.overwrite)

        elif args.command == "batch - add":
            try:
                with open(args.secrets_file, "r") as f:
                    secrets_dict = json.load(f)
                cli.batch_add_secrets(secrets_dict)
            except Exception as e:
                print(f"Error reading secrets file: {e}")

        elif args.command == "batch - delete":
            cli.batch_delete_secrets(args.key_names, args.force)

        elif args.command == "config":
            cli.configure_store(args.option, args.value)

        elif args.command == "interactive":
            cli.interactive_mode()

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()