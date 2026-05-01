import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))

def get_user(request):
    u = request.session.get("user")
    if not u:
        return None
    return u

@router.get("/styles", response_class=HTMLResponse)
def styles_page(request: Request):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import StyleController, BrandController, MerchantController
    return templates.TemplateResponse("styles.html", {
        "request": request, "user": user, "active": "styles",
        "styles": StyleController.get_all(),
        "brands": BrandController.get_all(),
        "merchants": MerchantController.get_all(),
    })

@router.post("/styles/create")
def styles_create(request: Request,
    style_code: str = Form(""),
    style_name: str = Form(...),
    brand_id: str = Form(""), merchant_id: str = Form(""),
    season: str = Form(""), garment_category: str = Form(""),
    fabric: str = Form(""), color: str = Form(""),
    target_fob: str = Form(""), target_dispatch: str = Form(""),
    design_notes: str = Form("")):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import StyleController
    import time
    # Auto-generate style code if not provided
    sc = style_code.strip() if style_code.strip() else f"STY{int(time.time())}"
    data = {"style_code": sc,
            "style_name": style_name, "brand_id": int(brand_id) if brand_id else None,
            "merchant_id": int(merchant_id) if merchant_id else None,
            "season": season, "garment_category": garment_category,
            "fabric": fabric, "color": color,
            "target_fob": float(target_fob) if target_fob else None,
            "target_dispatch": target_dispatch, "design_notes": design_notes}
    StyleController.create(data, user["id"])
    return RedirectResponse("/styles", 302)

@router.post("/styles/update")
def styles_update(request: Request, style_id: int = Form(...),
    style_name: str = Form(...), brand_id: str = Form(""),
    season: str = Form(""), color: str = Form(""),
    status: str = Form(""), design_notes: str = Form("")):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import StyleController
    data = {"style_name": style_name, "brand_id": int(brand_id) if brand_id else None,
            "season": season, "color": color, "status": status, "design_notes": design_notes}
    StyleController.update(style_id, data)
    return RedirectResponse("/styles", 302)
