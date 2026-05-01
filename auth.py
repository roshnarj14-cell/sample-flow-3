import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/dashboard", 302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@router.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    from auth_controller import AuthController
    user = AuthController.login(username, password)
    if user:
        request.session["user"] = user
        return RedirectResponse("/dashboard", 302)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", 302)
