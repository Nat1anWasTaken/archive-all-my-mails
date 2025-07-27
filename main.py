import getpass
import sys

import click

from src.gmail_archiver import GmailArchiver


@click.command()
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview what would be archived without making changes",
)
@click.option("--client-id", help="Google OAuth Client ID")
@click.option("--client-secret", help="Google OAuth Client Secret")
@click.option(
    "--batch-size", default=100, help="Number of emails to process in each batch"
)
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
def main(dry_run, client_id, client_secret, batch_size, yes):
    """Archive all emails from Gmail inbox using the Gmail API."""

    print("Gmail Email Archiver")
    print("=" * 50)

    if not client_id:
        client_id = input("Enter your Google OAuth Client ID: ").strip()

    if not client_secret:
        client_secret = getpass.getpass(
            "Enter your Google OAuth Client Secret: "
        ).strip()

    if not client_id or not client_secret:
        print("❌ Both Client ID and Client Secret are required")
        sys.exit(1)

    print("\n🔐 Authenticating with Google...")
    archiver = GmailArchiver(client_id=client_id, client_secret=client_secret)

    try:
        archiver.connect()

        inbox_count = archiver.get_inbox_count()
        if inbox_count == 0:
            print("No emails found in inbox. Nothing to archive.")
            return

        print(f"Found approximately {inbox_count} emails in inbox")

        if dry_run:
            print("\n🔍 DRY RUN MODE - No changes will be made")
        else:
            print("\n⚠️  This will archive ALL emails from your inbox!")
            print(
                "Archived emails will remain accessible in 'All Mail' but will be removed from inbox."
            )

        if not yes and not dry_run:
            if not click.confirm("\nDo you want to continue?"):
                print("Operation cancelled.")
                return

        print("\nStarting archiving process...")
        result = archiver.archive_all_inbox_emails(
            dry_run=dry_run, batch_size=batch_size
        )

        if dry_run:
            print(f"\n✅ DRY RUN: Would have archived {result['success']} emails")
        else:
            print("\n✅ Archiving complete!")
            print(f"   Successfully archived: {result['success']} emails")
            if result["failed"] > 0:
                print(f"   Failed to archive: {result['failed']} emails")

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nTo get OAuth credentials:")
        print("1. Go to https://console.developers.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API")
        print("4. Create credentials (OAuth 2.0 client ID)")
        print("5. Select 'Desktop Application' as application type")
        print("6. Use the Client ID and Client Secret with this script")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)


@click.command()
@click.option("--client-id", help="Google OAuth Client ID")
@click.option("--client-secret", help="Google OAuth Client Secret")
def status(client_id, client_secret):
    """Check inbox status without making changes."""
    if not client_id:
        client_id = input("Enter your Google OAuth Client ID: ").strip()

    if not client_secret:
        client_secret = getpass.getpass(
            "Enter your Google OAuth Client Secret: "
        ).strip()

    archiver = GmailArchiver(client_id=client_id, client_secret=client_secret)
    try:
        archiver.connect()
        count = archiver.get_inbox_count()
        print(f"Inbox contains approximately {count} emails")
    except Exception as e:
        print(f"Error checking status: {e}")


if __name__ == "__main__":
    main()
