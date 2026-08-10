#!/usr/bin/env python3
from __future__ import annotations

import argparse
import getpass
import mimetypes
import os
import smtplib
import socket
import ssl
import sys
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import parseaddr
from pathlib import Path
from typing import Iterable


PROGRAM_NAME = "EmailSenderV2"
VERSION = "3.0.0"
PASSWORD_ENV = "EMAIL_SENDER_PASSWORD"


@dataclass(frozen=True, slots=True)
class MailConfig:
    smtp_server: str
    smtp_port: int
    security: str
    sender: str
    username: str | None
    password: str | None
    recipients: tuple[str, ...]
    cc: tuple[str, ...]
    bcc: tuple[str, ...]
    subject: str
    body: str
    html_body: str | None
    attachments: tuple[Path, ...]
    timeout: float


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Must be an integer."
        ) from exc

    if not 1 <= number <= 65535:
        raise argparse.ArgumentTypeError(
            "Port must be between 1 and 65535."
        )

    return number


def positive_float(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Must be a number."
        ) from exc

    if number <= 0:
        raise argparse.ArgumentTypeError(
            "Must be greater than zero."
        )

    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Send email through an authenticated SMTP server "
            "using STARTTLS or implicit TLS."
        ),
        epilog=(
            f"SMTP passwords are never accepted as command-line "
            f"arguments. Use {PASSWORD_ENV} or the secure password prompt."
        ),
    )

    parser.add_argument(
        "--smtp-server",
        help="SMTP server hostname, e.g. smtp.gmail.com",
    )

    parser.add_argument(
        "--port",
        type=positive_int,
        help=(
            "SMTP port. Defaults to 587 for STARTTLS "
            "and 465 for SSL."
        ),
    )

    parser.add_argument(
        "--security",
        choices=("starttls", "ssl"),
        default="starttls",
        help="Transport security mode (default: starttls).",
    )

    parser.add_argument(
        "-s",
        "--sender",
        help="Sender email address.",
    )

    parser.add_argument(
        "--username",
        help="SMTP username. Defaults to the sender address.",
    )

    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Do not authenticate to the SMTP server.",
    )

    parser.add_argument(
        "-r",
        "--to",
        action="append",
        default=[],
        metavar="EMAIL[,EMAIL...]",
        help=(
            "Recipient address. Repeatable; "
            "comma-separated values are accepted."
        ),
    )

    parser.add_argument(
        "--cc",
        action="append",
        default=[],
        metavar="EMAIL[,EMAIL...]",
        help=(
            "CC recipient. Repeatable; "
            "comma-separated values are accepted."
        ),
    )

    parser.add_argument(
        "--bcc",
        action="append",
        default=[],
        metavar="EMAIL[,EMAIL...]",
        help=(
            "BCC recipient. Repeatable; "
            "comma-separated values are accepted."
        ),
    )

    parser.add_argument(
        "--subject",
        help="Email subject.",
    )

    body_group = parser.add_mutually_exclusive_group()

    body_group.add_argument(
        "--body",
        help="Plain-text message body.",
    )

    body_group.add_argument(
        "--body-file",
        type=Path,
        help="Read the plain-text message body from a UTF-8 file.",
    )

    parser.add_argument(
        "--html-file",
        type=Path,
        help="Optional UTF-8 HTML alternative body.",
    )

    parser.add_argument(
        "-a",
        "--attach",
        action="append",
        default=[],
        type=Path,
        metavar="FILE",
        help="Attach a file. Repeatable.",
    )

    parser.add_argument(
        "--timeout",
        type=positive_float,
        default=20.0,
        help="SMTP socket timeout in seconds (default: 20).",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Validate and build the message "
            "without connecting to SMTP."
        ),
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    return parser


def contains_newline(value: str) -> bool:
    return "\r" in value or "\n" in value


def validate_email(
    value: str,
    field_name: str,
) -> str:
    value = value.strip()

    if not value:
        raise ValueError(
            f"{field_name} cannot be empty."
        )

    if contains_newline(value):
        raise ValueError(
            f"{field_name} contains an invalid newline character."
        )

    display_name, address = parseaddr(value)

    if display_name or address != value:
        raise ValueError(
            f"{field_name} must be a bare email address "
            f"without a display name: {value}"
        )

    if not address or "@" not in address:
        raise ValueError(
            f"Invalid {field_name}: {value}"
        )

    local_part, domain = address.rsplit(
        "@",
        1,
    )

    if (
        not local_part
        or not domain
        or "." not in domain
    ):
        raise ValueError(
            f"Invalid {field_name}: {value}"
        )

    return address


def split_addresses(
    values: Iterable[str],
    field_name: str,
) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        for candidate in value.split(","):
            candidate = candidate.strip()

            if not candidate:
                continue

            normalized = validate_email(
                candidate,
                field_name,
            )

            key = normalized.lower()

            if key not in seen:
                seen.add(key)
                result.append(normalized)

    return tuple(result)


def read_utf8_file(
    path: Path,
    label: str,
) -> str:
    path = path.expanduser()

    if not path.is_file():
        raise ValueError(
            f"{label} not found: {path}"
        )

    try:
        return path.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError as exc:
        raise ValueError(
            f"{label} must be UTF-8 encoded: {path}"
        ) from exc

    except OSError as exc:
        raise ValueError(
            f"Could not read {label.lower()}: "
            f"{path}: {exc}"
        ) from exc


def validate_attachments(
    paths: Iterable[Path],
) -> tuple[Path, ...]:
    attachments: list[Path] = []

    for raw_path in paths:
        path = raw_path.expanduser()

        if not path.is_file():
            raise ValueError(
                f"Attachment not found: {path}"
            )

        if not os.access(
            path,
            os.R_OK,
        ):
            raise ValueError(
                f"Attachment is not readable: {path}"
            )

        attachments.append(path)

    return tuple(attachments)


def prompt_if_missing(
    value: str | None,
    prompt: str,
) -> str:
    if (
        value is not None
        and value.strip()
    ):
        return value.strip()

    entered = input(prompt).strip()

    if not entered:
        raise ValueError(
            "Required value cannot be empty."
        )

    return entered


def collect_config(
    args: argparse.Namespace,
) -> MailConfig:
    smtp_server = prompt_if_missing(
        args.smtp_server,
        "SMTP server: ",
    )

    if (
        contains_newline(smtp_server)
        or any(
            character.isspace()
            for character in smtp_server
        )
    ):
        raise ValueError(
            "SMTP server must be a hostname "
            "without whitespace."
        )

    sender = validate_email(
        prompt_if_missing(
            args.sender,
            "Sender email: ",
        ),
        "sender email",
    )

    raw_to = list(args.to)

    if not raw_to:
        raw_to.append(
            prompt_if_missing(
                None,
                "Recipient email: ",
            )
        )

    recipients = split_addresses(
        raw_to,
        "recipient email",
    )

    cc = split_addresses(
        args.cc,
        "CC email",
    )

    bcc = split_addresses(
        args.bcc,
        "BCC email",
    )

    if (
        not recipients
        and not cc
        and not bcc
    ):
        raise ValueError(
            "At least one recipient is required."
        )

    subject = args.subject

    if subject is None:
        subject = input(
            "Subject: "
        )

    if contains_newline(subject):
        raise ValueError(
            "Subject cannot contain newline characters."
        )

    if args.body_file is not None:
        body = read_utf8_file(
            args.body_file,
            "Body file",
        )

    elif args.body is not None:
        body = args.body

    else:
        body = input(
            "Message: "
        )

    html_body = (
        read_utf8_file(
            args.html_file,
            "HTML file",
        )
        if args.html_file is not None
        else None
    )

    attachments = validate_attachments(
        args.attach
    )

    port = args.port

    if port is None:
        port = (
            465
            if args.security == "ssl"
            else 587
        )

    username: str | None
    password: str | None

    if args.no_auth:
        username = None
        password = None

    else:
        username = (
            args.username
            or sender
        ).strip()

        if not username:
            raise ValueError(
                "SMTP username cannot be empty."
            )

        password = os.environ.get(
            PASSWORD_ENV
        )

        if (
            not password
            and not args.dry_run
        ):
            password = getpass.getpass(
                "SMTP password/app password: "
            )

        if (
            not password
            and not args.dry_run
        ):
            raise ValueError(
                "SMTP password cannot be empty."
            )

    return MailConfig(
        smtp_server=smtp_server,
        smtp_port=port,
        security=args.security,
        sender=sender,
        username=username,
        password=password,
        recipients=recipients,
        cc=cc,
        bcc=bcc,
        subject=subject,
        body=body,
        html_body=html_body,
        attachments=attachments,
        timeout=args.timeout,
    )


def add_attachment(
    message: EmailMessage,
    path: Path,
) -> None:
    mime_type, encoding = mimetypes.guess_type(
        path.name
    )

    if (
        mime_type is None
        or encoding is not None
    ):
        maintype = "application"
        subtype = "octet-stream"

    else:
        maintype, subtype = mime_type.split(
            "/",
            1,
        )

    try:
        data = path.read_bytes()

    except OSError as exc:
        raise ValueError(
            f"Could not read attachment: "
            f"{path}: {exc}"
        ) from exc

    message.add_attachment(
        data,
        maintype=maintype,
        subtype=subtype,
        filename=path.name,
    )


def build_message(
    config: MailConfig,
) -> EmailMessage:
    message = EmailMessage()

    message["From"] = config.sender

    if config.recipients:
        message["To"] = ", ".join(
            config.recipients
        )

    if config.cc:
        message["Cc"] = ", ".join(
            config.cc
        )

    message["Subject"] = config.subject

    message.set_content(
        config.body
    )

    if config.html_body is not None:
        message.add_alternative(
            config.html_body,
            subtype="html",
        )

    for attachment in config.attachments:
        add_attachment(
            message,
            attachment,
        )

    return message


def envelope_recipients(
    config: MailConfig,
) -> list[str]:
    addresses: list[str] = []
    seen: set[str] = set()

    all_addresses = (
        *config.recipients,
        *config.cc,
        *config.bcc,
    )

    for address in all_addresses:
        key = address.lower()

        if key not in seen:
            seen.add(key)
            addresses.append(address)

    return addresses


def authenticate(
    server: smtplib.SMTP,
    config: MailConfig,
) -> None:
    if config.username is None:
        return

    if not config.password:
        raise ValueError(
            "SMTP password is required "
            "for authenticated sending."
        )

    server.login(
        config.username,
        config.password,
    )


def send_message(
    config: MailConfig,
    message: EmailMessage,
) -> dict[str, tuple[int, bytes]]:
    context = ssl.create_default_context()

    recipients = envelope_recipients(
        config
    )

    if config.security == "ssl":
        with smtplib.SMTP_SSL(
            config.smtp_server,
            config.smtp_port,
            timeout=config.timeout,
            context=context,
        ) as server:

            authenticate(
                server,
                config,
            )

            return server.send_message(
                message,
                from_addr=config.sender,
                to_addrs=recipients,
            )

    with smtplib.SMTP(
        config.smtp_server,
        config.smtp_port,
        timeout=config.timeout,
    ) as server:

        server.ehlo()

        server.starttls(
            context=context
        )

        server.ehlo()

        authenticate(
            server,
            config,
        )

        return server.send_message(
            message,
            from_addr=config.sender,
            to_addrs=recipients,
        )


def print_summary(
    config: MailConfig,
) -> None:
    print(
        f"SMTP server:    "
        f"{config.smtp_server}:{config.smtp_port}"
    )

    print(
        f"Security:       "
        f"{config.security}"
    )

    print(
        f"Sender:         "
        f"{config.sender}"
    )

    print(
        f"To:             "
        f"{', '.join(config.recipients) or '-'}"
    )

    print(
        f"Cc:             "
        f"{', '.join(config.cc) or '-'}"
    )

    print(
        f"Bcc count:      "
        f"{len(config.bcc)}"
    )

    print(
        f"Subject:        "
        f"{config.subject}"
    )

    print(
        f"Attachments:    "
        f"{len(config.attachments)}"
    )

    print(
        "Authentication: "
        + (
            "disabled"
            if config.username is None
            else "enabled"
        )
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = collect_config(
            args
        )

        message = build_message(
            config
        )

    except (
        EOFError,
        KeyboardInterrupt,
    ):
        print(
            "\n[ERROR] Input cancelled.",
            file=sys.stderr,
        )

        return 130

    except ValueError as exc:
        print(
            f"[ERROR] {exc}",
            file=sys.stderr,
        )

        return 2

    if args.dry_run:
        print(
            "[OK] Message validated successfully. "
            "No email was sent."
        )

        print_summary(
            config
        )

        return 0

    try:
        refused = send_message(
            config,
            message,
        )

    except smtplib.SMTPAuthenticationError:
        print(
            "[ERROR] SMTP authentication failed. "
            "Check the username and password/app password.",
            file=sys.stderr,
        )

        return 1

    except smtplib.SMTPNotSupportedError as exc:
        print(
            f"[ERROR] SMTP feature not supported: {exc}",
            file=sys.stderr,
        )

        return 1

    except smtplib.SMTPRecipientsRefused as exc:
        print(
            "[ERROR] All recipients were refused: "
            f"{exc.recipients}",
            file=sys.stderr,
        )

        return 1

    except smtplib.SMTPSenderRefused as exc:
        print(
            f"[ERROR] Sender was refused: "
            f"{exc.sender}",
            file=sys.stderr,
        )

        return 1

    except smtplib.SMTPResponseException as exc:
        if isinstance(
            exc.smtp_error,
            bytes,
        ):
            error_text = exc.smtp_error.decode(
                errors="replace"
            )
        else:
            error_text = str(
                exc.smtp_error
            )

        print(
            f"[ERROR] SMTP error "
            f"{exc.smtp_code}: {error_text}",
            file=sys.stderr,
        )

        return 1

    except (
        smtplib.SMTPException,
        ssl.SSLError,
        socket.timeout,
        TimeoutError,
        OSError,
    ) as exc:
        print(
            f"[ERROR] Could not send email: {exc}",
            file=sys.stderr,
        )

        return 1

    if refused:
        print(
            "[WARN] Email accepted for at least one "
            "recipient, but some were refused:"
        )

        for (
            address,
            (
                code,
                response,
            ),
        ) in refused.items():

            if isinstance(
                response,
                bytes,
            ):
                text = response.decode(
                    errors="replace"
                )
            else:
                text = str(
                    response
                )

            print(
                f"  - {address}: "
                f"{code} {text}"
            )

        return 1

    print(
        "[OK] Email sent successfully."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
