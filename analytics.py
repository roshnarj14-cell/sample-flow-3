import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))

@router.get("/analytics", response_class=HTMLResponse)
def analytics(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login", 302)
    from business_logic import (
        get_sample_otif, get_wash_otif, get_stage_progress,
        calc_avg_approval_time, generate_alerts
    )
    from database import get_connection

    conn = get_connection()

    # Wash breakdown by type
    wash_type_rows = conn.execute("""
        SELECT wash_type, COUNT(*) as total,
               SUM(CASE WHEN result='Pass' THEN 1 ELSE 0 END) as passed,
               SUM(CASE WHEN result='Fail' THEN 1 ELSE 0 END) as failed,
               SUM(CASE WHEN result='Rework' THEN 1 ELSE 0 END) as rework
        FROM wash_reports GROUP BY wash_type ORDER BY total DESC
    """).fetchall()
    wash_by_type = [dict(r) for r in wash_type_rows]

    # Customer-wise indent count
    cust_rows = conn.execute("""
        SELECT b.name as customer, COUNT(*) as cnt,
               SUM(CASE WHEN i.status='Completed' THEN 1 ELSE 0 END) as done
        FROM indents i LEFT JOIN brands b ON i.brand_id=b.id
        WHERE b.name IS NOT NULL
        GROUP BY b.name ORDER BY cnt DESC LIMIT 10
    """).fetchall()
    by_customer = [dict(r) for r in cust_rows]

    # Sample type breakdown
    st_rows = conn.execute("""
        SELECT sample_type, COUNT(*) as cnt FROM indents GROUP BY sample_type ORDER BY cnt DESC
    """).fetchall()
    by_sample_type = [dict(r) for r in st_rows]

    # Merchant performance
    merch_rows = conn.execute("""
        SELECT m.name as merchant,
               COUNT(*) as total,
               SUM(CASE WHEN i.status='Completed' AND i.actual_dispatch_date IS NOT NULL AND i.actual_dispatch_date <= i.target_dispatch THEN 1 ELSE 0 END) as on_time,
               SUM(CASE WHEN i.status='Completed' THEN 1 ELSE 0 END) as completed
        FROM indents i LEFT JOIN merchants m ON i.merchant_id=m.id
        WHERE m.name IS NOT NULL
        GROUP BY m.name ORDER BY total DESC
    """).fetchall()
    by_merchant = [dict(r) for r in merch_rows]

    # Monthly trend (last 6 months)
    monthly_rows = conn.execute("""
        SELECT strftime('%Y-%m', created_at) as month,
               COUNT(*) as created,
               SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) as completed
        FROM indents
        WHERE created_at >= date('now','-6 months')
        GROUP BY month ORDER BY month
    """).fetchall()
    monthly_trend = [dict(r) for r in monthly_rows]

    # WIP breakdown
    wip_rows = conn.execute("""
        SELECT wip_stage, COUNT(*) as cnt FROM indents
        WHERE status NOT IN ('Cancelled','Completed')
        GROUP BY wip_stage
    """).fetchall()
    wip_breakdown = [dict(r) for r in wip_rows]

    conn.close()

    sample_otif = get_sample_otif()
    wash_otif = get_wash_otif()
    avg_approval = calc_avg_approval_time()
    stage_progress = get_stage_progress()

    return templates.TemplateResponse("analytics.html", {
        "request": request, "user": user, "active": "analytics",
        "sample_otif": sample_otif, "wash_otif": wash_otif,
        "avg_approval": avg_approval, "stage_progress": stage_progress,
        "wash_by_type": wash_by_type, "by_customer": by_customer,
        "by_sample_type": by_sample_type, "by_merchant": by_merchant,
        "monthly_trend": monthly_trend, "wip_breakdown": wip_breakdown,
    })

@router.get("/api/alert-count")
def api_alert_count(request: Request):
    if not request.session.get("user"):
        return JSONResponse({"total": 0, "critical": 0, "warning": 0, "info": 0})
    from business_logic import get_alert_counts
    return JSONResponse(get_alert_counts())

@router.get("/api/otif")
def api_otif(request: Request):
    if not request.session.get("user"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    from business_logic import get_sample_otif, get_wash_otif
    return JSONResponse({
        "sample_otif": get_sample_otif(),
        "wash_otif": get_wash_otif()
    })
