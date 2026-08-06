from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from vonage_http_client import HttpRequestError, AuthenticationError
import vonage_handlers
from config import settings

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Use in-memory storage to simulate a database for demonstration purposes
verify_sessions = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})


@app.post("/send-code", response_class=HTMLResponse)
async def send_code(request: Request, email: str = Form(...)):
    try:
        response = vonage_handlers.start_email_verification(email=email)
        verify_sessions[email] = response.request_id
        return templates.TemplateResponse(
            request, "verify.html", {"request": request, "email": email}
        )
    except AuthenticationError:
        return templates.TemplateResponse(
            request, "index.html", {"error": "Authentication error."}
        )
    except HttpRequestError as e:
        error = (
            "Something went wrong. Please try again."
            if e.response.status_code != 400
            else "Invalid request. Please try again."
        )
        return templates.TemplateResponse(request, "index.html", {"error": error})


@app.post("/check-code", response_class=HTMLResponse)
async def check_code(request: Request, email: str = Form(...), code: str = Form(...)):
    request_id = verify_sessions.get(email)

    if not request_id:
        return templates.TemplateResponse(
            request,
            "verify.html",
            {
                "request": request,
                "email": email,
                "error": "Session expired. Please try again.",
            },
        )

    try:
        vonage_handlers.check_code(request_id=request_id, code=code)
        del verify_sessions[email]
        return templates.TemplateResponse(request, "success.html", {"request": request})
    except AuthenticationError:
        return templates.TemplateResponse(
            request,
            "verify.html",
            {"request": request, "email": email, "error": "Invalid verification code."},
        )
    except HttpRequestError as e:
        error = (
            "Invalid code. Please try again."
            if e.response.status_code == 400
            else "Something went wrong. Please try again."
        )
        return templates.TemplateResponse(
            request,
            "verify.html",
            {"request": request, "email": email, "error": error},
        )
