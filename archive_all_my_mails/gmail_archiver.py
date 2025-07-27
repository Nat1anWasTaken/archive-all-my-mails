import time
from typing import TYPE_CHECKING

from googleapiclient.errors import HttpError
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from .auth import GmailAuth

if TYPE_CHECKING:
    from googleapiclient.discovery import Resource


class GmailArchiver:
    def __init__(
        self, client_id: str | None = None, client_secret: str | None = None, token_file: str = "token.pickle"
    ) -> None:
        self.auth = GmailAuth(client_id, client_secret, token_file)
        self.service: Resource | None = None
        self.console = Console()

    def connect(self) -> None:
        try:
            self.service = self.auth.get_gmail_service()
            self.console.print("[bold green]✅ Successfully connected to Gmail API[/bold green]")
        except Exception as e:
            self.console.print(f"[bold red]❌ Failed to connect to Gmail API: {e}[/bold red]")
            raise

    def get_all_message_ids(self, query: str = "in:inbox") -> list[str]:
        if not self.service:
            raise RuntimeError("Not connected to Gmail API. Call connect() first.")

        message_ids = []
        page_token = None

        self.console.print(f"[cyan]🔍 Fetching message IDs with query: {query}[/cyan]")

        while True:
            try:
                results = (
                    self.service.users()
                    .messages()
                    .list(userId="me", q=query, pageToken=page_token, maxResults=500)
                    .execute()
                )

                messages = results.get("messages", [])
                if not messages:
                    break

                message_ids.extend([msg["id"] for msg in messages])
                self.console.print(f"[dim]📧 Found {len(message_ids)} messages so far...[/dim]")

                page_token = results.get("nextPageToken")
                if not page_token:
                    break

            except HttpError as error:
                self.console.print(f"[bold red]❌ An error occurred while fetching messages: {error}[/bold red]")
                raise

        self.console.print(f"[bold cyan]📊 Total messages found: {len(message_ids)}[/bold cyan]")
        return message_ids

    def archive_messages(
        self,
        message_ids: list[str],
        batch_size: int = 100,
        dry_run: bool = False,
    ) -> dict[str, int]:
        if not self.service:
            raise RuntimeError("Not connected to Gmail API. Call connect() first.")

        if not message_ids:
            self.console.print("[yellow]📭 No messages to archive[/yellow]")
            return {"success": 0, "failed": 0}

        if dry_run:
            self.console.print(
                Panel(
                    f"[bold yellow]🔍 DRY RUN: Would archive {len(message_ids)} messages[/bold yellow]",
                    border_style="yellow",
                )
            )
            return {"success": len(message_ids), "failed": 0}

        self.console.print(
            f"[bold blue]🚀 Starting to archive {len(message_ids)} messages in batches of {batch_size}[/bold blue]"
        )

        success_count = 0
        failed_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]Archiving emails...", total=len(message_ids))

            for i in range(0, len(message_ids), batch_size):
                batch = message_ids[i : i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(message_ids) + batch_size - 1) // batch_size

                progress.update(
                    task,
                    description=f"[cyan]Processing batch {batch_num}/{total_batches}...",
                )

                try:
                    (
                        self.service.users()
                        .messages()
                        .batchModify(
                            userId="me",
                            body={"ids": batch, "removeLabelIds": ["INBOX"]},
                        )
                        .execute()
                    )

                    success_count += len(batch)
                    progress.advance(task, len(batch))

                    time.sleep(0.2)

                except HttpError as error:
                    self.console.print(f"[red]❌ Failed to archive batch {batch_num}: {error}[/red]")
                    self.console.print(
                        f"[dim]Error details: {error.content if hasattr(error, 'content') else 'No details'}[/dim]"
                    )
                    failed_count += len(batch)
                    progress.advance(task, len(batch))
                    continue
                except Exception as error:
                    self.console.print(f"[red]❌ Unexpected error in batch {batch_num}: {error}[/red]")
                    failed_count += len(batch)
                    progress.advance(task, len(batch))
                    continue

        self.console.print(
            Panel(
                f"[bold green]✅ Archiving complete![/bold green]\n"
                f"[green]📈 Success: {success_count}[/green]\n"
                f"[red]❌ Failed: {failed_count}[/red]",
                border_style="green",
                title="Batch Results",
            )
        )
        return {"success": success_count, "failed": failed_count}

    def archive_all_inbox_emails(self, dry_run: bool = False, batch_size: int = 100) -> dict[str, int]:
        self.console.print("[bold blue]🚀 Starting email archiving process...[/bold blue]")

        try:
            self.connect()

            total_success = 0
            total_failed = 0
            rounds = 0

            while True:
                rounds += 1
                self.console.print(f"\n[bold magenta]--- Round {rounds} ---[/bold magenta]")

                inbox_count_before = self.get_inbox_count()
                self.console.print(f"[dim]📊 Inbox count before round: {inbox_count_before}[/dim]")

                message_ids = self.get_all_message_ids("in:inbox")

                if not message_ids:
                    self.console.print("[green]✅ No more emails found in inbox[/green]")
                    break

                self.console.print(f"[cyan]📧 Found {len(message_ids)} emails to archive in this round[/cyan]")

                result = self.archive_messages(message_ids, batch_size=batch_size, dry_run=dry_run)
                total_success += result["success"]
                total_failed += result["failed"]

                if dry_run:
                    self.console.print(f"[yellow]🔍 DRY RUN: Round {rounds} complete[/yellow]")
                    break

                if not dry_run:
                    time.sleep(2)
                    inbox_count_after = self.get_inbox_count()
                    self.console.print(f"[dim]📊 Inbox count after round: {inbox_count_after}[/dim]")
                    self.console.print(
                        f"[green]📈 Emails archived in this round: {inbox_count_before - inbox_count_after}[/green]"
                    )

                if result["success"] == 0:
                    self.console.print(
                        "[yellow]⚠️ No emails were successfully archived in this round, stopping[/yellow]"
                    )
                    break

                self.console.print(f"[green]✅ Round {rounds} complete. Checking for more emails...[/green]")
                time.sleep(1)

            self.console.print(
                Panel(
                    f"[bold green]🎉 Archiving process complete after {rounds} rounds![/bold green]",
                    border_style="green",
                    title="Final Results",
                )
            )
            return {"success": total_success, "failed": total_failed}

        except Exception as e:
            self.console.print(f"[bold red]❌ Error during archiving process: {e}[/bold red]")
            raise

    def get_inbox_count(self) -> int:
        if not self.service:
            self.connect()

        if not self.service:
            raise RuntimeError("Failed to connect to Gmail API")

        try:
            results = self.service.users().messages().list(userId="me", q="in:inbox", maxResults=1).execute()

            estimated_count: int = results.get("resultSizeEstimate", 0)
            return estimated_count
        except HttpError as error:
            self.console.print(f"[red]❌ Error getting inbox count: {error}[/red]")
            return 0
