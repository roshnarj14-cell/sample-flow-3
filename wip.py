import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))

def get_user(r): return r.session.get("user")

@router.get("/wip", response_class=HTMLResponse)
def wip_page(request: Request):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import WIPController, BrandController, MerchantController
    from business_logic import calc_indent_delay
    rows = WIPController.get_rows()
    # Attach delay info to each row
    for r in rows:
        r["_delay"] = calc_indent_delay(r)
    return templates.TemplateResponse("wip.html", {
        "request": request, "user": user, "active": "wip",
        "wip_summary": WIPController.get_summary(),
        "wip_rows": rows,
        "brands": BrandController.get_all(),
        "merchants": MerchantController.get_all(),
    })

@router.post("/wip/update-stage")
def update_stage(request: Request, indent_id: int = Form(...), wip_stage: str = Form(...)):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from database import get_connection
    conn = get_connection()
    valid_stages = ["U/P","U/C","U/S","U/W","U/F","Dispatched"]
    if wip_stage in valid_stages:
        new_status = "Completed" if wip_stage == "Dispatched" else "In Progress"
        from datetime import date
        actual_dispatch = date.today().isoformat() if wip_stage == "Dispatched" else None
        if actual_dispatch:
            conn.execute(
                "UPDATE indents SET wip_stage=?, status=?, actual_dispatch_date=?, updated_at=datetime('now') WHERE id=?",
                (wip_stage, new_status, actual_dispatch, indent_id)
            )
        else:
            conn.execute(
                "UPDATE indents SET wip_stage=?, status=?, updated_at=datetime('now') WHERE id=?",
                (wip_stage, new_status, indent_id)
            )
        conn.commit()
    conn.close()
    return RedirectResponse("/wip", 303)
