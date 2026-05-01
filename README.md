# NexaSync PLM — Setup & Deployment Guide

## What is NexaSync?
A web-based sample lifecycle tracking system for apparel product development.
Built with FastAPI + SQLite + Jinja2.

---

## Running Locally in PyCharm

### Step 1 — Open the Project
1. Open PyCharm
2. Click **File → Open**
3. Select the `nexasync_plm` folder
4. Click **OK**

### Step 2 — Set Up Python Interpreter
1. Go to **File → Settings → Project → Python Interpreter**
2. Click the gear icon → **Add**
3. Select **Virtual Environment → New**
4. Click **OK**

### Step 3 — Install Requirements
Open the **Terminal** tab at the bottom of PyCharm and run:
```
pip install -r requirements.txt
```

### Step 4 — Run the App
In the PyCharm Terminal run:
```
uvicorn main:app --reload
```

### Step 5 — Open in Browser
Go to: **http://127.0.0.1:8000**

### Login Credentials
| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Merchandiser | merch1 | pass123 |
| Sampling | sampling1 | pass123 |
| QA | qa1 | pass123 |

### Seed Demo Data (Optional)
To load sample data into the database:
```
python seed_demo_data.py
```

---

## Deploying to Render (Free Hosting)

### Step 1 — Create GitHub Repository
1. Go to **github.com** → sign in → click **New Repository**
2. Name it: `nexasync-plm`
3. Set to **Public**
4. Click **Create Repository**

### Step 2 — Push Code to GitHub
In PyCharm Terminal:
```
git init
git add .
git commit -m "NexaSync PLM - initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/nexasync-plm.git
git push -u origin main
```

### Step 3 — Deploy on Render
1. Go to **render.com** → Sign up / Log in
2. Click **New → Web Service**
3. Connect your GitHub account
4. Select the `nexasync-plm` repository
5. Render will auto-detect the settings from `render.yaml`
6. Click **Create Web Service**
7. Wait 2-3 minutes for build to complete
8. Your app will be live at: `https://nexasync-plm.onrender.com`

### Important Note for Render
Render's free tier uses SQLite stored in `/tmp` — data resets on each redeploy.
For permanent data storage on Render free tier, use the DATABASE_URL approach.
This is fine for demo/GP purposes.

---

## Project Structure
```
nexasync_plm/
├── main.py              ← App entry point
├── database.py          ← Database schema and connection
├── main_controller.py   ← Main business logic
├── business_logic.py    ← Delay calc, OTIF, alerts
├── auth.py              ← Login/logout
├── indent.py            ← Indent management
├── wip.py               ← WIP stage tracking
├── wash.py              ← Wash tracking
├── alerts.py            ← Alert engine
├── analytics.py         ← Analytics dashboard
├── dashboard.py         ← Home dashboard
├── samples.py           ← Sample management
├── dispatch.py          ← Dispatch module
├── qa.py                ← QA module
├── brands.py            ← Brand master
├── merchants.py         ← Merchant master
├── users.py             ← User management
├── static/
│   └── style.css        ← Stylesheet
├── *.html               ← Jinja2 templates
├── seed_demo_data.py    ← Load demo data
├── requirements.txt     ← Python dependencies
├── render.yaml          ← Render deployment config
└── Procfile             ← Process file for deployment
```
