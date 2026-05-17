import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from validators import validate_email_address, send_validation_email


load_dotenv()

app = FastAPI(title="UAReady Email and Domain Validation System")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.state.mail_sender = send_validation_email


def build_home_context(error: str | None = None, email: str = "", error_type: str | None = None) -> dict:
    return {"error": error, "error_type": error_type, "email": email, "submitted": False}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
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
                    "error_type": "SMTP Error",
                    "email": email,
                    "submitted": False,
                },
                status_code=502,
            )

        # After successful send, redirect to thank-you page (keeps behavior consistent with tests)
        return RedirectResponse(url="/thank-you", status_code=303)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "error": validation.error_message or "Please enter a valid international email address.",
            "error_type": validation.error_type or "Validation Error",
            "email": email,
            "submitted": False,
        },
        status_code=200,
    )


@app.post("/")
async def submit_contact_root(request: Request, email: str = Form("")):
    # Delegate to the existing handler so the same logic applies,
    # but posting to `/` keeps the browser URL at the base path.
    return await submit_contact(request, email)


@app.get("/thank-you", response_class=HTMLResponse)
async def thank_you(request: Request):
    return templates.TemplateResponse(request, "thank_you.html", {})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
