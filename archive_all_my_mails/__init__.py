"""Archive All My Mails - A Python tool to archive all emails from Gmail inbox using the Gmail API."""

__version__ = "0.1.0"
__author__ = "Nathan"
__email__ = ""
__description__ = "A Python tool to archive all emails from Gmail inbox using the Gmail API"

from .gmail_archiver import GmailArchiver

__all__ = ["GmailArchiver"]