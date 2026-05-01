import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))
def get_user(r): return r.session.get("user")

@router.get("/users", response_class=HTMLResponse)
def users_page(request: Request):
    user = get_user(request)
    if not user or user["role"] != "Admin": return RedirectResponse("/dashboard", 302)
    from auth_controller import AuthController
    return templates.TemplateResponse("users.html", {"request": request, "user": user, "active": "users", "users": AuthController.get_all_users()})

@router.post("/users/create")
def users_create(request: Request, username: str = Form(...), full_name: str = Form(...),
    role: str = Form(...), email: str = Form(""), password: str = Form(...)):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from auth_controller import AuthController
    AuthController.create_user(username, password, full_name, role, email)
    return RedirectResponse("/users", 302)

@router.post("/users/update")
def users_update(request: Request, user_id: int = Form(...), full_name: str = Form(...),
    role: str = Form(...), email: str = Form(""), password: str = Form("")):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from auth_controller import AuthController
    AuthController.update_user(user_id, full_name, role, email, 1)
    if password:
        AuthController.change_password(user_id, password)
    return RedirectResponse("/users", 302)
