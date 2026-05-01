import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))

@router.get("/alerts", response_class=HTMLResponse)
def alerts_page(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", 302)
    from business_logic import generate_alerts, get_alert_counts
    alerts = generate_alerts()
    counts = get_alert_counts()
    return templates.TemplateResponse("alerts.html", {
        "request": request, "user": user,
        "alerts": alerts, "counts": counts, "active": "alerts"
    })
