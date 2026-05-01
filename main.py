import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from database import init_db
import auth, dashboard, styles, samples, qa, dispatch, brands, merchants, users, wash
import indent, wip, output, alerts, analytics

# Use environment variable for secret key
SECRET_KEY = os.environ.get("SECRET_KEY", "sampleflow-plm-secret-2025-aquarelle")

app = FastAPI(title="SampleFlow Apparel PLM", description="Sample Lifecycle Tracking System")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.on_event("startup")
def startup():
    # Initialize database tables
    init_db()
    # Auto-seed demo data when running on Render
    if os.environ.get("RENDER"):
        try:
            from database import get_connection
            conn = get_connection()
            count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            conn.close()
            if count == 0:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "seed", os.path.join(os.path.dirname(__file__), "seed_demo_data.py"))
                seed = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(seed)
                seed.reset_and_seed()
                print("==> SampleFlow: Demo data seeded successfully on Render")
        except Exception as e:
            print(f"==> SampleFlow: Auto-seed note: {e}")

for r in [auth, dashboard, styles, samples, qa, dispatch, brands, merchants, users, wash,
          indent, wip, output, alerts, analytics]:
    app.include_router(r.router)

@app.get("/")
def root():
    return RedirectResponse("/login", 302)

@app.get("/health")
def health():
    return {"status": "ok", "app": "SampleFlow PLM"}
