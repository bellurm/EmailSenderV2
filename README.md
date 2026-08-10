# EmailSenderV2

A secure command-line email client written in Python using SMTP, TLS, and Python's modern `EmailMessage` API.

EmailSenderV2 can send plain-text or HTML email, multiple attachments, CC/BCC recipients, and authenticated SMTP messages using either STARTTLS or implicit TLS.

The project uses only the Python standard library.

---

## Features

- SMTP email sending
- STARTTLS support
- Implicit TLS / SMTP SSL support
- Secure certificate validation
- Multiple recipients
- CC recipients
- BCC recipients
- Plain-text email
- Optional HTML alternative
- Multiple file attachments
- Automatic MIME type detection
- Secure password prompt
- Environment-variable password support
- No SMTP passwords in command-line arguments
- SMTP authentication
- Optional unauthenticated SMTP mode
- Configurable SMTP server and port
- Configurable connection timeout
- Input validation
- Duplicate-recipient filtering
- UTF-8 body files
- Dry-run validation
- Detailed SMTP error handling
- Partial recipient rejection reporting

---

## Requirements

- Python 3.10 or newer
- Access to an SMTP server

No third-party Python packages are required.

---

## Basic Usage

Run:

```bash
python3 email_sender.py
```

When required values are missing, EmailSenderV2 asks for them interactively:

```text
SMTP server:
Sender email:
Recipient email:
Subject:
Message:
SMTP password/app password:
```

The SMTP password is entered using a hidden password prompt.

---

## Command-Line Usage

Example using Gmail-compatible SMTP settings:

```bash
python3 email_sender.py \
    --smtp-server smtp.gmail.com \
    --sender sender@example.com \
    --to receiver@example.com \
    --subject "Hello" \
    --body "Hello from EmailSenderV2"
```

With the default security mode:

```text
STARTTLS
```

the default port is:

```text
587
```

---

## SMTP Password

EmailSenderV2 intentionally does not provide:

```text
--password
-p
```

command-line options.

Passwords supplied through command-line arguments can become visible through process inspection or shell history.

If authentication is enabled and no environment password exists, EmailSenderV2 asks securely:

```text
SMTP password/app password:
```

The characters are not displayed while typing.

---

## Password Environment Variable

For automation, the password can be supplied through:

```text
EMAIL_SENDER_PASSWORD
```

Linux/macOS example:

```bash
export EMAIL_SENDER_PASSWORD="your-app-password"

python3 email_sender.py \
    --smtp-server smtp.example.com \
    --sender sender@example.com \
    --to receiver@example.com \
    --subject "Automated report" \
    --body "Report completed."
```

After use:

```bash
unset EMAIL_SENDER_PASSWORD
```

Interactive password entry is preferable when long-term environment-variable storage is unnecessary.

---

## SMTP Username

By default, the SMTP username is the sender email address.

Use another username:

```bash
python3 email_sender.py \
    --smtp-server smtp.example.com \
    --sender sender@example.com \
    --username smtp-account \
    --to receiver@example.com \
    --subject "Test" \
    --body "Hello"
```

---

## STARTTLS

STARTTLS is the default transport mode.

```bash
python3 email_sender.py \
    --smtp-server smtp.example.com \
    --security starttls \
    --sender sender@example.com \
    --to receiver@example.com \
    --subject "STARTTLS test" \
    --body "Encrypted SMTP transport."
```

Default port:

```text
587
```

The connection begins as SMTP and is upgraded to TLS before authentication and message transmission.

---

## Implicit TLS / SMTP SSL

For SMTP servers that require TLS immediately:

```bash
python3 email_sender.py \
    --smtp-server smtp.example.com \
    --security ssl \
    --sender sender@example.com \
    --to receiver@example.com \
    --subject "TLS test" \
    --body "Hello"
```

Default port:

```text
465
```

---

## Custom Port

Override the automatic port:

```bash
python3 email_sender.py \
    --smtp-server mail.example.com \
    --port 2525 \
    --sender sender@example.com \
    --to receiver@example.com \
    --subject "Custom SMTP" \
    --body "Hello"
```

---

## Multiple Recipients

Comma-separated recipients:

```bash
python3 email_sender.py \
    --smtp-server smtp.example.com \
    --sender sender@example.com \
    --to alice@example.com,bob@example.com \
    --subject "Team message" \
    --body "Hello everyone"
```

Or repeat the option:

```bash
python3 email_sender.py \
    --smtp-server smtp.example.com \
    --sender sender@example.com \
    --to alice@example.com \
    --to bob@example.com \
    --subject "Team message" \
    --body "Hello everyone"
```

Duplicate addresses are automatically removed.

---

## CC

```bash
python3 email_sender.py \
    --smtp-server smtp.example.com \
    --sender sender@example.com \
    --to alice@example.com \
    --cc manager@example.com \
    --subject "Report" \
    --body "Report attached."
```

---

## BCC

```bash
python3 email_sender.py \
    --smtp-server smtp.example.com \
    --sender sender@example.com \
    --to alice@example.com \
    --bcc archive@example.com \
    --subject "Report" \
    --body "Hello"
```

BCC recipients are included in the SMTP envelope but are not added to the visible email headers.

---

## File Attachments

Attach a file:

```bash
python3 email_sender.py \
    --smtp-server smtp.example.com \
    --sender sender@example.com \
    --to receiver@example.com \
    --subject "Document" \
    --body "Please see the attachment." \
    --attach report.pdf
```

Multiple attachments:

```bash
python3 email_sender.py \
    --smtp-server smtp.example.com \
    --sender sender@example.com \
    --to receiver@example.com \
    --subject "Files" \
    --body "Files attached." \
    --attach report.pdf \
    --attach screenshot.png \
    --attach archive.zip
```

EmailSenderV2 automatically determines MIME types where possible.

Unknown file types are sent as:

```text
application/octet-stream
```

---

## Body From File

Instead of placing a long message on the command line:

```bash
python3 email_sender.py \
    --smtp-server smtp.example.com \
    --sender sender@example.com \
    --to receiver@example.com \
    --subject "Report" \
    --body-file message.txt
```

The body file must be UTF-8 encoded.

---

## HTML Email

Provide an HTML alternative:

```bash
python3 email_sender.py \
    --smtp-server smtp.example.com \
    --sender sender@example.com \
    --to receiver@example.com \
    --subject "HTML message" \
    --body "Plain-text fallback" \
    --html-file message.html
```

The resulting message contains:

```text
text/plain
text/html
```

email alternatives.

Mail clients can choose the most appropriate representation.

---

## Dry Run

Validate the message without connecting to the SMTP server:

```bash
python3 email_sender.py \
    --smtp-server smtp.example.com \
    --sender sender@example.com \
    --to receiver@example.com \
    --subject "Test" \
    --body "Hello" \
    --dry-run
```

Example output:

```text
[OK] Message validated successfully. No email was sent.

SMTP server:    smtp.example.com:587
Security:       starttls
Sender:         sender@example.com
To:             receiver@example.com
Cc:             -
Bcc count:      0
Subject:        Test
Attachments:    0
Authentication: enabled
```

Dry-run mode does not connect to SMTP and does not require the SMTP password.

---

## Unauthenticated SMTP

For trusted local relays that do not require SMTP authentication:

```bash
python3 email_sender.py \
    --smtp-server smtp.internal.example \
    --no-auth \
    --sender sender@example.com \
    --to receiver@example.com \
    --subject "Internal message" \
    --body "Hello"
```

Transport encryption is still controlled by:

```text
--security
```

---

## Connection Timeout

Default:

```text
20 seconds
```

Custom timeout:

```bash
python3 email_sender.py \
    --smtp-server smtp.example.com \
    --timeout 10 \
    --sender sender@example.com \
    --to receiver@example.com \
    --subject "Test" \
    --body "Hello"
```

---

## Email Construction

EmailSenderV2 uses Python's modern:

```text
email.message.EmailMessage
```

API.

Conceptually:

```text
Sender / Recipients
        │
        ▼
Subject + Plain Body
        │
        ├──── Optional HTML Body
        │
        ├──── Optional Attachments
        │
        ▼
EmailMessage
        │
        ▼
SMTP Connection
        │
        ▼
TLS
        │
        ▼
Authentication
        │
        ▼
SMTP Envelope
        │
        ▼
Message Delivery
```

---

## TLS Security

EmailSenderV2 creates its TLS configuration using Python's default SSL context.

This enables normal certificate validation and hostname verification provided by the operating system and Python SSL stack.

The project does not intentionally disable TLS certificate verification.

---

## Error Handling

The application handles common SMTP failures including:

- Authentication errors
- Rejected senders
- Rejected recipients
- Unsupported SMTP features
- TLS errors
- Connection errors
- Socket timeouts
- SMTP response errors
- Missing attachments
- Invalid email addresses
- Invalid ports

If an SMTP server accepts the message for some recipients but rejects others, the rejected recipients are reported separately.

---

## Security Improvements

Compared with the original version, EmailSenderV2 no longer:

- Accepts SMTP passwords through `-p`
- Accepts passwords through `--password`
- Uses the deprecated project-level `optparse` workflow
- Uses manual `MIMEBase` attachment construction
- Assumes every SMTP server uses STARTTLS port 587
- Uses broad `except Exception` handling for SMTP operations

The current version provides explicit transport security configuration and more specific error handling.

---

## Example Automation

```bash
export EMAIL_SENDER_PASSWORD="app-password"

python3 email_sender.py \
    --smtp-server smtp.example.com \
    --sender alerts@example.com \
    --to admin@example.com \
    --subject "Backup completed" \
    --body-file backup-report.txt \
    --attach backup.log
```

This makes EmailSenderV2 usable from scripts while keeping the SMTP password out of command-line arguments.

---

## What This Project Demonstrates

EmailSenderV2 demonstrates practical knowledge of:

- Python
- SMTP
- TLS
- SSL
- STARTTLS
- Email MIME structure
- File attachments
- HTML email
- CLI development
- Secure secret input
- Input validation
- Network error handling
- Python standard library
- Automation

---

## Limitations

EmailSenderV2 is a lightweight SMTP client rather than a complete mail platform.

It does not currently provide:

- OAuth2 authentication
- Contact management
- Email templates
- Mail queues
- Retry queues
- Delivery tracking
- IMAP
- POP3
- Bulk marketing functionality

Some email providers require application passwords, OAuth2, or provider-specific SMTP configuration.

Always follow the authentication and security requirements of the SMTP provider being used.

---

## Responsible Use

Use EmailSenderV2 only with email accounts and SMTP servers you are authorized to use.

Do not use the project for spam, phishing, unsolicited bulk email, or impersonation.

---

## Author

**Cyber Worm**

GitHub: [@bellurm](https://github.com/bellurm)
