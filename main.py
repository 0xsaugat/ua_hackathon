import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from validators import validate_email_address


load_dotenv()

app = FastAPI(title="UAReady Email and Domain Validation System")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def build_home_context(error: str | None = None, email: str = "", error_type: str | None = None) -> dict:
    return {"error": error, "error_type": error_type, "email": email, "submitted": False}


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
        status_code=400,
    )


@app.get("/thank-you", response_class=HTMLResponse)
async def thank_you(request: Request):
    return templates.TemplateResponse(request, "thank_you.html", {})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
