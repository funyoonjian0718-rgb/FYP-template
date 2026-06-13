import os

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()

_base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
templates = Jinja2Templates(directory=os.path.join(_base, "frontend", "templates"))


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse, include_in_schema=False)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/ask", response_class=HTMLResponse, include_in_schema=False)
def ask_page(request: Request):
    return templates.TemplateResponse("ask.html", {"request": request})


@router.get("/history", response_class=HTMLResponse, include_in_schema=False)
def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})


@router.get("/profile", response_class=HTMLResponse, include_in_schema=False)
def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

