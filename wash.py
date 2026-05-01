import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))
def get_user(r): return r.session.get("user")

@router.get("/wash", response_class=HTMLResponse)
def wash_page(request: Request):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import WashController
    from business_logic import calc_wash_delay, get_wash_otif, WASH_LEAD_TIMES
    from datetime import date, timedelta
    records = WashController().get_all()
    # Attach delay info + expected receive date
    for w in records:
        w["_delay"] = calc_wash_delay(w)
        if w.get("sent_date") and w.get("wash_type"):
            lead = WASH_LEAD_TIMES.get(w["wash_type"], 3)
            from business_logic import _parse_date
            sent = _parse_date(w["sent_date"])
            if sent:
                w["_expected_rcv"] = (sent + timedelta(days=lead)).isoformat()
            else:
                w["_expected_rcv"] = None
        else:
            w["_expected_rcv"] = None
    wash_otif = get_wash_otif()
    return templates.TemplateResponse("wash.html", {
        "request": request, "user": user, "active": "wash",
        "records": records, "wash_otif": wash_otif,
        "wash_lead_times": WASH_LEAD_TIMES,
    })

@router.post("/wash/create")
def wash_create(request: Request,
    style_code: str = Form(""), customer: str = Form(""),
    merchant: str = Form(""), season: str = Form(""), color: str = Form(""),
    fabric_type: str = Form(""), sample_type: str = Form(""),
    wash_type: str = Form("BASIC"), required_wash: str = Form(""),
    wash_unit: str = Form(""), result: str = Form("Pending"),
    sent_date: str = Form(""), received_date: str = Form(""),
    comments: str = Form("")):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import WashController
    WashController().create({
        "sample_id": None, "style_code": style_code, "customer": customer,
        "merchant": merchant, "season": season, "color": color,
        "fabric_type": fabric_type, "sample_type": sample_type,
        "wash_type": wash_type, "required_wash": required_wash,
        "wash_unit": wash_unit, "sent_date": sent_date or None,
        "received_date": received_date or None, "result": result,
        "comments": comments, "created_by": user["id"]
    })
    return RedirectResponse("/wash", 302)

@router.post("/wash/update/{record_id}")
def wash_update(request: Request, record_id: int,
    received_date: str = Form(""), result: str = Form("Pending"),
    comments: str = Form("")):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from database import get_connection
    conn = get_connection()
    conn.execute(
        "UPDATE wash_reports SET received_date=?, result=?, comments=? WHERE id=?",
        (received_date or None, result, comments, record_id)
    )
    conn.commit(); conn.close()
    return RedirectResponse("/wash", 303)

@router.get("/reports", response_class=HTMLResponse)
def reports_page(request: Request):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    return templates.TemplateResponse("reports.html", {"request": request, "user": user, "active": "reports"})
