# UAReady Email and Domain Validation System

Hackathon Nepal 2026 technical track demo for internationalized email and domain validation.

## What it does

This FastAPI app validates internationalized email addresses and IDN domains across scripts such as Devanagari, Latin, Arabic, Chinese, and Cyrillic. It normalizes Unicode to NFC, validates with SMTPUTF8/EAI-aware handling, and can send a confirmation email over SMTP when credentials are provided through environment variables.

## Standards covered

- SMTPUTF8 and EAI-aware email validation
- IDNA2008 and UTS #46 domain handling via IDN conversion
- Unicode NFC normalization before validation and sendout
- Clear failure messages for invalid inputs

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open:

```text
http://127.0.0.1:8000/contact-us
```

## SMTP configuration

Copy [.env.example](.env.example) to `.env` and fill in your SMTP details later. The app reads these variables at startup:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `SMTP_FROM_NAME`
- `SMTP_USE_TLS`
- `SMTP_USE_SSL`
- `SMTP_TIMEOUT`

If SMTP settings are missing, validation still works and the UI will show a clear delivery error when sending is attempted.

## Tests

Run the validation suite with:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The suite includes at least 5 valid and 5 invalid internationalized email/domain cases.

## Notes

- The demo sends confirmation mail to the submitted address.
- For live SMTPUTF8 testing, use a server that advertises UTF8 support.
- The UI is intentionally built as a hackathon-ready landing page instead of a plain form.
