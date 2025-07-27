# Gmail Email Archiver

A Python tool to archive all emails from your Gmail inbox using the Gmail API. Emails are moved from the inbox to the archive (All Mail), keeping them accessible while decluttering your inbox.

## Features

- **Safe archiving**: Emails are moved to archive, not deleted
- **Batch processing**: Process emails in configurable batches for efficiency
- **Dry run mode**: Preview what would be archived without making changes
- **Progress tracking**: Real-time feedback during the archiving process
- **OAuth authentication**: Secure Google OAuth 2.0 authentication
- **Status checking**: Check inbox count without making changes

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install archive-all-my-mails
```

### Option 2: Install from source

1. Clone this repository:

   ```bash
   git clone <repository-url>
   cd archive-all-my-mails
   ```

2. Install dependencies using uv (recommended) or pip:

   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -e .
   ```

## Gmail API OAuth Setup

Before using the archiver, you need to set up OAuth credentials with Google.

### Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" at the top of the page
3. Click "New Project"
4. Enter a project name (e.g., "gmail-archiver")
5. Click "Create"

### Step 2: Enable the Gmail API

1. In your project, go to "APIs & Services" > "Library"
2. Search for "Gmail API"
3. Click on "Gmail API" from the results
4. Click "Enable"

### Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in the required application information
   - Add your email to test users
4. For application type, select "Desktop application"
5. Give it a name (e.g., "Gmail Archiver")
6. Click "Create"

### Step 4: Get Your Credentials

1. After creating the OAuth client, you'll see your credentials:
   - **Client ID** (looks like: `xxxxx.apps.googleusercontent.com`)
   - **Client Secret** (a random string)
2. Copy these values - you'll need to provide them when running the script
3. Keep these credentials secure and do not share them

## Usage

### Basic Commands

```bash
# Check inbox status (dry run to see what would be archived)
archive-gmail --dry-run

# Archive all emails with confirmation prompt
archive-gmail

# Archive all emails without confirmation
archive-gmail --yes

# Provide credentials as command line arguments
archive-gmail --client-id "your-client-id" --client-secret "your-secret"

# Process in smaller batches (default is 100)
archive-gmail --batch-size 50
```

### First Run Authentication

When you first run the script:

1. You'll be prompted to enter your Client ID and Client Secret
2. A browser window will open automatically
3. Sign in to your Google account
4. Grant permission to access your Gmail
5. The script will save authentication tokens locally (`token.pickle`) for future use

### Command Line Options

- `--dry-run`: Preview what would be archived without making changes
- `--client-id`: Google OAuth Client ID
- `--client-secret`: Google OAuth Client Secret
- `--batch-size`: Number of emails to process in each batch (default: 100)
- `--yes`: Skip confirmation prompt

## How It Works

1. **Authentication**: Uses OAuth 2.0 to securely connect to your Gmail account
2. **Email Discovery**: Fetches all emails from your inbox
3. **Batch Processing**: Processes emails in configurable batches for efficiency
4. **Archiving**: Removes the "INBOX" label from emails, moving them to archive
5. **Reporting**: Provides feedback on success/failure counts

## Safety Features

- **No email deletion**: Emails are archived, not deleted
- **Dry run mode**: Test the process without making changes
- **Confirmation prompts**: Asks for confirmation before archiving (unless `--yes` flag is used)
- **Batch processing**: Handles large inboxes efficiently
- **Error handling**: Graceful handling of API errors and rate limits

## Security Notes

- Your Client ID and Client Secret are sensitive - keep them secure
- The script creates a `token.pickle` file to store authentication tokens
- Never share your credentials or commit them to version control
- The script only requests the minimum required Gmail permissions

## Troubleshooting

### Common Issues

**"Invalid credentials"**

- Double-check your Client ID and Client Secret
- Ensure you're using the correct credentials from Google Cloud Console

**"Access denied"**

- Make sure you've enabled the Gmail API in Google Cloud Console
- Verify OAuth consent screen is properly configured
- Check that your email is added as a test user

**"Browser doesn't open for authentication"**

- Try deleting `token.pickle` and re-authenticating
- Ensure you have a default browser configured
- Check firewall settings that might block the redirect

**"Rate limit exceeded"**

- The script handles rate limits automatically with exponential backoff
- If issues persist, try reducing the batch size with `--batch-size`

### Getting Help

If you encounter issues:

1. Try running with `--dry-run` first to test authentication
2. Check the error messages for specific guidance
3. Verify your Google Cloud Console setup matches the instructions above
4. Delete `token.pickle` and re-authenticate if authentication seems stuck

## License

This project is provided as-is for personal use. Please review and comply with Google's API Terms of Service when using this tool.
