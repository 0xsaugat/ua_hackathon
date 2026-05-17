# smtp_test.py
from dotenv import load_dotenv
import os, smtplib, ssl

load_dotenv()  # reads .env in project root

host = os.getenv("SMTP_HOST", "smtp.gmail.com")
port = int(os.getenv("SMTP_PORT", "587"))
user = os.getenv("SMTP_USERNAME")
pwd = os.getenv("SMTP_PASSWORD")
use_tls = os.getenv("SMTP_USE_TLS", "true").lower() not in ("0", "false", "no")
timeout = float(os.getenv("SMTP_TIMEOUT", "20"))

print("SMTP host:", host, "port:", port, "user:", user, "use_tls:", use_tls)

ctx = ssl.create_default_context()
try:
    s = smtplib.SMTP(host, port, timeout=timeout)
    s.set_debuglevel(0)
    s.ehlo()
    if use_tls:
        s.starttls(context=ctx)
        s.ehlo()
    s.login(user, pwd)
    print("Login OK")
    s.quit()
except Exception as e:
    print("SMTP error:", repr(e))
