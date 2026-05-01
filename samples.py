import os
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=os.path.dirname(os.path.abspath(__file__)))

def get_user(request):
    return request.session.get("user")

@router.get("/samples", response_class=HTMLResponse)
def samples_page(request: Request):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import SampleController, StyleController
    return templates.TemplateResponse("samples.html", {
        "request": request, "user": user, "active": "samples",
        "samples": SampleController.get_all(),
        "styles": StyleController.get_all(),
    })

@router.post("/samples/create")
def samples_create(request: Request, style_id: int = Form(...),
    sample_type: str = Form(...), size: str = Form(""),
    color: str = Form(""), due_date: str = Form(""), remarks: str = Form("")):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import SampleController
    data = {"sample_type": sample_type, "size": size, "color": color,
            "due_date": due_date, "remarks": remarks}
    SampleController.create(style_id, data, user["id"])
    return RedirectResponse("/samples", 302)

@router.post("/samples/move")
def samples_move(request: Request, sample_db_id: int = Form(...),
    to_dept: str = Form(...), status: str = Form("In Progress"), notes: str = Form("")):
    user = get_user(request)
    if not user: return RedirectResponse("/login", 302)
    from main_controller import SampleController
    SampleController.move_sample(sample_db_id, to_dept, status, user["id"], notes)
    return RedirectResponse("/samples", 302)
