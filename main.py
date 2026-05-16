import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from validators import send_validation_email, validate_email_address


load_dotenv()

app = FastAPI(title="UAReady Email and Domain Validation System")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.state.mail_sender = send_validation_email


def build_home_context(error: str | None = None, email: str = "") -> dict:
    return {"error": error, "email": email, "submitted": False}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html", build_home_context())


@app.get("/contact-us", response_class=HTMLResponse)
async def contact_us(request: Request):
    return templates.TemplateResponse(request, "index.html", build_home_context())


@app.post("/contact-us")
async def submit_contact(request: Request, email: str = Form("")):
    validation = validate_email_address(email)
    if validation.valid:
        sender = getattr(request.app.state, "mail_sender", send_validation_email)
        try:
            delivery_message = sender(validation.normalized_email or email.strip(), validation)
        except Exception as exc:  # pragma: no cover - displayed in UI
            return templates.TemplateResponse(
                request,
                "index.html",
                {
                    "error": f"Email is valid, but SMTP delivery failed: {exc}",
                    "email": email,
                    "submitted": False,
                },
                status_code=502,
            )

        return templates.TemplateResponse(
            request,
            "thank_you.html",
            {
                "email": validation.normalized_email,
                "domain_unicode": validation.domain_unicode,
                "domain_ascii": validation.domain_ascii,
                "smtp_utf8": validation.smtp_utf8,
                "delivery_message": delivery_message,
            },
        )

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "error": validation.error_message or "Please enter a valid email address.",
            "email": email,
            "submitted": False,
        },
        status_code=400,
    )


@app.get("/thank-you", response_class=HTMLResponse)
async def thank_you(request: Request):
    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
