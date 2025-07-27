import time
from typing import List, Dict, Optional
from googleapiclient.errors import HttpError
from auth import GmailAuth

class GmailArchiver:
    def __init__(self, client_id=None, client_secret=None, token_file='token.pickle'):
        self.auth = GmailAuth(client_id, client_secret, token_file)
        self.service = None
        
    def connect(self):
        try:
            self.service = self.auth.get_gmail_service()
            print("Successfully connected to Gmail API")
        except Exception as e:
            print(f"Failed to connect to Gmail API: {e}")
            raise
    
    def get_all_message_ids(self, query: str = 'in:inbox') -> List[str]:
        if not self.service:
            raise RuntimeError("Not connected to Gmail API. Call connect() first.")
        
        message_ids = []
        page_token = None
        
        print(f"Fetching message IDs with query: {query}")
        
        while True:
            try:
                results = self.service.users().messages().list(
                    userId='me',
                    q=query,
                    pageToken=page_token,
                    maxResults=500
                ).execute()
                
                messages = results.get('messages', [])
                if not messages:
                    break
                
                message_ids.extend([msg['id'] for msg in messages])
                print(f"Found {len(message_ids)} messages so far...")
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                    
            except HttpError as error:
                print(f"An error occurred while fetching messages: {error}")
                raise
        
        print(f"Total messages found: {len(message_ids)}")
        return message_ids
    
    def archive_messages(self, message_ids: List[str], batch_size: int = 100, dry_run: bool = False) -> Dict[str, int]:
        if not self.service:
            raise RuntimeError("Not connected to Gmail API. Call connect() first.")
        
        if not message_ids:
            print("No messages to archive")
            return {"success": 0, "failed": 0}
        
        if dry_run:
            print(f"DRY RUN: Would archive {len(message_ids)} messages")
            return {"success": len(message_ids), "failed": 0}
        
        print(f"Starting to archive {len(message_ids)} messages in batches of {batch_size}")
        
        success_count = 0
        failed_count = 0
        
        for i in range(0, len(message_ids), batch_size):
            batch = message_ids[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(message_ids) + batch_size - 1)//batch_size}")
            
            try:
                response = self.service.users().messages().batchModify(
                    userId='me',
                    body={
                        'ids': batch,
                        'removeLabelIds': ['INBOX']
                    }
                ).execute()
                
                success_count += len(batch)
                print(f"Successfully archived {len(batch)} messages (batch {i//batch_size + 1})")
                
                time.sleep(0.2)
                
            except HttpError as error:
                print(f"Failed to archive batch {i//batch_size + 1}: {error}")
                print(f"Error details: {error.content if hasattr(error, 'content') else 'No details'}")
                failed_count += len(batch)
                continue
            except Exception as error:
                print(f"Unexpected error in batch {i//batch_size + 1}: {error}")
                failed_count += len(batch)
                continue
        
        print(f"Archiving complete. Success: {success_count}, Failed: {failed_count}")
        return {"success": success_count, "failed": failed_count}
    
    def archive_all_inbox_emails(self, dry_run: bool = False, batch_size: int = 100) -> Dict[str, int]:
        print("Starting email archiving process...")
        
        try:
            self.connect()
            
            total_success = 0
            total_failed = 0
            rounds = 0
            
            while True:
                rounds += 1
                print(f"\n--- Round {rounds} ---")
                
                inbox_count_before = self.get_inbox_count()
                print(f"Inbox count before round: {inbox_count_before}")
                
                message_ids = self.get_all_message_ids('in:inbox')
                
                if not message_ids:
                    print("No more emails found in inbox")
                    break
                
                print(f"Found {len(message_ids)} emails to archive in this round")
                
                result = self.archive_messages(message_ids, batch_size=batch_size, dry_run=dry_run)
                total_success += result["success"]
                total_failed += result["failed"]
                
                if dry_run:
                    print(f"DRY RUN: Round {rounds} complete")
                    break
                
                if not dry_run:
                    time.sleep(2)
                    inbox_count_after = self.get_inbox_count()
                    print(f"Inbox count after round: {inbox_count_after}")
                    print(f"Emails archived in this round: {inbox_count_before - inbox_count_after}")
                
                if result["success"] == 0:
                    print("No emails were successfully archived in this round, stopping")
                    break
                
                print(f"Round {rounds} complete. Checking for more emails...")
                time.sleep(1)
            
            print(f"\nArchiving process complete after {rounds} rounds")
            return {"success": total_success, "failed": total_failed}
            
        except Exception as e:
            print(f"Error during archiving process: {e}")
            raise
    
    def get_inbox_count(self) -> int:
        if not self.service:
            self.connect()
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q='in:inbox',
                maxResults=1
            ).execute()
            
            estimated_count = results.get('resultSizeEstimate', 0)
            return estimated_count
        except HttpError as error:
            print(f"Error getting inbox count: {error}")
            return 0