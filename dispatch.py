import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))

def get_user(r): return r.session.get("user")

@router.get("/dispatch", response_class=HTMLResponse)
def dispatch_page(request: Request, tab: str = "history"):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import DispatchController, SampleController
    dispatches = DispatchController.get_all()
    # Show samples that are approved or in progress (ready/near-ready to dispatch)
    from database import get_connection
    conn = get_connection()
    pending_rows = conn.execute("""
        SELECT s.*, st.style_code, b.name as brand_name
        FROM samples s
        JOIN styles st ON s.style_id = st.id
        LEFT JOIN brands b ON st.brand_id = b.id
        WHERE s.current_status NOT IN ('Dispatched','Cancelled','Rejected')
        ORDER BY s.due_date ASC
    """).fetchall()
    conn.close()
    pending = [dict(r) for r in pending_rows] or SampleController.get_all(filters={"dept": "QA"})
    return templates.TemplateResponse("dispatch.html", {"request": request, "user": user, "active": "dispatch", "tab": tab, "dispatches": dispatches, "pending": pending})

@router.post("/dispatch/submit")
def dispatch_submit(request: Request, sample_db_id: int = Form(...),
    recipient: str = Form(...), address: str = Form(""),
    courier: str = Form(""), tracking_no: str = Form(""), notes: str = Form("")):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import DispatchController
    DispatchController.dispatch_sample(sample_db_id, recipient, address, courier, tracking_no, user["id"], notes)
    return RedirectResponse("/dispatch", 302)
