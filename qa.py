import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))

def get_user(r): return r.session.get("user")

@router.get("/qa", response_class=HTMLResponse)
def qa_page(request: Request):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import QAController
    return templates.TemplateResponse("qa.html", {"request": request, "user": user, "active": "qa", "samples": QAController.get_samples_in_qa()})

@router.post("/qa/submit")
def qa_submit(request: Request, sample_db_id: int = Form(...),
    check_type: str = Form(...), result: str = Form(...),
    defects: str = Form(""), notes: str = Form("")):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import QAController
    QAController.add_check(sample_db_id, check_type, "", defects, result, user["id"], notes)
    return RedirectResponse("/qa", 302)
