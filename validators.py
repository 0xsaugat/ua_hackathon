from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import os
import smtplib
import ssl
import unicodedata

import idna
from email_validator import EmailNotValidError, validate_email


@dataclass(frozen=True)
class EmailValidationResult:
    valid: bool
    normalized_email: str | None = None
    local_part: str | None = None
    domain_unicode: str | None = None
    domain_ascii: str | None = None
    smtp_utf8: bool = False
    error_message: str | None = None


def _normalize_text(value: str) -> str:
    return unicodedata.normalize("NFC", (value or "").strip())


def validate_idn_domain(domain: str) -> tuple[bool, str | None, str | None, str | None]:
    normalized_domain = _normalize_text(domain)
    if not normalized_domain:
        return False, None, None, "Domain name is required."

    try:
        ascii_domain = idna.encode(normalized_domain, uts46=True).decode("ascii")
    except idna.IDNAError as exc:
        return False, None, None, f"Invalid international domain name: {exc}"

    return True, normalized_domain, ascii_domain, None


def validate_email_address(email: str) -> EmailValidationResult:
    normalized_email = _normalize_text(email)
    if not normalized_email:
        return EmailValidationResult(
            valid=False,
            error_message="Email address is required. कृपया ईमेल ठेगाना प्रविष्ट गर्नुहोस्।",
        )

    try:
        result = validate_email(
            normalized_email,
            allow_smtputf8=True,
            check_deliverability=False,
        )
    except EmailNotValidError as exc:
        return EmailValidationResult(
            valid=False,
            error_message=f"Please enter a valid international email address. ({exc})",
        )

    normalized_value = getattr(result, "normalized", None) or getattr(result, "email", None) or normalized_email
    local_part = getattr(result, "local_part", None)
    domain_unicode = getattr(result, "domain", None)
    ascii_domain = getattr(result, "ascii_domain", None)
    smtp_utf8 = bool(getattr(result, "smtputf8", any(ord(char) > 127 for char in normalized_value)))

    if domain_unicode:
        domain_valid, normalized_domain, normalized_ascii_domain, domain_error = validate_idn_domain(domain_unicode)
        if not domain_valid:
            return EmailValidationResult(valid=False, error_message=domain_error)
        domain_unicode = normalized_domain
        ascii_domain = normalized_ascii_domain

    return EmailValidationResult(
        valid=True,
        normalized_email=normalized_value,
        local_part=local_part,
        domain_unicode=domain_unicode,
        domain_ascii=ascii_domain,
        smtp_utf8=smtp_utf8,
    )


def build_validation_message(validation: EmailValidationResult) -> str:
    domain_display = validation.domain_unicode or ""
    ascii_domain = validation.domain_ascii or domain_display
    normalized_email = validation.normalized_email or ""

    return (
        "UAReady validation demo message\n\n"
        f"Normalized email: {normalized_email}\n"
        f"Unicode domain: {domain_display}\n"
        f"ASCII domain: {ascii_domain}\n"
        f"SMTPUTF8 required: {'yes' if validation.smtp_utf8 else 'no'}\n\n"
        "This message was generated for the UA Adaptation and Hackathon Nepal 2026 demo."
    )


def send_validation_email(recipient_email: str, validation: EmailValidationResult) -> str:
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL", smtp_username or recipient_email).strip()
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "UAReady Demo").strip()
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() not in {"0", "false", "no"}
    smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").strip().lower() in {"1", "true", "yes"}
    smtp_timeout = float(os.getenv("SMTP_TIMEOUT", "20"))

    if not smtp_host:
        raise RuntimeError("SMTP_HOST is not configured.")

    message = EmailMessage()
    message["Subject"] = "UAReady validation result"
    message["From"] = f"{smtp_from_name} <{smtp_from_email}>"
    message["To"] = recipient_email
    message.set_content(build_validation_message(validation), subtype="plain", charset="utf-8")

    use_smtputf8 = validation.smtp_utf8 or any(ord(char) > 127 for char in recipient_email) or any(
        ord(char) > 127 for char in smtp_from_email
    )
    mail_options = ["SMTPUTF8", "BODY=8BITMIME"] if use_smtputf8 else []

    context = ssl.create_default_context()

    if smtp_use_ssl:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=smtp_timeout) as client:
            if smtp_username and smtp_password:
                client.login(smtp_username, smtp_password)
            client.send_message(message, mail_options=mail_options)
    else:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=smtp_timeout) as client:
            client.ehlo()
            if smtp_use_tls:
                client.starttls(context=context)
                client.ehlo()
            if smtp_username and smtp_password:
                client.login(smtp_username, smtp_password)
            client.send_message(message, mail_options=mail_options)

    return f"Email sent to {recipient_email} using {smtp_host}:{smtp_port}."
