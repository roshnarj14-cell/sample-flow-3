import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))

def get_user(r): return r.session.get("user")

@router.get("/output", response_class=HTMLResponse)
def output_page(request: Request):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import OutputReportController, BrandController, MerchantController
    return templates.TemplateResponse("output.html", {
        "request": request, "user": user, "active": "output",
        "output_rows": OutputReportController.get_rows(),
        "years": OutputReportController.get_years(),
        "brands": BrandController.get_all(),
        "merchants": MerchantController.get_all(),
    })
