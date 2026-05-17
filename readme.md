# UAReady Email and Domain Validation System

A small FastAPI application to validate internationalized (EAI) email addresses and IDN domains.

Key features
- Validates Unicode email addresses (local part and domain), including non-ASCII scripts.
- Normalizes input with Unicode NFC and verifies IDNA2008/UTS46 domain conversion.
- Performs DNS checks (MX/A) when available and reports clear, localized error messages.
- Optionally sends a validation email via SMTP when SMTP credentials are configured.

Requirements
- Python 3.10 or newer
- See `requirements.txt` for exact dependency versions

Quick start (Windows)
1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the app with Uvicorn:

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

4. Open the application in your browser:

```
http://127.0.0.1:8000/
```

Configuration (environment variables)
Create a `.env` file or set environment variables for SMTP if you want the app to send emails. The app reads these variables:

- `SMTP_HOST` — SMTP server hostname (required to send mail)
- `SMTP_PORT` — SMTP server port (default: `587`)
- `SMTP_USERNAME` — SMTP username (optional)
- `SMTP_PASSWORD` — SMTP password (optional)
- `SMTP_FROM_EMAIL` — From address for outgoing mail (defaults to username or recipient)
- `SMTP_FROM_NAME` — Friendly sender name (default: `UAReady Demo`)
- `SMTP_USE_TLS` — Use STARTTLS (`true`/`false`, default: `true`)
- `SMTP_USE_SSL` — Use implicit SSL (`true`/`false`, default: `false`)
- `SMTP_TIMEOUT` — Connection timeout in seconds (default: `20`)

If SMTP is not configured the app will still validate addresses and display a delivery error when sending is attempted.

Project layout
- `main.py` — FastAPI application and route handlers
- `validators.py` — Email and domain validation logic, DNS lookups, and SMTP send helper
- `templates/` — Jinja2 HTML templates (`index.html`, `thank_you.html`, etc.)
- `static/` — Static assets (CSS)
- `tests/` — Pytest test suite

Testing
Run the test suite with:

```powershell
pytest
```

Notes
- The validator performs several checks (syntax, normalization, IDNA conversion, DNS lookups) and returns descriptive error types and messages. Use the UI or tests to explore different cases.
- For end-to-end SMTPUTF8 testing, use an SMTP server that advertises `SMTPUTF8` support.

License
See the repository for licensing information.
