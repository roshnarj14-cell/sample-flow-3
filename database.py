"""
PLM Database Model - SQLite schema and connection management
"""
import sqlite3
import os
import hashlib
from datetime import datetime

# On Render, use /tmp for writable storage. Locally use app directory.
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "plm_data.db"))
if os.environ.get("RENDER"):
    DB_PATH = "/tmp/plm_data.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # ── USERS ──────────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        username    TEXT    UNIQUE NOT NULL,
        password    TEXT    NOT NULL,
        full_name   TEXT    NOT NULL,
        role        TEXT    NOT NULL CHECK(role IN ('Admin','Designer','Merchandiser','Sampling','QA','Manager','SE','SamplingTech','Dispatch')),
        email       TEXT,
        active      INTEGER DEFAULT 1,
        created_at  TEXT    DEFAULT (datetime('now'))
    )""")

    # ── BRANDS ─────────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS brands (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        code        TEXT    UNIQUE NOT NULL,
        name        TEXT    NOT NULL,
        country     TEXT,
        contact     TEXT,
        email       TEXT,
        notes       TEXT,
        active      INTEGER DEFAULT 1,
        created_at  TEXT    DEFAULT (datetime('now'))
    )""")

    # ── MERCHANTS ──────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS merchants (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        code        TEXT    UNIQUE NOT NULL,
        name        TEXT    NOT NULL,
        email       TEXT,
        phone       TEXT,
        department  TEXT,
        notes       TEXT,
        active      INTEGER DEFAULT 1,
        created_at  TEXT    DEFAULT (datetime('now'))
    )""")

    # ── STYLES ─────────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS styles (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        style_code      TEXT    UNIQUE NOT NULL,
        style_name      TEXT    NOT NULL,
        brand_id        INTEGER REFERENCES brands(id),
        merchant_id     INTEGER REFERENCES merchants(id),
        season          TEXT,
        garment_category TEXT,
        fabric          TEXT,
        fabric_composition TEXT,
        color           TEXT,
        target_fob      REAL,
        target_dispatch TEXT,
        design_notes    TEXT,
        sketch_path     TEXT,
        status          TEXT    DEFAULT 'Design Intent'
                                CHECK(status IN ('Design Intent','Sampling','QA','Approved','Dispatched','Cancelled')),
        created_by      INTEGER REFERENCES users(id),
        created_at      TEXT    DEFAULT (datetime('now')),
        updated_at      TEXT    DEFAULT (datetime('now'))
    )""")

    # ── SAMPLES ────────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS samples (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        sample_id       TEXT    UNIQUE NOT NULL,
        style_id        INTEGER NOT NULL REFERENCES styles(id),
        sample_type     TEXT    NOT NULL,
        size            TEXT,
        color           TEXT,
        fabric_ref      TEXT,
        due_date        TEXT,
        current_dept    TEXT    DEFAULT 'Design',
        current_status  TEXT    DEFAULT 'Pending'
                                CHECK(current_status IN ('Pending','In Progress','QA Hold','Approved','Rejected','Dispatched')),
        qr_path         TEXT,
        remarks         TEXT,
        created_by      INTEGER REFERENCES users(id),
        created_at      TEXT    DEFAULT (datetime('now')),
        updated_at      TEXT    DEFAULT (datetime('now'))
    )""")

    # ── SAMPLE MOVEMENTS ───────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS sample_movements (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        sample_id       INTEGER NOT NULL REFERENCES samples(id),
        from_dept       TEXT,
        to_dept         TEXT    NOT NULL,
        status          TEXT    NOT NULL,
        scanned_by      INTEGER REFERENCES users(id),
        notes           TEXT,
        timestamp       TEXT    DEFAULT (datetime('now'))
    )""")

    # ── QA CHECKPOINTS ─────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS qa_checks (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        sample_id       INTEGER NOT NULL REFERENCES samples(id),
        check_type      TEXT    NOT NULL,
        measurements    TEXT,
        defects         TEXT,
        result          TEXT    CHECK(result IN ('Pass','Fail','Conditional Pass')),
        inspector       INTEGER REFERENCES users(id),
        notes           TEXT,
        checked_at      TEXT    DEFAULT (datetime('now'))
    )""")

    # ── DISPATCH ───────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS dispatches (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        dispatch_no     TEXT    UNIQUE NOT NULL,
        sample_id       INTEGER NOT NULL REFERENCES samples(id),
        recipient       TEXT    NOT NULL,
        address         TEXT,
        courier         TEXT,
        tracking_no     TEXT,
        dispatch_date   TEXT    DEFAULT (datetime('now')),
        dispatched_by   INTEGER REFERENCES users(id),
        notes           TEXT
    )""")

    # ── WASH REPORTS ───────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS wash_reports (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        sample_id       TEXT    REFERENCES samples(sample_id),
        style_code      TEXT,
        customer        TEXT,
        merchant        TEXT,
        season          TEXT,
        color           TEXT,
        fabric_type     TEXT,
        sample_type     TEXT,
        wash_type       TEXT    CHECK(wash_type IN ('BASIC','NON-WASH','RFD/OD','DENIM -CRITICAL','DENIM - NON CRITICAL','NON-DENIM CRITICAL','TBC')),
        required_wash   TEXT,
        wash_unit       TEXT,
        sent_date       TEXT,
        received_date   TEXT,
        result          TEXT    CHECK(result IN ('Pass','Fail','Pending','Rework')),
        comments        TEXT,
        created_by      INTEGER REFERENCES users(id),
        created_at      TEXT    DEFAULT (datetime('now'))
    )""")

    # ── INDENTS (Sample Request Forms) ─────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS indents (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        indent_no           TEXT    UNIQUE NOT NULL,
        style_code          TEXT,
        style_name          TEXT,
        brand_id            INTEGER REFERENCES brands(id),
        merchant_id         INTEGER REFERENCES merchants(id),
        season              TEXT,
        sample_type         TEXT    NOT NULL,
        size                TEXT,
        qty                 INTEGER DEFAULT 1,
        color               TEXT,
        body_fabric_code    TEXT,
        body_fabric_desc    TEXT,
        fabric_composition  TEXT,
        fabric_status       TEXT,
        trim_fabric_code    TEXT,
        trim_desc           TEXT,
        fabric_placement    TEXT,
        wash_type           TEXT,
        special_requirements TEXT,
        print_embroidery    TEXT,
        thread_top_stitch   TEXT,
        thread_body         TEXT,
        button_details      TEXT,
        erp_ref             TEXT,
        indent_date         TEXT,
        target_dispatch     TEXT,
        is_planned          INTEGER DEFAULT 0,
        actual_dispatch_date TEXT,
        priority            TEXT    DEFAULT 'Normal',
        wip_stage           TEXT    DEFAULT 'U/P',
        status              TEXT    DEFAULT 'Pending'
                                    CHECK(status IN ('Pending','In Progress','Completed','Cancelled')),
        remarks             TEXT,
        created_by          INTEGER REFERENCES users(id),
        created_at          TEXT    DEFAULT (datetime('now')),
        updated_at          TEXT    DEFAULT (datetime('now'))
    )""")

    # ── SEED DATA ──────────────────────────────────────────────────────────────
    # Default admin user
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("""INSERT INTO users (username,password,full_name,role,email)
                     VALUES (?,?,?,?,?)""",
                  ('admin', hash_password('admin123'), 'System Administrator', 'Admin', 'admin@plm.com'))
        c.execute("""INSERT INTO users (username,password,full_name,role)
                     VALUES (?,?,?,?)""",
                  ('designer1', hash_password('pass123'), 'Sarah Ahmed', 'Designer'))
        c.execute("""INSERT INTO users (username,password,full_name,role)
                     VALUES (?,?,?,?)""",
                  ('merch1', hash_password('pass123'), 'Raj Kumar', 'Merchandiser'))
        c.execute("""INSERT INTO users (username,password,full_name,role)
                     VALUES (?,?,?,?)""",
                  ('sampling1', hash_password('pass123'), 'Ali Hassan', 'Sampling'))
        c.execute("""INSERT INTO users (username,password,full_name,role)
                     VALUES (?,?,?,?)""",
                  ('qa1', hash_password('pass123'), 'Priya Singh', 'QA'))

    # Demo brands
    c.execute("SELECT COUNT(*) FROM brands")
    if c.fetchone()[0] == 0:
        brands = [
            ('LEV', "Levi's",                    'USA',       "Levi's Sourcing",   'sourcing@levi.com'),
            ('DOC', 'Dockers',                   'USA',       'Dockers Sourcing',  'sourcing@dockers.com'),
            ('SUP', 'Superdry',                  'UK',        'Superdry PD',       'pd@superdry.com'),
            ('JOU', 'Joules',                    'UK',        'Joules Sourcing',   'sourcing@joules.com'),
            ('UCB', 'United Colours of Benetton','Italy',     'UCB Sampling',      'samples@benetton.com'),
            ('MUJ', 'Muji',                      'Japan',     'Muji PD',           'pd@muji.com'),
            ('LAM', 'La Martina',                'Argentina', 'La Martina QA',     'qa@lamartina.com'),
            ('DRS', 'Dressman',                  'Norway',    'Dressman Sourcing', 'sourcing@dressman.com'),
            ('THF', 'Tommy Hilfiger',             'USA',       'TH Sourcing',       'sourcing@tommy.com'),
            ('FAR', 'Farah',                     'UK',        'Farah PD',          'pd@farah.com'),
        ]
        c.executemany("INSERT INTO brands(code,name,country,contact,email) VALUES (?,?,?,?,?)", brands)

    # Demo merchants
    c.execute("SELECT COUNT(*) FROM merchants")
    if c.fetchone()[0] == 0:
        merchants = [
            ('MCH001', 'Prasad / Asha',    'prasad@aquarelleindia.com',  '+91-9876541001', 'Woven - Muji UCB'),
            ('MCH002', 'Deepthi Menon',    'deepthi@aquarelleindia.com', '+91-9876541002', "Woven - Levi's Dockers"),
            ('MCH003', 'Shruthi Krishnan', 'shruthi@aquarelleindia.com', '+91-9876541003', "Woven - Levi's"),
            ('MCH004', 'Nimmy Thomas',     'nimmy@aquarelleindia.com',   '+91-9876541004', 'Woven - UCB La Martina'),
            ('MCH005', 'Asha Nair',        'asha@aquarelleindia.com',    '+91-9876541005', 'Woven - Superdry Joules'),
        ]
        c.executemany("INSERT INTO merchants(code,name,email,phone,department) VALUES (?,?,?,?,?)", merchants)

    conn.commit()
    conn.close()


# ── Utility: auto-generate codes ──────────────────────────────────────────────

def next_style_code():
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as n FROM styles").fetchone()
    n = row['n'] + 1
    conn.close()
    year = datetime.now().strftime('%y')
    return f"STY{year}{n:04d}"


def next_sample_id(style_code: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as n FROM samples s JOIN styles st ON s.style_id=st.id WHERE st.style_code=?",
        (style_code,)
    ).fetchone()
    n = row['n'] + 1
    conn.close()
    return f"{style_code}-S{n:03d}"


def next_dispatch_no():
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as n FROM dispatches").fetchone()
    n = row['n'] + 1
    conn.close()
    today = datetime.now().strftime('%Y%m%d')
    return f"DSP{today}{n:03d}"