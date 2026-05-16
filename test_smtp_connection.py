#!/usr/bin/env python3
"""
Test SMTP connection and email sending with the provided credentials.
"""
import os
import smtplib
import ssl
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def test_smtp_connection():
    """Test SMTP connection."""
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL", smtp_username).strip()
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "UAReady Demo").strip()
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() not in {"0", "false", "no"}
    smtp_timeout = float(os.getenv("SMTP_TIMEOUT", "20"))

    print("=" * 60)
    print("SMTP Configuration Test")
    print("=" * 60)
    print(f"SMTP Host: {smtp_host}")
    print(f"SMTP Port: {smtp_port}")
    print(f"SMTP Username: {smtp_username}")
    print(f"SMTP Use TLS: {smtp_use_tls}")
    print(f"SMTP Timeout: {smtp_timeout}s")
    print("=" * 60)

    try:
        print("\n[1/3] Connecting to SMTP server...")
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_host, smtp_port, timeout=smtp_timeout) as client:
            client.set_debuglevel(1)  # Enable debug output
            print("[2/3] Connected! Running EHLO...")
            
            if smtp_use_tls:
                print("[3/3] Starting TLS...")
                client.starttls(context=context)
                client.ehlo()
            
            print("\n[AUTH] Authenticating...")
            if smtp_username and smtp_password:
                client.login(smtp_username, smtp_password)
                print("✓ Authentication successful!")
            else:
                print("⚠ No username/password provided, skipping auth.")
        
        print("\n" + "=" * 60)
        print("✓ SMTP connection test PASSED")
        print("=" * 60)
        return True

    except Exception as exc:
        print("\n" + "=" * 60)
        print(f"✗ SMTP connection test FAILED: {exc}")
        print("=" * 60)
        return False


def test_send_email(recipient: str = None):
    """Test sending an actual email."""
    if not recipient:
        recipient = os.getenv("SMTP_USERNAME", "").strip()
    
    if not recipient:
        print("\n⚠ No recipient email provided. Skipping send test.")
        return False

    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from_email = os.getenv("SMTP_FROM_EMAIL", smtp_username).strip()
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "UAReady Demo").strip()
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").strip().lower() not in {"0", "false", "no"}
    smtp_timeout = float(os.getenv("SMTP_TIMEOUT", "20"))

    print("\n" + "=" * 60)
    print("Email Send Test")
    print("=" * 60)
    print(f"Recipient: {recipient}")
    print(f"From: {smtp_from_name} <{smtp_from_email}>")
    print("=" * 60)

    try:
        message = EmailMessage()
        message["Subject"] = "UAReady SMTP Test Email"
        message["From"] = f"{smtp_from_name} <{smtp_from_email}>"
        message["To"] = recipient
        
        body = """
This is a test email from the UAReady Email and Domain Validation System.

If you're seeing this, the SMTP email sending functionality is working!

Test Details:
- System: UA Adaptation and Hackathon Nepal 2026
- Feature: Email validation and sending
- Date: 2026-05-16

Please ignore this message if this is not your email address.
        """
        message.set_content(body, subtype="plain", charset="utf-8")

        context = ssl.create_default_context()
        
        print("\n[1/2] Connecting and sending email...")
        with smtplib.SMTP(smtp_host, smtp_port, timeout=smtp_timeout) as client:
            if smtp_use_tls:
                client.starttls(context=context)
                client.ehlo()
            
            if smtp_username and smtp_password:
                client.login(smtp_username, smtp_password)
            
            client.send_message(message)
            print("[2/2] Email sent!")

        print("\n" + "=" * 60)
        print(f"✓ Email send test PASSED")
        print(f"Email successfully sent to: {recipient}")
        print("=" * 60)
        return True

    except Exception as exc:
        print("\n" + "=" * 60)
        print(f"✗ Email send test FAILED: {exc}")
        print("=" * 60)
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("UAReady SMTP Functionality Test Suite")
    print("=" * 60 + "\n")

    # Test 1: Connection
    conn_result = test_smtp_connection()
    
    # Test 2: Send (only if connection works)
    if conn_result:
        send_result = test_send_email()
    else:
        print("\n⚠ Skipping send test due to connection failure.")
        send_result = False

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Connection Test: {'PASSED ✓' if conn_result else 'FAILED ✗'}")
    print(f"Send Test: {'PASSED ✓' if send_result else 'FAILED ✗' if conn_result else 'SKIPPED ⚠'}")
    print("=" * 60)
