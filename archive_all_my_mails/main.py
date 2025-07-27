import sys

import click
import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from .gmail_archiver import GmailArchiver


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
    console = Console()
    
    console.print(Panel.fit(
        "[bold blue]Gmail Email Archiver[/bold blue]",
        border_style="blue"
    ))

    if not client_id:
        questions = [
            inquirer.Text('client_id', message="Enter your Google OAuth Client ID")
        ]
        answers = inquirer.prompt(questions)
        client_id = answers['client_id'].strip() if answers else None

    if not client_secret:
        questions = [
            inquirer.Password('client_secret', message="Enter your Google OAuth Client Secret")
        ]
        answers = inquirer.prompt(questions)
        client_secret = answers['client_secret'].strip() if answers else None

    if not client_id or not client_secret:
        console.print("[bold red]❌ Both Client ID and Client Secret are required[/bold red]")
        sys.exit(1)

    console.print("\n[yellow]🔐 Authenticating with Google...[/yellow]")
    archiver = GmailArchiver(client_id=client_id, client_secret=client_secret)

    try:
        archiver.connect()

        inbox_count = archiver.get_inbox_count()
        if inbox_count == 0:
            console.print("[green]✅ No emails found in inbox. Nothing to archive.[/green]")
            return

        console.print(f"[cyan]📧 Found approximately {inbox_count} emails in inbox[/cyan]")

        if dry_run:
            console.print(Panel(
                "[bold yellow]🔍 DRY RUN MODE - No changes will be made[/bold yellow]",
                border_style="yellow"
            ))
        else:
            console.print(Panel(
                "[bold red]⚠️  This will archive ALL emails from your inbox![/bold red]\n"
                "[dim]Archived emails will remain accessible in 'All Mail' but will be removed from inbox.[/dim]",
                border_style="red",
                title="Warning"
            ))

        if not yes and not dry_run:
            if not Confirm.ask("\n[bold]Do you want to continue?[/bold]"):
                console.print("[yellow]Operation cancelled.[/yellow]")
                return

        console.print("\n[bold green]🚀 Starting archiving process...[/bold green]")
        result = archiver.archive_all_inbox_emails(
            dry_run=dry_run, batch_size=batch_size
        )

        if dry_run:
            console.print(Panel(
                f"[bold green]✅ DRY RUN: Would have archived {result['success']} emails[/bold green]",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"[bold green]✅ Archiving complete![/bold green]\n"
                f"[green]📈 Successfully archived: {result['success']} emails[/green]" +
                (f"\n[red]❌ Failed to archive: {result['failed']} emails[/red]" if result["failed"] > 0 else ""),
                border_style="green",
                title="Results"
            ))

    except ValueError as e:
        console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        console.print(Panel(
            "[bold]To get OAuth credentials:[/bold]\n"
            "1. Go to https://console.developers.google.com/\n"
            "2. Create a new project or select existing one\n"
            "3. Enable Gmail API\n"
            "4. Create credentials (OAuth 2.0 client ID)\n"
            "5. Select 'Desktop Application' as application type\n"
            "6. Use the Client ID and Client Secret with this script",
            border_style="blue",
            title="Setup Instructions"
        ))
        sys.exit(1)

    except Exception as e:
        console.print(f"\n[bold red]❌ An error occurred: {e}[/bold red]")
        sys.exit(1)


@click.command()
@click.option("--client-id", help="Google OAuth Client ID")
@click.option("--client-secret", help="Google OAuth Client Secret")
def status(client_id, client_secret):
    """Check inbox status without making changes."""
    console = Console()
    
    if not client_id:
        questions = [
            inquirer.Text('client_id', message="Enter your Google OAuth Client ID")
        ]
        answers = inquirer.prompt(questions)
        client_id = answers['client_id'].strip() if answers else None

    if not client_secret:
        questions = [
            inquirer.Password('client_secret', message="Enter your Google OAuth Client Secret")
        ]
        answers = inquirer.prompt(questions)
        client_secret = answers['client_secret'].strip() if answers else None

    archiver = GmailArchiver(client_id=client_id, client_secret=client_secret)
    try:
        archiver.connect()
        count = archiver.get_inbox_count()
        console.print(Panel(
            f"[bold cyan]📧 Inbox contains approximately {count} emails[/bold cyan]",
            border_style="cyan",
            title="Inbox Status"
        ))
    except Exception as e:
        console.print(f"[bold red]❌ Error checking status: {e}[/bold red]")


if __name__ == "__main__":
    main()
