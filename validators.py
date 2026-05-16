from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
import os
import smtplib
import ssl
import unicodedata
import re
import socket

import idna
import dns.resolver
import dns.exception
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


# --- Script helpers from external validator (Nepal ID)
NEPALI_RANGE = (0x0900, 0x097F)   # Devanagari block

def _script_of(char: str) -> str:
    cp = ord(char)
    if 0x0041 <= cp <= 0x007A:
        return "Latin"
    if 0x0900 <= cp <= 0x097F:
        return "Devanagari"
    if 0x0600 <= cp <= 0x06FF:
        return "Arabic"
    if 0x4E00 <= cp <= 0x9FFF:
        return "Han"
    if 0x0400 <= cp <= 0x04FF:
        return "Cyrillic"
    if 0x0370 <= cp <= 0x03FF:
        return "Greek"
    return "Other"

def _is_nepali(text: str) -> bool:
    return any(NEPALI_RANGE[0] <= ord(c) <= NEPALI_RANGE[1] for c in text)

def _contains_non_ascii(text: str) -> bool:
    return any(ord(c) > 127 for c in text)



def validate_idn_domain(domain: str) -> tuple[bool, str | None, str | None, str | None]:
    normalized_domain = _normalize_text(domain)
    if not normalized_domain:
        return False, None, None, "Domain name is required."

    try:
        ascii_domain = idna.encode(normalized_domain, uts46=True).decode("ascii")
    except idna.IDNAError as exc:
        return False, None, None, f"Invalid international domain name: {exc}"

    return True, normalized_domain, ascii_domain, None


# --- IDN / domain validator from Nepal validator (keeps DNS checks)
def validate_domain_eai(domain: str) -> dict:
    # reuse NFC normalization and idna conversion, return dict similar to external validator
    result = {
        "input": domain,
        "valid": False,
        "punycode": None,
        "is_idn": False,
        "idna2008_valid": False,
        "has_mx": False,
        "has_a": False,
        "mx_records": [],
        "error": None,
        "is_nepali_domain": False,
    }

    domain = unicodedata.normalize("NFC", domain.strip().lower())
    result["is_nepali_domain"] = _is_nepali(domain)
    result["is_idn"] = _contains_non_ascii(domain)

    try:
        labels = domain.split(".")
        encoded_labels = []
        for label in labels:
            if _contains_non_ascii(label):
                encoded_labels.append(idna.encode(label, uts46=True).decode("ascii"))
            else:
                encoded_labels.append(label)
        punycode = ".".join(encoded_labels)
        result["punycode"] = punycode
        result["idna2008_valid"] = True
    except (idna.core.InvalidCodepoint, idna.core.InvalidCodepointContext, UnicodeError) as e:
        result["error"] = f"IDNA encoding error: {e}"
        return result

    lookup_domain = result["punycode"] or domain

    # MX lookup
    try:
        mx_records = dns.resolver.resolve(lookup_domain, "MX", lifetime=5)
        result["mx_records"] = [str(r.exchange).rstrip(".") for r in mx_records]
        result["has_mx"] = True
    except Exception:
        pass

    # A / AAAA lookup
    try:
        dns.resolver.resolve(lookup_domain, "A", lifetime=5)
        result["has_a"] = True
    except Exception:
        try:
            dns.resolver.resolve(lookup_domain, "AAAA", lifetime=5)
            result["has_a"] = True
        except Exception:
            pass

    result["valid"] = result["idna2008_valid"]
    return result


# --- EAI / email validator from Nepal validator (returns dict)
def validate_email_eai(email: str) -> dict:
    result = {
        "input": email,
        "valid": False,
        "local_part": None,
        "domain_part": None,
        "is_eai": False,
        "is_smtputf8_compatible": False,
        "normalized": None,
        "domain_info": None,
        "error": None,
        "checks": {
            "syntax": False,
            "unicode_normalized": False,
            "local_part_valid": False,
            "domain_valid": False,
            "smtputf8": False,
        },
        "nepali_message": None,
    }

    email = email.strip()

    if email.count("@") != 1:
        result["error"] = "Email must contain exactly one @ symbol."
        result["nepali_message"] = "इमेलमा एकमात्र @ चिह्न हुनुपर्छ।"
        return result

    local, domain = email.rsplit("@", 1)
    result["local_part"] = local
    result["domain_part"] = domain

    if not local:
        result["error"] = "Local part (before @) cannot be empty."
        result["nepali_message"] = "@ अघिको भाग खाली हुन हुँदैन।"
        return result

    if not domain:
        result["error"] = "Domain part (after @) cannot be empty."
        result["nepali_message"] = "@ पछिको डोमेन भाग खाली हुन हुँदैन।"
        return result

    result["is_eai"] = _contains_non_ascii(local) or _contains_non_ascii(domain)

    local_norm = unicodedata.normalize("NFC", local)
    domain_norm = unicodedata.normalize("NFC", domain)
    result["normalized"] = f"{local_norm}@{domain_norm}"
    result["checks"]["unicode_normalized"] = True

    # Check for illegal special characters in local part
    # Allowed: alphanumeric, dots (.), hyphens (-), underscores (_), and non-ASCII for EAI
    illegal_chars_in_local = set()
    for char in local_norm:
        if char.isalnum() or char in ".!#$%&'*+-/=?^_`{|}~" or ord(char) > 127:
            continue
        illegal_chars_in_local.add(char)
    if illegal_chars_in_local:
        result["error"] = f"Local part contains invalid characters: {', '.join(sorted(illegal_chars_in_local))}"
        result["nepali_message"] = "स्थानीय भागमा अमान्य वर्णहरू छन्।"
        return result

    # Check for spaces (universal rule violation)
    if " " in local_norm or " " in domain_norm:
        result["error"] = "Email address cannot contain spaces."
        result["nepali_message"] = "इमेल ठेगानामा खाली स्थान हुन हुँदैन।"
        return result

    # Check for consecutive dots
    if ".." in local_norm or ".." in domain_norm:
        result["error"] = "Email cannot contain consecutive dots (..)."
        result["nepali_message"] = "इमेलमा लगातार दुई बिन्दु (..) हुन हुँदैन।"
        return result

    # Check for dots at start/end of local part
    if local_norm.startswith(".") or local_norm.endswith("."):
        result["error"] = "Local part cannot start or end with a dot (.)."
        result["nepali_message"] = "स्थानीय भाग बिन्दु (.)बाट सुरु वा अन्त हुन हुँदैन।"
        return result

    # Check for dots at start/end of domain
    if domain_norm.startswith(".") or domain_norm.endswith("."):
        result["error"] = "Domain cannot start or end with a dot (.)."
        result["nepali_message"] = "डोमेन बिन्दु (.)बाट सुरु वा अन्त हुन हुँदैन।"
        return result

    # Domain must have at least one dot (for TLD)
    if "." not in domain_norm:
        result["error"] = "Domain must have a valid TLD (e.g., example.com)."
        result["nepali_message"] = "डोमेनमा मान्य TLD हुनुपर्छ (उदाहरण: example.com)।"
        return result

    result["checks"]["local_part_valid"] = True
    result["checks"]["syntax"] = True

    domain_info = validate_domain_eai(domain_norm)
    result["domain_info"] = domain_info

    if not domain_info["idna2008_valid"]:
        result["error"] = f"Domain is invalid: {domain_info.get('error', 'Unknown error')}"
        result["nepali_message"] = "डोमेन नाम अमान्य छ।"
        return result

    result["checks"]["domain_valid"] = True

    if result["is_eai"]:
        result["is_smtputf8_compatible"] = True
        result["checks"]["smtputf8"] = True
    else:
        result["checks"]["smtputf8"] = True

    result["valid"] = True
    result["nepali_message"] = "इमेल ठेगाना मान्य छ।"
    return result


def validate_email_address(email: str) -> EmailValidationResult:
    # Use the Nepal EAI validator for comprehensive checks and DNS lookups
    try:
        res = validate_email_eai(email)
    except Exception as exc:
        return EmailValidationResult(valid=False, error_message=f"Validator error: {exc}")

    if not res.get("valid"):
        err = res.get("error") or res.get("nepali_message") or "Invalid"
        return EmailValidationResult(valid=False, error_message=err)

    normalized_value = res.get("normalized")
    local_part = res.get("local_part")
    domain_unicode = res.get("domain_part")
    domain_info = res.get("domain_info") or {}
    ascii_domain = domain_info.get("punycode")
    smtp_utf8 = bool(res.get("is_smtputf8_compatible", False))

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
