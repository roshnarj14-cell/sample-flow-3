import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))

def get_user(r): return r.session.get("user")

@router.get("/brands", response_class=HTMLResponse)
def brands_page(request: Request):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import BrandController
    return templates.TemplateResponse("brands.html", {"request": request, "user": user, "active": "brands", "brands": BrandController.get_all()})

@router.post("/brands/create")
def brands_create(request: Request, code: str = Form(...), name: str = Form(...),
    country: str = Form(""), contact: str = Form(""), email: str = Form("")):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import BrandController
    BrandController.create(code, name, country, contact, email, "")
    return RedirectResponse("/brands", 302)

@router.post("/brands/update")
def brands_update(request: Request, brand_id: int = Form(...), code: str = Form(...),
    name: str = Form(...), country: str = Form(""), contact: str = Form(""), email: str = Form("")):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import BrandController
    BrandController.update(brand_id, code, name, country, contact, email, "", 1)
    return RedirectResponse("/brands", 302)

@router.post("/brands/delete")
def brands_delete(request: Request, brand_id: int = Form(...)):
    user = get_user(request)
    if not user or user["role"] != "Admin": return RedirectResponse("/brands", 302)
    from database import get_connection
    conn = get_connection()
    conn.execute("UPDATE brands SET active=0 WHERE id=?", (brand_id,))
    conn.commit(); conn.close()
    return RedirectResponse("/brands", 302)

@router.post("/brands/delete")
def brands_delete(request: Request, brand_id: int = Form(...)):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from database import get_connection
    conn = get_connection()
    conn.execute("UPDATE brands SET active=0 WHERE id=?", (brand_id,))
    conn.commit(); conn.close()
    return RedirectResponse("/brands", 302)
