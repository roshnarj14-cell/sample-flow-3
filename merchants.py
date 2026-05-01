import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))
def get_user(r): return r.session.get("user")

@router.get("/merchants", response_class=HTMLResponse)
def merchants_page(request: Request):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import MerchantController
    return templates.TemplateResponse("merchants.html", {"request": request, "user": user, "active": "merchants", "merchants": MerchantController.get_all()})

@router.post("/merchants/create")
def merchants_create(request: Request, code: str = Form(...), name: str = Form(...),
    email: str = Form(""), phone: str = Form(""), department: str = Form("")):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import MerchantController
    MerchantController.create(code, name, email, phone, department, "")
    return RedirectResponse("/merchants", 302)

@router.post("/merchants/update")
def merchants_update(request: Request, merchant_id: int = Form(...), code: str = Form(...),
    name: str = Form(...), email: str = Form(""), phone: str = Form("")):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import MerchantController
    MerchantController.update(merchant_id, code, name, email, phone, "", "", 1)
    return RedirectResponse("/merchants", 302)

@router.post("/merchants/delete")
def merchants_delete(request: Request, merchant_id: int = Form(...)):
    user = get_user(request)
    if not user or user["role"] != "Admin": return RedirectResponse("/merchants", 302)
    from database import get_connection
    conn = get_connection()
    conn.execute("UPDATE merchants SET active=0 WHERE id=?", (merchant_id,))
    conn.commit(); conn.close()
    return RedirectResponse("/merchants", 302)

@router.post("/merchants/delete")
def merchants_delete(request: Request, merchant_id: int = Form(...)):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from database import get_connection
    conn = get_connection()
    conn.execute("UPDATE merchants SET active=0 WHERE id=?", (merchant_id,))
    conn.commit(); conn.close()
    return RedirectResponse("/merchants", 302)
