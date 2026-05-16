from dotenv import load_dotenv
from validators import validate_email_address, send_validation_email

load_dotenv()

recipient = "mailbox9@क्यान.संगठन"
print("Recipient:", recipient)

validation = validate_email_address(recipient)
print("Valid:", validation.valid)
if not validation.valid:
    print("Validation error:", validation.error_message)
else:
    try:
        result = send_validation_email(validation.normalized_email, validation)
        print("Send result:", result)
    except Exception as exc:
        print("SMTP error:", repr(exc))
