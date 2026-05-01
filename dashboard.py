import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", 302)
    from business_logic import get_enhanced_dashboard_stats
    stats = get_enhanced_dashboard_stats()
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "stats": stats, "active": "dashboard"})
