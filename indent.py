import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))

def get_user(r): return r.session.get("user")

@router.get("/indent", response_class=HTMLResponse)
def indent_page(request: Request):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import IndentController, BrandController, MerchantController
    from business_logic import calc_indent_delay
    indents = IndentController.get_all()
    for i in indents:
        i["_delay"] = calc_indent_delay(i)
    return templates.TemplateResponse("indent.html", {
        "request": request, "user": user, "active": "indent",
        "indents": indents,
        "brands": BrandController.get_all(),
        "merchants": MerchantController.get_all(),
    })

@router.post("/indent/create")
def indent_create(
    request: Request,
    style_code: str = Form(""),
    style_name: str = Form(""),
    brand_id: str = Form(""),
    merchant_id: str = Form(""),
    season: str = Form(""),
    sample_type: str = Form(...),
    size: str = Form(""),
    qty: int = Form(1),
    color: str = Form(""),
    body_fabric_code: str = Form(""),
    body_fabric_desc: str = Form(""),
    fabric_composition: str = Form(""),
    fabric_status: str = Form(""),
    trim_fabric_code: str = Form(""),
    trim_desc: str = Form(""),
    fabric_placement: str = Form(""),
    wash_type: str = Form(""),
    special_requirements: str = Form(""),
    print_embroidery: str = Form(""),
    thread_top_stitch: str = Form(""),
    thread_body: str = Form(""),
    button_details: str = Form(""),
    erp_ref: str = Form(""),
    indent_date: str = Form(""),
    target_dispatch: str = Form(""),
    is_planned: int = Form(0),
    priority: str = Form("Normal"),
    remarks: str = Form(""),
):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import IndentController
    data = {
        "style_code": style_code, "style_name": style_name,
        "brand_id": int(brand_id) if brand_id else None,
        "merchant_id": int(merchant_id) if merchant_id else None,
        "season": season, "sample_type": sample_type, "size": size, "qty": qty,
        "color": color, "body_fabric_code": body_fabric_code,
        "body_fabric_desc": body_fabric_desc, "fabric_composition": fabric_composition,
        "fabric_status": fabric_status, "trim_fabric_code": trim_fabric_code,
        "trim_desc": trim_desc, "fabric_placement": fabric_placement,
        "wash_type": wash_type, "special_requirements": special_requirements,
        "print_embroidery": print_embroidery, "thread_top_stitch": thread_top_stitch,
        "thread_body": thread_body, "button_details": button_details,
        "erp_ref": erp_ref, "indent_date": indent_date or None,
        "target_dispatch": target_dispatch or None,
        "is_planned": is_planned, "priority": priority, "remarks": remarks,
        "created_by": user["id"],
    }
    IndentController.create(data)
    return RedirectResponse("/indent", 302)

@router.post("/indent/update")
def indent_update(
    request: Request,
    indent_id: int = Form(...),
    status: str = Form("Pending"),
    is_planned: int = Form(0),
    remarks: str = Form(""),
):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import IndentController
    IndentController.update(indent_id, status, is_planned, remarks)
    return RedirectResponse("/indent", 302)

@router.post("/indent/update-full")
def indent_update_full(
    request: Request,
    indent_id: int = Form(...),
    status: str = Form("Pending"),
    wip_stage: str = Form("U/P"),
    is_planned: int = Form(0),
    remarks: str = Form(""),
):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from database import get_connection
    from datetime import date
    conn = get_connection()
    new_status = "Completed" if wip_stage == "Dispatched" else status
    actual_dispatch = date.today().isoformat() if wip_stage == "Dispatched" else None
    if actual_dispatch:
        conn.execute(
            "UPDATE indents SET status=?, wip_stage=?, is_planned=?, remarks=?, actual_dispatch_date=?, updated_at=datetime('now') WHERE id=?",
            (new_status, wip_stage, is_planned, remarks, actual_dispatch, indent_id)
        )
    else:
        conn.execute(
            "UPDATE indents SET status=?, wip_stage=?, is_planned=?, remarks=?, updated_at=datetime('now') WHERE id=?",
            (new_status, wip_stage, is_planned, remarks, indent_id)
        )
    conn.commit()
    conn.close()
    return RedirectResponse("/indent", 302)
