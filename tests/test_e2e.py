#!/usr/bin/env python3
"""
End-to-end test: Validate an internationalized email and send via the application.
"""
import time
from validators import validate_email_address, send_validation_email

print("=" * 70)
print("UAReady Email Validation & SMTP Send End-to-End Test")
print("=" * 70)

# Test cases with internationalized addresses
test_cases = [
    ("test@example.com", "ASCII domain"),
    ("राम@नेपाल.नेपाल", "Nepali domain (full IDN)"),
    ("user@münchen.de", "German domain (IDN)"),
    ("mailbox9@क्यान.संगठन", "Nepali domain variant"),
    ("josé@españa.es", "Spanish domain (IDN)"),
]

print("\n" + "=" * 70)
print("VALIDATION & SEND TEST")
print("=" * 70)

for email, description in test_cases:
    print(f"\n[Test] {description}")
    print(f"Input: {email}")
    
    # Validate
    result = validate_email_address(email)
    
    if not result.valid:
        print(f"Status: INVALID ✗")
        print(f"Error: {result.error_message}")
        continue
    
    print(f"Status: VALID ✓")
    print(f"  Normalized: {result.normalized_email}")
    print(f"  Domain (Unicode): {result.domain_unicode}")
    print(f"  Domain (ASCII/Punycode): {result.domain_ascii}")
    print(f"  SMTPUTF8 Required: {result.smtp_utf8}")
    
    # Send
    try:
        send_msg = send_validation_email(result.normalized_email, result)
        print(f"  Email Send: {send_msg}")
    except Exception as exc:
        print(f"  Email Send FAILED: {exc}")

print("\n" + "=" * 70)
print("Test Complete")
print("=" * 70)
